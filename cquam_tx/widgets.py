from __future__ import annotations
import math
from .qt import Qt, QColor, QPainter, QPen, QWidget

class VuMeter(QWidget):
    def __init__(self, label, parent=None):
        super().__init__(parent); self.label, self.level, self.peak = label, -60., -60.; self.setMinimumSize(58, 210)
    def set_rms(self, rms):
        db = max(-60., min(3., 20*math.log10(max(rms, 1e-5))))
        self.level += (db-self.level)*(.65 if db > self.level else .18)
        self.peak = max(db, self.peak-.45); self.update()
    def paintEvent(self, event):
        p = QPainter(self); p.setRenderHint(QPainter.Antialiasing)
        r = self.rect().adjusted(19, 22, -13, -24); p.fillRect(r, QColor("#10161c"))
        segments, gap = 24, 2
        active = int((self.level+60)/63*segments)
        for n in range(segments):
            y = r.bottom()-(n+1)*r.height()/segments; h = r.height()/segments-gap
            ratio = n/segments; color = QColor("#26a269" if ratio < .72 else "#f6c343" if ratio < .9 else "#e74c3c")
            if n >= active: color.setAlpha(42)
            p.fillRect(r.x()+2, int(y)+1, r.width()-4, max(1, int(h)), color)
        py = r.bottom()-int((self.peak+60)/63*r.height()); p.setPen(QPen(QColor("white"), 2)); p.drawLine(r.left(), py, r.right(), py)
        p.setPen(QColor("#dfe7ef")); p.drawText(self.rect().adjusted(0,2,0,0), Qt.AlignTop|Qt.AlignHCenter, self.label)
        p.drawText(self.rect().adjusted(0,0,0,-3), Qt.AlignBottom|Qt.AlignHCenter, f"{self.level:.0f} dB")

class ScopeWidget(QWidget):
    def __init__(self, parent=None): super().__init__(parent); self.samples=[]; self.setMinimumHeight(85)
    def set_samples(self, samples): self.samples = list(samples); self.update()
    def paintEvent(self, event):
        p=QPainter(self); p.fillRect(self.rect(), QColor("#10161c")); p.setPen(QPen(QColor("#22313e"),1)); p.drawLine(0,self.height()//2,self.width(),self.height()//2)
        if len(self.samples)<2:return
        p.setPen(QPen(QColor("#38a6ff"),1.4)); mid=self.height()/2; scale=self.height()*.42
        last=(0, mid-self.samples[0]*scale)
        for i,v in enumerate(self.samples[1:],1):
            cur=(i*self.width()/(len(self.samples)-1), mid-v*scale); p.drawLine(int(last[0]),int(last[1]),int(cur[0]),int(cur[1])); last=cur
