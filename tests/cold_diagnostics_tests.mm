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
    std::puts("cold diagnostics: validation, absent values, intervals and exactly-once JSON PASS");
    return 0;
}}
