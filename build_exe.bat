@echo off
setlocal
python -m pip install -r requirements.txt pyinstaller
python -m PyInstaller --noconfirm --clean --windowed --name hAckMstereo --collect-all sounddevice ^
 --add-binary "C:\Users\epeli\radioconda\Library\bin\hackrf-0.dll;." ^
 --add-binary "C:\Users\epeli\radioconda\Library\bin\libusb-1.0.dll;." ^
 --add-binary "C:\Users\epeli\radioconda\Library\bin\libwinpthread-1.dll;." ^
 --add-binary "C:\Users\epeli\radioconda\Library\bin\ffmpeg.exe;." run.py
"%LOCALAPPDATA%\Programs\Inno Setup 6\ISCC.exe" installer.iss
echo Installer creato nella cartella outputs.
