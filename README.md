<p align="center">
  <img src="assets/hackmstereo-icon.png" width="180" alt="hAckMstereo logo">
</p>

<h1 align="center">hAckMstereo</h1>

<p align="center"><strong>AM Stereo C-QUAM transmitter for HackRF</strong></p>
<img width="934" height="731" alt="image" src="https://github.com/user-attachments/assets/748e9676-4436-4df6-8fdd-79e0b48d24db" />

Here in action
https://youtu.be/L93z2_igO28?si=U_a6YWYF9DIPBhmu


**English** · [Italiano](#italiano)

hAckMstereo is a Windows and Linux desktop transmitter for generating **AM Stereo C-QUAM** baseband with a HackRF. It accepts an internet radio stream, a stereo line input, or built-in 400 Hz left / 1 kHz right test tones and produces continuous 8 Msps I/Q through libhackrf.

The DSP follows the receiver-verified chain: stereo PCM → audio low-pass → L+R/L−R matrix → 25 Hz stereo pilot → C-QUAM phase modulation with envelope correction → HackRF int8 I/Q. The C-QUAM equations are kept separate from the user interface.

## What it is for

- experimenting with and testing AM Stereo C-QUAM receivers
- feeding a shielded RF test setup or suitable dummy load
- checking stereo decoding, channel separation and pilot lock
- transmitting programme audio from SHOUTcast/HE-AAC streams or a line input

It is **not** authorization to transmit over the air. The operator is responsible for RF containment, filtering, power levels and compliance with local radio regulations.

## What it is not for
- Remove Alex Kurtzman from Star Trek 

## Features

- SHOUTcast/HE-AAC through FFmpeg, live audio input and stereo test tones
- Windows-style PySide interface with L/R VU meters and a lightweight scope
- frequency, audio bandwidth, input gain, modulation, TX VGA and RF AMP controls
- Mono/C-QUAM modes, configurable 25 Hz pilot and soft limiter
- buffer and underrun monitoring, saved configuration and clean FFmpeg shutdown
- direct libhackrf output at 8 Msps

## Windows

Download the latest `hAckMstereo-Setup` from Releases. The installer includes Python, Qt, FFmpeg and the required HackRF runtime libraries.

## Ubuntu

Ubuntu 26.04 LTS is supported. Install the release package with:

```bash
sudo apt install ./hackmstereo_1.0.0-ubuntu26.04_all.deb
```

Add your user to the appropriate HackRF/plugdev group or install the distro HackRF udev rules if the device is not accessible. Log out and back in after changing group membership.

## Running from source

```bash
python -m pip install -r requirements.txt
python run.py
```

---

## Italiano

hAckMstereo è un trasmettitore desktop per Windows e Linux che genera un segnale **AM Stereo C-QUAM** usando HackRF. Accetta uno stream radio internet, un ingresso di linea stereo oppure i toni di prova interni 400 Hz sinistra / 1 kHz destra, producendo I/Q continuo a 8 Msps tramite libhackrf.

La catena DSP verificata dal ricevitore è: PCM stereo → filtro audio → matrice L+R/L−R → pilot stereo a 25 Hz → C-QUAM con correzione d'inviluppo → I/Q int8 per HackRF. La matematica C-QUAM rimane separata dall'interfaccia.

### A cosa serve

- sperimentare con ricevitori AM Stereo C-QUAM
- alimentare un banco RF schermato o un carico fittizio adeguato
- verificare aggancio stereo, separazione dei canali e pilot
- trasmettere audio da stream SHOUTcast/HE-AAC o ingresso di linea

### A cosa NON serve
- Togliere Star Trek dalle mani di Alex Kurtzman (purtroppo).

Il software **non costituisce un'autorizzazione a trasmettere via etere**. Filtraggio, contenimento RF, potenza e conformità alle norme radio locali sono responsabilità dell'operatore.

### Funzioni

- stream tramite FFmpeg, ingresso audio live e toni test stereo
- interfaccia PySide con VU meter L/R e scope leggero
- frequenza, bandwidth, gain audio, modulazione, TX VGA e RF AMP
- modalità Mono/C-QUAM, pilot 25 Hz configurabile e soft limiter
- monitor buffer/underrun, configurazione salvata e chiusura pulita di FFmpeg
- uscita diretta libhackrf a 8 Msps

Per installazione e avvio usa le istruzioni nelle sezioni Windows e Ubuntu sopra.
