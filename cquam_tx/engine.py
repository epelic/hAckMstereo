from __future__ import annotations
import threading,time
from .dsp import CquamProcessor
from .hackrf import HackRFDevice
from .sources import StreamSource,LineInputSource,TestToneSource

class IQBuffer:
    def __init__(self,rate,max_seconds=.55):self.data,self.lock=bytearray(),threading.Lock();self.rate,self.limit,self.underruns=rate,int(rate*2*max_seconds),0
    def put(self,data,stop):
        while not stop.is_set():
            with self.lock:
                if len(self.data)+len(data)<=self.limit:self.data.extend(data);return
            time.sleep(.003)
    def take(self,size):
        with self.lock:
            n=min(size,len(self.data));out=bytes(self.data[:n]);del self.data[:n]
            if n<size:self.underruns+=1;out+=bytes(size-n)
            return out
    @property
    def seconds(self):
        with self.lock:return len(self.data)/(2*self.rate)

class TxEngine:
    def __init__(self,event_callback=lambda *_:None):
        self.event=event_callback;self.stop_event=threading.Event();self.worker=None;self.buffer=self.device=self.source=None;self.running=False;self.vu=(0.,0.);self.scope=[]
    def start(self,cfg):
        if self.running:return
        cfg.validate();self.stop_event.clear();self.buffer=IQBuffer(cfg.rf_sample_rate);sources={"Stream":StreamSource,"Live":LineInputSource,"Test tones":TestToneSource}
        self.source=sources[cfg.source](cfg);self.event("stream","Connecting...");self.source.open();self.event("stream","OK")
        processor=CquamProcessor(cfg);self.device=HackRFDevice(cfg,self.buffer);self.device.open();self.event("hackrf","Ready")
        self.worker=threading.Thread(target=self._produce,args=(cfg,processor),daemon=True);self.worker.start();deadline=time.monotonic()+4
        while self.buffer.seconds<.35 and self.worker.is_alive() and time.monotonic()<deadline:time.sleep(.02)
        self.device.start();self.running=True;self.event("log","C-QUAM TX ON AIR")
    def _produce(self,cfg,processor):
        try:
            while not self.stop_event.is_set():
                stereo=self.source.read(cfg.block_frames);block,self.vu,self.scope=processor.process(stereo);self.buffer.put(block,self.stop_event)
        except Exception as e:
            if not self.stop_event.is_set():self.event("error",str(e))
            self.stop_event.set()
    def stop(self):
        self.stop_event.set()
        if self.source:self.source.close()
        if self.worker and self.worker.is_alive():self.worker.join(timeout=2)
        if self.device:self.device.close()
        self.running=False;self.event("stream","Stopped");self.event("hackrf","Disconnected");self.event("log","TX stopped")
    def status(self):return {"running":self.running,"buffer":self.buffer.seconds if self.buffer else 0,"underruns":self.buffer.underruns if self.buffer else 0,"vu":self.vu,"scope":self.scope}
