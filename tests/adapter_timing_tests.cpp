#include "../integration/moonlight-qt/apple_video_timing.h"
#include <cstdio>
int main() {
    if (!appleVideoTimestampSmoke()) {
        std::fprintf(stderr, "FAIL: RTP wrap, repeated/backward timestamps, invalid fallback, or stale callback ordering\n");
        return 1;
    }
    std::puts("PASS: adapter RTP wrap, timestamp validity, and callback display ordering");
    return 0;
}
