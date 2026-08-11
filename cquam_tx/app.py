from __future__ import annotations
import sys, traceback
from pathlib import Path
from .qt import (QTimer, Signal, QObject, Qt, QIcon, QApplication, QCheckBox, QComboBox, QDoubleSpinBox,
 QFormLayout, QGridLayout, QGroupBox, QHBoxLayout, QLabel, QLineEdit, QMainWindow, QMessageBox,
 QPushButton, QSpinBox, QPlainTextEdit, QVBoxLayout, QWidget)
from .config import TxConfig
from .engine import TxEngine
from .sources import audio_devices
from .widgets import VuMeter, ScopeWidget

STYLE = """
QWidget{background:#20262d;color:#e8edf2;font:10pt 'Segoe UI'} QMainWindow{background:#171c21}
QGroupBox{font-weight:600;border:1px solid #3a4652;border-radius:4px;margin-top:12px;padding:12px 9px 9px}
QGroupBox::title{subcontrol-origin:margin;left:10px;padding:0 5px;color:#9bcfff}
QLineEdit,QComboBox,QSpinBox,QDoubleSpinBox,QPlainTextEdit{background:#12181e;border:1px solid #465461;border-radius:3px;padding:5px;selection-background-color:#0078d4}
QLineEdit:focus,QComboBox:focus,QSpinBox:focus,QDoubleSpinBox:focus{border-color:#38a6ff}
QPushButton{background:#34414d;border:1px solid #526170;border-radius:3px;padding:7px 14px} QPushButton:hover{background:#40505e}
QPushButton#start{background:#0078d4;border-color:#1590ec;font-weight:600} QPushButton#start:hover{background:#1686d9}
QPushButton#stop{background:#a62b2b;border-color:#d44} QPushButton:disabled{color:#7b8791;background:#2a3138}
QCheckBox::indicator{width:34px;height:17px;border-radius:8px;background:#59636d} QCheckBox::indicator:checked{background:#0078d4}
QLabel#hero{font-size:18pt;font-weight:600;color:white} QLabel#onair{padding:7px;border-radius:3px;background:#37414a;font-weight:700}
"""

