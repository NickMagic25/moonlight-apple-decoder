// Portable input validation: no Apple frameworks or encoder invocation.
#include "fixture_options.hpp"
#include <iostream>
#include <vector>

static fixture::Options parse(std::initializer_list<const char*> arguments) {
    std::vector<const char*> argv = {"mav-fixture"};
    argv.insert(argv.end(), arguments.begin(), arguments.end());
    return fixture::parse_options(static_cast<int>(argv.size()), argv.data());
}

static void require(bool condition, const char* message) {
    if (!condition) throw std::runtime_error(message);
}

static void invalid(std::initializer_list<const char*> arguments, const char* message) {
    try {
        (void)parse(arguments);
    } catch (const std::runtime_error& error) {
        require(std::string(error.what()).find(message) != std::string::npos,
                "invalid arguments produced an unexpected error");
        return;
    }
    throw std::runtime_error("invalid arguments were accepted");
}

int main() {
    try {
        auto defaults = parse({});
        require(defaults.codec == "av1" && defaults.variant == "sdr8"
                && defaults.width == 1920 && defaults.height == 1080
                && defaults.fps == 120 && defaults.frames == 120 && defaults.gop == 60
                && !defaults.bitrate_kbps, "legacy defaults changed");
        require(defaults.hevc_target_bitrate_bps() == 82944000, "legacy HEVC target changed");
        auto tiny = parse({"--width", "64", "--height", "64", "--fps", "1"});
        require(tiny.hevc_target_bitrate_bps() == 1000000, "legacy HEVC minimum changed");
        auto configured = parse({"--codec", "hevc", "--variant", "hdr10", "--width", "3440",
                                 "--height", "1440", "--fps", "240", "--frames", "480",
                                 "--gop", "120", "--bitrate-mbps", "150"});
        require(configured.bitrate_kbps == 150000 && configured.hevc_target_bitrate_bps() == 150000000
                && configured.gop == 120 && configured.fps == 240 && configured.frames == 480
                && configured.width == 3440 && configured.height == 1440
                && configured.variant == "hdr10", "explicit options were not applied");
        auto minimum = parse({"--bitrate-mbps", "0.001", "--gop", "1"});
        require(minimum.hevc_target_bitrate_bps() == 1000 && minimum.gop == 1,
                "explicit bitrate must not use legacy minimum");
        auto maximum = parse({"--width", "8192", "--height", "8192", "--fps", "1000",
                              "--frames", "100000", "--gop", "100000", "--bitrate-mbps", "1000"});
        require(maximum.hevc_target_bitrate_bps() == 1000000000, "explicit bitrate overflow");
        require(parse({"--bitrate-mbps", "1.25"}).bitrate_kbps == 1250,
                "fractional Mbps must convert exactly to AV1 kbps");
        require(parse({"--bitrate-mbps", "12.345"}).hevc_target_bitrate_bps() == 12345000,
                "fractional Mbps must convert exactly to HEVC bps");
        require(parse({"--bitrate-mbps", "1000.000"}).bitrate_kbps == 1000000,
                "maximum with fractional notation changed");
        for (const auto* value : {"50", "100", "250", "350"}) {
            auto options = parse({"--bitrate-mbps", value});
            auto mbps = static_cast<uint32_t>(std::stoul(value));
            require(options.bitrate_kbps == mbps * 1000, "high Mbps target must reach AV1 in kbps");
            require(options.hevc_target_bitrate_bps() == uint64_t(mbps) * 1000000,
                    "high Mbps target must reach HEVC in bps");
        }
        require(parse({"--width", "8192", "--height", "8192", "--fps", "1000"})
                    .hevc_target_bitrate_bps() == 22369621333ULL, "legacy bitrate overflow");
        require(parse({"--help"}).help, "help must not invoke generation");
        auto imported = parse({"--import", "capture/manifest.json", "--output", "destination"});
        require(imported.import_manifest == "capture/manifest.json" && imported.output == "destination",
                "import options changed");
        require(parse({"--codec", "hevc", "--aomenc", "unused-common-helper-option"}).codec == "hevc",
                "legacy validation helper passes --aomenc to both codecs");

        invalid({"--bitrate", "20000"}, "unknown option");
        invalid({"--bitrate-kbps", "50000"}, "replaced by --bitrate-mbps");
        invalid({"--help", "--unknown"}, "unknown option");
        invalid({"--fps", "60", "--fps", "120"}, "duplicate option");
        invalid({"--bitrate-mbps"}, "requires value");
        invalid({"--bitrate-mbps", "--frames", "120"}, "requires value");
        invalid({"--output", ""}, "requires value");
        invalid({"--import", "capture.json", "--bitrate-mbps", "10000"}, "cannot be used with --import");
        invalid({"--import", "capture.json", "--codec", "hevc"}, "cannot be used with --import");
        invalid({"--codec", "h264"}, "codec must");
        invalid({"--variant", "sdr10"}, "variant must");
        invalid({"--width", "65"}, "must be even");
        invalid({"--height", "8194"}, "--height must");
        invalid({"--width", "63"}, "--width must");
        invalid({"--fps", "0"}, "--fps must");
        invalid({"--fps", "1001"}, "--fps must");
        invalid({"--frames", "100001"}, "--frames must");
        invalid({"--gop", "0"}, "--gop must");
        invalid({"--gop", "100001"}, "--gop must");
        for (auto value : {"0", "-1", "+1", "0.0001", "1.0000", "1000.001", "1000mbps", " 1", "1 ",
                           "1001", "4294967296", "18446744073709551616", "NaN", "nan", "inf", "Infinity",
                           "1e2", "1.", ".5", "1.2.3", "1,5"})
            invalid({"--bitrate-mbps", value}, "--bitrate-mbps must");
        invalid({"--width", "4294969216"}, "--width must"); // Cannot wrap to 1920.
        invalid({"--frames", "120frames"}, "--frames must");
        std::cout << "PASS fixture option defaults, rate targets, strict inputs, and import isolation\n";
        return 0;
    } catch (const std::exception& error) {
        std::cerr << "FAIL fixture options: " << error.what() << '\n';
        return 1;
    }
}
