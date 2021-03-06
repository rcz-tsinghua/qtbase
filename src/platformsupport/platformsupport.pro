TEMPLATE = subdirs
QT_FOR_CONFIG += gui-private

SUBDIRS = \
    devicediscovery \
    fbconvenience

qtConfig(evdev)|qtConfig(tslib)|qtConfig(libinput)|qtConfig(integrityhid)|qtConfig(xkbcommon) {
    SUBDIRS += input
    input.depends += devicediscovery
}

qtConfig(egl): \
    SUBDIRS += eglconvenience
qtConfig(xlib):qtConfig(opengl):!qtConfig(opengles2): \
    SUBDIRS += glxconvenience
qtConfig(kms): \
    SUBDIRS += kmsconvenience

!android:linux*:qtHaveModule(dbus) \
    SUBDIRS += linuxofono

