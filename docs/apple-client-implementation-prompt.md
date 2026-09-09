# Apple Moonlight client implementation prompt

Use the following as the initial prompt for a new implementation task. Research and repository context were checked on September 9, 2026; verify API availability and upstream host behavior against the versions selected for implementation.

---

You are building a new native Apple game-streaming client using the Moonlight protocol. Deliver a working application, with an implementation that can be measured and maintained, rather than stopping at an architecture proposal or a UI demonstration.

## 1. Product objective and scope

Build a SwiftUI application with a dedicated Metal video renderer and HDR support. The primary targets are native macOS, iOS and iPadOS. Share the streaming engine with a tvOS target, including controller and focus navigation. Keep platform adapters separate so visionOS can be considered later without making it a first-release requirement.

The application connects to **Sunshine and Apollo hosts** using the Moonlight/GameStream-compatible protocol. Moonlight Qt, Moonlight iOS and VoidLink are client compatibility and feature references. They are not the servers this application connects to.

Required capabilities:

- Automatic host discovery, manual host/IP/hostname entry, pairing, saved hosts, application listing, launch/resume, disconnect and explicitly requested quit of the remote application.
- Standard PIN pairing and Apollo token-assisted pairing, implemented according to the verified host protocol described below.
- HEVC Main/Main10 and AV1 Main 8/10-bit video, with hardware capability negotiation and correct SDR/HDR rendering.
- User-selectable stream resolution, frame rate and bitrate, including custom dimensions and a native-display **“Native — Safe Area”** resolution that keeps the video rectangle clear of the notch or Dynamic Island.
- Low-latency audio, controller, keyboard, mouse and appropriate touch input.
- Good performance on Ethernet and Wi-Fi, observable network behavior, and documented Apple Game Mode integration on supported platforms.
- Native, accessible SwiftUI host/library/settings/stream-overlay screens. Use AppKit/UIKit wrappers only where the streaming surface or platform services require them.

Build the client in its own repository. Keep the decoder as a reusable package dependency. Use the current stable Swift/Xcode toolchain, explicit concurrency boundaries, and public Apple APIs in production. Establish and document minimum OS versions from the actual API requirements; the decoder package's minimum versions do not automatically determine the application's minimum versions.

### Mandatory: our decoder is the only video-decoding implementation

**Every compressed video frame must be decoded by `moonlight-apple-decoder` through its `MoonlightAppleVideo` Swift package product. This is an architectural requirement, not a preferred backend.** We want to own the decoder integration, capability policy, recovery, output negotiation, instrumentation and future changes in one codebase.

- Do not add a decoder selector, pluggable third-party decoder system, or automatic fallback to another video decoder.
- Do not use FFmpeg/libavcodec, another Moonlight client's video-decoding implementation, app-level `VTDecompressionSession` calls, or AVPlayer/AVFoundation/`AVSampleBufferDisplayLayer` compressed-video decoding as an alternate path. VideoToolbox session creation and decoding belong inside our package.
- The Metal renderer accepts the package's already-decoded CVPixelBuffers and metadata. It does not decode compressed samples.
- Common-c supplies transport and session services, not a competing video decoder. Required audio-codec and transport/crypto libraries are separate from this video-decoder restriction.
- Keep hardware decoding required. When our package cannot decode the negotiated stream on a device, negotiate a supported HEVC/AV1 configuration through the same package or fail with a clear compatibility explanation. Never silently switch to software video decoding or an unimplemented codec.
- Canonical versus native/lossless output is a configuration choice within our decoder, not a backend choice. Any future H.264, additional profile, format or recovery support must be added to and tested in our package first.
- If an application requirement exposes a limitation in the decoder, fix the package with a focused, versioned change. Do not work around it by introducing a parallel decoder in the app.

This gives us control of the client and decoder code while retaining VideoToolbox as the package's Apple hardware-decoding implementation; it does not imply control over Apple's closed driver or firmware.

## 2. Repositories and starting evidence

Inspect these before designing substitutes:

