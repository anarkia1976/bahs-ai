import argparse
import logging
import os
import re
import shutil
import subprocess
import sys
from datetime import datetime
from pathlib import Path

import cv2
from ultralytics import YOLO

SCRIPT_NAME = "05_BAHS_convert-clips-REEL"
COCO_SPORTS_BALL_CLASS = 32
CLIP_PATTERN = re.compile(r"^canestro_\d{2}_(?:\d{1,2}-)?\d{1,2}-\d{2}\.mp4$", re.IGNORECASE)
BALL_CLASS_KEYWORDS = ("sports ball", "basketball", "ball")
MODEL_EXTENSIONS = {".pt", ".onnx", ".engine", ".tflite", ".pb"}
CLEANABLE_DIRS = ("log", "tmp", "out")

# Colori ANSI per console
ANSI_RESET = "\033[0m"
ANSI_BOLD = "\033[1m"
ANSI_DIM = "\033[2m"
ANSI_CYAN = "\033[96m"
ANSI_GREEN = "\033[92m"
ANSI_YELLOW = "\033[93m"
ANSI_RED = "\033[91m"
ANSI_BLUE = "\033[94m"


def is_valid_clip_filename_05_bahs_convert_clips_reel(path: Path) -> bool:
    """Verifica che il file sia una clip nel formato canestro_<2 cifre>_<timestamp_con_trattini>.mp4."""
    return path.is_file() and bool(CLIP_PATTERN.match(path.name))


def enable_windows_ansi_05_bahs_convert_clips_reel() -> None:
    """Abilita il supporto alle sequenze ANSI sulle console Windows quando possibile."""
    if os.name == "nt":
        try:
            import ctypes

            kernel32 = ctypes.windll.kernel32
            handle = kernel32.GetStdHandle(-11)  # STD_OUTPUT_HANDLE
            mode = ctypes.c_uint32()
            if kernel32.GetConsoleMode(handle, ctypes.byref(mode)):
                kernel32.SetConsoleMode(handle, mode.value | 0x0004)  # ENABLE_VIRTUAL_TERMINAL_PROCESSING
        except Exception:
            pass


def clear_console_05_bahs_convert_clips_reel(use_color: bool = True) -> None:
    """Pulisce la console all'avvio dello script."""
    enable_windows_ansi_05_bahs_convert_clips_reel()
    if sys.stdout.isatty():
        if use_color:
            sys.stdout.write("\033[2J\033[H")
            sys.stdout.flush()
        else:
            os.system("cls" if os.name == "nt" else "clear")


class ColorConsoleFormatter_05_bahs_convert_clips_reel(logging.Formatter):
    """Formatter colorato per console con badge ad alta visibilità."""

    LEVEL_STYLES = {
        logging.DEBUG: (ANSI_DIM, "DBG"),
        logging.INFO: (ANSI_CYAN, "INF"),
        logging.WARNING: (ANSI_YELLOW + ANSI_BOLD, "WRN"),
        logging.ERROR: (ANSI_RED + ANSI_BOLD, "ERR"),
        logging.CRITICAL: (ANSI_RED + ANSI_BOLD, "CRT"),
    }

    def __init__(self, use_color: bool = True) -> None:
        super().__init__(datefmt="%H:%M:%S")
        self.use_color = use_color

    def format(self, record: logging.LogRecord) -> str:
        ts = self.formatTime(record, self.datefmt)
        msg = record.getMessage()

        if not self.use_color:
            return f"[{ts}] [{record.levelname:<7}] {msg}"

        color, tag = self.LEVEL_STYLES.get(record.levelno, (ANSI_RESET, record.levelname[:3].upper()))
        if msg.startswith("=== ") or msg.startswith("--- Avvio"):
            return f"\n{ANSI_BOLD}{ANSI_BLUE}[{ts}] {msg}{ANSI_RESET}"
        if "Completata con successo" in msg:
            return f"{ANSI_GREEN}{ANSI_BOLD}[{ts}] [{tag}] {msg}{ANSI_RESET}"
        return f"{ANSI_DIM}[{ts}]{ANSI_RESET} {color}[{tag}]{ANSI_RESET} {msg}"


def print_banner_05_bahs_convert_clips_reel(use_color: bool = True) -> None:
    """Stampa un banner compatto e leggibile a inizio esecuzione."""
    title = f"{SCRIPT_NAME} • BASKETBALL 1080p TO FACEBOOK REEL (9:16)"
    if use_color:
        print(f"{ANSI_BOLD}{ANSI_CYAN}{'=' * len(title)}{ANSI_RESET}")
        print(f"{ANSI_BOLD}{ANSI_GREEN}{title}{ANSI_RESET}")
        print(f"{ANSI_BOLD}{ANSI_CYAN}{'=' * len(title)}{ANSI_RESET}")
    else:
        print("=" * len(title))
        print(title)
        print("=" * len(title))


def emit_progress_dot_05_bahs_convert_clips_reel(dot_char: str = ".", color: str = ANSI_GREEN, use_color: bool = True) -> None:
    """Stampa un singolo punto di avanzamento senza andare a capo."""
    if not sys.stdout.isatty():
        return
    if use_color:
        sys.stdout.write(f"{color}{dot_char}{ANSI_RESET}")
    else:
        sys.stdout.write(dot_char)
    sys.stdout.flush()


