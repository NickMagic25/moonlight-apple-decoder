#include <moonlight_apple_video/decoder.h>
#include <string.h>
/* The actual old ABI-2 allocation, not a current struct with a falsified size.
 * Sanitizers can therefore catch a helper reading the new tail past this prefix. */
typedef struct legacy_completion {
    uint32_t struct_size, version; uint64_t frame_id, generation; void *caller_context;
    mav_completion_status status; mav_result result; int32_t backend_status;
    mav_pixel_buffer pixel_buffer; mav_time pts, duration; mav_color color;
    uint32_t width, height, pixel_format, bit_depth, hardware_accelerated;
    uint32_t internal_samples, displayed_outputs, show_existing_frame;
    mav_trace trace; mav_gpu_frame gpu_frame;
} legacy_completion;
_Static_assert(sizeof(legacy_completion)==offsetof(mav_completion,decode_trace),"ABI-2 completion prefix size changed");
_Static_assert(offsetof(legacy_completion,trace)==offsetof(mav_completion,trace),"trace prefix moved");
_Static_assert(offsetof(legacy_completion,gpu_frame)==offsetof(mav_completion,gpu_frame),"GPU pointer prefix moved");
int main(void) {
    mav_config c; mav_config_default(&c, MAV_CODEC_AV1);
    if(c.version != MAV_ABI_VERSION || c.max_frames_in_flight != 2)return 1;
    legacy_completion legacy={0};legacy.struct_size=sizeof(legacy);legacy.version=MAV_ABI_VERSION;
    legacy.frame_id=123;legacy.trace.callback_ns=456;
    mav_decode_trace stage={0};stage.struct_size=sizeof(stage);stage.version=MAV_ABI_VERSION;stage.backend_start_ns=789;
    if(mav_completion_get_decode_trace((const mav_completion*)&legacy,&stage)!=MAV_API_UNAVAILABLE||stage.backend_start_ns!=789)return 2;
    mav_completion copy={0};copy.struct_size=sizeof(copy);copy.version=MAV_ABI_VERSION;
    if(mav_completion_copy((const mav_completion*)&legacy,&copy)!=MAV_OK||copy.frame_id!=123||copy.trace.callback_ns!=456||copy.struct_size!=sizeof(legacy))return 3;
    if(copy.decode_trace.valid||copy.decode_trace.backend_start_ns)return 4;
    if(mav_completion_get_decode_trace(&copy,&stage)!=MAV_API_UNAVAILABLE)return 5;
    copy.struct_size=sizeof(copy);copy.decode_trace.struct_size=sizeof(stage);copy.decode_trace.version=MAV_ABI_VERSION;
    copy.decode_trace.valid=MAV_DECODE_TRACE_BACKEND_START;copy.decode_trace.backend_start_ns=999;
    if(mav_completion_get_decode_trace(&copy,&stage)!=MAV_OK||stage.valid!=MAV_DECODE_TRACE_BACKEND_START||stage.backend_start_ns!=999)return 6;
    stage.struct_size=0;
    if(mav_completion_get_decode_trace(&copy,&stage)!=MAV_INVALID_ARGUMENT)return 7;
    if(mav_completion_copy(0,&copy)!=MAV_INVALID_ARGUMENT)return 8;
    /* Declared partial tail and bytes beyond it are poisoned. The whole optional
     * tail must stay zero/unavailable, even if its fragments resemble valid tags. */
    unsigned char partial[sizeof(legacy_completion)+12+32];memset(partial,0xa5,sizeof(partial));
    legacy.struct_size=sizeof(legacy_completion)+12;memcpy(partial,&legacy,sizeof(legacy));
    copy.struct_size=sizeof(copy);copy.version=MAV_ABI_VERSION;
    if(mav_completion_copy((const mav_completion*)partial,&copy)!=MAV_OK||copy.frame_id!=123)return 9;
    mav_decode_trace zero={0};if(memcmp(&copy.decode_trace,&zero,sizeof(zero)))return 10;
    stage.struct_size=sizeof(stage);stage.version=MAV_ABI_VERSION;stage.backend_start_ns=789;
    mav_decode_trace unchanged_stage=stage;
    if(mav_completion_get_decode_trace((const mav_completion*)partial,&stage)!=MAV_API_UNAVAILABLE||memcmp(&stage,&unchanged_stage,sizeof(stage)))return 11;
    copy.struct_size=sizeof(copy);copy.version=MAV_ABI_VERSION;
    mav_completion unchanged_copy=copy;
    legacy.version=0;
    if(mav_completion_copy((const mav_completion*)&legacy,&copy)!=MAV_INVALID_ARGUMENT||memcmp(&copy,&unchanged_copy,sizeof(copy)))return 12;
    if(mav_completion_get_decode_trace((const mav_completion*)&legacy,&stage)!=MAV_INVALID_ARGUMENT||memcmp(&stage,&unchanged_stage,sizeof(stage)))return 13;
    legacy.version=MAV_ABI_VERSION;legacy.struct_size=sizeof(uint32_t)*2;
    if(mav_completion_copy((const mav_completion*)&legacy,&copy)!=MAV_INVALID_ARGUMENT||memcmp(&copy,&unchanged_copy,sizeof(copy)))return 14;
    if(mav_completion_get_decode_trace((const mav_completion*)&legacy,&stage)!=MAV_INVALID_ARGUMENT||memcmp(&stage,&unchanged_stage,sizeof(stage)))return 15;
    copy.struct_size=sizeof(copy);copy.version=MAV_ABI_VERSION;copy.decode_trace.struct_size=sizeof(stage);copy.decode_trace.version=0;
    if(mav_completion_get_decode_trace(&copy,&stage)!=MAV_API_UNAVAILABLE||memcmp(&stage,&unchanged_stage,sizeof(stage)))return 16;
    legacy.struct_size=sizeof(legacy);copy.version=0;unchanged_copy=copy;
    if(mav_completion_copy((const mav_completion*)&legacy,&copy)!=MAV_INVALID_ARGUMENT||memcmp(&copy,&unchanged_copy,sizeof(copy)))return 17;
    return 0;
}
