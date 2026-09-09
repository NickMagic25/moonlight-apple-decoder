#include "moonlight_apple_video/decoder.h"
#include "backend_fake.hpp"
#include "test_stream.hpp"
#include <atomic>
#include <chrono>
#include <cstdlib>
#include <iostream>
#include <mutex>
#include <thread>
#include <vector>
#define CHECK(x) do{if(!(x)){std::cerr<<__FILE__<<":"<<__LINE__<<": "#x"\n";std::abort();}}while(0)
using mav_test::Mode;
struct Sink {
    mav_decoder* decoder=nullptr;std::mutex mutex;std::vector<mav_completion> completions;
    bool check_reentrancy=false;std::atomic<unsigned> notifications{0};
};
void callback(void* p,const mav_completion* c) {
    auto& sink=*static_cast<Sink*>(p);
    if(sink.check_reentrancy){
        CHECK(mav_decoder_reset(sink.decoder)==MAV_REENTRANT_CALL);
        CHECK(mav_decoder_drain(sink.decoder)==MAV_REENTRANT_CALL);
        CHECK(mav_decoder_destroy(sink.decoder)==MAV_REENTRANT_CALL);
        CHECK(mav_decoder_wait_for_capacity(sink.decoder,0)==MAV_REENTRANT_CALL);
        mav_access_unit u;mav_access_unit_default(&u,MAV_CODEC_AV1);
        CHECK(mav_decoder_submit_copy(sink.decoder,&u)==MAV_REENTRANT_CALL);
        mav_metrics m{};m.struct_size=sizeof(m);m.version=MAV_ABI_VERSION;
        CHECK(mav_decoder_get_metrics(sink.decoder,&m)==MAV_OK);
    }
    std::lock_guard<std::mutex> l(sink.mutex);sink.completions.push_back(*c);
}
void notification(void* p){++static_cast<Sink*>(p)->notifications;}
void create(Sink& sink,unsigned max=2){mav_config c;mav_config_default(&c,MAV_CODEC_AV1);c.completion=callback;c.capacity_available=notification;c.context=&sink;c.max_frames_in_flight=max;CHECK(mav_decoder_create(&c,&sink.decoder)==MAV_OK);}
mav_result submit(Sink& sink,const std::vector<uint8_t>& data,uint64_t id=1){mav_span span{data.data(),data.size()};mav_access_unit u;mav_access_unit_default(&u,MAV_CODEC_AV1);u.spans=&span;u.span_count=1;u.frame_id=id;return mav_decoder_submit_copy(sink.decoder,&u);}
mav_result submit_fragmented(Sink& sink,const std::vector<uint8_t>& data,uint64_t id,bool fragmented){
    if(!fragmented)return submit(sink,data,id);
    size_t boundary=data.size()/2;mav_span spans[]={{data.data(),boundary},{data.data()+boundary,data.size()-boundary}};
    mav_access_unit u;mav_access_unit_default(&u,MAV_CODEC_AV1);u.spans=spans;u.span_count=2;u.frame_id=id;return mav_decoder_submit_copy(sink.decoder,&u);
}
mav_metrics metrics(Sink& sink){mav_metrics m{};m.struct_size=sizeof(m);m.version=MAV_ABI_VERSION;CHECK(mav_decoder_get_metrics(sink.decoder,&m)==MAV_OK);return m;}
void destroy(Sink& s){CHECK(mav_decoder_destroy(s.decoder)==MAV_OK);s.decoder=nullptr;CHECK(mav_test::retained()==0);}
int main(){
    const auto key=mav_test::av1_key_unit();const auto inter=mav_test::av1_frame(false,true);
    {Sink s;create(s);s.check_reentrancy=true;mav_test::mode(Mode::Inline);
        CHECK(submit(s,key)==MAV_OK);CHECK(s.completions.size()==1);auto c=s.completions[0];
        CHECK(c.status==MAV_COMPLETION_OUTPUT);CHECK(c.trace.valid&MAV_TRACE_VT_SUBMIT);CHECK(c.trace.valid&MAV_TRACE_CALLBACK);
        CHECK(!(c.trace.valid&MAV_TRACE_VT_RETURN));CHECK(c.trace.callback_ns>=c.trace.vt_submit_ns);
        CHECK(submit(s,inter,2)==MAV_OK);CHECK(metrics(s).session_creations==1);CHECK(metrics(s).accepted==2);destroy(s);}
    {Sink s;create(s);mav_test::mode(Mode::Inline);CHECK(submit(s,mav_test::av1_sequence())==MAV_OK);
        CHECK(s.completions.size()==1&&s.completions[0].status==MAV_COMPLETION_NO_DISPLAY);CHECK(metrics(s).internal_samples==0);
        CHECK(submit(s,inter)==MAV_NEED_RANDOM_ACCESS);CHECK(submit(s,mav_test::av1_frame())==MAV_OK);destroy(s);}
    {Sink s;create(s);mav_test::mode(Mode::Delayed);auto copied=key;
        CHECK(submit(s,copied,10)==MAV_OK);std::fill(copied.begin(),copied.end(),0xff);
        CHECK(submit(s,inter,11)==MAV_OK);CHECK(submit(s,inter,12)==MAV_WOULD_BLOCK);
        CHECK(mav_decoder_wait_for_capacity(s.decoder,0)==MAV_TIMEOUT);CHECK(s.completions.empty());
        std::thread completion([]{mav_test::finish(true);});
        CHECK(mav_decoder_wait_for_capacity(s.decoder,1000000000)==MAV_OK);completion.join();
        auto m=metrics(s);CHECK(m.accepted==2&&m.completed==2&&m.outstanding==0&&m.peak_outstanding==2&&m.would_block==1);
        CHECK(s.notifications==2);for(auto& c:s.completions)CHECK(c.trace.valid&MAV_TRACE_VT_RETURN);destroy(s);}
    {Sink s;create(s);mav_test::mode(Mode::Delayed);CHECK(submit(s,key)==MAV_OK);CHECK(submit(s,inter,2)==MAV_OK);
        CHECK(mav_decoder_reset(s.decoder)==MAV_OK);CHECK(s.completions.size()==2);
        for(auto& c:s.completions)CHECK(c.status==MAV_COMPLETION_CANCELLED&&c.pixel_buffer==nullptr&&c.generation==1);
        CHECK(metrics(s).generation==2);CHECK(submit(s,inter)==MAV_NEED_RANDOM_ACCESS);
        CHECK(submit(s,key,3)==MAV_OK);CHECK(mav_decoder_drain(s.decoder)==MAV_OK);CHECK(s.completions.back().generation==2);destroy(s);}
    {Sink s;create(s);mav_test::mode(Mode::Delayed);CHECK(submit(s,key)==MAV_OK);destroy(s);
        CHECK(s.completions.size()==1&&s.completions[0].status==MAV_COMPLETION_CANCELLED);}
    for(auto mode:{Mode::SynchronousFailure,Mode::AsynchronousFailure,Mode::Missing,Mode::Drop}){
        Sink s;create(s);mav_test::mode(mode);CHECK(submit(s,key)==MAV_OK);CHECK(mav_decoder_drain(s.decoder)==MAV_OK);
        CHECK(s.completions.size()==1);CHECK(s.completions[0].status==(mode==Mode::Drop?MAV_COMPLETION_DROPPED:MAV_COMPLETION_FAILED));
        CHECK(metrics(s).outstanding==0);CHECK(submit(s,inter)==MAV_NEED_RANDOM_ACCESS);
        mav_test::mode(Mode::Inline);CHECK(submit(s,key,2)==MAV_OK);CHECK(metrics(s).session_creations==2);destroy(s);
    }
    {Sink s;create(s);mav_test::mode(Mode::Delayed);CHECK(submit(s,key)==MAV_OK);
        auto larger=mav_test::av1_key_unit(8,128,64);CHECK(submit(s,larger)==MAV_WOULD_BLOCK);
        CHECK(mav_decoder_drain(s.decoder)==MAV_OK);CHECK(submit(s,larger,2)==MAV_OK);CHECK(mav_decoder_drain(s.decoder)==MAV_OK);
        CHECK(metrics(s).session_creations==2);destroy(s);}
    {Sink s;create(s);mav_test::mode(Mode::Inline);CHECK(submit(s,key)==MAV_OK);
        auto hidden=mav_test::av1_frame(false,false),existing=mav_test::av1_existing(0);hidden.insert(hidden.end(),existing.begin(),existing.end());
        CHECK(submit(s,hidden,2)==MAV_OK);auto c=s.completions.back();CHECK(c.internal_samples==2&&c.show_existing_frame==1&&c.displayed_outputs==1);
        CHECK(submit(s,mav_test::av1_frame(false,false),3)==MAV_OK);CHECK(s.completions.back().status==MAV_COMPLETION_NO_DISPLAY);destroy(s);}
    {Sink s;create(s);mav_test::mode(Mode::Delayed);
        for(unsigned i=0;i<200;++i){CHECK(submit(s,key,i*2)==MAV_OK);CHECK(submit(s,inter,i*2+1)==MAV_OK);CHECK(mav_decoder_reset(s.decoder)==MAV_OK);}
        auto m=metrics(s);CHECK(m.accepted==400&&m.completed==400&&m.cancelled==400&&m.outstanding==0);destroy(s);}
    {Sink s;create(s);mav_test::mode(Mode::Inline);CHECK(submit(s,key)==MAV_OK);
        mav_test::fail_next_configure();CHECK(submit(s,mav_test::av1_key_unit(8,128,64))==MAV_UNSUPPORTED);
        CHECK(metrics(s).hardware_validated==0);CHECK(submit(s,inter)==MAV_NEED_RANDOM_ACCESS);
        CHECK(submit(s,key)==MAV_OK);destroy(s);}
    {Sink s;create(s);mav_test::mode(Mode::AsynchronousFailure);
        CHECK(submit(s,key)==MAV_OK);CHECK(submit(s,inter,2)==MAV_OK);mav_test::finish();
        CHECK(s.completions.size()==2);CHECK(s.completions[0].status==MAV_COMPLETION_FAILED);
        CHECK(s.completions[1].status==MAV_COMPLETION_CANCELLED);CHECK(metrics(s).failed==1&&metrics(s).cancelled==1);
        CHECK(submit(s,inter)==MAV_NEED_RANDOM_ACCESS);destroy(s);}
    for(bool fragmented:{false,true}) {
        // Parse succeeds before this format change is rejected for pending work.
        // A following inter frame must still use the old accepted configuration.
        {Sink s;create(s);mav_test::mode(Mode::Delayed);CHECK(submit(s,key,1)==MAV_OK);
            CHECK(submit_fragmented(s,mav_test::av1_key_unit(10,128,64),2,fragmented)==MAV_WOULD_BLOCK);
            CHECK(metrics(s).accepted==1);CHECK(mav_decoder_drain(s.decoder)==MAV_OK);
            CHECK(submit_fragmented(s,inter,3,fragmented)==MAV_OK);CHECK(mav_decoder_drain(s.decoder)==MAV_OK);
            CHECK(s.completions.back().bit_depth==8&&metrics(s).session_creations==1);destroy(s);}
        // A valid sequence is consumed before the missing tile group is found.
        {Sink s;create(s);mav_test::mode(Mode::Inline);CHECK(submit(s,key,1)==MAV_OK);
            auto invalid=mav_test::av1_sequence(10,128,64);auto header=mav_test::av1_frame();header[0]=0x1a;mav_test::append(invalid,header);
            CHECK(submit_fragmented(s,invalid,2,fragmented)==MAV_MALFORMED_INPUT);CHECK(metrics(s).accepted==1);
            CHECK(submit_fragmented(s,inter,3,fragmented)==MAV_OK);CHECK(s.completions.back().bit_depth==8&&metrics(s).session_creations==1);destroy(s);}
        // Configuration-only admission advances the parser, but the backend
        // must still apply that configuration on the next random-access picture.
        {Sink s;create(s);mav_test::mode(Mode::Inline);CHECK(submit(s,key,1)==MAV_OK);
            CHECK(submit_fragmented(s,mav_test::av1_sequence(10,128,64),2,fragmented)==MAV_OK);
            CHECK(s.completions.back().status==MAV_COMPLETION_NO_DISPLAY&&metrics(s).session_creations==1);
            CHECK(submit_fragmented(s,inter,3,fragmented)==MAV_NEED_RANDOM_ACCESS);
            CHECK(submit_fragmented(s,mav_test::av1_frame(),4,fragmented)==MAV_OK);
            CHECK(s.completions.back().bit_depth==10&&metrics(s).session_creations==2&&metrics(s).accepted==3);destroy(s);}
        // Backend rejection must not commit the parsed candidate either.
        {Sink s;create(s);mav_test::mode(Mode::Inline);CHECK(submit(s,key,1)==MAV_OK);
            mav_test::fail_next_configure();CHECK(submit_fragmented(s,mav_test::av1_key_unit(10,128,64),2,fragmented)==MAV_UNSUPPORTED);
            CHECK(metrics(s).accepted==1);CHECK(submit_fragmented(s,mav_test::av1_frame(),3,fragmented)==MAV_OK);
            CHECK(s.completions.back().bit_depth==8&&metrics(s).session_creations==2);destroy(s);}
    }
    // A prior async error racing a large preparation must never be erased by
    // an inter-frame admission. Timings here only arrange concurrency, not perf.
    for(unsigned run=0;run<20;++run){Sink s;create(s);mav_test::mode(Mode::Delayed);
        CHECK(submit(s,key)==MAV_OK);auto large=inter;large.push_back(0x7a);
        size_t bytes=1024*1024,n=bytes;while(n>=128){large.push_back(uint8_t(n)|128);n>>=7;}large.push_back(uint8_t(n));large.resize(large.size()+bytes);
        std::thread failure([]{std::this_thread::sleep_for(std::chrono::microseconds(50));mav_test::mode(Mode::AsynchronousFailure);mav_test::finish();});
        auto result=submit(s,large,2);CHECK(result==MAV_OK||result==MAV_NEED_RANDOM_ACCESS||result==MAV_WOULD_BLOCK);
        failure.join();CHECK(mav_decoder_drain(s.decoder)==MAV_OK);CHECK(submit(s,inter,3)==MAV_NEED_RANDOM_ACCESS);destroy(s);
    }
    std::cout<<"PASS: lifecycle using fake backend (not decoder performance evidence)\n";
}
