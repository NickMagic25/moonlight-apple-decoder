#pragma once
#include "moonlight_apple_video/decoder.h"
#include <array>
#include <cstdio>
#include <cstdlib>
#include <sstream>
#include <string>
#include <unistd.h>

namespace mav {
// Private opt-in experiment. No public ABI, callback logging, or steady-frame
// timestamps are added. Only the serialized submitting/control thread uses it.
struct ColdDiagnostics {
    enum Stage { Capability, FormatCreation, SessionCreation, HardwareQuery,
        SupportedProperties, PropertyHints, PoolExperiment, FirstSample, StageCount };
    struct Interval { uint64_t begin=0,end=0; int32_t status=0; };
    std::string path;
    int pool_requested=0;
    bool skip_capability_requested=false,skip_capability_applied=false,capability_query_attempted=false;
    int hardware_candidate=-1;
    bool valid=true,active=false,emitted=false,first_attempt=false;
    uint64_t ordinal=0,configure_begin=0,configure_end=0,first_submit=0,first_return=0;
    uint32_t codec=0,width=0,height=0,depth=0,hardware=0;
    mav_hardware_policy hardware_policy=MAV_HARDWARE_REQUIRED;
    int32_t configure_result=-1,backend_status=0;
    int32_t realtime_status=0,realtime_effective=-1,power_status=0,power_effective=-1;
    int pool_supported=-1,pool_effective=-1,pool_shared=-1;
    bool pool_set_attempted=false,pool_read_attempted=false,shared_read_attempted=false;
    int32_t pool_set_status=0,pool_read_status=0,shared_read_status=0;
    std::array<Interval,StageCount> stages{};

    ColdDiagnostics():ColdDiagnostics(std::getenv("MAV_EXPERIMENT_COLD_TRACE"),
                                     std::getenv("MAV_EXPERIMENT_POOL_MIN"),
                                     std::getenv("MAV_EXPERIMENT_SKIP_CAPABILITY")){}
    ColdDiagnostics(const char* output,const char* pool,const char* skip=nullptr):path(output?output:"") {
        if(pool && *pool) {
            std::string value(pool);
            if(value=="3")pool_requested=3;
            else if(value=="6")pool_requested=6;
            else if(value!="0")valid=false;
            if(path.empty())valid=false;
        }
        if(skip && *skip) {
            std::string value(skip);
            if(value=="1")skip_capability_requested=true;
            else if(value!="0")valid=false;
            if(skip_capability_requested&&path.empty())valid=false;
        }
    }
    bool enabled() const noexcept { return !path.empty(); }
    bool shouldSkipCapability(mav_hardware_policy policy) const noexcept {
        return valid&&enabled()&&skip_capability_requested&&policy==MAV_HARDWARE_REQUIRED;
    }
    void beginSession(uint32_t c,uint32_t w,uint32_t h,uint32_t d,mav_hardware_policy policy=MAV_HARDWARE_REQUIRED) {
        if(!enabled())return;
        ++ordinal;active=true;emitted=false;first_attempt=false;
        configure_begin=mav_monotonic_time_ns();configure_end=first_submit=first_return=0;
        codec=c;width=w;height=h;depth=d;hardware=0;configure_result=-1;backend_status=0;
        hardware_policy=policy;
        skip_capability_applied=capability_query_attempted=false;hardware_candidate=-1;
        realtime_status=power_status=0;realtime_effective=power_effective=-1;
        pool_supported=pool_effective=pool_shared=-1;
        pool_set_attempted=pool_read_attempted=shared_read_attempted=false;
        pool_set_status=pool_read_status=shared_read_status=0;stages={};
    }
    void begin(Stage stage) noexcept { if(active)stages[stage].begin=mav_monotonic_time_ns(); }
    void end(Stage stage,int32_t status=0) noexcept {
        if(active){stages[stage].end=mav_monotonic_time_ns();stages[stage].status=status;}
    }
    void configured(mav_result result,int32_t status) noexcept {
        if(active){configure_end=mav_monotonic_time_ns();configure_result=result;backend_status=status;}
    }
    static void number(std::ostream& out,uint64_t value) { if(value)out<<value;else out<<"null"; }
    void emitOnce() noexcept {
        if(!active||emitted)return;
        emitted=true;active=false;
        try {
            std::ostringstream out;
            out<<"{\"schema_version\":1,\"kind\":\"vt-cold-stages\",\"pid\":"<<getpid()
               <<",\"session_ordinal\":"<<ordinal<<",\"codec\":"<<codec<<",\"width\":"<<width
               <<",\"height\":"<<height<<",\"bit_depth\":"<<depth<<",\"configure_result\":"<<configure_result
               <<",\"backend_status\":"<<backend_status<<",\"hardware\":"<<hardware
               <<",\"skip_capability_requested\":"<<(skip_capability_requested?"true":"false")
               <<",\"skip_capability_applied\":"<<(skip_capability_applied?"true":"false")
               <<",\"hardware_policy\":"<<hardware_policy
               <<",\"capability_query_attempted\":"<<(capability_query_attempted?"true":"false")
               <<",\"hardware_candidate\":"<<hardware_candidate
               <<",\"configure_begin_ns\":";number(out,configure_begin);
            out<<",\"configure_end_ns\":";number(out,configure_end);
            out<<",\"first_vt_submit_ns\":";number(out,first_submit);
            out<<",\"first_vt_return_ns\":";number(out,first_return);
            out<<",\"realtime_status\":"<<realtime_status<<",\"realtime_effective\":"<<realtime_effective
               <<",\"power_status\":"<<power_status<<",\"power_effective\":"<<power_effective
               <<",\"pool_minimum\":{\"requested\":"<<pool_requested<<",\"supported\":"<<pool_supported
               <<",\"setter_attempted\":"<<(pool_set_attempted?"true":"false")<<",\"setter_status\":";
            if(pool_set_attempted)out<<pool_set_status;else out<<"null";
            out<<",\"read_status\":";if(pool_read_attempted)out<<pool_read_status;else out<<"null";
            out<<",\"readback\":"<<pool_effective<<",\"shared_read_status\":";
            if(shared_read_attempted)out<<shared_read_status;else out<<"null";
            out<<",\"shared\":"<<pool_shared<<"},\"stages\":{";
            const char* names[]={"capability","create_format","vt_session_create","hardware_query",
                "supported_properties","property_hints","pool_experiment","first_sample_creation"};
            for(size_t i=0;i<stages.size();++i){const auto& s=stages[i];if(i)out<<',';
                out<<'"'<<names[i]<<"\":{\"begin_ns\":";number(out,s.begin);
                out<<",\"end_ns\":";number(out,s.end);out<<",\"duration_ns\":";
                if(s.begin&&s.end>=s.begin)out<<s.end-s.begin;else out<<"null";
                out<<",\"status\":";if(s.end)out<<s.status;else out<<"null";out<<'}';}
            out<<"}}\n";
            const auto bytes=out.str();FILE* file=std::fopen(path.c_str(),"a");
            if(!file){std::fprintf(stderr,"cold diagnostic output open failed: %s\n",path.c_str());return;}
            bool ok=std::fwrite(bytes.data(),1,bytes.size(),file)==bytes.size();
            if(std::fclose(file)!=0)ok=false;
            if(!ok)std::fprintf(stderr,"cold diagnostic output write failed: %s\n",path.c_str());
        } catch(...) { std::fprintf(stderr,"cold diagnostic serialization failed\n"); }
    }
};
}
