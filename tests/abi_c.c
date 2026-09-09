#include <moonlight_apple_video/decoder.h>
int main(void) {
    mav_config c; mav_config_default(&c, MAV_CODEC_AV1);
    return c.version != MAV_ABI_VERSION || c.max_frames_in_flight != 2;
}
