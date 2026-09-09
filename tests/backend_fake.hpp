#pragma once
#include <cstddef>
namespace mav_test {
enum class Mode { Inline, Delayed, SynchronousFailure, AsynchronousFailure, Drop, Missing };
void mode(Mode);
void fail_next_configure();
void finish(bool concurrent=false);
size_t retained();
}
