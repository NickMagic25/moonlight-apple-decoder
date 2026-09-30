#include "moonlight_apple_video/decoder.h"
#include "pyrowave.hpp"
#include "pyrowave_bitstream.hpp"
#include "pyrowave_metal.h"
#import <Metal/Metal.h>
#include <algorithm>
#include <chrono>
#include <condition_variable>
#include <cstdlib>
#include <cstring>
#include <iomanip>
#include <iostream>
#include <mutex>
#include <vector>

namespace {
void check(bool ok,const char* message) {if(!ok){std::cerr<<message<<'\n';std::exit(1);}}
void report(const char* label,std::vector<double> values) {
    if(values.empty()){std::cout<<label<<"_ms unavailable\n";return;}
    std::sort(values.begin(),values.end());
    std::cout<<label<<"_ms median="<<values[values.size()/2]<<" p95="<<values[values.size()*95/100]<<" max="<<values.back()<<'\n';
}
uint64_t pixel_hash(id<MTLTexture> texture,id<MTLCommandQueue> queue) {
    const size_t row=(texture.width*2+255)&~size_t(255);
    id<MTLBuffer> buffer=[texture.device newBufferWithLength:row*texture.height options:MTLResourceStorageModeShared];
    id<MTLCommandBuffer> command=[queue commandBuffer];id<MTLBlitCommandEncoder> blit=[command blitCommandEncoder];
    [blit copyFromTexture:texture sourceSlice:0 sourceLevel:0 sourceOrigin:MTLOriginMake(0,0,0)
        sourceSize:MTLSizeMake(texture.width,texture.height,1) toBuffer:buffer destinationOffset:0
        destinationBytesPerRow:row destinationBytesPerImage:row*texture.height];
    [blit endEncoding];[command commit];[command waitUntilCompleted];
    check(command.status==MTLCommandBufferStatusCompleted,"Readback failed");
    uint64_t hash=14695981039346656037ull;
    for(size_t y=0;y<texture.height;++y)for(size_t x=0;x<texture.width*2;++x){
        hash^=static_cast<const uint8_t*>(buffer.contents)[y*row+x];hash*=1099511628211ull;}
    return hash;
}
void append_word(std::vector<uint8_t>& bytes,uint32_t word) {
    for(int i=0;i<4;++i)bytes.push_back(uint8_t(word>>(8*i)));
}
uint32_t next_random(uint32_t& state) {
    state^=state<<13;state^=state>>17;state^=state<<5;return state;
}
void coefficient_fixture(uint32_t width,uint32_t height,bool chroma444,size_t budget,bool dense,
                         std::vector<uint8_t>& bytes,std::vector<pyrowave_packet>& packets) {
    PyroWave::BlockLayout layout;check(layout.init(int(width),int(height),chroma444?
        PyroWave::ChromaSubsampling::Chroma444:PyroWave::ChromaSubsampling::Chroma420),"Fixture layout failed");
    bytes.clear();packets.clear();append_word(bytes,0x80000000u|(width-1)|((height-1)<<14));append_word(bytes,0);
    packets.push_back({0,8});uint32_t random=0x9e3779b9u,blocks=0;
    for(uint32_t index=0;index<uint32_t(layout.block_count_32x32);++index){
        std::vector<uint8_t> record(8);std::vector<uint16_t> controls(dense?16:2);
        for(auto& control:controls){control=uint16_t(next_random(random));record.push_back(uint8_t(control));record.push_back(uint8_t(control>>8));}
        for(size_t i=0;i<controls.size();++i)record.push_back(4); // Four magnitude planes plus the 2-bit local controls.
        for(auto control:controls)for(int group=0;group<8;++group){
            const unsigned planes=4+((control>>(group*2))&3);
            record.push_back(255); // All eight coefficients require a sign.
            for(unsigned p=1;p<planes;++p)record.push_back(uint8_t(next_random(random)));}
        for(size_t i=0;i<controls.size()*8;++i)record.push_back(uint8_t(next_random(random)));
        while(record.size()%4)record.push_back(0);
        const uint32_t header0=(uint32_t(record.size()/4)<<16)|((1u<<controls.size())-1),header1=(index<<8)|128u;
        for(int i=0;i<4;++i){record[i]=uint8_t(header0>>(8*i));record[i+4]=uint8_t(header1>>(8*i));}
        if(bytes.size()+record.size()>budget)break;
        if(packets.back().size+record.size()<=1024)packets.back().size+=record.size();
        else packets.push_back({bytes.size(),record.size()});
        bytes.insert(bytes.end(),record.begin(),record.end());++blocks;
    }
    const uint32_t header1=blocks|(chroma444?(1u<<26):0);
    for(int i=0;i<4;++i)bytes[4+i]=uint8_t(header1>>(8*i));
}
struct Completion {
    std::mutex mutex;std::condition_variable changed;size_t count=0;
    double preparation=0,latency=0;
    mav_decode_trace stages{};uint64_t callback_ns=0,preparation_end_ns=0;
    static void callback(void* context,const mav_completion* output) {
        auto* self=static_cast<Completion*>(context);
        check(output->status==MAV_COMPLETION_OUTPUT,"Production decode failed");
        std::lock_guard<std::mutex> lock(self->mutex);
        self->preparation=double(output->trace.preparation_end_ns-output->trace.preparation_start_ns)/1e6;
        self->latency=double(output->trace.callback_ns-output->trace.admission_ns)/1e6;
        self->stages.struct_size=sizeof(self->stages);self->stages.version=MAV_ABI_VERSION;
        check(mav_completion_get_decode_trace(output,&self->stages)==MAV_OK,"Stage trace unavailable");
        self->callback_ns=output->trace.callback_ns;self->preparation_end_ns=output->trace.preparation_end_ns;
        ++self->count;self->changed.notify_all();
    }
    void wait(size_t expected) {
        std::unique_lock<std::mutex> lock(mutex);
        check(changed.wait_for(lock,std::chrono::seconds(30),[&]{return count==expected;}),"Decode timeout");
    }
};
}

