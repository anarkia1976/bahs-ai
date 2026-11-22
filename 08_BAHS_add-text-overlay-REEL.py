import os
import sys
import logging
import subprocess
import shutil
import threading
from datetime import datetime
from pathlib import Path

try:
    from tqdm import tqdm
except ImportError:
    tqdm = None

SCRIPT_NAME = "08_BAHS_add-text-overlay-REEL"
INPUT_DIR = "FINAL"
OUTPUT_DIR = "FINAL"
DEFAULT_INPUT_VIDEO = os.path.join(INPUT_DIR, "video_finale_merged_reel_music.mp4")
DEFAULT_OUTPUT_FILE = os.path.join(OUTPUT_DIR, "video_finale_merged_reel_music_text.mp4")
EXTRA_DIR = "EXTRA"
LOG_DIR = "LOG"
TMP_DIR = "TMP"

# Formato standard Facebook Reels (9:16 verticale)
REEL_WIDTH = 1080
REEL_HEIGHT = 1920

# Riferimento logo REEL (larghezza 9% di 1080 = 98px, margine destro 36px, margine inferiore 48px)
REEL_LOGO_WIDTH = 98
REEL_LOGO_MARGIN_X = 36
REEL_LOGO_MARGIN_Y = 48


# ==========================================
# CONFIGURAZIONE DINAMICA DELLA CPU
# ==========================================
def calcola_parametri_cpu_08_bahs_add_text_overlay_reel():
    total_threads = os.cpu_count() or 4
    physical_cores = max(2, total_threads // 2)
    if total_threads <= 4:
        max_workers, threads_per_worker = 2, max(1, total_threads // 2)
    elif total_threads <= 8:
        max_workers, threads_per_worker = 4, 2
    else:
        max_workers, threads_per_worker = physical_cores, 4
    return total_threads, max_workers, threads_per_worker


TOTAL_THREADS, MAX_WORKERS, THREADS_PER_WORKER = calcola_parametri_cpu_08_bahs_add_text_overlay_reel()


def setup_directories_08_bahs_add_text_overlay_reel():
    for directory in [INPUT_DIR, OUTPUT_DIR, EXTRA_DIR, TMP_DIR, LOG_DIR]:
        os.makedirs(directory, exist_ok=True)


def setup_logging_08_bahs_add_text_overlay_reel():
    setup_directories_08_bahs_add_text_overlay_reel()
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_filename = os.path.join(LOG_DIR, f"{SCRIPT_NAME}_{timestamp}.log")

    logger = logging.getLogger(SCRIPT_NAME)
    logger.setLevel(logging.INFO)
    if logger.hasHandlers():
        logger.handlers.clear()

    handler = logging.FileHandler(log_filename, encoding="utf-8")
    handler.setFormatter(logging.Formatter("%(asctime)s [%(levelname)s] - %(message)s"))
    logger.addHandler(handler)
    return logger, log_filename


def clear_console_08_bahs_add_text_overlay_reel():
    os.system("cls" if os.name == "nt" else "clear")


def check_ffmpeg_08_bahs_add_text_overlay_reel(logger):
    if shutil.which("ffmpeg") is None or shutil.which("ffprobe") is None:
        print("\n[X] Errore: FFmpeg o ffprobe non sono installati nel PATH.")
        logger.error(f"[{SCRIPT_NAME}] FFmpeg o ffprobe non trovati nel sistema.")
        sys.exit(1)


def cleanup_tmp_08_bahs_add_text_overlay_reel(logger):
    if os.path.exists(TMP_DIR):
        try:
            shutil.rmtree(TMP_DIR)
            logger.info(f"[{SCRIPT_NAME}] Cartella temporanea '{TMP_DIR}' pulita con successo.")
        except Exception as e:
            logger.warning(f"[{SCRIPT_NAME}] Impossibile rimuovere completamente '{TMP_DIR}': {e}")


def escape_drawtext_08_bahs_add_text_overlay_reel(text: str) -> str:
    """Effettua l'escape dei caratteri speciali per il filtro drawtext di FFmpeg."""
    escaped = text.replace("\\", "\\\\")
    escaped = escaped.replace(":", "\\:")
    escaped = escaped.replace("'", "’")
    escaped = escaped.replace("%", "\\%")
    return escaped


def has_audio_stream_08_bahs_add_text_overlay_reel(video_path: str) -> bool:
    """Verifica se il file video contiene almeno uno stream audio."""
    cmd = [
        "ffprobe",
        "-v", "error",
        "-select_streams", "a",
        "-show_entries", "stream=index",
        "-of", "csv=p=0",
        str(video_path)
    ]
    res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    return bool(res.stdout.strip())


def get_video_duration_08_bahs_add_text_overlay_reel(video_path: str) -> float:
    """Restituisce la durata del video in secondi tramite ffprobe."""
    cmd = [
        "ffprobe",
        "-v", "error",
        "-show_entries", "format=duration",
        "-of", "default=noprint_wrappers=1:nokey=1",
        str(video_path)
    ]
    res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    try:
        return max(0.0, float(res.stdout.strip()))
    except ValueError:
        return 0.0


def get_logo_dimensions_08_bahs_add_text_overlay_reel() -> tuple[int, int]:
    """Restituisce (larghezza, altezza) del logo REEL in EXTRA/logo.* se presente, altrimenti stima quadrata."""
    exts = (".png", ".jpg", ".jpeg", ".webp", ".bmp", ".tif", ".tiff")
    logo_path = None
    if os.path.isdir(EXTRA_DIR):
        for entry in sorted(os.listdir(EXTRA_DIR)):
            p = Path(EXTRA_DIR) / entry
            if p.is_file() and p.stem.lower() == "logo" and p.suffix.lower() in exts:
                logo_path = str(p)
                break

    if logo_path and shutil.which("ffprobe"):
        cmd = [
            "ffprobe",
            "-v", "error",
            "-select_streams", "v:0",
            "-show_entries", "stream=width,height",
            "-of", "csv=p=0:s=x",
            logo_path,
        ]
        res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        parts = res.stdout.strip().split("x")
        if len(parts) == 2 and parts[0].isdigit() and parts[1].isdigit():
            orig_w, orig_h = int(parts[0]), int(parts[1])
            if orig_w > 0 and orig_h > 0:
                scaled_h = max(2, int(round((orig_h * REEL_LOGO_WIDTH) / orig_w)))
                if scaled_h % 2 != 0:
                    scaled_h += 1
                return REEL_LOGO_WIDTH, scaled_h

    return REEL_LOGO_WIDTH, REEL_LOGO_WIDTH


def list_mp4_in_final_08_bahs_add_text_overlay_reel(input_dir: str = INPUT_DIR) -> list[str]:
    """Restituisce i file .mp4 in FINAL escludendo quelli che terminano con '_logo' o '_text'."""
    if not os.path.isdir(input_dir):
        return []

    files = []
    for entry in sorted(os.listdir(input_dir)):
        p = Path(input_dir) / entry
        if not p.is_file():
            continue
        stem_lower = p.stem.lower()
        if p.suffix.lower() == ".mp4" and not stem_lower.endswith("_logo") and not stem_lower.endswith("_text"):
            files.append(str(p))
    return files


def resolve_input_video_08_bahs_add_text_overlay_reel(
    raw_input: str,
    available_files: list[str] | None = None,
) -> str:
    """Risolve il percorso del video di partenza (default con Invio, indice, nome in FINAL o percorso custom)."""
    cleaned = raw_input.strip().strip('"').strip("'")

    if not cleaned:
        return DEFAULT_INPUT_VIDEO

    # Selezione per indice numerico dall'elenco mostrato
    if available_files and cleaned.isdigit():
        idx = int(cleaned) - 1
        if 0 <= idx < len(available_files):
            return available_files[idx]

    # Se viene indicata una cartella, usa il file di default dentro quella cartella
    if os.path.isdir(cleaned):
        return os.path.join(cleaned, os.path.basename(DEFAULT_INPUT_VIDEO))

    # Se il percorso esiste già così com'è, lo restituisce direttamente
    if os.path.exists(cleaned):
        return cleaned

    # Altrimenti cerca dentro INPUT_DIR aggiungendo .mp4 se mancante
    candidate_name = cleaned if cleaned.lower().endswith(".mp4") else f"{cleaned}.mp4"
    in_final = os.path.join(INPUT_DIR, os.path.basename(candidate_name))
    return in_final


def resolve_output_video_08_bahs_add_text_overlay_reel(input_video: str) -> str:
    """Determina il file di output in FINAL in base al video di input."""
    if os.path.abspath(input_video) == os.path.abspath(DEFAULT_INPUT_VIDEO):
        return DEFAULT_OUTPUT_FILE

    stem = Path(input_video).stem
    return os.path.join(OUTPUT_DIR, f"{stem}_text.mp4")


def _parse_out_time_to_ms_08_bahs_add_text_overlay_reel(line: str) -> int | None:
    """Converte le righe out_time_us / out_time_ms / out_time di FFmpeg in millisecondi."""
    if line.startswith("out_time_us=") or line.startswith("out_time_ms="):
        val_str = line.split("=", 1)[1].strip()
        if val_str.lstrip("-").isdigit():
            return max(0, int(val_str) // 1000)
    elif line.startswith("out_time="):
        time_str = line.split("=", 1)[1].strip()
        if time_str and time_str != "N/A":
            try:
                parts = time_str.split(":")
                if len(parts) == 3:
                    h = float(parts[0])
                    m = float(parts[1])
                    s = float(parts[2])
                    total_sec = max(0.0, h * 3600.0 + m * 60.0 + s)
                    return int(round(total_sec * 1000.0))
            except ValueError:
                return None
    return None


def run_ffmpeg_with_progress_08_bahs_add_text_overlay_reel(
    cmd: list[str],
    output_path: str,
    total_duration: float,
    logger=None,
) -> bool:
    """Esegue FFmpeg mostrando una barra di avanzamento colorata tqdm leggendo stderr in thread dedicato."""
    progress_cmd = list(cmd)
    progress_cmd = progress_cmd[:-1] + ["-progress", "pipe:1", "-nostats", progress_cmd[-1]]

    total_ms = int(round(total_duration * 1000)) if total_duration > 0 else 0
    pbar = None
    if tqdm is not None and total_ms > 0:
        pbar = tqdm(
            total=total_ms,
            desc="Overlay Testo REEL",
            unit="ms",
            unit_scale=True,
            colour="cyan",
        )

    last_ms = 0
    stderr_lines: list[str] = []

    def _drain_stderr(pipe):
        try:
            for err_line in iter(pipe.readline, ""):
                if err_line:
                    stderr_lines.append(err_line.rstrip())
        finally:
            try:
                pipe.close()
            except Exception:
                pass

    try:
        process = subprocess.Popen(
            progress_cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            encoding="utf-8",
            errors="replace",
        )

        err_thread = None
        if process.stderr is not None:
            err_thread = threading.Thread(target=_drain_stderr, args=(process.stderr,), daemon=True)
            err_thread.start()

        if process.stdout is not None:
            try:
                for raw_line in iter(process.stdout.readline, ""):
                    line = raw_line.strip()
                    current_ms = _parse_out_time_to_ms_08_bahs_add_text_overlay_reel(line)
                    if current_ms is not None:
                        if pbar is not None:
                            clamped_ms = min(total_ms, current_ms)
                            if clamped_ms > last_ms:
                                pbar.update(clamped_ms - last_ms)
                                last_ms = clamped_ms
                        elif total_ms > 0:
                            pct = min(100.0, (current_ms / total_ms) * 100.0)
                            sys.stdout.write(f"\rAvanzamento Overlay Testo REEL: {pct:5.1f}% ")
                            sys.stdout.flush()
                    elif line == "progress=end":
                        if pbar is not None and last_ms < total_ms:
                            pbar.update(total_ms - last_ms)
                            last_ms = total_ms
            finally:
                try:
                    process.stdout.close()
                except Exception:
                    pass

        returncode = process.wait()
        if err_thread is not None:
            err_thread.join(timeout=5.0)

        if pbar is not None:
            if returncode == 0 and last_ms < total_ms:
                pbar.update(total_ms - last_ms)
            pbar.close()
        elif total_ms > 0:
            if returncode == 0:
                sys.stdout.write("\rAvanzamento Overlay Testo REEL: 100.0%\n")
            else:
                print("")

        out_p = Path(output_path)
        file_ok = out_p.is_file() and out_p.stat().st_size > 0

        if returncode != 0 or not file_ok:
            if out_p.exists() and out_p.stat().st_size == 0:
                try:
                    out_p.unlink()
                except Exception:
                    pass
            if logger:
                err_msg = "\n".join(stderr_lines) if stderr_lines else f"File output non valido o vuoto (rc={returncode})"
                logger.error(f"[{SCRIPT_NAME}] Errore FFmpeg:\n{err_msg}")
            return False

        return True

    except Exception as e:
        if pbar is not None:
            pbar.close()
        if logger:
            logger.critical(f"[{SCRIPT_NAME}] Eccezione overlay Reel: {str(e)}")
        return False


def apply_text_overlay_reel_08_bahs_add_text_overlay_reel(video_path, output_path, dynamic_text, duration=5.0, logger=None):
    setup_directories_08_bahs_add_text_overlay_reel()
    extra_font = Path(EXTRA_DIR) / "font.ttf"
    tmp_font = Path(TMP_DIR) / "font.ttf"

    font_clause = ""
    if extra_font.exists():
        shutil.copy(extra_font, tmp_font)
        font_path = str(tmp_font).replace("\\", "/").replace(":", "\\:")
        font_clause = f"fontfile='{font_path}':"
        if logger:
            logger.info(f"[{SCRIPT_NAME}] Copiato EXTRA/font.ttf in TMP.")
    else:
        msg = f"File font '{extra_font}' non trovato: uso del font predefinito di sistema."
        print(f"\n[!] Attenzione: {msg}")
        if logger:
            logger.warning(f"[{SCRIPT_NAME}] {msg}")

    safe_dynamic_text = escape_drawtext_08_bahs_add_text_overlay_reel(dynamic_text)

    _, logo_scaled_h = get_logo_dimensions_08_bahs_add_text_overlay_reel()
    logo_top_y = REEL_HEIGHT - REEL_LOGO_MARGIN_Y - logo_scaled_h
    logo_center_y = int(round(logo_top_y + (logo_scaled_h / 2.0)))

    base_x = 40
    line_height = 5
    # Centro verticale della linea verde allineato al centro verticale del logo
    line_y = logo_center_y - (line_height // 2)
    # Testo "HIGHLIGHTS" sopra la linea verde e testo dinamico sotto la linea verde
    base_y = line_y - 70
    dynamic_y = line_y + 22
    line_width = 760

    trans_time = 1.2
    start_x = -1120
    target_x = base_x
    hold_end = max(trans_time, duration - trans_time)

    if logger:
        logger.info(
            f"[{SCRIPT_NAME}] Linea verde allineata al centro del logo REEL: "
            f"logo_center_y={logo_center_y}, line_y={line_y}, base_y={base_y}, dynamic_y={dynamic_y}"
        )

    x_expr = (
        f"if(lt(t\\,{trans_time})\\,"
        f"{start_x}+({target_x}-({start_x}))*sin((t/{trans_time})*1.570796)\\,"
        f"if(lt(t\\,{hold_end})\\,"
        f"{target_x}\\,"
        f"{target_x}+({start_x}-{target_x})*sin(((t-{hold_end})/{trans_time})*1.570796)))"
    )

    alpha_expr = (
        f"if(lt(t\\,{trans_time})\\,t/{trans_time}\\,"
        f"if(lt(t\\,{hold_end})\\,1\\,"
        f"({duration}-t)/{trans_time}))"
    )

    filter_complex = (
        f"[0:v]scale={REEL_WIDTH}:{REEL_HEIGHT}:force_original_aspect_ratio=decrease,"
        f"pad={REEL_WIDTH}:{REEL_HEIGHT}:(ow-iw)/2:(oh-ih)/2:color=black,"
        f"setsar=1,format=yuv420p[v_norm];"
        f"[v_norm]drawtext={font_clause}text='HIGHLIGHTS':"
        f"fontcolor=white:fontsize=58:borderw=3:bordercolor=black@0.85:"
        f"x={base_x}:y={base_y}:alpha='{alpha_expr}':"
        f"enable='between(t,0,{duration})'[txt_top];"
        f"[txt_top]drawbox=x={base_x}:y={line_y}:w={line_width}:h={line_height}:color=0x00FF66:t=fill:"
        f"enable='between(t,0,{duration})'[line_green];"
        f"[line_green]drawtext={font_clause}text='{safe_dynamic_text}':"
        f"fontcolor=white:fontsize=46:borderw=3:bordercolor=black@0.85:"
        f"x='{x_expr}':y={dynamic_y}:alpha='{alpha_expr}':"
        f"enable='between(t,0,{duration})'[v_final]"
    )

    audio_present = has_audio_stream_08_bahs_add_text_overlay_reel(video_path)
    total_duration = get_video_duration_08_bahs_add_text_overlay_reel(video_path)

    cmd = [
        "ffmpeg",
        "-i", str(video_path),
        "-filter_complex", filter_complex,
        "-map", "[v_final]",
    ]

    if audio_present:
        cmd.extend(["-map", "0:a?", "-c:a", "aac", "-b:a", "192k"])
    else:
        if logger:
            logger.info(f"[{SCRIPT_NAME}] Nessuno stream audio rilevato nel file di input: esporto solo video.")

    cmd.extend([
        "-c:v", "libx264",
        "-preset", "medium",
        "-crf", "18",
        "-pix_fmt", "yuv420p",
        "-movflags", "+faststart",
        "-threads", str(TOTAL_THREADS),
        "-y",
        str(output_path)
    ])

    if logger:
        logger.info(f"[{SCRIPT_NAME}] Avvio elaborazione overlay Reel FFmpeg...")
    return run_ffmpeg_with_progress_08_bahs_add_text_overlay_reel(
        cmd,
        output_path=str(output_path),
        total_duration=total_duration,
        logger=logger,
    )


def main_08_bahs_add_text_overlay_reel():
    clear_console_08_bahs_add_text_overlay_reel()
    setup_directories_08_bahs_add_text_overlay_reel()
    logger, log_file = setup_logging_08_bahs_add_text_overlay_reel()

    print("=" * 70)
    print(f" REEL TEXT OVERLAY: {SCRIPT_NAME}")
    print(f" Formato target: {REEL_WIDTH}x{REEL_HEIGHT} (9:16 Facebook Reels)")
    print(f" [Hardware Rilevato] Thread logici: {TOTAL_THREADS} | Worker: {MAX_WORKERS} | Thread/Worker: {THREADS_PER_WORKER}")
    print(f" Output previsto in FINAL: '{DEFAULT_OUTPUT_FILE}'")
    print(f" Data e ora: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 70)

    logger.info(f"[{SCRIPT_NAME}] INIZIO elaborazione script (Thread CPU: {TOTAL_THREADS})")
    check_ffmpeg_08_bahs_add_text_overlay_reel(logger)

    try:
        mp4_files = list_mp4_in_final_08_bahs_add_text_overlay_reel(INPUT_DIR)
        if mp4_files:
            print(f"\n--- VIDEO MP4 DISPONIBILI IN '{INPUT_DIR}' (esclusi '*_logo' e '*_text') ---")
            for idx, fpath in enumerate(mp4_files, start=1):
                marker = " [DEFAULT]" if os.path.abspath(fpath) == os.path.abspath(DEFAULT_INPUT_VIDEO) else ""
                print(f"  {idx}. {os.path.basename(fpath)}{marker}")

        raw_video_input = input(
            f"\n📁 Numero, nome in '{INPUT_DIR}' o percorso [INVIO = {os.path.basename(DEFAULT_INPUT_VIDEO)}]: "
        ).strip()
        video_input = resolve_input_video_08_bahs_add_text_overlay_reel(raw_video_input, mp4_files)

        if not os.path.exists(video_input):
            print(f"\n[!] Errore: File video '{video_input}' non trovato.")
            logger.error(f"[{SCRIPT_NAME}] File video '{video_input}' non trovato.")
            return

        output_file = resolve_output_video_08_bahs_add_text_overlay_reel(video_input)

        dynamic_input = input("📝 Inserisci il testo dinamico inferiore [Default: CAMPIONATO - TEAM vs TEAM]: ").strip()
        if not dynamic_input:
            dynamic_input = "CAMPIONATO - TEAM vs TEAM"

        print(f"\n🎬 Video input: '{video_input}'")
        print(f"💾 Elaborazione Reel in corso -> Output: '{output_file}'...\n")
        logger.info(f"[{SCRIPT_NAME}] Input: {video_input} | Output: {output_file}")

        if apply_text_overlay_reel_08_bahs_add_text_overlay_reel(video_input, output_file, dynamic_input, duration=5.0, logger=logger):
            print(f"\n\n[✔] Elaborazione completata! File: {output_file}")
            logger.info(f"[{SCRIPT_NAME}] Elaborazione completata con successo: {output_file}")
        else:
            print(f"\n\n[X] Errore durante l'elaborazione con FFmpeg. Controlla il log: {log_file}")
            logger.error(f"[{SCRIPT_NAME}] Errore durante l'elaborazione con FFmpeg.")

    except Exception as e:
        print(f"\n[X] Errore critico: {e}")
        logger.critical(f"[{SCRIPT_NAME}] Errore critico: {e}")
    finally:
        cleanup_tmp_08_bahs_add_text_overlay_reel(logger)

    print("\n" + "=" * 70)
    print(f" FINE ELABORAZIONE: {SCRIPT_NAME}")
    print(f" Report salvato in: {log_file}")
    print("=" * 70)


if __name__ == "__main__":
    main_08_bahs_add_text_overlay_reel()