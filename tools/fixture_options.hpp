#pragma once

#include <algorithm>
#include <charconv>
#include <cstdint>
#include <map>
#include <optional>
#include <stdexcept>
#include <string>

namespace fixture {

struct Options {
    bool help = false;
    std::string codec = "av1", variant = "sdr8", output = "fixtures/generated";
    std::string aomenc = ".local/aom-build/aomenc", import_manifest;
    uint32_t width = 1920, height = 1080, fps = 120, frames = 120, gop = 60;
    // Integer kbps is only the internal encoder representation; the CLI uses Mbps.
    std::optional<uint32_t> bitrate_kbps;

    uint64_t hevc_target_bitrate_bps() const {
        return bitrate_kbps ? uint64_t(*bitrate_kbps) * 1000
                            : std::max(uint64_t(1000000), uint64_t(width) * height * fps / 3);
    }
};

inline Options parse_options(int argc, const char* const* argv) {
    Options result;
    if (argc == 2 && std::string(argv[1]) == "--help") {
        result.help = true;
        return result;
    }
    const std::map<std::string, bool> known = {
        {"--codec", true}, {"--variant", true}, {"--output", true},
        {"--width", true}, {"--height", true}, {"--fps", true},
        {"--frames", true}, {"--gop", true}, {"--bitrate-mbps", true},
        {"--aomenc", true}, {"--import", true}
    };
    std::map<std::string, std::string> values;
    for (int i = 1; i < argc; ++i) {
        std::string key = argv[i];
        if (key == "--bitrate-kbps")
            throw std::runtime_error("--bitrate-kbps was replaced by --bitrate-mbps; divide the old value by 1000");
        if (!known.count(key)) throw std::runtime_error("unknown option: " + key);
        if (values.count(key)) throw std::runtime_error("duplicate option: " + key);
        if (i + 1 >= argc) throw std::runtime_error("option requires value: " + key);
        std::string value = argv[++i];
        if (value.empty() || value.rfind("--", 0) == 0)
            throw std::runtime_error("option requires value: " + key);
        values.emplace(key, value);
    }
    auto string_value = [&](const char* key, std::string& destination) {
        auto found = values.find(key);
        if (found != values.end()) destination = found->second;
    };
    string_value("--output", result.output);
    string_value("--import", result.import_manifest);
    if (!result.import_manifest.empty()) {
        for (const auto& value : values)
            if (value.first != "--output" && value.first != "--import")
                throw std::runtime_error("generation option cannot be used with --import: " + value.first);
        return result;
    }
    string_value("--codec", result.codec);
    string_value("--variant", result.variant);
    string_value("--aomenc", result.aomenc);
    if (result.codec != "av1" && result.codec != "hevc")
        throw std::runtime_error("codec must be av1 or hevc");
    if (result.variant != "sdr8" && result.variant != "hdr10")
        throw std::runtime_error("variant must be sdr8 or hdr10");
    auto number = [&](const char* key, uint32_t& destination, uint32_t minimum, uint32_t maximum) {
        auto found = values.find(key);
        if (found == values.end()) return;
        const auto& text = found->second;
        uint32_t parsed = 0;
        auto conversion = std::from_chars(text.data(), text.data() + text.size(), parsed);
        if (conversion.ec != std::errc{} || conversion.ptr != text.data() + text.size()
            || parsed < minimum || parsed > maximum)
            throw std::runtime_error(std::string(key) + " must be an integer from "
                                     + std::to_string(minimum) + " to " + std::to_string(maximum));
        destination = parsed;
    };
    number("--width", result.width, 64, 8192);
    number("--height", result.height, 64, 8192);
    number("--fps", result.fps, 1, 1000);
    number("--frames", result.frames, 1, 100000);
    number("--gop", result.gop, 1, 100000);
    if (result.width % 2 || result.height % 2)
        throw std::runtime_error("width and height must be even for 4:2:0");
    if (values.count("--bitrate-mbps")) {
        // Convert decimal Mbps exactly, without binary floating point rounding or
        // accepting non-finite values, exponent notation, or a truncated target.
        const auto& text = values.at("--bitrate-mbps");
        const auto dot = text.find('.');
        const auto whole_text = text.substr(0, dot);
        const auto fraction_text = dot == std::string::npos ? std::string{} : text.substr(dot + 1);
        auto reject = [] {
            throw std::runtime_error("--bitrate-mbps must be a decimal number from 0.001 to 1000 with at most 3 decimal places");
        };
        auto digits = [](const std::string& value) {
            return std::all_of(value.begin(), value.end(), [](char c) { return c >= '0' && c <= '9'; });
        };
        if (whole_text.empty() || !digits(whole_text) || !digits(fraction_text)
            || fraction_text.size() > 3 || (dot != std::string::npos && fraction_text.empty()))
            reject();
        uint32_t whole = 0;
        auto converted = std::from_chars(whole_text.data(), whole_text.data() + whole_text.size(), whole);
        if (converted.ec != std::errc{} || converted.ptr != whole_text.data() + whole_text.size() || whole > 1000)
            reject();
        uint32_t fraction = 0;
        for (char digit : fraction_text) fraction = fraction * 10 + uint32_t(digit - '0');
        for (auto places = fraction_text.size(); places < 3; ++places) fraction *= 10;
        uint32_t bitrate = whole * 1000 + fraction;
        if (bitrate < 1 || bitrate > 1000000) reject();
        result.bitrate_kbps = bitrate;
    }
    return result;
}

} // namespace fixture
