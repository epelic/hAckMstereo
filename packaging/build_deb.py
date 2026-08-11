from __future__ import annotations
import io, os, stat, tarfile, time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "linux-dist"
VERSION = "1.0.2"

DESKTOP = """[Desktop Entry]
Type=Application
Name=hAckMstereo
Comment=AM Stereo C-QUAM transmitter for HackRF
Comment[it]=Trasmettitore AM Stereo C-QUAM per HackRF
Exec=hackmstereo
Icon=hackmstereo
Terminal=false
Categories=AudioVideo;HamRadio;
Keywords=HackRF;C-QUAM;AM Stereo;SDR;
"""

LAUNCHER = """#!/bin/sh
exec /usr/bin/python3 /usr/lib/hackmstereo/run.py "$@"
"""

def tar_bytes(files: list[tuple[str, bytes, int]]) -> bytes:
    stream = io.BytesIO()
    with tarfile.open(fileobj=stream, mode="w:gz", format=tarfile.GNU_FORMAT) as tf:
        for name, data, mode in files:
            info = tarfile.TarInfo(name); info.size = len(data); info.mode = mode
            info.mtime = int(time.time()); info.uid = info.gid = 0; info.uname = info.gname = "root"
            tf.addfile(info, io.BytesIO(data))
    return stream.getvalue()

def ar_member(name: str, data: bytes) -> bytes:
    header = f"{name + '/':<16}{int(time.time()):<12}{0:<6}{0:<6}{0o100644:<8o}{len(data):<10}`\n".encode("ascii")
    return header + data + (b"\n" if len(data) % 2 else b"")

def build(ubuntu: str, qt_dependency: str) -> Path:
    package_version = f"{VERSION}-ubuntu{ubuntu}"
    control = f"""Package: hackmstereo
Version: {package_version}
Section: hamradio
Priority: optional
Architecture: all
Maintainer: hAckMstereo contributors
Depends: python3, python3-numpy, {qt_dependency}, python3-sounddevice, ffmpeg, libhackrf0
Recommends: hackrf
Homepage: https://github.com/epelic/hAckMstereo
Description: AM Stereo C-QUAM transmitter for HackRF
 hAckMstereo generates receiver-verified C-QUAM I/Q from internet
 streams, stereo line input, or built-in channel test tones.
"""
    control_tgz = tar_bytes([("./control", control.encode(), 0o644)])
    data_files = [("./usr/bin/hackmstereo", LAUNCHER.encode(), 0o755),
                  ("./usr/share/applications/hackmstereo.desktop", DESKTOP.encode(), 0o644),
                  ("./usr/share/pixmaps/hackmstereo.png", (ROOT/"assets"/"hackmstereo-icon.png").read_bytes(), 0o644),
                  ("./usr/share/doc/hackmstereo/README.md", (ROOT/"README.md").read_bytes(), 0o644),
                  ("./usr/lib/hackmstereo/run.py", (ROOT/"run.py").read_bytes(), 0o644)]
    for path in sorted((ROOT/"cquam_tx").glob("*.py")):
        data_files.append((f"./usr/lib/hackmstereo/cquam_tx/{path.name}", path.read_bytes(), 0o644))
    data_tgz = tar_bytes(data_files)
    OUT.mkdir(exist_ok=True)
    target = OUT / f"hackmstereo_{package_version}_all.deb"
    target.write_bytes(b"!<arch>\n" + ar_member("debian-binary", b"2.0\n") + ar_member("control.tar.gz", control_tgz) + ar_member("data.tar.gz", data_tgz))
    return target

if __name__ == "__main__":
    for args in [("24.04", "python3-pyside2.qtwidgets"), ("26.04", "python3-pyside6.qtwidgets")]:
        path = build(*args); print(path, path.stat().st_size)
