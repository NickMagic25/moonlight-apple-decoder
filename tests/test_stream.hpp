#pragma once
#include <cstddef>
#include <cstdint>
#include <vector>

// Synthetic syntax for parser/fake-backend tests only. The tile bytes are not
// entropy-coded image data. Real VideoToolbox tests use generated fixtures.
namespace mav_test {
struct Writer {
    std::vector<uint8_t> bytes;
    unsigned position = 0;
    void bits(uint32_t value, unsigned count) {
        for (unsigned i = count; i; --i) {
            if (!(position % 8)) bytes.push_back(0);
            bytes.back() |= uint8_t(((value >> (i - 1)) & 1) << (7 - position % 8));
            ++position;
        }
    }
    void ue(uint32_t value) {
        unsigned count = 0; for (uint32_t n = value + 1; n >>= 1;) ++count;
        bits(0, count); bits(value + 1, count + 1);
    }
    void trailing() { bits(1, 1); while (position % 8) bits(0, 1); }
};
inline std::vector<uint8_t> obu(unsigned type, const std::vector<uint8_t>& payload) {
    std::vector<uint8_t> result{uint8_t((type << 3) | 2)};
    std::size_t size = payload.size();
    do { uint8_t byte = uint8_t(size & 127); size >>= 7; result.push_back(uint8_t(byte | (size ? 128 : 0))); } while (size);
    result.insert(result.end(), payload.begin(), payload.end()); return result;
}
inline void append(std::vector<uint8_t>& destination, const std::vector<uint8_t>& source) {
    destination.insert(destination.end(), source.begin(), source.end());
}
inline std::vector<uint8_t> av1_sequence(unsigned depth = 8, unsigned width = 64, unsigned height = 64, unsigned chroma_position = 0) {
    Writer w;
    w.bits(0, 3); w.bits(0, 1); w.bits(0, 1); // Main, not a still picture
    w.bits(0, 1); w.bits(0, 1); w.bits(0, 5); // no timing/delay, one operating point
    w.bits(0, 12); w.bits(0, 5); // all layers, level 2.0
    w.bits(15, 4); w.bits(15, 4); w.bits(width - 1, 16); w.bits(height - 1, 16);
    w.bits(0, 1); w.bits(0, 3); // no frame IDs, coding tools
    w.bits(0, 5); w.bits(1, 1); w.bits(1, 1); // no order hint, choose screen/integer MV
    w.bits(0, 3); w.bits(depth == 10, 1); w.bits(0, 1); // superres/filter flags, depth, monochrome
    w.bits(1, 1); w.bits(depth == 10 ? 9 : 1, 8); w.bits(depth == 10 ? 16 : 1, 8); w.bits(depth == 10 ? 9 : 1, 8);
    w.bits(0, 1); w.bits(chroma_position, 2); w.bits(0, 1); w.bits(0, 1); // range/chroma/delta/film grain
    w.trailing(); return obu(1, w.bytes);
}
inline std::vector<uint8_t> av1_frame(bool key = true, bool display = true) {
    Writer w;
    w.bits(0, 1); w.bits(key ? 0 : 1, 2); w.bits(display, 1);
    if (!display) w.bits(1, 1); // showable
    if (!key || !display) w.bits(1, 1); // error resilient
    w.bits(1, 1); w.bits(0, 1); w.bits(0, 1); // disable CDF, no screen tools/size override
    if (!key || !display) w.bits(1, 8); // refresh reference slot zero
    w.bits(0, 16); w.trailing(); return obu(6, w.bytes);
}
inline std::vector<uint8_t> av1_key_unit(unsigned depth = 8, unsigned width = 64, unsigned height = 64) {
    auto result = av1_sequence(depth, width, height); append(result, av1_frame()); return result;
}
inline std::vector<uint8_t> av1_existing(unsigned index = 0) {
    Writer w; w.bits(1, 1); w.bits(index, 3); w.trailing(); return obu(3, w.bytes);
}
}