- Decoder: https://github.com/NickMagic25/moonlight-apple-decoder
- Moonlight transport: https://github.com/moonlight-stream/moonlight-common-c
- Desktop reference: https://github.com/moonlight-stream/moonlight-qt
- Apple reference: https://github.com/moonlight-stream/moonlight-ios
- VoidLink reference: https://github.com/The-Fried-Fish/VoidLink-previously-moonlight-zwm
- Apollo host: https://github.com/ClassicOldSong/Apollo
- Artemis Apollo pairing reference: https://github.com/ClassicOldSong/moonlight-android/tree/moonlight-noir

The decoder was inspected at revision `f1a3bc1e3b3686d53f9e454dcfe4dd209bab1e6f`. Start with a reproducible pinned revision or reviewed release; document upgrades. For local development, use a SwiftPM local package override rather than copying the decoder into the application.

Important decoder files are `Package.swift`, `include/moonlight_apple_video/decoder.h`, `examples/swift/main.swift`, `docs/architecture.md`, and `integration/moonlight-qt/`. Read the ownership and concurrency contract, not just the Swift smoke example. The Qt adapter is a useful reference for common-c frame ownership, timestamp conversion, decoder backpressure and keyframe recovery; the new application does not need its FFmpeg/Qt/SDL wrapping.

Preserve dependency licenses and notices, including the decoder's existing GPL license, and document the distribution model and dependency build requirements.

## 3. Architecture and ownership

Use clear boundaries for:

1. SwiftUI application state and user flows.
2. Host discovery, authenticated host control and host capability profiles.
3. A small C/Objective-C bridge to `moonlight-common-c` and its required dependencies.
4. A Swift-facing `MoonlightAppleVideo` decoder adapter.
5. A dedicated Metal renderer and display-pacing controller.
6. Audio output, input forwarding, display geometry and network-state services.
7. Structured diagnostics and a replay/performance harness.

These may be modules or targets; choose the simplest organization that keeps the boundaries testable. Use Swift concurrency for orchestration and `@MainActor` UI state. The receive, decode, render and audio paths must not depend on per-frame SwiftUI updates or unbounded actor/task creation.

Use a dedicated serialized decoder/control worker. VideoToolbox submission can block even with asynchronous decompression enabled. Keep it off the network receive thread, main thread and audio callback. Evaluate common-c's pull renderer interface and release each video-frame handle exactly once at the correct ownership boundary. Follow its actual `LiWaitForNextVideoFrame`/`LiCompleteVideoFrame` contracts and selected capabilities.

Keep compressed input, decoder outstanding work, decoded-frame handoff, GPU work and audio buffering explicitly bounded. Specify the capacity, overflow policy and ownership at each boundary. Start with the decoder's two-frame outstanding default and a small decoded-frame/GPU queue; tune only with measurements.

A latest-frame policy may replace obsolete **decoded presentation frames**. It must not arbitrarily discard compressed reference pictures. Handle congestion through common-c's recovery behavior, bounded admission, keyframe requests and explicit stream restart where necessary. Do not hold C frame pointers or borrowed callbacks across asynchronous work without acquiring ownership.

On shutdown or reconfiguration, close admission, join API users, resolve/cancel decoder callbacks, retire stale generations and release GPU-held resources after their last use. Never release a texture or pixel buffer still referenced by an in-flight GPU command.

## 4. Integrate the existing decoder through SwiftPM

Depend on the package's `MoonlightAppleVideo` product and import its C Clang module from Swift. Swift C++ interoperability is not required. Keep the public ABI boundary intact and wrap it in a small, well-documented Swift owner.

Honor these existing contracts:

- `mav_decoder_submit_copy` accepts one complete HEVC Annex-B access unit or an AV1 low-overhead temporal unit with explicit OBU sizes. Preserve parameter sets and color metadata. Do not pass RTP fragments or container framing directly.
- `MAV_OK` means the compressed bytes have been acquired and exactly one terminal completion is owed. `MAV_WOULD_BLOCK` or another synchronous rejection consumes no input and produces no completion.
- Callbacks can execute inline and on different threads. A callback may retain the pixel buffer, record bounded diagnostics and signal another worker. It must not submit, wait, drain, reset or destroy the decoder.
- Completion structures and CVPixelBuffers are borrowed during the callback. Acquire a strong/retained buffer reference before returning, and keep it alive until all GPU uses complete. Review Swift `Unmanaged`/ARC ownership explicitly; do not mark unsafe objects `@unchecked Sendable` without a documented synchronization and lifetime proof.
- Serialize submit/control operations. Use event-driven capacity handling, not polling loops. Distinguish ordinary capacity pressure from a pending configuration change.
- Preserve generation/frame identity and AV1 hidden/show-existing/no-display accounting. Suppress obsolete presentation output after reset without losing terminal-completion accounting.
- Map transport timestamps into the documented monotonic clock domain before comparing them with decoder traces. Do not subtract unrelated host, RTP, common-c and Apple clock values.

