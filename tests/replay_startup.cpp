// Pure scheduling policy tests, including Release builds with NDEBUG.
#include "replay_startup.h"
#include <iostream>

static void require(bool condition, const char* message) {
    if (!condition) throw std::runtime_error(message);
}

template <typename Exception, typename Function>
static void rejects(Function function, const char* message) {
    try {
        function();
    } catch (const Exception&) {
        return;
    }
    throw std::runtime_error(message);
}

int main() {
    try {
        constexpr uint64_t start = 1000000000;
        constexpr uint64_t interval240 = 1000000000 / 240;
        constexpr uint64_t interval60 = 1000000000 / 60;
        const replay::InitialDeadline legacy(start, interval240, 16, 0);
        const replay::InitialDeadline grace(start, interval240, 16, 100);

        // A 72 ms session setup pushes frame 1 beyond the legacy 16-frame
        // budget at 240 Hz. The initial floor permits it to catch up.
        require(legacy.expired(start + 72000000, start + interval240),
                "legacy policy must expose the observed startup failure");
        require(!grace.expired(start + 72000000, start + interval240),
                "initial startup allowance must admit the 72 ms case");
        require(grace.deadline(start + interval240) == start + 100000000,
                "startup floor must be anchored to stream start");

        // The floor cannot tighten an existing, longer queue allowance.
        const replay::InitialDeadline slower(start, interval60, 16, 100);
        require(slower.deadline(start) == start + interval60 * 16,
                "60 Hz must retain its 266.7 ms queue allowance");
        require(!slower.expired(start + 200000000, start),
                "startup floor must not shorten the 60 Hz allowance");

        // The same strict boundary is used before submit and after capacity
        // waits: equality is allowed; one nanosecond later is expired.
        require(!grace.expired(start + 100000000, start),
                "deadline equality must remain admissible");
        require(grace.expired(start + 100000001, start),
                "startup deadline must expire without a hidden extension");

        for (uint64_t index : {uint64_t(0), uint64_t(1), uint64_t(60), uint64_t(240), uint64_t(2400)}) {
            const uint64_t arrival = start + index * interval240;
            const uint64_t ordinaryDeadline = arrival + interval240 * 16;
            require(legacy.deadline(arrival) == ordinaryDeadline,
                    "zero grace must preserve every legacy deadline");
            if (index >= 60) {
                require(grace.deadline(arrival) == ordinaryDeadline,
                        "keyframes and fixture loops must not rearm grace");
                require(grace.expired(ordinaryDeadline + 1, arrival),
                        "late steady-state frames must still expire");
            }
        }

        require(replay::parseStartupGraceMs("0") == 0, "zero grace must parse");
        require(replay::parseStartupGraceMs("10000") == 10000, "maximum grace must parse");
        for (auto input : {"", "-1", "+1", "1.5", "1e2", " 1", "1 ", "250ms", "10001",
                           "18446744073709551616", "NaN"}) {
            rejects<std::invalid_argument>([&] { replay::parseStartupGraceMs(input); },
                                           "invalid startup grace was accepted");
        }
        constexpr auto maximum = std::numeric_limits<uint64_t>::max();
        rejects<std::overflow_error>([&] { replay::InitialDeadline bad(start, maximum, 2, 0); },
                                     "queue duration overflow was accepted");
        rejects<std::overflow_error>([&] { replay::InitialDeadline bad(maximum, 1, 1, 1); },
                                     "initial floor overflow was accepted");
        rejects<std::overflow_error>([&] { legacy.deadline(maximum); },
                                     "per-frame deadline overflow was accepted");
        rejects<std::invalid_argument>([&] { replay::InitialDeadline bad(start, 1, 1, 10001); },
                                       "programmatic grace overflow was accepted");

        std::cout << "PASS fixed initial admission deadline, strict inputs, and overflow checks\n";
        return 0;
    } catch (const std::exception& error) {
        std::cerr << "FAIL replay startup: " << error.what() << '\n';
        return 1;
    }
}
