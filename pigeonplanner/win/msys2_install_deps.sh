#!/bin/bash

set -e

if [[ "$MSYSTEM" == "MINGW32" ]]; then
    MSYS2_ARCH="i686"
else
    MSYS2_ARCH="x86_64"
fi

pacman --noconfirm -S --needed \
    upx \
    mingw-w64-$MSYS2_ARCH-gtk3 \
    mingw-w64-$MSYS2_ARCH-pkg-config \
    mingw-w64-$MSYS2_ARCH-cairo \
    mingw-w64-$MSYS2_ARCH-gobject-introspection \
    mingw-w64-$MSYS2_ARCH-python3 \
    mingw-w64-$MSYS2_ARCH-python3-gobject \
    mingw-w64-$MSYS2_ARCH-python3-cairo \
    mingw-w64-$MSYS2_ARCH-python3-pip \
    mingw-w64-$MSYS2_ARCH-python3-setuptools \
    mingw-w64-$MSYS2_ARCH-osm-gps-map
