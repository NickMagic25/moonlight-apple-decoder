#include "vt_experiment.hpp"
#include <cstdio>
#include <cstdlib>
#include <stdexcept>
#include <string>
#include <vector>

// Pure control validation: never creates a VT session or queries a device.
namespace {
const char* keys[]={"MAV_VT_PIXEL_FORMAT","MAV_VT_REALTIME","MAV_VT_THREAD_COUNT",
    "MAV_VT_ASYNC","MAV_VT_METAL","MAV_VT_IOSURFACE","MAV_VT_SIGNPOST","MAV_VT_POWER_EFFICIENCY"};
unsigned checks=0;
void require(bool condition,const char* message){++checks;if(!condition)throw std::runtime_error(message);}
struct Environment {
    std::vector<std::pair<bool,std::string>> saved;
    Environment(){for(auto key:keys){const char* value=std::getenv(key);saved.emplace_back(value!=nullptr,value?value:"");unsetenv(key);}}
    ~Environment(){for(size_t i=0;i<saved.size();++i){if(saved[i].first)setenv(keys[i],saved[i].second.c_str(),1);else unsetenv(keys[i]);}}
};
void invalid(const char* key,const char* value){
    setenv(key,value,1);mav::VTExperiment controls;
    require(!controls.load(),"invalid environment value was accepted");
    require(!controls.error.empty(),"invalid value lacks diagnostic reason");
    unsetenv(key);
}
void environment_controls(){
    mav::VTExperiment controls;require(controls.load(),"default controls rejected");
    require(!controls.pixel_format&&!controls.native_pixel,"default changes selected pixel format");
    require(controls.realtime==-1&&controls.thread_count==-1&&controls.power_efficiency==-1,"default overrides session controls");
    require(controls.asynchronous==1&&controls.metal==1&&controls.iosurface==1&&!controls.signposts,"default changes delivery/output attributes or enables tracing");
    for(auto key:{"MAV_VT_REALTIME","MAV_VT_ASYNC","MAV_VT_METAL","MAV_VT_IOSURFACE","MAV_VT_SIGNPOST"}){
        for(auto value:{"","-1","+1"," 1","1 ","true","2","4294967296","99999999999999999999999999999"})invalid(key,value);
        for(auto value:{"0","1"}){setenv(key,value,1);require(controls.load(),"valid Boolean control rejected");unsetenv(key);}
    }
    for(auto value:{"","-1","+1","1x","0x10","2147483648","4294967296","99999999999999999999999999999"})invalid("MAV_VT_THREAD_COUNT",value);
    for(auto value:{"","-1","1","9","4294967296"})invalid("MAV_VT_POWER_EFFICIENCY",value);
    setenv("MAV_VT_POWER_EFFICIENCY","0",1);require(controls.load()&&controls.power_efficiency==0,"power-efficiency disable rejected");unsetenv("MAV_VT_POWER_EFFICIENCY");
    for(auto value:{"0","1","16","2147483647"}){setenv("MAV_VT_THREAD_COUNT",value,1);require(controls.load(),"valid thread-count boundary rejected");require(controls.thread_count==std::strtol(value,nullptr,10),"thread-count parsing changed value");unsetenv("MAV_VT_THREAD_COUNT");}
    for(auto value:{"","420","420vX","NATIVE","\n420"})invalid("MAV_VT_PIXEL_FORMAT",value);
    setenv("MAV_VT_PIXEL_FORMAT","420v",1);require(controls.load()&&controls.pixel_format==kCVPixelFormatType_420YpCbCr8BiPlanarVideoRange,"FourCC byte order is wrong");
    setenv("MAV_VT_PIXEL_FORMAT","native",1);require(controls.load()&&controls.native_pixel&&!controls.pixel_format,"native selection was not recognized");
    unsetenv("MAV_VT_PIXEL_FORMAT");require(controls.load()&&!controls.native_pixel&&!controls.pixel_format,"load leaked previous override");
}
void pixel_controls(){
    using E=mav::VTExperiment;
    const uint32_t linear[]={kCVPixelFormatType_420YpCbCr8BiPlanarVideoRange,kCVPixelFormatType_420YpCbCr8BiPlanarFullRange,
        kCVPixelFormatType_420YpCbCr10BiPlanarVideoRange,kCVPixelFormatType_420YpCbCr10BiPlanarFullRange};
    const uint32_t lossless[]={kCVPixelFormatType_Lossless_420YpCbCr8BiPlanarVideoRange,kCVPixelFormatType_Lossless_420YpCbCr8BiPlanarFullRange,
        kCVPixelFormatType_Lossless_420YpCbCr10PackedBiPlanarVideoRange,kCVPixelFormatType_Lossless_420YpCbCr10PackedBiPlanarFullRange};
    const uint32_t lossy[]={kCVPixelFormatType_Lossy_420YpCbCr8BiPlanarVideoRange,kCVPixelFormatType_Lossy_420YpCbCr8BiPlanarFullRange,
        kCVPixelFormatType_Lossy_420YpCbCr10PackedBiPlanarVideoRange};
    for(unsigned i=0;i<4;++i){
        E controls;controls.native_pixel=true;uint32_t selected=linear[i];
        require(controls.select_pixel(selected)&&selected==linear[i],"native selection lost expected linear format");
        require(E::linear_equivalent(lossless[i])==linear[i],"lossless mapping changed depth/range");
        require(controls.accepts_native_pixel(linear[i])&&controls.accepts_native_pixel(lossless[i]),"equivalent native output rejected");
        for(unsigned j=0;j<4;++j)if(i!=j){require(!controls.accepts_native_pixel(linear[j]),"native output changed depth/range");require(!controls.accepts_native_pixel(lossless[j]),"compressed native output changed depth/range");}
        for(auto pixel:lossy){require(!controls.accepts_native_pixel(pixel),"lossy native output accepted");E explicit_request;explicit_request.pixel_format=pixel;uint32_t requested=linear[i];require(!explicit_request.select_pixel(requested),"explicit lossy output accepted");}
        require(!controls.accepts_native_pixel(kCVPixelFormatType_32BGRA),"RGB conversion accepted as equivalent native output");
        require(!controls.accepts_native_pixel(kCVPixelFormatType_422YpCbCr8BiPlanarVideoRange),"native output changed chroma sampling");
        controls.allowed_format_count=1;controls.allowed_formats[0]=linear[i];
        require(controls.accepts_native_pixel(linear[i])&&!controls.accepts_native_pixel(lossless[i]),"native output ignored caller format constraints");
        E explicit_request;explicit_request.pixel_format=linear[(i+1)%4];uint32_t requested=linear[i];
        require(!explicit_request.select_pixel(requested)&&requested==linear[i],"explicit incompatible override accepted or changed selection");
    }
    require(E::linear_equivalent(kCVPixelFormatType_420YpCbCr8Planar)!=linear[0],"unvalidated three-plane output accepted");
    require(E::linear_equivalent(kCVPixelFormatType_420YpCbCr8PlanarFullRange)!=linear[1],"unvalidated full-range three-plane output accepted");
    require(E::fourcc(linear[0])=="420v"&&E::fourcc(lossless[2])=="&xv0","FourCC reporting mismatch");
    require(E::json_string("a\"b\\c\n")=="\"a\\\"b\\\\c\\u000a\"","diagnostic JSON escaping mismatch");
}
}
int main(){
    try{Environment environment;environment_controls();pixel_controls();std::printf("PASS: %u VT experiment control checks (no hardware)\n",checks);return 0;}
    catch(const std::exception& error){std::fprintf(stderr,"FAIL: %s\n",error.what());return 1;}
}
