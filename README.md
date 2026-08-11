# hAckMstereo

Trasmettitore AM Stereo C-QUAM per Windows e HackRF, con interfaccia PySide6. Mantiene la matematica C-QUAM V0.7 verificata: matrice L+R/L-R, pilot 25 Hz, correzione d'inviluppo e uscita diretta libhackrf a 8 Msps.

## Funzioni

- Stream SHOUTcast/HE-AAC tramite FFmpeg, ingresso audio live e toni test stereo
- VU meter L/R, scope audio, buffer e conteggio underrun
- Frequenza, bandwidth, gain audio, modulazione, TX VGA e RF AMP configurabili
- Modalità Mono/C-QUAM, pilot 25 Hz e soft limiter
- Salvataggio configurazione e shutdown pulito di FFmpeg

## Avvio

Da Prompt/PowerShell nella cartella del progetto:

```bat
C:\Users\epeli\radioconda\python.exe run.py
```

Per la sorgente Live installare `sounddevice` (`python -m pip install sounddevice`). FFmpeg deve essere disponibile nel PATH. Il percorso DLL predefinito è quello Radioconda già verificato e può essere modificato nel file di configurazione in `%APPDATA%\CQUAM-TX\config.json`.

## Sicurezza e uso

Collegare HackRF a un carico adatto o a una catena RF conforme. I parametri vengono bloccati durante TX. In questa installazione il comando RF AMP è configurato con polarità invertita: ON invia 0 alla DLL, OFF invia 1. La scelta è salvata come `rf_amp_inverted`.

## EXE

Eseguire `build_exe.bat`. Il risultato è in `dist\hAckMstereo`. FFmpeg e `hackrf-0.dll` restano dipendenze esterne; è preferibile mantenerli nell'ambiente Radioconda già funzionante.
