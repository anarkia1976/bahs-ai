import os
import sys
import logging
import subprocess
import shutil
from datetime import datetime
from tqdm import tqdm

SCRIPT_NAME = "06_BAHS_merge-clips-ALL"
INPUT_DIR = "OUT"
OUTPUT_DIR = "FINAL"
TMP_DIR = "TMP"
LOG_DIR = "LOG"
FILE_PREFIX = "canestro_"
FADE_DURATION = 1.0


# ==========================================
# CONFIGURAZIONE DINAMICA DELLA CPU
# ==========================================
def calcola_parametri_cpu_06_bahs_merge_clips_all():
    total_threads = os.cpu_count() or 4
    physical_cores = max(2, total_threads // 2)
    if total_threads <= 4:
        max_workers, threads_per_worker = 2, max(1, total_threads // 2)
    elif total_threads <= 8:
        max_workers, threads_per_worker = 4, 2
    else:
        max_workers, threads_per_worker = physical_cores, 4
    return total_threads, max_workers, threads_per_worker


TOTAL_THREADS, MAX_WORKERS, THREADS_PER_WORKER = calcola_parametri_cpu_06_bahs_merge_clips_all()


def setup_directories_06_bahs_merge_clips_all():
    for directory in [INPUT_DIR, OUTPUT_DIR, TMP_DIR, LOG_DIR]:
        if not os.path.exists(directory):
            os.makedirs(directory)


def setup_logging_06_bahs_merge_clips_all():
    setup_directories_06_bahs_merge_clips_all()
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


def clear_console_06_bahs_merge_clips_all():
    os.system('cls' if os.name == 'nt' else 'clear')


def check_ffmpeg_06_bahs_merge_clips_all(logger):
    if shutil.which("ffmpeg") is None or shutil.which("ffprobe") is None:
        print("\n[X] Errore: FFmpeg o FFprobe non sono installati o non sono presenti nel PATH.")
        logger.error(f"[{SCRIPT_NAME}] FFmpeg o FFprobe non trovati nel sistema.")
        sys.exit(1)


def cleanup_tmp_06_bahs_merge_clips_all(logger):
    if os.path.exists(TMP_DIR):
        try:
            shutil.rmtree(TMP_DIR)
            logger.info(f"[{SCRIPT_NAME}] Cartella temporanea '{TMP_DIR}' pulita ed eliminata con successo.")
        except Exception as e:
            logger.warning(f"[{SCRIPT_NAME}] Impossibile rimuovere completamente la cartella '{TMP_DIR}': {e}")


def get_video_duration_06_bahs_merge_clips_all(file_path):
    cmd = [
        "ffprobe", "-v", "error",
        "-show_entries", "format=duration",
        "-of", "default=noprint_wrappers=1:nokey=1",
        file_path
    ]
    result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    try:
        return float(result.stdout.strip())
    except ValueError:
        return 0.0


def prompt_clip_mode_06_bahs_merge_clips_all():
    """Chiede all'utente in fase iniziale se unire le clip 1080P (senza _reel) o quelle REEL (_reel)."""
    print("\n--- SELEZIONE FORMATO CLIP DA UNIRE ---")
    print("  1. Clip 1080P (senza '_reel') [Default]")
    print("  2. Clip REEL (con '_reel')")

    while True:
        scelta = input("\n👉 Scegli il tipo di clip da unire (1 o 2) [INVIO = 1]: ").strip().lower()
        if scelta in ("", "1", "1080p", "1080", "no_reel", "senza_reel"):
            return "1080p"
        if scelta in ("2", "reel", "con_reel"):
            return "reel"
        print("[!] Scelta non valida. Inserisci 1 (1080P senza '_reel'), 2 (REEL con '_reel') oppure premi INVIO.")


def select_matching_clips_06_bahs_merge_clips_all(input_dir, mode):
    """Restituisce l'elenco ordinato delle clip in base alla modalità ('1080p' o 'reel')."""
    all_mp4 = sorted([
        f for f in os.listdir(input_dir)
        if f.lower().startswith(FILE_PREFIX.lower()) and f.lower().endswith(".mp4")
    ])

    if mode == "reel":
        return [f for f in all_mp4 if f.lower().endswith("_reel.mp4")]
    return [f for f in all_mp4 if not f.lower().endswith("_reel.mp4")]


def normalize_clip_06_bahs_merge_clips_all(input_path, output_path, is_first=False, is_last=False, duration=0.0):
    vf_filters = "fps=30,format=yuv420p"
    af_filters = "aresample=48000,aformat=channel_layouts=stereo"

    if is_first and duration > FADE_DURATION:
        vf_filters += f",fade=t=in:st=0:d={FADE_DURATION}"
        af_filters += f",afade=t=in:st=0:d={FADE_DURATION}"

    if is_last and duration > FADE_DURATION:
        start_fade_out = max(0, duration - FADE_DURATION)
        vf_filters += f",fade=t=out:st={start_fade_out}:d={FADE_DURATION}"
        af_filters += f",afade=t=out:st={start_fade_out}:d={FADE_DURATION}"

    cmd = [
        "ffmpeg", "-i", input_path,
        "-vf", vf_filters,
        "-af", af_filters,
        "-c:v", "libx264", "-crf", "18", "-preset", "slow",
        "-threads", str(TOTAL_THREADS),
        "-c:a", "aac", "-b:a", "192k",
        "-y", output_path
    ]

    result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    return result.returncode == 0


def main_06_bahs_merge_clips_all():
    clear_console_06_bahs_merge_clips_all()
    logger, log_file = setup_logging_06_bahs_merge_clips_all()

    print("=" * 80)
    print(f" INIZIO ELABORAZIONE (Fade In/Out + Transizioni): {SCRIPT_NAME}")
    print(f" [Hardware Rilevato] Thread logici: {TOTAL_THREADS} | Worker: {MAX_WORKERS} | Thread/Worker: {THREADS_PER_WORKER}")
    print(f" Input: '{INPUT_DIR}' | Output: '{OUTPUT_DIR}' | Durata Fade: {FADE_DURATION}s")
    print(f" Data e ora: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 80)

    logger.info(f"[{SCRIPT_NAME}] INIZIO elaborazione script (Modalità Fade In/Out Completo - Thread CPU: {TOTAL_THREADS})")
    check_ffmpeg_06_bahs_merge_clips_all(logger)

    try:
        setup_directories_06_bahs_merge_clips_all()

        clip_mode = prompt_clip_mode_06_bahs_merge_clips_all()
        mode_label = "1080P (senza '_reel')" if clip_mode == "1080p" else "REEL (con '_reel')"
        output_file = os.path.join(
            OUTPUT_DIR,
            "video_finale_merged_1080p.mp4" if clip_mode == "1080p" else "video_finale_merged_reel.mp4"
        )

        print(f"\n✅ Modalità selezionata: {mode_label} -> Output: '{output_file}'")
        logger.info(f"[{SCRIPT_NAME}] Modalità clip selezionata: {clip_mode} ({mode_label}) | Output: {output_file}")

        mp4_files = select_matching_clips_06_bahs_merge_clips_all(INPUT_DIR, clip_mode)

        if not mp4_files:
            print(f"\n[!] Nessun file video di tipo {mode_label} trovato in '{INPUT_DIR}' con prefisso '{FILE_PREFIX}'.")
            logger.warning(f"[{SCRIPT_NAME}] Nessun file video di tipo {clip_mode} trovato in '{INPUT_DIR}' con prefisso '{FILE_PREFIX}'.")
            return

        print(f"\nTrovati {len(mp4_files)} file validi ({mode_label}) in '{INPUT_DIR}'.")
        logger.info(f"[{SCRIPT_NAME}] Trovati {len(mp4_files)} file validi ({clip_mode}) in '{INPUT_DIR}'.")
        print("\n[Fase 1/2] Normalizzazione e applicazione Fade In/Out...")

        normalized_files = []
        total_files = len(mp4_files)

        for idx, file in enumerate(tqdm(mp4_files, desc="Normalizzazione", unit="file", colour="blue")):
            src_path = os.path.join(INPUT_DIR, file)
            dst_path = os.path.join(TMP_DIR, f"norm_{idx:03d}.mp4")
            orig_duration = get_video_duration_06_bahs_merge_clips_all(src_path)

            is_first = (idx == 0)
            is_last = (idx == total_files - 1)

            success = normalize_clip_06_bahs_merge_clips_all(src_path, dst_path, is_first=is_first, is_last=is_last, duration=orig_duration)
            if success:
                dur = get_video_duration_06_bahs_merge_clips_all(dst_path)
                normalized_files.append({"path": dst_path, "duration": dur})
            else:
                print(f"\n[X] Errore di normalizzazione per il file: {file}")
                logger.error(f"[{SCRIPT_NAME}] Errore di normalizzazione per il file: {file}")
                return

        if len(normalized_files) == 1:
            shutil.copy(normalized_files[0]["path"], output_file)
            print(f"\n[✔] Elaborazione completata! File generato: {output_file}")
            logger.info(f"[{SCRIPT_NAME}] Elaborazione completata su singolo file: {output_file}")
            return

        print("\n[Fase 2/2] Unione ad alta precisione con transizioni intermedie...")
        cmd = ["ffmpeg"]
        for info in normalized_files:
            cmd.extend(["-i", info["path"]])

        filter_complex = ""
        current_duration = normalized_files[0]["duration"]

        for i in range(len(normalized_files) - 1):
            next_duration = normalized_files[i + 1]["duration"]
            offset = max(0, current_duration - FADE_DURATION)

            v_in1 = f"[{i:d}:v]" if i == 0 else f"[v{i}]"
            v_in2 = f"[{i+1}:v]"
            v_out = f"[v{i+1}]" if i < len(normalized_files) - 2 else "[vout]"

            a_in1 = f"[{i:d}:a]" if i == 0 else f"[a{i}]"
            a_in2 = f"[{i+1}:a]"
            a_out = f"[a{i+1}]" if i < len(normalized_files) - 2 else "[aout]"

            filter_complex += f"{v_in1}{v_in2}xfade=transition=fade:duration={FADE_DURATION}:offset={offset}{v_out};"
            filter_complex += f"{a_in1}{a_in2}acrossfade=d={FADE_DURATION}{a_out};"
            current_duration = offset + next_duration

        cmd.extend([
            "-filter_complex", filter_complex.rstrip(";"),
            "-map", "[vout]",
            "-map", "[aout]",
            "-c:v", "libx264",
            "-crf", "18",
            "-preset", "slow",
            "-threads", str(TOTAL_THREADS),
            "-c:a", "aac",
            "-b:a", "192k",
            "-y",
            output_file
        ])

        process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, universal_newlines=True, encoding='utf-8')
        for line in process.stdout:
            if "frame=" in line or "time=" in line:
                sys.stdout.write(f"\rRendering Preciso: {line.strip()[-60:]} ")
                sys.stdout.flush()

        process.wait()

        if process.returncode == 0:
            print(f"\n\n[✔] Elaborazione completata con successo! File: {output_file}")
            logger.info(f"[{SCRIPT_NAME}] Elaborazione completata con successo: {output_file}")
        else:
            print(f"\n\n[X] Errore durante il rendering finale di FFmpeg.")
            logger.error(f"[{SCRIPT_NAME}] Errore durante il rendering finale di FFmpeg.")

    except Exception as e:
        print(f"\n[X] Errore critico: {e}")
        logger.exception(f"[{SCRIPT_NAME}] Errore critico: {e}")
    finally:
        cleanup_tmp_06_bahs_merge_clips_all(logger)

    print("\n" + "=" * 80)
    print(f" FINE ELABORAZIONE: {SCRIPT_NAME}")
    print(f" Report salvato in: {log_file}")
    print("=" * 80)


if __name__ == "__main__":
    main_06_bahs_merge_clips_all()