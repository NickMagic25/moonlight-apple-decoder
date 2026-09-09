#import <VideoToolbox/VideoToolbox.h>
#include "fixture_support.hpp"
#include "bitstream.hpp"
#include <mutex>
#include <iostream>
#include <map>
#include <cstring>
#include <cstdio>

using namespace fixture;
struct LayoutOptions { uint32_t columns=1,rows=0; bool rowsExplicit=false,psnr=false,planOnly=false,queryHevc=false; };
static NSDictionary* copiedProperty(VTCompressionSessionRef session,CFStringRef key) {
    CFTypeRef value=nullptr; auto status=VTSessionCopyProperty(session,key,nullptr,&value);
    id object=value?CFBridgingRelease(value):nil;
    // Keep type-stable scalar readback; preserve descriptions of richer values.
    if(object && ![object isKindOfClass:NSString.class] && ![object isKindOfClass:NSNumber.class]) object=[object description];
    return @{@"status":@(status),@"value":object?:NSNull.null};
}
static OSStatus hevcLayoutReport(VTCompressionSessionRef session,NSMutableDictionary* settings) {
    CFDictionaryRef supported=nullptr;
    auto status=VTSessionCopySupportedPropertyDictionary(session,&supported);
    NSDictionary* properties=CFBridgingRelease(supported);
    NSMutableArray* keys=[NSMutableArray new]; NSMutableDictionary* layout=[NSMutableDictionary new];
    for(NSString* key in properties) {
        [keys addObject:key]; NSString* lower=key.lowercaseString;
        if([lower containsString:@"slice"]||[lower containsString:@"tile"])
            layout[key]=@{@"supported_property_description":[properties[key] description],@"readback":copiedProperty(session,(__bridge CFStringRef)key)};
    }
    [keys sortUsingSelector:@selector(compare:)];
    settings[@"hevc_layout"]=@{@"status":@"UNAVAILABLE_PUBLIC_CONTROL",@"reason":@"The macOS 26.5 public VTCompressionProperties.h declares MaxH264SliceBytes for H.264 only; no HEVC slice/tile setter. Advertised private keys are queried, never set.",@"supported_properties_status":@(status),@"supported_keys":keys,@"advertised_slice_tile_properties":layout,@"control_set_status":NSNull.null};
    settings[@"hardware_readback"]=copiedProperty(session,kVTCompressionPropertyKey_UsingHardwareAcceleratedVideoEncoder);
    settings[@"encoder_id"]=copiedProperty(session,kVTCompressionPropertyKey_EncoderID);
    return status;
}
struct Encoded {uint64_t id;std::vector<uint8_t> data;};
struct EncodeState {std::mutex lock;std::vector<Encoded> units;std::string error;};
static void output(void* context,void* frame,OSStatus status,VTEncodeInfoFlags flags,CMSampleBufferRef sample){
    auto& s=*static_cast<EncodeState*>(context);std::lock_guard<std::mutex>g(s.lock);
    if(status||!sample){s.error="VT encoder callback status "+std::to_string(status);return;}
    Encoded e{uint64_t(reinterpret_cast<uintptr_t>(frame))-1,{}};
    auto add=[&](const uint8_t*p,size_t n){e.data.insert(e.data.end(),{0,0,0,1});e.data.insert(e.data.end(),p,p+n);};
    CMFormatDescriptionRef format=CMSampleBufferGetFormatDescription(sample);
    size_t count=0,length=0;int prefix=0;const uint8_t*ps=nullptr;
    status=CMVideoFormatDescriptionGetHEVCParameterSetAtIndex(format,0,&ps,&length,&count,&prefix);
    if(status||prefix<1||prefix>4){s.error="cannot extract HEVC parameter sets";return;}
    // Retain PS on every random access; using sample attachment preserves actual encoder decisions.
    auto attachments=CMSampleBufferGetSampleAttachmentsArray(sample,false);
    bool key=!attachments||!CFDictionaryContainsKey((CFDictionaryRef)CFArrayGetValueAtIndex(attachments,0),kCMSampleAttachmentKey_NotSync);
    if(key)for(size_t i=0;i<count;++i){status=CMVideoFormatDescriptionGetHEVCParameterSetAtIndex(format,i,&ps,&length,nullptr,nullptr);if(status){s.error="parameter set extraction failed";return;}add(ps,length);}
    auto block=CMSampleBufferGetDataBuffer(sample);size_t n=CMBlockBufferGetDataLength(block);std::vector<uint8_t>b(n);
    if(CMBlockBufferCopyDataBytes(block,0,n,b.data())){s.error="encoder block copy failed";return;}
    size_t at=0;while(at<n){if(n-at<size_t(prefix)){s.error="truncated encoder length";return;}size_t len=0;for(int i=0;i<prefix;++i)len=len*256+b[at++];if(!len||len>n-at){s.error="invalid encoder length";return;}add(b.data()+at,len);at+=len;}
    s.units.push_back(std::move(e));(void)flags;
}
static void property(VTCompressionSessionRef s,CFStringRef k,CFTypeRef v){auto e=VTSessionSetProperty(s,k,v);if(e)throw std::runtime_error("VT encoder property "+utf((__bridge NSString*)k)+" rejected: "+std::to_string(e));}
static std::vector<Encoded> hevc(const std::string& out,uint32_t w,uint32_t h,uint32_t depth,uint32_t fps,uint32_t frames,uint32_t gop,const LayoutOptions& options,NSMutableDictionary* settings){
    EncodeState state;VTCompressionSessionRef session=nullptr;
    NSDictionary* spec=@{(__bridge NSString*)kVTVideoEncoderSpecification_RequireHardwareAcceleratedVideoEncoder:@YES};
    auto status=VTCompressionSessionCreate(nullptr,w,h,kCMVideoCodecType_HEVC,(__bridge CFDictionaryRef)spec,nullptr,nullptr,output,&state,&session);
    settings[@"session_create_status"]=@(status);
    json(out+"/encoder-settings.json",settings);
    if(status)throw std::runtime_error("BLOCKED HEVC hardware encoder creation "+std::to_string(status));
    try {
        property(session,kVTCompressionPropertyKey_ProfileLevel,depth==10?kVTProfileLevel_HEVC_Main10_AutoLevel:kVTProfileLevel_HEVC_Main_AutoLevel);
        auto queryStatus=hevcLayoutReport(session,settings); json(out+"/encoder-settings.json",settings);
        if(options.queryHevc&&queryStatus)throw std::runtime_error("HEVC supported-property query failed: "+std::to_string(queryStatus));
        if(options.queryHevc){VTCompressionSessionInvalidate(session);CFRelease(session);return {};}
        property(session,kVTCompressionPropertyKey_RealTime,kCFBooleanTrue);property(session,kVTCompressionPropertyKey_AllowFrameReordering,kCFBooleanFalse);
        property(session,kVTCompressionPropertyKey_ExpectedFrameRate,(__bridge CFNumberRef)@(fps));property(session,kVTCompressionPropertyKey_MaxKeyFrameInterval,(__bridge CFNumberRef)@(gop));
        property(session,kVTCompressionPropertyKey_AverageBitRate,(__bridge CFNumberRef)@(std::max(uint64_t(1000000),uint64_t(w)*h*fps/3)));
        property(session,kVTCompressionPropertyKey_ColorPrimaries,depth==10?kCVImageBufferColorPrimaries_ITU_R_2020:kCVImageBufferColorPrimaries_ITU_R_709_2);
        property(session,kVTCompressionPropertyKey_TransferFunction,depth==10?kCVImageBufferTransferFunction_SMPTE_ST_2084_PQ:kCVImageBufferTransferFunction_ITU_R_709_2);
        property(session,kVTCompressionPropertyKey_YCbCrMatrix,depth==10?kCVImageBufferYCbCrMatrix_ITU_R_2020:kCVImageBufferYCbCrMatrix_ITU_R_709_2);
        if(depth==10){auto m=mastering();uint8_t cll[]={3,232,1,144};property(session,kVTCompressionPropertyKey_MasteringDisplayColorVolume,(__bridge CFDataRef)[NSData dataWithBytes:m.data() length:m.size()]);property(session,kVTCompressionPropertyKey_ContentLightLevelInfo,(__bridge CFDataRef)[NSData dataWithBytes:cll length:4]);}
        status=VTCompressionSessionPrepareToEncodeFrames(session);if(status)throw std::runtime_error("prepare encoder "+std::to_string(status));
        for(uint32_t f=0;f<frames;++f){
            CVPixelBufferRef pixel=nullptr;NSDictionary* attrs=@{(__bridge NSString*)kCVPixelBufferIOSurfacePropertiesKey:@{}};
            status=CVPixelBufferCreate(nullptr,w,h,depth==10?kCVPixelFormatType_420YpCbCr10BiPlanarVideoRange:kCVPixelFormatType_420YpCbCr8BiPlanarVideoRange,(__bridge CFDictionaryRef)attrs,&pixel);
            if(status)throw std::runtime_error("source pixel buffer "+std::to_string(status));
            CVPixelBufferLockBaseAddress(pixel,0);
            auto p=(uint8_t*)CVPixelBufferGetBaseAddressOfPlane(pixel,0);auto stride=CVPixelBufferGetBytesPerRowOfPlane(pixel,0);
            for(uint32_t y=0;y<h;++y)for(uint32_t x=0;x<w;++x){auto v=luma(x,y,w,h,f,depth);if(depth==10)reinterpret_cast<uint16_t*>(p+y*stride)[x]=v<<6;else p[y*stride+x]=uint8_t(v);}
            p=(uint8_t*)CVPixelBufferGetBaseAddressOfPlane(pixel,1);stride=CVPixelBufferGetBytesPerRowOfPlane(pixel,1);
            for(uint32_t y=0;y<h/2;++y)for(uint32_t x=0;x<w;++x){if(depth==10)reinterpret_cast<uint16_t*>(p+y*stride)[x]=uint16_t(512)<<6;else p[y*stride+x]=128;}
            CVPixelBufferUnlockBaseAddress(pixel,0);
            NSDictionary* options=(f%gop==0)?@{(__bridge NSString*)kVTEncodeFrameOptionKey_ForceKeyFrame:@YES}:@{};
            status=VTCompressionSessionEncodeFrame(session,pixel,CMTimeMake(f,fps),CMTimeMake(1,fps),(__bridge CFDictionaryRef)options,reinterpret_cast<void*>(uintptr_t(f)+1),nullptr);CVPixelBufferRelease(pixel);
            if(status)throw std::runtime_error("encode frame "+std::to_string(status));
        }
        status=VTCompressionSessionCompleteFrames(session,kCMTimeInvalid);if(status)throw std::runtime_error("encoder completion "+std::to_string(status));
        if(!state.error.empty())throw std::runtime_error(state.error);
        settings[@"hardware_readback"]=copiedProperty(session,kVTCompressionPropertyKey_UsingHardwareAcceleratedVideoEncoder);
        settings[@"status"]=@"ENCODED";json(out+"/encoder-settings.json",settings);
    } catch(...) {VTCompressionSessionInvalidate(session);CFRelease(session);throw;}
    VTCompressionSessionInvalidate(session);CFRelease(session);
    std::sort(state.units.begin(),state.units.end(),[](auto&a,auto&b){return a.id<b.id;});
    if(state.units.size()!=frames)throw std::runtime_error("encoder lost frames");
    if(depth==10){auto m=mastering();std::vector<uint8_t>rbsp={137,24};rbsp.insert(rbsp.end(),m.begin(),m.end());rbsp.insert(rbsp.end(),{144,4,3,232,1,144,0x80});std::vector<uint8_t>sei={0,0,0,1,0x4e,1};unsigned zeros=0;for(auto b:rbsp){if(zeros>=2&&b<=3){sei.push_back(3);zeros=0;}sei.push_back(b);zeros=b==0?zeros+1:0;}for(auto&u:state.units)u.data.insert(u.data.begin(),sei.begin(),sei.end());}
    return state.units;
}
static std::string run(NSString* executable,NSArray<NSString*>* args){
    NSTask*task=[NSTask new];task.executableURL=[NSURL fileURLWithPath:executable];task.arguments=args;
    NSPipe* pipe=[NSPipe pipe];task.standardOutput=pipe;task.standardError=pipe;NSError* e=nil;
    if(![task launchAndReturnError:&e])throw std::runtime_error("BLOCKED launching encoder: "+utf(e.description));
    NSData*d=[pipe.fileHandleForReading readDataToEndOfFile];[task waitUntilExit];std::string result=utf([[NSString alloc]initWithData:d encoding:NSUTF8StringEncoding]);
    if(task.terminationStatus)throw std::runtime_error("encoder failed: "+result);return result;
}
static uint64_t le(const uint8_t*p,unsigned n){uint64_t v=0;for(unsigned i=0;i<n;++i)v|=uint64_t(p[i])<<(i*8);return v;}
static std::vector<Encoded> ivf(const std::string& path,uint32_t w,uint32_t h){
    auto b=read(path);if(b.size()<32||memcmp(b.data(),"DKIF",4)||memcmp(b.data()+8,"AV01",4)||le(b.data()+6,2)!=32||le(b.data()+12,2)!=w||le(b.data()+14,2)!=h)throw std::runtime_error("unsupported IVF header");
    size_t at=32;std::vector<Encoded>r;while(at<b.size()){if(b.size()-at<12)throw std::runtime_error("truncated IVF packet");uint64_t n=le(b.data()+at,4),id=le(b.data()+at+4,8);at+=12;if(!n||n>b.size()-at)throw std::runtime_error("invalid IVF packet size");r.push_back({id,{b.begin()+at,b.begin()+at+n}});at+=n;}return r;
}
static std::vector<Encoded> av1(const std::string& out,const std::string& encoder,uint32_t w,uint32_t h,uint32_t depth,uint32_t fps,uint32_t frames,uint32_t gop,std::string& version,const LayoutOptions& options,NSMutableDictionary* settings){
    std::string raw=out+"/source.yuv",encoded=out+"/encoded.ivf";
    NSMutableArray<NSString*>* args=[NSMutableArray arrayWithArray:@[@"--codec=av1",@"--ivf",@"--i420",@"--passes=1",@"--usage=0",@"--cpu-used=6",@"--enable-tpl-model=0",@"--threads=6",@"--test-decode=fatal",@"--row-mt=1",ns("--tile-columns="+std::to_string(options.columns)),@"--lag-in-frames=0",@"--enable-keyframe-filtering=0",@"--auto-alt-ref=0",@"--end-usage=q",@"--cq-level=12",@"--disable-warning-prompt",ns("--width="+std::to_string(w)),ns("--height="+std::to_string(h)),ns("--fps="+std::to_string(fps)+"/1"),ns("--limit="+std::to_string(frames)),ns("--bit-depth="+std::to_string(depth)),ns("--input-bit-depth="+std::to_string(depth)),ns("--kf-max-dist="+std::to_string(gop)),ns("--kf-min-dist="+std::to_string(gop)),ns("--color-primaries="+std::to_string(depth==10?9:1)),ns("--transfer-characteristics="+std::to_string(depth==10?16:1)),ns("--matrix-coefficients="+std::to_string(depth==10?9:1)),ns("--output="+encoded),ns(raw)]];
    if(options.rowsExplicit)[args insertObject:ns("--tile-rows="+std::to_string(options.rows)) atIndex:0];
    if(options.psnr)[args insertObject:@"--psnr=1" atIndex:0];
    settings[@"av1_layout"]=@{@"tile_columns_log2":@(options.columns),@"tile_rows_log2":@(options.rows),@"tile_rows_argument_explicit":@(options.rowsExplicit),@"encoded_tile_geometry":NSNull.null,@"geometry_status":@"REQUEST_ONLY_NOT_BITSTREAM_VERIFIED"};
    settings[@"rate_control"]=@{@"mode":@"q",@"cq_level":@12};
    settings[@"encoder_executable"]=ns(encoder);
    settings[@"planned_arguments"]=args;settings[@"actual_arguments"]=NSNull.null;
    settings[@"psnr_requested"]=@(options.psnr);settings[@"quality"]=NSNull.null;
    json(out+"/encoder-settings.json",settings);
    if(options.planOnly)return {};
    {std::ofstream file(raw,std::ios::binary);std::vector<uint8_t> row(w*(depth==10?2:1));
        for(uint32_t f=0;f<frames;++f){for(uint32_t y=0;y<h;++y){for(uint32_t x=0;x<w;++x){auto v=luma(x,y,w,h,f,depth);if(depth==10){row[x*2]=v;row[x*2+1]=v>>8;}else row[x]=v;}file.write((char*)row.data(),row.size());}
        std::fill(row.begin(),row.end(),128);if(depth==10)for(size_t x=0;x<row.size();x+=2){row[x]=0;row[x+1]=2;}
        for(uint32_t y=0;y<h/2;++y)file.write((char*)row.data(),row.size());}if(!file)throw std::runtime_error("source write failed");}

    settings[@"status"]=@"LAUNCH_REQUESTED";settings[@"actual_arguments"]=args;
    json(out+"/encoder-arguments.json",args);json(out+"/encoder-settings.json",settings);
    auto log=run(ns(encoder),args);auto help=run(ns(encoder),@[@"--help"]);auto at=help.find("AOMedia Project AV1 Encoder");version=at==std::string::npos?"AOM encoder version unavailable":help.substr(at,help.find('\n',at)-at);write(out+"/encoder.log",{log.begin(),log.end()});
    settings[@"status"]=@"ENCODED";settings[@"encoder_version"]=ns(version);
    if(options.psnr){
        auto marker=log.rfind("PSNR (Overall/Avg/Y/U/V)");double overall=0,average=0,y=0,u=0,v=0;
        if(marker==std::string::npos||std::sscanf(log.c_str()+marker,"PSNR (Overall/Avg/Y/U/V) %lf %lf %lf %lf %lf",&overall,&average,&y,&u,&v)!=5)
            throw std::runtime_error("requested AOM PSNR summary missing; encoder.log retained");
        settings[@"quality"]=@{@"source":@"AOM encoder reconstructed pictures versus identical uncompressed input",@"metric":@"PSNR dB in encoded sample domain",@"overall_db":@(overall),@"frame_average_db":@(average),@"y_db":@(y),@"u_db":@(u),@"v_db":@(v),@"hdr_perceptual_quality_measured":@NO};
    }
    json(out+"/encoder-settings.json",settings);
    auto units=ivf(encoded,w,h);if(units.size()!=frames)throw std::runtime_error("encoder did not produce one low-delay temporal unit per input frame");
    if(depth==10){ // HDR metadata OBU, independent of genuinely encoded 10-bit pixels/sequence signaling.
        auto m=mastering(); auto put16=[&](size_t at,uint32_t x){m[at]=x>>8;m[at+1]=x;}; auto put32=[&](size_t at,uint32_t x){put16(at,x>>16);put16(at+2,x);}; put16(0,46400);put16(2,19136);put16(4,11141);put16(6,52232);put16(8,8585);put16(10,3015);put16(12,20493);put16(14,21561);put32(16,256000);put32(20,82);std::vector<uint8_t>metadata={0x2a,6,1,3,232,1,144,0x80,0x2a,26,2};metadata.insert(metadata.end(),m.begin(),m.end());metadata.push_back(0x80);
        for(auto&u:units)u.data.insert(u.data.begin(),metadata.begin(),metadata.end());
    }
    [[NSFileManager defaultManager]removeItemAtPath:ns(raw) error:nil];return units;
}
static void save(const std::string& dir,const std::string& codec,uint32_t w,uint32_t h,uint32_t depth,uint32_t fps,std::vector<Encoded>& units,const std::string& encoder,NSMutableDictionary* settings){
    mav::Bitstream parser(codec=="av1"?mav::Codec::AV1:mav::Codec::HEVC);std::vector<uint8_t>payload;NSMutableArray* access=[NSMutableArray new];uint32_t keys=0,inters=0;mav::Format final;
    for(auto&u:units){mav::Prepared p;std::string error;auto status=parser.prepare(u.data.data(),u.data.size(),p,error);if(status!=mav::ParseResult::Ok)throw std::runtime_error("encoded AU "+std::to_string(u.id)+" rejected by codec verifier: "+error);
        if(p.format.width!=w||p.format.height!=h||p.format.bit_depth!=depth||p.format.chroma!=1||p.format.profile!=(codec=="av1"?0:(depth==10?2:1)))throw std::runtime_error("encoded profile/dimensions/depth do not match request");
        if(p.displayed_frames!=1)throw std::runtime_error("generated low-delay AU must display exactly once");
        if(depth==10&&(!p.format.color.description_valid||p.format.color.primaries!=9||p.format.color.transfer!=16||p.format.color.matrix!=9))throw std::runtime_error("encoded stream missing BT2020/PQ HDR signaling");
        if(p.random_access)++keys;else ++inters;final=p.format;
        [access addObject:@{@"offset":@(payload.size()),@"length":@(u.data.size()),@"frame_id":@(u.id),@"pts":@(u.id),@"dts":@(u.id),@"duration":@1,@"random_access":@(p.random_access),@"discontinuity":@NO,@"expected_display_count":@(p.displayed_frames),@"expected_visible_frame_id":@(u.id),@"sha256":ns(sha(u.data.data(),u.data.size()))}];payload.insert(payload.end(),u.data.begin(),u.data.end());
    }
    if(units.size()>2&&!inters)throw std::runtime_error("fixture has no reference-dependent inter frames");
    if(depth==10&&(!final.color.mastering_valid||!final.color.content_light_valid))throw std::runtime_error("HDR fixture missing mastering/content light metadata");
    write(dir+"/payload.bin",payload);
    settings[@"payload_bytes"]=@(payload.size());settings[@"payload_bitrate_bps"]=@(double(payload.size())*8*fps/units.size());
    settings[@"payload_bitrate_scope"]=@"Complete codec AUs including inserted static HDR metadata; excludes IVF/container and transport";
    json(dir+"/encoder-settings.json",settings);
    NSDictionary*doc=@{@"schema_version":@1,@"codec":ns(codec),@"variant":depth==10?@"hdr10":@"sdr8",@"profile":@(final.profile),@"framing":codec=="av1"?@"av1-low-overhead-obu":@"hevc-annex-b",@"width":@(w),@"height":@(h),@"bit_depth":@(depth),@"chroma":@"420",@"frame_rate":@{@"num":@(fps),@"den":@1},@"timebase":@{@"num":@1,@"den":@(fps)},@"color":@{@"primaries":@(final.color.primaries),@"transfer":@(final.color.transfer),@"matrix":@(final.color.matrix),@"full_range":@(final.color.full_range),@"mastering_base64":[[NSData dataWithBytes:final.color.mastering.data() length:24] base64EncodedStringWithOptions:0],@"content_light_base64":[[NSData dataWithBytes:final.color.content_light.data() length:4] base64EncodedStringWithOptions:0],@"mastering_valid":@(final.color.mastering_valid),@"content_light_valid":@(final.color.content_light_valid)},@"payload_file":@"payload.bin",@"payload_sha256":ns(sha(payload.data(),payload.size())),@"access_units":access,@"generator":@{@"name":@"mav-fixture",@"pattern":@"moving-gradient-detail-square-frame-id-v1",@"encoder":ns(encoder),@"settings":settings,@"os":NSProcessInfo.processInfo.operatingSystemVersionString,@"low_delay_verified":@YES,@"random_access_count":@(keys),@"inter_count":@(inters)}};
    json(dir+"/manifest.json",doc);(void)load(dir+"/manifest.json");
    std::cout<<"PASS "<<codec<<" "<<(depth==10?"hdr10":"sdr8")<<" "<<w<<"x"<<h<<" "<<units.size()<<" AUs: "<<dir<<"/manifest.json\n";
}
int main(int argc,char**argv){@autoreleasepool{try{
    std::map<std::string,std::string> o;
    const std::unordered_set<std::string> known={"--codec","--variant","--output","--width","--height","--fps","--frames","--gop","--aomenc","--import","--av1-tile-columns","--av1-tile-rows","--aom-psnr","--plan-only","--query-hevc-layout"};
    for(int i=1;i<argc;++i){
        std::string k=argv[i];
        if(k=="--help"){
            std::cout<<"mav-fixture --codec av1|hevc --variant sdr8|hdr10 --output DIR [--width 1920 --height 1080 --fps 120 --frames 120 --gop 60 --aomenc PATH]\n"
                <<"AV1 layout: --av1-tile-columns 0..6 (log2, default 1), --av1-tile-rows 0..6 (log2, encoder default 0). Fixed CQ remains 12.\n"
                <<"--aom-psnr 0|1 (default 0) records encoder PSNR; --plan-only 1 writes AV1 arguments without encoding.\n"
                <<"--codec hevc --query-hevc-layout 1 queries the hardware encoder without encoding; no public HEVC slice/tile setter is available.\n"
                <<"Import verified capture: --import MANIFEST --output DIR\n";
            return 0;
        }
        if(!known.count(k))throw std::runtime_error("unknown option: "+k);
        if(i+1>=argc)throw std::runtime_error("option requires value: "+k);
        if(o.count(k))throw std::runtime_error("duplicate option: "+k);
        o[k]=argv[++i];
    }
    auto val=[&](const std::string& k,const std::string& d){return o.count(k)?o[k]:d;};
    auto number=[&](const std::string& k,uint32_t fallback,uint32_t max){
        auto text=val(k,std::to_string(fallback));
        if(text.empty()||text.find_first_not_of("0123456789")!=std::string::npos)throw std::runtime_error("invalid unsigned value: "+k);
        auto n=std::stoull(text);if(n>max)throw std::runtime_error("value out of range: "+k);return uint32_t(n);
    };
    std::string codec=val("--codec","av1"),variant=val("--variant","sdr8");
    if(codec!="av1"&&codec!="hevc")throw std::runtime_error("codec must be av1 or hevc");
    if(variant!="sdr8"&&variant!="hdr10")throw std::runtime_error("variant must be sdr8 or hdr10");
    LayoutOptions layout;
    layout.columns=number("--av1-tile-columns",1,6);layout.rows=number("--av1-tile-rows",0,6);
    layout.rowsExplicit=o.count("--av1-tile-rows");layout.psnr=number("--aom-psnr",0,1);
    layout.planOnly=number("--plan-only",0,1);layout.queryHevc=number("--query-hevc-layout",0,1);
    if(codec!="av1"&&(o.count("--av1-tile-columns")||layout.rowsExplicit||o.count("--aom-psnr")||layout.planOnly))throw std::runtime_error("AV1 options cannot be applied to HEVC");
    if(codec!="hevc"&&layout.queryHevc)throw std::runtime_error("--query-hevc-layout requires --codec hevc");
    if(o.count("--import")&&(o.count("--av1-tile-columns")||layout.rowsExplicit||o.count("--aom-psnr")||layout.planOnly||layout.queryHevc))throw std::runtime_error("import preserves encoded layout; encoder experiment options cannot be applied");
    uint32_t w=number("--width",1920,8192),h=number("--height",1080,8192),fps=number("--fps",120,1000),frames=number("--frames",120,100000),gop=number("--gop",60,UINT32_MAX),depth=variant=="hdr10"?10:8;
    if(w<64||h<64||w%2||h%2||!fps||!frames||!gop)throw std::runtime_error("invalid generator dimensions/rate/count");
    std::string dir=val("--output","fixtures/generated");NSError*e=nil;
    if(![[NSFileManager defaultManager]createDirectoryAtPath:ns(dir) withIntermediateDirectories:YES attributes:nil error:&e])throw std::runtime_error(utf(e.description));
    if(o.count("--import")){auto m=load(o["--import"]);mav::Bitstream parser(m.codec=="av1"?mav::Codec::AV1:mav::Codec::HEVC);for(auto&a:m.units){mav::Prepared p;std::string error;if(a.discontinuity)parser.clear();if(parser.prepare(m.payload.data()+a.offset,a.size,p,error)!=mav::ParseResult::Ok||p.displayed_frames!=a.displays||p.random_access!=a.random||p.format.width!=m.width||p.format.height!=m.height||p.format.bit_depth!=m.depth)throw std::runtime_error("capture manifest disagrees with encoded access units: "+error);}NSMutableDictionary* document=[m.document mutableCopy];document[@"payload_file"]=@"payload.bin";document[@"import_provenance"]=@{@"source_payload_sha256":ns(m.hash),@"operation":@"verified complete access-unit import; original timing and expected display sequence preserved"};write(dir+"/payload.bin",m.payload);json(dir+"/manifest.json",document);std::cout<<"PASS imported verified complete access units\n";return 0;}
    NSMutableDictionary* settings=[@{@"schema_version":@1,@"status":layout.planOnly?@"PLANNED":layout.queryHevc?@"QUERY_ONLY":@"REQUESTED",@"codec":ns(codec),@"width":@(w),@"height":@(h),@"bit_depth":@(depth),@"fps":@(fps),@"frames":@(frames),@"gop":@(gop),@"pattern":@"moving-gradient-detail-square-frame-id-v1",@"source_signal":depth==10?@"BT2020-PQ-code-values":@"BT709-code-values",@"hardware_encoder_required":@(codec=="hevc"),@"rate_control":codec=="hevc"?@{@"mode":@"average-bitrate",@"requested_bps":@(std::max(uint64_t(1000000),uint64_t(w)*h*fps/3))}:@{}} mutableCopy];
    std::string version="Apple VTCompressionSession HEVC (OS-versioned)";
    auto units=codec=="av1"?av1(dir,val("--aomenc",".local/aom-build/aomenc"),w,h,depth,fps,frames,gop,version,layout,settings):hevc(dir,w,h,depth,fps,frames,gop,layout,settings);
    if(layout.planOnly||layout.queryHevc){std::cout<<"PASS "<<(layout.planOnly?"planned arguments without encoder execution":"queried HEVC hardware encoder without encoding frames")<<": "<<dir<<"/encoder-settings.json\n";return 0;}
    save(dir,codec,w,h,depth,fps,units,version,settings);return 0;
}catch(const std::exception&e){std::cerr<<"BLOCKED/FAIL: "<<e.what()<<"\n";return 1;}}}
