#include "moonlight_apple_video/decoder.h"
#include "bitstream.hpp"
#include "fixture_support.hpp"
#include <CoreVideo/CoreVideo.h>
#include <cstring>
#include <iostream>
#include <memory>
#include <mutex>

// This hardware correctness test deliberately maps visible planes in its sink.
// Its timings must never be used as decoder performance measurements.
namespace {
void require(bool condition,const std::string& message) {
    if (!condition) throw std::runtime_error(message);
}
struct Packet { std::vector<uint8_t> bytes; mav::Format format; };
struct Stream {
    std::string name,path,hash; std::vector<Packet> packets;
};
Stream load_probe(const std::string& path,mav::Codec codec,unsigned depth) {
    Stream stream{depth==8?"720p SDR":"720p 10-bit",path,"",{}};
    auto bytes=fixture::read(path,MAV_MAX_ACCESS_UNIT_BYTES);
    mav::Bitstream parser(codec);mav::Prepared prepared;std::string error;
    require(parser.prepare(bytes.data(),bytes.size(),prepared,error)==mav::ParseResult::Ok,"probe parse: "+error);
    require(prepared.random_access&&prepared.displayed_frames==1,"probe must contain one real random-access image");
    require(prepared.format.width==1280&&prepared.format.height==720&&prepared.format.bit_depth==depth,"probe dimensions/depth mismatch");
    stream.hash=fixture::sha(bytes.data(),bytes.size());
    stream.packets.push_back({std::move(bytes),prepared.format});return stream;
}
Stream load_manifest(const std::string& path,mav::Codec codec,unsigned depth) {
    auto manifest=fixture::load(path);
    require(manifest.codec==(codec==mav::Codec::AV1?"av1":"hevc")&&manifest.depth==depth,"manifest codec/depth mismatch");
    require(manifest.width==1920&&manifest.height==1080&&manifest.units.size()>=4,"test requires a real 1080p fixture with at least four frames");
    Stream stream{depth==8?"1080p SDR":"1080p HDR",path,manifest.hash,{}};
    mav::Bitstream parser(codec);
    for (size_t i=0;i<4;++i) {
        const auto& unit=manifest.units[i];const uint8_t* begin=manifest.payload.data()+unit.offset;
        mav::Prepared prepared;std::string error;
        require(parser.prepare(begin,unit.size,prepared,error)==mav::ParseResult::Ok,"fixture parse: "+error);
        require(prepared.displayed_frames==1&&(i||prepared.random_access),"fixture must begin at random access and display one image per AU");
        const auto& f=prepared.format;
        require(f.width==manifest.width&&f.height==manifest.height&&f.bit_depth==depth,"fixture bitstream disagrees with manifest format");
        require(f.color.description_valid&&f.color.primaries==(depth==10?9:1)&&f.color.transfer==(depth==10?16:1)&&f.color.matrix==(depth==10?9:1),"fixture lacks expected in-band SDR/HDR color description");
        require(f.color.mastering_valid==(depth==10)&&f.color.content_light_valid==(depth==10),"fixture lacks expected in-band static HDR metadata");
        if(i) require(f==stream.packets.front().format,"fixture unexpectedly changes configuration within the initial four AUs");
        stream.packets.push_back({std::vector<uint8_t>(begin,begin+unit.size),f});
    }
    return stream;
}
std::string manifest_path(const std::string& root,const std::string& codec,const std::string& variant) {
    auto canonical=root+"/"+codec+"-"+variant+"-1920x1080p120-120/manifest.json";
    if([[NSFileManager defaultManager]fileExistsAtPath:fixture::ns(canonical)])return canonical;
    auto legacy=root+"/"+codec+"-"+variant+"/manifest.json";
    require([[NSFileManager defaultManager]fileExistsAtPath:fixture::ns(legacy)],"missing fixture "+canonical+"; run scripts/validate.sh --suite offline-hardware first");
    return legacy;
}
std::string visible_hash(CVPixelBufferRef pixel,const mav::Format& expected) {
    require(pixel&&CVPixelBufferGetWidth(pixel)==expected.width&&CVPixelBufferGetHeight(pixel)==expected.height,"retained buffer dimensions changed");
    require(CVPixelBufferGetPlaneCount(pixel)==2&&CVPixelBufferGetIOSurface(pixel),"output requires two IOSurface-backed planes");
    require(CVPixelBufferLockBaseAddress(pixel,kCVPixelBufferLock_ReadOnly)==kCVReturnSuccess,"cannot lock retained pixel buffer");
    struct Unlock { CVPixelBufferRef pixel;~Unlock(){CVPixelBufferUnlockBaseAddress(pixel,kCVPixelBufferLock_ReadOnly);} } unlock{pixel};
    CC_SHA256_CTX hash;CC_SHA256_Init(&hash);
    size_t row_bytes=size_t(expected.width)*(expected.bit_depth==10?2:1);
    for(size_t plane=0;plane<2;++plane) {
        size_t rows=expected.height/(plane?2:1),stride=CVPixelBufferGetBytesPerRowOfPlane(pixel,plane);
        auto data=static_cast<const uint8_t*>(CVPixelBufferGetBaseAddressOfPlane(pixel,plane));
        require(data&&stride>=row_bytes&&CVPixelBufferGetHeightOfPlane(pixel,plane)==rows,"invalid visible plane layout");
        for(size_t row=0;row<rows;++row) CC_SHA256_Update(&hash,data+row*stride,CC_LONG(row_bytes));
    }
    uint8_t digest[CC_SHA256_DIGEST_LENGTH];CC_SHA256_Final(digest,&hash);
    std::string text;const char* digits="0123456789abcdef";
    for(auto b:digest){text+=digits[b>>4];text+=digits[b&15];}return text;
}
void check_color(const mav_color& actual,const mav::Color& expected) {
    if(expected.description_valid) require((actual.valid&MAV_COLOR_DESCRIPTION)&&actual.primaries==expected.primaries&&actual.transfer==expected.transfer&&actual.matrix==expected.matrix,"output ISO color description mismatch");
    if(expected.range_valid) require((actual.valid&MAV_COLOR_RANGE)&&bool(actual.full_range)==expected.full_range,"output color range mismatch");
    if(expected.chroma_position_valid) require((actual.valid&MAV_COLOR_CHROMA_LOCATION)&&actual.chroma_location==expected.chroma_position,"output chroma location mismatch");
    require(bool(actual.valid&MAV_COLOR_MASTERING)==expected.mastering_valid,"mastering metadata was lost or leaked from a previous configuration");
    require(bool(actual.valid&MAV_COLOR_CONTENT_LIGHT)==expected.content_light_valid,"content-light metadata was lost or leaked from a previous configuration");
    if(expected.mastering_valid) require(!std::memcmp(actual.mastering,expected.mastering.data(),24),"mastering metadata byte mismatch");
    if(expected.content_light_valid) require(!std::memcmp(actual.content_light,expected.content_light.data(),4),"content-light metadata byte mismatch");
}
struct Input { const Packet* packet;size_t stage;uint64_t generation; };
struct Record { bool received=false;CVPixelBufferRef retained=nullptr;uint64_t generation=0;uint32_t pixel_format=0;std::string hash; };
struct Sink {
    const std::vector<Input>& inputs;std::vector<Record> records;std::mutex mutex;std::vector<std::string> errors;
    explicit Sink(const std::vector<Input>& in):inputs(in),records(in.size()){}
    ~Sink(){for(auto& r:records)if(r.retained)CVPixelBufferRelease(r.retained);}
};
void completion(void* context,const mav_completion* c) {
    auto& sink=*static_cast<Sink*>(context);CVPixelBufferRef retained=nullptr;
    try {
        require(c->frame_id<sink.inputs.size(),"unknown completion frame ID");
        const auto& input=sink.inputs[c->frame_id];const auto& format=input.packet->format;
        require(c->caller_context==&input&&c->generation==input.generation,"caller identity or generation isolation mismatch");
        require(c->status==MAV_COMPLETION_OUTPUT&&c->result==MAV_OK&&c->pixel_buffer&&c->displayed_outputs==1&&c->hardware_accelerated,"submission did not produce exactly one hardware image");
        require(c->width==format.width&&c->height==format.height&&c->bit_depth==format.bit_depth,"completion dimensions/bit depth mismatch");
        bool full=format.color.range_valid&&format.color.full_range;
        uint32_t pixel_format=format.bit_depth==10?(full?kCVPixelFormatType_420YpCbCr10BiPlanarFullRange:kCVPixelFormatType_420YpCbCr10BiPlanarVideoRange):(full?kCVPixelFormatType_420YpCbCr8BiPlanarFullRange:kCVPixelFormatType_420YpCbCr8BiPlanarVideoRange);
        require(c->pixel_format==pixel_format&&CVPixelBufferGetPixelFormatType(c->pixel_buffer)==pixel_format,"output pixel format mismatch after reconfiguration");
        require(c->pts.valid&&c->pts.value==int64_t(c->frame_id)&&c->pts.timescale==60,"timestamp identity mismatch");
        check_color(c->color,format.color);
        retained=CVPixelBufferRetain(c->pixel_buffer);auto hash=visible_hash(retained,format);
        std::lock_guard<std::mutex> lock(sink.mutex);auto& record=sink.records[c->frame_id];
        require(!record.received,"duplicate terminal completion");record.received=true;record.retained=retained;retained=nullptr;
        record.generation=c->generation;record.pixel_format=c->pixel_format;record.hash=std::move(hash);
    } catch(const std::exception& e) {
        if(retained)CVPixelBufferRelease(retained);
        std::lock_guard<std::mutex> lock(sink.mutex);sink.errors.push_back(e.what());
    } catch(...) {
        if(retained)CVPixelBufferRelease(retained);
        std::lock_guard<std::mutex> lock(sink.mutex);sink.errors.push_back("unknown callback exception");
    }
}
mav_metrics metrics(mav_decoder* decoder) {
    mav_metrics result{};result.struct_size=sizeof(result);result.version=MAV_ABI_VERSION;
    require(mav_decoder_get_metrics(decoder,&result)==MAV_OK,"metrics query failed");return result;
}
NSDictionary* run(mav_codec codec,const std::string& probes,const std::string& fixtures) {
    bool av1=codec==MAV_CODEC_AV1;auto kind=av1?mav::Codec::AV1:mav::Codec::HEVC;
    std::string name=av1?"av1":"hevc";
    Stream small8=load_probe(probes+(av1?"/AV1Main8.bin":"/HEVCMain.bin"),kind,8);
    Stream small10=load_probe(probes+(av1?"/AV1Main10.bin":"/HEVCMain10.bin"),kind,10);
    Stream large8=load_manifest(manifest_path(fixtures,name,"sdr8"),kind,8);
    Stream large10=load_manifest(manifest_path(fixtures,name,"hdr10"),kind,10);
    std::vector<const Stream*> stages{&small8,&large8,&large10,&small10,&large8,&small8,&large10};
    std::vector<Input> inputs;
    for(size_t stage=0;stage<stages.size();++stage) {
        if(stage)require(!(stages[stage]->packets[0].format==stages[stage-1]->packets[0].format),"test stage did not change the codec configuration");
        for(const auto& packet:stages[stage]->packets) inputs.push_back({&packet,stage,stage+1});
        // Repeating the identical random-access AU and its parameter sets must
        // not change generation or recreate an otherwise compatible session.
        inputs.push_back({&stages[stage]->packets[0],stage,stage+1});
    }
    Sink sink(inputs);mav_config config;mav_config_default(&config,codec);
    config.width=0;config.height=0;config.bit_depth=0;config.max_frames_in_flight=3;
    config.completion=completion;config.context=&sink;
    mav_decoder* raw=nullptr;require(mav_decoder_create(&config,&raw)==MAV_OK,"wildcard decoder create failed");
    std::unique_ptr<mav_decoder,decltype(&mav_decoder_destroy)> decoder(raw,mav_decoder_destroy);
    uint64_t would_block=0,changed_format_would_block=0,accepted=0;
    for(size_t i=0;i<inputs.size();++i) {
        const auto& input=inputs[i];mav_span span{input.packet->bytes.data(),input.packet->bytes.size()};
        mav_access_unit unit;mav_access_unit_default(&unit,codec);unit.spans=&span;unit.span_count=1;
        unit.frame_id=i;unit.caller_context=const_cast<Input*>(&input);unit.pts={int64_t(i),60,1};unit.dts=unit.pts;unit.duration={1,60,1};
        bool transition=i&&input.stage!=inputs[i-1].stage;
        mav_result result=mav_decoder_submit_copy(decoder.get(),&unit);
        if(result==MAV_WOULD_BLOCK) {
            ++would_block;changed_format_would_block+=transition;
            // Drain is permitted by the public configuration-change contract;
            // reset must never be necessary for these in-band RA transitions.
            require(mav_decoder_drain(decoder.get())==MAV_OK,"transition/capacity drain failed");
            result=mav_decoder_submit_copy(decoder.get(),&unit);
        }
        require(result==MAV_OK,"submit "+name+" stage "+std::to_string(input.stage)+": "+mav_result_string(result));++accepted;
        auto current=metrics(decoder.get());
        require(current.session_creations==input.stage+1&&current.generation==input.generation,"unchanged sequence recreated a session or changed sequence retained the old generation");
        require(current.accepted==accepted,"synchronous rejection was incorrectly accepted");
    }
    require(mav_decoder_drain(decoder.get())==MAV_OK,"final drain failed");
    auto final=metrics(decoder.get());
    {std::lock_guard<std::mutex> lock(sink.mutex);require(sink.errors.empty(),sink.errors.empty()?"":sink.errors.front());}
    require(final.accepted==inputs.size()&&final.completed==inputs.size()&&final.displayed==inputs.size()&&!final.failed&&!final.cancelled&&!final.dropped&&!final.outstanding&&final.hardware_validated,"hardware/terminal accounting mismatch");
    for(size_t i=0;i<inputs.size();++i)require(sink.records[i].received&&sink.records[i].hash==visible_hash(sink.records[i].retained,inputs[i].packet->format),"retained pixels changed across an implicit configuration change");
    require(mav_decoder_reset(decoder.get())==MAV_OK,"final reset failed");
    require(metrics(decoder.get()).generation==stages.size()+1,"explicit reset did not isolate the next generation");
    require(mav_decoder_destroy(decoder.release())==MAV_OK,"decoder destruction failed");
    NSMutableArray* frames=[NSMutableArray array];
    for(size_t i=0;i<inputs.size();++i) {
        const auto& input=inputs[i];const auto& f=input.packet->format;const auto& r=sink.records[i];
        require(r.hash==visible_hash(r.retained,f),"retained pixels changed after reset/destruction");
        [frames addObject:@{@"frame_id":@(i),@"stage":@(input.stage),@"generation":@(r.generation),@"width":@(f.width),@"height":@(f.height),@"bit_depth":@(f.bit_depth),@"pixel_format":@(r.pixel_format),@"primaries":@(f.color.primaries),@"transfer":@(f.color.transfer),@"matrix":@(f.color.matrix),@"mastering_valid":@(f.color.mastering_valid),@"content_light_valid":@(f.color.content_light_valid),@"visible_plane_sha256":fixture::ns(r.hash)}];
    }
    NSMutableArray* provenance=[NSMutableArray array];
    for(auto stream:{&small8,&small10,&large8,&large10})[provenance addObject:@{@"path":fixture::ns(stream->path),@"sha256":fixture::ns(stream->hash)}];
    std::cout<<"PASS "<<name<<": "<<inputs.size()<<" hardware outputs, "<<stages.size()-1<<" implicit format changes, "<<changed_format_would_block<<" pending transition retries; retained pixels stable\n";
    return @{@"status":@"PASS",@"codec":fixture::ns(name),@"accepted":@(accepted),@"completed":@(final.completed),@"displayed":@(final.displayed),@"session_creations":@(final.session_creations),@"implicit_reconfigurations":@(stages.size()-1),@"generation_before_final_reset":@(final.generation),@"repeated_sequence_preserved_generation":@YES,@"reset_calls_during_transitions":@0,@"would_block":@(would_block),@"changed_format_would_block":@(changed_format_would_block),@"hardware_required_and_validated":@YES,@"iosurface_verified":@YES,@"hdr_metadata_and_sdr_clear_verified":@YES,@"retained_visible_planes_stable_after_reconfiguration_reset_destroy":@YES,@"outstanding":@(final.outstanding),@"fixtures":provenance,@"frames":frames};
}
}
int main(int argc,char** argv) {@autoreleasepool {
    std::string output=argc==4?argv[3]:"results/reconfiguration.json";
    try {
        require(argc==4,"usage: mav-reconfiguration probe-directory generated-fixtures-directory results.json");
        [[NSFileManager defaultManager]createDirectoryAtPath:fixture::ns(output).stringByDeletingLastPathComponent withIntermediateDirectories:YES attributes:nil error:nil];
        auto av1=run(MAV_CODEC_AV1,argv[1],argv[2]);auto hevc=run(MAV_CODEC_HEVC,argv[1],argv[2]);
        fixture::json(output,@{@"schema_version":@1,@"status":@"PASS",@"os":NSProcessInfo.processInfo.operatingSystemVersionString,@"wildcard_dimensions_and_bit_depth":@YES,@"results":@[av1,hevc],@"performance":@"NOT MEASURED: correctness sink hashes visible planes"});return 0;
    }catch(const std::exception& e){
        try{fixture::json(output,@{@"schema_version":@1,@"status":@"FAIL",@"reason":fixture::ns(e.what())});}catch(...){}
        std::cerr<<"FAIL reconfiguration: "<<e.what()<<"\n";return 1;
    }
}}
