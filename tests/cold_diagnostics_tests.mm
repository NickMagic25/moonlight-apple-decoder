#include "cold_diagnostics.hpp"
#import <Foundation/Foundation.h>
#include <fstream>
#include <iterator>

int main(){@autoreleasepool{
    const char* path="cold-diagnostics-test.jsonl";
    std::remove(path);
    mav::ColdDiagnostics disabled(nullptr,nullptr);
    disabled.beginSession(1,1920,1080,8);
    if(disabled.active||!disabled.valid)return 1;
    for(const char* value:{"0","3","6"})if(!mav::ColdDiagnostics(path,value).valid)return 1;
    for(const char* value:{"-1","2","03","6x"})if(mav::ColdDiagnostics(path,value).valid)return 1;
    if(mav::ColdDiagnostics(nullptr,"3").valid)return 1;
    for(const char* value:{"0","1"})if(!mav::ColdDiagnostics(path,nullptr,value).valid)return 1;
    for(const char* value:{"-1","2","01","true"})if(mav::ColdDiagnostics(path,nullptr,value).valid)return 1;
    if(mav::ColdDiagnostics(nullptr,nullptr,"1").valid)return 1;
    if(mav::ColdDiagnostics(path,nullptr).shouldSkipCapability(MAV_HARDWARE_REQUIRED))return 1;
    if(mav::ColdDiagnostics(path,nullptr,"0").shouldSkipCapability(MAV_HARDWARE_REQUIRED))return 1;
    mav::ColdDiagnostics direct(path,nullptr,"1");
    if(!direct.shouldSkipCapability(MAV_HARDWARE_REQUIRED)||direct.shouldSkipCapability(MAV_HARDWARE_PREFERRED))return 1;
    mav::ColdDiagnostics trace(path,"3");
    trace.beginSession(1,1920,1080,8);
    trace.begin(mav::ColdDiagnostics::Capability);trace.end(mav::ColdDiagnostics::Capability,MAV_OK);
    trace.configured(MAV_OK,0);trace.emitOnce();trace.emitOnce();
    std::ifstream input(path);std::string bytes((std::istreambuf_iterator<char>(input)),{});
    NSData* data=[NSData dataWithBytes:bytes.data() length:bytes.size()];NSError* error=nil;
    NSDictionary* record=[NSJSONSerialization JSONObjectWithData:data options:0 error:&error];
    std::remove(path);
    if(error||!record||[record[@"session_ordinal"] intValue]!=1||[record[@"configure_result"] intValue]!=MAV_OK)return 1;
    NSDictionary* capability=record[@"stages"][@"capability"];
    if([capability[@"begin_ns"] unsignedLongLongValue]>[capability[@"end_ns"] unsignedLongLongValue])return 1;
    if(record[@"first_vt_submit_ns"]!=NSNull.null||record[@"pool_minimum"][@"setter_status"]!=NSNull.null||
       record[@"stages"][@"first_sample_creation"][@"duration_ns"]!=NSNull.null)return 1;
    if([record[@"skip_capability_requested"] boolValue]||[record[@"skip_capability_applied"] boolValue]||
       [record[@"capability_query_attempted"] boolValue]||[record[@"hardware_candidate"] intValue]!=-1)return 1;
    direct.beginSession(1,1920,1080,8);direct.skip_capability_applied=true;direct.hardware=1;
    direct.configured(MAV_OK,0);direct.emitOnce();
    std::ifstream directInput(path);bytes.assign(std::istreambuf_iterator<char>(directInput),{});
    data=[NSData dataWithBytes:bytes.data() length:bytes.size()];
    record=[NSJSONSerialization JSONObjectWithData:data options:0 error:&error];std::remove(path);
    if(error||![record[@"skip_capability_requested"] boolValue]||![record[@"skip_capability_applied"] boolValue]||
       [record[@"capability_query_attempted"] boolValue]||[record[@"hardware"] intValue]!=1)return 1;
    direct.beginSession(2,1920,1080,10);
    if(direct.ordinal!=2||direct.skip_capability_applied||direct.capability_query_attempted||direct.hardware_candidate!=-1)return 1;
    std::puts("cold diagnostics: controls, required-only bypass, session reset and exactly-once JSON PASS");
    return 0;
}}
