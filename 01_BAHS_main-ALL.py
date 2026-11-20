import os
import sys
import logging
import shutil
import subprocess
from datetime import datetime

try:
    from tqdm import tqdm
except ImportError:
    tqdm = None

SCRIPT_NAME = "01_BAHS_main-ALL"

# Elenco di tutte le cartelle standard utilizzate dai vari moduli della suite
REQUIRED_DIRECTORIES = ["IN", "OUT", "FINAL", "TMP", "LOG", "MUSIC", "EXTRA"]

# Cartelle soggette a pulizia automatica con l'opzione 1
CLEANUP_DIRECTORIES = ["FINAL", "OUT", "TMP"]

# Estensioni video supportate dai controlli
SUPPORTED_VIDEO_EXTS = (".mp4", ".mov", ".avi", ".mkv", ".m4v", ".webm")

# Colori ANSI
VERDE_LAMP = "\033[1m\033[5m\033[92m"
VERDE = "\033[92m"
CIANO = "\033[96m"
GIALLO = "\033[93m"
ROSSO_LAMP = "\033[1m\033[5m\033[91m"
GRIGIO = "\033[90m"
BIANCO_BOLD = "\033[1m\033[97m"
RESET = "\033[0m"


def abilita_colori_terminale_01_bahs_main_all():
    """Abilita le sequenze ANSI su Windows."""
    if os.name == "nt":
        os.system("")


