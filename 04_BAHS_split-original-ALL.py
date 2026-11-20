import os
import sys
import subprocess
from pathlib import Path
import logging
from tqdm import tqdm
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed

# Nome dello script di riferimento dinamico
NOME_SCRIPT = "04_BAHS_split-original-ALL"


# ==========================================
# CONFIGURAZIONE DINAMICA DELLA CPU
# ==========================================
def calcola_parametri_cpu_04_bahs_split_original_all():
    """Rileva i thread logici della CPU e calcola i worker e i thread ottimali."""
    total_threads = os.cpu_count() or 4

    # Stima dei core fisici (ipotizzando hyperthreading 2x, con un minimo di 2)
    physical_cores = max(2, total_threads // 2)

    if total_threads <= 4:
        # CPU entry-level (es. 2 core / 4 thread)
        max_workers = 2
        threads_per_worker = max(1, total_threads // 2)
    elif total_threads <= 8:
        # CPU medie (es. 4 core / 8 thread)
        max_workers = 4
        threads_per_worker = 2
    else:
        # CPU performanti (es. 6 core / 12 thread o superiori)
        # Assegniamo un worker per ogni core fisico o quasi, limitando a 4 thread per FFmpeg
        max_workers = physical_cores
        threads_per_worker = 4

    return total_threads, max_workers, threads_per_worker


# Otteniamo i valori dinamici all'avvio
TOTAL_THREADS, MAX_WORKERS, THREADS_PER_WORKER = calcola_parametri_cpu_04_bahs_split_original_all()


def svuota_buffer_input_04_bahs_split_original_all():
    """Svuota eventuali tasti Invio premuti per sbaglio durante l'elaborazione."""
    try:
        if os.name == 'nt':
            import msvcrt
            while msvcrt.kbhit():
                msvcrt.getch()
        else:
            import termios
            termios.tcflush(sys.stdin, termios.TCIFLUSH)
    except Exception:
        # In alcune console IDE (es. VS Code / PyCharm) stdin potrebbe non essere un TTY standard
        pass


def pulisci_schermo_04_bahs_split_original_all():
    """Pulisce la console del terminale ad avvio script."""
    os.system('cls' if os.name == 'nt' else 'clear')


def setup_logging_04_bahs_split_original_all():
    """Configura la cartella LOG e il file di log (thread-safe)."""
    log_dir = Path("LOG")
    log_dir.mkdir(exist_ok=True)

    session_timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    log_file = log_dir / f"{NOME_SCRIPT}_{session_timestamp}.log"

    logger = logging.getLogger(NOME_SCRIPT)
    logger.setLevel(logging.INFO)

    if logger.hasHandlers():
        logger.handlers.clear()

    formatter = logging.Formatter("[%(asctime)s] [%(levelname)s] - %(message)s", datefmt="%Y-%m-%d %H:%M:%S")

    session_handler = logging.FileHandler(log_file, encoding="utf-8")
    session_handler.setLevel(logging.INFO)
    session_handler.setFormatter(formatter)
    logger.addHandler(session_handler)

    return logger, log_file


def stampa_intestazione_04_bahs_split_original_all():
    """Stampa in modo chiaro l'INIZIO con il nome dello script e l'hardware rilevato."""
    print("=" * 76)
    print(f" INIZIO ELABORAZIONE - {NOME_SCRIPT}")
    print(f" [Hardware Rilevato] Thread logici: {TOTAL_THREADS} | Worker: {MAX_WORKERS} | Thread/Worker: {THREADS_PER_WORKER}")
    print("=" * 76)
    print()


def stampa_chiusura_04_bahs_split_original_all(successo=True):
    """Stampa in modo chiaro la FINE con il nome dello script e l'esito."""
    print()
    print("=" * 76)
    stato = "PROCESSO COMPLETATO CON SUCCESSO" if successo else "PROCESSO TERMINATO CON ERRORI"
    print(f" FINE ELABORAZIONE [{NOME_SCRIPT}] - {stato}")
    print("=" * 76)


def check_ffmpeg_04_bahs_split_original_all():
    """Verifica se FFmpeg e ffprobe sono installati e raggiungibili dal sistema."""
    try:
        subprocess.run(['ffmpeg', '-version'], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        subprocess.run(['ffprobe', '-version'], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        return True
    except FileNotFoundError:
        return False


def get_video_duration_04_bahs_split_original_all(video_path):
    """Restituisce la durata totale del video in secondi usando ffprobe."""
    cmd = [
        'ffprobe',
        '-v', 'error',
        '-show_entries', 'format=duration',
        '-of', 'default=noprint_wrappers=1:nokey=1',
        str(video_path)
    ]
    try:
        result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, check=True)
        return float(result.stdout.strip())
    except Exception:
        return None


def time_to_seconds_04_bahs_split_original_all(time_str):
    """Converte una stringa di tempo (MM:SS o HH:MM:SS) in secondi totali."""
    parts = list(map(float, time_str.split(':')))
    if len(parts) == 3:
        return parts[0] * 3600 + parts[1] * 60 + parts[2]
    elif len(parts) == 2:
        return parts[0] * 60 + parts[1]
    return parts[0]


def extract_clip_04_bahs_split_original_all(input_video, timestamp, output_name, buffer_before=4, duration=12, logger=None):
    """Estrae e ricodifica la clip sfruttando i parametri dinamici della CPU con Input Seeking veloce."""
    center_sec = time_to_seconds_04_bahs_split_original_all(timestamp)
    start_sec = max(0, center_sec - buffer_before)

    cmd = [
        'ffmpeg',
        '-ss', f"{start_sec:.3f}",
        '-i', str(input_video),
        '-t', f"{duration:.3f}",
        '-c:v', 'libx264',
        '-preset', 'fast',
        '-crf', '18',
        '-threads', str(THREADS_PER_WORKER),
        '-c:a', 'aac',
        '-b:a', '320k',
        '-avoid_negative_ts', 'make_zero',
        '-y',
        str(output_name)
    ]

    if logger:
        logger.info(f"[{NOME_SCRIPT} - Worker] Avvio taglio '{output_name.name}' (Target: {timestamp}, Start: {start_sec:.2f}s)")

    try:
        result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        if result.returncode == 0:
            if logger:
                logger.info(f"[{NOME_SCRIPT} - Worker] SUCCESSO: '{output_name.name}'")
            return True
        else:
            if logger:
                logger.error(f"[{NOME_SCRIPT} - Worker] ERRORE FFmpeg su '{output_name.name}': {result.stderr.strip()}")
            return False
    except Exception as e:
        if logger:
            logger.critical(f"[{NOME_SCRIPT} - Worker] Eccezione su '{output_name.name}': {str(e)}")
        return False


def merge_clips_list_04_bahs_split_original_all(list_of_clips, output_merged_path, dir_out, logger=None):
    """Unisce una lista specifica di clip in un unico file senza ricodifica (stream copy)."""
    list_file_path = dir_out / f"temp_sublist_{NOME_SCRIPT}_{output_merged_path.stem}.txt"
    try:
        with open(list_file_path, "w", encoding="utf-8") as f:
            for clip in list_of_clips:
                f.write(f"file '{clip.name}'\n")

        cmd = [
            'ffmpeg',
            '-f', 'concat',
            '-safe', '0',
            '-i', str(list_file_path.name),
            '-c', 'copy',
            '-y',
            str(output_merged_path.name)
        ]

        result = subprocess.run(cmd, cwd=str(dir_out), stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)

        if result.returncode == 0:
            return True
        else:
            if logger:
                logger.error(f"[{NOME_SCRIPT}] Errore unione blocchi: {result.stderr.strip()}")
            return False
    except Exception as e:
        if logger:
            logger.critical(f"[{NOME_SCRIPT}] Eccezione unione blocchi: {str(e)}")
        return False
    finally:
        if list_file_path.exists():
            list_file_path.unlink()


def merge_in_groups_strategy_04_bahs_split_original_all(dir_out, logger=None):
    """Unisce le clip a gruppi di 4 in parallelo e poi fonde i gruppi nel video finale."""
    tqdm.write("\n🔗 Avvio unione avanzata a blocchi (Gruppi di 4 clip)...")

    clip_files = sorted([f for f in dir_out.glob("canestro_*.mp4")])

    if not clip_files:
        tqdm.write("⚠️ Nessuna clip trovata nella cartella OUT da unire.")
        if logger:
            logger.warning(f"[{NOME_SCRIPT}] Unione saltata: nessuna clip trovata in OUT.")
        return

    chunk_size = 4
    gruppi_creati = []

    for i in range(0, len(clip_files), chunk_size):
        chunk = clip_files[i:i + chunk_size]
        gruppo_idx = (i // chunk_size) + 1
        gruppo_path = dir_out / f"gruppo_temp_{gruppo_idx:02d}.mp4"

        tqdm.write(f"   📦 Unione blocco {gruppo_idx} ({len(chunk)} clip)...")
        if logger:
            logger.info(f"[{NOME_SCRIPT}] Unione blocco intermedio {gruppo_idx} con {len(chunk)} clip.")

        success = merge_clips_list_04_bahs_split_original_all(chunk, gruppo_path, dir_out, logger=logger)
        if success:
            gruppi_creati.append(gruppo_path)
        else:
            tqdm.write(f"❌ Errore durante l'unione del blocco {gruppo_idx}")

    if not gruppi_creati:
        tqdm.write("❌ Errore critico: nessun gruppo intermedio creato con successo.")
        return

    tqdm.write("   🎞️ Fusione finale dei blocchi intermedi nel video riassuntivo...")
    output_merged_path = dir_out / "riassunto_highlights_finale.mp4"

    success_final = merge_clips_list_04_bahs_split_original_all(gruppi_creati, output_merged_path, dir_out, logger=logger)

    for g_path in gruppi_creati:
        if g_path.exists():
            try:
                g_path.unlink()
            except Exception:
                pass

    if success_final:
        tqdm.write(f"✅ Video riassuntivo creato con successo: {output_merged_path.absolute()}")
        if logger:
            logger.info(f"[{NOME_SCRIPT}] Video riassuntivo unito con successo: {output_merged_path}")
    else:
        tqdm.write("❌ Errore durante la creazione del video riassuntivo finale.")
        if logger:
            logger.error(f"[{NOME_SCRIPT}] Errore nella fusione finale dei gruppi.")


def load_timestamps_from_file_04_bahs_split_original_all(dir_out):
    """Legge i timestamp da OUT/timestamps.txt."""
    txt_path = dir_out / "timestamps.txt"
    if not txt_path.exists():
        with open(txt_path, "w", encoding="utf-8") as f:
            f.write("# Inserisci qui i timestamp dei canestri (uno per riga oppure separati da virgola)\n")
            f.write("# Esempio:\n# 03:45\n# 12:20\n# 24:10\n")
        return None

    try:
        with open(txt_path, "r", encoding="utf-8") as f:
            lines = f.readlines()

        timestamps = []
        for line in lines:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            parts = [p.strip() for p in line.split(",")]
            for p in parts:
                if p:
                    timestamps.append(p)

        return timestamps if timestamps else None
    except Exception as e:
        print(f"⚠️ Errore nella lettura del file timestamps.txt: {e}")
        return None


def interactive_process_04_bahs_split_original_all():
    pulisci_schermo_04_bahs_split_original_all()
    stampa_intestazione_04_bahs_split_original_all()
    logger, log_file_path = setup_logging_04_bahs_split_original_all()
    successo_processo = True

    logger.info(f"[{NOME_SCRIPT}] === Nuova sessione avviata | Thread logici: {TOTAL_THREADS} | Worker: {MAX_WORKERS} | Thread/Worker: {THREADS_PER_WORKER} ===")
    print(f"⚡ Motore CPU dinamico attivo: {MAX_WORKERS} processi FFmpeg paralleli ({THREADS_PER_WORKER} thread/worker) su {TOTAL_THREADS} thread logici rilevati.\n")

    try:
        if not check_ffmpeg_04_bahs_split_original_all():
            print("❌ ERRORE CRITICO: FFmpeg / ffprobe non sono installati o non sono nel PATH.")
            logger.critical(f"[{NOME_SCRIPT}] FFmpeg/ffprobe non trovato nel sistema.")
            successo_processo = False
            return

        dir_out = Path("OUT")
        dir_out.mkdir(exist_ok=True)

        print("--- 1. SELEZIONE VIDEO ---")
        video_filename = input("📁 Nome file video nella cartella 'OUT' [Default: video_finale.mp4]: ").strip()
        if not video_filename:
            video_filename = "video_finale.mp4"
            print(f"⚠️ Nessun nome inserito, uso il predefinito: {video_filename}\n")
        else:
            print(f"✅ Video selezionato: {video_filename}\n")

        input_video_path = dir_out / video_filename

        if not input_video_path.exists():
            error_str = f"File video '{input_video_path}' non trovato nella cartella OUT."
            print(f"❌ {error_str}")
            logger.critical(f"[{NOME_SCRIPT}] {error_str}")
            successo_processo = False
            return

        video_duration = get_video_duration_04_bahs_split_original_all(input_video_path)
        if video_duration:
            mins_v = int(video_duration // 60)
            secs_v = int(video_duration % 60)
            print(f"⏱️ Durata totale video rilevata: {video_duration:.1f} secondi ({mins_v:02d}:{secs_v:02d})\n")
            logger.info(f"[{NOME_SCRIPT}] Durata video {video_filename}: {video_duration}s")
        else:
            print("⚠️ Impossibile rilevare la durata esatta del video tramite ffprobe.")

        print("--- 2. TIMESTAMP DEI CANESTRI ---")
        basket_times = load_timestamps_from_file_04_bahs_split_original_all(dir_out)

        if basket_times:
            print(f"📂 File 'timestamps.txt' trovato nella cartella 'OUT'! Caricati {len(basket_times)} timestamp.")
            logger.info(f"[{NOME_SCRIPT}] Caricati {len(basket_times)} timestamp dal file OUT/timestamps.txt")
        else:
            print("⚠️ File 'timestamps.txt' non trovato o vuoto (creato file di esempio in OUT/timestamps.txt).")
            timestamps_input = input("✍️ Inserisci manualmente i timestamps separati da virgola: ").strip()
            basket_times = [t.strip() for t in timestamps_input.split(",") if t.strip()]

            if not basket_times:
                print("❌ Nessun timestamp valido inserito. Interruzione script.")
                logger.warning(f"[{NOME_SCRIPT}] Interruzione: nessun timestamp inserito.")
                successo_processo = False
                return
            logger.info(f"[{NOME_SCRIPT}] Inseriti {len(basket_times)} timestamp manualmente.")

        if video_duration:
            valid_times = []
            for t in basket_times:
                sec = time_to_seconds_04_bahs_split_original_all(t)
                if sec > video_duration:
                    print(f"⚠️ Attenzione: Il timestamp '{t}' supera la durata totale del video. Scartato.")
                    logger.warning(f"[{NOME_SCRIPT}] Timestamp {t} scartato perché superiore alla durata del video.")
                else:
                    valid_times.append(t)
            basket_times = valid_times

            if not basket_times:
                print("❌ Errore: Nessun timestamp valido rimasto dopo il controllo di durata.")
                logger.error(f"[{NOME_SCRIPT}] Nessun timestamp valido rimasto.")
                successo_processo = False
                return

        print("\n--- 3. CONFIGURAZIONE INTERVALLO DI TAGLIO ---")
        try:
            b_before_input = input("⏱️ Secondi PRIMA del canestro [Default: 3]: ").strip()
            buffer_before = float(b_before_input) if b_before_input else 3.0

            b_after_input = input("⏱️ Secondi DOPO del canestro [Default: 3]: ").strip()
            buffer_after = float(b_after_input) if b_after_input else 3.0
        except ValueError:
            print("⚠️ Valore non valido rilevato, utilizzo i default (3s prima, 3s dopo).")
            buffer_before = 3.0
            buffer_after = 3.0

        total_duration = buffer_before + buffer_after
        logger.info(f"[{NOME_SCRIPT}] Parametri -> Video: {video_filename} | Prima: {buffer_before}s | Dopo: {buffer_after}s")

        print(f"\n🚀 Avvio elaborazione parallela di {len(basket_times)} canestri su {MAX_WORKERS} worker dinamici...")

        success_count = 0
        fail_count = 0

        with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
            futures = {}
            for i, t in enumerate(basket_times, start=1):
                safe_time_str = t.replace(':', '-')
                output_filename = dir_out / f"canestro_{i:02d}_{safe_time_str}.mp4"

                future = executor.submit(
                    extract_clip_04_bahs_split_original_all,
                    input_video_path,
                    t,
                    output_filename,
                    buffer_before=buffer_before,
                    duration=total_duration,
                    logger=logger
                )
                futures[future] = t

            with tqdm(total=len(basket_times), desc="Taglio Parallelo Dinamico", unit="clip", colour="blue") as pbar:
                pbar.set_postfix({"ok": 0, "err": 0})
                for future in as_completed(futures):
                    t_completed = futures[future]
                    try:
                        if future.result():
                            success_count += 1
                        else:
                            fail_count += 1
                    except Exception as exc:
                        logger.error(f"[{NOME_SCRIPT}] Eccezione non gestita sul timestamp {t_completed}: {exc}")
                        fail_count += 1

                    pbar.set_postfix({"ok": success_count, "err": fail_count})
                    pbar.update(1)

        print(f"\n📊 Riepilogo estrazione: {success_count} completate, {fail_count} fallite.")

        if success_count > 0:
            print("\n--- 4. CREAZIONE VIDEO UNICO FINALE (STRATEGIA A BLOCCHI) ---")
            svuota_buffer_input_04_bahs_split_original_all()
            merge_choice = input("🎞️ Vuoi unire automaticamente tutte le clip generate in un unico video riassuntivo? (S/n) [Default: S]: ").strip().lower()
            if merge_choice in ("", "s", "si", "sì", "y", "yes"):
                merge_in_groups_strategy_04_bahs_split_original_all(dir_out, logger=logger)

        logger.info(f"[{NOME_SCRIPT}] Sessione completata. Successi: {success_count}, Falliti: {fail_count}")

    except Exception as e:
        logger.exception(f"[{NOME_SCRIPT}] Errore critico durante l'esecuzione: {e}")
        successo_processo = False

    finally:
        stampa_chiusura_04_bahs_split_original_all(successo=successo_processo)


if __name__ == "__main__":
    interactive_process_04_bahs_split_original_all()