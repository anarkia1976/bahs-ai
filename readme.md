# 🏀 BAHS-AI — Basketball Automation Highlights Suite

Suite Python automatizzata per la preparazione, il taglio, la conversione, il montaggio, la sonorizzazione, l'aggiunta di testi animati e l'inserimento del logo proporzionale per video **1080P (16:9)** e **REEL (9:16)** basata su **FFmpeg**, **FFprobe** e **YOLO / Computer Vision**.

---

## 📋 Panoramica del Workflow

Il launcher centrale **`01_BAHS_main-ALL.py`** coordina l'ambiente, esegue i controlli iniziali, gestisce la pulizia delle cartelle di lavoro (`1`), avvia i moduli singoli (`2`–`10`) e gestisce l'uscita (`99`).

| Scelta Menu | Modulo / Azione | Descrizione |
| :---: | :--- | :--- |
| **`1`** | **Pulizia cartelle di lavoro** | Svuota le cartelle `FINAL`, `OUT`, `TMP` e i vecchi file in `LOG` (escludendo i file attivi) |
| **`2`** | `02_BAHS_merge-originals-ALL.py` | Unione rapida dei video originali in `IN` tramite FFmpeg concat (`stream copy`) |
| **`3`** | `03_BAHS_identify-timestamps-ALL.py` | Identificazione dei timestamp degli highlights / canestri tramite analisi video e YOLO |
| **`4`** | `04_BAHS_split-original-ALL.py` | Taglio delle clip dai video originali |
| **`5`** | `05_BAHS_convert-clips-REEL.py` | Conversione / adattamento clip in formato verticale REEL (`1080x1920`, `9:16`) |
| **`6`** | `06_BAHS_merge-clips-ALL.py` | Unione delle clip elaborate in formato **1080P** o **REEL** dentro `FINAL/` |
| **`7`** | `07_BAHS_add-music-overlay-ALL.py` | Aggiunta / mixaggio della traccia audio o musica sui video in `FINAL/` |
| **`8`** | `08_BAHS_add-text-overlay-REEL.py` | Sovraimpressione testo animato (`HIGHLIGHTS` + testo dinamico + linea verde `0x00FF66` allineata al centro del logo) su video **REEL** |
| **`9`** | `09_BAHS_add-text-overlay-1080P.py` | Sovraimpressione testo animato (`HIGHLIGHTS` + testo dinamico + linea verde `0x00FF66` allineata al centro del logo) su video **1080P** |
| **`10`** | `10_BAHS_add-logo-overlay-ALL.py` | Inserimento proporzionale del logo (`EXTRA/logo.*`) in basso a destra per **1080P** o **REEL** con trasparenza del `25%` |
| **`99`** | **Esci** | Chiude il launcher e mostra il riepilogo della sessione |

---

## 📁 Struttura delle Cartelle

```text
BAHS-AI/
├── 01_BAHS_main-ALL.py
├── 02_BAHS_merge-originals-ALL.py
├── 03_BAHS_identify-timestamps-ALL.py
├── 04_BAHS_split-original-ALL.py
├── 05_BAHS_convert-clips-REEL.py
├── 06_BAHS_merge-clips-ALL.py
├── 07_BAHS_add-music-overlay-ALL.py
├── 08_BAHS_add-text-overlay-REEL.py
├── 09_BAHS_add-text-overlay-1080P.py
├── 10_BAHS_add-logo-overlay-ALL.py
├── IN/          # Video grezzi / originali in ingresso
├── OUT/         # Output intermedi di elaborazione
├── FINAL/       # Video uniti, sonorizzati, con testo e con logo pronti alla pubblicazione
├── TMP/         # File temporanei di sessione (font, liste, appoggio FFmpeg)
├── LOG/         # File di log dettagliati per ciascuno script e sessione
├── MUSIC/       # Tracce audio / basi musicali
└── EXTRA/       # Risorse extra: font.ttf e immagine logo.<estensione>
```

---

## ⚙️ Requisiti e Installazione

### 1. Requisiti di sistema
* **Python 3.10+**
* **FFmpeg** e **FFprobe** installati e presenti nel `PATH` di sistema (Windows, macOS o Linux).