# ==========================================
# CONFIGURAZIONE DINAMICA DELLA CPU
# ==========================================
def calcola_parametri_cpu_01_bahs_main_all():
    total_threads = os.cpu_count() or 4
    physical_cores = max(2, total_threads // 2)
    if total_threads <= 4:
        max_workers, threads_per_worker = 2, max(1, total_threads // 2)
    elif total_threads <= 8:
        max_workers, threads_per_worker = 4, 2
    else:
        max_workers, threads_per_worker = physical_cores, 4
    return total_threads, max_workers, threads_per_worker


TOTAL_THREADS, MAX_WORKERS, THREADS_PER_WORKER = calcola_parametri_cpu_01_bahs_main_all()


def pulisci_schermo_01_bahs_main_all():
    """Pulisce la console del terminale ad avvio script."""
    os.system("cls" if os.name == "nt" else "clear")


def setup_logging_01_bahs_main_all():
    """Configura la cartella LOG e il file di log associato alla sessione (creato solo su richiesta di elaborazione)."""
    log_dir = "LOG"
    os.makedirs(log_dir, exist_ok=True)
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    log_filename = os.path.join(log_dir, f"{SCRIPT_NAME}_{timestamp}.log")

    for handler in logging.root.handlers[:]:
        logging.root.removeHandler(handler)

    logging.basicConfig(
        filename=log_filename,
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
        encoding="utf-8",
    )
    return log_filename


def stampa_intestazione_01_bahs_main_all():
    """Stampa in modo chiaro l'INIZIO con il nome dello script e l'hardware rilevato."""
    print("=" * 78)
    print(f" {CIANO}INIZIO ELABORAZIONE - SCRIPT: {SCRIPT_NAME}{RESET}")
    print(f" {GIALLO}[Hardware Rilevato]{RESET} Thread logici: {TOTAL_THREADS} | Worker: {MAX_WORKERS} | Thread/Worker: {THREADS_PER_WORKER}")
    print("=" * 78)


def stampa_chiusura_01_bahs_main_all(successo=True):
    """Stampa in modo chiaro la FINE con il nome dello script e l'esito."""
    print("=" * 78)
    colore_stato = VERDE if successo else ROSSO_LAMP
    stato = "PROCESSO COMPLETATO CON SUCCESSO" if successo else "PROCESSO TERMINATO CON ERRORI"
    print(f" FINE ELABORAZIONE [{SCRIPT_NAME}] - {colore_stato}{stato}{RESET}")
    print("=" * 78)


def setup_directories_01_bahs_main_all():
    """Verifica la presenza delle cartelle nella dir root e le crea se non esistenti con barra di avanzamento."""
    print(f"\n{CIANO}[Fase 1]{RESET} Controllo e creazione cartelle di sistema nella directory root...")

    iterabile = REQUIRED_DIRECTORIES
    if tqdm is not None:
        iterabile = tqdm(REQUIRED_DIRECTORIES, desc="Verifica Cartelle", ncols=65, ascii=" #")

    for directory in iterabile:
        if not os.path.exists(directory):
            try:
                os.makedirs(directory)
            except Exception as e:
                print(f"   {ROSSO_LAMP}[X] Errore creazione cartella '{directory}': {e}{RESET}")


def check_input_videos_01_bahs_main_all():
    """Verifica la presenza di file video supportati nella cartella IN e suggerisce di inserirli se assenti."""
    print(f"\n{CIANO}[Fase 2]{RESET} Controllo presenza file video nella cartella 'IN'...")
    in_dir = "IN"

    if os.path.exists(in_dir):
        video_files = [f for f in os.listdir(in_dir) if f.lower().endswith(SUPPORTED_VIDEO_EXTS)]
        if not video_files:
            messaggio_lampeggiante = f"{ROSSO_LAMP}[!] Attenzione: Nessun file video valido ({', '.join(SUPPORTED_VIDEO_EXTS)}) trovato nella cartella 'IN'.{RESET}"
            print(f"   {messaggio_lampeggiante}")
            print(f"   {GIALLO}💡 SUGGERIMENTO:{RESET} Inserisci i file video (es. .mp4, .mov, ecc.) nella cartella 'IN' prima di avviare le attività.")
        else:
            print(f"   {VERDE}[✔] Trovati {len(video_files)} file video supportati nella cartella 'IN'.{RESET}")
    else:
        print(f"   {GIALLO}[!] Cartella 'IN' non trovata.{RESET}")


def check_ffmpeg_01_bahs_main_all():
    """Verifica disponibilità di FFmpeg e FFprobe nel sistema."""
    print(f"\n{CIANO}[Fase 3]{RESET} Verifica disponibilità di FFmpeg e FFprobe nel sistema...")
    if shutil.which("ffmpeg") is None or shutil.which("ffprobe") is None:
        print(f"   {ROSSO_LAMP}[!] Attenzione: FFmpeg o FFprobe non sono installati o non sono presenti nel PATH.{RESET}")
        return False
    else:
        print(f"   {VERDE}[✔] FFmpeg e FFprobe rilevati correttamente.{RESET}")
        return True


def pulisci_cartelle_lavoro_01_bahs_main_all():
    """Svuota e pulisce in automatico le cartelle di elaborazione (FINAL, OUT, TMP e log vecchi)."""
    print(f"\n{CIANO}🧹 Avvio pulizia automatica delle cartelle di lavoro...{RESET}")

    for directory in CLEANUP_DIRECTORIES:
        if os.path.exists(directory):
            try:
                for item in os.listdir(directory):
                    item_path = os.path.join(directory, item)
                    if os.path.isfile(item_path) or os.path.islink(item_path):
                        os.unlink(item_path)
                    elif os.path.isdir(item_path):
                        shutil.rmtree(item_path)
                print(f"   {VERDE}[✔] Cartella pulita con successo: '{directory}'{RESET}")
            except Exception as e:
                print(f"   {ROSSO_LAMP}[X] Errore durante la pulizia della cartella '{directory}': {e}{RESET}")
        else:
            os.makedirs(directory, exist_ok=True)
            print(f"   {GIALLO}[+] Cartella ricreata (perché inesistente): '{directory}'{RESET}")

    log_dir = "LOG"
    if os.path.exists(log_dir):
        try:
            for item in os.listdir(log_dir):
                item_path = os.path.join(log_dir, item)
                try:
                    if os.path.isfile(item_path):
                        os.unlink(item_path)
                except Exception:
                    pass
            print(f"   {VERDE}[✔] Cartella log pulita (file attivi esclusi): '{log_dir}'{RESET}")
        except Exception as e:
            print(f"   {ROSSO_LAMP}[X] Errore pulizia cartella '{log_dir}': {e}{RESET}")

    print(f"{VERDE}✨ Pulizia completata con successo!{RESET}\n")
    input("Premi [INVIO] per tornare al menu principale... ")


def _stampa_riga_voce(num, descrizione, script_file, base_dir, ultima_scelta):
    """Formatta in modo allineato una singola voce del menu con stato file ed eventuale badge ultima eseguita."""
    esiste = os.path.isfile(os.path.join(base_dir, script_file))
    stato_file = f"{VERDE}[OK]{RESET}" if esiste else f"{ROSSO_LAMP}[MANCANTE]{RESET}"

    if ultima_scelta == num:
        print(f" {VERDE_LAMP}{num:>2}. {descrizione:<36} ({script_file}){RESET} {stato_file} {VERDE_LAMP}[ULTIMA ESEGUITA]{RESET}")
    else:
        print(f" {BIANCO_BOLD}{num:>2}.{RESET} {descrizione:<36} {GRIGIO}({script_file}){RESET} {stato_file}")


def mostra_menu_principale_01_bahs_main_all(script_mapping, base_dir, ultima_scelta=None):
    """Mostra il menu suddiviso per fasi, allineato e con stato dei moduli."""
    sezione_preparazione = [
        ("2", "Unione video originali"),
        ("3", "Identifica timestamp canestri"),
        ("4", "Taglia clip originali"),
    ]

    sezione_finalizzazione = [
        ("5", "Converti clip REEL"),
        ("6", "Unisci clip 1080P / REEL"),
        ("7", "Aggiungi musica"),
        ("8", "Sovraimpressione testo REEL"),
        ("9", "Sovraimpressione testo 1080P"),
        ("10", "Sovraimpressione logo 1080P / REEL"),
    ]

    print("\n" + "=" * 86)
    print(f" {CIANO}🏀 BASKETBALL AUTOMATION HIGHLIGHTS SUITE (BAHS) - MENU PRINCIPALE{RESET}")
    print("=" * 86)
    print("")
    print(f" {GIALLO} [ 1 ]{RESET} {BIANCO_BOLD}Pulizia cartelle di lavoro{RESET} {GRIGIO}(FINAL, OUT, LOG, TMP){RESET}")
    print("")
    print("-" * 86)
    print(f" {CIANO}--- FASE 1: PREPARAZIONE E TAGLIO ---{RESET}")
    for num, descrizione in sezione_preparazione:
        _stampa_riga_voce(num, descrizione, script_mapping[num], base_dir, ultima_scelta)

    print(f"\n {CIANO}--- FASE 2: MONTAGGIO, AUDIO, TESTI E LOGO ---{RESET}")
    for num, descrizione in sezione_finalizzazione:
        _stampa_riga_voce(num, descrizione, script_mapping[num], base_dir, ultima_scelta)

    print("-" * 86)
    print("")
    print(f" {ROSSO_LAMP} [ 99 ]{RESET} {GIALLO}Esci dal programma{RESET}")
    print("")
    print("=" * 86)


def main_01_bahs_main_all():
    abilita_colori_terminale_01_bahs_main_all()
    pulisci_schermo_01_bahs_main_all()
    stampa_intestazione_01_bahs_main_all()

    successo_processo = True
    ultima_scelta_eseguita = None
    log_file = None
    base_dir = os.path.dirname(os.path.abspath(__file__))

    script_mapping = {
        "2": "02_BAHS_merge-originals-ALL.py",
        "3": "03_BAHS_identify-timestamps-ALL.py",
        "4": "04_BAHS_split-original-ALL.py",
        "5": "05_BAHS_convert-clips-REEL.py",
        "6": "06_BAHS_merge-clips-ALL.py",
        "7": "07_BAHS_add-music-overlay-ALL.py",
        "8": "08_BAHS_add-text-overlay-REEL.py",
        "9": "09_BAHS_add-text-overlay-1080P.py",
        "10": "10_BAHS_add-logo-overlay-ALL.py",
    }

    try:
        setup_directories_01_bahs_main_all()
        check_input_videos_01_bahs_main_all()
        check_ffmpeg_01_bahs_main_all()

        while True:
            mostra_menu_principale_01_bahs_main_all(
                script_mapping=script_mapping,
                base_dir=base_dir,
                ultima_scelta=ultima_scelta_eseguita,
            )
            raw_scelta = input(f"\n👉 {BIANCO_BOLD}Scelta{RESET} {GRIGIO}[1: Pulizia | 2-10: Script | 99: Esci]{RESET}: ")
            scelta = "".join(ch for ch in raw_scelta.strip() if ch.isdigit())

            if scelta == "1":
                pulisci_cartelle_lavoro_01_bahs_main_all()
                ultima_scelta_eseguita = None
            elif scelta in script_mapping:
                if not log_file:
                    log_file = setup_logging_01_bahs_main_all()
                    logging.info(f"INIZIO script principale {SCRIPT_NAME} (Thread CPU: {TOTAL_THREADS})")

                nome_script_target = script_mapping[scelta]
                script_path = os.path.join(base_dir, nome_script_target)

                if not os.path.isfile(script_path):
                    msg = f"File sottoscript non trovato: {script_path}"
                    print(f"\n{ROSSO_LAMP}[X] {msg}{RESET}")
                    logging.error(msg)
                    input("\nPremi [INVIO] per tornare al menu principale... ")
                    continue

                print(f"\n{CIANO}🚀 Avvio di {nome_script_target}...{RESET}\n")
                logging.info(f"Lancio sottoscript: {nome_script_target}")

                risultato = subprocess.run([sys.executable, script_path], cwd=base_dir)
                if risultato.returncode == 0:
                    ultima_scelta_eseguita = scelta
                    logging.info(f"Sottoscript {nome_script_target} completato con successo (code=0).")
                else:
                    print(f"\n{GIALLO}[!] Lo script {nome_script_target} è terminato con codice {risultato.returncode}.{RESET}")
                    logging.warning(f"Sottoscript {nome_script_target} terminato con codice {risultato.returncode}")

                input("\nPremi [INVIO] per tornare al menu principale... ")

            elif scelta == "99":
                print(f"\n{GIALLO}👋 Chiusura del programma di controllo. Arrivederci!{RESET}")
                if log_file:
                    logging.info("Chiusura manuale del sistema da parte dell'utente.")
                break
            else:
                print(f"\n{ROSSO_LAMP}[!] Scelta non valida ('{raw_scelta.strip()}'). Inserisci un'opzione corretta dal menu (1-10 oppure 99).{RESET}")

    except Exception as e:
        if log_file:
            logging.exception(f"Errore critico nello script principale: {e}")
        else:
            print(f"\n{ROSSO_LAMP}[X] Errore critico: {e}{RESET}")
        successo_processo = False
    finally:
        if log_file:
            print(f"\n{CIANO}📄 Report salvato in: {log_file}{RESET}")
            logging.info(f"FINE script principale {SCRIPT_NAME}")
        stampa_chiusura_01_bahs_main_all(successo=successo_processo)


if __name__ == "__main__":
    main_01_bahs_main_all()