// Synthetic offscreen throughput/latency probe. GPU waits below belong only to
// this benchmark, never the production submit path. Encode once, then decode a
// warmed fixed access unit so encoder and network work do not confound results.
int main(int argc,char** argv) {@autoreleasepool {
    const uint32_t width=argc>1?uint32_t(std::atoi(argv[1])):3440;
    const uint32_t height=argc>2?uint32_t(std::atoi(argv[2])):1440;
    const size_t frames=argc>3?size_t(std::atoi(argv[3])):120;
    const bool chroma444=argc>4?std::atoi(argv[4])==444:true;
    const char* pattern=argc>5?argv[5]:"ramp";
    check(width&&height&&frames>=20&&(!std::strcmp(pattern,"ramp")||!std::strcmp(pattern,"coefficients")||!std::strcmp(pattern,"blocks")),
        "Usage: mav-pyrowave-benchmark [width height frames chroma(420|444) pattern(ramp|coefficients|blocks)]");
    id<MTLDevice> metal=MTLCreateSystemDefaultDevice();
    if(!pyrowave_device_is_supported((__bridge void*)metal)){std::cout<<"SKIP: Apple7 Metal GPU unavailable\n";return 77;}
    std::cout<<"device="<<metal.name.UTF8String<<" dimensions="<<width<<'x'<<height<<" chroma="<<(chroma444?444:420)<<" output_depth=10 frames="<<frames<<" pattern="<<pattern<<'\n';
    pyrowave_device device=nullptr;pyrowave_device_create_info device_info{};device_info.mtl_device=(__bridge void*)metal;
    check(pyrowave_device_create(&device_info,&device)==PYROWAVE_SUCCESS,"Device create failed");
    pyrowave_encoder encoder=nullptr;pyrowave_encoder_create_info encoder_info{device,int(width),int(height),chroma444?PYROWAVE_CHROMA_SUBSAMPLING_444:PYROWAVE_CHROMA_SUBSAMPLING_420};
    check(pyrowave_encoder_create(&encoder_info,&encoder)==PYROWAVE_SUCCESS,"Encoder create failed");
    std::vector<uint8_t> samples[3];pyrowave_cpu_buffer input{};
    input.width=int(width);input.height=int(height);input.format=chroma444?PYROWAVE_CPU_BUFFER_FORMAT_YUV444P:PYROWAVE_CPU_BUFFER_FORMAT_YUV420P;
    for(uint32_t p=0;p<3;++p){size_t w=p&&!chroma444?width/2:width,h=p&&!chroma444?height/2:height;samples[p].resize(w*h);
        for(size_t y=0;y<h;++y)for(size_t x=0;x<w;++x){
            samples[p][y*w+x]=uint8_t(32+96*x/std::max<size_t>(w-1,1)+96*y/std::max<size_t>(h-1,1));}
        input.data[p]=samples[p].data();input.row_stride_in_bytes[p]=w;input.plane_size_in_bytes[p]=samples[p].size();}
    pyrowave_rate_control rate{1000000000u/8u/165u};
    check(pyrowave_encoder_encode_cpu_synchronous(encoder,&input,&rate)==PYROWAVE_SUCCESS,"Encode failed");
    size_t packet_count=0;check(pyrowave_encoder_compute_num_packets(encoder,1024,&packet_count)==PYROWAVE_SUCCESS,"Packet count failed");
    std::vector<pyrowave_packet> packets(packet_count);std::vector<uint8_t> bytes(size_t(width)*height*16+65536);
    check(pyrowave_encoder_packetize(encoder,packets.data(),1024,&packet_count,bytes.data(),bytes.size())==PYROWAVE_SUCCESS,"Packetize failed");
    size_t end=0;for(size_t i=0;i<packet_count;++i)end=std::max(end,packets[i].offset+packets[i].size);bytes.resize(end);
    if(std::strcmp(pattern,"ramp")){
        coefficient_fixture(width,height,chroma444,rate.maximum_bitstream_size,!std::strcmp(pattern,"coefficients"),bytes,packets);packet_count=packets.size();}
    std::cout<<"compressed_bytes="<<bytes.size()<<" packet_count="<<packet_count<<" budget_bytes="<<rate.maximum_bitstream_size<<'\n';
    pyrowave_encoder_destroy(encoder);

    // Isolate actual GPU compute time from CPU parsing, driver scheduling and
    // callback dispatch; private textures are reused only after GPU completion.
    pyrowave_decoder direct=nullptr;pyrowave_decoder_create_info direct_info{device,int(width),int(height),encoder_info.chroma};
    check(pyrowave_decoder_create(&direct_info,&direct)==PYROWAVE_SUCCESS,"Direct decoder create failed");
    id<MTLTexture> textures[3];pyrowave_gpu_buffers buffers{};
    for(int p=0;p<3;++p){auto descriptor=[MTLTextureDescriptor texture2DDescriptorWithPixelFormat:MTLPixelFormatR16Unorm width:p&&!chroma444?width/2:width height:p&&!chroma444?height/2:height mipmapped:NO];
        descriptor.storageMode=MTLStorageModePrivate;descriptor.usage=MTLTextureUsageShaderRead|MTLTextureUsageShaderWrite;
        textures[p]=[metal newTextureWithDescriptor:descriptor];buffers.planes[p]=(__bridge void*)textures[p];}
    id<MTLCommandQueue> queue=[metal newCommandQueue];std::vector<double> gpu;
    for(size_t i=0;i<frames+10;++i){@autoreleasepool {
        pyrowave_decoder_clear(direct);check(pyrowave_decoder_push_packet(direct,bytes.data(),bytes.size())==PYROWAVE_SUCCESS,"Direct parse failed");
        id<MTLCommandBuffer> command=[queue commandBuffer];check(pyrowave_decoder_decode_gpu_buffer(direct,(__bridge void*)command,&buffers)==PYROWAVE_SUCCESS,"Direct decode failed");
        [command commit];[command waitUntilCompleted];check(command.status==MTLCommandBufferStatusCompleted,"GPU command failed");
        if(i>=10)gpu.push_back((command.GPUEndTime-command.GPUStartTime)*1000.0);
    }}
    report("gpu_compute",gpu);
    for(int p=0;p<3;++p)std::cout<<"decoded_plane"<<p<<"_hash="<<std::hex<<pixel_hash(textures[p],queue)<<std::dec<<'\n';
    pyrowave_decoder_destroy(direct);pyrowave_device_destroy(device);

    Completion completion;mav_config config;mav_config_default(&config,MAV_CODEC_PYROWAVE);
    config.width=width;config.height=height;config.bit_depth=10;config.chroma_format=chroma444?3:1;
    config.completion=Completion::callback;config.context=&completion;
    mav_decoder* production=nullptr;check(mav_decoder_create(&config,&production)==MAV_OK,"Production decoder create failed");
    mav_span span{bytes.data(),bytes.size()};mav_access_unit unit;mav_access_unit_default(&unit,MAV_CODEC_PYROWAVE);unit.spans=&span;unit.span_count=1;
    std::vector<mav_pyrowave_fragment> fragments;fragments.reserve(packet_count);
    for(size_t i=0;i<packet_count;++i)fragments.push_back({uint32_t(packets[i].offset),uint32_t(packets[i].size),MAV_PYROWAVE_FRAGMENT_RECORD_START});
    unit.pyrowave_fragments=fragments.data();unit.pyrowave_fragment_count=fragments.size();
    std::vector<double> layout_times;
    for(size_t i=0;i<frames+10;++i){auto before=mav_monotonic_time_ns();PyroWave::BlockLayout layout;
        check(layout.init(int(width),int(height),encoder_info.chroma==PYROWAVE_CHROMA_SUBSAMPLING_444?
            PyroWave::ChromaSubsampling::Chroma444:PyroWave::ChromaSubsampling::Chroma420),"Layout failed");
        if(i>=10)layout_times.push_back(double(mav_monotonic_time_ns()-before)/1e6);}
    report("cpu_layout_with_mapping",layout_times);
    mav::Span parse_span{bytes.data(),bytes.size()};mav::Prepared prepared;std::string error;
    if(mav::prepare_pyrowave(&parse_span,1,config,unit,prepared,error)!=mav::ParseResult::Ok){std::cerr<<"Production framing validation: "<<error<<'\n';return 1;}
    check(prepared.bytes==bytes,"Intact validated access unit differs from input");
    std::vector<double> preparation,submit,latency,setup,push,encoding,gpu_queue,production_gpu,callback_lag;
    auto start=mav_monotonic_time_ns();
    for(size_t i=0;i<frames+10;++i){unit.frame_id=i;auto before=mav_monotonic_time_ns();
        check(mav_decoder_submit_copy(production,&unit)==MAV_OK,"Production submit failed");auto after=mav_monotonic_time_ns();
        completion.wait(i+1);if(i>=10){submit.push_back(double(after-before)/1e6);preparation.push_back(completion.preparation);latency.push_back(completion.latency);
            const auto& stage=completion.stages;
            if((stage.valid&7)==7){setup.push_back(double(stage.backend_start_ns-completion.preparation_end_ns)/1e6);
                push.push_back(double(stage.backend_submit_ns-stage.backend_start_ns)/1e6);
                encoding.push_back(double(stage.backend_return_ns-stage.backend_submit_ns)/1e6);}
            if((stage.valid&24)==24){gpu_queue.push_back(double(stage.gpu_start_ns-stage.gpu_commit_ns)/1e6);
                production_gpu.push_back(double(stage.gpu_end_ns-stage.gpu_start_ns)/1e6);
                callback_lag.push_back(double(completion.callback_ns-stage.gpu_end_ns)/1e6);}
        }}
    std::cout<<"sequential_decode_fps="<<double(frames+10)*1e9/double(mav_monotonic_time_ns()-start)<<'\n';
    report("cpu_preparation",preparation);report("cpu_submit",submit);report("admission_to_callback",latency);
    std::cout<<"backend_stage_samples="<<push.size()<<" calibrated_gpu_stage_samples="<<production_gpu.size()<<'/'<<frames<<'\n';
    report("preparation_to_backend",setup);report("backend_packet_push",push);report("backend_upload_encoding",encoding);
    report("decode_gpu_queue",gpu_queue);report("decode_gpu_execution",production_gpu);report("gpu_end_to_callback",callback_lag);
    check(mav_decoder_destroy(production)==MAV_OK,"Production destroy failed");
}}
