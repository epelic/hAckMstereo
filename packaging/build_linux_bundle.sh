#!/usr/bin/env bash
set -euo pipefail

UBUNTU_VERSION="${1:?Ubuntu version required}"
APP_VERSION="${2:-1.0.2}"
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
BUILD_ROOT="$ROOT/linux-build/$UBUNTU_VERSION"
VENV="$BUILD_ROOT/venv"
PKG="$BUILD_ROOT/package"
DIST="$ROOT/linux-dist"

rm -rf "$BUILD_ROOT"
mkdir -p "$BUILD_ROOT" "$DIST"
python3 -m venv "$VENV"
"$VENV/bin/python" -m pip install --upgrade pip
"$VENV/bin/python" -m pip install numpy PySide6 sounddevice pyinstaller

cd "$ROOT"
"$VENV/bin/pyinstaller" --noconfirm --clean --windowed --name hAckMstereo \
  --icon assets/hackmstereo-icon.png \
  --add-data "assets/hackmstereo-icon.png:assets" run.py

mkdir -p "$PKG/DEBIAN" "$PKG/opt/hackmstereo" "$PKG/usr/bin" \
  "$PKG/usr/share/applications" "$PKG/usr/share/pixmaps"
cp -a "$ROOT/dist/hAckMstereo/." "$PKG/opt/hackmstereo/"
install -m 0644 "$ROOT/assets/hackmstereo-icon.png" "$PKG/usr/share/pixmaps/hackmstereo.png"
install -m 0644 "$ROOT/packaging/hackmstereo.desktop" "$PKG/usr/share/applications/hackmstereo.desktop"
cat > "$PKG/usr/bin/hackmstereo" <<'EOF'
#!/bin/sh
exec /opt/hackmstereo/hAckMstereo "$@"
EOF
chmod 0755 "$PKG/usr/bin/hackmstereo"
cat > "$PKG/DEBIAN/control" <<EOF
Package: hackmstereo
Version: ${APP_VERSION}-ubuntu${UBUNTU_VERSION}
Section: hamradio
Priority: optional
Architecture: amd64
Maintainer: Max Epelic
Depends: ffmpeg, libhackrf0, libusb-1.0-0, libportaudio2, libgl1, libegl1, libxkbcommon-x11-0, libxcb-cursor0
Homepage: https://github.com/epelic/hAckMstereo
Description: Bundled AM Stereo C-QUAM transmitter for HackRF
 Includes Python, PySide6, NumPy and sounddevice. System RF, audio and
 FFmpeg libraries are installed through Ubuntu package dependencies.
EOF

dpkg-deb --root-owner-group --build "$PKG" "$DIST/hackmstereo_${APP_VERSION}-ubuntu${UBUNTU_VERSION}_amd64.deb"
dpkg-deb --info "$DIST/hackmstereo_${APP_VERSION}-ubuntu${UBUNTU_VERSION}_amd64.deb"

