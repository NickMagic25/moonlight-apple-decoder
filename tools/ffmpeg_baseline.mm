#include "fixture_support.hpp"
#include "moonlight_apple_video/decoder.h"
extern "C" {
#include <libavcodec/avcodec.h>
#include <libavcodec/videotoolbox.h>
#include <libavutil/error.h>
}
#include <map>
#include <cstring>
#include <thread>
#include <iostream>
using namespace fixture;
struct Record {uint64_t id=0,arrival=0,send=0,returned=0,output=0;uint32_t format=0;bool cold=false;};
static AVPixelFormat format(AVCodecContext*,const AVPixelFormat* formats){for(auto f=formats;*f!=AV_PIX_FMT_NONE;++f)if(*f==AV_PIX_FMT_VIDEOTOOLBOX)return *f;return AV_PIX_FMT_NONE;}
static std::string error(int s){char b[AV_ERROR_MAX_STRING_SIZE];av_strerror(s,b,sizeof(b));return b;}
static NSDictionary* stats(std::vector<double> v){if(v.empty())return @{ @"count":@0,@"mean":NSNull.null,@"median":NSNull.null,@"p95":NSNull.null,@"p99":NSNull.null,@"min":NSNull.null,@"max":NSNull.null};std::sort(v.begin(),v.end());double sum=0;for(auto n:v)sum+=n;auto q=[&](double x){auto a=x*(v.size()-1);size_t i=a;return v[i]+(a-i)*(v[std::min(i+1,v.size()-1)]-v[i]);};return @{@"count":@(v.size()),@"mean":@(sum/v.size()),@"median":@(q(.5)),@"p95":@(q(.95)),@"p99":@(q(.99)),@"min":@(v.front()),@"max":@(v.back())};}
int main(int argc,char** argv){@autoreleasepool {
    AVCodecContext* context=nullptr;AVPacket* packet=nullptr;AVFrame* frame=nullptr;AVVideotoolboxContext vt{};
    std::string out="results/ffmpeg-baseline",failure,codec,variant,hash,mode="throughput",loopMode="reset";std::vector<Record> records;
    uint64_t submitted=0,displayed=0,expected=0,start=0,end=0,warmup=0,loops=1;bool hardware=false;VTDecompressionSessionRef verifiedSession=nullptr;double fps=0;
    try {
        std::map<std::string,std::string> options;for(int i=1;i<argc;++i){if(std::string(argv[i])=="--help"){std::cout<<"mav-ffmpeg-baseline --fixture manifest.json --output prefix [--mode paced|throughput --fps 120 --warmup 12 --loops 10 --loop-mode reset|continuous]\n";return 0;}if(i+1>=argc)throw std::runtime_error("option requires value");std::string k=argv[i];options[k]=argv[++i];}
        if(options.count("--output"))out=options["--output"];
        if(!options.count("--fixture"))throw std::runtime_error("--fixture required");
        auto m=load(options["--fixture"]);codec=m.codec;variant=m.variant;hash=m.hash;fps=double(m.fps_num)/m.fps_den;
        if(options.count("--mode"))mode=options["--mode"];if(mode!="paced"&&mode!="throughput")throw std::runtime_error("unsupported mode");
        if(options.count("--fps"))fps=std::stod(options["--fps"]);if(!(fps>0&&fps<=10000))throw std::runtime_error("invalid fps");
        if(options.count("--warmup"))warmup=std::stoull(options["--warmup"]);
        if(options.count("--loops"))loops=std::stoull(options["--loops"]);
        if(options.count("--loop-mode"))loopMode=options["--loop-mode"];
        if(loopMode!="reset"&&loopMode!="continuous")throw std::runtime_error("invalid loop mode");
        if(loopMode=="continuous"&&!m.units.front().random)throw std::runtime_error("continuous loops require an initial random-access picture");
        if(!loops||loops>10000||loops*m.units.size()>1000000)throw std::runtime_error("too many submissions");
        const AVCodec* decoder=avcodec_find_decoder_by_name(codec.c_str());if(!decoder)throw std::runtime_error("BLOCKED: installed FFmpeg has no native "+codec+" decoder");
        bool supports=false;for(int i=0;;++i){auto c=avcodec_get_hw_config(decoder,i);if(!c)break;if(c->pix_fmt==AV_PIX_FMT_VIDEOTOOLBOX)supports=true;}
        if(!supports)throw std::runtime_error("BLOCKED: installed FFmpeg codec exposes no VideoToolbox configuration");
        context=avcodec_alloc_context3(decoder);packet=av_packet_alloc();frame=av_frame_alloc();if(!context||!packet||!frame)throw std::bad_alloc();
        // Documented API-specific context path makes the exact VT session
        // observable for hardware read-back. No FFmpeg private structures.
        vt.cv_pix_fmt_type=m.depth==10?kCVPixelFormatType_420YpCbCr10BiPlanarVideoRange:kCVPixelFormatType_420YpCbCr8BiPlanarVideoRange;
        context->hwaccel_context=&vt;context->get_format=format;context->thread_count=1;context->flags|=AV_CODEC_FLAG_LOW_DELAY|AV_CODEC_FLAG_COPY_OPAQUE;
        context->pkt_timebase={static_cast<int>(m.timebase_num),static_cast<int>(m.timebase_den)};
        int status=avcodec_open2(context,decoder,nullptr);if(status<0)throw std::runtime_error("BLOCKED: avcodec_open2: "+error(status));
        records.resize(m.units.size()*loops);start=mav_monotonic_time_ns()+(mode=="paced"?20000000:0);
        auto receive=[&]{for(;;){int result=avcodec_receive_frame(context,frame);uint64_t when=mav_monotonic_time_ns();if(result==AVERROR(EAGAIN)||result==AVERROR_EOF)return;if(result<0)throw std::runtime_error("receive: "+error(result));
            if(frame->format!=AV_PIX_FMT_VIDEOTOOLBOX||!frame->data[3])throw std::runtime_error("BLOCKED: FFmpeg output is not a VT pixel buffer");
            auto buffer=reinterpret_cast<CVPixelBufferRef>(frame->data[3]);auto pixel=CVPixelBufferGetPixelFormatType(buffer);
            if(pixel!=vt.cv_pix_fmt_type||CVPixelBufferGetWidth(buffer)!=m.width||CVPixelBufferGetHeight(buffer)!=m.height||!CVPixelBufferGetIOSurface(buffer))throw std::runtime_error("FFmpeg output violates equivalent YUV/IOSurface format constraints");
            if(!vt.session)throw std::runtime_error("BLOCKED: FFmpeg VT session unavailable for hardware verification");
            if(verifiedSession!=vt.session){
            CFTypeRef property=nullptr;auto os=VTSessionCopyProperty(vt.session,kVTDecompressionPropertyKey_UsingHardwareAcceleratedVideoDecoder,kCFAllocatorDefault,&property);
            bool hw=!os&&property&&CFGetTypeID(property)==CFBooleanGetTypeID()&&CFBooleanGetValue(static_cast<CFBooleanRef>(property));if(property)CFRelease(property);
            if(!hw)throw std::runtime_error("BLOCKED: FFmpeg session did not select verified hardware");hardware=true;verifiedSession=vt.session;}
            auto r=static_cast<Record*>(frame->opaque);if(!r||r<records.data()||r>=records.data()+records.size()||r->output)throw std::runtime_error("FFmpeg input/output association unavailable or duplicate");
            r->output=when;r->format=pixel;++displayed;av_frame_unref(frame);
        }};
        int64_t loop_span=m.units.back().pts+m.units.back().duration-m.units.front().pts;
        if(loop_span<=0)throw std::runtime_error("invalid loop duration");
        for(size_t i=0;i<records.size();++i){const auto& a=m.units[i%m.units.size()];auto& r=records[i];r.id=i;r.cold=i==0||(loopMode=="reset"&&i%m.units.size()==0);
            if(i&&r.cold){
                avcodec_send_packet(context,nullptr);receive();avcodec_free_context(&context);
                if(vt.session){VTDecompressionSessionInvalidate(vt.session);CFRelease(vt.session);}
                if(vt.cm_fmt_desc)CFRelease(vt.cm_fmt_desc);vt={};verifiedSession=nullptr;
                vt.cv_pix_fmt_type=m.depth==10?kCVPixelFormatType_420YpCbCr10BiPlanarVideoRange:kCVPixelFormatType_420YpCbCr8BiPlanarVideoRange;
                context=avcodec_alloc_context3(decoder);if(!context)throw std::bad_alloc();
                context->hwaccel_context=&vt;context->get_format=format;context->thread_count=1;context->flags|=AV_CODEC_FLAG_LOW_DELAY|AV_CODEC_FLAG_COPY_OPAQUE;
                context->pkt_timebase={int(m.timebase_num),int(m.timebase_den)};
                int opened=avcodec_open2(context,decoder,nullptr);if(opened<0)throw std::runtime_error("reopen: "+error(opened));
            }
            r.arrival=mode=="paced"?start+uint64_t(i*1e9/fps):mav_monotonic_time_ns();
            // Match the native harness's capped absolute-deadline wait, including
            // macOS timer coalescing behavior. Keep the original offered deadline.
            for(;;){auto now=mav_monotonic_time_ns();if(now>=r.arrival)break;std::this_thread::sleep_for(std::chrono::nanoseconds(std::min(r.arrival-now,uint64_t(1000000))));}
            if(a.discontinuity&&i)avcodec_flush_buffers(context);
            status=av_new_packet(packet,static_cast<int>(a.size));if(status<0)throw std::bad_alloc();std::memcpy(packet->data,m.payload.data()+a.offset,a.size);
            int64_t rebase=int64_t(i/m.units.size())*loop_span;packet->pts=a.pts_valid?a.pts+rebase:AV_NOPTS_VALUE;packet->dts=a.dts_valid?a.dts+rebase:AV_NOPTS_VALUE;packet->duration=a.duration;packet->opaque=&r;if(a.random)packet->flags|=AV_PKT_FLAG_KEY;
            r.send=mav_monotonic_time_ns();status=avcodec_send_packet(context,packet);r.returned=mav_monotonic_time_ns();
            if(status==AVERROR(EAGAIN)){receive();status=avcodec_send_packet(context,packet);r.returned=mav_monotonic_time_ns();}
            av_packet_unref(packet);if(status<0)throw std::runtime_error("send: "+error(status));++submitted;expected+=a.displays;receive();
        }
        int status2=avcodec_send_packet(context,nullptr);if(status2<0&&status2!=AVERROR_EOF)throw std::runtime_error("flush: "+error(status2));receive();end=mav_monotonic_time_ns();
        if(displayed!=expected||!hardware)throw std::runtime_error("output count or hardware verification failed");
    }catch(const std::exception& e){failure=e.what();end=mav_monotonic_time_ns();}
    av_packet_free(&packet);av_frame_free(&frame);avcodec_free_context(&context);
    if(vt.session){VTDecompressionSessionInvalidate(vt.session);CFRelease(vt.session);}if(vt.cm_fmt_desc)CFRelease(vt.cm_fmt_desc);
    [[NSFileManager defaultManager]createDirectoryAtPath:ns(out).stringByDeletingLastPathComponent withIntermediateDirectories:YES attributes:nil error:nil];
    std::ofstream csv(out+".csv");csv<<"frame_id,scheduled_arrival_ns,send_packet_entry_ns,send_packet_return_ns,receive_frame_return_ns,pixel_format\n";
    std::vector<double> complete,api,queue,call,cold;for(size_t i=0;i<records.size();++i){auto&r=records[i];csv<<r.id<<','<<r.arrival<<','<<r.send<<','<<r.returned<<','<<r.output<<','<<r.format<<'\n';if(r.cold&&r.output)cold.push_back(r.output-r.arrival);if(i>=warmup&&r.output&&!r.cold){complete.push_back(r.output-r.arrival);api.push_back(r.output-r.send);queue.push_back(r.send-r.arrival);call.push_back(r.returned-r.send);}}
    NSString* state=failure.empty()?@"PASS":(failure.find("BLOCKED")!=std::string::npos?@"BLOCKED":@"FAIL");
    NSDictionary* result=@{@"status":state,@"reason":failure.empty()?static_cast<id>(NSNull.null):ns(failure),@"backend":@"ffmpeg-videotoolbox",@"ffmpeg_version":ns(av_version_info()),@"codec":ns(codec),@"variant":ns(variant),@"fixture_sha256":ns(hash),@"mode":ns(mode),@"hardware_verified":@(hardware),@"submitted":@(submitted),@"displayed_outputs":@(displayed),@"expected_outputs":@(expected),@"requested_fps":@(fps),@"warmup_frames":@(warmup),@"thread_count":@1,@"loops":@(loops),@"loop_mode":ns(loopMode),@"cold_complete_au_to_output_ns":stats(cold),@"run_seconds":start&&end>=start?static_cast<id>(@(double(end-start)/1e9)):NSNull.null,@"complete_au_to_output_ns":stats(complete),@"send_packet_to_receive_frame_ns":stats(api),@"queue_and_packet_preparation_ns":stats(queue),@"send_packet_call_ns":stats(call),@"vt_submit_to_callback_ns":NSNull.null,@"renderer_ns":NSNull.null,@"presentation_ns":NSNull.null};
    try{json(out+".json",result);}catch(const std::exception&e){std::cerr<<e.what()<<"\n";return 1;}
    std::cout<<utf(state)<<" FFmpeg VT "<<codec<<" "<<variant<<" outputs="<<displayed<<" "<<failure<<" result="<<out<<".json\n";
    return failure.empty()?0:1;
}}
