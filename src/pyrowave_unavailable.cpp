#include "backend.hpp"
namespace mav {
namespace {
class UnavailablePyroWave final:public Backend {
public:
    mav_result configure(const Format&,const mav_config&,const mav_color&) override{return MAV_API_UNAVAILABLE;}
    void submit(std::shared_ptr<Work> work) override{BackendOutput out;out.result=MAV_API_UNAVAILABLE;work->complete(out);}
    mav_result drain() override{return MAV_OK;}
    void invalidate() override{}
    BackendInfo info() const override{return {};}
};
}
std::unique_ptr<Backend> make_pyrowave_backend(){return std::make_unique<UnavailablePyroWave>();}
mav_result pyrowave_capability(mav_capability& c){c.codec=MAV_CODEC_PYROWAVE;c.api_available=c.hardware_decode_candidate=0;return MAV_API_UNAVAILABLE;}
}
extern "C" {
void mav_gpu_frame_retain(mav_gpu_frame){}
void mav_gpu_frame_release(mav_gpu_frame){}
void* mav_gpu_frame_plane(mav_gpu_frame,uint32_t){return nullptr;}
uint32_t mav_gpu_frame_chroma(mav_gpu_frame){return 0;}
}
