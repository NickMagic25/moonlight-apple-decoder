#include "backend.hpp"
#include "color.hpp"
#include <algorithm>
#include <chrono>
#include <condition_variable>
#include <cstring>
#include <limits>
#include <map>
#include <mutex>
#include <new>
using namespace mav;
namespace { thread_local unsigned callback_depth=0; struct CallbackScope { CallbackScope(){++callback_depth;} ~CallbackScope(){--callback_depth;} }; }
struct Submission {
    uint64_t serial=0; mav_completion completion{}; mav_color bitstream_color{};
    size_t remaining=0; std::vector<std::shared_ptr<Work>> work;
    ~Submission(){if(completion.pixel_buffer) release_pixel(completion.pixel_buffer);}
};
struct mav_decoder {
    mav_config config; Bitstream parser; std::unique_ptr<Backend> backend;
    std::mutex operation,state; std::condition_variable capacity;
    std::map<uint64_t,std::shared_ptr<Submission>> pending;
    uint64_t serial=0; bool closing=false,need_random_access=true,configured=false;
    Format format; mav_color format_color{}; mav_metrics metrics{};
    explicit mav_decoder(const mav_config& c):config(c),parser(c.codec==MAV_CODEC_AV1?Codec::AV1:Codec::HEVC),backend(make_backend()) {
        metrics.struct_size=sizeof(metrics); metrics.version=MAV_ABI_VERSION;metrics.generation=1;
        metrics.realtime_effective=metrics.power_efficiency_effective=metrics.thread_count_effective=-1;
    }
    void info() {
        auto i=backend->info(); std::lock_guard<std::mutex> l(state);
        metrics.hardware_accelerated=i.hardware;metrics.pixel_format=i.pixel_format;
        metrics.realtime_status=i.realtime_status;metrics.power_efficiency_status=i.power_status;
        metrics.thread_count_status=i.thread_status;metrics.last_backend_status=i.last_status;
        metrics.realtime_effective=i.realtime_effective;metrics.power_efficiency_effective=i.power_effective;
        metrics.thread_count_effective=i.thread_effective;
    }
    void complete(const std::shared_ptr<Submission>& s,const BackendOutput& output,bool display) {
        bool terminal=false;
        {
            std::lock_guard<std::mutex> l(state);
            if(!pending.count(s->serial)||!s->remaining) return;
            auto& c=s->completion;
            if(c.generation!=metrics.generation||closing) {
                if(c.status!=MAV_COMPLETION_FAILED&&c.status!=MAV_COMPLETION_DROPPED){c.status=MAV_COMPLETION_CANCELLED;c.result=MAV_OK;}
            }
            else if(output.result!=MAV_OK) {
                c.status=MAV_COMPLETION_FAILED;c.result=output.result;c.backend_status=output.status;
                if(!need_random_access)++metrics.generation;
                need_random_access=true;metrics.hardware_validated=0;metrics.last_backend_status=output.status;
            } else if(output.dropped&&c.status!=MAV_COMPLETION_FAILED) {
                c.status=MAV_COMPLETION_DROPPED;
                // Suppress dependents already admitted under the failed generation.
                if(!need_random_access)++metrics.generation;
                need_random_access=true;metrics.hardware_validated=0;
            } else if(output.image&&display&&c.status!=MAV_COMPLETION_FAILED) {
                if(c.pixel_buffer) release_pixel(c.pixel_buffer);
                c.pixel_buffer=output.image;retain_pixel(output.image);
                c.status=MAV_COMPLETION_OUTPUT;c.displayed_outputs=1;
                c.width=output.width;c.height=output.height;c.pixel_format=output.pixel_format;
                c.color=merge_color(s->bitstream_color,merge_color(output.color,c.color));
                if(c.hardware_accelerated) metrics.hardware_validated=1;
            }
            if(output.callback_ns) {c.trace.callback_ns=std::max(c.trace.callback_ns,output.callback_ns);c.trace.valid|=MAV_TRACE_CALLBACK;}
            if(--s->remaining==0) {
                if(c.status!=MAV_COMPLETION_OUTPUT) {c.displayed_outputs=0;if(c.pixel_buffer){release_pixel(c.pixel_buffer);c.pixel_buffer=nullptr;}}
                uint64_t first=UINT64_MAX,last_return=0; bool returns=true;uint32_t calls=0;
                for(const auto& w:s->work) {
                    auto a=w->submit_ns.load(),b=w->return_ns.load();
                    if(a){first=std::min(first,a);++calls;if(!b)returns=false;}
                    last_return=std::max(last_return,b);
                }
                c.internal_samples=calls;
                if(calls){c.trace.vt_submit_ns=first;c.trace.valid|=MAV_TRACE_VT_SUBMIT;}
                if(calls&&returns){c.trace.vt_return_ns=last_return;c.trace.valid|=MAV_TRACE_VT_RETURN;}
                c.trace.handoff_ns=mav_monotonic_time_ns();
                ++metrics.completed;metrics.displayed+=c.displayed_outputs;
                if(c.status==MAV_COMPLETION_NO_DISPLAY)++metrics.no_display;
                if(c.status==MAV_COMPLETION_FAILED)++metrics.failed;
                if(c.status==MAV_COMPLETION_DROPPED)++metrics.dropped;
                if(c.status==MAV_COMPLETION_CANCELLED)++metrics.cancelled;
                pending.erase(s->serial);metrics.outstanding=pending.size();terminal=true;
            }
        }
        if(terminal) {
            capacity.notify_all();
            CallbackScope guard;
            config.completion(config.context,&s->completion);
            if(config.capacity_available)config.capacity_available(config.context);
        }
    }
    void resolve_missing(bool cancel) {
        for(;;) {
            std::shared_ptr<Submission> s;
            {std::lock_guard<std::mutex> l(state);if(pending.empty())break;s=pending.begin()->second;s->remaining=1;}
            BackendOutput o; o.result=cancel?MAV_OK:MAV_DECODER_FAILED;
            complete(s,o,false);
        }
    }
};
namespace {
bool tag(uint32_t size,uint32_t version,size_t required){return size>=required&&version==MAV_ABI_VERSION;}
mav_result reject(mav_decoder* d,mav_result r){std::lock_guard<std::mutex> l(d->state);if(r==MAV_WOULD_BLOCK)++d->metrics.would_block;else ++d->metrics.rejected;return r;}
mav_result parse_result(ParseResult r){switch(r){case ParseResult::Ok:return MAV_OK;case ParseResult::Malformed:return MAV_MALFORMED_INPUT;case ParseResult::Unsupported:return MAV_UNSUPPORTED;case ParseResult::NeedConfiguration:return MAV_NEED_RANDOM_ACCESS;}return MAV_MALFORMED_INPUT;}
mav_result submit(mav_decoder* d,const mav_access_unit* u) {
    if(!d||!u)return MAV_INVALID_ARGUMENT;
    if(callback_depth)return MAV_REENTRANT_CALL;
    std::unique_lock<std::mutex> op(d->operation,std::try_to_lock);
    if(!op.owns_lock())return reject(d,MAV_WOULD_BLOCK);
    if(!tag(u->struct_size,u->version,sizeof(*u))||u->codec!=d->config.codec||!u->spans||!u->span_count||u->span_count>MAV_MAX_SPANS||
        (u->flags&~(MAV_INPUT_RANDOM_ACCESS|MAV_INPUT_DISCONTINUITY))||!valid_color(u->color)||
        u->framing!=(u->codec==MAV_CODEC_AV1?MAV_FRAMING_AV1_LOW_OVERHEAD:MAV_FRAMING_HEVC_ANNEX_B)) return reject(d,MAV_INVALID_ARGUMENT);
    for(auto t:{u->pts,u->dts,u->duration}) if(t.valid&&t.timescale<=0)return reject(d,MAV_INVALID_ARGUMENT);
    // This initial path is explicitly decode-order==presentation-order.
    if(u->pts.valid&&u->dts.valid && (__int128)u->pts.value*u->dts.timescale!=(__int128)u->dts.value*u->pts.timescale)return reject(d,MAV_UNSUPPORTED);
    uint64_t generation;size_t outstanding;bool recovery;
    {std::lock_guard<std::mutex> l(d->state);if(d->closing)return MAV_CLOSED;outstanding=d->pending.size();generation=d->metrics.generation;recovery=d->need_random_access;}
    if(outstanding>=d->config.max_frames_in_flight)return reject(d,MAV_WOULD_BLOCK);
    if((u->flags&MAV_INPUT_DISCONTINUITY)&&d->configured)return reject(d,MAV_NEED_RANDOM_ACCESS);
    auto s=std::make_shared<Submission>();auto& c=s->completion;
    c.struct_size=sizeof(c);c.version=MAV_ABI_VERSION;c.frame_id=u->frame_id;c.generation=generation;c.caller_context=u->caller_context;
    c.status=MAV_COMPLETION_NO_DISPLAY;c.pts=u->pts;c.duration=u->duration;
    c.trace.admission_ns=mav_monotonic_time_ns();c.trace.preparation_start_ns=c.trace.admission_ns;
    c.trace.scheduled_arrival_ns=u->scheduled_arrival_ns;c.trace.first_packet_ns=u->first_packet_ns;
    if(u->scheduled_arrival_ns)c.trace.valid|=MAV_TRACE_ARRIVAL;if(u->first_packet_ns)c.trace.valid|=MAV_TRACE_FIRST_PACKET;
    size_t total=0;std::vector<Span> spans;spans.reserve(u->span_count);
    for(size_t n=0;n<u->span_count;++n){const auto& p=u->spans[n];if((!p.data&&p.size)||p.size>MAV_MAX_ACCESS_UNIT_BYTES-total)return reject(d,MAV_INVALID_ARGUMENT);total+=p.size;spans.push_back({p.data,p.size});}
    if(!total)return reject(d,MAV_INVALID_ARGUMENT);
    auto candidate=d->parser; Prepared p;std::string error;
    auto parsed=candidate.prepare(spans.data(),spans.size(),p,error);
    if(parsed!=ParseResult::Ok)return reject(d,parse_result(parsed));
    c.trace.preparation_end_ns=mav_monotonic_time_ns();c.trace.valid|=MAV_TRACE_PREPARATION;
    bool has_picture=!p.samples.empty();
    // A previously admitted frame may fail while this AU is being parsed.
    {std::lock_guard<std::mutex> l(d->state);recovery=d->need_random_access;}
    if(has_picture) {
        if((d->config.width&&p.format.width!=d->config.width)||(d->config.height&&p.format.height!=d->config.height)||
            (d->config.bit_depth&&p.format.bit_depth!=d->config.bit_depth)||p.format.chroma!=1)return reject(d,MAV_UNSUPPORTED);
        if(recovery&&!p.random_access)return reject(d,MAV_NEED_RANDOM_ACCESS);
    }
    s->bitstream_color=parsed_color(p.format.color);
    c.color=merge_color(s->bitstream_color,merge_color(u->color,d->config.fallback_color));
    if(!valid_color(c.color))return reject(d,MAV_MALFORMED_INPUT);
    bool changed=has_picture&&(!d->configured||!(p.format==d->format)||std::memcmp(&c.color,&d->format_color,sizeof(c.color))||recovery);
    if(changed) {
        if(outstanding)return reject(d,MAV_WOULD_BLOCK);
        if(d->configured&&!p.random_access)return reject(d,MAV_NEED_RANDOM_ACCESS);
        if(d->configured){std::lock_guard<std::mutex> l(d->state);c.generation=++d->metrics.generation;}
        auto result=d->backend->configure(p.format,d->config,c.color);d->info();
        if(result!=MAV_OK){d->configured=false;{std::lock_guard<std::mutex> l(d->state);d->need_random_access=true;d->metrics.hardware_validated=0;}return reject(d,result);}
        d->configured=true;d->format=p.format;d->format_color=c.color;
        {std::lock_guard<std::mutex> l(d->state);++d->metrics.session_creations;d->metrics.hardware_validated=0;if(d->metrics.session_creations>1)++d->metrics.recoveries;}
    }
    c.bit_depth=p.format.bit_depth;c.width=p.format.width;c.height=p.format.height;
    auto bi=d->backend->info();c.hardware_accelerated=bi.hardware;c.pixel_format=bi.pixel_format;
    auto bytes=std::make_shared<std::vector<uint8_t>>(std::move(p.bytes));
    s->work.reserve(p.samples.size());
    for(const auto& ps:p.samples) {
        auto w=std::make_shared<Work>();w->bytes=bytes;w->offset=ps.offset;w->size=ps.size;
        w->pts=u->pts;w->dts=u->dts;w->duration=u->duration;w->display=ps.display;w->random_access=ps.random_access;w->show_existing=ps.show_existing;
        if(ps.show_existing)c.show_existing_frame=1;
        std::weak_ptr<Submission> weak=s;bool display=ps.display;
        w->complete=[d,weak,display](const BackendOutput& o){if(auto held=weak.lock())d->complete(held,o,display);};
        s->work.push_back(std::move(w));
    }
    s->remaining=std::max<size_t>(1,s->work.size());s->serial=++d->serial;
    {std::lock_guard<std::mutex> l(d->state);
        // Do not erase an async error which arrived after the recovery snapshot.
        // Retry a random-access AU so the next attempt recreates the session.
        if(has_picture&&d->need_random_access&&!recovery){
            if(p.random_access){++d->metrics.would_block;return MAV_WOULD_BLOCK;}
            ++d->metrics.rejected;return MAV_NEED_RANDOM_ACCESS;
        }
        c.generation=d->metrics.generation;
        d->pending.emplace(s->serial,s);++d->metrics.accepted;d->metrics.outstanding=d->pending.size();
        d->metrics.peak_outstanding=std::max(d->metrics.peak_outstanding,d->metrics.outstanding);
        d->metrics.compressed_copy_count+=p.compressed_copy_count;d->metrics.compressed_copy_bytes+=p.compressed_copy_bytes;
        if(has_picture&&p.random_access)d->need_random_access=false;
    }
    d->parser=std::move(candidate);
    if(s->work.empty()){BackendOutput o;d->complete(s,o,false);}
    else for(const auto& w:s->work) {
        d->backend->submit(w);
        if(w->submit_ns.load()){std::lock_guard<std::mutex> l(d->state);++d->metrics.internal_samples;}
    }
    return MAV_OK;
}
mav_result control(mav_decoder* d,int mode) {
    if(!d)return MAV_INVALID_ARGUMENT;if(callback_depth)return MAV_REENTRANT_CALL;
    std::unique_lock<std::mutex> op(d->operation,std::try_to_lock);if(!op.owns_lock())return MAV_WOULD_BLOCK;
    if(mode){std::lock_guard<std::mutex> l(d->state);++d->metrics.generation;d->need_random_access=true;if(mode==2)d->closing=true;}
    auto r=d->backend->drain();
    if(mode)d->backend->invalidate();
    d->resolve_missing(mode!=0);
    if(mode){d->parser.clear();d->configured=false;std::lock_guard<std::mutex> l(d->state);d->metrics.hardware_validated=0;}
    d->capacity.notify_all();
    if(mode==2){op.unlock();delete d;}
    return r;
}
}
extern "C" {
void mav_config_default(mav_config* c,mav_codec codec){if(!c)return;std::memset(c,0,sizeof(*c));c->struct_size=sizeof(*c);c->version=MAV_ABI_VERSION;c->codec=codec;c->max_frames_in_flight=2;c->realtime=1;c->power_efficiency=-1;}
void mav_access_unit_default(mav_access_unit* u,mav_codec codec){if(!u)return;std::memset(u,0,sizeof(*u));u->struct_size=sizeof(*u);u->version=MAV_ABI_VERSION;u->codec=codec;u->framing=codec==MAV_CODEC_AV1?MAV_FRAMING_AV1_LOW_OVERHEAD:MAV_FRAMING_HEVC_ANNEX_B;}
const char* mav_result_string(mav_result r){switch(r){case MAV_OK:return "OK";case MAV_WOULD_BLOCK:return "WOULD_BLOCK";case MAV_INVALID_ARGUMENT:return "INVALID_ARGUMENT";case MAV_MALFORMED_INPUT:return "MALFORMED_INPUT";case MAV_UNSUPPORTED:return "UNSUPPORTED";case MAV_NEED_RANDOM_ACCESS:return "NEED_RANDOM_ACCESS";case MAV_DECODER_FAILED:return "DECODER_FAILED";case MAV_OUT_OF_MEMORY:return "OUT_OF_MEMORY";case MAV_REENTRANT_CALL:return "REENTRANT_CALL";case MAV_CLOSED:return "CLOSED";case MAV_TIMEOUT:return "TIMEOUT";case MAV_API_UNAVAILABLE:return "API_UNAVAILABLE";}return "UNKNOWN";}
mav_result mav_query_capability(mav_codec codec,mav_capability* c){if(!c||!tag(c->struct_size,c->version,sizeof(*c))||(codec!=MAV_CODEC_AV1&&codec!=MAV_CODEC_HEVC))return MAV_INVALID_ARGUMENT;return backend_capability(codec,*c);}
mav_result mav_decoder_create(const mav_config* c,mav_decoder** out){
    if(!out)return MAV_INVALID_ARGUMENT;*out=nullptr;
    if(!c||!tag(c->struct_size,c->version,sizeof(*c))||!c->completion||(c->codec!=MAV_CODEC_AV1&&c->codec!=MAV_CODEC_HEVC)||
       !c->max_frames_in_flight||c->max_frames_in_flight>64||c->pixel_format_count>8||c->hardware_policy>MAV_HARDWARE_PREFERRED||c->hardware_policy<0||
       c->realtime<0||c->realtime>1||c->power_efficiency< -1||c->power_efficiency>1||!valid_color(c->fallback_color)||
       (c->bit_depth&&c->bit_depth!=8&&c->bit_depth!=10)||c->width>65536||c->height>65536)return MAV_INVALID_ARGUMENT;
    if(c->power_efficiency==1&&c->realtime)return MAV_UNSUPPORTED;
    try{auto d=new mav_decoder(*c);*out=d;return MAV_OK;}catch(const std::bad_alloc&){return MAV_OUT_OF_MEMORY;}catch(...){return MAV_DECODER_FAILED;}
}
mav_result mav_decoder_submit_copy(mav_decoder* d,const mav_access_unit* u){try{return submit(d,u);}catch(const std::bad_alloc&){return MAV_OUT_OF_MEMORY;}catch(...){return MAV_DECODER_FAILED;}}
mav_result mav_decoder_drain(mav_decoder* d){return control(d,0);}
mav_result mav_decoder_reset(mav_decoder* d){return control(d,1);}
mav_result mav_decoder_destroy(mav_decoder* d){if(!d)return MAV_OK;return control(d,2);}
mav_result mav_decoder_get_metrics(mav_decoder* d,mav_metrics* m){if(!d||!m||!tag(m->struct_size,m->version,sizeof(*m)))return MAV_INVALID_ARGUMENT;std::lock_guard<std::mutex> l(d->state);*m=d->metrics;return MAV_OK;}
mav_result mav_decoder_wait_for_capacity(mav_decoder* d,uint64_t ns){
    if(!d)return MAV_INVALID_ARGUMENT;if(callback_depth)return MAV_REENTRANT_CALL;
    std::unique_lock<std::mutex> l(d->state);auto pred=[&]{return d->closing||d->pending.size()<d->config.max_frames_in_flight;};
    if(ns==UINT64_MAX)d->capacity.wait(l,pred);
    else if(!d->capacity.wait_for(l,std::chrono::nanoseconds(std::min<uint64_t>(ns,INT64_MAX)),pred))return MAV_TIMEOUT;
    return d->closing?MAV_CLOSED:MAV_OK;
}
}
