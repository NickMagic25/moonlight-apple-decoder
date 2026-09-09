#pragma once
#include <array>
#include <cstddef>
#include <cstdint>
#include <memory>
#include <string>
#include <vector>

namespace mav {
enum class Codec { AV1, HEVC };
enum class ParseResult { Ok, Malformed, Unsupported, NeedConfiguration };
struct Span { const uint8_t* data; size_t size; };
struct Color {
    uint16_t primaries = 2, transfer = 2, matrix = 2;
    bool description_valid = false, range_valid = false, full_range = false;
    uint8_t chroma_position = 0;
    bool chroma_position_valid = false, mastering_valid = false, content_light_valid = false;
    // HEVC/SMPTE2086 big-endian units: xy 1/50000, luminance 1/10000 nit.
    std::array<uint8_t, 24> mastering{};
    std::array<uint8_t, 4> content_light{};
    bool operator==(const Color&) const;
};
struct Format {
    uint32_t width = 0, height = 0;
    uint8_t profile = 0, level = 0, bit_depth = 0, chroma = 1;
    Color color;
    std::vector<uint8_t> av1c;
    // Selected VPS, SPS, PPS, without start codes; original escaped bytes.
    std::vector<std::vector<uint8_t>> parameter_sets;
    bool operator==(const Format&) const;
};
struct Sample {
    size_t offset = 0, size = 0;
    bool display = true, show_existing = false, random_access = false;
    uint8_t existing_frame_index = 0, refresh_frame_flags = 0, frame_type = 0;
};
struct Prepared {
    std::vector<uint8_t> bytes;
    std::vector<Sample> samples;
    Format format;
    bool config_changed = false, random_access = false;
    uint32_t displayed_frames = 0;
    uint64_t compressed_copy_count = 0, compressed_copy_bytes = 0;
};
// Thread-confined parser. prepare() preserves cached state on error. Input max 64 MiB,
// max 4096 units; AV1 low-overhead sized OBUs, single layer and operating point.
// Each accepted AU contains at most one displayed image; hidden AV1 frames are
// split into child samples, preserving every original codec payload byte.
class Bitstream {
public:
    explicit Bitstream(Codec);
    ~Bitstream();
    Bitstream(Bitstream&&) noexcept;
    Bitstream& operator=(Bitstream&&) noexcept;
    Bitstream(const Bitstream&);
    Bitstream& operator=(const Bitstream&);
    ParseResult prepare(const uint8_t*, size_t, Prepared&, std::string&);
    ParseResult prepare(const Span*, size_t, Prepared&, std::string&);
    // Internal admission fast path: this object must already be an isolated
    // candidate. Discard it after ANY rejection; errors may mutate its cache.
    // The caller commits it only after the complete admission succeeds.
    ParseResult prepare_isolated(const Span*, size_t, Prepared&, std::string&);
    void clear() noexcept;
private:
    struct State;
    std::unique_ptr<State> state_;
    ParseResult prepare_impl(const Span*, size_t, Prepared&, std::string&, bool transactional);
};
// Validates both the record header and its one sequence OBU for consistency.
ParseResult validate_av1c(const uint8_t*, size_t, Format&, std::string&);
}
