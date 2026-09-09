#pragma once
// Private, opt-in diagnostic interface. Not installed or part of the C ABI.
#include <cstdint>
#include <cstddef>
#include <vector>
namespace mav {
struct ExperimentVTCall { uint64_t submit_ns, return_ns; };
void experiment_vt_begin(bool synchronous, std::size_t capacity);
const std::vector<ExperimentVTCall>& experiment_vt_calls();
uint64_t experiment_vt_overflow();
}
