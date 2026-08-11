from __future__ import annotations
import subprocess, threading
import numpy as np

class StreamSource:
    def __init__(self, cfg): self.cfg, self.proc = cfg, None
    def open(self):
        cmd = [self.cfg.ffmpeg_path, "-hide_banner", "-loglevel", "quiet", "-reconnect", "1",
               "-reconnect_streamed", "1", "-reconnect_delay_max", "5", "-i", self.cfg.stream_url,
               "-vn", "-ac", "2", "-ar", str(self.cfg.audio_sample_rate), "-f", "f32le", "-acodec", "pcm_f32le", "pipe:1"]
        flags = subprocess.CREATE_NO_WINDOW if hasattr(subprocess, "CREATE_NO_WINDOW") else 0
        self.proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, bufsize=0, creationflags=flags)
    def read(self, frames):
        need, data = frames*8, bytearray()
        while len(data) < need:
            block = self.proc.stdout.read(need-len(data))
            if not block: raise EOFError("Stream disconnected")
            data.extend(block)
        return np.frombuffer(data, np.float32).reshape(-1, 2)
    def close(self):
        if not self.proc: return
        try:
            if self.proc.stdout: self.proc.stdout.close()
            self.proc.terminate(); self.proc.wait(timeout=1)
        except Exception:
            try: self.proc.kill(); self.proc.wait(timeout=1)
            except Exception: pass
        self.proc = None

class TestToneSource:
    def __init__(self, cfg): self.cfg, self.pos = cfg, 0
    def open(self): pass
    def read(self, frames):
        n = np.arange(frames) + self.pos; self.pos += frames
        l = .45*np.sin(2*np.pi*400*n/self.cfg.audio_sample_rate)
        r = .45*np.sin(2*np.pi*1000*n/self.cfg.audio_sample_rate)
        return np.column_stack((l, r)).astype(np.float32)
    def close(self): pass

class LineInputSource:
    def __init__(self, cfg): self.cfg, self.stream = cfg, None
    def open(self):
        try: import sounddevice as sd
        except ImportError as e: raise RuntimeError("Install sounddevice to use Line Input") from e
        self.stream = sd.InputStream(device=self.cfg.audio_device, samplerate=self.cfg.audio_sample_rate,
                                     channels=2, dtype="float32", blocksize=self.cfg.block_frames,
                                     latency="high")
        self.stream.start()
    def read(self, frames):
        data, overflow = self.stream.read(frames)
        return np.asarray(data, dtype=np.float32)
    def close(self):
        if self.stream: self.stream.stop(); self.stream.close(); self.stream = None

def audio_devices():
    try:
        import sounddevice as sd
        return [(i, d['name']) for i, d in enumerate(sd.query_devices()) if d['max_input_channels'] >= 2]
    except Exception: return []
