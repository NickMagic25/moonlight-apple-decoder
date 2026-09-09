#include "backend.hpp"
#include "backend_fake.hpp"
#include <mutex>
#include <thread>
namespace {
std::mutex mutex;std::vector<std::shared_ptr<mav::Work>> pending;
mav_test::Mode mode=mav_test::Mode::Inline;std::atomic<size_t> references{0};std::atomic<bool> configuration_failure{false};
void complete(const std::shared_ptr<mav::Work>& w,mav_test::Mode m) {
    mav::BackendOutput o;o.callback_ns=mav_monotonic_time_ns();o.width=128;o.height=72;o.pixel_format=0x34323076;
    if(m==mav_test::Mode::SynchronousFailure||m==mav_test::Mode::AsynchronousFailure){o.result=MAV_DECODER_FAILED;o.status=-99;}
    else if(m==mav_test::Mode::Drop)o.dropped=true;
    else o.image=reinterpret_cast<mav_pixel_buffer>(uintptr_t(1));
    w->complete(o);
}
}
namespace mav_test {
void fail_next_configure(){configuration_failure=true;}
void mode(Mode m){std::lock_guard<std::mutex> l(mutex);::mode=m;}
size_t retained(){return references.load();}
void finish(bool concurrent){
    std::vector<std::shared_ptr<mav::Work>> work;Mode m;
    {std::lock_guard<std::mutex> l(mutex);work.swap(pending);m=::mode;}
    if(m==Mode::Missing)return;
    std::vector<std::thread> threads;
    for(auto& w:work){if(concurrent)threads.emplace_back([w,m]{complete(w,m);});else complete(w,m);}
    for(auto& t:threads)t.join();
}
}
namespace mav {
class Fake final:public Backend {
public:
    mav_result configure(const Format&,const mav_config&,const mav_color&)override{return configuration_failure.exchange(false)?MAV_UNSUPPORTED:MAV_OK;}
    void submit(std::shared_ptr<Work> w)override {
        mav_test::Mode m;{std::lock_guard<std::mutex> l(mutex);m=::mode;}
        w->submit_ns.store(mav_monotonic_time_ns());
        if(m==mav_test::Mode::Inline||m==mav_test::Mode::SynchronousFailure||m==mav_test::Mode::Drop)complete(w,m);
        else {std::lock_guard<std::mutex> l(mutex);pending.push_back(w);}
        w->return_ns.store(mav_monotonic_time_ns());
    }
    mav_result drain()override{mav_test::finish();return MAV_OK;}
    void invalidate()override{mav_test::finish();}
    BackendInfo info()const override {BackendInfo i;i.hardware=1;i.pixel_format=0x34323076;return i;}
};
std::unique_ptr<Backend> make_backend(){return std::make_unique<Fake>();}
mav_result backend_capability(mav_codec c,mav_capability& cap){cap.codec=c;cap.api_available=1;cap.hardware_decode_candidate=1;return MAV_OK;}
void retain_pixel(mav_pixel_buffer){++references;}
void release_pixel(mav_pixel_buffer){--references;}
}
