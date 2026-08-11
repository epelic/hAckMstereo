from __future__ import annotations
import ctypes

class HackRFTransfer(ctypes.Structure):
    _fields_ = [("device", ctypes.c_void_p), ("buffer", ctypes.POINTER(ctypes.c_uint8)),
                ("buffer_length", ctypes.c_int), ("valid_length", ctypes.c_int),
                ("rx_ctx", ctypes.c_void_p), ("tx_ctx", ctypes.c_void_p)]
TX_CALLBACK = ctypes.CFUNCTYPE(ctypes.c_int, ctypes.POINTER(HackRFTransfer))

class HackRFDevice:
    def __init__(self, cfg, buffer):
        self.cfg, self.buffer = cfg, buffer
        self.lib = self.device = self.callback = None
    @staticmethod
    def _check(code, name):
        if code != 0: raise RuntimeError(f"{name} failed (code {code})")
    def open(self):
        self.lib = ctypes.CDLL(self.cfg.dll_path)
        l = self.lib
        l.hackrf_init.restype = l.hackrf_exit.restype = ctypes.c_int
        l.hackrf_open.argtypes = [ctypes.POINTER(ctypes.c_void_p)]; l.hackrf_open.restype = ctypes.c_int
        l.hackrf_close.argtypes = [ctypes.c_void_p]; l.hackrf_close.restype = ctypes.c_int
        l.hackrf_set_freq.argtypes = [ctypes.c_void_p, ctypes.c_uint64]; l.hackrf_set_freq.restype = ctypes.c_int
        l.hackrf_set_sample_rate.argtypes = [ctypes.c_void_p, ctypes.c_double]; l.hackrf_set_sample_rate.restype = ctypes.c_int
        l.hackrf_set_txvga_gain.argtypes = [ctypes.c_void_p, ctypes.c_uint32]; l.hackrf_set_txvga_gain.restype = ctypes.c_int
        l.hackrf_set_amp_enable.argtypes = [ctypes.c_void_p, ctypes.c_uint8]; l.hackrf_set_amp_enable.restype = ctypes.c_int
        l.hackrf_start_tx.argtypes = [ctypes.c_void_p, TX_CALLBACK, ctypes.c_void_p]; l.hackrf_start_tx.restype = ctypes.c_int
        l.hackrf_stop_tx.argtypes = [ctypes.c_void_p]; l.hackrf_stop_tx.restype = ctypes.c_int
        self._check(l.hackrf_init(), "hackrf_init")
        self.device = ctypes.c_void_p(); self._check(l.hackrf_open(ctypes.byref(self.device)), "hackrf_open")
        self._check(l.hackrf_set_sample_rate(self.device, float(self.cfg.rf_sample_rate)), "sample rate")
        self._check(l.hackrf_set_freq(self.device, self.cfg.frequency_hz), "frequency")
        self._check(l.hackrf_set_txvga_gain(self.device, self.cfg.tx_vga), "TX VGA")
        amp_value = int(not self.cfg.rf_amp) if self.cfg.rf_amp_inverted else int(self.cfg.rf_amp)
        self._check(l.hackrf_set_amp_enable(self.device, amp_value), "RF AMP")
    def start(self):
        @TX_CALLBACK
        def callback(ptr):
            transfer = ptr.contents; data = self.buffer.take(transfer.buffer_length)
            ctypes.memmove(transfer.buffer, data, transfer.buffer_length)
            transfer.valid_length = transfer.buffer_length
            return 0
        self.callback = callback
        self._check(self.lib.hackrf_start_tx(self.device, self.callback, None), "TX start")
    def close(self):
        if not self.lib: return
        if self.device:
            try: self.lib.hackrf_stop_tx(self.device)
            except Exception: pass
            try: self.lib.hackrf_close(self.device)
            except Exception: pass
        try: self.lib.hackrf_exit()
        except Exception: pass
        self.device = self.lib = self.callback = None
