#import <VideoToolbox/VideoToolbox.h>
#include "fixture_support.hpp"
#include "fixture_options.hpp"
#include "bitstream.hpp"
#include <mutex>
#include <iostream>
#include <cstring>
#include <cerrno>
#include <csignal>
#include <fcntl.h>
#include <spawn.h>
#include <sys/wait.h>
#include <unistd.h>
#include <crt_externs.h>

using namespace fixture;
// Explicit bitrate workloads need enough changing detail for rate control to
// spend the requested bits. Keep the legacy frame-ID strip exactly intact so
// both old and new replay binaries retain their independent identity check.
static uint16_t source_luma(uint32_t x,uint32_t y,uint32_t w,uint32_t h,uint64_t frame,uint32_t depth,bool bitrate_workload){
    if(!bitrate_workload||y<h/8)return luma(x,y,w,h,frame,depth);
    // Fixed unsigned arithmetic gives the same source on every platform/run.
    uint32_t value=0x6d617631u^(x*0x9e3779b9u)^(y*0x85ebca6bu)^(uint32_t(frame)*0xc2b2ae35u)^uint32_t(frame>>32);
    value^=value>>16;value*=0x7feb352du;value^=value>>15;value*=0x846ca68bu;value^=value>>16;
    return depth==10?uint16_t(64+value%877):uint16_t(16+value%220);
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
static std::vector<Encoded> hevc(uint32_t w,uint32_t h,uint32_t depth,uint32_t fps,uint32_t frames,uint32_t gop,uint64_t bitrate,bool bitrate_workload){
    EncodeState state;VTCompressionSessionRef session=nullptr;
    NSDictionary* spec=@{(__bridge NSString*)kVTVideoEncoderSpecification_RequireHardwareAcceleratedVideoEncoder:@YES};
    auto status=VTCompressionSessionCreate(nullptr,w,h,kCMVideoCodecType_HEVC,(__bridge CFDictionaryRef)spec,nullptr,nullptr,output,&state,&session);
    if(status)throw std::runtime_error("BLOCKED HEVC hardware encoder creation "+std::to_string(status));
    try {
        property(session,kVTCompressionPropertyKey_ProfileLevel,depth==10?kVTProfileLevel_HEVC_Main10_AutoLevel:kVTProfileLevel_HEVC_Main_AutoLevel);
        property(session,kVTCompressionPropertyKey_RealTime,kCFBooleanTrue);property(session,kVTCompressionPropertyKey_AllowFrameReordering,kCFBooleanFalse);
        property(session,kVTCompressionPropertyKey_ExpectedFrameRate,(__bridge CFNumberRef)@(fps));property(session,kVTCompressionPropertyKey_MaxKeyFrameInterval,(__bridge CFNumberRef)@(gop));
        property(session,kVTCompressionPropertyKey_AverageBitRate,(__bridge CFNumberRef)@(bitrate));
        if(bitrate_workload)property(session,kVTCompressionPropertyKey_DataRateLimits,(__bridge CFArrayRef)@[@(bitrate*3/20),@1]);
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
            for(uint32_t y=0;y<h;++y)for(uint32_t x=0;x<w;++x){auto v=source_luma(x,y,w,h,f,depth,bitrate_workload);if(depth==10)reinterpret_cast<uint16_t*>(p+y*stride)[x]=v<<6;else p[y*stride+x]=uint8_t(v);}
            p=(uint8_t*)CVPixelBufferGetBaseAddressOfPlane(pixel,1);stride=CVPixelBufferGetBytesPerRowOfPlane(pixel,1);
            for(uint32_t y=0;y<h/2;++y)for(uint32_t x=0;x<w;++x){if(depth==10)reinterpret_cast<uint16_t*>(p+y*stride)[x]=uint16_t(512)<<6;else p[y*stride+x]=128;}
            CVPixelBufferUnlockBaseAddress(pixel,0);
            NSDictionary* options=(f%gop==0)?@{(__bridge NSString*)kVTEncodeFrameOptionKey_ForceKeyFrame:@YES}:@{};
            status=VTCompressionSessionEncodeFrame(session,pixel,CMTimeMake(f,fps),CMTimeMake(1,fps),(__bridge CFDictionaryRef)options,reinterpret_cast<void*>(uintptr_t(f)+1),nullptr);CVPixelBufferRelease(pixel);
            if(status)throw std::runtime_error("encode frame "+std::to_string(status));
        }
        status=VTCompressionSessionCompleteFrames(session,kCMTimeInvalid);if(status)throw std::runtime_error("encoder completion "+std::to_string(status));
        if(!state.error.empty())throw std::runtime_error(state.error);
    } catch(...) {VTCompressionSessionInvalidate(session);CFRelease(session);throw;}
    VTCompressionSessionInvalidate(session);CFRelease(session);
    std::sort(state.units.begin(),state.units.end(),[](auto&a,auto&b){return a.id<b.id;});
    if(state.units.size()!=frames)throw std::runtime_error("encoder lost frames");
    if(depth==10){auto m=mastering();std::vector<uint8_t>rbsp={137,24};rbsp.insert(rbsp.end(),m.begin(),m.end());rbsp.insert(rbsp.end(),{144,4,3,232,1,144,0x80});std::vector<uint8_t>sei={0,0,0,1,0x4e,1};unsigned zeros=0;for(auto b:rbsp){if(zeros>=2&&b<=3){sei.push_back(3);zeros=0;}sei.push_back(b);zeros=b==0?zeros+1:0;}for(auto&u:state.units)u.data.insert(u.data.begin(),sei.begin(),sei.end());}
    return state.units;
}
static std::string run(NSString* executable,NSArray<NSString*>* args){
    auto check=[](int status,const char* operation){if(status)throw std::runtime_error(std::string(operation)+": "+std::strerror(status));};
    struct Child {
        int output[2]={-1,-1};pid_t pid=-1;
        ~Child(){for(auto fd:output)if(fd>=0)close(fd);if(pid>0){kill(pid,SIGKILL);while(waitpid(pid,nullptr,0)<0&&errno==EINTR){}}}
        void close_output(unsigned index){if(output[index]>=0){close(output[index]);output[index]=-1;}}
    } child;
    if(pipe(child.output))check(errno,"encoder pipe");
    for(auto&fd:child.output){
        // Keep descriptors away from stdio so the spawn close actions cannot
        // close an output that was just duplicated to stdout or stderr.
        if(fd<3){int replacement=fcntl(fd,F_DUPFD_CLOEXEC,3);if(replacement<0)check(errno,"encoder pipe duplication");close(fd);fd=replacement;}
        if(fcntl(fd,F_SETFD,FD_CLOEXEC)<0)check(errno,"encoder pipe flags");
    }
    struct Actions {
        posix_spawn_file_actions_t value;
        Actions(){int status=posix_spawn_file_actions_init(&value);if(status)throw std::runtime_error(std::string("encoder spawn actions: ")+std::strerror(status));}
        ~Actions(){posix_spawn_file_actions_destroy(&value);}
    } actions;
    check(posix_spawn_file_actions_adddup2(&actions.value,child.output[1],STDOUT_FILENO),"encoder stdout action");
    check(posix_spawn_file_actions_adddup2(&actions.value,child.output[1],STDERR_FILENO),"encoder stderr action");
    check(posix_spawn_file_actions_addclose(&actions.value,child.output[0]),"encoder read-pipe action");
    check(posix_spawn_file_actions_addclose(&actions.value,child.output[1]),"encoder write-pipe action");
    std::vector<std::string> storage={utf(executable)};for(NSString*argument in args)storage.push_back(utf(argument));
    std::vector<char*> argv;for(auto&argument:storage)argv.push_back(argument.data());argv.push_back(nullptr);
    // No POSIX_SPAWN_SETPGROUP: inherit mav-fixture's group so the benchmark
    // runner's isolated-group timeout also terminates its aomenc child.
    pid_t spawned=-1;check(posix_spawn(&spawned,storage.front().c_str(),&actions.value,nullptr,argv.data(),*_NSGetEnviron()),"BLOCKED launching encoder");child.pid=spawned;
    child.close_output(1);
    std::string result;char buffer[8192];
    for(;;){ssize_t size=read(child.output[0],buffer,sizeof(buffer));if(size>0)result.append(buffer,size);else if(!size)break;else if(errno!=EINTR)check(errno,"encoder output read");}
    child.close_output(0);
    int status=0;pid_t waited;do{waited=waitpid(child.pid,&status,0);}while(waited<0&&errno==EINTR);
    if(waited<0){int error=errno;if(error==ECHILD)child.pid=-1;check(error,"encoder wait");}
    child.pid=-1;
    if(!WIFEXITED(status)||WEXITSTATUS(status))throw std::runtime_error("encoder failed: "+result);return result;
}
static uint64_t le(const uint8_t*p,unsigned n){uint64_t v=0;for(unsigned i=0;i<n;++i)v|=uint64_t(p[i])<<(i*8);return v;}
static std::vector<Encoded> ivf(const std::string& path,uint32_t w,uint32_t h){
    auto b=read(path);if(b.size()<32||memcmp(b.data(),"DKIF",4)||memcmp(b.data()+8,"AV01",4)||le(b.data()+6,2)!=32||le(b.data()+12,2)!=w||le(b.data()+14,2)!=h)throw std::runtime_error("unsupported IVF header");
    size_t at=32;std::vector<Encoded>r;while(at<b.size()){if(b.size()-at<12)throw std::runtime_error("truncated IVF packet");uint64_t n=le(b.data()+at,4),id=le(b.data()+at+4,8);at+=12;if(!n||n>b.size()-at)throw std::runtime_error("invalid IVF packet size");r.push_back({id,{b.begin()+at,b.begin()+at+n}});at+=n;}return r;
}
static std::vector<Encoded> av1(const std::string& out,const std::string& encoder,uint32_t w,uint32_t h,uint32_t depth,uint32_t fps,uint32_t frames,uint32_t gop,uint32_t bitrate,std::string& version,NSArray<NSString*>* __strong& arguments){
    std::string raw=out+"/source.yuv",encoded=out+"/encoded.ivf";
    {std::ofstream file(raw,std::ios::binary);std::vector<uint8_t> row(w*(depth==10?2:1));
        for(uint32_t f=0;f<frames;++f){for(uint32_t y=0;y<h;++y){for(uint32_t x=0;x<w;++x){auto v=source_luma(x,y,w,h,f,depth,bitrate!=0);if(depth==10){row[x*2]=v;row[x*2+1]=v>>8;}else row[x]=v;}file.write((char*)row.data(),row.size());}
        std::fill(row.begin(),row.end(),128);if(depth==10)for(size_t x=0;x<row.size();x+=2){row[x]=0;row[x+1]=2;}
        for(uint32_t y=0;y<h/2;++y)file.write((char*)row.data(),row.size());}if(!file)throw std::runtime_error("source write failed");}
    NSMutableArray<NSString*>* args=[NSMutableArray arrayWithArray:@[@"--codec=av1",@"--ivf",@"--i420",@"--passes=1",ns(bitrate?"--usage=1":"--usage=0"),ns(bitrate?"--cpu-used=8":"--cpu-used=6"),@"--enable-tpl-model=0",@"--threads=6",@"--test-decode=fatal",@"--row-mt=1",@"--tile-columns=1",@"--lag-in-frames=0",@"--enable-keyframe-filtering=0",@"--auto-alt-ref=0",ns(bitrate?"--end-usage=cbr":"--end-usage=q"),ns(bitrate?"--target-bitrate="+std::to_string(bitrate):"--cq-level=12"),@"--disable-warning-prompt",ns("--width="+std::to_string(w)),ns("--height="+std::to_string(h)),ns("--fps="+std::to_string(fps)+"/1"),ns("--limit="+std::to_string(frames)),ns("--bit-depth="+std::to_string(depth)),ns("--input-bit-depth="+std::to_string(depth)),ns("--kf-max-dist="+std::to_string(gop)),ns("--kf-min-dist="+std::to_string(gop)),ns("--color-primaries="+std::to_string(depth==10?9:1)),ns("--transfer-characteristics="+std::to_string(depth==10?16:1)),ns("--matrix-coefficients="+std::to_string(depth==10?9:1)),ns("--output="+encoded),ns(raw)]];
    if(bitrate){
        NSArray<NSString*>* rateArguments=@[@"--max-intra-rate=300",@"--max-inter-rate=300",@"--undershoot-pct=10",@"--overshoot-pct=10",@"--buf-sz=1000",@"--buf-initial-sz=500",@"--buf-optimal-sz=500",@"--drop-frame=0"];
        for(NSString* argument in rateArguments)[args insertObject:argument atIndex:args.count-1];
    }
    arguments=args;
    auto log=run(ns(encoder),args);auto help=run(ns(encoder),@[@"--help"]);auto at=help.find("AOMedia Project AV1 Encoder");version=at==std::string::npos?"AOM encoder version unavailable":help.substr(at,help.find('\n',at)-at);write(out+"/encoder.log",{log.begin(),log.end()});json(out+"/encoder-arguments.json",args);
    auto units=ivf(encoded,w,h);if(units.size()!=frames)throw std::runtime_error("encoder did not produce one low-delay temporal unit per input frame");
    if(depth==10){ // HDR metadata OBU, independent of genuinely encoded 10-bit pixels/sequence signaling.
        auto m=mastering(); auto put16=[&](size_t at,uint32_t x){m[at]=x>>8;m[at+1]=x;}; auto put32=[&](size_t at,uint32_t x){put16(at,x>>16);put16(at+2,x);}; put16(0,46400);put16(2,19136);put16(4,11141);put16(6,52232);put16(8,8585);put16(10,3015);put16(12,20493);put16(14,21561);put32(16,256000);put32(20,82);std::vector<uint8_t>metadata={0x2a,6,1,3,232,1,144,0x80,0x2a,26,2};metadata.insert(metadata.end(),m.begin(),m.end());metadata.push_back(0x80);
        for(auto&u:units)u.data.insert(u.data.begin(),metadata.begin(),metadata.end());
    }
    [[NSFileManager defaultManager]removeItemAtPath:ns(raw) error:nil];return units;
}
static void save(const Options& options,std::vector<Encoded>& units,const std::string& encoder,NSArray<NSString*>* encoderArguments){
    const auto& dir=options.output;const auto& codec=options.codec;auto w=options.width,h=options.height,depth=options.variant=="hdr10"?10u:8u,fps=options.fps;
    mav::Bitstream parser(codec=="av1"?mav::Codec::AV1:mav::Codec::HEVC);std::vector<uint8_t>payload;NSMutableArray* access=[NSMutableArray new];uint32_t keys=0,inters=0;mav::Format final;
    for(auto&u:units){mav::Prepared p;std::string error;auto status=parser.prepare(u.data.data(),u.data.size(),p,error);if(status!=mav::ParseResult::Ok)throw std::runtime_error("encoded AU "+std::to_string(u.id)+" rejected by codec verifier: "+error);
        if(p.format.width!=w||p.format.height!=h||p.format.bit_depth!=depth||p.format.chroma!=1||p.format.profile!=(codec=="av1"?0:(depth==10?2:1)))throw std::runtime_error("encoded profile/dimensions/depth do not match request");
        if(p.displayed_frames!=1)throw std::runtime_error("generated low-delay AU must display exactly once");
        if(depth==10&&(!p.format.color.description_valid||p.format.color.primaries!=9||p.format.color.transfer!=16||p.format.color.matrix!=9))throw std::runtime_error("encoded stream missing BT2020/PQ HDR signaling");
        if(p.random_access)++keys;else ++inters;final=p.format;
        [access addObject:@{@"offset":@(payload.size()),@"length":@(u.data.size()),@"frame_id":@(u.id),@"pts":@(u.id),@"dts":@(u.id),@"duration":@1,@"random_access":@(p.random_access),@"discontinuity":@NO,@"expected_display_count":@(p.displayed_frames),@"expected_visible_frame_id":@(u.id),@"sha256":ns(sha(u.data.data(),u.data.size()))}];payload.insert(payload.end(),u.data.begin(),u.data.end());
    }
    if(units.size()>2&&!inters&&options.gop!=1)throw std::runtime_error("fixture has no reference-dependent inter frames");
    if(depth==10&&(!final.color.mastering_valid||!final.color.content_light_valid))throw std::runtime_error("HDR fixture missing mastering/content light metadata");
    write(dir+"/payload.bin",payload);
    id requestedBitrate=options.bitrate_kbps?(id)@(double(*options.bitrate_kbps)/1000.0):(id)[NSNull null];
    id targetBitrate=codec=="hevc"?(id)@(options.hevc_target_bitrate_bps()):(options.bitrate_kbps?(id)@(uint64_t(*options.bitrate_kbps)*1000):(id)[NSNull null]);
    NSDictionary* encoderSettings=codec=="av1"?@{@"arguments":encoderArguments}:@{@"hardware_required":@YES,@"realtime":@YES,@"allow_frame_reordering":@NO,@"average_bitrate_bps":targetBitrate,@"data_rate_limits":options.bitrate_kbps?(id)@[@(options.hevc_target_bitrate_bps()*3/20),@1]:(id)[NSNull null],@"expected_frame_rate":@(fps),@"max_key_frame_interval":@(options.gop),@"profile":depth==10?@"Main10_AutoLevel":@"Main_AutoLevel"};
    NSDictionary* generator=@{@"name":@"mav-fixture",@"pattern":@"moving-gradient-detail-square-frame-id-v1",@"content_profile":options.bitrate_kbps?@"seeded-noise-frame-id-v1":@"moving-gradient-detail-square-frame-id-v1",@"content_seed":options.bitrate_kbps?(id)@(0x6d617631u):(id)[NSNull null],@"encoder":ns(encoder),@"os":NSProcessInfo.processInfo.operatingSystemVersionString,@"low_delay_verified":@YES,@"random_access_count":@(keys),@"inter_count":@(inters),@"requested_bitrate_mbps":requestedBitrate,@"target_bitrate_bps":targetBitrate,@"measured_bitrate_bps":@(double(payload.size())*8.0*fps/units.size()),@"measured_bitrate_mbps":@(double(payload.size())*8.0*fps/units.size()/1000000.0),@"bitrate_measurement":@"encoded payload bytes including codec headers and HDR metadata divided by generated presentation duration; no transport overhead",@"rate_control":codec=="hevc"?@"average_bitrate":(options.bitrate_kbps?@"cbr":@"constant_quality"),@"settings":@{@"codec":ns(codec),@"variant":ns(options.variant),@"width":@(w),@"height":@(h),@"fps":@(fps),@"frames":@(options.frames),@"gop":@(options.gop),@"bitrate_mbps":requestedBitrate,@"chroma":@"420"},@"encoder_settings":encoderSettings};
    NSDictionary*doc=@{@"schema_version":@1,@"codec":ns(codec),@"variant":depth==10?@"hdr10":@"sdr8",@"profile":@(final.profile),@"framing":codec=="av1"?@"av1-low-overhead-obu":@"hevc-annex-b",@"width":@(w),@"height":@(h),@"bit_depth":@(depth),@"chroma":@"420",@"frame_rate":@{@"num":@(fps),@"den":@1},@"timebase":@{@"num":@1,@"den":@(fps)},@"color":@{@"primaries":@(final.color.primaries),@"transfer":@(final.color.transfer),@"matrix":@(final.color.matrix),@"full_range":@(final.color.full_range),@"mastering_base64":[[NSData dataWithBytes:final.color.mastering.data() length:24] base64EncodedStringWithOptions:0],@"content_light_base64":[[NSData dataWithBytes:final.color.content_light.data() length:4] base64EncodedStringWithOptions:0],@"mastering_valid":@(final.color.mastering_valid),@"content_light_valid":@(final.color.content_light_valid)},@"payload_file":@"payload.bin",@"payload_sha256":ns(sha(payload.data(),payload.size())),@"access_units":access,@"generator":generator};
    json(dir+"/manifest.json",doc);(void)load(dir+"/manifest.json");
    std::cout<<"PASS "<<codec<<" "<<(depth==10?"hdr10":"sdr8")<<" "<<w<<"x"<<h<<" "<<units.size()<<" AUs: "<<dir<<"/manifest.json\n";
}
int main(int argc,char**argv){@autoreleasepool{try{
    auto options=parse_options(argc,argv);if(options.help){std::cout<<"mav-fixture --codec av1|hevc --variant sdr8|hdr10 --output DIR [--width 1920 --height 1080 --fps 120 --frames 120 --gop 60 --bitrate-mbps 50 --aomenc PATH]\nBitrate is an encoder target in decimal Mbps (0.001..1000, at most 3 decimal places); measured payload bitrate is recorded separately. Omit for legacy encoder defaults.\nImport verified capture: --import MANIFEST --output DIR\n";return 0;}
    const auto& dir=options.output;NSError*e=nil;if(![[NSFileManager defaultManager]createDirectoryAtPath:ns(dir) withIntermediateDirectories:YES attributes:nil error:&e])throw std::runtime_error(utf(e.description));
    if(!options.import_manifest.empty()){auto m=load(options.import_manifest);mav::Bitstream parser(m.codec=="av1"?mav::Codec::AV1:mav::Codec::HEVC);for(auto&a:m.units){mav::Prepared p;std::string error;if(a.discontinuity)parser.clear();if(parser.prepare(m.payload.data()+a.offset,a.size,p,error)!=mav::ParseResult::Ok||p.displayed_frames!=a.displays||p.random_access!=a.random||p.format.width!=m.width||p.format.height!=m.height||p.format.bit_depth!=m.depth)throw std::runtime_error("capture manifest disagrees with encoded access units: "+error);}NSMutableDictionary* document=[m.document mutableCopy];document[@"payload_file"]=@"payload.bin";document[@"import_provenance"]=@{@"source_payload_sha256":ns(m.hash),@"operation":@"verified complete access-unit import; original timing and expected display sequence preserved"};write(dir+"/payload.bin",m.payload);json(dir+"/manifest.json",document);std::cout<<"PASS imported verified complete access units\n";return 0;}
    auto w=options.width,h=options.height,fps=options.fps,frames=options.frames,gop=options.gop,depth=options.variant=="hdr10"?10u:8u;
    std::string version="Apple VTCompressionSession HEVC (OS-versioned)";NSArray<NSString*>* arguments=nil;auto units=options.codec=="av1"?av1(dir,options.aomenc,w,h,depth,fps,frames,gop,options.bitrate_kbps.value_or(0),version,arguments):hevc(w,h,depth,fps,frames,gop,options.hevc_target_bitrate_bps(),options.bitrate_kbps.has_value());save(options,units,version,arguments);return 0;
}catch(const std::exception&e){std::cerr<<"BLOCKED/FAIL: "<<e.what()<<"\n";return 1;}}}
