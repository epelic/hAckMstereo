@echo off
setlocal
if not exist .build-venv\Scripts\python.exe python -m venv .build-venv
.build-venv\Scripts\python.exe -m pip install -r requirements.txt pyinstaller
.build-venv\Scripts\python.exe -m PyInstaller --noconfirm --clean --windowed --name hAckMstereo --collect-all sounddevice ^
 --icon "assets\hackmstereo.ico" --add-data "assets\hackmstereo-icon.png;assets" ^
 --add-binary "C:\Users\epeli\radioconda\Library\bin\hackrf-0.dll;." ^
 --add-binary "C:\Users\epeli\radioconda\Library\bin\libusb-1.0.dll;." ^
 --add-binary "C:\Users\epeli\radioconda\Library\bin\libwinpthread-1.dll;." ^
 --add-binary "C:\Users\epeli\radioconda\Library\bin\ffmpeg.exe;." run.py
"%LOCALAPPDATA%\Programs\Inno Setup 6\ISCC.exe" installer.iss
echo Installer creato nella cartella outputs.