Advertise only codecs, profiles, bit depths and chroma formats the active decoder and renderer can handle. The package currently supports low-delay 4:2:0 HEVC/AV1 and has no H.264 backend. It currently rejects HEVC B slices and display reordering; test real host encoders, including configurations that may emit low-delay B pictures. Do not silently advertise support or fall back to unimplemented H.264. Add a narrow, independently validated decoder enhancement if real interoperability requires it, or report an actionable unsupported configuration.

The package's codec-level capability query is only a candidate check. Confirm the exact stream through successful hardware output. Auto codec selection should intersect host, device and renderer capabilities; allow explicit HEVC or AV1 preference and make any renegotiation visible. All selections continue to use the same package and hardware-required path.

### Native output requires an explicit integration step

At the inspected revision, native/lossless output selection is exposed through diagnostic `MAV_VT_EXPERIMENTS` controls. The ordinary SwiftPM target does not enable those controls, and zero pixel-format constraints currently select canonical NV12/P010-family output. Do not assume that merely importing the package enables native lossless output.

If native output is adopted, add or use a reviewed, explicit production configuration in the decoder package, with ABI/version compatibility and canonical-format fallback defined. Keep that focused package change separate and test it through SwiftPM. Do not enable the entire experimental build or rely on process environment variables in the shipping application.

## 5. Host discovery, pairing and Apollo compatibility

Use Bonjour discovery for `_nvstream._tcp`, with manual address/port entry, IPv4/IPv6 support and useful connection failures. Persist a stable client identity and host identity. Provide clearly distinct discovered, unpaired, paired, offline and streaming states.

Implement ordinary Moonlight PIN pairing and the certificate challenge sequence using the established protocol. Support pairing cancellation, timeout, wrong PIN, changed host certificate, unpair/re-pair and host removal. Keep private keys, pairing credentials and persistent secrets in Keychain; redact credentials, pairing URLs and authentication material from logs.

### Apollo “token” pairing: use the real protocol

The user requires an Apollo token-based alternative to manual PIN entry. Verify the deployed Apollo version and the kind of token it supplies before deciding the API contract.

