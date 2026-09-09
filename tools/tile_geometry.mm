#include "fixture_support.hpp"
#include <aom/aom_decoder.h>
#include <aom/aomdx.h>
#include <cstring>
#include <iostream>
#include <map>

using namespace fixture;
static uint64_t little(const uint8_t* p,unsigned bytes) {
    uint64_t result=0;for(unsigned i=0;i<bytes;++i)result|=uint64_t(p[i])<<(8*i);return result;
}
int main(int argc,char** argv){@autoreleasepool{
    aom_codec_ctx_t decoder{};bool initialized=false;std::string output;
    NSMutableDictionary* report=[@{@"schema_version":@1,@"tool":@"mav-tile-geometry",@"status":@"FAIL",@"control":@"AOMD_GET_TILE_INFO",@"libaom_version":ns(aom_codec_version_str()),@"timing_measured":@NO} mutableCopy];
    NSMutableArray* frames=[NSMutableArray new];report[@"frames"]=frames;
    try {
        std::map<std::string,std::string> options;
        for(int i=1;i<argc;++i){
            std::string key=argv[i];
            if(key=="--help"){
                std::cout<<"mav-tile-geometry --ivf saved.ivf --expect-columns 1|2|4 --expect-rows 1 --output tile-geometry.json\nOffline software decode using public libaom; counts are actual tile counts, not log2.\n";return 0;
            }
            if(key!="--ivf"&&key!="--expect-columns"&&key!="--expect-rows"&&key!="--output")throw std::runtime_error("unknown option: "+key);
            if(i+1>=argc||options.count(key))throw std::runtime_error("missing value or duplicate option: "+key);
            options[key]=argv[++i];
        }
        output=options["--output"];
        if(output.empty()||options["--ivf"].empty())throw std::runtime_error("--ivf and --output required");
        auto count=[&](const char* key){auto text=options[key];if(text.empty()||text.find_first_not_of("0123456789")!=std::string::npos)throw std::runtime_error(std::string("invalid count: ")+key);auto n=std::stoul(text);if(n<1||n>64)throw std::runtime_error("expected tile count must be 1..64");return int(n);};
        const int expectedColumns=count("--expect-columns"),expectedRows=count("--expect-rows");
        report[@"expected_columns"]=@(expectedColumns);report[@"expected_rows"]=@(expectedRows);
#if !defined(AOM_CTRL_AOMD_GET_TILE_INFO) || !defined(AOMD_CTRL_AOMD_GET_SHOW_EXISTING_FRAME_FLAG) || !defined(AOM_CTRL_AOMD_GET_SHOW_FRAME_FLAG)
        report[@"status"]=@"UNAVAILABLE";throw std::runtime_error("public AOMD_GET_TILE_INFO is unavailable in these libaom headers");
#else
        auto data=read(options["--ivf"]);
        if(data.size()<32||memcmp(data.data(),"DKIF",4)||little(data.data()+4,2)!=0||little(data.data()+6,2)!=32||memcmp(data.data()+8,"AV01",4))throw std::runtime_error("requires version-0 AV1 IVF with 32-byte header");
        const auto width=little(data.data()+12,2),height=little(data.data()+14,2),declaredFrames=little(data.data()+24,4);
        if(!width||!height||!little(data.data()+16,4)||!little(data.data()+20,4))throw std::runtime_error("invalid IVF dimensions/rate");
        report[@"ivf_sha256"]=ns(sha(data.data(),data.size()));report[@"ivf_path"]=ns(options["--ivf"]);
        report[@"width"]=@(width);report[@"height"]=@(height);report[@"declared_frames"]=@(declaredFrames);
        aom_codec_dec_cfg_t config{};config.threads=1;
        auto status=aom_codec_dec_init(&decoder,aom_codec_av1_dx(),&config,0);
        if(status!=AOM_CODEC_OK)throw std::runtime_error(std::string("libaom init: ")+aom_codec_err_to_string(status));
        initialized=true;size_t at=32;bool matches=true,consistent=true;NSDictionary* firstGeometry=nil;
        while(at<data.size()){
            if(data.size()-at<12)throw std::runtime_error("truncated IVF packet header");
            auto length=little(data.data()+at,4),pts=little(data.data()+at+4,8);at+=12;
            if(!length||length>(64u<<20)||length>data.size()-at)throw std::runtime_error("invalid IVF packet size");
            status=aom_codec_decode(&decoder,data.data()+at,size_t(length),nullptr);at+=size_t(length);
            if(status!=AOM_CODEC_OK)throw std::runtime_error(std::string("libaom decode: ")+aom_codec_error(&decoder));
            aom_codec_iter_t iterator=nullptr;unsigned outputs=0;
            while(auto* image=aom_codec_get_frame(&decoder,&iterator)){
                if(image->d_w!=width||image->d_h!=height)throw std::runtime_error("decoded dimensions differ from IVF");
                ++outputs;
            }
            if(outputs!=1)throw std::runtime_error("requires exactly one displayed frame per low-delay IVF packet");
            aom_tile_info info{};status=aom_codec_control(&decoder,AOMD_GET_TILE_INFO,&info);
            if(status!=AOM_CODEC_OK)throw std::runtime_error(std::string("AOMD_GET_TILE_INFO: ")+aom_codec_err_to_string(status));
            int showExisting=0,showFrame=0;
            if(aom_codec_control(&decoder,AOMD_GET_SHOW_EXISTING_FRAME_FLAG,&showExisting)!=AOM_CODEC_OK||aom_codec_control(&decoder,AOMD_GET_SHOW_FRAME_FLAG,&showFrame)!=AOM_CODEC_OK||showExisting||!showFrame)
                throw std::runtime_error("requires newly decoded displayed frames; show-existing/hidden frame geometry is not attributed");
            if(info.tile_columns<1||info.tile_columns>AOM_MAX_TILE_COLS||info.tile_rows<1||info.tile_rows>AOM_MAX_TILE_ROWS)throw std::runtime_error("libaom returned invalid tile dimensions");
            NSMutableArray* widths=[NSMutableArray new];NSMutableArray* heights=[NSMutableArray new];
            for(int i=0;i<info.tile_columns;++i)[widths addObject:@(info.tile_widths[i])];
            for(int i=0;i<info.tile_rows;++i)[heights addObject:@(info.tile_heights[i])];
            NSDictionary* geometry=@{@"columns":@(info.tile_columns),@"rows":@(info.tile_rows),@"widths_in_superblocks":widths,@"heights_in_superblocks":heights,@"tile_groups":@(info.num_tile_groups)};
            if(!firstGeometry)firstGeometry=geometry;else consistent&=[firstGeometry isEqual:geometry];
            bool match=info.tile_columns==expectedColumns&&info.tile_rows==expectedRows;matches&=match;
            [frames addObject:@{@"index":@(frames.count),@"ivf_timestamp":@(pts),@"control_status":@(status),@"geometry":geometry,@"matches_expected_counts":@(match)}];
        }
        if(!frames.count||(declaredFrames&&declaredFrames!=frames.count))throw std::runtime_error("IVF frame count mismatch");
        status=aom_codec_decode(&decoder,nullptr,0,nullptr);aom_codec_iter_t iterator=nullptr;
        if(status!=AOM_CODEC_OK||aom_codec_get_frame(&decoder,&iterator))throw std::runtime_error("unexpected delayed output at flush");
        report[@"decoded_frames"]=@(frames.count);report[@"all_frames_match_expected_counts"]=@(matches);
        report[@"all_frame_geometry_consistent"]=@(consistent);
        if(!matches||!consistent)throw std::runtime_error("actual tile geometry differs from requested counts or varies across frames");
        report[@"status"]=@"PASS";json(output,report);
        aom_codec_destroy(&decoder);initialized=false;
        std::cout<<"PASS actual AV1 tiles "<<expectedColumns<<"x"<<expectedRows<<" across "<<frames.count<<" frames: "<<output<<"\n";return 0;
#endif
    }catch(const std::exception& error){
        if(initialized)aom_codec_destroy(&decoder);
        report[@"error"]=ns(error.what());
        if(!output.empty()){try{json(output,report);}catch(const std::exception& writeError){std::cerr<<writeError.what()<<"\n";}}
        std::cerr<<"BLOCKED/FAIL: "<<error.what()<<"\n";return 1;
    }
}}
