#include "replay_qos.hpp"
#include <cstdio>
#include <thread>

int main() {
    bool passed = true;
    for (const char* mode : {"unchanged", "user-initiated", "user-interactive"}) {
        // Each request uses a fresh owned thread; no restoration or scheduler
        // mutation can leak between cases, and no VideoToolbox work is involved.
        std::thread worker([&] {
            ReplayQosExperiment experiment;
            experiment.select(mode);
            bool ok = experiment.apply();
            experiment.finish();
            ok = ok && experiment.end.observed && !experiment.end.get_status &&
                experiment.end.requested_class == experiment.start.requested_class &&
                experiment.end.relative_priority == experiment.start.relative_priority;
            if (experiment.mode == "unchanged") {
                ok = ok && !experiment.setter_attempted &&
                    experiment.start.requested_class == experiment.before.requested_class &&
                    experiment.start.relative_priority == experiment.before.relative_priority;
            } else {
                ok = ok && experiment.setter_attempted && !experiment.setter_status;
            }
            std::printf("%s: %s requested=%s start=%s end=%s setter=%d\n", mode, ok ? "PASS" : "FAIL",
                replayQosName(experiment.requested_class), replayQosName(experiment.start.requested_class),
                replayQosName(experiment.end.requested_class), experiment.setter_status);
            passed = passed && ok;
        });
        worker.join();
    }
    ReplayQosExperiment invalid;
    try { invalid.select("realtime"); passed = false; } catch (const std::runtime_error&) {}
    return passed ? 0 : 1;
}
