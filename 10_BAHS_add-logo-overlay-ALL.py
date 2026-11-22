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

SCRIPT_NAME = "10_BAHS_add-logo-overlay-ALL"
INPUT_DIR = "FINAL"
OUTPUT_DIR = "FINAL"
EXTRA_DIR = "EXTRA"
LOG_DIR = "LOG"
TMP_DIR = "TMP"

DEFAULT_1080P_INPUT = os.path.join(INPUT_DIR, "video_finale_merged_1080p_music_text.mp4")
DEFAULT_REEL_INPUT = os.path.join(INPUT_DIR, "video_finale_merged_reel_music_text.mp4")

DEFAULT_1080P_OUTPUT = os.path.join(OUTPUT_DIR, "video_finale_merged_1080p_music_text_logo.mp4")
DEFAULT_REEL_OUTPUT = os.path.join(OUTPUT_DIR, "video_finale_merged_reel_music_text_logo.mp4")

LOGO_BASENAME = "logo"
SUPPORTED_LOGO_EXTS = (".png", ".jpg", ".jpeg", ".webp", ".bmp", ".tif", ".tiff")

# Dimensioni target per le due modalità
VIDEO_1080P_WIDTH = 1920
VIDEO_1080P_HEIGHT = 1080

REEL_WIDTH = 1080
REEL_HEIGHT = 1920


