import os
import cv2
from pathlib import Path
import time
import ctypes
import logging
from datetime import datetime

try:
    from tqdm import tqdm
except ImportError:
    tqdm = None

NOME_SCRIPT = "03_BAHS_identify-timestamps-ALL"


# ==========================================
# CONFIGURAZIONE DINAMICA DELLA CPU
# ==========================================
def calcola_parametri_cpu_03_bahs_identify_timestamps_all():
    total_threads = os.cpu_count() or 4
    physical_cores = max(2, total_threads // 2)
    if total_threads <= 4:
        max_workers, threads_per_worker = 2, max(1, total_threads // 2)
    elif total_threads <= 8:
        max_workers, threads_per_worker = 4, 2
    else:
        max_workers, threads_per_worker = physical_cores, 4
    return total_threads, max_workers, threads_per_worker


TOTAL_THREADS, MAX_WORKERS, THREADS_PER_WORKER = calcola_parametri_cpu_03_bahs_identify_timestamps_all()


class TqdmLoggingHandler_03_bahs_identify_timestamps_all(logging.Handler):
    """Invia i log su console tramite tqdm.write per non sovrapporsi alla barra."""

    def __init__(self, level=logging.NOTSET):
        super().__init__(level)

    def emit(self, record):
        try:
            msg = self.format(record)
            if tqdm is not None:
                tqdm.write(msg)
            else:
                print(msg)
        except Exception:
            self.handleError(record)


def pulisci_schermo_03_bahs_identify_timestamps_all():
    os.system('cls' if os.name == 'nt' else 'clear')


def configura_logging_03_bahs_identify_timestamps_all():
    cartella_log = "LOG"
    os.makedirs(cartella_log, exist_ok=True)
    timestamp_file = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    percorso_file_log = os.path.join(cartella_log, f"{NOME_SCRIPT}_{timestamp_file}.log")

    formato_log = logging.Formatter('[%(asctime)s] %(levelname)s: %(message)s', datefmt='%Y-%m-%d %H:%M:%S')
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)

    if logger.hasHandlers():
        logger.handlers.clear()

    handler_console = TqdmLoggingHandler_03_bahs_identify_timestamps_all()
    handler_console.setFormatter(formato_log)
    logger.addHandler(handler_console)

    handler_file = logging.FileHandler(percorso_file_log, encoding='utf-8')
    handler_file.setFormatter(formato_log)
    logger.addHandler(handler_file)

    logging.info(f"[{NOME_SCRIPT}] Sistema di log inizializzato. File salvato in: {percorso_file_log}")


def stampa_intestazione_03_bahs_identify_timestamps_all():
    print("=" * 80)
    print(f" INIZIO ELABORAZIONE - SCRIPT: {NOME_SCRIPT}")
    print(f" [Hardware Rilevato] Thread logici: {TOTAL_THREADS} | Worker max: {MAX_WORKERS} | Thread/Worker: {THREADS_PER_WORKER}")
    print("=" * 80)
    print()


def stampa_chiusura_03_bahs_identify_timestamps_all(successo=True):
    print()
    print("=" * 80)
    stato = "PROCESSO COMPLETATO CON SUCCESSO" if successo else "PROCESSO TERMINATO CON ERRORI"
    print(f" FINE ELABORAZIONE [{NOME_SCRIPT}] - {stato}")
    print("=" * 80)


def seconds_to_time_str_03_bahs_identify_timestamps_all(seconds):
    seconds = max(0.0, float(seconds))
    mins = int(seconds // 60)
    secs = int(seconds % 60)
    if mins >= 60:
        hours = mins // 60
        mins = mins % 60
        return f"{hours:02d}:{mins:02d}:{secs:02d}"
    return f"{mins:02d}:{secs:02d}"


def parse_speed_03_bahs_identify_timestamps_all(raw_input, default_speed=1.5):
    cleaned = raw_input.strip()
    if not cleaned:
        return float(default_speed), True

    normalized = cleaned.lower().rstrip("x").strip().replace(",", ".")
    try:
        value = float(normalized)
        if value <= 0:
            logging.warning(f"[{NOME_SCRIPT}] Velocità non positiva ('{raw_input}'). Imposto 1.0x.")
            return 1.0, False
        return value, True
    except ValueError:
        logging.warning(f"[{NOME_SCRIPT}] Valore velocità non valido ('{raw_input}'). Imposto {default_speed}x.")
        return float(default_speed), False


def put_contrasted_text_03_bahs_identify_timestamps_all(frame, text, org, font_scale, color, thickness=2):
    cv2.putText(frame, text, org, cv2.FONT_HERSHEY_SIMPLEX, font_scale, (0, 0, 0), thickness + 2, cv2.LINE_AA)
    cv2.putText(frame, text, org, cv2.FONT_HERSHEY_SIMPLEX, font_scale, color, thickness, cv2.LINE_AA)


def draw_overlay_03_bahs_identify_timestamps_all(frame, current_sec, total_sec, speed, paused, recorded_times, flash_timer, session_label):
    h, w, _ = frame.shape
    put_contrasted_text_03_bahs_identify_timestamps_all(frame, f"Sessione: {session_label}", (20, 45), 0.9, (0, 255, 255), 2)

    time_str = seconds_to_time_str_03_bahs_identify_timestamps_all(current_sec)
    speed_label = f"{speed:g}x"
    status_text = "PAUSA (Premi P per riprendere)" if paused else f"IN RIPRODUZIONE ({speed_label})"
    status_color = (0, 165, 255) if paused else (0, 255, 0)

    put_contrasted_text_03_bahs_identify_timestamps_all(frame, f"Tempo: {time_str}", (20, 90), 0.9, (255, 255, 255), 2)
    put_contrasted_text_03_bahs_identify_timestamps_all(frame, status_text, (20, 135), 0.7, status_color, 2)
    put_contrasted_text_03_bahs_identify_timestamps_all(frame, f"Canestri registrati: {len(recorded_times)}", (20, 185), 0.7, (0, 255, 255), 2)

    start_idx = max(0, len(recorded_times) - 6)
    y_offset = 225
    for i, t in enumerate(recorded_times[start_idx:], start=start_idx + 1):
        text_item = f"[{i}] Canestro: {t}"
        put_contrasted_text_03_bahs_identify_timestamps_all(frame, text_item, (20, y_offset), 0.65, (255, 255, 0), 2)
        y_offset += 35

    if time.time() < flash_timer:
        put_contrasted_text_03_bahs_identify_timestamps_all(frame, "CANESTRO REGISTRATO!", (w // 2 - 320, h // 2), 1.4, (0, 255, 0), 3)

    bar_x, bar_y, bar_w, bar_h = 30, h - 85, w - 60, 16
    progress = min(1.0, max(0.0, current_sec / total_sec)) if total_sec > 0 else 0
    filled_w = int(bar_w * progress)

    cv2.rectangle(frame, (bar_x, bar_y), (bar_x + bar_w, bar_y + bar_h), (50, 50, 50), -1)
    cv2.rectangle(frame, (bar_x, bar_y), (bar_x + filled_w, bar_y + bar_h), (0, 200, 0), -1)
    cv2.rectangle(frame, (bar_x, bar_y), (bar_x + bar_w, bar_y + bar_h), (255, 255, 255), 1)

    total_str = seconds_to_time_str_03_bahs_identify_timestamps_all(total_sec)
    progress_text = f"Progresso Elaborazione: {time_str} / {total_str} ({int(progress * 100)}%)"
    put_contrasted_text_03_bahs_identify_timestamps_all(frame, progress_text, (bar_x, bar_y - 12), 0.6, (255, 255, 255), 2)
    put_contrasted_text_03_bahs_identify_timestamps_all(frame, "[BARRA SPAZIO]: Canestro | [P]: Pausa | [F/R]: Avanti/Indietro 5s | [Q]: Salva ed Esci", (30, h - 25), 0.6, (0, 255, 255), 2)

    return frame


def record_timestamps_03_bahs_identify_timestamps_all():
    pulisci_schermo_03_bahs_identify_timestamps_all()
    stampa_intestazione_03_bahs_identify_timestamps_all()
    configura_logging_03_bahs_identify_timestamps_all()

    successo_processo = True
    dir_in = Path("OUT")
    dir_in.mkdir(exist_ok=True)

    try:
        logging.info(f"[{NOME_SCRIPT}] Avvio procedura di identificazione timestamp e analisi video.")
        session_label = input("🏷️ Inserisci un'etichetta/nome per la sessione [Default: campionato_squadra]: ").strip()
        if not session_label:
            session_label = "campionato_squadra"
        safe_label = "".join(c if c.isalnum() or c in ('_', '-') else '_' for c in session_label)

        video_name = input("📁 Inserisci il nome del video nella cartella 'OUT' [Default: video_finale.mp4]: ").strip()
        if not video_name:
            video_name = "video_finale.mp4"

        video_path = dir_in / video_name
        if not video_path.exists():
            logging.error(f"[{NOME_SCRIPT}] File video non trovato in: {video_path.absolute()}")
            successo_processo = False
            return

        speed_input = input("🚀 Velocità di riproduzione (es. 1, 1.5, 2, 4, o 8) [Default: 1.5]: ")
        speed, _ = parse_speed_03_bahs_identify_timestamps_all(speed_input, default_speed=1.5)

        cap = cv2.VideoCapture(str(video_path))
        if not cap.isOpened():
            logging.error(f"[{NOME_SCRIPT}] Impossibile aprire il flusso video: {video_path}")
            successo_processo = False
            return

        fps = cap.get(cv2.CAP_PROP_FPS)
        if fps <= 0:
            fps = 25.0

        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        total_sec = total_frames / fps if fps > 0 else 0

        logging.info(
            f"[{NOME_SCRIPT}] Video: '{video_name}' | FPS: {fps:.2f} | Frame totali: {total_frames} | "
            f"Velocità impostata: {speed:g}x"
        )

        txt_path = dir_in / "timestamps.txt"
        custom_txt_path = dir_in / f"timestamps_{safe_label}.txt"

        print("\n🎮 GUIDA CONTROLLI DA TASTIERA:")
        print("   [BARRA SPAZIATRICE] -> 🎯 Registra | [P] -> ⏸️ Pausa | [F/R] -> ⏩/⏪ 5s | [Q] -> 💾 Esci")
        input("Premi [INVIO] per aprire il video a schermo intero e iniziare subito... ")

        recorded_times = []
        paused = False
        flash_timer = 0
        window_title = f"Player Analisi [{NOME_SCRIPT}] - {session_label} ({speed:g}x)"

        cv2.namedWindow(window_title, cv2.WINDOW_NORMAL)
        cv2.setWindowProperty(window_title, cv2.WND_PROP_FULLSCREEN, cv2.WINDOW_FULLSCREEN)

        ret, current_frame = cap.read()
        if not ret:
            logging.error(f"[{NOME_SCRIPT}] Impossibile leggere il primo fotogramma.")
            successo_processo = False
            return

        current_frame_idx = 0
        current_sec = 0.0

        # Mostra subito il primo fotogramma e forza il focus sulla finestra
        display_frame = current_frame.copy()
        display_frame = draw_overlay_03_bahs_identify_timestamps_all(
            display_frame, current_sec, total_sec, speed, paused, recorded_times, flash_timer, session_label
        )
        cv2.imshow(window_title, display_frame)
        cv2.waitKey(1)

        if os.name == 'nt':
            try:
                hwnd = ctypes.windll.user32.FindWindowW(None, window_title)
                if hwnd:
                    ctypes.windll.user32.SetForegroundWindow(hwnd)
            except Exception:
                pass

        pbar = None
        if tqdm is not None and total_frames > 0:
            pbar = tqdm(total=total_frames, desc="Analisi Video", unit="frame", colour="blue")

        # Ancoraggio temporale reale per mantenere la velocità esatta (1x, 1.5x, 2x, 4x, 8x...)
        anchor_wall_time = time.perf_counter()
        anchor_video_sec = 0.0

        try:
            while cap.isOpened():
                if not paused:
                    now = time.perf_counter()
                    expected_video_sec = anchor_video_sec + (now - anchor_wall_time) * speed
                    target_frame_idx = int(expected_video_sec * fps)

                    if total_frames > 0 and target_frame_idx >= total_frames:
                        break

                    frames_to_advance = target_frame_idx - current_frame_idx

                    if frames_to_advance > 0:
                        # Se dobbiamo saltare più frame per stare al passo (es. 4x / 8x), usiamo grab() per quelli intermedi
                        grabbed_ok = True
                        for _ in range(frames_to_advance - 1):
                            if not cap.grab():
                                grabbed_ok = False
                                break
                        if not grabbed_ok:
                            break

                        if not cap.grab():
                            break
                        ret, frame = cap.retrieve()
                        if not ret or frame is None:
                            break

                        current_frame = frame
                        current_frame_idx = target_frame_idx
                        current_sec = current_frame_idx / fps

                if pbar is not None:
                    target_pbar = min(total_frames, current_frame_idx + 1)
                    if target_pbar > pbar.n:
                        pbar.update(target_pbar - pbar.n)
                    elif target_pbar < pbar.n:
                        pbar.n = max(0, target_pbar)
                        pbar.refresh()

                display_frame = current_frame.copy()
                display_frame = draw_overlay_03_bahs_identify_timestamps_all(
                    display_frame, current_sec, total_sec, speed, paused, recorded_times, flash_timer, session_label
                )
                cv2.imshow(window_title, display_frame)

                # Calcola esattamente quanti millisecondi mancano al prossimo fotogramma
                if paused:
                    wait_ms = 30
                else:
                    next_frame_video_sec = (current_frame_idx + 1) / fps
                    time_until_next_frame = (next_frame_video_sec - anchor_video_sec) / speed - (time.perf_counter() - anchor_wall_time)
                    wait_ms = max(1, int(time_until_next_frame * 1000))

                key = cv2.waitKey(wait_ms) & 0xFF
                if key in (ord('q'), ord('Q')):
                    break
                elif key in (ord('p'), ord('P')):
                    paused = not paused
                    if not paused:
                        # Riallinea l'ancora temporale quando esce dalla pausa
                        anchor_wall_time = time.perf_counter()
                        anchor_video_sec = current_sec
                elif key in (ord('f'), ord('F')):
                    target_sec = min(total_sec, current_sec + 5.0)
                    target_frame = int(round(target_sec * fps))
                    if total_frames > 0:
                        target_frame = min(total_frames - 1, max(0, target_frame))
                    cap.set(cv2.CAP_PROP_POS_FRAMES, target_frame)
                    ret, frame = cap.read()
                    if ret:
                        current_frame = frame
                        current_frame_idx = target_frame
                        current_sec = current_frame_idx / fps
                        anchor_wall_time = time.perf_counter()
                        anchor_video_sec = current_sec
                elif key in (ord('r'), ord('R')):
                    target_sec = max(0.0, current_sec - 5.0)
                    target_frame = max(0, int(round(target_sec * fps)))
                    cap.set(cv2.CAP_PROP_POS_FRAMES, target_frame)
                    ret, frame = cap.read()
                    if ret:
                        current_frame = frame
                        current_frame_idx = target_frame
                        current_sec = current_frame_idx / fps
                        anchor_wall_time = time.perf_counter()
                        anchor_video_sec = current_sec
                elif key == 32:
                    time_str = seconds_to_time_str_03_bahs_identify_timestamps_all(current_sec)
                    if time_str not in recorded_times:
                        recorded_times.append(time_str)
                        flash_timer = time.time() + 0.6
                        logging.info(f"[{NOME_SCRIPT}] Registrato timestamp canestro: {time_str}")
                        if pbar is not None:
                            pbar.set_postfix({"canestri": len(recorded_times)})
        finally:
            if pbar is not None:
                pbar.close()

        cap.release()
        cv2.destroyAllWindows()

        if recorded_times:
            file_content = f"# Sessione: {session_label} | Script: {NOME_SCRIPT}\n"
            for t in recorded_times:
                file_content += f"{t}\n"
            with open(txt_path, "w", encoding="utf-8") as f:
                f.write(file_content)
            with open(custom_txt_path, "w", encoding="utf-8") as f:
                f.write(file_content)
            logging.info(f"[{NOME_SCRIPT}] Salvati {len(recorded_times)} timestamp in '{txt_path}' e '{custom_txt_path}'.")
        else:
            logging.warning(f"[{NOME_SCRIPT}] Nessun timestamp registrato durante la sessione.")

    except Exception as e:
        logging.exception(f"[{NOME_SCRIPT}] Errore critico: {e}")
        successo_processo = False
    finally:
        stampa_chiusura_03_bahs_identify_timestamps_all(successo=successo_processo)


if __name__ == "__main__":
    record_timestamps_03_bahs_identify_timestamps_all()