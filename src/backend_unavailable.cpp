#include "backend.hpp"
namespace mav {
class Unavailable final:public Backend {
public:
 mav_result configure(const Format&,const mav_config&,const mav_color&)override{return MAV_API_UNAVAILABLE;}
 void submit(std::shared_ptr<Work> w)override{BackendOutput o;o.result=MAV_API_UNAVAILABLE;w->complete(o);}
 mav_result drain()override{return MAV_OK;}void invalidate()override{}BackendInfo info()const override{return {};}
};
std::unique_ptr<Backend> make_backend(){return std::make_unique<Unavailable>();}
mav_result backend_capability(mav_codec codec,mav_capability& c){c.codec=codec;c.api_available=0;c.hardware_decode_candidate=0;return MAV_API_UNAVAILABLE;}
void retain_pixel(mav_pixel_buffer){}void release_pixel(mav_pixel_buffer){}
}
