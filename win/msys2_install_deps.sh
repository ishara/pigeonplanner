#!/bin/bash

set -e

pacman --noconfirm -S --needed \
    upx \
    mingw-w64-x86_64-gtk3 \
    mingw-w64-x86_64-pkg-config \
    mingw-w64-x86_64-cairo \
    mingw-w64-x86_64-gobject-introspection \
    mingw-w64-x86_64-python3 \
    mingw-w64-x86_64-python3-gobject \
    mingw-w64-x86_64-python3-cairo \
    mingw-w64-x86_64-python3-pip \
    mingw-w64-x86_64-python3-setuptools \
    mingw-w64-x86_64-osm-gps-map
