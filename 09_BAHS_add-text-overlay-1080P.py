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

SCRIPT_NAME = "09_BAHS_add-text-overlay-1080P"
INPUT_DIR = "FINAL"
OUTPUT_DIR = "FINAL"
DEFAULT_VIDEO_NAME = "video_finale_merged_1080p_music.mp4"
DEFAULT_INPUT_VIDEO = os.path.join(INPUT_DIR, DEFAULT_VIDEO_NAME)
DEFAULT_OUTPUT_FILE = os.path.join(OUTPUT_DIR, "video_finale_merged_1080p_music_text.mp4")
EXTRA_DIR = "EXTRA"
LOG_DIR = "LOG"
TMP_DIR = "TMP"

# Formato standard Full HD orizzontale (16:9)
VIDEO_WIDTH = 1920
VIDEO_HEIGHT = 1080

# Riferimento logo 1080P (larghezza 6.5% di 1920 = 125px, margine destro 40px, margine inferiore 36px)
FHD_LOGO_WIDTH = 125
FHD_LOGO_MARGIN_X = 40
FHD_LOGO_MARGIN_Y = 36


# ==========================================
# CONFIGURAZIONE DINAMICA DELLA CPU
# ==========================================
def calcola_parametri_cpu_09_bahs_add_text_overlay_1080p():
    total_threads = os.cpu_count() or 4
    physical_cores = max(2, total_threads // 2)
    if total_threads <= 4:
        max_workers, threads_per_worker = 2, max(1, total_threads // 2)
    elif total_threads <= 8:
        max_workers, threads_per_worker = 4, 2
    else:
        max_workers, threads_per_worker = physical_cores, 4
    return total_threads, max_workers, threads_per_worker


TOTAL_THREADS, MAX_WORKERS, THREADS_PER_WORKER = calcola_parametri_cpu_09_bahs_add_text_overlay_1080p()


def setup_directories_09_bahs_add_text_overlay_1080p():
    for directory in [INPUT_DIR, OUTPUT_DIR, EXTRA_DIR, TMP_DIR, LOG_DIR]:
        os.makedirs(directory, exist_ok=True)


def setup_logging_09_bahs_add_text_overlay_1080p():
    setup_directories_09_bahs_add_text_overlay_1080p()
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


def clear_console_09_bahs_add_text_overlay_1080p():
    os.system("cls" if os.name == "nt" else "clear")


def check_ffmpeg_09_bahs_add_text_overlay_1080p(logger):
    if shutil.which("ffmpeg") is None or shutil.which("ffprobe") is None:
        print("\n[X] Errore: FFmpeg o ffprobe non sono installati nel PATH.")
        logger.error(f"[{SCRIPT_NAME}] FFmpeg o ffprobe non trovati nel sistema.")
        sys.exit(1)


def cleanup_tmp_09_bahs_add_text_overlay_1080p(logger):
    if os.path.exists(TMP_DIR):
        try:
            shutil.rmtree(TMP_DIR)
            logger.info(f"[{SCRIPT_NAME}] Cartella temporanea '{TMP_DIR}' pulita con successo.")
        except Exception as e:
            logger.warning(f"[{SCRIPT_NAME}] Impossibile rimuovere completamente '{TMP_DIR}': {e}")


def escape_drawtext_09_bahs_add_text_overlay_1080p(text: str) -> str:
    """Effettua l'escape dei caratteri speciali per il filtro drawtext di FFmpeg."""
    escaped = text.replace("\\", "\\\\")
    escaped = escaped.replace(":", "\\:")
    escaped = escaped.replace("'", "’")
    escaped = escaped.replace("%", "\\%")
    return escaped


def has_audio_stream_09_bahs_add_text_overlay_1080p(video_path: str) -> bool:
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


def get_video_duration_09_bahs_add_text_overlay_1080p(video_path: str) -> float:
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


def get_logo_dimensions_09_bahs_add_text_overlay_1080p() -> tuple[int, int]:
    """Restituisce (larghezza, altezza) del logo 1080P in EXTRA/logo.* se presente, altrimenti stima quadrata."""
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
                scaled_h = max(2, int(round((orig_h * FHD_LOGO_WIDTH) / orig_w)))
                if scaled_h % 2 != 0:
                    scaled_h += 1
                return FHD_LOGO_WIDTH, scaled_h

    return FHD_LOGO_WIDTH, FHD_LOGO_WIDTH


def resolve_final_video_09_bahs_add_text_overlay_1080p(input_dir: str, raw_input: str) -> tuple[str | None, str | None]:
    """
    Risolve e valida un video esclusivamente all'interno di `input_dir` ('FINAL').
    Restituisce (input_path, output_path) oppure (None, motivo_errore).
    """
    final_root = Path(input_dir).resolve()
    cleaned = raw_input.strip().strip('"').strip("'")

    if not cleaned:
        candidate = (final_root / DEFAULT_VIDEO_NAME).resolve()
    else:
        raw_path = Path(cleaned)
        # Se è un percorso relativo che inizia già per 'FINAL/' o 'FINAL\', lo risolviamo rispetto alla cwd
        if not raw_path.is_absolute() and len(raw_path.parts) > 0 and raw_path.parts[0].lower() == input_dir.lower():
            candidate = raw_path.resolve()
        elif raw_path.is_absolute():
            candidate = raw_path.resolve()
        else:
            # L'utente ha inserito un nome file (es. "mio_video.mp4" o "mio_video")
            candidate = (final_root / raw_path).resolve()

        # Se non ha estensione, prova con .mp4 dentro FINAL
        if not candidate.suffix and not candidate.exists():
            candidate = candidate.with_suffix(".mp4").resolve()

    # Verifica stretta: il file deve risiedere direttamente o in una sottocartella di FINAL
    try:
        candidate.relative_to(final_root)
    except ValueError:
        return None, f"Sono accettati esclusivamente video situati all'interno della cartella '{input_dir}'."

    if not candidate.is_file():
        return None, f"Il file '{candidate.name}' non esiste nella cartella '{input_dir}'."

    out_dir = Path(OUTPUT_DIR).resolve()
    if candidate.stem.lower() == Path(DEFAULT_VIDEO_NAME).stem.lower():
        out_path = out_dir / f"{candidate.stem}_text{candidate.suffix or '.mp4'}"
    else:
        out_path = out_dir / f"{candidate.stem}_text{candidate.suffix or '.mp4'}"

    # Evita che output e input coincidano esattamente
    if out_path.resolve() == candidate:
        out_path = out_dir / f"{candidate.stem}_overlay{candidate.suffix or '.mp4'}"

    return str(candidate), str(out_path)


def _parse_out_time_to_ms_09_bahs_add_text_overlay_1080p(line: str) -> int | None:
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


def run_ffmpeg_with_progress_09_bahs_add_text_overlay_1080p(
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
            desc="Overlay Testo 1080P",
            unit="ms",
            unit_scale=True,
            colour="green",
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
                    current_ms = _parse_out_time_to_ms_09_bahs_add_text_overlay_1080p(line)
                    if current_ms is not None:
                        if pbar is not None:
                            clamped_ms = min(total_ms, current_ms)
                            if clamped_ms > last_ms:
                                pbar.update(clamped_ms - last_ms)
                                last_ms = clamped_ms
                        elif total_ms > 0:
                            pct = min(100.0, (current_ms / total_ms) * 100.0)
                            sys.stdout.write(f"\rAvanzamento Overlay Testo 1080P: {pct:5.1f}% ")
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
                sys.stdout.write("\rAvanzamento Overlay Testo 1080P: 100.0%\n")
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
            logger.critical(f"[{SCRIPT_NAME}] Eccezione overlay 1080P: {str(e)}")
        return False


def apply_text_overlay_1080p_09_bahs_add_text_overlay_1080p(video_path, output_path, dynamic_text, duration=5.0, logger=None):
    setup_directories_09_bahs_add_text_overlay_1080p()
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

    safe_dynamic_text = escape_drawtext_09_bahs_add_text_overlay_1080p(dynamic_text)

    _, logo_scaled_h = get_logo_dimensions_09_bahs_add_text_overlay_1080p()
    logo_top_y = VIDEO_HEIGHT - FHD_LOGO_MARGIN_Y - logo_scaled_h
    logo_center_y = int(round(logo_top_y + (logo_scaled_h / 2.0)))

    base_x = 60
    line_height = 4
    # Centro verticale della linea verde allineato al centro verticale del logo 1080P
    line_y = logo_center_y - (line_height // 2)
    # Testo "HIGHLIGHTS" sopra la linea verde e testo dinamico sotto la linea verde
    base_y = line_y - 72
    dynamic_y = line_y + 24
    line_width = 750

    trans_time = 1.5
    start_x = -1600
    target_x = base_x
    hold_end = max(trans_time, duration - trans_time)

    if logger:
        logger.info(
            f"[{SCRIPT_NAME}] Linea verde allineata al centro del logo 1080P: "
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
        f"[0:v]scale={VIDEO_WIDTH}:{VIDEO_HEIGHT}:force_original_aspect_ratio=decrease,"
        f"pad={VIDEO_WIDTH}:{VIDEO_HEIGHT}:(ow-iw)/2:(oh-ih)/2,format=yuv420p[v_norm];"
        f"[v_norm]drawtext={font_clause}text='HIGHLIGHTS':"
        f"fontcolor=white:fontsize=64:borderw=3:bordercolor=black:"
        f"x={base_x}:y={base_y}:alpha='{alpha_expr}':"
        f"enable='between(t,0,{duration})'[txt_top];"
        f"[txt_top]drawbox=x={base_x}:y={line_y}:w={line_width}:h={line_height}:color=0x00FF66:t=fill:"
        f"enable='between(t,0,{duration})'[line_green];"
        f"[line_green]drawtext={font_clause}text='{safe_dynamic_text}':"
        f"fontcolor=white:fontsize=64:borderw=3:bordercolor=black:"
        f"x='{x_expr}':y={dynamic_y}:alpha='{alpha_expr}':"
        f"enable='between(t,0,{duration})'[v_final]"
    )

    audio_present = has_audio_stream_09_bahs_add_text_overlay_1080p(video_path)
    total_duration = get_video_duration_09_bahs_add_text_overlay_1080p(video_path)

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
        "-crf", "18",
        "-pix_fmt", "yuv420p",
        "-threads", str(TOTAL_THREADS),
        "-y",
        str(output_path)
    ])

    if logger:
        logger.info(f"[{SCRIPT_NAME}] Avvio elaborazione overlay 1080P FFmpeg...")
    return run_ffmpeg_with_progress_09_bahs_add_text_overlay_1080p(
        cmd,
        output_path=str(output_path),
        total_duration=total_duration,
        logger=logger,
    )


def main_09_bahs_add_text_overlay_1080p():
    clear_console_09_bahs_add_text_overlay_1080p()
    setup_directories_09_bahs_add_text_overlay_1080p()
    logger, log_file = setup_logging_09_bahs_add_text_overlay_1080p()

    print("=" * 70)
    print(f" TEXT OVERLAY 1080P: {SCRIPT_NAME}")
    print(f" Formato target: {VIDEO_WIDTH}x{VIDEO_HEIGHT} (16:9 Full HD)")
    print(f" [Hardware Rilevato] Thread logici: {TOTAL_THREADS} | Worker: {MAX_WORKERS} | Thread/Worker: {THREADS_PER_WORKER}")
    print(f" Cartella input/output consentita: '{INPUT_DIR}/'")
    print(f" Data e ora: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 70)

    logger.info(f"[{SCRIPT_NAME}] INIZIO elaborazione script (Thread CPU: {TOTAL_THREADS})")
    check_ffmpeg_09_bahs_add_text_overlay_1080p(logger)

    try:
        raw_video_input = input(
            f"\n📁 Inserisci il nome del video in '{INPUT_DIR}' [Default: {DEFAULT_VIDEO_NAME}]: "
        ).strip()

        video_input, output_file = resolve_final_video_09_bahs_add_text_overlay_1080p(INPUT_DIR, raw_video_input)

        if not video_input or not output_file:
            err_msg = output_file or f"Video non valido per la cartella '{INPUT_DIR}'."
            print(f"\n[!] Errore: {err_msg}")
            logger.warning(f"[{SCRIPT_NAME}] {err_msg} Input ricevuto: '{raw_video_input}'")
            return

        dynamic_input = input("📝 Inserisci il testo dinamico inferiore [Default: CAMPIONATO - TEAM vs TEAM]: ").strip()
        if not dynamic_input:
            dynamic_input = "CAMPIONATO - TEAM vs TEAM"

        print(f"\n🎬 Elaborazione video 1080P in corso...")
        print(f"   Input : '{video_input}'")
        print(f"   Output: '{output_file}'\n")
        logger.info(f"[{SCRIPT_NAME}] Input: {video_input} | Output: {output_file}")

        if apply_text_overlay_1080p_09_bahs_add_text_overlay_1080p(video_input, output_file, dynamic_input, duration=5.0, logger=logger):
            print(f"\n\n[✔] Elaborazione completata! File: {output_file}")
            logger.info(f"[{SCRIPT_NAME}] Elaborazione completata con successo: {output_file}")
        else:
            print(f"\n\n[X] Errore durante l'elaborazione con FFmpeg. Controlla il log: {log_file}")
            logger.error(f"[{SCRIPT_NAME}] Errore durante l'elaborazione con FFmpeg.")

    except Exception as e:
        print(f"\n[X] Errore critico: {e}")
        logger.critical(f"[{SCRIPT_NAME}] Errore critico: {e}")
    finally:
        cleanup_tmp_09_bahs_add_text_overlay_1080p(logger)

    print("\n" + "=" * 70)
    print(f" FINE ELABORAZIONE: {SCRIPT_NAME}")
    print(f" Report salvato in: {log_file}")
    print("=" * 70)


if __name__ == "__main__":
    main_09_bahs_add_text_overlay_1080p()