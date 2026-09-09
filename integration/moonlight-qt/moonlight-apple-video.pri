# Included from the consumer's app/app.pro. The implementation stays in this
# independently buildable library repository and uses only the installed C ABI.
macx:contains(QMAKE_APPLE_DEVICE_ARCHS, arm64):!contains(QMAKE_APPLE_DEVICE_ARCHS, x86_64) {
    MAV_INSTALL_DIR = $$(MOONLIGHT_APPLE_VIDEO_INSTALL_DIR)
    isEmpty(MAV_INSTALL_DIR):error("Set MOONLIGHT_APPLE_VIDEO_INSTALL_DIR to the CMake install prefix")
    !exists($$MAV_INSTALL_DIR/lib/libmoonlight-apple-video.a):error("Build/install moonlight-apple-video first")
    DEFINES += HAVE_MOONLIGHT_APPLE_VIDEO
    INCLUDEPATH += $$PWD $$MAV_INSTALL_DIR/include $$_PRO_FILE_PWD_/streaming/video
    SOURCES += $$PWD/apple_video.cpp $$PWD/apple_video_frame.cpp
    HEADERS += $$PWD/apple_video.h $$PWD/apple_video_frame.h $$PWD/apple_video_timing.h
    LIBS += $$MAV_INSTALL_DIR/lib/libmoonlight-apple-video.a
    LIBS += -framework VideoToolbox -framework CoreMedia -framework CoreVideo -framework CoreFoundation -framework IOSurface -framework Foundation
    message("Native Apple video adapter enabled (AV1 + HEVC)")
} else {
    message("Native Apple video adapter requires an arm64-only macOS build; existing backends preserved")
}
