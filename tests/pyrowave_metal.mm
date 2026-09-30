#include "moonlight_apple_video/decoder.h"
#include "pyrowave_metal.h"
#import <Metal/Metal.h>
#include <cassert>
#include <cmath>
#include <condition_variable>
#include <fstream>
#include <iostream>
#include <mutex>
#include <vector>
struct Outputs {
    std::mutex mutex;std::condition_variable changed;
    std::vector<mav_gpu_frame> frames;uint32_t failed=0;mav_color expected_color{};
    static void callback(void* context,const mav_completion* c){
        auto* self=static_cast<Outputs*>(context);std::lock_guard<std::mutex> lock(self->mutex);
        assert(!(c->trace.valid&(MAV_TRACE_VT_SUBMIT|MAV_TRACE_VT_RETURN)));
        mav_decode_trace stage{};stage.struct_size=sizeof(stage);stage.version=MAV_ABI_VERSION;
        assert(mav_completion_get_decode_trace(c,&stage)==MAV_OK);
        assert(stage.valid==(MAV_DECODE_TRACE_BACKEND_START|MAV_DECODE_TRACE_BACKEND_SUBMIT|
            MAV_DECODE_TRACE_BACKEND_RETURN|MAV_DECODE_TRACE_GPU_COMMIT|MAV_DECODE_TRACE_GPU_EXECUTION));
        assert(c->trace.preparation_start_ns<=c->trace.preparation_end_ns&&c->trace.preparation_end_ns<=stage.backend_start_ns);
        assert(stage.backend_start_ns<=stage.backend_submit_ns&&stage.backend_submit_ns<=stage.backend_return_ns);
        assert(stage.backend_return_ns<=stage.gpu_commit_ns&&stage.gpu_commit_ns<=stage.gpu_start_ns);
        assert(stage.gpu_start_ns<=stage.gpu_end_ns&&stage.gpu_end_ns<=c->trace.callback_ns);
        assert(stage.gpu_clock_uncertainty_ns<=1000000);
        assert(c->color.valid==self->expected_color.valid&&c->color.primaries==self->expected_color.primaries&&
               c->color.transfer==self->expected_color.transfer&&c->color.matrix==self->expected_color.matrix&&
               c->color.full_range==self->expected_color.full_range);
        if(c->status==MAV_COMPLETION_OUTPUT){assert(!c->pixel_buffer&&c->gpu_frame);mav_gpu_frame_retain(c->gpu_frame);self->frames.push_back(c->gpu_frame);}
        else ++self->failed;
        self->changed.notify_all();
    }
    void wait(size_t count){std::unique_lock<std::mutex> lock(mutex);assert(changed.wait_for(lock,std::chrono::seconds(10),[&]{return frames.size()>=count||failed;}));assert(!failed);}
    ~Outputs(){for(auto frame:frames)mav_gpu_frame_release(frame);}
};
std::vector<uint8_t> readback(id<MTLTexture> texture) {
    size_t bytes=texture.pixelFormat==MTLPixelFormatR16Unorm?2:1;
    size_t row=(texture.width*bytes+255)&~size_t(255);
    id<MTLBuffer> buffer=[texture.device newBufferWithLength:row*texture.height options:MTLResourceStorageModeShared];
    id<MTLCommandQueue> queue=[texture.device newCommandQueue];id<MTLCommandBuffer> cmd=[queue commandBuffer];
    id<MTLBlitCommandEncoder> encoder=[cmd blitCommandEncoder];
    [encoder copyFromTexture:texture sourceSlice:0 sourceLevel:0 sourceOrigin:MTLOriginMake(0,0,0) sourceSize:MTLSizeMake(texture.width,texture.height,1)
                   toBuffer:buffer destinationOffset:0 destinationBytesPerRow:row destinationBytesPerImage:row*texture.height];
    [encoder endEncoding];[cmd commit];[cmd waitUntilCompleted];assert(cmd.status==MTLCommandBufferStatusCompleted);
    std::vector<uint8_t> result(texture.width*texture.height*bytes);
    for(size_t y=0;y<texture.height;++y)memcpy(result.data()+y*texture.width*bytes,static_cast<uint8_t*>(buffer.contents)+y*row,texture.width*bytes);
    return result;
}
void upload_admission() {
    id<MTLDevice> metal=MTLCreateSystemDefaultDevice();
    pyrowave_device device=nullptr;pyrowave_device_create_info create_device{};create_device.mtl_device=(__bridge void*)metal;
    assert(pyrowave_device_create(&create_device,&device)==PYROWAVE_SUCCESS);
    pyrowave_decoder decoder=nullptr;pyrowave_decoder_create_info create{device,128,128,PYROWAVE_CHROMA_SUBSAMPLING_420};
    assert(pyrowave_decoder_create(&create,&decoder)==PYROWAVE_SUCCESS);
    uint32_t sequence[2]={0x80000000u|127u|(127u<<14),0};
    id<MTLTexture> textures[3];pyrowave_gpu_buffers buffers{};
    for(int i=0;i<3;++i){auto descriptor=[MTLTextureDescriptor texture2DDescriptorWithPixelFormat:MTLPixelFormatR8Unorm width:i?64:128 height:i?64:128 mipmapped:NO];
        descriptor.usage=MTLTextureUsageShaderRead|MTLTextureUsageShaderWrite;descriptor.storageMode=MTLStorageModePrivate;
        textures[i]=[metal newTextureWithDescriptor:descriptor];buffers.planes[i]=(__bridge void*)textures[i];}
    id<MTLCommandQueue> queue=[metal newCommandQueue];id<MTLCommandBuffer> commands[5];
    for(int i=0;i<5;++i){pyrowave_decoder_clear(decoder);assert(pyrowave_decoder_push_packet(decoder,sequence,sizeof(sequence))==PYROWAVE_SUCCESS);
        commands[i]=[queue commandBuffer];auto result=pyrowave_decoder_decode_gpu_buffer(decoder,(__bridge void*)commands[i],&buffers);
        assert(result==(i==4?PYROWAVE_ERROR_BUSY:PYROWAVE_SUCCESS));}
    assert(pyrowave_decoder_decode_is_ready(decoder,false)); // Busy consumed nothing.
    assert(!pyrowave_decoder_decode_is_ready_with_sideband(decoder,true,5,0.9f,nullptr,0));
    assert(!pyrowave_decoder_decode_is_ready_with_sideband(decoder,true,-1,0.9f,nullptr,0));
    assert(!pyrowave_decoder_decode_is_ready_with_sideband(decoder,true,0,NAN,nullptr,0));
    for(int i=0;i<4;++i)[commands[i] commit];for(int i=0;i<4;++i)[commands[i] waitUntilCompleted];
    assert(pyrowave_decoder_decode_gpu_buffer(decoder,(__bridge void*)commands[4],&buffers)==PYROWAVE_SUCCESS);
    [commands[4] commit];[commands[4] waitUntilCompleted];
    auto result=readback(textures[0]);for(uint8_t value:result)assert(value==128);
    pyrowave_decoder_destroy(decoder);pyrowave_device_destroy(device);
    std::cout<<"Bounded upstream upload admission and sideband validation passed\n";
}
void partial_frames() {
    std::vector<uint32_t> words{0x80000000u|127u|(127u<<14),20};
    for(uint32_t i=0;i<20;++i){words.push_back(2u<<16);words.push_back(i<<8);}
    std::vector<mav_pyrowave_fragment> fragments{{0,8,MAV_PYROWAVE_FRAGMENT_RECORD_START}};
    for(uint32_t i=0;i<20;++i)fragments.push_back({8+i*8,8,i==17?MAV_PYROWAVE_FRAGMENT_LOST:MAV_PYROWAVE_FRAGMENT_RECORD_START});
    Outputs outputs;mav_config config;mav_config_default(&config,MAV_CODEC_PYROWAVE);
    config.width=config.height=128;config.chroma_format=1;config.bit_depth=8;config.completion=Outputs::callback;config.context=&outputs;
    mav_decoder* decoder=nullptr;assert(mav_decoder_create(&config,&decoder)==MAV_OK);
    mav_span span{reinterpret_cast<const uint8_t*>(words.data()),words.size()*4};mav_access_unit unit;mav_access_unit_default(&unit,MAV_CODEC_PYROWAVE);
    unit.spans=&span;unit.span_count=1;unit.pyrowave_fragments=fragments.data();unit.pyrowave_fragment_count=fragments.size();unit.pyrowave_critical_packets=13;
    assert(mav_decoder_submit_copy(decoder,&unit)==MAV_OK);outputs.wait(1);assert(mav_decoder_drain(decoder)==MAV_OK);
    fragments[3].kind=MAV_PYROWAVE_FRAGMENT_LOST;assert(mav_decoder_submit_copy(decoder,&unit)==MAV_MALFORMED_INPUT);
    fragments[3].kind=MAV_PYROWAVE_FRAGMENT_RECORD_START;assert(mav_decoder_submit_copy(decoder,&unit)==MAV_OK);outputs.wait(2);
    assert(mav_decoder_reset(decoder)==MAV_OK);assert(mav_decoder_destroy(decoder)==MAV_OK);
    for(auto frame:outputs.frames)for(int i=0;i<3;++i){auto image=readback((__bridge id<MTLTexture>)mav_gpu_frame_plane(frame,i));for(auto value:image)assert(value==128);}
    std::cout<<"Partial GPU output, critical loss and next independent frame passed\n";
}
void run(uint32_t width,uint32_t height,bool chroma444,uint32_t depth,const char* output_dir) {
    pyrowave_device device=nullptr;assert(pyrowave_create_default_device(&device)==PYROWAVE_SUCCESS);
    pyrowave_encoder_create_info create{device,int(width),int(height),chroma444?PYROWAVE_CHROMA_SUBSAMPLING_444:PYROWAVE_CHROMA_SUBSAMPLING_420};
    pyrowave_encoder encoder=nullptr;assert(pyrowave_encoder_create(&create,&encoder)==PYROWAVE_SUCCESS);
    std::vector<uint8_t> samples[3];pyrowave_cpu_buffer input{};
    input.width=int(width);input.height=int(height);input.format=chroma444?PYROWAVE_CPU_BUFFER_FORMAT_YUV444P:PYROWAVE_CPU_BUFFER_FORMAT_YUV420P;
    for(uint32_t p=0;p<3;++p){uint32_t w=p&&!chroma444?width/2:width,h=p&&!chroma444?height/2:height;
        samples[p].resize(size_t(w)*h);
        for(uint32_t y=0;y<h;++y)for(uint32_t x=0;x<w;++x){
            uint32_t dx=std::max<uint32_t>(1,w-1),dy=std::max<uint32_t>(1,h-1);
            samples[p][size_t(y)*w+x]=p==0?uint8_t(32+96*x/dx+96*y/dy):
                p==1?uint8_t(64+64*x/dx+32*y/dy):uint8_t(160-48*x/dx+32*y/dy);}
        input.data[p]=samples[p].data();input.row_stride_in_bytes[p]=w;input.plane_size_in_bytes[p]=samples[p].size();}
    pyrowave_rate_control control{size_t(width)*height*4};assert(pyrowave_encoder_encode_cpu_synchronous(encoder,&input,&control)==PYROWAVE_SUCCESS);
    size_t count=0;assert(pyrowave_encoder_compute_num_packets(encoder,1024,&count)==PYROWAVE_SUCCESS);
    std::vector<pyrowave_packet> packets(count);std::vector<uint8_t> bytes(size_t(width)*height*16+65536);size_t actual=count;
    assert(pyrowave_encoder_packetize(encoder,packets.data(),1024,&actual,bytes.data(),bytes.size())==PYROWAVE_SUCCESS);
    size_t end=0;for(size_t i=0;i<actual;++i)end=std::max(end,packets[i].offset+packets[i].size);bytes.resize(end);
    if(output_dir){std::string path=std::string(output_dir)+"/pyrowave-"+std::to_string(width)+"x"+std::to_string(height)+(chroma444?"-444":"-420")+".bin";
        std::ofstream file(path,std::ios::binary);file.write(reinterpret_cast<char*>(bytes.data()),std::streamsize(bytes.size()));}
    Outputs outputs;mav_config config;mav_config_default(&config,MAV_CODEC_PYROWAVE);
    config.width=width;config.height=height;config.bit_depth=depth;config.chroma_format=chroma444?3:1;config.completion=Outputs::callback;config.context=&outputs;
    config.fallback_color.valid=MAV_COLOR_DESCRIPTION|MAV_COLOR_RANGE;
    config.fallback_color.primaries=depth==10?9:1;config.fallback_color.transfer=depth==10?16:1;
    config.fallback_color.matrix=depth==10?9:1;config.fallback_color.full_range=0;
    outputs.expected_color=config.fallback_color;
    mav_decoder* decoder=nullptr;assert(mav_decoder_create(&config,&decoder)==MAV_OK);
    mav_span span{bytes.data(),bytes.size()};mav_access_unit unit;mav_access_unit_default(&unit,MAV_CODEC_PYROWAVE);unit.spans=&span;unit.span_count=1;
    auto malformed=bytes;malformed[0]=0;malformed[1]=0;malformed[2]=0;malformed[3]=0;
    mav_span invalid{malformed.data(),malformed.size()};unit.spans=&invalid;
    assert(mav_decoder_submit_copy(decoder,&unit)==MAV_MALFORMED_INPUT);
    unit.spans=&span;
    for(size_t n=0;n<6;++n){unit.frame_id=n;assert(mav_decoder_submit_copy(decoder,&unit)==MAV_OK);outputs.wait(n+1);assert(mav_decoder_drain(decoder)==MAV_OK);}
    assert(mav_decoder_submit_copy(decoder,&unit)==MAV_WOULD_BLOCK);
    assert(mav_decoder_wait_for_capacity(decoder,0)==MAV_TIMEOUT);
    mav_gpu_frame_release(outputs.frames.front());outputs.frames.erase(outputs.frames.begin());
    assert(mav_decoder_wait_for_capacity(decoder,100000000)==MAV_OK);
    assert(mav_decoder_submit_copy(decoder,&unit)==MAV_OK);outputs.wait(6);assert(mav_decoder_drain(decoder)==MAV_OK);
    mav_metrics metrics{};metrics.struct_size=sizeof(metrics);metrics.version=MAV_ABI_VERSION;assert(mav_decoder_get_metrics(decoder,&metrics)==MAV_OK);assert(metrics.hardware_validated&&metrics.displayed==7);
    assert(mav_decoder_reset(decoder)==MAV_OK);assert(mav_decoder_destroy(decoder)==MAV_OK);
    auto frame=outputs.frames.back();assert(mav_gpu_frame_chroma(frame)==(chroma444?3u:1u));
    for(uint32_t p=0;p<3;++p){id<MTLTexture> texture=(__bridge id<MTLTexture>)mav_gpu_frame_plane(frame,p);auto result=readback(texture);
        double max_error=0,squared=0;for(size_t i=0;i<samples[p].size();++i){double v=depth==10?double(uint16_t(result[2*i])|uint16_t(result[2*i+1])<<8)/65535.0:double(result[i])/255.0;
            double error=std::abs(v-double(samples[p][i])/255.0);max_error=std::max(error,max_error);squared+=error*error;}
        // PyroWave is lossy. This large-budget ramp checks actual dequant+iDWT,
        // plane geometry and retained outputs without asserting bit-exact coding.
        assert(max_error<0.015&&std::sqrt(squared/samples[p].size())<0.004);
        std::cout<<width<<'x'<<height<<" chroma="<<(chroma444?444:420)<<" depth="<<depth<<" plane="<<p<<" max_error="<<max_error<<'\n';}
    pyrowave_encoder_destroy(encoder);pyrowave_device_destroy(device);
}
int main(int argc,char** argv){@autoreleasepool {
    mav_capability cap{};cap.struct_size=sizeof(cap);cap.version=MAV_ABI_VERSION;assert(mav_query_capability(MAV_CODEC_PYROWAVE,&cap)==MAV_OK);
    if(!cap.hardware_decode_candidate){std::cout<<"SKIP: Apple7 Metal GPU unavailable\n";return 77;}
    upload_admission();partial_frames();run(128,128,false,8,argc>1?argv[1]:nullptr);run(127,97,true,10,argc>1?argv[1]:nullptr);
    std::cout<<"Exact-pinned native PyroWave encode/decode, readback, pool and retained reset/destroy tests passed\n";
}}
