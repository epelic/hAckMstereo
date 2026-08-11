from __future__ import annotations
from dataclasses import asdict, dataclass
import json
from pathlib import Path
import sys
import os, shutil, ctypes.util

def bundled_file(name: str, fallback: str) -> str:
    base = Path(getattr(sys, "_MEIPASS", Path(sys.executable).parent))
    candidate = base / name
    return str(candidate if candidate.exists() else Path(fallback))

def default_hackrf() -> str:
    if sys.platform == "win32": return bundled_file("hackrf-0.dll", r"C:\Users\epeli\radioconda\Library\bin\hackrf-0.dll")
    return ctypes.util.find_library("hackrf") or "libhackrf.so.0"

def default_ffmpeg() -> str:
    if sys.platform == "win32": return bundled_file("ffmpeg.exe", "ffmpeg")
    return shutil.which("ffmpeg") or "/usr/bin/ffmpeg"

APP_DIR = (Path(os.environ.get("APPDATA", Path.home()/"AppData"/"Roaming")) / "hAckMstereo") if sys.platform == "win32" else Path(os.environ.get("XDG_CONFIG_HOME", Path.home()/".config")) / "hackmstereo"
CONFIG_FILE = APP_DIR / "config.json"

@dataclass
class TxConfig:
    source: str = "Stream URL"
    stream_url: str = "http://dreamsiteradiocp3.com:8000"
    audio_device: int | None = None
    frequency_hz: int = 9_000_000
    audio_bw_hz: float = 10_000.0
    input_gain: float = 0.90
    modulation: float = 0.85
    limiter_enabled: bool = True
    limiter_drive: float = 1.35
    pilot_enabled: bool = True
    pilot_level: float = 0.04
    tx_vga: int = 47
    rf_amp: bool = True
    rf_amp_inverted: bool = True
    mode: str = "C-QUAM"
    dll_path: str = default_hackrf()
    ffmpeg_path: str = default_ffmpeg()
    rf_sample_rate: int = 8_000_000
    audio_sample_rate: int = 100_000
    block_frames: int = 5000
    output_peak: float = 0.70

    def validate(self) -> None:
        if not 100_000 <= self.frequency_hz <= 6_000_000_000: raise ValueError("Frequenza fuori intervallo")
        if not 1_000 <= self.audio_bw_hz <= 12_000: raise ValueError("Audio BW: 1–12 kHz")
        if not 0 <= self.input_gain <= 4: raise ValueError("Input gain: 0–4")
        if not 0 <= self.modulation <= 0.95: raise ValueError("Modulazione massima 95%")
        if not 0 <= self.pilot_level <= 0.10: raise ValueError("Pilot massimo 10%")
        if not 0 <= self.tx_vga <= 47: raise ValueError("TX VGA: 0–47 dB")
        if self.rf_sample_rate % self.audio_sample_rate: raise ValueError("RF sample rate deve essere multiplo dell'audio")

    def save(self, path: Path = CONFIG_FILE) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(asdict(self), indent=2), encoding="utf-8")

    @classmethod
    def load(cls, path: Path = CONFIG_FILE) -> "TxConfig":
        if not path.exists(): return cls()
        raw = json.loads(path.read_text(encoding="utf-8"))
        return cls(**{k: v for k, v in raw.items() if k in cls.__dataclass_fields__})