def end_progress_dots_05_bahs_convert_clips_reel() -> None:
    """Chiude la riga dei puntini di avanzamento."""
    if sys.stdout.isatty():
        sys.stdout.write("\n")
        sys.stdout.flush()


def setup_workspace_05_bahs_convert_clips_reel(base_dir: Path, use_color: bool = True) -> dict[str, Path]:
    """Verifica ed eventualmente crea le cartelle IN, TMP, OUT, LOG, EXTRA ed EXTRA/MODEL."""
    extra_dir = base_dir / "EXTRA"
    dirs = {
        "in": base_dir / "IN",
        "tmp": base_dir / "TMP",
        "out": base_dir / "OUT",
        "log": base_dir / "LOG",
        "extra": extra_dir,
        "model": extra_dir / "MODEL",
    }
    labels = {
        "in": "IN",
        "tmp": "TMP",
        "out": "OUT",
        "log": "LOG",
        "extra": "EXTRA",
        "model": r"EXTRA\MODEL",
    }
    for key, path in dirs.items():
        if not path.exists():
            path.mkdir(parents=True, exist_ok=True)
            msg = f"Creata cartella {labels[key]}: {path}"
            if use_color:
                print(f"{ANSI_GREEN}[DIR]{ANSI_RESET} {msg}")
            else:
                print(f"[DIR] {msg}")
        elif not path.is_dir():
            raise NotADirectoryError(f"Il percorso {path} esiste ma non è una cartella.")
    return dirs


def clean_target_dirs_05_bahs_convert_clips_reel(
    base_dir: Path,
    targets: list[str],
    use_color: bool = True,
) -> list[str]:
    """Svuota il contenuto delle cartelle richieste tra LOG, TMP ed OUT."""
    normalized: list[str] = []
    for t in targets:
        key = t.lower().strip()
        if key == "all":
            for k in CLEANABLE_DIRS:
                if k not in normalized:
                    normalized.append(k)
        elif key in CLEANABLE_DIRS and key not in normalized:
            normalized.append(key)

    cleaned_names: list[str] = []
    for key in normalized:
        target_path = base_dir / key.upper()
        removed_count = 0
        if target_path.exists() and target_path.is_dir():
            for item in target_path.iterdir():
                try:
                    if item.is_dir() and not item.is_symlink():
                        shutil.rmtree(item)
                    else:
                        item.unlink()
                    removed_count += 1
                except Exception as exc:
                    msg = f"Impossibile rimuovere {item.name} in {key.upper()}: {exc}"
                    print(f"{ANSI_RED}[ERR]{ANSI_RESET} {msg}" if use_color else f"[ERR] {msg}")
        target_path.mkdir(parents=True, exist_ok=True)
        cleaned_names.append(key.upper())
        msg = f"Pulita cartella {key.upper()} ({removed_count} elementi rimossi): {target_path}"
        print(f"{ANSI_YELLOW}[CLN]{ANSI_RESET} {msg}" if use_color else f"[CLN] {msg}")

    return cleaned_names