# ==========================================
# CONFIGURAZIONE DINAMICA DELLA CPU
# ==========================================
def calcola_parametri_cpu_10_bahs_add_logo_overlay_all():
    total_threads = os.cpu_count() or 4
    physical_cores = max(2, total_threads // 2)
    if total_threads <= 4:
        max_workers, threads_per_worker = 2, max(1, total_threads // 2)
    elif total_threads <= 8:
        max_workers, threads_per_worker = 4, 2
    else:
        max_workers, threads_per_worker = physical_cores, 4
    return total_threads, max_workers, threads_per_worker


TOTAL_THREADS, MAX_WORKERS, THREADS_PER_WORKER = calcola_parametri_cpu_10_bahs_add_logo_overlay_all()


def setup_directories_10_bahs_add_logo_overlay_all():
    for directory in [INPUT_DIR, OUTPUT_DIR, EXTRA_DIR, TMP_DIR, LOG_DIR]:
        os.makedirs(directory, exist_ok=True)


def setup_logging_10_bahs_add_logo_overlay_all():
    setup_directories_10_bahs_add_logo_overlay_all()
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


def clear_console_10_bahs_add_logo_overlay_all():
    os.system("cls" if os.name == "nt" else "clear")


def check_ffmpeg_10_bahs_add_logo_overlay_all(logger):
    if shutil.which("ffmpeg") is None or shutil.which("ffprobe") is None:
        print("\n[X] Errore: FFmpeg o ffprobe non sono installati nel PATH.")
        logger.error(f"[{SCRIPT_NAME}] FFmpeg o ffprobe non trovati nel sistema.")
        sys.exit(1)


def cleanup_tmp_10_bahs_add_logo_overlay_all(logger):
    if os.path.exists(TMP_DIR):
        try:
            shutil.rmtree(TMP_DIR)
            logger.info(f"[{SCRIPT_NAME}] Cartella temporanea '{TMP_DIR}' pulita con successo.")
        except Exception as e:
            logger.warning(f"[{SCRIPT_NAME}] Impossibile rimuovere completamente '{TMP_DIR}': {e}")


def has_audio_stream_10_bahs_add_logo_overlay_all(video_path: str) -> bool:
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


def get_video_duration_10_bahs_add_logo_overlay_all(video_path: str) -> float:
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


def prompt_format_mode_10_bahs_add_logo_overlay_all() -> str:
    """Chiede all'utente in fase iniziale se elaborare in modalità 1080P o REEL."""
    print("\n--- SELEZIONE PROPORZIONI / MODALITÀ LOGO ---")
    print("  1. 1080P (1920x1080 orizzontale) [Default]")
    print("  2. REEL  (1080x1920 verticale 9:16)")

    while True:
        scelta = input("\n👉 Scegli la modalità (1 o 2) [INVIO = 1]: ").strip().lower()
        if scelta in ("", "1", "1080p", "1080", "hd", "fhd"):
            return "1080p"
        if scelta in ("2", "reel", "reels", "9:16"):
            return "reel"
        print("[!] Scelta non valida. Inserisci 1 (1080P), 2 (REEL) oppure premi INVIO.")


def list_mp4_in_final_10_bahs_add_logo_overlay_all(input_dir: str = INPUT_DIR) -> list[str]:
    """Restituisce i file .mp4 in FINAL escludendo quelli che terminano con '_logo'."""
    if not os.path.isdir(input_dir):
        return []

    files = []
    for entry in sorted(os.listdir(input_dir)):
        p = Path(input_dir) / entry
        if not p.is_file():
            continue
        if p.suffix.lower() == ".mp4" and not p.stem.lower().endswith("_logo"):
            files.append(str(p))
    return files


def resolve_input_video_10_bahs_add_logo_overlay_all(
    mode: str,
    raw_input: str,
    available_files: list[str] | None = None,
) -> str:
    """Risolve il percorso del video di partenza (default con Invio, indice, nome in FINAL o percorso custom)."""
    default_video = DEFAULT_1080P_INPUT if mode == "1080p" else DEFAULT_REEL_INPUT
    cleaned = raw_input.strip().strip('"').strip("'")

    if not cleaned:
        return default_video

    # Selezione per indice numerico dall'elenco mostrato
    if available_files and cleaned.isdigit():
        idx = int(cleaned) - 1
        if 0 <= idx < len(available_files):
            return available_files[idx]

    # Se viene indicata una cartella, usa il file di default dentro quella cartella
    if os.path.isdir(cleaned):
        return os.path.join(cleaned, os.path.basename(default_video))

    # Se il percorso esiste già così com'è, lo restituisce direttamente
    if os.path.exists(cleaned):
        return cleaned

    # Altrimenti cerca dentro INPUT_DIR aggiungendo .mp4 se mancante
    candidate_name = cleaned if cleaned.lower().endswith(".mp4") else f"{cleaned}.mp4"
    in_final = os.path.join(INPUT_DIR, os.path.basename(candidate_name))
    if os.path.exists(in_final):
        return in_final

    return in_final


def resolve_output_video_10_bahs_add_logo_overlay_all(mode: str, input_video: str) -> str:
    """Determina il file di output in FINAL in base al video di input e alla modalità."""
    default_output = DEFAULT_1080P_OUTPUT if mode == "1080p" else DEFAULT_REEL_OUTPUT
    expected_default_input = DEFAULT_1080P_INPUT if mode == "1080p" else DEFAULT_REEL_INPUT

    if os.path.abspath(input_video) == os.path.abspath(expected_default_input):
        return default_output

    stem = Path(input_video).stem
    return os.path.join(OUTPUT_DIR, f"{stem}_logo.mp4")


def find_logo_files_10_bahs_add_logo_overlay_all(extra_dir: str) -> list[str]:
    """Cerca in EXTRA i file immagine logo.<estensione> con estensioni classiche."""
    if not os.path.isdir(extra_dir):
        return []

    found = []
    for entry in sorted(os.listdir(extra_dir)):
        p = Path(extra_dir) / entry
        if not p.is_file():
            continue
        if p.stem.lower() == LOGO_BASENAME and p.suffix.lower() in SUPPORTED_LOGO_EXTS:
            found.append(str(p))
    return found


def select_logo_file_10_bahs_add_logo_overlay_all(extra_dir: str, logger=None) -> str | None:
    """Seleziona il logo in EXTRA/logo.* (chiedendo solo se sono presenti più varianti)."""
    logos = find_logo_files_10_bahs_add_logo_overlay_all(extra_dir)
    if not logos:
        return None
    if len(logos) == 1:
        return logos[0]

    print("\n--- PIÙ LOGO TROVATI IN 'EXTRA' ---")
    for idx, path in enumerate(logos, start=1):
        print(f"  {idx}. {os.path.basename(path)}")

    while True:
        scelta = input(f"\n👉 Scegli il logo da usare (1-{len(logos)}) [INVIO = 1]: ").strip()
        if scelta == "":
            return logos[0]
        if scelta.isdigit():
            idx = int(scelta) - 1
            if 0 <= idx < len(logos):
                return logos[idx]
        print(f"[!] Scelta non valida. Inserisci un numero da 1 a {len(logos)} oppure premi INVIO.")


def _parse_out_time_to_ms_10_bahs_add_logo_overlay_all(line: str) -> int | None:
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


def run_ffmpeg_with_progress_10_bahs_add_logo_overlay_all(
    cmd: list[str],
    output_path: str,
    total_duration: float,
    desc: str = "Overlay Logo",
    colour: str = "magenta",
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
            desc=desc,
            unit="ms",
            unit_scale=True,
            colour=colour,
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
                    current_ms = _parse_out_time_to_ms_10_bahs_add_logo_overlay_all(line)
                    if current_ms is not None:
                        if pbar is not None:
                            clamped_ms = min(total_ms, current_ms)
                            if clamped_ms > last_ms:
                                pbar.update(clamped_ms - last_ms)
                                last_ms = clamped_ms
                        elif total_ms > 0:
                            pct = min(100.0, (current_ms / total_ms) * 100.0)
                            sys.stdout.write(f"\rAvanzamento {desc}: {pct:5.1f}% ")
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
                sys.stdout.write(f"\rAvanzamento {desc}: 100.0%\n")
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
            logger.critical(f"[{SCRIPT_NAME}] Eccezione overlay logo: {str(e)}")
        return False


def apply_logo_overlay_10_bahs_add_logo_overlay_all(
    video_path: str,
    logo_path: str,
    output_path: str,
    mode: str,
    logger=None,
) -> bool:
    """Applica il logo proporzionale in basso a destra rispettando le proporzioni 1080P o REEL."""
    setup_directories_10_bahs_add_logo_overlay_all()

    if mode == "reel":
        target_w, target_h = REEL_WIDTH, REEL_HEIGHT
        # Su formato REEL (9:16) il logo è dimezzato rispetto al precedente 18% -> 9% (98px su 1080px)
        logo_target_w = int(round(target_w * 0.09))
        if logo_target_w % 2 != 0:
            logo_target_w += 1
        margin_x = 36
        margin_y = 48
        bar_desc = "Overlay Logo REEL"
        bar_colour = "cyan"
        # Trasparenza leggera del 25% -> opacità alfa 0.75
        logo_chain = (
            f"[1:v]format=rgba,colorchannelmixer=aa=0.75,"
            f"scale={logo_target_w}:-2:flags=lanczos[logo_scaled];"
        )
    else:
        target_w, target_h = VIDEO_1080P_WIDTH, VIDEO_1080P_HEIGHT
        # Su formato 1080P il logo è dimezzato rispetto al precedente 13% -> 6.5% (125px su 1920px)
        logo_target_w = int(round(target_w * 0.065))
        if logo_target_w % 2 != 0:
            logo_target_w += 1
        margin_x = 40
        margin_y = 36
        bar_desc = "Overlay Logo 1080P"
        bar_colour = "green"
        # Trasparenza leggera del 25% -> opacità alfa 0.75
        logo_chain = (
            f"[1:v]format=rgba,colorchannelmixer=aa=0.75,"
            f"scale={logo_target_w}:-2:flags=lanczos[logo_scaled];"
        )

    filter_complex = (
        f"[0:v]scale={target_w}:{target_h}:force_original_aspect_ratio=decrease,"
        f"pad={target_w}:{target_h}:(ow-iw)/2:(oh-ih)/2:color=black,"
        f"setsar=1,format=yuv420p[v_base];"
        f"{logo_chain}"
        f"[v_base][logo_scaled]overlay=x=W-w-{margin_x}:y=H-h-{margin_y}:format=auto[v_out]"
    )

    audio_present = has_audio_stream_10_bahs_add_logo_overlay_all(video_path)
    total_duration = get_video_duration_10_bahs_add_logo_overlay_all(video_path)

    cmd = [
        "ffmpeg",
        "-i", str(video_path),
        "-i", str(logo_path),
        "-filter_complex", filter_complex,
        "-map", "[v_out]",
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
        str(output_path),
    ])

    if logger:
        logger.info(
            f"[{SCRIPT_NAME}] Avvio overlay logo ({mode.upper()}, {target_w}x{target_h}, "
            f"logo_w={logo_target_w}px, margin=({margin_x},{margin_y}))..."
        )

    return run_ffmpeg_with_progress_10_bahs_add_logo_overlay_all(
        cmd,
        output_path=str(output_path),
        total_duration=total_duration,
        desc=bar_desc,
        colour=bar_colour,
        logger=logger,
    )


def main_10_bahs_add_logo_overlay_all():
    clear_console_10_bahs_add_logo_overlay_all()
    setup_directories_10_bahs_add_logo_overlay_all()
    logger, log_file = setup_logging_10_bahs_add_logo_overlay_all()

    print("=" * 74)
    print(f" LOGO OVERLAY (1080P / REEL): {SCRIPT_NAME}")
    print(f" [Hardware Rilevato] Thread logici: {TOTAL_THREADS} | Worker: {MAX_WORKERS} | Thread/Worker: {THREADS_PER_WORKER}")
    print(f" Cartella Loghi: '{EXTRA_DIR}/{LOGO_BASENAME}.*' | Output: '{OUTPUT_DIR}'")
    print(f" Data e ora: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 74)

    logger.info(f"[{SCRIPT_NAME}] INIZIO elaborazione script (Thread CPU: {TOTAL_THREADS})")
    check_ffmpeg_10_bahs_add_logo_overlay_all(logger)

    try:
        mode = prompt_format_mode_10_bahs_add_logo_overlay_all()
        mode_label = "1080P (1920x1080)" if mode == "1080p" else "REEL (1080x1920 9:16)"
        default_video = DEFAULT_1080P_INPUT if mode == "1080p" else DEFAULT_REEL_INPUT

        logo_path = select_logo_file_10_bahs_add_logo_overlay_all(EXTRA_DIR, logger=logger)
        if not logo_path or not os.path.exists(logo_path):
            exts_str = ", ".join(SUPPORTED_LOGO_EXTS)
            msg = f"Nessun file '{LOGO_BASENAME}.*' trovato in '{EXTRA_DIR}' (estensioni supportate: {exts_str})."
            print(f"\n[!] Errore: {msg}")
            logger.error(f"[{SCRIPT_NAME}] {msg}")
            return

        mp4_files = list_mp4_in_final_10_bahs_add_logo_overlay_all(INPUT_DIR)
        if mp4_files:
            print(f"\n--- VIDEO MP4 DISPONIBILI IN '{INPUT_DIR}' (esclusi '*_logo') ---")
            for idx, fpath in enumerate(mp4_files, start=1):
                marker = " [DEFAULT]" if os.path.abspath(fpath) == os.path.abspath(default_video) else ""
                print(f"  {idx}. {os.path.basename(fpath)}{marker}")

        raw_video_input = input(
            f"\n📁 Numero, nome in '{INPUT_DIR}' o percorso [INVIO = {os.path.basename(default_video)}]: "
        ).strip()
        video_input = resolve_input_video_10_bahs_add_logo_overlay_all(mode, raw_video_input, mp4_files)

        if not os.path.exists(video_input):
            print(f"\n[!] Errore: File video '{video_input}' non trovato.")
            logger.error(f"[{SCRIPT_NAME}] File video '{video_input}' non trovato.")
            return

        output_file = resolve_output_video_10_bahs_add_logo_overlay_all(mode, video_input)

        print(f"\n✅ Modalità: {mode_label}")
        print(f"🖼️  Logo selezionato: '{logo_path}'")
        print(f"🎬 Video input: '{video_input}'")
        print(f"💾 Output previsto: '{output_file}'\n")
        logger.info(f"[{SCRIPT_NAME}] Modalità={mode} | Logo={logo_path} | Input={video_input} | Output={output_file}")

        if apply_logo_overlay_10_bahs_add_logo_overlay_all(
            video_path=video_input,
            logo_path=logo_path,
            output_path=output_file,
            mode=mode,
            logger=logger,
        ):
            print(f"\n\n[✔] Elaborazione completata! File: {output_file}")
            logger.info(f"[{SCRIPT_NAME}] Elaborazione completata con successo: {output_file}")
        else:
            print(f"\n\n[X] Errore durante l'elaborazione con FFmpeg. Controlla il log: {log_file}")
            logger.error(f"[{SCRIPT_NAME}] Errore durante l'elaborazione con FFmpeg.")

    except Exception as e:
        print(f"\n[X] Errore critico: {e}")
        logger.critical(f"[{SCRIPT_NAME}] Errore critico: {e}")
    finally:
        cleanup_tmp_10_bahs_add_logo_overlay_all(logger)

    print("\n" + "=" * 74)
    print(f" FINE ELABORAZIONE: {SCRIPT_NAME}")
    print(f" Report salvato in: {log_file}")
    print("=" * 74)


if __name__ == "__main__":
    main_10_bahs_add_logo_overlay_all()