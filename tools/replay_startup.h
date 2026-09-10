#ifndef MAV_REPLAY_STARTUP_H
#define MAV_REPLAY_STARTUP_H

#include <algorithm>
#include <cstdint>
#include <limits>
#include <stdexcept>
#include <string_view>

namespace replay {

inline uint64_t parseStartupGraceMs(std::string_view value) {
    constexpr uint64_t maximum = 10000;
    uint64_t result = 0;
    if (value.empty()) throw std::invalid_argument("startup-grace-ms must be an integer in 0..10000");
    for (char digit : value) {
        if (digit < '0' || digit > '9' || result > (maximum - (digit - '0')) / 10)
            throw std::invalid_argument("startup-grace-ms must be an integer in 0..10000");
        result = result * 10 + (digit - '0');
    }
    return result;
}

// Admission may catch up after initial session creation, but scheduled arrivals
// stay absolute. This immutable floor is never renewed by a reset or keyframe.
// It is not a promise that an output arrives before the admission deadline.
class InitialDeadline {
public:
    InitialDeadline(uint64_t scheduledStartNs, uint64_t intervalNs,
                    uint64_t queueDepth, uint64_t startupGraceMs)
        : frameBudgetNs_(multiply(intervalNs, queueDepth)),
          initialDeadlineNs_(add(scheduledStartNs, graceNs(startupGraceMs))) {}

    uint64_t deadline(uint64_t scheduledArrivalNs) const {
        return std::max(add(scheduledArrivalNs, frameBudgetNs_), initialDeadlineNs_);
    }

    bool expired(uint64_t observedNs, uint64_t scheduledArrivalNs) const {
        return observedNs > deadline(scheduledArrivalNs);
    }

private:
    static uint64_t add(uint64_t left, uint64_t right) {
        if (right > std::numeric_limits<uint64_t>::max() - left)
            throw std::overflow_error("replay admission deadline overflow");
        return left + right;
    }

    static uint64_t multiply(uint64_t left, uint64_t right) {
        if (right && left > std::numeric_limits<uint64_t>::max() / right)
            throw std::overflow_error("replay queue duration overflow");
        return left * right;
    }

    static uint64_t graceNs(uint64_t milliseconds) {
        if (milliseconds > 10000)
            throw std::invalid_argument("startup-grace-ms must be an integer in 0..10000");
        return milliseconds * 1000000;
    }

    const uint64_t frameBudgetNs_;
    const uint64_t initialDeadlineNs_;
};

} // namespace replay
#endif