def setup_logger_05_bahs_convert_clips_reel(log_dir: Path, use_color: bool = True) -> logging.Logger:
    """Configura il logger su file (in LOG/, senza codici ANSI) e su console (colorato)."""
    logger = logging.getLogger(SCRIPT_NAME)
    logger.setLevel(logging.INFO)
    logger.handlers.clear()

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_file = log_dir / f"{SCRIPT_NAME}_{timestamp}.log"

    file_formatter = logging.Formatter(
        "%(asctime)s | %(levelname)-8s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    file_handler = logging.FileHandler(log_file, encoding="utf-8")
    file_handler.setFormatter(file_formatter)

    console_handler = logging.StreamHandler()
    console_handler.setFormatter(ColorConsoleFormatter_05_bahs_convert_clips_reel(use_color=use_color))

    logger.addHandler(file_handler)
    logger.addHandler(console_handler)

    logger.info(f"[{SCRIPT_NAME}] File di log inizializzato: {log_file}")
    return logger


def normalize_model_name_05_bahs_convert_clips_reel(model_arg: str) -> str:
    """Normalizza nomi tipo 'YOLO26L' o 'yolo26l' in 'yolo26l.pt' se non è un file già esistente."""
    p = Path(model_arg)
    if p.is_file() or p.suffix.lower() in MODEL_EXTENSIONS:
        return model_arg
    return f"{model_arg.lower()}.pt"


def resolve_model_05_bahs_convert_clips_reel(model_arg: str, model_dir: Path, logger: logging.Logger) -> YOLO:
    """Verifica/carica il modello YOLO assicurandosi che risieda nella cartella EXTRA\\MODEL."""
    model_dir.mkdir(parents=True, exist_ok=True)
    normalized = normalize_model_name_05_bahs_convert_clips_reel(model_arg)
    if normalized != model_arg:
        logger.info(f"[{SCRIPT_NAME}] Nome modello normalizzato da '{model_arg}' a '{normalized}'.")

    arg_path = Path(normalized)
    target_path = model_dir / arg_path.name

    if target_path.is_file():
        logger.info(f"[{SCRIPT_NAME}] Modello trovato in EXTRA\\MODEL: {target_path}")
        return YOLO(str(target_path))

    if arg_path.is_file():
        shutil.copy2(arg_path, target_path)
        logger.info(f"[{SCRIPT_NAME}] Modello copiato in EXTRA\\MODEL: {target_path}")
        return YOLO(str(target_path))

    logger.info(f"[{SCRIPT_NAME}] Modello '{normalized}' non presente in EXTRA\\MODEL. Caricamento/download in corso...")
    model = YOLO(normalized)

    local_downloaded = Path(arg_path.name)
    if local_downloaded.is_file() and local_downloaded.resolve() != target_path.resolve():
        shutil.move(str(local_downloaded), str(target_path))
        logger.info(f"[{SCRIPT_NAME}] Modello spostato in EXTRA\\MODEL: {target_path}")
        model = YOLO(str(target_path))
    elif target_path.is_file():
        logger.info(f"[{SCRIPT_NAME}] Modello salvato in EXTRA\\MODEL: {target_path}")

    return model


def detect_ball_class_id_05_bahs_convert_clips_reel(model: YOLO, logger: logging.Logger) -> int:
    """Individua e stampa nel log l'ID e il nome della classe pallone nel modello YOLO."""
    names = model.names if isinstance(model.names, dict) else {}
    ball_cls_id = COCO_SPORTS_BALL_CLASS

    for cls_id, label in names.items():
        lbl = str(label).lower().strip()
        if lbl in BALL_CLASS_KEYWORDS:
            ball_cls_id = int(cls_id)
            break

    ball_label = names.get(ball_cls_id, f"class_{ball_cls_id}")
    logger.info(f"[{SCRIPT_NAME}] Modello YOLO -> Classe pallone individuata: ID {ball_cls_id} ({ball_label})")
    return ball_cls_id


def smooth_positions_05_bahs_convert_clips_reel(positions: list[float], alpha: float = 0.12) -> list[float]:
    """Applica un filtro EMA (Exponential Moving Average) per rendere fluido il movimento del crop."""
    if not positions:
        return []
    smoothed = [positions[0]]
    for pos in positions[1:]:
        smoothed.append(alpha * pos + (1.0 - alpha) * smoothed[-1])
    return smoothed


def fill_short_gaps_linear_05_bahs_convert_clips_reel(
    centers_x: list[float | None],
    fallback_x: float,
    max_gap_frames: int = 15,
) -> list[float]:
    """
    Riempie i buchi brevi (<= max_gap_frames) con interpolazione lineare tra due rilevamenti
    e mantiene l'ultima posizione nota per i tratti più lunghi.
    """
    n = len(centers_x)
    if n == 0:
        return []

    known = [i for i, v in enumerate(centers_x) if v is not None]
    if not known:
        return [fallback_x] * n

    filled: list[float] = [0.0] * n
    for idx in known:
        filled[idx] = float(centers_x[idx])

    for i in range(n):
        if centers_x[i] is not None:
            continue

        prev_idx = max([k for k in known if k < i], default=None)
        next_idx = min([k for k in known if k > i], default=None)

        if prev_idx is not None and next_idx is not None:
            gap = next_idx - prev_idx - 1
            if gap <= max_gap_frames:
                ratio = (i - prev_idx) / (next_idx - prev_idx)
                filled[i] = (1.0 - ratio) * float(centers_x[prev_idx]) + ratio * float(centers_x[next_idx])
            else:
                filled[i] = float(centers_x[prev_idx])
        elif prev_idx is not None:
            filled[i] = float(centers_x[prev_idx])
        elif next_idx is not None:
            filled[i] = float(centers_x[next_idx])
        else:
            filled[i] = fallback_x

    return filled


def detect_ball_centers_05_bahs_convert_clips_reel(
    video_path: Path,
    model: YOLO,
    ball_cls_id: int,
    conf_threshold: float,
    imgsz: int | None,
    logger: logging.Logger,
    use_color: bool = True,
) -> tuple[list[float | None], float, int, int, int, int]:
    """Rileva il centro X della palla (con confidenza massima) per ogni frame."""
    cap = cv2.VideoCapture(str(video_path))
    if not cap.isOpened():
        raise RuntimeError(f"Impossibile aprire il video: {video_path}")

    fps = cap.get(cv2.CAP_PROP_FPS) or 30.0
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    step_every = max(1, total_frames // 40) if total_frames > 0 else 10

    names = model.names if isinstance(model.names, dict) else {}
    ball_label_name = str(names.get(ball_cls_id, f"class_{ball_cls_id}"))
    seen_classes: dict[int, str] = {}

    raw_centers_x: list[float | None] = []
    detected_frames = 0
    frame_idx = 0

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        if imgsz is not None:
            results = model.predict(frame, conf=conf_threshold, imgsz=imgsz, verbose=False)
        else:
            results = model.predict(frame, conf=conf_threshold, verbose=False)

        best_x = None
        best_conf = 0.0

        for r in results:
            if r.boxes is None:
                continue
            for box in r.boxes:
                cls_id = int(box.cls[0].item())
                conf = float(box.conf[0].item())
                seen_classes[cls_id] = str(names.get(cls_id, f"class_{cls_id}"))
                if cls_id == ball_cls_id and conf > best_conf:
                    x1, _, x2, _ = box.xyxy[0].tolist()
                    best_x = (x1 + x2) / 2.0
                    best_conf = conf

        if best_x is not None:
            raw_centers_x.append(best_x)
            detected_frames += 1
        else:
            raw_centers_x.append(None)

        if frame_idx % step_every == 0:
            emit_progress_dot_05_bahs_convert_clips_reel(
                dot_char="•",
                color=ANSI_GREEN if best_x is not None else ANSI_YELLOW,
                use_color=use_color,
            )
        frame_idx += 1

    end_progress_dots_05_bahs_convert_clips_reel()
    cap.release()

    seen_summary = ", ".join(f"{k}:{v}" for k, v in sorted(seen_classes.items())) or "nessuna"
    logger.info(
        f"[{SCRIPT_NAME}] {video_path.name}: {total_frames} frame totali, classe palla '{ball_label_name}' (ID {ball_cls_id}) "
        f"rilevata in {detected_frames} frame [{width}x{height} @ {fps:.2f} fps]"
    )
    logger.info(f"[{SCRIPT_NAME}] {video_path.name}: classi rilevate da YOLO nel video -> {seen_summary}")
    return raw_centers_x, fps, width, height, total_frames, detected_frames


def render_reel_05_bahs_convert_clips_reel(
    input_path: Path,
    output_path: Path,
    tmp_dir: Path,
    centers_x: list[float],
    fps: float,
    src_w: int,
    src_h: int,
    logger: logging.Logger,
    out_w: int = 1080,
    out_h: int = 1920,
    use_color: bool = True,
) -> None:
    """Esegue il crop 9:16 centrato sulla palla in TMP/, ridimensiona a 1080x1920 e salva in OUT/."""
    crop_w = min(src_w, int(round(src_h * (out_w / out_h))))
    crop_h = src_h
    half_crop_w = crop_w / 2.0

    tmp_silent_video = tmp_dir / f"{input_path.stem}_silent.mp4"
    tmp_final_video = tmp_dir / f"{input_path.stem}_reel_tmp.mp4"

    cap = cv2.VideoCapture(str(input_path))
    if not cap.isOpened():
        raise RuntimeError(f"Impossibile riaprire il video per il rendering: {input_path}")

    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    step_every = max(1, total_frames // 25) if total_frames > 0 else 15

    fourcc = cv2.VideoWriter_fourcc(*"mp4v")
    writer = cv2.VideoWriter(str(tmp_silent_video), fourcc, fps, (out_w, out_h))

    idx = 0
    while True:
        ret, frame = cap.read()
        if not ret:
            break

        cx = centers_x[idx] if idx < len(centers_x) else src_w / 2.0
        if idx % step_every == 0:
            emit_progress_dot_05_bahs_convert_clips_reel(dot_char=".", color=ANSI_CYAN, use_color=use_color)
        idx += 1

        x1 = int(round(cx - half_crop_w))
        x1 = max(0, min(x1, src_w - crop_w))
        x2 = x1 + crop_w

        cropped = frame[0:crop_h, x1:x2]
        resized = cv2.resize(cropped, (out_w, out_h), interpolation=cv2.INTER_LANCZOS4)
        writer.write(resized)

    end_progress_dots_05_bahs_convert_clips_reel()
    cap.release()
    writer.release()
    logger.info(f"[{SCRIPT_NAME}] Video temporaneo senza audio salvato in TMP: {tmp_silent_video.name}")

    cmd = [
        "ffmpeg",
        "-y",
        "-i", str(tmp_silent_video),
        "-i", str(input_path),
        "-map", "0:v:0",
        "-map", "1:a?",
        "-c:v", "libx264",
        "-preset", "fast",
        "-crf", "20",
        "-pix_fmt", "yuv420p",
        "-c:a", "aac",
        "-b:a", "192k",
        "-movflags", "+faststart",
        str(tmp_final_video),
    ]
    proc = subprocess.run(cmd, capture_output=True, text=True)
    if proc.returncode != 0:
        raise RuntimeError(f"Errore FFmpeg su {input_path.name}: {proc.stderr.strip()}")

    shutil.move(str(tmp_final_video), str(output_path))
    logger.info(f"[{SCRIPT_NAME}] Reel finale salvato in OUT: {output_path}")

    if tmp_silent_video.exists():
        os.remove(tmp_silent_video)


def _prompt_clean_dirs_05_bahs_convert_clips_reel(current_clean: list[str], use_color: bool) -> list[str]:
    """Chiede per prima cosa se svuotare LOG, TMP e/o OUT indicando effetti e cautele."""
    default_label = ", ".join(current_clean) if current_clean else "nessuna"
    if use_color:
        print(f"\n{ANSI_BOLD}{ANSI_CYAN}[clean_dirs]{ANSI_RESET} Default: {ANSI_GREEN}{default_label}{ANSI_RESET} | Valori ammessi: {ANSI_YELLOW}none / log / tmp / out / all (separati da spazio o virgola){ANSI_RESET}")
        print(f"  {ANSI_DIM}• log: VANTAGGIO = ripulisce i vecchi file di log; SVANTAGGIO = perdi lo storico delle esecuzioni precedenti.{ANSI_RESET}")
        print(f"  {ANSI_DIM}• tmp: VANTAGGIO = libera spazio da eventuali file temporanei residui; SVANTAGGIO = nessuno (i temporanei normali vengono già rimossi).{ANSI_RESET}")
        print(f"  {ANSI_DIM}• out: VANTAGGIO = svuota i vecchi file in OUT; SVANTAGGIO = elimina clip e reel presenti in OUT/ prima di leggere le clip sorgente.{ANSI_RESET}")
    else:
        print(f"\n[clean_dirs] Default: {default_label} | Valori ammessi: none / log / tmp / out / all (separati da spazio o virgola)")
        print("  • log: VANTAGGIO = ripulisce i vecchi file di log; SVANTAGGIO = perdi lo storico delle esecuzioni precedenti.")
        print("  • tmp: VANTAGGIO = libera spazio da eventuali file temporanei residui; SVANTAGGIO = nessuno (i temporanei normali vengono già rimossi).")
        print("  • out: VANTAGGIO = svuota i vecchi file in OUT; SVANTAGGIO = elimina clip e reel presenti in OUT/ prima di leggere le clip sorgente.")

    valid_tokens = {"none", "nessuna", "no", "all", *CLEANABLE_DIRS}
    while True:
        raw = input(f"Cartelle da pulire [INVIO = {default_label}]: ").strip().lower()
        if raw == "":
            return current_clean
        tokens = [tok.strip() for tok in raw.replace(",", " ").split() if tok.strip()]
        if not tokens or any(tok not in valid_tokens for tok in tokens):
            err = "Inserisci 'none', 'all' oppure una combinazione di 'log', 'tmp', 'out' (o premi INVIO)."
            print(f"{ANSI_RED}{err}{ANSI_RESET}" if use_color else err)
            continue
        if any(tok in {"none", "nessuna", "no"} for tok in tokens):
            return []
        if "all" in tokens:
            return list(CLEANABLE_DIRS)
        ordered: list[str] = []
        for k in CLEANABLE_DIRS:
            if k in tokens and k not in ordered:
                ordered.append(k)
        return ordered


def _prompt_model_05_bahs_convert_clips_reel(default: str, use_color: bool) -> str:
    """Chiede il modello YOLO indicando default e pro/contro della dimensione."""
    if use_color:
        print(f"\n{ANSI_BOLD}{ANSI_CYAN}[model]{ANSI_RESET} Default: {ANSI_GREEN}{default}{ANSI_RESET} | Range: {ANSI_YELLOW}yolo26n / yolo26s / yolo26m / yolo26l / yolo26x (o .pt in EXTRA\\MODEL){ANSI_RESET}")
        print(f"  {ANSI_DIM}• Diminuire (es. yolo26n/s/m): VANTAGGIO = più veloce; SVANTAGGIO = meno preciso su palla piccola o sfocata.{ANSI_RESET}")
        print(f"  {ANSI_DIM}• Aumentare (es. yolo26x): VANTAGGIO = maggiore accuratezza; SVANTAGGIO = più lento e più memoria richiesta.{ANSI_RESET}")
    else:
        print(f"\n[model] Default: {default} | Range: yolo26n / yolo26s / yolo26m / yolo26l / yolo26x (o .pt in EXTRA\\MODEL)")
        print("  • Diminuire (es. yolo26n/s/m): VANTAGGIO = più veloce; SVANTAGGIO = meno preciso su palla piccola o sfocata.")
        print("  • Aumentare (es. yolo26x): VANTAGGIO = maggiore accuratezza; SVANTAGGIO = più lento e più memoria richiesta.")

    raw = input(f"Modello YOLO [INVIO = {default}]: ").strip()
    return raw if raw else default


def _prompt_imgsz_05_bahs_convert_clips_reel(default: int | None, use_color: bool) -> int | None:
    """Chiede imgsz e richiede nuovamente il valore se fuori dal range 640-1280."""
    default_label = "None (default YOLO)" if default is None else str(default)
    if use_color:
        print(f"\n{ANSI_BOLD}{ANSI_CYAN}[imgsz]{ANSI_RESET} Default: {ANSI_GREEN}{default_label}{ANSI_RESET} | Range: {ANSI_YELLOW}640 – 1280 (oppure None){ANSI_RESET}")
        print(f"  {ANSI_DIM}• Diminuire (es. 640): VANTAGGIO = elaborazione più rapida; SVANTAGGIO = può perdere la palla se piccola o lontana.{ANSI_RESET}")
        print(f"  {ANSI_DIM}• Aumentare (es. 1280): VANTAGGIO = vede meglio la palla piccola; SVANTAGGIO = più lento e maggiore consumo VRAM/RAM.{ANSI_RESET}")
    else:
        print(f"\n[imgsz] Default: {default_label} | Range: 640 – 1280 (oppure None)")
        print("  • Diminuire (es. 640): VANTAGGIO = elaborazione più rapida; SVANTAGGIO = può perdere la palla se piccola o lontana.")
        print("  • Aumentare (es. 1280): VANTAGGIO = vede meglio la palla piccola; SVANTAGGIO = più lento e maggiore consumo VRAM/RAM.")

    while True:
        raw = input(f"imgsz [INVIO = {default_label}, 'none' = None]: ").strip().lower()
        if raw == "":
            return default
        if raw in {"none", "null", "default"}:
            return None
        try:
            val = int(raw)
            if val < 640 or val > 1280:
                err = f"Valore {val} non nel range (640 – 1280). Reinserisci imgsz oppure premi INVIO per {default_label}."
                print(f"{ANSI_RED}{err}{ANSI_RESET}" if use_color else err)
                continue
            return val
        except ValueError:
            err = "Inserisci un intero tra 640 e 1280, 'none' oppure premi INVIO."
            print(f"{ANSI_RED}{err}{ANSI_RESET}" if use_color else err)


def _prompt_conf_05_bahs_convert_clips_reel(default: float, use_color: bool) -> float:
    """Chiede conf e richiede nuovamente il valore se fuori dal range 0.10-0.50."""
    if use_color:
        print(f"\n{ANSI_BOLD}{ANSI_CYAN}[conf]{ANSI_RESET} Default: {ANSI_GREEN}{default}{ANSI_RESET} | Range: {ANSI_YELLOW}0.10 – 0.50{ANSI_RESET}")
        print(f"  {ANSI_DIM}• Diminuire (es. 0.10–0.15): VANTAGGIO = aggancia più spesso la palla; SVANTAGGIO = più falsi positivi (riflessi, scarpe, ecc.).{ANSI_RESET}")
        print(f"  {ANSI_DIM}• Aumentare (es. 0.35–0.50): VANTAGGIO = rilevamenti più affidabili; SVANTAGGIO = più buchi se la palla è sfocata.{ANSI_RESET}")
    else:
        print(f"\n[conf] Default: {default} | Range: 0.10 – 0.50")
        print("  • Diminuire (es. 0.10–0.15): VANTAGGIO = aggancia più spesso la palla; SVANTAGGIO = più falsi positivi (riflessi, scarpe, ecc.).")
        print("  • Aumentare (es. 0.35–0.50): VANTAGGIO = rilevamenti più affidabili; SVANTAGGIO = più buchi se la palla è sfocata.")

    while True:
        raw = input(f"conf [INVIO = {default}]: ").strip().replace(",", ".")
        if raw == "":
            return default
        try:
            val = float(raw)
            if val < 0.10 or val > 0.50:
                err = f"Valore {val} non nel range (0.10 – 0.50). Reinserisci conf oppure premi INVIO per {default}."
                print(f"{ANSI_RED}{err}{ANSI_RESET}" if use_color else err)
                continue
            return val
        except ValueError:
            err = "Inserisci un numero decimale tra 0.10 e 0.50 (es. 0.50) oppure premi INVIO."
            print(f"{ANSI_RED}{err}{ANSI_RESET}" if use_color else err)


def _prompt_alpha_05_bahs_convert_clips_reel(default: float, use_color: bool) -> float:
    """Chiede alpha e richiede nuovamente il valore se fuori dal range 0.05-0.30."""
    if use_color:
        print(f"\n{ANSI_BOLD}{ANSI_CYAN}[alpha]{ANSI_RESET} Default: {ANSI_GREEN}{default}{ANSI_RESET} | Range: {ANSI_YELLOW}0.05 – 0.30{ANSI_RESET}")
        print(f"  {ANSI_DIM}• Diminuire (es. 0.05–0.08): VANTAGGIO = camera molto fluida e cinematografica; SVANTAGGIO = può inseguire in ritardo i passaggi veloci.{ANSI_RESET}")
        print(f"  {ANSI_DIM}• Aumentare (es. 0.20–0.30): VANTAGGIO = inseguimento più rapido e reattivo; SVANTAGGIO = movimento più scattoso/nervoso.{ANSI_RESET}")
    else:
        print(f"\n[alpha] Default: {default} | Range: 0.05 – 0.30")
        print("  • Diminuire (es. 0.05–0.08): VANTAGGIO = camera molto fluida e cinematografica; SVANTAGGIO = può inseguire in ritardo i passaggi veloci.")
        print("  • Aumentare (es. 0.20–0.30): VANTAGGIO = inseguimento più rapido e reattivo; SVANTAGGIO = movimento più scattoso/nervoso.")

    while True:
        raw = input(f"alpha [INVIO = {default}]: ").strip().replace(",", ".")
        if raw == "":
            return default
        try:
            val = float(raw)
            if val < 0.05 or val > 0.30:
                err = f"Valore {val} non nel range (0.05 – 0.30). Reinserisci alpha oppure premi INVIO per {default}."
                print(f"{ANSI_RED}{err}{ANSI_RESET}" if use_color else err)
                continue
            return val
        except ValueError:
            err = "Inserisci un numero decimale tra 0.05 e 0.30 (es. 0.12) oppure premi INVIO."
            print(f"{ANSI_RED}{err}{ANSI_RESET}" if use_color else err)


def _prompt_gap_frames_05_bahs_convert_clips_reel(default: int, use_color: bool) -> int:
    """Chiede gap_frames e richiede nuovamente il valore se fuori dal range 5-30."""
    if use_color:
        print(f"\n{ANSI_BOLD}{ANSI_CYAN}[gap_frames]{ANSI_RESET} Default: {ANSI_GREEN}{default}{ANSI_RESET} | Range: {ANSI_YELLOW}5 – 30{ANSI_RESET}")
        print(f"  {ANSI_DIM}• Diminuire (es. 5–10): VANTAGGIO = interpolazione corta e aderente; SVANTAGGIO = torna prima sull'ultima posizione nota se il buco è medio.{ANSI_RESET}")
        print(f"  {ANSI_DIM}• Aumentare (es. 20–30): VANTAGGIO = colma buchi più lunghi tra rilevamenti; SVANTAGGIO = interpolazione lineare su tratti lunghi meno precisa.{ANSI_RESET}")
    else:
        print(f"\n[gap_frames] Default: {default} | Range: 5 – 30")
        print("  • Diminuire (es. 5–10): VANTAGGIO = interpolazione corta e aderente; SVANTAGGIO = torna prima sull'ultima posizione nota se il buco è medio.")
        print("  • Aumentare (es. 20–30): VANTAGGIO = colma buchi più lunghi tra rilevamenti; SVANTAGGIO = interpolazione lineare su tratti lunghi meno precisa.")

    while True:
        raw = input(f"gap_frames [INVIO = {default}]: ").strip()
        if raw == "":
            return default
        try:
            val = int(raw)
            if val < 5 or val > 30:
                err = f"Valore {val} non nel range (5 – 30). Reinserisci gap_frames oppure premi INVIO per {default}."
                print(f"{ANSI_RED}{err}{ANSI_RESET}" if use_color else err)
                continue
            return val
        except ValueError:
            err = "Inserisci un numero intero tra 5 e 30 (es. 15) oppure premi INVIO."
            print(f"{ANSI_RED}{err}{ANSI_RESET}" if use_color else err)


def interactive_configure_05_bahs_convert_clips_reel(
    args: argparse.Namespace,
    base_dir: Path,
    cleaned_dirs: list[str],
    use_color: bool,
) -> tuple[argparse.Namespace, list[str]]:
    """Chiede prima la pulizia cartelle (eseguendola subito) e poi i parametri YOLO/tracking."""
    clean_label = ",".join(args.clean_dirs) if args.clean_dirs else "none"
    summary = (
        f"clean={clean_label} | model={args.model} | imgsz={args.imgsz} | "
        f"conf={args.conf} | alpha={args.alpha} | gap_frames={args.gap_frames}"
    )
    if use_color:
        print(f"\n{ANSI_BOLD}{ANSI_BLUE}PARAMETRI ATTUALI:{ANSI_RESET} {ANSI_YELLOW}{summary}{ANSI_RESET}")
        print(f"{ANSI_DIM}Premi INVIO su qualsiasi voce per mantenere il valore predefinito.{ANSI_RESET}")
    else:
        print(f"\nPARAMETRI ATTUALI: {summary}")
        print("Premi INVIO su qualsiasi voce per mantenere il valore predefinito.")

    prev_clean = list(args.clean_dirs)
    args.clean_dirs = _prompt_clean_dirs_05_bahs_convert_clips_reel(args.clean_dirs, use_color)
    newly_selected = [d for d in args.clean_dirs if d not in prev_clean]
    if newly_selected:
        cleaned_dirs.extend(clean_target_dirs_05_bahs_convert_clips_reel(base_dir, newly_selected, use_color=use_color))

    args.model = _prompt_model_05_bahs_convert_clips_reel(args.model, use_color)
    args.imgsz = _prompt_imgsz_05_bahs_convert_clips_reel(args.imgsz, use_color)
    args.conf = _prompt_conf_05_bahs_convert_clips_reel(args.conf, use_color)
    args.alpha = _prompt_alpha_05_bahs_convert_clips_reel(args.alpha, use_color)
    args.gap_frames = _prompt_gap_frames_05_bahs_convert_clips_reel(args.gap_frames, use_color)
    print("")
    return args, cleaned_dirs


def process_clip_05_bahs_convert_clips_reel(
    input_path: Path,
    dirs: dict[str, Path],
    model: YOLO,
    ball_cls_id: int,
    alpha: float,
    conf: float,
    imgsz: int | None,
    gap_frames: int,
    keep_tmp: bool,
    logger: logging.Logger,
    use_color: bool = True,
) -> None:
    """Elabora una singola clip canestro_XX_<timestamp>.mp4 da OUT verso OUT (<nome>_reel.mp4)."""
    output_path = dirs["out"] / f"{input_path.stem}_reel.mp4"
    logger.info(f"[{SCRIPT_NAME}] --- Avvio elaborazione: {input_path.name} ---")
    try:
        raw_x, fps, w, h, _, _ = detect_ball_centers_05_bahs_convert_clips_reel(
            video_path=input_path,
            model=model,
            ball_cls_id=ball_cls_id,
            conf_threshold=conf,
            imgsz=imgsz,
            logger=logger,
            use_color=use_color,
        )
        if not raw_x:
            logger.warning(f"[{SCRIPT_NAME}] Nessun frame letto da {input_path.name}, clip saltata.")
            return

        filled_x = fill_short_gaps_linear_05_bahs_convert_clips_reel(raw_x, fallback_x=w / 2.0, max_gap_frames=gap_frames)
        smooth_x = smooth_positions_05_bahs_convert_clips_reel(filled_x, alpha=alpha)

        render_reel_05_bahs_convert_clips_reel(
            input_path=input_path,
            output_path=output_path,
            tmp_dir=dirs["tmp"],
            centers_x=smooth_x,
            fps=fps,
            src_w=w,
            src_h=h,
            logger=logger,
            use_color=use_color,
        )
        logger.info(f"[{SCRIPT_NAME}] --- Completata con successo: {output_path.name} ---")
    except Exception as exc:
        logger.exception(f"[{SCRIPT_NAME}] Errore durante l'elaborazione di {input_path.name}: {exc}")
    finally:
        if not keep_tmp:
            for orphan in dirs["tmp"].glob(f"{input_path.stem}*"):
                if orphan.exists():
                    os.remove(orphan)


def main_05_bahs_convert_clips_reel() -> None:
    parser = argparse.ArgumentParser(
        prog=SCRIPT_NAME,
        description=(
            f"[{SCRIPT_NAME}] Converte clip canestro_XX_<timestamp>.mp4 presenti in OUT "
            r"in formato Reel 9:16 (<nome>_reel.mp4) in OUT usando TMP, LOG ed EXTRA\MODEL."
        ),
        formatter_class=argparse.RawTextHelpFormatter,
    )
    parser.add_argument(
        "--base-dir",
        default=".",
        help=r"Cartella radice contenente IN, TMP, OUT, LOG ed EXTRA\MODEL (default: cartella corrente).",
    )
    parser.add_argument(
        "--clean-dirs",
        nargs="+",
        default=[],
        metavar="DIR",
        help="Svuota una o più cartelle per prima cosa all'avvio tra: log, tmp, out, all (default: nessuna).",
    )
    parser.add_argument(
        "--model",
        default="yolo26l.pt",
        help=r"Modello YOLO salvato/caricato in EXTRA\MODEL (default: yolo26l.pt).",
    )
    parser.add_argument(
        "--imgsz",
        type=int,
        default=None,
        help="Risoluzione YOLO in pixel (default: None; range: 640-1280).",
    )
    parser.add_argument(
        "--conf",
        type=float,
        default=0.50,
        help="Soglia minima di confidenza per la palla (default: 0.50; range: 0.10-0.50).",
    )
    parser.add_argument(
        "--alpha",
        type=float,
        default=0.12,
        help="Fattore di smoothing EMA sul centro del crop (default: 0.12; range: 0.05-0.30).",
    )
    parser.add_argument(
        "--gap-frames",
        type=int,
        default=15,
        help="Max frame di buco interpolati linearmente (default: 15; range: 5-30).",
    )
    parser.add_argument(
        "-n",
        "--no-interactive",
        action="store_true",
        help="Salta la configurazione interattiva all'avvio e usa direttamente default/argomenti.",
    )
    parser.add_argument(
        "--keep-tmp",
        action="store_true",
        help="Non elimina i file temporanei in TMP al termine.",
    )
    parser.add_argument("--no-clear", action="store_true", help="Non pulisce la console all'avvio.")
    parser.add_argument("--no-color", action="store_true", help="Disattiva i colori ANSI nell'output su console.")
    args = parser.parse_args()

    use_color = not args.no_color and sys.stdout.isatty()
    if not args.no_clear:
        clear_console_05_bahs_convert_clips_reel(use_color=use_color)
    else:
        enable_windows_ansi_05_bahs_convert_clips_reel()

    print_banner_05_bahs_convert_clips_reel(use_color=use_color)

    base_dir = Path(args.base_dir).resolve()

    # 1) Pulizia cartelle da CLI (se specificata) eseguita per prima
    cleaned_dirs: list[str] = []
    if args.clean_dirs:
        cleaned_dirs = clean_target_dirs_05_bahs_convert_clips_reel(base_dir, args.clean_dirs, use_color=use_color)

    # 2) Configurazione interattiva: chiede prima la pulizia cartelle e poi il modello YOLO e gli altri parametri
    if not args.no_interactive and sys.stdin.isatty():
        args, cleaned_dirs = interactive_configure_05_bahs_convert_clips_reel(args, base_dir, cleaned_dirs, use_color=use_color)

    # 3) Setup cartelle e logger (dopo la pulizia, così il nuovo log resta intatto)
    dirs = setup_workspace_05_bahs_convert_clips_reel(base_dir, use_color=use_color)
    logger = setup_logger_05_bahs_convert_clips_reel(dirs["log"], use_color=use_color)

    if cleaned_dirs:
        logger.info(f"[{SCRIPT_NAME}] Cartelle pulite all'avvio: {', '.join(cleaned_dirs)}")

    logger.info(
        f"[{SCRIPT_NAME}] imgsz={args.imgsz} | conf={args.conf} | alpha={args.alpha} | "
        f"gap_frames={args.gap_frames} | model={args.model}"
    )

    all_out_files = sorted(dirs["out"].iterdir())
    videos = [p for p in all_out_files if is_valid_clip_filename_05_bahs_convert_clips_reel(p)]
    ignored_files = [
        p.name for p in all_out_files
        if p.is_file() and not is_valid_clip_filename_05_bahs_convert_clips_reel(p)
    ]

    if ignored_files:
        logger.warning(
            f"[{SCRIPT_NAME}] Ignorati {len(ignored_files)} file in OUT non conformi al formato "
            f"'canestro_<2 cifre>_<timestamp>.mp4': {', '.join(ignored_files)}"
        )

    if not videos:
        logger.warning(
            f"[{SCRIPT_NAME}] Nessun file 'canestro_<2 cifre>_<timestamp>.mp4' trovato in {dirs['out']}. "
            "Inserisci le clip nel formato atteso in OUT e rilancia lo script."
        )
        return

    logger.info(f"[{SCRIPT_NAME}] Trovate {len(videos)} clip valide in {dirs['out']}.")
    model = resolve_model_05_bahs_convert_clips_reel(args.model, dirs["model"], logger)
    ball_cls_id = detect_ball_class_id_05_bahs_convert_clips_reel(model, logger)

    for video_path in videos:
        process_clip_05_bahs_convert_clips_reel(
            input_path=video_path,
            dirs=dirs,
            model=model,
            ball_cls_id=ball_cls_id,
            alpha=args.alpha,
            conf=args.conf,
            imgsz=args.imgsz,
            gap_frames=args.gap_frames,
            keep_tmp=args.keep_tmp,
            logger=logger,
            use_color=use_color,
        )

    logger.info(f"[{SCRIPT_NAME}] === Elaborazione batch completata ===")


if __name__ == "__main__":
    main_05_bahs_convert_clips_reel()