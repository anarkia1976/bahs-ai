import os
import logging
from datetime import datetime
import subprocess

try:
    from tqdm import tqdm
except ImportError:
    tqdm = None

NOME_SCRIPT = "02_BAHS_merge-originals-ALL"


# ==========================================
# CONFIGURAZIONE DINAMICA DELLA CPU
# ==========================================
def calcola_parametri_cpu_02_bahs_merge_originals_all():
    total_threads = os.cpu_count() or 4
    physical_cores = max(2, total_threads // 2)
    if total_threads <= 4:
        max_workers, threads_per_worker = 2, max(1, total_threads // 2)
    elif total_threads <= 8:
        max_workers, threads_per_worker = 4, 2
    else:
        max_workers, threads_per_worker = physical_cores, 4
    return total_threads, max_workers, threads_per_worker


TOTAL_THREADS, MAX_WORKERS, THREADS_PER_WORKER = calcola_parametri_cpu_02_bahs_merge_originals_all()


def pulisci_schermo_02_bahs_merge_originals_all():
    os.system('cls' if os.name == 'nt' else 'clear')


def configura_logging_02_bahs_merge_originals_all():
    cartella_log = "LOG"
    os.makedirs(cartella_log, exist_ok=True)
    timestamp_file = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    percorso_file_log = os.path.join(cartella_log, f"{NOME_SCRIPT}_{timestamp_file}.log")

    formato_log = logging.Formatter('[%(asctime)s] %(levelname)s: %(message)s', datefmt='%Y-%m-%d %H:%M:%S')
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)

    if not logger.handlers:
        handler_console = logging.StreamHandler()
        handler_console.setFormatter(formato_log)
        logger.addHandler(handler_console)

        handler_file = logging.FileHandler(percorso_file_log, encoding='utf-8')
        handler_file.setFormatter(formato_log)
        logger.addHandler(handler_file)

    logging.info(f"[{NOME_SCRIPT}] Sistema di log inizializzato. File salvato in: {percorso_file_log}")


def stampa_intestazione_02_bahs_merge_originals_all():
    print("=" * 84)
    print(f" INIZIO ELABORAZIONE - SCRIPT: {NOME_SCRIPT}")
    print(f" [Hardware Rilevato] Thread logici: {TOTAL_THREADS} | Worker max: {MAX_WORKERS} | Thread/Worker: {THREADS_PER_WORKER}")
    print("=" * 84)
    print()


def stampa_chiusura_02_bahs_merge_originals_all(successo=True):
    print()
    print("=" * 84)
    stato = "PROCESSO COMPLETATO CON SUCCESSO" if successo else "PROCESSO TERMINATO CON ERRORI"
    print(f" FINE ELABORAZIONE [{NOME_SCRIPT}] - {stato}")
    print("=" * 84)


def mostra_barra_avanzamento_02_bahs_merge_originals_all(iterabile, descrizione="Elaborazione", colore="blue", unita="file"):
    if tqdm is not None:
        return tqdm(iterabile, desc=descrizione, unit=unita, colour=colore)
    else:
        print(f"[{NOME_SCRIPT} - {descrizione}] In corso...")
        return iterabile


def rimuovi_file_temporanei_02_bahs_merge_originals_all(cartelle_da_controllare, file_lista_temp=None):
    logging.info(f"[{NOME_SCRIPT}] Pulizia dei file temporanei residui...")
    if file_lista_temp and os.path.exists(file_lista_temp):
        try:
            os.remove(file_lista_temp)
            logging.info(f"[{NOME_SCRIPT}] Rimosso file temporaneo: {file_lista_temp}")
        except Exception:
            pass

    for cartella in cartelle_da_controllare:
        if os.path.exists(cartella):
            for file in os.listdir(cartella):
                percorso_elem = os.path.join(cartella, file)
                try:
                    if os.path.isfile(percorso_elem) or os.path.islink(percorso_elem):
                        os.remove(percorso_elem)
                except Exception:
                    pass
            logging.info(f"[{NOME_SCRIPT}] Cartella temporanea '{cartella}' svuotata.")


def unisci_video_ffmpeg_02_bahs_merge_originals_all(cartella_input="IN", cartella_output="OUT", cartella_tmp="TMP", nome_file_output="video_finale.mp4"):
    pulisci_schermo_02_bahs_merge_originals_all()
    stampa_intestazione_02_bahs_merge_originals_all()
    configura_logging_02_bahs_merge_originals_all()

    successo_processo = True
    file_lista_temp = os.path.join(cartella_tmp, "filelist_02_bahs_merge_originals_all.txt")

    try:
        logging.info(f"[{NOME_SCRIPT}] Avvio procedura di unione rapida FFmpeg dalla cartella '{cartella_input}'.")

        if not os.path.exists(cartella_input):
            logging.error(f"[{NOME_SCRIPT}] La cartella '{cartella_input}' non esiste.")
            successo_processo = False
            return

        os.makedirs(cartella_output, exist_ok=True)
        os.makedirs(cartella_tmp, exist_ok=True)

        percorso_output = os.path.join(cartella_output, nome_file_output)

        file_video = sorted([
            f for f in os.listdir(cartella_input)
            if f.lower().endswith(('.mp4', '.mov', '.avi', '.mkv'))
        ])

        if not file_video:
            logging.warning(f"[{NOME_SCRIPT}] Nessun file video trovato in '{cartella_input}'.")
            successo_processo = False
            return

        logging.info(f"[{NOME_SCRIPT}] Trovati {len(file_video)} video da unire in sequenza.")

        with open(file_lista_temp, "w", encoding="utf-8") as f:
            for file in mostra_barra_avanzamento_02_bahs_merge_originals_all(file_video, descrizione="Scansione Video", colore="blue", unita="file"):
                percorso_completo = os.path.abspath(os.path.join(cartella_input, file))
                f.write(f"file '{percorso_completo.replace(os.sep, '/')}'\n")
                logging.info(f"[{NOME_SCRIPT}] - Aggiunto alla sequenza: {file}")

        logging.info(f"[{NOME_SCRIPT}] Creato file temporaneo in '{file_lista_temp}'.")
        logging.info(f"[{NOME_SCRIPT}] Esecuzione unione istantanea tramite FFmpeg (Stream Copy)...")

        comando = [
            "ffmpeg",
            "-y",
            "-f", "concat",
            "-safe", "0",
            "-i", file_lista_temp,
            "-c", "copy",
            percorso_output
        ]

        if tqdm is not None:
            with tqdm(total=1, desc="Unione FFmpeg", unit="video", colour="green") as pbar_ffmpeg:
                processo = subprocess.run(comando, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
                pbar_ffmpeg.update(1)
        else:
            processo = subprocess.run(comando, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)

        if processo.returncode != 0:
            logging.error(f"[{NOME_SCRIPT}] Errore durante l'esecuzione di FFmpeg:\n{processo.stderr}")
            successo_processo = False
        else:
            logging.info(f"[{NOME_SCRIPT}] Video unito ed esportato con successo in: {percorso_output}")

    except Exception as e:
        logging.exception(f"[{NOME_SCRIPT}] Errore critico: {e}")
        successo_processo = False

    finally:
        rimuovi_file_temporanei_02_bahs_merge_originals_all([cartella_tmp], file_lista_temp)
        stampa_chiusura_02_bahs_merge_originals_all(successo=successo_processo)


if __name__ == "__main__":
    unisci_video_ffmpeg_02_bahs_merge_originals_all(
        cartella_input="IN",
        cartella_output="OUT",
        cartella_tmp="TMP",
        nome_file_output="video_finale.mp4"
    )