class Bridge(QObject): event = Signal(str, str)

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__(); self.setWindowTitle("hAckMstereo"); self.resize(1030,720)
        icon_base=Path(getattr(sys,"_MEIPASS",Path(__file__).resolve().parents[1])); icon_path=icon_base/"assets"/"hackmstereo-icon.png"
        if icon_path.exists(): self.setWindowIcon(QIcon(str(icon_path)))
        try:self.cfg=TxConfig.load()
        except Exception:self.cfg=TxConfig()
        self.bridge=Bridge();self.bridge.event.connect(self.on_event);self.engine=TxEngine(lambda a,b:self.bridge.event.emit(a,b))
        self.build();self.to_ui(self.cfg);self.timer=QTimer(self);self.timer.timeout.connect(self.refresh);self.timer.start(80)
    def spin(self,lo,hi,step=1,decimals=0,suffix=""):
        w=QDoubleSpinBox() if decimals else QSpinBox();w.setRange(lo,hi);w.setSingleStep(step);w.setSuffix(suffix)
        if decimals:w.setDecimals(decimals)
        return w
    def build(self):
        root=QWidget();self.setCentralWidget(root);outer=QVBoxLayout(root)
        head=QHBoxLayout();title=QLabel("hAckMstereo");title.setObjectName("hero");head.addWidget(title);head.addStretch();self.onair=QLabel("● OFF AIR");self.onair.setObjectName("onair");head.addWidget(self.onair);outer.addLayout(head)
        body=QHBoxLayout();outer.addLayout(body,1);controls=QWidget();grid=QGridLayout(controls);body.addWidget(controls,4)
        source=QGroupBox("AUDIO SOURCE");sf=QFormLayout(source);self.source=QComboBox();self.source.addItems(["Stream","Live","Test tones"]);self.source.currentTextChanged.connect(self.source_changed)
        self.url=QLineEdit();self.url.setPlaceholderText("http://server:port/stream");self.device=QComboBox();self.reload_devices();sf.addRow("Source",self.source);sf.addRow("Stream URL",self.url);sf.addRow("Live device",self.device);grid.addWidget(source,0,0,1,2)
        audio=QGroupBox("AUDIO AND MODULATION");af=QFormLayout(audio);self.input_gain=self.spin(0,4,.05,2," ×");self.mod=self.spin(0,95,1,0," %");self.bw=QComboBox();self.bw.setEditable(True);self.bw.addItems(["4.5","6","8","10","12","15"])
        self.limiter=QCheckBox(" Enabled");self.drive=self.spin(1,3,.05,2," ×");self.mode=QComboBox();self.mode.addItems(["C-QUAM","Mono"])
        for label,w in [("Audio gain",self.input_gain),("Modulation",self.mod),("Bandwidth (kHz)",self.bw),("Soft limiter",self.limiter),("Limiter drive",self.drive),("Mode",self.mode)]:af.addRow(label,w)
        grid.addWidget(audio,1,0)
        rf=QGroupBox("TRANSMITTER");rf_f=QFormLayout(rf);self.freq=self.spin(.1,6000,.001,3," MHz");self.txgain=self.spin(0,47,1,0," dB");self.amp=QCheckBox(" RF AMP ON");self.pilot=QCheckBox(" Stereo pilot ON");self.pilot_level=self.spin(0,10,.1,1," %")
        for label,w in [("Frequency",self.freq),("TX VGA gain",self.txgain),("RF amplifier",self.amp),("25 Hz pilot",self.pilot),("Pilot level",self.pilot_level)]:rf_f.addRow(label,w)
        grid.addWidget(rf,1,1)
        action=QHBoxLayout();self.start=QPushButton("▶  START TX");self.start.setObjectName("start");self.stop=QPushButton("■  STOP TX");self.stop.setObjectName("stop");self.stop.setEnabled(False);info=QPushButton("INFO");save=QPushButton("Save configuration")
        self.start.clicked.connect(self.start_tx);self.stop.clicked.connect(self.stop_tx);info.clicked.connect(self.show_info);save.clicked.connect(self.save_config);action.addWidget(self.start);action.addWidget(self.stop);action.addStretch();action.addWidget(info);action.addWidget(save);grid.addLayout(action,2,0,1,2)
        status=QGroupBox("STATUS");sg=QGridLayout(status);self.hackrf=QLabel("Disconnected");self.stream=QLabel("Stopped");self.buffer=QLabel("0.000 s");self.underruns=QLabel("0");self.stereo=QLabel("○ STEREO PILOT")
        for row,(label,w) in enumerate([("HackRF",self.hackrf),("Source",self.stream),("Buffer",self.buffer),("Underruns",self.underruns)]):sg.addWidget(QLabel(label),row,0);sg.addWidget(w,row,1)
        sg.addWidget(self.stereo,0,2,2,1);grid.addWidget(status,3,0,1,2);self.log=QPlainTextEdit();self.log.setReadOnly(True);self.log.setMaximumBlockCount(400);grid.addWidget(self.log,4,0,1,2)
        meters=QGroupBox("AUDIO MONITOR");mv=QVBoxLayout(meters);mh=QHBoxLayout();self.vul=VuMeter("LEFT");self.vur=VuMeter("RIGHT");mh.addStretch();mh.addWidget(self.vul);mh.addWidget(self.vur);mh.addStretch();mv.addLayout(mh);self.scope=ScopeWidget();mv.addWidget(self.scope);body.addWidget(meters,1)
    def reload_devices(self):
        self.device.clear();self.device.addItem("Default",None)
        for idx,name in audio_devices():self.device.addItem(name,idx)
    def source_changed(self,text):self.url.setVisible(text=="Stream");self.device.setVisible(text=="Live")
    def to_ui(self,c):
        self.source.setCurrentText("Stream" if c.source=="Stream URL" else c.source);self.url.setText(c.stream_url);self.freq.setValue(c.frequency_hz/1e6);self.bw.setCurrentText(f"{c.audio_bw_hz/1000:g}");self.input_gain.setValue(c.input_gain);self.mod.setValue(c.modulation*100);self.limiter.setChecked(c.limiter_enabled);self.drive.setValue(c.limiter_drive);self.pilot.setChecked(c.pilot_enabled);self.pilot_level.setValue(c.pilot_level*100);self.txgain.setValue(c.tx_vga);self.amp.setChecked(c.rf_amp);self.mode.setCurrentText(c.mode);self.source_changed(self.source.currentText())
    def from_ui(self):
        c=TxConfig.load();c.source=self.source.currentText();c.stream_url=self.url.text().strip();c.audio_device=self.device.currentData();c.frequency_hz=int(self.freq.value()*1e6);c.audio_bw_hz=float(self.bw.currentText().replace(',','.'))*1000;c.input_gain=self.input_gain.value();c.modulation=self.mod.value()/100;c.limiter_enabled=self.limiter.isChecked();c.limiter_drive=self.drive.value();c.pilot_enabled=self.pilot.isChecked();c.pilot_level=self.pilot_level.value()/100;c.tx_vga=self.txgain.value();c.rf_amp=self.amp.isChecked();c.mode=self.mode.currentText();c.validate();return c
    def set_locked(self,running):
        self.start.setEnabled(not running);self.stop.setEnabled(running)
        for w in [self.source,self.url,self.device,self.freq,self.bw,self.input_gain,self.mod,self.limiter,self.drive,self.pilot,self.pilot_level,self.txgain,self.amp,self.mode]:w.setEnabled(not running)
    def start_tx(self):
        try:self.cfg=self.from_ui();self.cfg.save();self.log.appendPlainText("Starting transmitter…");self.engine.start(self.cfg);self.set_locked(True);self.onair.setText("● ON AIR");self.onair.setStyleSheet("background:#a4262c;color:white")
        except Exception as e:self.engine.stop();QMessageBox.critical(self,"TX start",str(e));self.log.appendPlainText(traceback.format_exc())
    def stop_tx(self):self.engine.stop();self.set_locked(False);self.onair.setText("● OFF AIR");self.onair.setStyleSheet("")
    def save_config(self):
        try:self.cfg=self.from_ui();self.cfg.save();self.log.appendPlainText("Configuration saved.")
        except Exception as e:QMessageBox.warning(self,"Configuration",str(e))
    def show_info(self):
        box=QMessageBox(self);box.setWindowTitle("About hAckMstereo");box.setIcon(QMessageBox.Information);box.setTextFormat(Qt.RichText);box.setTextInteractionFlags(Qt.TextBrowserInteraction);box.setText('hAckMstereo V.1.0.2&nbsp; by Max Epelic<br><a href="http://www.freewaves.it">http://www.freewaves.it</a>');box.exec() if hasattr(box,"exec") else box.exec_()
    def on_event(self,kind,text):
        if kind=="hackrf":self.hackrf.setText(text)
        elif kind=="stream":self.stream.setText(text)
        else:self.log.appendPlainText(text)
        if kind=="error":QMessageBox.critical(self,"TX error",text);self.stop_tx()
    def refresh(self):
        s=self.engine.status();self.buffer.setText(f"{s['buffer']:.3f} s");self.underruns.setText(str(s['underruns']));self.vul.set_rms(s['vu'][0]);self.vur.set_rms(s['vu'][1]);self.scope.set_samples(s['scope']);active=s['running'] and self.mode.currentText()=="C-QUAM" and self.pilot.isChecked();self.stereo.setText("● STEREO PILOT" if active else "○ STEREO PILOT");self.stereo.setStyleSheet("color:#35d07f;font-weight:700" if active else "color:#84919c")
    def closeEvent(self,event):self.engine.stop();event.accept()

def main():
    app=QApplication(sys.argv);app.setStyle("Fusion");app.setStyleSheet(STYLE);w=MainWindow();w.show();return app.exec() if hasattr(app,"exec") else app.exec_()
