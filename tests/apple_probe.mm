#include "moonlight_apple_video/decoder.h"
#import <Metal/Metal.h>
#include <CoreVideo/CoreVideo.h>
#include <fstream>
#include <iostream>
#include <iterator>
#include <vector>
struct Sink { unsigned outputs=0,failures=0; CVPixelBufferRef retained=nullptr; };
static void output(void* context,const mav_completion* c) {
    auto& sink=*static_cast<Sink*>(context);
    std::cout<<"completion frame="<<c->frame_id<<" status="<<c->status<<" result="<<mav_result_string(c->result)<<" backend="<<c->backend_status<<" size="<<c->width<<"x"<<c->height<<" depth="<<c->bit_depth<<" hardware="<<c->hardware_accelerated<<"\n";
    if(c->status==MAV_COMPLETION_OUTPUT){++sink.outputs;sink.retained=CVPixelBufferRetain(c->pixel_buffer);}else ++sink.failures;
}
int main(int argc,char** argv){@autoreleasepool {
    if(argc!=3){std::cerr<<"usage: mav-codec-probe av1|hevc complete-access-unit.bin\n";return 2;}
    auto codec=std::string(argv[1])=="av1"?MAV_CODEC_AV1:MAV_CODEC_HEVC;
    std::ifstream file(argv[2],std::ios::binary);std::vector<uint8_t> bytes((std::istreambuf_iterator<char>(file)),{});
    Sink sink;mav_config config;mav_config_default(&config,codec);config.completion=output;config.context=&sink;
    mav_decoder* decoder=nullptr;auto result=mav_decoder_create(&config,&decoder);
    if(result!=MAV_OK)return 1;
    mav_span span{bytes.data(),bytes.size()};mav_access_unit unit;mav_access_unit_default(&unit,codec);unit.spans=&span;unit.span_count=1;unit.frame_id=1;
    result=mav_decoder_submit_copy(decoder,&unit);std::cout<<"submit="<<mav_result_string(result)<<"\n";
    mav_decoder_drain(decoder);mav_metrics metrics{};metrics.struct_size=sizeof(metrics);metrics.version=MAV_ABI_VERSION;mav_decoder_get_metrics(decoder,&metrics);std::cout<<"last_backend_status="<<metrics.last_backend_status<<" hardware="<<metrics.hardware_accelerated<<"\n";
    mav_decoder_reset(decoder);mav_decoder_destroy(decoder);
    bool ok=result==MAV_OK&&sink.outputs==1&&sink.failures==0&&metrics.hardware_validated;
    if(sink.retained){
        ok&=CVPixelBufferGetIOSurface(sink.retained)!=nullptr;
        id<MTLDevice> device=MTLCreateSystemDefaultDevice();CVMetalTextureCacheRef cache=nullptr;
        ok&=CVMetalTextureCacheCreate(kCFAllocatorDefault,nullptr,device,nullptr,&cache)==kCVReturnSuccess;
        bool ten=CVPixelBufferGetPixelFormatType(sink.retained)==kCVPixelFormatType_420YpCbCr10BiPlanarVideoRange||CVPixelBufferGetPixelFormatType(sink.retained)==kCVPixelFormatType_420YpCbCr10BiPlanarFullRange;
        for(size_t i=0;cache&&i<2;++i){CVMetalTextureRef texture=nullptr;auto f=i?(ten?MTLPixelFormatRG16Unorm:MTLPixelFormatRG8Unorm):(ten?MTLPixelFormatR16Unorm:MTLPixelFormatR8Unorm);
            auto s=CVMetalTextureCacheCreateTextureFromImage(kCFAllocatorDefault,cache,sink.retained,nullptr,f,CVPixelBufferGetWidthOfPlane(sink.retained,i),CVPixelBufferGetHeightOfPlane(sink.retained,i),i,&texture);
            ok&=s==kCVReturnSuccess&&texture&&CVMetalTextureGetTexture(texture)!=nil;if(texture)CFRelease(texture);}
        if(cache)CFRelease(cache);CVPixelBufferRelease(sink.retained);
    }
    std::cout<<(ok?"PASS":"FAIL")<<": hardware output, retained buffer after reset/destroy, IOSurface and Metal textures\n";return ok?0:1;
}}
