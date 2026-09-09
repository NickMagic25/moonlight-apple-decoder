#include "moonlight_apple_video/decoder.h"
#include "bitstream.hpp"
#include <CoreVideo/CoreVideo.h>
#include <algorithm>
#include <atomic>
#include <cmath>
#include <fstream>
#include <iostream>
#include <iterator>
#include <memory>
#include <mutex>
#include <stdexcept>
#include <string>
#include <utility>
#include <vector>

// Correctness-only test. Visible-plane copying and reference comparisons are
// deliberately excluded from all benchmark paths and latency claims.
namespace {
uint16_t le16(const uint8_t* p) { return uint16_t(p[0]) | uint16_t(p[1]) << 8; }
uint32_t le32(const uint8_t* p) { return uint32_t(le16(p)) | uint32_t(le16(p+2)) << 16; }
uint64_t le64(const uint8_t* p) { return uint64_t(le32(p)) | uint64_t(le32(p+4)) << 32; }
void require(bool condition,const std::string& message) { if (!condition) throw std::runtime_error(message); }
std::vector<uint8_t> read(const char* path) {
    std::ifstream file(path,std::ios::binary);require(bool(file),std::string("cannot open ")+path);
    std::vector<uint8_t> data((std::istreambuf_iterator<char>(file)),{});
    require(data.size()<=64*1024*1024,"accounting test fixture exceeds 64 MiB");return data;
}
struct Packet { size_t offset,size; uint64_t timestamp; mav::Prepared parsed; };
struct Fixture {
    std::vector<uint8_t> data;std::vector<Packet> packets;
    unsigned width=0,height=0,depth=0,displays=0,hidden=0,existing=0,multi=0;
};
Fixture load(const char* path) {
    Fixture f;f.data=read(path);const auto& b=f.data;
    require(b.size()>=32&&std::equal(b.begin(),b.begin()+4,"DKIF"),"not an IVF file");
    require(le16(b.data()+4)==0&&le16(b.data()+6)==32&&std::equal(b.begin()+8,b.begin()+12,"AV01"),"unsupported IVF header");
    mav::Bitstream parser(mav::Codec::AV1);size_t pos=32;
    while (pos<b.size()) {
        require(b.size()-pos>=12,"truncated IVF frame header");
        uint32_t size=le32(b.data()+pos);uint64_t timestamp=le64(b.data()+pos+4);pos+=12;
        require(size&&size<=b.size()-pos&&timestamp<=INT64_MAX,"invalid IVF packet bounds");
        Packet p{pos,size,timestamp,{}};std::string error;
        require(parser.prepare(b.data()+pos,size,p.parsed,error)==mav::ParseResult::Ok,"AV1 parse: "+error);
        require(p.parsed.displayed_frames==1,"generated accounting temporal units must each display one image");
        if (f.packets.empty()) {f.width=p.parsed.format.width;f.height=p.parsed.format.height;f.depth=p.parsed.format.bit_depth;}
        require(p.parsed.format.width==f.width&&p.parsed.format.height==f.height&&p.parsed.format.bit_depth==f.depth,"unexpected configuration change");
        for (const auto& s:p.parsed.samples) {f.hidden+=!s.display;f.existing+=s.show_existing;}
        f.multi+=p.parsed.samples.size()>1;f.displays+=p.parsed.displayed_frames;
        f.packets.push_back(std::move(p));pos+=size;
    }
    require(f.displays&&f.hidden&&f.existing&&f.multi,"encoder did not produce hidden, existing and multiple-frame accounting cases");
    return f;
}
struct Input { size_t offset,size;unsigned display_index;bool display,existing;uint64_t timestamp; };
struct Sink {
    const Fixture& fixture;const std::vector<Input>& inputs;
    std::mutex mutex;unsigned completed=0,outputs=0,no_display=0,existing=0,failed=0;
    std::vector<bool> seen;std::vector<std::vector<uint16_t>> pixels;
    Sink(const Fixture& f,const std::vector<Input>& in):fixture(f),inputs(in),seen(in.size()),pixels(f.displays) {}
};
std::vector<uint16_t> visible_pixels(CVPixelBufferRef pixel,unsigned width,unsigned height,unsigned depth) {
    require(CVPixelBufferGetWidth(pixel)==width&&CVPixelBufferGetHeight(pixel)==height&&CVPixelBufferGetPlaneCount(pixel)==2,"output dimensions/planes mismatch");
    auto format=CVPixelBufferGetPixelFormatType(pixel);
    require(depth==8?(format==kCVPixelFormatType_420YpCbCr8BiPlanarVideoRange||format==kCVPixelFormatType_420YpCbCr8BiPlanarFullRange):
                     (format==kCVPixelFormatType_420YpCbCr10BiPlanarVideoRange||format==kCVPixelFormatType_420YpCbCr10BiPlanarFullRange),"output bit depth/format mismatch");
    require(CVPixelBufferGetIOSurface(pixel)!=nullptr,"output lacks IOSurface backing");
    require(CVPixelBufferLockBaseAddress(pixel,kCVPixelBufferLock_ReadOnly)==kCVReturnSuccess,"pixel lock failed");
    struct Unlock {CVPixelBufferRef p;~Unlock(){CVPixelBufferUnlockBaseAddress(p,kCVPixelBufferLock_ReadOnly);}} unlock{pixel};
    std::vector<uint16_t> values(size_t(width)*height*3/2);
    auto y=static_cast<const uint8_t*>(CVPixelBufferGetBaseAddressOfPlane(pixel,0));
    auto uv=static_cast<const uint8_t*>(CVPixelBufferGetBaseAddressOfPlane(pixel,1));
    size_t ystride=CVPixelBufferGetBytesPerRowOfPlane(pixel,0),uvstride=CVPixelBufferGetBytesPerRowOfPlane(pixel,1);
    size_t luma=size_t(width)*height,chroma=luma/4;
    for (unsigned row=0;row<height;++row) for (unsigned x=0;x<width;++x)
        values[size_t(row)*width+x]=depth==8?y[row*ystride+x]:le16(y+row*ystride+x*2)>>6;
    for (unsigned row=0;row<height/2;++row) for (unsigned x=0;x<width/2;++x) {
        size_t i=size_t(row)*(width/2)+x;
        values[luma+i]=depth==8?uv[row*uvstride+x*2]:le16(uv+row*uvstride+x*4)>>6;
        values[luma+chroma+i]=depth==8?uv[row*uvstride+x*2+1]:le16(uv+row*uvstride+x*4+2)>>6;
    }
    return values;
}
void completion(void* context,const mav_completion* c) {
    auto& sink=*static_cast<Sink*>(context);
    try {
        require(c->frame_id<sink.inputs.size(),"completion has unknown frame ID");
        const auto& input=sink.inputs[c->frame_id];
        std::vector<uint16_t> pixels;
        if (input.display) {
            require(c->status==MAV_COMPLETION_OUTPUT&&c->pixel_buffer&&c->displayed_outputs==1&&c->hardware_accelerated,"displayed submission did not produce hardware image");
            pixels=visible_pixels(c->pixel_buffer,sink.fixture.width,sink.fixture.height,sink.fixture.depth);
        } else require(c->status==MAV_COMPLETION_NO_DISPLAY&&!c->pixel_buffer&&!c->displayed_outputs,"hidden submission terminal status/image mismatch");
        require(bool(c->show_existing_frame)==input.existing,"existing-frame event identity mismatch");
        std::lock_guard<std::mutex> lock(sink.mutex);
        require(!sink.seen[c->frame_id],"duplicate terminal completion");sink.seen[c->frame_id]=true;
        ++sink.completed;sink.existing+=input.existing;
        if (input.display) {++sink.outputs;sink.pixels[input.display_index]=std::move(pixels);} else ++sink.no_display;
    } catch (const std::exception& e) {
        std::lock_guard<std::mutex> lock(sink.mutex);++sink.failed;std::cerr<<"completion failure: "<<e.what()<<"\n";
    }
}
struct Run {unsigned accepted,completed,outputs,no_display,existing;uint64_t internal_samples;std::vector<std::vector<uint16_t>> pixels;};
Run run(const Fixture& f,bool split,unsigned inflight) {
    std::vector<Input> inputs;unsigned display_index=0;
    for (const auto& p:f.packets) {
        if (split) for (const auto& s:p.parsed.samples) {
            inputs.push_back({p.offset+s.offset,s.size,display_index,s.display,s.show_existing,p.timestamp});
            display_index+=s.display;
        } else {
            bool existing=false;for (const auto& s:p.parsed.samples)existing|=s.show_existing;
            inputs.push_back({p.offset,p.size,display_index++,true,existing,p.timestamp});
        }
    }
    Sink sink(f,inputs);mav_config config;mav_config_default(&config,MAV_CODEC_AV1);
    config.completion=completion;config.context=&sink;config.width=f.width;config.height=f.height;config.bit_depth=f.depth;config.max_frames_in_flight=inflight;
    mav_decoder* raw=nullptr;require(mav_decoder_create(&config,&raw)==MAV_OK,"decoder create failed");
    std::unique_ptr<mav_decoder,decltype(&mav_decoder_destroy)> decoder(raw,mav_decoder_destroy);
    for (size_t i=0;i<inputs.size();++i) {
        const auto& input=inputs[i];mav_span span{f.data.data()+input.offset,input.size};
        mav_access_unit u;mav_access_unit_default(&u,MAV_CODEC_AV1);u.frame_id=i;u.spans=&span;u.span_count=1;u.pts={int64_t(input.timestamp),30,1};u.dts=u.pts;
        auto result=mav_decoder_submit_copy(decoder.get(),&u);
        while (result==MAV_WOULD_BLOCK) {
            require(mav_decoder_wait_for_capacity(decoder.get(),5000000000)==MAV_OK,"capacity did not return after AV1 hidden/existing submission");
            result=mav_decoder_submit_copy(decoder.get(),&u);
        }
        require(result==MAV_OK,std::string("submit failed: ")+mav_result_string(result));
    }
    require(mav_decoder_drain(decoder.get())==MAV_OK,"drain failed");
    mav_metrics m{};m.struct_size=sizeof(m);m.version=MAV_ABI_VERSION;require(mav_decoder_get_metrics(decoder.get(),&m)==MAV_OK,"metrics failed");
    require(!sink.failed&&sink.completed==inputs.size()&&sink.outputs==f.displays&&sink.existing==f.existing,"terminal/output accounting mismatch");
    require(sink.no_display==(split?f.hidden:0)&&!m.outstanding&&m.accepted==inputs.size()&&m.completed==inputs.size()&&m.hardware_validated,"capacity/hardware metrics mismatch");
    return {unsigned(inputs.size()),sink.completed,sink.outputs,sink.no_display,sink.existing,m.internal_samples,std::move(sink.pixels)};
}
struct Difference {unsigned maximum=0;double mean=0;uint64_t samples=0;};
Difference compare(const std::vector<std::vector<uint16_t>>& native,const std::vector<uint8_t>& reference,unsigned depth) {
    size_t bytes_per_sample=depth==8?1:2,total=0;for (const auto& p:native)total+=p.size();
    require(reference.size()==total*bytes_per_sample,"software reference visible-plane byte count mismatch");
    Difference d;uint64_t sum=0;size_t offset=0;
    for (const auto& p:native) for (auto value:p) {
        unsigned ref=depth==8?reference[offset++]:le16(reference.data()+offset);
        if (depth!=8) offset+=2;
        unsigned error=unsigned(std::abs(int(value)-int(ref)));d.maximum=std::max(d.maximum,error);sum+=error;
    }
    d.samples=total;d.mean=double(sum)/total;return d;
}
}
int main(int argc,char** argv) {
    try {
        require(argc==4,"usage: mav-av1-accounting input.ivf software-reference.i420 results.json");
        Fixture fixture=load(argv[1]);auto reference=read(argv[2]);
        auto grouped=run(fixture,false,3);auto split=run(fixture,true,1);
        require(grouped.pixels==split.pixels,"whole-temporal-unit vs split-coded-frame visible planes differ");
        auto difference=compare(grouped.pixels,reference,fixture.depth);
        require(difference.maximum<=2&&difference.mean<=0.10,"native visible planes disagree with software decoder of same bitstream");
        std::ofstream json(argv[3]);require(bool(json),"cannot create result file");
        json<<"{\n  \"status\": \"PASS\", \"codec\": \"av1\", \"bit_depth\": "<<fixture.depth<<", \"width\": "<<fixture.width<<", \"height\": "<<fixture.height
            <<",\n  \"hardware_required_and_validated\": true, \"temporal_units\": "<<fixture.packets.size()<<", \"multiple_frame_units\": "<<fixture.multi
            <<",\n  \"grouped\": {\"accepted\": "<<grouped.accepted<<", \"completed\": "<<grouped.completed<<", \"displayed\": "<<grouped.outputs<<", \"internal_samples\": "<<grouped.internal_samples<<", \"inflight\": 3},"
            <<"\n  \"split\": {\"accepted\": "<<split.accepted<<", \"completed\": "<<split.completed<<", \"displayed\": "<<split.outputs<<", \"no_display\": "<<split.no_display<<", \"internal_samples\": "<<split.internal_samples<<", \"inflight\": 1},"
            <<"\n  \"existing_frame_events\": "<<grouped.existing<<", \"outstanding_after_drain\": 0, \"whole_vs_split_exact_match\": true,"
            <<"\n  \"software_reference\": {\"decoder\": \"libaom aomdec\", \"sample_count\": "<<difference.samples<<", \"max_error\": "<<difference.maximum<<", \"mean_error\": "<<difference.mean
            <<", \"max_error_limit\": 2, \"mean_error_limit\": 0.10},\n  \"performance\": \"NOT MEASURED - correctness sink maps visible planes\"\n}\n";
        std::cout<<"PASS AV1 "<<fixture.depth<<"-bit accounting: "<<grouped.completed<<" grouped, "<<split.completed<<" split, "<<split.no_display<<" no-display, "<<grouped.existing<<" existing; software max/mean error "<<difference.maximum<<"/"<<difference.mean<<"\n";return 0;
    } catch (const std::exception& e) {std::cerr<<"FAIL AV1 accounting: "<<e.what()<<"\n";return 1;}
}
