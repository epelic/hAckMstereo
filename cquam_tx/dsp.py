from __future__ import annotations
import numpy as np

def make_lowpass(cutoff: float, fs: int, taps: int = 257) -> np.ndarray:
    fc = cutoff / fs
    n = np.arange(taps) - (taps - 1) / 2
    h = 2 * fc * np.sinc(2 * fc * n) * np.hamming(taps)
    return (h / np.sum(h)).astype(np.float64)

class FIRFilter:
    def __init__(self, coefficients):
        self.h = coefficients
        self.state = np.zeros(len(coefficients) - 1, dtype=np.float64)
    def process(self, x):
        extended = np.concatenate((self.state, x))
        y = np.convolve(extended, self.h, mode="valid")
        self.state = extended[-(len(self.h) - 1):]
        return y

def soft_limiter(x, drive=1.35):
    norm = np.tanh(drive)
    return np.tanh(x * drive) / norm if norm else x

def interpolate_block(x, previous, factor):
    if previous is None: previous = x[0]
    src = np.concatenate(([previous], x))
    positions = np.arange(len(x) * factor, dtype=np.float64) / factor
    return np.interp(positions, np.arange(len(src)), src), x[-1]

class CquamProcessor:
    """The verified V0.7 C-QUAM equations, isolated from UI and I/O."""
    def __init__(self, cfg):
        self.cfg = cfg
        fir = make_lowpass(cfg.audio_bw_hz, cfg.audio_sample_rate)
        self.left_filter, self.right_filter = FIRFilter(fir), FIRFilter(fir)
        self.prev_i = self.prev_q = None
        self.pilot_sample = 0
        self.factor = cfg.rf_sample_rate // cfg.audio_sample_rate

    def process(self, stereo):
        c = self.cfg
        left = stereo[:, 0].astype(np.float64) * c.input_gain
        right = stereo[:, 1].astype(np.float64) * c.input_gain
        vu = (float(np.sqrt(np.mean(left*left))), float(np.sqrt(np.mean(right*right))))
        if c.limiter_enabled:
            left, right = soft_limiter(left, c.limiter_drive), soft_limiter(right, c.limiter_drive)
        left = self.left_filter.process(np.clip(left, -1, 1))
        right = self.right_filter.process(np.clip(right, -1, 1))
        if c.mode == "Mono": right = left
        sum_audio = (left + right) * .5
        diff_audio = (left - right) * .5
        s = c.modulation * sum_audio
        d = c.modulation * diff_audio
        frames = len(stereo)
        if c.mode == "C-QUAM" and c.pilot_enabled:
            n = np.arange(frames, dtype=np.float64) + self.pilot_sample
            d += c.pilot_level * np.sin(2*np.pi*25*n/c.audio_sample_rate)
        self.pilot_sample = (self.pilot_sample + frames) % (c.audio_sample_rate * 100)
        raw_i, raw_q = 1.0 + s, d
        phase = np.arctan2(raw_q, raw_i)
        envelope = 1.0 + s
        i, q = envelope*np.cos(phase), envelope*np.sin(phase)
        i, self.prev_i = interpolate_block(i, self.prev_i, self.factor)
        q, self.prev_q = interpolate_block(q, self.prev_q, self.factor)
        scale = c.output_peak / (1.0 + c.modulation)
        i8 = np.clip(np.round(i*scale*127), -127, 127).astype(np.int8)
        q8 = np.clip(np.round(q*scale*127), -127, 127).astype(np.int8)
        out = np.empty(len(i8)*2, dtype=np.int8); out[0::2] = i8; out[1::2] = q8
        scope = np.asarray(sum_audio[::max(1, frames//256)], dtype=np.float32)
        return out.tobytes(), vu, scope

