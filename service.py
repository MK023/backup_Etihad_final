"""
Modulo: backup_service.py

Definisce il servizio Windows (ServiceFramework) che gestisce il ciclo di vita del backup:
- Legge la configurazione da config.ini (cartelle e log).
- Crea il logger rotativo nella directory scelta.
- Avvia, ferma e monitora il worker in un thread separato.
- Permette install/start/stop del servizio tramite pywin32.
"""

import win32timezone
import win32serviceutil
import win32service
import win32event
import servicemanager
import threading
import configparser
import os
import sys
import logging
from logging.handlers import RotatingFileHandler
from backup_worker import start_backup_worker

def setup_logger(log_dir, log_file, max_bytes, backup_count):
    """
    Crea e configura un logger rotativo su file nella directory richiesta.

    Args:
        log_dir (str): Cartella dove creare i file di log.
        log_file (str): Nome del file di log.
        max_bytes (int): Dimensione massima del file di log prima della rotazione.
        backup_count (int): Numero massimo di file di log di backup.

    Returns:
        logging.Logger: Oggetto logger configurato.
    """
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)
    full_log_path = os.path.join(log_dir, log_file)
    logger = logging.getLogger("BackupService")
    logger.setLevel(logging.INFO)
    handler = RotatingFileHandler(
        full_log_path,
        maxBytes=max_bytes,
        backupCount=backup_count
    )
    formatter = logging.Formatter(
        '%(asctime)s %(levelname)s %(message)s',
        '%Y-%m-%d %H:%M:%S'
    )
    handler.setFormatter(formatter)
    # Aggiunge l'handler solo una volta per evitare duplicati in caso di restart
    if not logger.handlers:
        logger.addHandler(handler)
    return logger

class BackupService(win32serviceutil.ServiceFramework):
    """
    Servizio Windows per il backup automatico dei file XML.
    - Legge da config.ini le cartelle di lavoro e la directory dei log.
    - Crea il logger rotativo.
    - Avvia il worker di backup in un thread e ne gestisce lo stop.
    """

    _svc_name_ = "BackupXMLWatcher"
    _svc_display_name_ = "Backup XML Watcher"
    _svc_description_ = (
        "Servizio che effettua il backup automatico dei file XML "
        "da una cartella sorgente a una di destinazione."
    )

    def __init__(self, args):
        """
        Inizializza il servizio:
        - Legge la configurazione dal file config.ini.
        - Prepara logger e worker.
        """
        win32serviceutil.ServiceFramework.__init__(self, args)
        self.stop_event = threading.Event()
        config = configparser.ConfigParser()

        # Determina la cartella dove si trova config.ini (compatibile con exe e script)
        if getattr(sys, 'frozen', False):
            base_path = os.path.dirname(sys.executable)
        else:
            base_path = os.path.dirname(__file__)
        config_path = os.path.join(base_path, 'config.ini')
        config.read(config_path)

        # Leggi le cartelle e i parametri log dal file di configurazione
        self.src = config.get('paths', 'source_dir')
        self.dst = config.get('paths', 'dest_dir')
        self.log_dir = config.get('paths', 'log_dir')
        self.log_file = config.get('logging', 'log_file')
        self.log_max_bytes = config.getint('logging', 'log_max_bytes')
        self.log_backup_count = config.getint('logging', 'log_backup_count')

        # Prepara logger rotativo sulla directory desiderata
        self.logger = setup_logger(self.log_dir, self.log_file, self.log_max_bytes, self.log_backup_count)
        self.worker_thread = None

    def SvcStop(self):
        """
        Metodo chiamato da Windows per fermare il servizio.
        Logga la richiesta e segnala al worker di terminare.
        """
        self.logger.info("Richiesta di stop del servizio Windows...")
        self.ReportServiceStatus(win32service.SERVICE_STOP_PENDING)
        self.stop_event.set()

    def SvcDoRun(self):
        """
        Metodo principale del servizio, lanciato da Windows all'avvio.
        - Logga l'avvio.
        - Avvia il worker in un thread separato.
        - Attende la terminazione del thread (o lo stop).
        """
        self.logger.info("Servizio Windows avviato.")
        servicemanager.LogMsg(
            servicemanager.EVENTLOG_INFORMATION_TYPE,
            servicemanager.PYS_SERVICE_STARTED,
            (self._svc_name_, '')
        )
        try:
            self.worker_thread = threading.Thread(
                target=start_backup_worker,
                args=(self.src, self.dst, self.logger),
                kwargs={'count_interval': 60, 'external_stop_event': self.stop_event},
                daemon=True
            )
            self.worker_thread.start()
            self.worker_thread.join()
        except Exception as e:
            self.logger.error(f"Errore nel servizio: {e}")
        self.logger.info("Servizio Windows terminato.")

if __name__ == '__main__':
    # Permette di installare, avviare, fermare, rimuovere il servizio da linea di comando.
    if len(sys.argv) == 1:
        # Avvio come servizio reale (da Windows)
        servicemanager.Initialize()
        servicemanager.PrepareToHostSingle(BackupService)
        servicemanager.StartServiceCtrlDispatcher()
    else:
        # Gestione dei comandi da shell: install, start, stop, remove...
        win32serviceutil.HandleCommandLine(BackupService)