Current upstream evidence describes an OTP/passphrase pairing link of the form `art://HOST:HTTPPORT?pin=OTP&passphrase=...&name=...`. Accept a pasted pairing link and the corresponding separate fields. Validate and percent-decode it correctly, including IPv6 addresses and custom ports. Consume the OTP through Artemis-compatible `otpauth` and complete normal certificate pairing. Implement the exact hash/salt encoding from the selected upstream revision, with cross-language test vectors; do not invent a bearer-token media protocol. [Apollo pairing-link source](https://github.com/ClassicOldSong/Apollo/blob/master/src_assets/common/assets/web/pin.html), [Artemis pairing implementation](https://github.com/ClassicOldSong/moonlight-android/blob/moonlight-noir/app/src/main/java/com/limelight/nvstream/http/PairingManager.java).

Apollo's inspected management API uses an authenticated session cookie, including for OTP generation. A reusable arbitrary API bearer-token login is not established by that implementation. If the user's host/fork actually provides a separate API-token mechanism, implement it behind a host-authentication capability adapter after verifying its endpoints, scopes and credential exchange. Keep this requirement explicit if that server contract is unavailable; do not pretend an OTP or an admin cookie is the requested long-lived API token. [Apollo authentication and OTP endpoints](https://github.com/ClassicOldSong/Apollo/blob/master/src/confighttp.cpp).

The normal client flow should consume a user-supplied pairing credential without requiring host administrator credentials. Treat expired, malformed, incorrect and already-used tokens as distinct recoverable failures. Store the resulting paired identity; do not retain a one-time pairing secret unnecessarily.

Respect Apollo host permissions. Listing apps, launching apps and forwarding different input classes may have separate grants. A permission error must not be reported as a decoder or network failure. Keep optional Apollo extensions behind capability/version checks so standard Sunshine hosts remain supported. Preserve host certificate validation and the established pairing trust bootstrap; do not globally disable TLS verification.

## 6. Resolution, frame rate and bitrate

Provide global defaults and per-host profiles, with optional per-application overrides. Store requested settings separately from host negotiation results and measured active behavior.

Required controls:

- Resolution presets such as 720p, 1080p, 1440p and 4K, plus custom width/height.
- Native display, Native — Safe Area, and a window-sized option where appropriate.
- Frame-rate presets including 30/60/90/120 where supported, plus custom/automatic display-matched selection. Support higher modes only when the host and actual display path can sustain them. “Requested stream FPS” and “display refresh rate” are separate values.
- A bitrate slider and numeric entry labeled in Mbps, with precise conversion to protocol units. Offer a sensible automatic initial value, preserve a manual override and show the active request. Do not claim resolution/FPS/bitrate can change seamlessly mid-stream unless that host protocol supports it; otherwise reconnect through a clear controlled transition.
- Codec Auto/HEVC/AV1 and HDR Auto/On/Off, with capability-aware explanations and explicit handling when required HDR cannot be honored.
- Aspect-fit by default, with deliberate aspect-fill/crop and integer/pixel scaling options where useful. Do not stretch images silently.

Negotiate dimensions, frame rate, bitrate, codec, HDR and color capabilities through the host's actual launch/stream configuration. Apollo can use its virtual display to match requested geometry; standard Sunshine behavior depends on host display configuration. Do not promise arbitrary host resolution changes solely because the client can render them. Show requested dimensions, decoded dimensions and presentation viewport separately.

## 7. Native — Safe Area behavior

This setting changes both the requested stream geometry and its presentation viewport. Merely adding SwiftUI padding around an unchanged full-display stream does not satisfy it.

Derive the largest usable rectangular video area from the **actual attached window/scene and destination display**, accounting for orientation and the current presentation mode. Distinguish logical points, backing/drawable pixels and physical display-mode pixels. Use the appropriate coordinate conversions and display-mode information instead of assuming `points × scale` always equals the panel's native resolution.

On UIKit platforms, resolve safe areas after the view is attached and laid out, using the scene's screen and live safe-area layout. On macOS, use the actual content viewport and the applicable `NSScreen` safe-area information. Native system full-screen can already place content inside the safe area: do not subtract the notch inset a second time. Account for the actual layout of custom borderless windows separately. [UIKit safe areas](https://developer.apple.com/documentation/uikit/uiview/safeareainsets), [macOS display safe areas](https://developer.apple.com/documentation/appkit/nsscreen/safeareainsets).

Map that rectangle into the requested pixel geometry, respecting encoder alignment and 4:2:0 even-dimension requirements. Keep coded dimensions, clean aperture, visible display aspect ratio and destination viewport distinct, including padded decoder output. Preserve aspect ratio, show the resulting exact dimensions and explain unavoidable rounding. Use black outside the fitted stream rectangle. A full-native alternative may intentionally use the whole display, but it must be a separate user choice.

Handle rotation, window resizing, Stage Manager, external displays, display-mode/scale changes and movement between displays. Recompute from current geometry; do not use device-model notch tables or assume the notch is always on the top edge. Coalesce layout changes and use a controlled stream reconfiguration instead of repeatedly restarting for every layout pass. Keep temporary OS overlays distinct from a permanent negotiated display mode.

Use the same viewport transform for video and absolute touch/mouse coordinates. Input in a letterbox/notch-excluded area must not produce misplaced host clicks. Test portrait/landscape, both landscape orientations, a notched Mac, a Dynamic Island iPhone, an iPad and an external display.

## 8. Metal renderer, color and HDR

Implement a native Metal surface hosted by SwiftUI through an AppKit/UIKit representable. Keep per-frame state and GPU submission outside SwiftUI observation. Reuse the Metal device, command queue, texture cache, samplers and pipeline states.

Import retained CVPixelBuffers through IOSurface/CoreVideo Metal interop. Aim for no CPU copies or CPU mapping of decoded pixel planes in the normal render path. Keep the pixel buffer and its `CVMetalTexture` wrappers alive until the corresponding command-buffer completion; retaining only the derived `MTLTexture` does not satisfy the Core Video texture-cache ownership contract. Do not allocate a CGImage, UIImage or AVFrame for every displayed frame. [Core Video Metal texture ownership](https://developer.apple.com/documentation/corevideo/cvmetaltexturecachecreatetexturefromimage%28_%3A_%3A_%3A_%3A_%3A_%3A_%3A_%3A_%3A%29).

Implement and validate canonical 8-bit NV12-family and 10-bit P010-family paths first. Then enable native/lossless formats only on supported hardware with a verified shader path. `&8v0` and especially packed 10-bit `&xv0` must not be treated as ordinary linear NV12/P010 bytes. Successful texture-view creation is not proof of correct shader sampling. The existing decoder tests' pixel-transfer readback also does not establish direct native-texture shader correctness. Add an actual render/readback comparison for the native Metal path before making it the default. Compare ordinary diagnostic render targets produced by the real import/shader path; include 10-bit code-value ramps, video/full range, chroma centers/siting, saturated colors, interpolation and padded dimensions. Establish sampled normalization rather than assuming P010 bit alignment applies to packed native textures.

Preserve and apply signaled range, YCbCr matrix, primaries, transfer function and chroma location. Handle SDR BT.709, HDR10 PQ/BT.2020 and the metadata supported by the decoder. Do not apply an 8-bit range expansion to 10-bit video, assume all streams share a matrix, or substitute BT.709 defaults when valid stream metadata exists.

Build a color-managed EDR presentation path. A linear floating-point drawable such as `rgba16Float`, an appropriate extended-linear color space, `wantsExtendedDynamicRangeContent` and compatible `CAEDRMetadata` are a candidate system-tone-mapping path, subject to platform availability and measured bandwidth cost. Implement the conversion from decoded YCbCr/transfer values to the declared layer space correctly. Define the relationship between reference white, nits and EDR values, and avoid double tone mapping. [Apple's Metal HDR workflow](https://developer.apple.com/documentation/metal/using-system-tone-mapping-on-video-content).

Observe the actual destination display's HDR/EDR capabilities and changing headroom. Handle HDR-to-SDR fallback, SDR content on an HDR display, brightness/Low Power Mode changes, and movement between SDR/HDR displays. Preserve mastering-display and content-light metadata where available. Gate any additional transfer format such as HLG on actual end-to-end implementation, not merely 10-bit decoding support.

Use `CAMetalDisplayLink` where appropriate and available, or the suitable platform display-link API. Keep `targetTimestamp` (the presentation-call deadline) separate from `targetPresentationTimestamp` (estimated display time). Use the drawable supplied by the Metal display-link update rather than independently acquiring a second one. Request one frame of preferred latency initially and support variable-refresh displays, while treating preferred frame rates and frame latency as requests rather than guarantees. With other pacing APIs, acquire drawables only when needed and keep GPU work bounded. Handle a missing drawable without blocking the receive or decoder callback path.

Avoid per-frame `waitUntilCompleted` or other CPU waits for GPU completion. Use completion handlers and bounded ownership. Measure low-latency and smooth-pacing policies, count decoded frames skipped for presentation separately, and keep actual presentation timestamps when the API exposes them. [CAMetalDisplayLink](https://developer.apple.com/documentation/quartzcore/cametaldisplaylink).

## 9. Audio and input

Use the established Moonlight audio protocol and Opus decoding with an appropriate Core Audio/Audio Unit or AVAudioEngine output path. Keep audio callbacks bounded and free of blocking locks, networking and heap churn. Use a measured bounded jitter buffer, preserve channel layout, handle underruns and route changes, and maintain A/V synchronization without accumulating video latency.

Configure AVAudioSession where applicable for the actual playback behavior. Do not select a voice-processing/game-chat mode merely because this is a game client. Measure wired and Bluetooth output latency separately. Handle interruptions, headphone changes, controller audio routes and disconnect/reconnect.

Use GameController and the applicable AppKit/UIKit keyboard, mouse and touch APIs. Support hot-plugged controllers, analog input, rumble/haptics when negotiated, relative mouse capture, keyboard forwarding and a reliable release/escape gesture. Scope capture to the active streaming session and restore normal system/UI input on exit or failure. Keep controller/touch handling responsive when the renderer or decoder is backpressured.

## 10. Wired/wireless networking and Apple integration

Preserve `moonlight-common-c` transport and recovery semantics initially, including its BSD sockets, packet framing, FEC, encryption, ENet/control behavior and congestion-related controls. Use Network.framework and Foundation where they fit discovery, path observation and host-control requests. Switching the media transport to QUIC, WebRTC or a new UDP abstraction is not an optimization unless it remains protocol-compatible and passes interoperability tests. [Apple's networking API selection guidance](https://developer.apple.com/documentation/technotes/tn3151-choosing-the-right-networking-api).

Use `NWPathMonitor` to observe interface and path changes and maintain useful network diagnostics. Record wired Ethernet, Wi-Fi/cellular, expensive/constrained status, IPv4/IPv6, RTT, jitter, loss, retransmission/FEC recovery and throughput. A global path monitor does not prove which interface an existing BSD socket uses; inspect the actual connection route/local address. Do not assume a fixed interface name or promise seamless migration when a path changes. [NWPath](https://developer.apple.com/documentation/network/nwpath).

Audit the existing socket service classes and buffer sizing before adding new knobs. Common-c already applies Apple voice/video service types in relevant paths. Preserve or tune those with measured evidence. Traffic classification primarily influences outgoing traffic; setting a client socket option does not guarantee prioritization of incoming video. Avoid oversized queues that trade packet loss for hidden latency. [Apple socket service types](https://developer.apple.com/library/archive/qa/qa1934/_index.html).

Implement a calm recovery policy for Ethernet/Wi-Fi switching, VPNs, transient outages, host sleep and application lifecycle changes. Show useful errors and retry affordances. If adaptive bitrate is offered, use sustained measurements and hysteresis, respect manual limits, and use only host-supported control paths.

Declare Bonjour services and local-network usage text on the targets where required. Handle permission denial and later changes. Raw broadcast Wake-on-LAN, if implemented, has different entitlement requirements from ordinary Bonjour discovery. Keep entitlement and privacy configuration platform-specific; current Apple documentation does not list local-network privacy as a tvOS feature. Validate through normally launched signed applications on real devices. [TN3179: local-network privacy](https://developer.apple.com/documentation/technotes/tn3179-understanding-local-network-privacy).

Use appropriate QoS and public activity/power APIs for active streaming, with scoped teardown. Observe thermal and Low Power Mode changes and provide measured quality/performance choices. Do not disable system networking features, force private media-engine modes or use busy-spinning as the default performance strategy.

### Game Mode

Configure documented eligibility using the current `LSSupportsGameMode` key and an accurate macOS game application category. Apple deprecates `GCSupportsGameMode` in favor of the newer key; retain legacy configuration only where the selected older deployment targets need it and verify those targets. Use native macOS full-screen presentation where required. [Current key](https://developer.apple.com/documentation/bundleresources/information-property-list/lssupportsgamemode), [legacy key](https://developer.apple.com/documentation/bundleresources/information-property-list/gcsupportsgamemode).

Game Mode is controlled by the OS and user. Eligibility is not proof of activation, and the user may have disabled it. Do not invent a force-enable API, a false “active” indicator, or guaranteed tvOS support. Validate through the available system Game Overlay/Metal HUD and compare the same workload with Game Mode enabled and disabled. [Apple's Game Mode requirements](https://support.apple.com/en-us/105118).

## 11. Performance goals and measurements

Optimize complete-frame arrival to actual presentation and input responsiveness. Keep network assembly, admission delay, parsing, VT submission call, VT submit-to-callback, callback handoff, texture import, GPU execution, presentation wait and audio delay as separate measurements.

Use `os_signpost`, Instruments System Trace, Metal profiling and appropriate device telemetry. Keep per-frame logging optional and bounded; export structured diagnostics without secrets. Report p50/p95/p99, frame losses and queue depths, not only averages. Distinguish measured presentation from a scheduling estimate, and do not call enqueue or GPU submission “displayed.” Use drawable presentation handlers/timestamps where available, treating a zero/unavailable presentation time as unconfirmed rather than successful display. Calibrate that clock domain against decoder timestamps. [Drawable presentation timing](https://developer.apple.com/documentation/metal/mtldrawable/presentedtime).

Prior decoder evidence on one M3 provides context, not a universal target:

- Native output produced roughly 0.06–0.11 ms median gains in repeated 4K60 comparisons.
- One instrumented HEVC native-output run measured approximately 2.63 ms VT submit-to-callback, including a roughly 0.67 ms submission call and a 1.47 ms post-return interval before an AppleAVD notification.
- Internal client-process and I/O-fence probes did not provide an effective HEVC/AV1 shortcut on that system.
- Sub-1 ms 4K60 decoding remains an aspiration, not an achieved or defensible hardware-independent acceptance threshold. Moving the call to another thread or returning before pixels are usable must not be counted as faster decoding.

The client should aim to add minimal processing and buffering around the decoder. Establish numerical CPU/GPU overhead budgets from a baseline, including a stretch goal of sub-1 ms combined client processing outside decode where the device permits it. Report unavoidable presentation cadence separately. Validate 4K60 first, then supported high-refresh modes; compare against existing Moonlight clients using the same host, encoder, scene, bitrate, device, display and network conditions.

## 12. Implementation milestones and acceptance criteria

Proceed through buildable, tested milestones:

1. **Foundation:** repository/project, reproducible dependencies, SwiftPM decoder import, host discovery/PIN pairing/app listing, platform and protocol capability matrix.
2. **Playable path:** real HEVC SDR streaming with correct Metal output, audio, controller/keyboard/mouse input, bounded queues, stream lifecycle and reconnect.
3. **Requested settings:** resolution/FPS/bitrate profiles, actual negotiation reporting, native/safe-area modes, external-display and input-coordinate correctness.
4. **Expanded compatibility:** AV1, HEVC/AV1 HDR10, Apollo OTP/token capability integration, permissions, and host-specific virtual-display negotiation.
5. **Optimization and platform completion:** validated native/lossless Metal path, Game Mode eligibility, wired/wireless profiling, tvOS interaction, sustained-load and fault testing.

Minimum validation must include:

- SwiftPM import/ownership and native app builds for the selected platforms; explicit capability behavior on devices without AV1 or HDR support. Audit dependencies and call sites to prove the package is the sole video decoder. Test that unsupported streams fail or renegotiate through this same package instead of activating a fallback backend.
- Standard Sunshine PIN pairing and the verified Apollo pairing flow, app launch/resume, insufficient permissions, expired/wrong token, certificate change and unpair/re-pair.
- Real HEVC and AV1 streams in SDR/HDR where supported; correct dimensions, color/range, visible frame identity, exact ownership/accounting and no unsupported-codec advertising.
- Reference-image/render-readback tests for YCbCr conversion and canonical/native texture sampling, plus real HDR display validation for black levels, reference white, highlights and metadata changes. SDR screenshots alone are not HDR validation.
- Safe-area geometry and input mapping across rotation, scaled/notched Macs, Dynamic Island devices, iPad windowing and external displays, including prevention of double-applied safe insets.
- Packet loss/reordering, decoder backpressure, missing drawables, stream reconfiguration, app suspension, audio interruptions, host disconnect and repeated start/stop without resource leaks or stale output.
- Ethernet and Wi-Fi performance, route changes, constrained/VPN/IPv6 paths, actual Game Mode eligibility/activation behavior and a sustained 30-minute target workload with thermal, memory, queue and frame-delivery measurements.

Use offline fixtures and mocked host responses for reproducible development, but mark real host/device/network/HDR checks unverified until executed. Simulator builds do not establish hardware decode, HDR output, network privacy or performance. If required hardware or host credentials are unavailable, finish independent work, state the exact remaining check and ask only for the missing access needed to run it.

Deliver source, build/run instructions, dependency versions, architecture/lifetime notes, a host/device compatibility matrix, benchmark methodology and results, and an honest list of remaining limitations. Make every promoted optimization explain its measured benefit, correctness evidence and effect on latency tails, CPU/GPU use and power. Begin with repository inspection and the first playable vertical slice, then continue through the remaining requirements.
