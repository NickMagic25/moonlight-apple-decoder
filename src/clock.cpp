#include "moonlight_apple_video/decoder.h"
#include <time.h>
extern "C" uint64_t mav_monotonic_time_ns(void) {
    timespec t{};
#if defined(__APPLE__)
    clock_gettime(CLOCK_UPTIME_RAW,&t);
#elif defined(CLOCK_MONOTONIC_RAW)
    clock_gettime(CLOCK_MONOTONIC_RAW,&t);
#else
    clock_gettime(CLOCK_MONOTONIC,&t);
#endif
    return uint64_t(t.tv_sec)*1000000000ull+uint64_t(t.tv_nsec);
}
