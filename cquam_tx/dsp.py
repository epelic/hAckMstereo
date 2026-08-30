from __future__ import annotations
import numpy as np

EQ_FREQUENCIES = (50, 250, 500, 1000, 2500, 5000, 7500, 10000, 12500, 15000)

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

def make_equalizer(gains_db, fs: int, taps: int = 513) -> np.ndarray:
    """Build one linear-phase FIR from the ten fixed graphic-EQ bands."""
    nfft = 2048
    bins = np.fft.rfftfreq(nfft, 1.0/fs)
    anchors = np.asarray((0, *EQ_FREQUENCIES, fs/2), dtype=np.float64)
    gains = np.asarray((gains_db[0], *gains_db, gains_db[-1]), dtype=np.float64)
    db = np.interp(bins, anchors, gains)
    impulse = np.fft.fftshift(np.fft.irfft(10.0**(db/20.0), nfft))
    center = nfft//2; half = taps//2
    return (impulse[center-half:center+half+1] * np.hamming(taps)).astype(np.float64)

def soft_limiter(x, drive=1.35):
    norm = np.tanh(drive)
    return np.tanh(x * drive) / norm if norm else x

class NrscPreEmphasis:
    """Modified 75 us AM pre-emphasis: 2122 Hz zero, 8700 Hz pole."""
    def __init__(self, fs):
        k=2.0*fs; tau_zero=75e-6; tau_pole=1.0/(2.0*np.pi*8700.0)
        a0=1.0+k*tau_pole
        self.b0=(1.0+k*tau_zero)/a0; self.b1=(1.0-k*tau_zero)/a0
        self.a1=(1.0-k*tau_pole)/a0; self.x1=0.0; self.y1=0.0
    def process(self,x):
        y=np.empty_like(x,dtype=np.float64); x1,y1=self.x1,self.y1
        for i,v in enumerate(x):
            out=self.b0*v+self.b1*x1-self.a1*y1; y[i]=out; x1,y1=v,out
        self.x1,self.y1=x1,y1; return y

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
        eq = make_equalizer(cfg.eq_gains_db, cfg.audio_sample_rate)
        self.left_eq, self.right_eq = FIRFilter(eq), FIRFilter(eq)
        self.input_gain = float(cfg.input_gain)
        self.eq_gains_db = tuple(float(v) for v in cfg.eq_gains_db)
        self.pending_eq_gains_db = self.eq_gains_db
        self.left_pre, self.right_pre = NrscPreEmphasis(cfg.audio_sample_rate), NrscPreEmphasis(cfg.audio_sample_rate)
        self.prev_i = self.prev_q = None
        self.pilot_sample = 0
        self.factor = cfg.rf_sample_rate // cfg.audio_sample_rate

    def set_audio_processing(self, input_gain, eq_gains_db):
        """Called by the UI; scalar/tuple assignment is atomic in CPython."""
        self.input_gain = max(0.0, min(4.0, float(input_gain)))
        values = tuple(max(-12.0, min(12.0, float(v))) for v in eq_gains_db)
        if len(values) != len(EQ_FREQUENCIES):
            raise ValueError("The equalizer requires ten bands")
        self.pending_eq_gains_db = values

    def process(self, stereo):
        c = self.cfg
        left = stereo[:, 0].astype(np.float64)
        right = stereo[:, 1].astype(np.float64)
        pending = self.pending_eq_gains_db
        if pending != self.eq_gains_db:
            coefficients = make_equalizer(pending, c.audio_sample_rate)
            self.left_eq.h = coefficients
            self.right_eq.h = coefficients
            self.eq_gains_db = pending
        left, right = self.left_eq.process(left), self.right_eq.process(right)
        gain = self.input_gain
        left, right = left * gain, right * gain
        vu = (float(np.sqrt(np.mean(left*left))), float(np.sqrt(np.mean(right*right))))
        if c.preemphasis_enabled:
            left, right = self.left_pre.process(left), self.right_pre.process(right)
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
