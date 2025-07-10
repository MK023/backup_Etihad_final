"""
Modulo: backup_worker.py

Contiene la logica di monitoraggio e copia dei file XML dalla directory sorgente a quella di destinazione.
Pensato per essere importato e utilizzato da un servizio Windows oppure lanciato manualmente in un thread.
Tutte le operazioni vengono loggate tramite il logger passato come parametro.
"""

import os
import shutil
import time
import re
import logging
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler


class CopyHandler(FileSystemEventHandler):
    """
    Handler personalizzato per gli eventi watchdog.
    Si occupa di copiare i file .xml appena creati nella root della source_dir nella dest_dir.
    """
    def __init__(self, source_dir, dest_dir, logger):
        """
        Args:
            source_dir (str): Directory da monitorare.
            dest_dir (str): Directory di destinazione dei file copiati.
            logger (logging.Logger): Logger per tracciare tutte le operazioni.
        """
        self.source_dir = source_dir
        self.dest_dir = dest_dir
        self.logger = logger

    def on_created(self, event):
        """
        Callback chiamata da watchdog quando viene creato un file nella directory monitorata.
        Copia solo i file .xml presenti nella root (non nelle sottocartelle).
        """
        
        if event.is_directory:
            return

        rel_path = os.path.relpath(event.src_path, self.source_dir)
        if os.path.dirname(rel_path):
            # Ignora file in sottocartelle
            return

        if not event.src_path.lower().endswith('.xml'):
            return

        dest_path = os.path.join(self.dest_dir, os.path.basename(event.src_path))
        try:
            self.copy_file_safely(event.src_path, dest_path)
        except Exception as e:
            self.logger.error(f"Errore nella copia di {rel_path}: {e}")

    def copy_file_safely(self, src, dest, retries=3, delay=0.5):
        """
        Copia il file src in dest, aggiungendo un suffisso numerico se necessario.
        Ignora file temporanei (che iniziano con '~$' o terminano con '.tmp').
        Riprova la copia in caso di PermissionError.

        Args:
            src (str): Percorso del file di origine.
            dest (str): Percorso di destinazione.
            retries (int): Numero massimo di tentativi in caso di errore.
            delay (float): Attesa in secondi tra i tentativi.
        """
        base, ext = os.path.splitext(dest)
        new_dest = dest
        filename = os.path.basename(src)
        if filename.startswith('~$') or filename.endswith('.tmp'):
            self.logger.info(f"File temporaneo ignorato: {filename}")
            return
        count = 1
        while os.path.exists(new_dest):
            new_dest = f"{base} {count}{ext}"
            count += 1

        for attempt in range(retries):
            try:
                shutil.copy2(src, new_dest)
                self.logger.info(
                    f"File copiato: {os.path.relpath(src, self.source_dir)} -> {os.path.relpath(new_dest, self.dest_dir)}"
                )
                return
            except PermissionError as e:
                if attempt < retries - 1:
                    self.logger.warning(f"Permesso negato per {src}, ritento ({attempt+1})...")
                    time.sleep(delay)
                else:
                    self.logger.error(f"Permesso negato per {src} dopo {retries} tentativi: {e}")
            except Exception as e:
                self.logger.error(f"Errore nella copia di {src}: {e}")
                return

def list_files_windows_style(directory, extension=".xml"):
    """
    Restituisce la lista dei file nella directory principale, ordinata in stile Windows:
    base.xml, base1.xml, base2.xml, ecc.

    Args:
        directory (str): Cartella dove elencare i file.
        extension (str): Estensione dei file da considerare (default .xml).

    Returns:
        list[str]: Lista dei file ordinati.
    """
    files = [
        f for f in os.listdir(directory)
        if os.path.isfile(os.path.join(directory, f)) and f.lower().endswith(extension)
    ]
    def extract_base_and_num(filename):
        m = re.match(r"^(.*?)(\d+)?(\.[^.]+)$", filename)
        if m:
            base, num, ext = m.groups()
            num = int(num) if num else 0
            return (base, num, ext)
        else:
            return (filename, 0, "")

    files_sorted = sorted(
        files,
        key=lambda f: extract_base_and_num(f)
    )
    return files_sorted

def count_files_in_directory(directory):
    """
    Conta il numero totale di file XML (solo nella root) in una directory.

    Args:
        directory (str): Cartella da analizzare.

    Returns:
        tuple: (numero file, lista dei file ordinati)
    """
    files = list_files_windows_style(directory)
    return len(files), files

def log_counts(source_dir, dest_dir, logger):
    """
    Logga il conteggio e la lista dei file nelle directory sorgente e destinazione.

    Args:
        source_dir (str): Directory di origine.
        dest_dir (str): Directory di destinazione.
        logger (logging.Logger): Logger da utilizzare.
    """
    src_count, src_files = count_files_in_directory(source_dir)
    dst_count, dst_files = count_files_in_directory(dest_dir)
    logger.info(f"File in source: {src_count} | File in dest: {dst_count}")
    logger.info(f"Lista file source: {src_files}")
    logger.info(f"Lista file dest: {dst_files}")

def start_backup_worker(source_dir, dest_dir, logger, count_interval=60, external_stop_event=None):
    """
    Avvia il backup worker che monitora source_dir e copia i nuovi file XML in dest_dir.

    Args:
        source_dir (str): Directory di origine.
        dest_dir (str): Directory di destinazione.
        logger (logging.Logger): Logger da utilizzare.
        count_interval (int): Intervallo in secondi tra un log di conteggio e l'altro.
        external_stop_event (threading.Event): Evento di stop per terminare il worker.
    """
    if not os.path.isdir(source_dir):
        logger.error(f"La directory sorgente non esiste: {source_dir}")
        return
    if not os.path.isdir(dest_dir):
        logger.error(f"La directory di destinazione non esiste: {dest_dir}")
        return

    logger.info(f"Backup worker avviato: {source_dir} -> {dest_dir}")
    event_handler = CopyHandler(source_dir, dest_dir, logger)
    observer = Observer()
    observer.schedule(event_handler, source_dir, recursive=False)
    observer.start()
    try:
        last_check = time.time()
        while True:
            time.sleep(0.1)
            if external_stop_event and external_stop_event.is_set():
                break
            if time.time() - last_check > count_interval:
                log_counts(source_dir, dest_dir, logger)
                last_check = time.time()
    finally:
        observer.stop()
        observer.join()
        logger.info("Backup worker terminato")