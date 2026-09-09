#pragma once
#include <cstdint>
#include <limits>

struct AppleVideoMediaTime {
    int64_t value = 0;
    int32_t timescale = 0;
    bool valid = false;
};

// common-c exposes a raw 32-bit 90-kHz RTP timestamp. presentationTimeUs in
// this revision is derived directly from that raw value (or is a receive-time
// fallback for hosts sending zero); it does not unwrap the ~13.26-hour cycle.
class AppleVideoTimestampUnwrapper {
public:
    AppleVideoMediaTime map(uint32_t timestamp, uint64_t fallbackUs) {
        if (!m_HaveRtp && !timestamp) {
            if (fallbackUs > uint64_t(std::numeric_limits<int64_t>::max())) return {};
            return {int64_t(fallbackUs), 1000000, true};
        }
        if (!m_HaveRtp) {
            m_Extended = timestamp;
            m_HaveRtp = true;
        } else {
            const uint32_t rawDelta = timestamp - m_Last;
            const int64_t delta = rawDelta <= INT32_MAX ? int64_t(rawDelta) : int64_t(rawDelta) - (int64_t(1) << 32);
            if ((delta > 0 && m_Extended > INT64_MAX - delta) ||
                (delta < 0 && m_Extended < INT64_MIN - delta)) return {};
            // Preserve actual repeated or backward media timestamps. This
            // arithmetic only unwraps the modulo counter; it does not invent
            // a monotonic presentation sequence or derive PTS from frame IDs.
            m_Extended += delta;
        }
        m_Last = timestamp;
        return {m_Extended, 90000, true};
    }
private:
    bool m_HaveRtp = false;
    uint32_t m_Last = 0;
    int64_t m_Extended = 0;
};

// Low-delay display policy: a callback arriving after a newer displayed frame
// is obsolete even though its compressed decode and terminal accounting remain
// valid. Epoch/generation changes establish a fresh display sequence.
class AppleVideoOutputOrder {
public:
    bool accept(uint64_t epoch, uint64_t generation, uint32_t frame) {
        if (m_HaveFrame && (epoch < m_Epoch || (epoch == m_Epoch && generation < m_Generation))) return false;
        if (m_HaveFrame && epoch == m_Epoch && generation == m_Generation) {
            const uint32_t delta = frame - m_Frame;
            if (!delta || delta > INT32_MAX) return false;
        }
        m_HaveFrame = true; m_Epoch = epoch; m_Generation = generation; m_Frame = frame;
        return true;
    }
private:
    bool m_HaveFrame = false;
    uint64_t m_Epoch = 0, m_Generation = 0;
    uint32_t m_Frame = 0;
};

inline bool appleVideoTimestampSmoke() {
    AppleVideoTimestampUnwrapper wrap;
    auto a = wrap.map(UINT32_MAX - 89, 0);
    auto b = wrap.map(0, 999999); // zero at a real wrap must not select fallback
    auto c = wrap.map(90, 0);
    auto repeat = wrap.map(90, 0);
    auto backward = wrap.map(45, 0);
    AppleVideoTimestampUnwrapper fallback;
    auto f0 = fallback.map(0, 1234567);
    auto f1 = fallback.map(0, UINT64_MAX);
    auto f2 = fallback.map(180, 0);
    AppleVideoOutputOrder order, frameWrap;
    const bool ordering = order.accept(0, 1, 100) && order.accept(0, 1, 102) &&
        !order.accept(0, 1, 101) && !order.accept(0, 1, 102) &&
        order.accept(0, 2, 1) && !order.accept(0, 1, 200) &&
        order.accept(1, 1, 0) && !order.accept(0, 3, 300) &&
        frameWrap.accept(0, 1, UINT32_MAX - 1) && frameWrap.accept(0, 1, 1) &&
        !frameWrap.accept(0, 1, 0);
    return ordering && a.valid && a.value == int64_t(UINT32_MAX) - 89 &&
        b.valid && b.timescale == 90000 && b.value == (int64_t(1) << 32) &&
        c.value == b.value + 90 && repeat.value == c.value && backward.value == c.value - 45 &&
        f0.valid && f0.value == 1234567 && f0.timescale == 1000000 &&
        !f1.valid && f2.valid && f2.value == 180 && f2.timescale == 90000;
}
