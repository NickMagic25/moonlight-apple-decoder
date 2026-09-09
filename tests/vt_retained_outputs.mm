#include "../tools/vt_retained_outputs.hpp"
#include <array>
#include <cstdio>
#include <cstdlib>
#include <stdexcept>
#include <string>

// CPU-owned pixel storage only: no decoder, IOSurface or Metal device required.
namespace {
unsigned checks = 0;
void require(bool condition, const char* message) {
    ++checks;
    if (!condition) throw std::runtime_error(message);
}

struct Environment {
    bool present;
    std::string value;
    Environment() : present(std::getenv("MAV_VT_RETAIN_OUTPUTS") != nullptr),
        value(present ? std::getenv("MAV_VT_RETAIN_OUTPUTS") : "") {}
    ~Environment() {
        if (present) setenv("MAV_VT_RETAIN_OUTPUTS", value.c_str(), 1);
        else unsetenv("MAV_VT_RETAIN_OUTPUTS");
    }
};

void configure(vt_experiment::RetainedOutputs& ring, const char* value) {
    if (value) require(setenv("MAV_VT_RETAIN_OUTPUTS", value, 1) == 0, "setenv failed");
    else require(unsetenv("MAV_VT_RETAIN_OUTPUTS") == 0, "unsetenv failed");
    ring.configureFromEnvironment();
}

struct Storage {
    std::array<uint8_t, 16> bytes{};
    unsigned releases = 0;
    bool wrong_address = false;
    static void released(void* context, const void* address) {
        auto& storage = *static_cast<Storage*>(context);
        storage.wrong_address |= address != storage.bytes.data();
        ++storage.releases;
    }
};

class Source {
    CVPixelBufferRef value_ = nullptr;
public:
    explicit Source(Storage& storage) {
        const auto status = CVPixelBufferCreateWithBytes(nullptr, 2, 2,
            kCVPixelFormatType_32BGRA, storage.bytes.data(), 8, Storage::released,
            &storage, nullptr, &value_);
        if (status || !value_) throw std::runtime_error("CPU pixel buffer creation failed");
    }
    ~Source() { reset(); }
    Source(const Source&) = delete;
    Source& operator=(const Source&) = delete;
    CVPixelBufferRef get() const { return value_; }
    void reset() { if (value_) CVPixelBufferRelease(value_); value_ = nullptr; }
};

void checkReleased(const Storage& storage, unsigned count, const char* message) {
    require(storage.releases == count && !storage.wrong_address, message);
}

void parseTests() {
    using Ring = vt_experiment::RetainedOutputs;
    require(Ring::parseLimit(nullptr) == 0, "absent retention control must disable retention");
    for (unsigned count = 0; count <= 8; ++count)
        require(Ring::parseLimit(std::to_string(count).c_str()) == count, "valid retention count changed");
    require(Ring::parseLimit("0008") == 8, "decimal leading zeros changed value");
    for (const char* value : {"", "-1", "+1", " 1", "1 ", "1\n", "9", "10", "0x8", "true",
                             "4294967296", "18446744073709551616", "99999999999999999999999999999"}) {
        bool rejected = false;
        try { (void)Ring::parseLimit(value); }
        catch (const std::invalid_argument&) { rejected = true; }
        require(rejected, "invalid retention control accepted");
    }
}

void disabledAndLifetimeTests() {
    Storage disabled;
    {
        vt_experiment::RetainedOutputs ring;
        require(ring.limit() == 0 && ring.size() == 0, "default ring must be inert");
        configure(ring, nullptr);
        Source source(disabled);
        ring.retain(source.get());
        source.reset();
        require(ring.size() == 0, "disabled ring retained a buffer");
        checkReleased(disabled, 1, "disabled ring extended source lifetime");
        ring.clear();
    }
    checkReleased(disabled, 1, "disabled ring released storage twice");

    Storage held;
    {
        vt_experiment::RetainedOutputs ring;
        configure(ring, "1");
        ring.retain(nullptr);
        require(ring.size() == 0, "null output occupied a ring slot");
        Source source(held);
        ring.retain(source.get());
        source.reset();
        require(ring.size() == 1, "ring did not report retained output");
        checkReleased(held, 0, "ring failed to retain after caller release");
    }
    checkReleased(held, 1, "ring destructor did not release final owner");
}

void overwriteAndClearTests() {
    Storage first, second, third;
    vt_experiment::RetainedOutputs ring;
    configure(ring, "2");
    { Source source(first); ring.retain(source.get()); }
    { Source source(second); ring.retain(source.get()); }
    require(ring.size() == 2, "two-slot ring has wrong occupancy");
    checkReleased(first, 0, "first output released before ring filled");
    checkReleased(second, 0, "second output released before replacement");
    { Source source(third); ring.retain(source.get()); }
    checkReleased(first, 1, "overwrite did not release oldest output");
    checkReleased(second, 0, "overwrite released the newer output");
    checkReleased(third, 0, "new output not retained after replacement");
    require(ring.size() == 2, "overwrite changed bounded occupancy");
    bool rejected = false;
    try { ring.configureFromEnvironment(); }
    catch (const std::logic_error&) { rejected = true; }
    require(rejected, "live ownership configuration change accepted");
    ring.clear();
    require(ring.size() == 0 && ring.limit() == 2, "clear changed configured limit or kept occupancy");
    checkReleased(second, 1, "clear did not release second output");
    checkReleased(third, 1, "clear did not release third output");
    ring.clear();
    checkReleased(first, 1, "repeated clear released first output twice");
    checkReleased(second, 1, "repeated clear released second output twice");
    checkReleased(third, 1, "repeated clear released third output twice");
    configure(ring, "0");
    require(ring.limit() == 0, "empty ring could not disable retention");
}

void sameBufferReplacementTest() {
    Storage storage;
    vt_experiment::RetainedOutputs ring;
    configure(ring, "1");
    Source source(storage);
    auto pixel = source.get();
    ring.retain(pixel);
    source.reset(); // The ring is now the only owner.
    for (unsigned repeat = 0; repeat < 3; ++repeat) ring.retain(pixel);
    checkReleased(storage, 0, "same-buffer replacement released the sole owner too early");
    require(ring.size() == 1, "same-buffer replacement grew occupancy");
    ring.clear();
    checkReleased(storage, 1, "same-buffer replacement leaked a reference");
}

void maximumCapacityTest() {
    std::array<Storage, 9> storage;
    {
        vt_experiment::RetainedOutputs ring;
        configure(ring, "8");
        for (unsigned index = 0; index < 8; ++index) {
            Source source(storage[index]);
            ring.retain(source.get());
        }
        require(ring.size() == 8 && ring.limit() == 8, "maximum ring capacity incorrect");
        for (unsigned index = 0; index < 8; ++index)
            checkReleased(storage[index], 0, "maximum ring dropped an output before capacity");
        { Source source(storage[8]); ring.retain(source.get()); }
        require(ring.size() == 8, "maximum ring exceeded its bound");
        checkReleased(storage[0], 1, "maximum ring did not evict its oldest output");
        for (unsigned index = 1; index < 9; ++index)
            checkReleased(storage[index], 0, "maximum ring evicted the wrong output");
    }
    for (const auto& item : storage) checkReleased(item, 1, "maximum ring destructor leaked ownership");
}
} // namespace

int main() {
    try {
        Environment environment;
        parseTests();
        disabledAndLifetimeTests();
        overwriteAndClearTests();
        sameBufferReplacementTest();
        maximumCapacityTest();
        std::printf("PASS: %u retained-output checks (CPU pixel buffers only)\n", checks);
        return 0;
    } catch (const std::exception& error) {
        std::fprintf(stderr, "FAIL: %s\n", error.what());
        return 1;
    }
}
