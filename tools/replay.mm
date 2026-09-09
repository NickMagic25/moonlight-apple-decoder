#import <Metal/Metal.h>
#import <CoreVideo/CVMetalTextureCache.h>
#import <IOSurface/IOSurface.h>
#include "moonlight_apple_video/decoder.h"
#include "fixture_support.hpp"
#include <sys/sysctl.h>
#include <unistd.h>
#include <mutex>
#include <condition_variable>
#include <map>
#include <set>
#include <thread>
#include <random>
#include <iostream>
#include <cmath>
#include <memory>
using namespace fixture;
struct Record {mav_completion c{};uint64_t entry=0;CVPixelBufferRef retained=nullptr;};
struct Sink {std::mutex lock;std::vector<Record> records;bool correctness=false;uint64_t overflow=0,retained=0,retainedPeak=0;std::condition_variable ready;bool finished=false;std::string validationError;CVPixelBufferRef ownershipProbe=nullptr;};
static void complete(void* context,const mav_completion* c){
    uint64_t entry=mav_monotonic_time_ns();auto&s=*static_cast<Sink*>(context);std::lock_guard<std::mutex>g(s.lock);
    if(s.records.size()==s.records.capacity()){++s.overflow;return;}
    Record r;r.c=*c;r.entry=entry;if(s.correctness&&c->pixel_buffer){if(s.retained>=32){++s.overflow;}else{r.retained=CVPixelBufferRetain(c->pixel_buffer);++s.retained;s.retainedPeak=std::max(s.retainedPeak,s.retained);if(!s.ownershipProbe)s.ownershipProbe=CVPixelBufferRetain(c->pixel_buffer);}}s.records.push_back(r);s.ready.notify_one();
}
static NSDictionary* distribution(std::vector<double>v){if(v.empty())return @{@"count":@0,@"mean":NSNull.null,@"median":NSNull.null,@"p95":NSNull.null,@"p99":NSNull.null,@"min":NSNull.null,@"max":NSNull.null};std::sort(v.begin(),v.end());double sum=0;for(auto x:v)sum+=x;auto q=[&](double p){double i=p*(v.size()-1);size_t n=size_t(i);return v[n]+(v[std::min(n+1,v.size()-1)]-v[n])*(i-n);};return @{@"count":@(v.size()),@"mean":@(sum/v.size()),@"median":@(q(.5)),@"p95":@(q(.95)),@"p99":@(q(.99)),@"min":@(v.front()),@"max":@(v.back())};}
static void verify(Record&r,const Manifest&m,id<MTLDevice>device,CVMetalTextureCacheRef cache){
    auto&c=r.c;if(c.status!=MAV_COMPLETION_OUTPUT)return;
    if(!r.retained||c.width!=m.width||c.height!=m.height||c.bit_depth!=m.depth||!c.hardware_accelerated)throw std::runtime_error("output dimensions/depth/hardware mismatch");
    auto p=r.retained;auto pf=CVPixelBufferGetPixelFormatType(p);bool ten=pf==kCVPixelFormatType_420YpCbCr10BiPlanarVideoRange||pf==kCVPixelFormatType_420YpCbCr10BiPlanarFullRange;
    if(ten!=(m.depth==10)||CVPixelBufferGetPlaneCount(p)!=2||!CVPixelBufferGetIOSurface(p))throw std::runtime_error("output format/IOSurface mismatch");
    for(size_t plane=0;plane<2;++plane){CVMetalTextureRef texture=nullptr;MTLPixelFormat fmt=plane?(ten?MTLPixelFormatRG16Unorm:MTLPixelFormatRG8Unorm):(ten?MTLPixelFormatR16Unorm:MTLPixelFormatR8Unorm);auto e=CVMetalTextureCacheCreateTextureFromImage(nullptr,cache,p,nullptr,fmt,CVPixelBufferGetWidthOfPlane(p,plane),CVPixelBufferGetHeightOfPlane(p,plane),plane,&texture);if(e||!texture||!CVMetalTextureGetTexture(texture))throw std::runtime_error("Metal texture creation failed");CFRelease(texture);}
    if(m.depth==10&&(!(c.color.valid&MAV_COLOR_DESCRIPTION)||c.color.primaries!=9||c.color.transfer!=16||c.color.matrix!=9||!(c.color.valid&MAV_COLOR_MASTERING)||!(c.color.valid&MAV_COLOR_CONTENT_LIGHT)))throw std::runtime_error("HDR normalized metadata lost");
    if(utf(m.document[@"generator"][@"pattern"])=="moving-gradient-detail-square-frame-id-v1"){
        if(CVPixelBufferLockBaseAddress(p,kCVPixelBufferLock_ReadOnly))throw std::runtime_error("pixel map failed");
        auto b=(uint8_t*)CVPixelBufferGetBaseAddressOfPlane(p,0);auto stride=CVPixelBufferGetBytesPerRowOfPlane(p,0);uint64_t visible=0;
        for(unsigned bit=0;bit<16;++bit){uint32_t x=(2*bit+1)*m.width/32,y=m.height/16;unsigned v=ten?(reinterpret_cast<uint16_t*>(b+y*stride)[x]>>6):b[y*stride+x];if(v>(ten?512:128))visible|=uint64_t(1)<<bit;}
        double variance=0,avg=0;unsigned n=0;for(uint32_t y=m.height/4;y<m.height;y+=std::max(1u,m.height/16))for(uint32_t x=0;x<m.width;x+=std::max(1u,m.width/16)){double v=ten?(reinterpret_cast<uint16_t*>(b+y*stride)[x]>>6):b[y*stride+x];avg+=v;variance+=v*v;++n;}
        CVPixelBufferUnlockBaseAddress(p,kCVPixelBufferLock_ReadOnly);
        size_t sourceIndex=(reinterpret_cast<uintptr_t>(c.caller_context)-1)%m.units.size(); NSDictionary* source=m.document[@"access_units"][sourceIndex]; uint64_t expected=[source[@"expected_visible_frame_id"] unsignedLongLongValue]&65535;
        if(visible!=expected)throw std::runtime_error("visible frame identity mismatch: public "+std::to_string(c.frame_id)+" expected "+std::to_string(expected)+" observed "+std::to_string(visible));
        if(variance/n-(avg/n)*(avg/n)<100)throw std::runtime_error("decoded image lacks known spatial structure");
    }
    (void)device;
}
struct ReferenceStats {uint64_t count=0,sum=0,max=0;};
static void compareReference(Record& r,const Manifest& m,std::ifstream& file,ReferenceStats& stats){
    if(!r.retained||r.c.status!=MAV_COMPLETION_OUTPUT)return;
    size_t source=(reinterpret_cast<uintptr_t>(r.c.caller_context)-1)%m.units.size(),ordinal=0;for(size_t i=0;i<source;++i)ordinal+=m.units[i].displays;
    uint64_t samples=uint64_t(m.width)*m.height*3/2,bytes=samples*(m.depth==10?2:1);std::vector<uint8_t>raw(bytes);file.seekg(ordinal*bytes);file.read(reinterpret_cast<char*>(raw.data()),raw.size());if(!file)throw std::runtime_error("software reference is truncated or expected display order disagrees");
    auto p=r.retained;if(CVPixelBufferLockBaseAddress(p,kCVPixelBufferLock_ReadOnly))throw std::runtime_error("reference comparison map failed");
    uint64_t maximum=0;for(unsigned plane=0;plane<3;++plane){uint32_t w=plane?m.width/2:m.width,h=plane?m.height/2:m.height;size_t base=plane?size_t(m.width)*m.height+(plane-1)*size_t(w)*h:0;auto buffer=(uint8_t*)CVPixelBufferGetBaseAddressOfPlane(p,plane?1:0);size_t stride=CVPixelBufferGetBytesPerRowOfPlane(p,plane?1:0);
        for(uint32_t y=0;y<h;++y)for(uint32_t x=0;x<w;++x){size_t index=base+size_t(y)*w+x,px=plane?x*2+plane-1:x;unsigned want=m.depth==10?uint16_t(raw[index*2])|(uint16_t(raw[index*2+1])<<8):raw[index];unsigned got=m.depth==10?(reinterpret_cast<uint16_t*>(buffer+y*stride)[px]>>6):buffer[y*stride+px];uint64_t error=got>want?got-want:want-got;stats.sum+=error;++stats.count;maximum=std::max(maximum,error);}}
    CVPixelBufferUnlockBaseAddress(p,kCVPixelBufferLock_ReadOnly);stats.max=std::max(stats.max,maximum);if(maximum>(m.depth==10?8:2))throw std::runtime_error("software/native output differs beyond tolerance; max code error="+std::to_string(maximum));
}
static mav_color manifestFallback(const Manifest& manifest){
    mav_color result{};id value=manifest.document[@"color"];if(!value)return result;
    NSDictionary* color=dictionary(value,"color");result.primaries=result.transfer=result.matrix=2;
    bool description=!color[@"description_valid"]||boolean(color[@"description_valid"],"description_valid");
    if(description&&(color[@"primaries"]||color[@"transfer"]||color[@"matrix"])){result.valid|=MAV_COLOR_DESCRIPTION;if(color[@"primaries"])result.primaries=integer(color[@"primaries"],"primaries",255);if(color[@"transfer"])result.transfer=integer(color[@"transfer"],"transfer",255);if(color[@"matrix"])result.matrix=integer(color[@"matrix"],"matrix",255);}
    if(color[@"full_range"]){result.valid|=MAV_COLOR_RANGE;result.full_range=boolean(color[@"full_range"],"full_range");}
    if(color[@"chroma_location"]){result.valid|=MAV_COLOR_CHROMA_LOCATION;result.chroma_location=integer(color[@"chroma_location"],"chroma_location",5);}
    auto metadata=[&](NSString* bytesKey,NSString* validKey,uint8_t* bytes,size_t size,uint32_t bit){
        bool valid=color[validKey]?boolean(color[validKey],validKey.UTF8String):color[bytesKey]!=nil;
        if(!valid)return;
        if(!color[bytesKey])throw std::runtime_error("valid manifest HDR metadata is missing its bytes");
        NSData* data=[[NSData alloc]initWithBase64EncodedString:ns(utf(color[bytesKey])) options:0];
        if(!data||data.length!=size)throw std::runtime_error("invalid manifest HDR metadata length");
        [data getBytes:bytes length:size];result.valid|=bit;
    };
    metadata(@"mastering_base64",@"mastering_valid",result.mastering,sizeof(result.mastering),MAV_COLOR_MASTERING);
    metadata(@"content_light_base64",@"content_light_valid",result.content_light,sizeof(result.content_light),MAV_COLOR_CONTENT_LIGHT);
    return result;
}
int main(int argc,char**argv){@autoreleasepool{mav_decoder*decoder=nullptr;Sink sink;CVMetalTextureCacheRef cache=nullptr;std::thread consumer;ReferenceStats referenceStats;try{
    std::map<std::string,std::string>o;for(int i=1;i<argc;++i){std::string k=argv[i];if(k=="--help"){std::cout<<"mav-replay --fixture manifest.json --output results/run --mode correctness|paced|throughput|fault [--inflight 2 --fps 120 --loops 1 --warmup 12 --power -1 --queue-depth 16 --seed 7 --jitter-us 0 --drop-every 0 --corrupt-every 0 --reset-every 0 --consumer-delay-ms 0 --loop-mode reset|continuous --cold-trace PATH --pool-minimum 0|3|6]\n";return 0;}if(i+1>=argc)throw std::runtime_error("option missing value");o[k]=argv[++i];}
    auto val=[&](std::string k,std::string d){return o.count(k)?o[k]:d;};if(!o.count("--fixture"))throw std::runtime_error("--fixture required");auto m=load(o["--fixture"]);std::string mode=val("--mode","correctness"),out=val("--output","results/replay");
    if(mode!="correctness"&&mode!="paced"&&mode!="throughput"&&mode!="fault")throw std::runtime_error("invalid mode");sink.correctness=mode=="correctness"||mode=="fault";
    std::string loopMode=val("--loop-mode","reset");if(loopMode!="reset"&&loopMode!="continuous")throw std::runtime_error("loop-mode must be reset or continuous");
    size_t loops=std::stoull(val("--loops","1")),warmup=std::stoull(val("--warmup","0"));if(!loops||loops>10000||loops*m.units.size()>1000000)throw std::runtime_error("too many submissions");
    size_t total=loops*m.units.size(),queue=std::stoull(val("--queue-depth","16"));sink.records.reserve(total);
    double fps=std::stod(val("--fps",std::to_string(double(m.fps_num)/m.fps_den)));if(fps<=0||fps>10000||queue<1||queue>4096)throw std::runtime_error("invalid rate/queue depth");
    uint64_t interval=uint64_t(1e9/fps),jitter=std::stoull(val("--jitter-us","0"))*1000,dropEvery=std::stoull(val("--drop-every","0")),corruptEvery=std::stoull(val("--corrupt-every","0")),resetEvery=std::stoull(val("--reset-every","0")),consumerDelay=std::stoull(val("--consumer-delay-ms","0"));
    std::mt19937_64 rng(std::stoull(val("--seed","7")));bool paced=mode=="paced"||mode=="fault";
    mav_config cfg;mav_config_default(&cfg,m.codec=="av1"?MAV_CODEC_AV1:MAV_CODEC_HEVC);cfg.width=m.width;cfg.height=m.height;cfg.bit_depth=m.depth;cfg.max_frames_in_flight=std::stoul(val("--inflight","2"));cfg.power_efficiency=std::stoi(val("--power","-1"));cfg.completion=complete;cfg.context=&sink;cfg.fallback_color=manifestFallback(m);
    std::string referencePath=val("--reference-raw","");auto reference=std::make_shared<std::ifstream>();if(!referencePath.empty()){reference->open(referencePath,std::ios::binary);if(!*reference)throw std::runtime_error("cannot open software reference raw YUV");}
    id<MTLDevice>device=nil;if(sink.correctness){device=MTLCreateSystemDefaultDevice();if(!device||CVMetalTextureCacheCreate(nullptr,nullptr,device,nullptr,&cache))throw std::runtime_error("Metal unavailable");
        consumer=std::thread([&,m,device,cache,consumerDelay,reference,referencePath]{size_t next=0;for(;;){Record record;{std::unique_lock<std::mutex>lock(sink.lock);sink.ready.wait(lock,[&]{return sink.finished||next<sink.records.size();});if(next==sink.records.size()&&sink.finished)break;record=sink.records[next];sink.records[next++].retained=nullptr;}if(record.retained){try{if(consumerDelay)std::this_thread::sleep_for(std::chrono::milliseconds(consumerDelay));verify(record,m,device,cache);if(!referencePath.empty())compareReference(record,m,*reference,referenceStats);}catch(const std::exception&e){std::lock_guard<std::mutex>lock(sink.lock);sink.validationError=e.what();}CVPixelBufferRelease(record.retained);{std::lock_guard<std::mutex>lock(sink.lock);--sink.retained;sink.ready.notify_all();}}}});
    }
    std::string coldTrace=val("--cold-trace","");
    std::string poolMinimum=val("--pool-minimum","0");
    if(poolMinimum!="0"&&poolMinimum!="3"&&poolMinimum!="6")throw std::runtime_error("pool-minimum must be 0, 3, or 6");
    if(o.count("--pool-minimum")&&coldTrace.empty())throw std::runtime_error("pool-minimum requires cold-trace");
    if(o.count("--cold-trace")) {
        if(coldTrace.empty())throw std::runtime_error("cold-trace path is empty");
        auto directory=ns(coldTrace).stringByDeletingLastPathComponent;
        if(directory.length)[[NSFileManager defaultManager]createDirectoryAtPath:directory withIntermediateDirectories:YES attributes:nil error:nil];
        std::ofstream trace(coldTrace,std::ios::trunc);
        if(!trace)throw std::runtime_error("cannot create cold-trace output");
        trace.close();
        if(setenv("MAV_EXPERIMENT_COLD_TRACE",coldTrace.c_str(),1)||setenv("MAV_EXPERIMENT_POOL_MIN",poolMinimum.c_str(),1))throw std::runtime_error("cannot set private cold diagnostic controls");
    }
    auto status=mav_decoder_create(&cfg,&decoder);if(status!=MAV_OK)throw std::runtime_error("BLOCKED create: "+std::string(mav_result_string(status)));
    uint64_t start=mav_monotonic_time_ns()+(paced?20000000:0),offered=0,submitted=0,rejected=0,backpressure=0,drops=0,resets=0,expectedOutputs=0;bool needRandom=false;std::vector<double>schedulerLateness;std::map<uint64_t,uint32_t>expected;
    int64_t mediaStart=m.units.front().pts,mediaEnd=mediaStart; uint64_t idStride=0; for(auto&a:m.units){if(a.pts_valid)mediaEnd=std::max(mediaEnd,a.pts+a.duration);idStride=std::max(idStride,a.id+1);}if(__int128(mediaEnd)-mediaStart>INT64_MAX)throw std::runtime_error("media duration overflow");int64_t mediaDuration=mediaEnd-mediaStart;if(mediaDuration<=0)throw std::runtime_error("fixture loop has no positive media duration"); auto scaled=[&](int64_t value,size_t loop){__int128 v=(__int128(value)+__int128(loop)*mediaDuration)*m.timebase_num;if(v<INT64_MIN||v>INT64_MAX)throw std::runtime_error("media timestamp overflow");return int64_t(v);};
    if(__int128(idStride)*loops>UINT64_MAX)throw std::runtime_error("loop frame IDs overflow");
    for(size_t i=0;i<total;++i){auto&a=m.units[i%m.units.size()];if(a.discontinuity){if(mav_decoder_reset(decoder)!=MAV_OK)throw std::runtime_error("fixture discontinuity reset failed");++resets;needRandom=true;}if(loopMode=="reset"&&i&&i%m.units.size()==0){if(mav_decoder_drain(decoder)!=MAV_OK)throw std::runtime_error("loop drain failed");if(mav_decoder_reset(decoder)!=MAV_OK)throw std::runtime_error("loop reset failed");++resets;}
        uint64_t arrival=paced?start+i*interval:mav_monotonic_time_ns();if(paced&&jitter){int64_t shift=int64_t(rng()%(2*jitter+1))-int64_t(jitter);arrival=uint64_t(std::max(int64_t(start),int64_t(arrival)+shift));}
        while(paced){auto now=mav_monotonic_time_ns();if(now>=arrival)break;std::this_thread::sleep_for(std::chrono::nanoseconds(std::min(arrival-now,uint64_t(1000000))));}
        ++offered;uint64_t attempt=mav_monotonic_time_ns();schedulerLateness.push_back(double(attempt>arrival?attempt-arrival:0));
        bool discard=(dropEvery&&i&&i%dropEvery==0)||(paced&&attempt>arrival+interval*queue);
        if(discard){++drops;needRandom=true;mav_decoder_reset(decoder);++resets;continue;}
        if(resetEvery&&i&&i%resetEvery==0){mav_decoder_reset(decoder);++resets;needRandom=true;}
        if(needRandom&&!a.random){++drops;continue;}if(a.random)needRandom=false;
        mav_access_unit u;mav_access_unit_default(&u,cfg.codec);mav_span span{m.payload.data()+a.offset,size_t(a.size)};std::vector<uint8_t>corrupt;
        if(corruptEvery&&i&&i%corruptEvery==0){corrupt.assign(span.data,span.data+span.size);corrupt[0]=0xff;span.data=corrupt.data();}
        u.spans=&span;u.span_count=1;u.frame_id=a.id+(i/m.units.size())*idStride;u.caller_context=reinterpret_cast<void*>(uintptr_t(i)+1);u.pts={scaled(a.pts,i/m.units.size()),int32_t(m.timebase_den),a.pts_valid};u.dts={scaled(a.dts,i/m.units.size()),int32_t(m.timebase_den),a.dts_valid};u.duration={scaled(a.duration,0),int32_t(m.timebase_den),1};u.flags=a.random?MAV_INPUT_RANDOM_ACCESS:0;u.scheduled_arrival_ns=arrival;
        if(mode=="correctness"){std::unique_lock<std::mutex>lock(sink.lock);sink.ready.wait(lock,[&]{return sink.retained<16;});}
        auto deadline=mav_monotonic_time_ns()+10000000000ull;
        do {status=mav_decoder_submit_copy(decoder,&u);if(status==MAV_WOULD_BLOCK){++backpressure;if(mav_monotonic_time_ns()>deadline)throw std::runtime_error("capacity stalled for 10 seconds");mav_decoder_wait_for_capacity(decoder,1000000);if(paced&&mav_monotonic_time_ns()>arrival+interval*queue){++drops;needRandom=true;mav_decoder_reset(decoder);++resets;break;}}}while(status==MAV_WOULD_BLOCK);
        if(status==MAV_OK){++submitted;expected[u.frame_id]=a.displays;expectedOutputs+=a.displays;}else if(status!=MAV_WOULD_BLOCK){++rejected;if(mode!="fault")throw std::runtime_error("submit "+std::to_string(i)+": "+mav_result_string(status));needRandom=true;mav_decoder_reset(decoder);++resets;}
    }
    status=mav_decoder_drain(decoder);if(status!=MAV_OK)throw std::runtime_error("drain failed");uint64_t end=mav_monotonic_time_ns();mav_metrics metrics{};metrics.struct_size=sizeof(metrics);metrics.version=MAV_ABI_VERSION;mav_decoder_get_metrics(decoder,&metrics);
    // Retained outputs are deliberately inspected after reset AND destruction.
    if(mav_decoder_reset(decoder)!=MAV_OK||mav_decoder_destroy(decoder)!=MAV_OK)throw std::runtime_error("teardown failed");decoder=nullptr;
    {std::lock_guard<std::mutex>lock(sink.lock);sink.finished=true;}sink.ready.notify_all();if(consumer.joinable())consumer.join();
    if(!sink.validationError.empty())throw std::runtime_error(sink.validationError);
    if(sink.ownershipProbe){if(CVPixelBufferLockBaseAddress(sink.ownershipProbe,kCVPixelBufferLock_ReadOnly))throw std::runtime_error("retained buffer invalid after destruction");volatile uint8_t byte=*((uint8_t*)CVPixelBufferGetBaseAddressOfPlane(sink.ownershipProbe,0));(void)byte;CVPixelBufferUnlockBaseAddress(sink.ownershipProbe,kCVPixelBufferLock_ReadOnly);}
    if(metrics.accepted!=metrics.completed||metrics.outstanding||sink.overflow||sink.records.size()!=submitted)throw std::runtime_error("terminal completion/capacity/trace accounting mismatch");
    std::set<uint64_t>ids;uint64_t outputs=0,failures=0,noDisplay=0,existing=0,displayMismatches=0;
    for(auto&r:sink.records){if(!ids.insert(r.c.frame_id).second||!expected.count(r.c.frame_id))throw std::runtime_error("duplicate or unexpected completion");if(mode!="fault"&&r.c.displayed_outputs!=expected[r.c.frame_id])++displayMismatches;if(r.c.status==MAV_COMPLETION_OUTPUT){++outputs;existing+=r.c.show_existing_frame;}else if(r.c.status==MAV_COMPLETION_NO_DISPLAY)++noDisplay;else ++failures;}
    bool passed=mode=="fault"?outputs>0:!(failures||drops||rejected||displayMismatches||outputs!=expectedOutputs||!metrics.hardware_validated);
    [[NSFileManager defaultManager]createDirectoryAtPath:ns(out).stringByDeletingLastPathComponent withIntermediateDirectories:YES attributes:nil error:nil];
    std::ofstream csv(out+".csv");csv<<"frame_id,generation,status,result,trace_valid,internal_samples,displayed_outputs,show_existing,scheduled_arrival_ns,admission_ns,preparation_start_ns,preparation_end_ns,vt_submit_ns,vt_return_ns,callback_ns,handoff_ns,sink_entry_ns,hardware,bit_depth,pixel_format\n";
    std::vector<double>decode,prep,queueWait,submission,available,handoff,coldDecodes;id cold=NSNull.null;std::map<uint64_t,uint64_t>firstInGeneration;for(auto&r:sink.records)if(r.c.status==MAV_COMPLETION_OUTPUT){auto&first=firstInGeneration[r.c.generation];uint64_t index=reinterpret_cast<uintptr_t>(r.c.caller_context);if(!first||index<first)first=index;}
    for(auto&r:sink.records){auto&c=r.c;auto&t=c.trace;csv<<c.frame_id<<','<<c.generation<<','<<c.status<<','<<c.result<<','<<t.valid<<','<<c.internal_samples<<','<<c.displayed_outputs<<','<<c.show_existing_frame<<','<<t.scheduled_arrival_ns<<','<<t.admission_ns<<','<<t.preparation_start_ns<<','<<t.preparation_end_ns<<','<<t.vt_submit_ns<<','<<t.vt_return_ns<<','<<t.callback_ns<<','<<t.handoff_ns<<','<<r.entry<<','<<c.hardware_accelerated<<','<<c.bit_depth<<','<<c.pixel_format<<'\n';
        if(c.status!=MAV_COMPLETION_OUTPUT||c.internal_samples!=1||c.show_existing_frame)continue;bool coldGeneration=firstInGeneration[c.generation]==reinterpret_cast<uintptr_t>(c.caller_context);if((t.valid&(MAV_TRACE_CALLBACK|MAV_TRACE_VT_SUBMIT))==(MAV_TRACE_CALLBACK|MAV_TRACE_VT_SUBMIT)&&t.callback_ns>=t.vt_submit_ns){if(coldGeneration){coldDecodes.push_back(t.callback_ns-t.vt_submit_ns);if(cold==NSNull.null)cold=@(t.callback_ns-t.vt_submit_ns);}if(!coldGeneration&&reinterpret_cast<uintptr_t>(c.caller_context)-1>=warmup)decode.push_back(t.callback_ns-t.vt_submit_ns);}if(coldGeneration||reinterpret_cast<uintptr_t>(c.caller_context)-1<warmup)continue;
        if(t.valid&MAV_TRACE_PREPARATION)prep.push_back(t.preparation_end_ns-t.preparation_start_ns);if((t.valid&MAV_TRACE_ARRIVAL)&&t.admission_ns>=t.scheduled_arrival_ns)queueWait.push_back(t.admission_ns-t.scheduled_arrival_ns);if((t.valid&(MAV_TRACE_VT_SUBMIT|MAV_TRACE_VT_RETURN))==(MAV_TRACE_VT_SUBMIT|MAV_TRACE_VT_RETURN))submission.push_back(t.vt_return_ns-t.vt_submit_ns);if((t.valid&(MAV_TRACE_ARRIVAL|MAV_TRACE_CALLBACK))==(MAV_TRACE_ARRIVAL|MAV_TRACE_CALLBACK)&&t.callback_ns>=t.scheduled_arrival_ns)available.push_back(t.callback_ns-t.scheduled_arrival_ns);if((t.valid&MAV_TRACE_CALLBACK)&&r.entry>=t.callback_ns)handoff.push_back(r.entry-t.callback_ns);
    }
    char model[128]={};size_t modelSize=sizeof(model);sysctlbyname("hw.model",model,&modelSize,nullptr,0);double seconds=double(end-start)/1e9;
    NSDictionary*result=@{@"status":passed?@"PASS":@"FAIL",@"cold_trace_path":coldTrace.empty()?static_cast<id>(NSNull.null):ns(coldTrace),@"pool_minimum_requested":coldTrace.empty()?static_cast<id>(NSNull.null):ns(poolMinimum),@"mode":ns(mode),@"codec":ns(m.codec),@"variant":ns(m.variant),@"width":@(m.width),@"height":@(m.height),@"bit_depth":@(m.depth),@"chroma":@"420",@"fixture_sha256":ns(m.hash),@"model":ns(model),@"os":NSProcessInfo.processInfo.operatingSystemVersionString,@"clock":@"mav_monotonic_time_ns CLOCK_UPTIME_RAW",@"requested_fps":@(fps),@"offered":@(offered),@"submitted":@(submitted),@"completed":@(metrics.completed),@"internal_samples":@(metrics.internal_samples),@"displayed_outputs":@(outputs),@"no_display":@(noDisplay),@"show_existing":@(existing),@"rejected":@(rejected),@"failed_or_cancelled_or_dropped":@(failures),@"scheduler_drops":@(drops),@"expected_display_mismatches":@(displayMismatches),@"resets":@(resets),@"backpressure":@(backpressure),@"peak_outstanding":@(metrics.peak_outstanding),@"compressed_copy_count":@(metrics.compressed_copy_count),@"compressed_copy_bytes":@(metrics.compressed_copy_bytes),@"trace_overflow":@(sink.overflow),@"hardware_validated":@(metrics.hardware_validated),@"pixel_format":@(metrics.pixel_format),@"inflight":@(cfg.max_frames_in_flight),@"power_requested":@(cfg.power_efficiency),@"power_status":@(metrics.power_efficiency_status),@"power_effective":@(metrics.power_efficiency_effective),@"realtime_status":@(metrics.realtime_status),@"realtime_effective":@(metrics.realtime_effective),@"warmup_frames":@(warmup),@"loops":@(loops),@"loop_mode":ns(loopMode),@"run_seconds":@(seconds),@"actual_offered_fps":@(offered/seconds),@"admission_fps":@(submitted/seconds),@"decoded_fps":@(outputs/seconds),@"cold_vt_submit_to_callback_ns":cold,@"cold_generation_vt_submit_to_callback_ns":distribution(coldDecodes),@"steady_excludes_first_output_each_generation":@YES,@"vt_submit_to_callback_ns":distribution(decode),@"preparation_ns":distribution(prep),@"queue_wait_ns":distribution(queueWait),@"submission_call_ns":distribution(submission),@"complete_au_to_output_ns":distribution(available),@"callback_to_client_handoff_ns":distribution(handoff),@"scheduler_lateness_ns":distribution(schedulerLateness),@"render_ns":NSNull.null,@"presentation_ns":NSNull.null,@"thermal_state":@(NSProcessInfo.processInfo.thermalState),@"power_state":NSNull.null,@"manifest_fallback_color_valid":@(cfg.fallback_color.valid),@"scheduler_lateness_population":@"all offered arrivals, including cold, warmup and losses",@"software_reference_samples":@(referenceStats.count),@"software_reference_max_code_error":referenceStats.count?@(referenceStats.max):NSNull.null,@"software_reference_mean_code_error":referenceStats.count?@(double(referenceStats.sum)/referenceStats.count):NSNull.null,@"software_reference_tolerance":@(m.depth==10?8:2),@"correctness_sink":@(sink.correctness),@"consumer_retention_delay_ms":@(consumerDelay),@"consumer_delay_semantics":@"bounded 32-buffer validation worker delayed per output",@"retained_peak":@(sink.retainedPeak),@"retained_after_destroy_verified":@(sink.correctness),@"iosurface_metal_verified":@(sink.correctness)};
    json(out+".json",result);for(auto&r:sink.records)if(r.retained)CVPixelBufferRelease(r.retained);if(cache)CFRelease(cache);cache=nullptr;if(sink.ownershipProbe)CVPixelBufferRelease(sink.ownershipProbe);sink.ownershipProbe=nullptr;
    std::cout<<(passed?"PASS ":"FAIL ")<<m.codec<<" "<<m.variant<<" outputs="<<outputs<<" accepted="<<submitted<<" median_vt_ms="<<([result[@"vt_submit_to_callback_ns"][@"count"] unsignedLongLongValue]?std::to_string([result[@"vt_submit_to_callback_ns"][@"median"] doubleValue]/1e6):"unavailable")<<" result="<<out<<".json\n";return passed?0:1;
}catch(const std::exception&e){if(decoder)mav_decoder_destroy(decoder);{std::lock_guard<std::mutex>lock(sink.lock);sink.finished=true;}sink.ready.notify_all();if(consumer.joinable())consumer.join();if(sink.ownershipProbe)CVPixelBufferRelease(sink.ownershipProbe);for(auto&r:sink.records)if(r.retained)CVPixelBufferRelease(r.retained);if(cache)CFRelease(cache);std::string failOut="results/replay";for(int i=1;i+1<argc;++i)if(std::string(argv[i])=="--output")failOut=argv[i+1];[[NSFileManager defaultManager]createDirectoryAtPath:ns(failOut).stringByDeletingLastPathComponent withIntermediateDirectories:YES attributes:nil error:nil];try{json(failOut+".json",@{@"status":@"FAIL",@"reason":ns(e.what()),@"completed_records":@(sink.records.size()),@"vt_submit_to_callback_ns":NSNull.null});}catch(...){}std::cerr<<"FAIL/BLOCKED: "<<e.what()<<"\n";return 1;}}}