### 2. Moduli Python richiesti (`requirements.txt`)

| Modulo | Categoria | Utilizzo nella Suite |
| :--- | :--- | :--- |
| `tqdm` | CLI & Progresso | Barre di avanzamento colorate per cartelle, elaborazioni batch e processi FFmpeg |
| `ultralytics` | YOLO / Object Detection | Rilevamento e analisi visiva tramite modelli YOLO per identificazione azioni / canestri |
| `opencv-python` (`cv2`) | Computer Vision | Lettura frame, elaborazione immagini e analisi video |
| `numpy` | Calcolo Numerico | Gestione array, matrici frame e calcoli numerici |
| `Pillow` (`PIL`) | Elaborazione Immagini | Gestione, conversione e supporto immagini / risorse grafiche |
| `torch` | Deep Learning | Backend tensoriale per inferenza modelli YOLO / reti neurali (CPU o GPU CUDA) |
| `torchvision` | Deep Learning Vision | Trasformazioni e utilità di visione artificiale collegate a PyTorch |
| `scipy` | Elaborazione Dati / Segnali | Supporto per analisi numerica e filtraggio segnali/dati |

### 3. Comando di installazione con `requirements.txt`

```bash
pip install -r requirements.txt
```

### 4. Risorse consigliate in `EXTRA/`
* **`EXTRA/font.ttf`**: font TrueType utilizzato dai moduli di overlay testo (`08` e `09`). Se assente, viene utilizzato il font predefinito di sistema.
* **`EXTRA/logo.<ext>`**: immagine del logo (`.png`, `.jpg`, `.jpeg`, `.webp`, `.bmp`, `.tif`, `.tiff`) utilizzata dal modulo **`10_BAHS_add-logo-overlay-ALL.py`**.

---

## 🚀 Avvio Rapido

Apri un terminale nella cartella principale del progetto e avvia il menu principale:

```bash
python 01_BAHS_main-ALL.py
```

### Parametri e Specifiche Principali
* **Allocazione dinamica CPU**: ogni modulo rileva i thread logici disponibili (`os.cpu_count()`) e calibra automaticamente `MAX_WORKERS`, `THREADS_PER_WORKER` e `-threads` per FFmpeg.
* **Proporzioni e Logo (`10_BAHS_add-logo-overlay-ALL.py`)**:
  * **1080P (`1920x1080`)**: logo scalato proporzionalmente (`6.5%` della larghezza, `125px`), posizionato in basso a destra con trasparenza del `25%` (`75%` opacità).
  * **REEL (`1080x1920`, `9:16`)**: logo scalato proporzionalmente (`9%` della larghezza, `98px`), posizionato in basso a destra con trasparenza del `25%` (`75%` opacità).
* **Allineamento linea verde e logo**: i moduli di overlay testo (`08` e `09`) allineano la linea verde (`0x00FF66`) al centro verticale del logo di riferimento per il rispettivo formato.
* **Monitoraggio FFmpeg**: esecuzione con lettura di `stderr` su thread dedicato, aggiornamento in tempo reale di `tqdm` e controllo che il file di output esista e abbia dimensione `> 0` byte.

---

## 🛠️ Risoluzione Problemi Comuni

* **FFmpeg o FFprobe non trovati**: verifica che entrambi i comandi siano accessibili da terminale (`ffmpeg -version` e `ffprobe -version`) e riavvia il terminale dopo aver aggiornato le variabili d'ambiente `PATH`.
* **Nessun video rilevato in `IN/`**: inserisci file con estensione supportata (`.mp4`, `.mov`, `.avi`, `.mkv`, `.m4v`, `.webm`) nella cartella `IN/`.
* **Errori di codifica o file di output non valido**: controlla il report dettagliato generato automaticamente nella cartella `LOG/` con data e ora dell'esecuzione.

---

## 📄 Licenza e Contributi

Progetto pensato per uso condiviso e collaborativo. Sentiti libero di clonare, adattare e migliorare i moduli mantenendo coerenza con la struttura delle cartelle (`IN`, `OUT`, `FINAL`, `TMP`, `LOG`, `MUSIC`, `EXTRA`) e il sistema di logging.