# 🚀 **Backup XML Watcher**  
Servizio Windows per backup automatico di file XML

---

![Windows Service](https://img.shields.io/badge/Windows-Service-blue.svg)  
![Python 3.8+](https://img.shields.io/badge/Python-3.8%2B-yellow?logo=python)  
![PyInstaller Ready](https://img.shields.io/badge/PyInstaller-Supported-green)  

---

## 📝 **Descrizione**

**Backup XML Watcher** è un servizio Windows che monitora una cartella e copia automaticamente ogni nuovo file `.xml` in una cartella di destinazione.  
Tutte le operazioni vengono tracciate su file di log con rotazione automatica, il tutto configurabile in modo semplice tramite file `config.ini`.

---

## 📦 **Indice**

- [🚀 **Backup XML Watcher**](#-backup-xml-watcher)
  - [📝 **Descrizione**](#-descrizione)
  - [📦 **Indice**](#-indice)
  - [✨ **Funzionalità**](#-funzionalità)
  - [⚙️ **Requisiti**](#️-requisiti)
  - [📁 **Struttura del progetto**](#-struttura-del-progetto)
  - [🛠️ **Configurazione**](#️-configurazione)
  - [🚦 **Come si usa**](#-come-si-usa)
    - [➊ **Esecuzione come servizio Windows**](#-esecuzione-come-servizio-windows)
    - [➋ **Test locale CLI**](#-test-locale-cli)
    - [➌ **Creazione dell’eseguibile con PyInstaller**](#-creazione-delleseguibile-con-pyinstaller)
  - [❓ **FAQ e risoluzione problemi**](#-faq-e-risoluzione-problemi)
  - [🔐 **Note di sicurezza**](#-note-di-sicurezza)
  - [📬 **Contatti e supporto**](#-contatti-e-supporto)

---

## ✨ **Funzionalità**

- ⏱️ **Monitoraggio continuo** della cartella sorgente (solo root, no sottocartelle)
- 📥 **Copia automatica** dei nuovi file `.xml` nella cartella di destinazione
- 🔁 **Gestione duplicati**: aggiunge suffisso numerico (`file.xml`, `file 1.xml`, ...)
- 🚫 **Esclusione file temporanei** (`~$...`, `.tmp`)
- 📝 **Log dettagliato** con rotazione automatica
- 🛠️ **Tutto configurabile** tramite `config.ini`
- 🪟 **Avvio/stop** da Service Manager di Windows o prompt

---

## ⚙️ **Requisiti**

- **Python 3.8 o superiore** (consigliato)
- **Windows** (qualsiasi versione server o desktop)
- **Librerie Python**:
  - `pywin32`
  - `watchdog`
  - `pyinstaller` (solo per creare EXE)

Installa tutto con:
```sh
pip install pywin32 watchdog pyinstaller
```

---

## 📁 **Struttura del progetto**

```
backup_service.py      # Servizio Windows (main)
backup_worker.py       # Worker: copia e monitoraggio
config.ini             # Configurazione (cartelle e log)
README.md              # Questa documentazione
```

---

## 🛠️ **Configurazione**

Modifica il file `config.ini` secondo le tue esigenze:

```
[paths]
source_dir = C:\source\folder          ; Cartella da monitorare (solo root)
dest_dir = C:\destination\folder       ; Cartella di destinazione
log_dir = C:\logs                      ; Dove salvare i log

[logging]
log_file = backup.log                  ; Nome file di log
log_max_bytes = 1048576                ; 1 MB per file di log
log_backup_count = 5                   ; Quanti file di log (oltre al principale)
```

---

## 🚦 **Come si usa**

### ➊ **Esecuzione come servizio Windows**

1. **Prepara la cartella**: assicurati che `backup_service.py`, `backup_worker.py` e `config.ini` siano insieme.
2. **Configura** il file `config.ini`.
3. **Apri un prompt come amministratore** e installa il servizio:
   ```sh
   python backup_service.py install
   ```
4. **Avvia il servizio**:
   ```sh
   python backup_service.py start
   ```
5. **Stoppa o rimuovi** quando vuoi:
   ```sh
   python backup_service.py stop
   python backup_service.py remove
   ```

> 📝 **Nota:** Il servizio cerca sempre `config.ini` e `backup_worker.py` nella stessa cartella dell’eseguibile.

---

### ➋ **Test locale CLI**

1. Apri `backup_worker.py` in VSCode.
2. Lancialo direttamente:
   ```sh
   python backup_worker.py
   ```
3. Verrà usata la stessa configurazione di `config.ini`.  
   Ferma con `CTRL+C` quando vuoi.

---

### ➌ **Creazione dell’eseguibile con PyInstaller**

Vuoi distribuire il servizio senza installare Python? Segui questi passi:

1. **Installa PyInstaller** (se non già fatto):
   ```sh
   pip install pyinstaller
   ```
2. **Crea l’eseguibile**:
   ```sh
   pyinstaller --onefile --hidden-import=win32timezone backup_service.py
   ```
   - `--onefile`: crea un unico `.exe`
   - `--hidden-import=win32timezone`: necessario per i servizi Windows

3. **Distribuisci** i file:
   - Copia `dist\backup_service.exe`, `backup_worker.py` e `config.ini` sulla macchina target.
   - Tutti i percorsi nella config devono essere assoluti o relativi alla cartella dell’eseguibile.

4. **Gestione servizio da EXE**:
   ```sh
   backup_service.exe install
   backup_service.exe start
   ```

   Per stop/rimozione:
   ```sh
   backup_service.exe stop
   backup_service.exe remove
   ```

> ⚠️ **IMPORTANTE:**  
> - `config.ini` e `backup_worker.py` DEVONO essere accanto all’eseguibile!
> - I log vanno dove indicato in `log_dir` della config.

---

## ❓ **FAQ e risoluzione problemi**

- **Il servizio non parte?**
  - Esegui il prompt come amministratore.
  - Controlla i percorsi in `config.ini`.
  - Consulta il log (cartella `log_dir`).

- **Il log non viene creato?**
  - Verifica che la cartella `log_dir` esista e sia scrivibile.
  - Controlla i permessi dell’utente del servizio.

- **Nessun file viene copiato?**
  - Solo file `.xml` nella root di `source_dir` vengono gestiti.
  - File temporanei (`~$`, `.tmp`) vengono ignorati.

- **Voglio cambiare la configurazione:**
  - Stoppa il servizio, modifica `config.ini`, riavvia il servizio.

- **Ho cambiato la posizione del servizio:**
  - Ricordati di spostare anche `backup_worker.py` e `config.ini`.

---

## 🔐 **Note di sicurezza**

- Il servizio lavora con i permessi dell’utente con cui viene avviato.
- I percorsi possono essere assoluti o relativi, ma in produzione è meglio usare percorsi assoluti.

---

## 📬 **Contatti e supporto**

Hai bisogno di aiuto, vuoi segnalare bug o suggerimenti?  
Apri una issue su GitHub oppure contatta il maintainer del progetto!

---

<div align="center">
  <b>Backup XML Watcher</b> - Semplice. Affidabile. Windows Ready. <br>
  🗂️🛡️📝
</div>