#pragma once
#import <Foundation/Foundation.h>
#include <CommonCrypto/CommonDigest.h>
#include <algorithm>
#include <cmath>
#include <unordered_set>
#include <cstdint>
#include <fstream>
#include <stdexcept>
#include <string>
#include <vector>

namespace fixture {
inline std::string utf(NSString* s) { if(s && ![s isKindOfClass:NSString.class])throw std::runtime_error("expected JSON string");return s ? std::string(s.UTF8String) : std::string(); }
inline NSString* ns(const std::string& s) { return [NSString stringWithUTF8String:s.c_str()]; }
inline std::vector<uint8_t> read(const std::string& path,size_t limit=(2ull<<30)) {
    std::ifstream f(path, std::ios::binary | std::ios::ate);
    if (!f) throw std::runtime_error("cannot read " + path);
    auto n=f.tellg(); if(n<0 || n>std::streamoff(limit)) throw std::runtime_error("file exceeds safety size limit");
    std::vector<uint8_t> b(static_cast<size_t>(n)); f.seekg(0); f.read(reinterpret_cast<char*>(b.data()),n);
    if(!f && n) throw std::runtime_error("short read"); return b;
}
inline void write(const std::string& path, const std::vector<uint8_t>& b) {
    std::ofstream f(path,std::ios::binary); f.write(reinterpret_cast<const char*>(b.data()),b.size());
    if(!f) throw std::runtime_error("cannot write " + path);
}
inline std::string sha(const uint8_t* p,size_t n) {
    CC_SHA256_CTX c; CC_SHA256_Init(&c);
    while(n){ auto k=std::min(n,size_t(UINT32_MAX)); CC_SHA256_Update(&c,p,CC_LONG(k)); p+=k; n-=k; }
    uint8_t digest[CC_SHA256_DIGEST_LENGTH]; CC_SHA256_Final(digest,&c);
    const char* h="0123456789abcdef"; std::string s;
    for(auto b:digest){s+=h[b>>4];s+=h[b&15];} return s;
}
inline void json(const std::string& path,id object) {
    NSError* e=nil; NSData* d=[NSJSONSerialization dataWithJSONObject:object options:NSJSONWritingPrettyPrinted|NSJSONWritingSortedKeys error:&e];
    if(!d || ![d writeToFile:ns(path) options:NSDataWritingAtomic error:&e]) throw std::runtime_error("JSON write: "+utf(e.description));
}
struct AU { uint64_t offset,size,id; int64_t pts,dts,duration; bool pts_valid,dts_valid,random,discontinuity; uint32_t displays; };
struct Manifest {
    NSDictionary* document; std::vector<uint8_t> payload; std::vector<AU> units;
    std::string codec,variant,hash; uint32_t width,height,depth,fps_num,fps_den,timebase_num,timebase_den;
};
inline bool numeric(id x) {return [x isKindOfClass:NSNumber.class]&&CFGetTypeID((__bridge CFTypeRef)x)!=CFBooleanGetTypeID()&&std::isfinite([x doubleValue]);}
inline uint64_t integer(id x,const char* name,uint64_t maximum=UINT64_MAX) {
    if(!numeric(x) || [x compare:@0]==NSOrderedAscending || [x compare:@(maximum)]==NSOrderedDescending || [x doubleValue]!=double([x unsignedLongLongValue]))
        throw std::runtime_error(std::string("invalid integer: ")+name);
    return [x unsignedLongLongValue];
}
inline int64_t signedInteger(id x,const char* name) {
    if(!numeric(x)||[x compare:@(INT64_MIN)]==NSOrderedAscending||[x compare:@(INT64_MAX)]==NSOrderedDescending||[x doubleValue]!=double([x longLongValue]))throw std::runtime_error(std::string("invalid signed integer: ")+name);return [x longLongValue];
}
inline bool boolean(id x,const char* name) {
    if(![x isKindOfClass:NSNumber.class]||([x compare:@0]!=NSOrderedSame&&[x compare:@1]!=NSOrderedSame))throw std::runtime_error(std::string("invalid boolean: ")+name);return [x boolValue];
}
inline NSDictionary* dictionary(id x,const char* name) {
    if(![x isKindOfClass:NSDictionary.class])throw std::runtime_error(std::string("invalid dictionary: ")+name);return x;
}
inline Manifest load(const std::string& path) {
    auto bytes=read(path,64u<<20); NSError* e=nil;
    id obj=[NSJSONSerialization JSONObjectWithData:[NSData dataWithBytes:bytes.data() length:bytes.size()] options:0 error:&e];
    if(![obj isKindOfClass:NSDictionary.class]) throw std::runtime_error("invalid fixture JSON");
    Manifest m{}; m.document=obj;
    if(integer(obj[@"schema_version"],"schema_version")!=1)throw std::runtime_error("unsupported fixture schema");
    m.codec=utf(obj[@"codec"]);m.variant=utf(obj[@"variant"]);if(m.variant!="sdr8"&&m.variant!="hdr10")throw std::runtime_error("invalid fixture variant");
    if(m.codec!="av1"&&m.codec!="hevc")throw std::runtime_error("unsupported codec");
    if(utf(obj[@"framing"])!=(m.codec=="av1"?"av1-low-overhead-obu":"hevc-annex-b"))throw std::runtime_error("invalid framing");
    m.width=integer(obj[@"width"],"width",16384);m.height=integer(obj[@"height"],"height",16384);m.depth=integer(obj[@"bit_depth"],"bit_depth",10);
    NSDictionary* rate=dictionary(obj[@"frame_rate"],"frame_rate");NSDictionary* timebase=dictionary(obj[@"timebase"],"timebase");
    m.fps_num=integer(rate[@"num"],"fps num",1000000);m.fps_den=integer(rate[@"den"],"fps den",1000000);
    m.timebase_num=integer(timebase[@"num"],"timebase num",1000000000);m.timebase_den=integer(timebase[@"den"],"timebase den",1000000000);
    if(!m.width||!m.height||m.width%2||m.height%2||utf(obj[@"chroma"])!="420"||(m.variant=="hdr10")!=(m.depth==10)||!m.fps_num||!m.fps_den||!m.timebase_num||!m.timebase_den||(m.depth!=8&&m.depth!=10))throw std::runtime_error("invalid fixture format");
    uint64_t profile=integer(obj[@"profile"],"profile",2);if(profile!=(m.codec=="av1"?0:(m.depth==10?2:1)))throw std::runtime_error("fixture profile mismatch");
    if(obj[@"generator"]){NSDictionary* generator=dictionary(obj[@"generator"],"generator");if(generator[@"pattern"])(void)utf(generator[@"pattern"]);}
    if(obj[@"color"]){NSDictionary* color=dictionary(obj[@"color"],"color");for(NSString* key in @[@"primaries",@"transfer",@"matrix"]){if(color[key])integer(color[key],key.UTF8String,255);}for(NSString* key in @[@"full_range",@"mastering_valid",@"content_light_valid"]){if(color[key])boolean(color[key],key.UTF8String);}for(NSString* key in @[@"mastering_base64",@"content_light_base64"]){if(color[key]){NSString* value=ns(utf(color[key]));NSData* data=[[NSData alloc]initWithBase64EncodedString:value options:0];if(!data||data.length!=([key isEqualToString:@"mastering_base64"]?24:4))throw std::runtime_error("invalid HDR metadata bytes");}}}
    NSString* relative=obj[@"payload_file"];
    if(![relative isKindOfClass:NSString.class]||relative.isAbsolutePath||[relative.pathComponents containsObject:@".."])throw std::runtime_error("payload path must stay within fixture directory");
    NSString* base=[NSURL fileURLWithPath:ns(path)].URLByResolvingSymlinksInPath.path.stringByDeletingLastPathComponent;NSString* payloadPath=[base stringByAppendingPathComponent:relative].stringByResolvingSymlinksInPath;if(![payloadPath hasPrefix:[base stringByAppendingString:@"/"]])throw std::runtime_error("resolved payload path escapes fixture directory");m.payload=read(utf(payloadPath));
    m.hash=sha(m.payload.data(),m.payload.size());if(m.hash!=utf(obj[@"payload_sha256"]))throw std::runtime_error("payload SHA256 mismatch");
    if(![obj[@"access_units"] isKindOfClass:NSArray.class]||[obj[@"access_units"] count]>1000000)throw std::runtime_error("invalid access_units");
    uint64_t last=0; std::unordered_set<uint64_t> ids;
    for(NSDictionary* d in obj[@"access_units"]){
        (void)dictionary(d,"access unit");AU a{};a.offset=integer(d[@"offset"],"offset");a.size=integer(d[@"length"],"length",64u<<20);a.id=integer(d[@"frame_id"],"frame_id",UINT64_MAX-1);
        if(!a.size||a.offset!=last||a.offset>m.payload.size()||a.size>m.payload.size()-a.offset)throw std::runtime_error("invalid or noncontiguous AU bounds");
        if(sha(m.payload.data()+a.offset,a.size)!=utf(d[@"sha256"]))throw std::runtime_error("AU SHA256 mismatch");
        if(!ids.insert(a.id).second)throw std::runtime_error("duplicate frame ID");
        a.pts_valid=d[@"pts"]!=NSNull.null&&d[@"pts"]!=nil;a.dts_valid=d[@"dts"]!=NSNull.null&&d[@"dts"]!=nil;
        a.pts=a.pts_valid?signedInteger(d[@"pts"],"pts"):0;a.dts=a.dts_valid?signedInteger(d[@"dts"],"dts"):0;a.duration=integer(d[@"duration"],"duration",INT64_MAX);
        a.random=boolean(d[@"random_access"],"random_access");a.discontinuity=boolean(d[@"discontinuity"],"discontinuity");a.displays=integer(d[@"expected_display_count"],"expected_display_count",1);
        if(a.pts_valid&&__int128(a.pts)+a.duration>INT64_MAX)throw std::runtime_error("presentation duration overflows");if(d[@"expected_visible_frame_id"])integer(d[@"expected_visible_frame_id"],"expected_visible_frame_id");m.units.push_back(a);last=a.offset+a.size;
    }
    if(m.units.empty()||last!=m.payload.size()||!m.units.front().random)throw std::runtime_error("fixture must start at random access and cover the whole payload");
    return m;
}
// 16 wide high-contrast cells carry the source frame number. Moving gradient,
// checker detail and a translating square exercise spatial and temporal coding.
inline uint16_t luma(uint32_t x,uint32_t y,uint32_t w,uint32_t h,uint64_t frame,uint32_t depth) {
    uint16_t v;
    if(y<h/8) {uint32_t bit=std::min(15u,x*16/w);v=((frame>>bit)&1)?220:28;}
    else if(x>=(frame*7)%(w-std::max(1u,w/8)) && x<(frame*7)%(w-std::max(1u,w/8))+w/8 && y>h/3&&y<h/2) v=224;
    else v=uint16_t(32+((x*96/w+y*72/h+frame*3)%160)+(((x/4+y/4)&1)?7:0));
    return depth==10?v*4:v;
}
inline std::vector<uint8_t> mastering() { // BT.2020 display, D65, 1000 / 0.005 nit.
    std::vector<uint8_t>b;auto be16=[&](uint16_t x){b.push_back(x>>8);b.push_back(x);};auto be32=[&](uint32_t x){be16(x>>16);be16(x);};
    be16(8500);be16(39850);be16(6550);be16(2300);be16(35400);be16(14600);be16(15635);be16(16450);be32(10000000);be32(50);return b;
}
}
