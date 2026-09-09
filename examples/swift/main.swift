import MoonlightAppleVideo
import CoreVideo

// Swift imports a Clang C module. Swift C++ interoperability is not enabled.
// A real consumer stores a strong CVPixelBuffer reference in its bounded queue;
// ARC then owns that reference independently of decoder reset/destruction.
func completion(_ context: UnsafeMutableRawPointer?, _ pointer: UnsafePointer<mav_completion>?) {
    guard let pointer else { return }
    let frame = pointer.pointee
    if let buffer = frame.pixel_buffer {
        let retained: CVPixelBuffer = buffer.takeUnretainedValue()
        withExtendedLifetime(retained) { _ = CVPixelBufferGetWidth(retained) }
    }
}
var config = mav_config()
mav_config_default(&config, MAV_CODEC_HEVC)
config.completion = completion
var decoder: OpaquePointer?
let created = mav_decoder_create(&config, &decoder)
precondition(created == MAV_OK)
precondition(mav_decoder_drain(decoder) == MAV_OK)
precondition(mav_decoder_reset(decoder) == MAV_OK)
precondition(mav_decoder_destroy(decoder) == MAV_OK)
print("PASS: Swift C ABI import and decoder ownership (no hardware decode claimed)")
