#include "fixture_support.hpp"
extern "C" {
#include <libavcodec/avcodec.h>
#include <libavutil/error.h>
}
#include <cstring>
#include <iostream>
#include <map>
using namespace fixture;
static AVPixelFormat software_format(AVCodecContext*,const AVPixelFormat* f){for(;*f!=AV_PIX_FMT_NONE;++f)if(*f==AV_PIX_FMT_YUV420P||*f==AV_PIX_FMT_YUV420P10LE)return *f;return AV_PIX_FMT_NONE;}
int main(int argc,char** argv){@autoreleasepool{
    AVCodecContext* context=nullptr;AVFrame* frame=nullptr;AVPacket* packet=nullptr;
    try{
        std::map<std::string,std::string> o;for(int i=1;i<argc;++i){if(i+1>=argc)throw std::runtime_error("usage: mav-reference-decode --fixture manifest.json --output reference.yuv");std::string k=argv[i];o[k]=argv[++i];}
        if(!o.count("--fixture")||!o.count("--output"))throw std::runtime_error("--fixture and --output required");
        auto m=load(o["--fixture"]);const AVCodec* decoder=nullptr;
        if(m.codec=="av1"){decoder=avcodec_find_decoder_by_name("libdav1d");if(!decoder)decoder=avcodec_find_decoder_by_name("libaom-av1");}
        else decoder=avcodec_find_decoder_by_name("hevc");
        if(!decoder)throw std::runtime_error("BLOCKED: software decoder unavailable; AV1 may use local aomdec instead");
        context=avcodec_alloc_context3(decoder);frame=av_frame_alloc();packet=av_packet_alloc();if(!context||!frame||!packet)throw std::bad_alloc();
        context->get_format=software_format;context->thread_count=2;
        if(avcodec_open2(context,decoder,nullptr)<0)throw std::runtime_error("software avcodec_open2 failed");
        std::ofstream out(o["--output"],std::ios::binary);if(!out)throw std::runtime_error("cannot create reference output");
        uint64_t displayed=0,expected=0;
        auto receive=[&]{for(;;){auto status=avcodec_receive_frame(context,frame);if(status==AVERROR(EAGAIN)||status==AVERROR_EOF)return;if(status<0)throw std::runtime_error("software receive failed");
            auto desired=m.depth==10?AV_PIX_FMT_YUV420P10LE:AV_PIX_FMT_YUV420P;
            if(frame->format!=desired||frame->width!=int(m.width)||frame->height!=int(m.height))throw std::runtime_error("software output format differs from fixture");
            for(unsigned plane=0;plane<3;++plane){unsigned width=plane?(m.width+1)/2:m.width,height=plane?(m.height+1)/2:m.height;size_t row=width*(m.depth==10?2:1);
                for(unsigned y=0;y<height;++y)out.write(reinterpret_cast<const char*>(frame->data[plane]+int64_t(y)*frame->linesize[plane]),row);}
            ++displayed;av_frame_unref(frame);
        }};
        for(auto& a:m.units){if(av_new_packet(packet,a.size)<0)throw std::bad_alloc();std::memcpy(packet->data,m.payload.data()+a.offset,a.size);packet->pts=a.pts;packet->dts=a.dts;packet->duration=a.duration;
            int status=avcodec_send_packet(context,packet);if(status==AVERROR(EAGAIN)){receive();status=avcodec_send_packet(context,packet);}av_packet_unref(packet);if(status<0)throw std::runtime_error("software send failed");expected+=a.displays;receive();}
        avcodec_send_packet(context,nullptr);receive();if(displayed!=expected||!out)throw std::runtime_error("software output count/write failure");
        out.close();json(o["--output"]+".json",@{@"status":@"PASS",@"codec":ns(m.codec),@"decoder":ns(decoder->name),@"ffmpeg_version":ns(av_version_info()),@"fixture_sha256":ns(m.hash),@"outputs":@(displayed),@"packing":m.depth==10?@"yuv420p10le-low-bits":@"yuv420p",@"row_padding":@"omitted"});
        av_packet_free(&packet);av_frame_free(&frame);avcodec_free_context(&context);std::cout<<"PASS software reference "<<m.codec<<" outputs="<<displayed<<"\n";return 0;
    }catch(const std::exception& e){av_packet_free(&packet);av_frame_free(&frame);avcodec_free_context(&context);std::cerr<<e.what()<<"\n";return 1;}
}}
