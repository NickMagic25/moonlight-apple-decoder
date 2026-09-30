#pragma once
#include "backend.hpp"
namespace mav {
// Stateless, complete independent-frame parser. It removes transport framing,
// validates all records before GPU admission, and recovers only known boundaries.
ParseResult prepare_pyrowave(const Span*, size_t, const mav_config&,
                             const mav_access_unit&, Prepared&, std::string&);
}
