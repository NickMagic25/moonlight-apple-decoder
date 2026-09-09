#pragma once

#include <pthread.h>
#include <pthread/qos.h>
#include <stdexcept>
#include <string>

// Replay-only experiment: never changes a decoder-owned callback thread.
struct ReplayQosObservation {
    qos_class_t requested_class = QOS_CLASS_UNSPECIFIED;
    int relative_priority = 0;
    int get_status = 0;
    bool observed = false;
};

inline ReplayQosObservation replayReadQos() noexcept {
    ReplayQosObservation result;
    result.get_status = pthread_get_qos_class_np(pthread_self(), &result.requested_class,
                                                &result.relative_priority);
    result.observed = true;
    return result;
}

inline const char* replayQosName(qos_class_t value) noexcept {
    switch (value) {
    case QOS_CLASS_USER_INTERACTIVE: return "user-interactive";
    case QOS_CLASS_USER_INITIATED: return "user-initiated";
    case QOS_CLASS_DEFAULT: return "default";
    case QOS_CLASS_UTILITY: return "utility";
    case QOS_CLASS_BACKGROUND: return "background";
    case QOS_CLASS_UNSPECIFIED: return "unspecified";
    default: return "unknown";
    }
}

struct ReplayQosExperiment {
    std::string mode = "unchanged";
    qos_class_t requested_class = QOS_CLASS_UNSPECIFIED;
    bool setter_attempted = false;
    int setter_status = 0;
    ReplayQosObservation before, start, end;

    void select(const std::string& value) {
        mode = value;
        if (value == "unchanged") requested_class = QOS_CLASS_UNSPECIFIED;
        else if (value == "user-initiated") requested_class = QOS_CLASS_USER_INITIATED;
        else if (value == "user-interactive") requested_class = QOS_CLASS_USER_INTERACTIVE;
        else throw std::runtime_error("qos must be unchanged, user-initiated, or user-interactive");
    }

    bool apply() noexcept {
        before = replayReadQos();
        if (mode != "unchanged") {
            setter_attempted = true;
            setter_status = pthread_set_qos_class_self_np(requested_class, 0);
        }
        start = replayReadQos();
        return !before.get_status && !start.get_status &&
            (!setter_attempted || (!setter_status && start.requested_class == requested_class &&
                                  start.relative_priority == 0));
    }

    void finish() noexcept { end = replayReadQos(); }
};
