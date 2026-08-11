import numpy as np
from cquam_tx.config import TxConfig
from cquam_tx.dsp import CquamProcessor, soft_limiter

def test_block_size_and_range():
    c=TxConfig(block_frames=100); p=CquamProcessor(c); x=np.zeros((100,2),np.float32)
    raw,vu,scope=p.process(x)
    assert len(raw)==100*(c.rf_sample_rate//c.audio_sample_rate)*2
    assert np.frombuffer(raw,np.int8).max()<=127

def test_limiter_is_bounded():
    y=soft_limiter(np.array([-10.,0.,10.]),1.35)
    assert np.max(np.abs(y)) <= 1/np.tanh(1.35)+1e-9

def test_tones_keep_stereo_difference():
    c=TxConfig(block_frames=1000); p=CquamProcessor(c); n=np.arange(1000)
    x=np.column_stack((.3*np.sin(2*np.pi*400*n/c.audio_sample_rate),.3*np.sin(2*np.pi*1000*n/c.audio_sample_rate))).astype(np.float32)
    raw,vu,_=p.process(x); iq=np.frombuffer(raw,np.int8).reshape(-1,2)
    assert vu[0]>0 and vu[1]>0 and np.std(iq[:,1])>0

