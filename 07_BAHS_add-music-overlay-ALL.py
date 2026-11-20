import os
import sys
import logging
import subprocess
import shutil
from datetime import datetime

SCRIPT_NAME = "07_BAHS_add-music-overlay-ALL"
INPUT_DIR = "FINAL"
MUSIC_DIR = "MUSIC"
OUTPUT_DIR = "FINAL"
TMP_DIR = "TMP"
LOG_DIR = "LOG"

MUSIC_VOLUME = 0.6
ORIGINAL_AUDIO_VOLUME = 0.4


# ==========================================
# CONFIGURAZIONE DINAMICA DELLA CPU
# ==========================================
def calcola_parametri_cpu_07_bahs_add_music_overlay_all():
    total_threads = os.cpu_count() or 4
    physical_cores = max(2, total_threads // 2)
    if total_threads <= 4:
        max_workers, threads_per_worker = 2, max(1, total_threads // 2)
    elif total_threads <= 8:
        max_workers, threads_per_worker = 4, 2
    else:
        max_workers, threads_per_worker = physical_cores, 4
    return total_threads, max_workers, threads_per_worker


TOTAL_THREADS, MAX_WORKERS, THREADS_PER_WORKER = calcola_parametri_cpu_07_bahs_add_music_overlay_all()


def setup_directories_07_bahs_add_music_overlay_all():
    for directory in [INPUT_DIR, MUSIC_DIR, OUTPUT_DIR, TMP_DIR, LOG_DIR]:
        if not os.path.exists(directory):
            os.makedirs(directory)


def setup_logging_07_bahs_add_music_overlay_all():
    setup_directories_07_bahs_add_music_overlay_all()
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


def clear_console_07_bahs_add_music_overlay_all():
    os.system('cls' if os.name == 'nt' else 'clear')


def check_ffmpeg_07_bahs_add_music_overlay_all(logger):
    if shutil.which("ffmpeg") is None:
        print("\n[X] Errore: FFmpeg non è installato o non è presente nel PATH.")
        logger.error(f"[{SCRIPT_NAME}] FFmpeg non trovato nel sistema.")
        sys.exit(1)


def cleanup_tmp_07_bahs_add_music_overlay_all(logger):
    if os.path.exists(TMP_DIR):
        try:
            shutil.rmtree(TMP_DIR)
            logger.info(f"[{SCRIPT_NAME}] Cartella temporanea '{TMP_DIR}' pulita ed eliminata con successo.")
        except Exception as e:
            logger.warning(f"[{SCRIPT_NAME}] Impossibile rimuovere completamente '{TMP_DIR}': {e}")


def select_input_video_07_bahs_add_music_overlay_all(input_dir):
    """Individua il video unificato in FINAL e, se presenti più varianti, chiede quale usare."""
    candidates = [
        os.path.join(input_dir, "video_finale_merged_1080p.mp4"),
        os.path.join(input_dir, "video_finale_merged_reel.mp4"),
        os.path.join(input_dir, "video_finale_merged.mp4"),
    ]
    existing = [p for p in candidates if os.path.isfile(p)]

    if not existing:
        return None
    if len(existing) == 1:
        return existing[0]

    print("\n--- SELEZIONE VIDEO UNIFICATO IN 'FINAL' ---")
    for idx, path in enumerate(existing, start=1):
        print(f"  {idx}. {os.path.basename(path)}")

    while True:
        scelta = input(f"\n👉 Scegli il video da usare (1-{len(existing)}) [INVIO = 1]: ").strip()
        if scelta == "":
            return existing[0]
        if scelta.isdigit():
            idx = int(scelta) - 1
            if 0 <= idx < len(existing):
                return existing[idx]
        print(f"[!] Scelta non valida. Inserisci un numero da 1 a {len(existing)} oppure premi INVIO.")


def main_07_bahs_add_music_overlay_all():
    clear_console_07_bahs_add_music_overlay_all()
    logger, log_file = setup_logging_07_bahs_add_music_overlay_all()

    print("=" * 70)
    print(f" INIZIO ELABORAZIONE (Mix Audio): {SCRIPT_NAME}")
    print(f" [Hardware Rilevato] Thread logici: {TOTAL_THREADS} | Worker: {MAX_WORKERS} | Thread/Worker: {THREADS_PER_WORKER}")
    print(f" Cartella Input: '{INPUT_DIR}' | Cartella Musica: '{MUSIC_DIR}'")
    print(f" Bilanciamento -> Musica: {int(MUSIC_VOLUME * 100)}% | Pubblico: {int(ORIGINAL_AUDIO_VOLUME * 100)}%")
    print("=" * 70)

    logger.info(f"[{SCRIPT_NAME}] INIZIO elaborazione script (Thread CPU: {TOTAL_THREADS})")
    check_ffmpeg_07_bahs_add_music_overlay_all(logger)
    setup_directories_07_bahs_add_music_overlay_all()

    try:
        input_video = select_input_video_07_bahs_add_music_overlay_all(INPUT_DIR)
        if not input_video or not os.path.exists(input_video):
            print(f"\n[!] Errore: Nessun file video unificato trovato in '{INPUT_DIR}'.")
            logger.error(f"[{SCRIPT_NAME}] Nessun file video unificato trovato in '{INPUT_DIR}'.")
            return

        base_name = os.path.splitext(os.path.basename(input_video))[0]
        output_file = os.path.join(OUTPUT_DIR, f"{base_name}_music.mp4")

        supported_audio_exts = ('.mp3', '.wav', '.m4a', '.aac', '.flac', '.ogg')
        music_files = sorted([f for f in os.listdir(MUSIC_DIR) if f.lower().endswith(supported_audio_exts)])

        if not music_files:
            print(f"\n[!] Nessun file musicale trovato nella cartella '{MUSIC_DIR}'.")
            logger.warning(f"[{SCRIPT_NAME}] Nessun file musicale trovato in '{MUSIC_DIR}'.")
            return

        selected_music = music_files[0]
        music_path = os.path.join(MUSIC_DIR, selected_music)
        print(f"\nVideo selezionato: '{input_video}'")
        print(f"Traccia musicale selezionata: '{selected_music}'")
        print(f"File di output previsto: '{output_file}'")
        logger.info(f"[{SCRIPT_NAME}] Video: {input_video} | Musica: {music_path} | Output: {output_file}")

        cmd = [
            "ffmpeg",
            "-i", input_video,
            "-stream_loop", "-1",
            "-i", music_path,
            "-filter_complex",
            f"[0:a]volume={ORIGINAL_AUDIO_VOLUME}[original];[1:a]volume={MUSIC_VOLUME}[music];[original][music]amix=inputs=2:duration=first:dropout_transition=2[aout]",
            "-map", "0:v",
            "-map", "[aout]",
            "-c:v", "copy",
            "-threads", str(TOTAL_THREADS),
            "-c:a", "aac",
            "-b:a", "192k",
            "-shortest",
            "-y",
            output_file
        ]

        process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, universal_newlines=True, encoding='utf-8')
        for line in process.stdout:
            if "time=" in line:
                sys.stdout.write(f"\rElaborazione in corso: {line.strip()[-50:]} ")
                sys.stdout.flush()

        process.wait()

        if process.returncode == 0:
            print(f"\n\n[✔] Elaborazione completata! File: {output_file}")
            logger.info(f"[{SCRIPT_NAME}] Elaborazione completata con successo: {output_file}")
        else:
            print(f"\n\n[X] Errore durante l'esecuzione di FFmpeg.")
            logger.error(f"[{SCRIPT_NAME}] Errore durante l'esecuzione di FFmpeg.")

    except Exception as e:
        print(f"\n[X] Errore critico: {e}")
        logger.exception(f"[{SCRIPT_NAME}] Errore critico: {e}")
    finally:
        cleanup_tmp_07_bahs_add_music_overlay_all(logger)

    print("\n" + "=" * 70)
    print(f" FINE ELABORAZIONE: {SCRIPT_NAME}")
    print(f" Report salvato in: {log_file}")
    print("=" * 70)


if __name__ == "__main__":
    main_07_bahs_add_music_overlay_all()