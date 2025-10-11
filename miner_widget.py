#!/usr/bin/env python3
"""
Miner Widget - macOS Menu Bar Widget pro monitoring mining pool.

Tento modul poskytuje widget pro menu bar, který zobrazuje:
- Aktuální hash rate z pool.braiins.com
- Teplotu z Tuya API
- Automatické aktualizace každých 5 minut
- Logování do souboru s rotací

Author: Jan
Version: 1.0
"""

import os
import rumps
import requests
import threading
import time
import logging
import socket
import subprocess
import urllib3
from logging.handlers import RotatingFileHandler
from dotenv import load_dotenv

# Import lokálních modulů
import get_api

# Načtení .env proměnných
load_dotenv()

TOKEN = os.getenv("TOKEN")
COIN = os.getenv("COIN", "btc")
BASE_URL = os.getenv("BASE_URL", "https://pool.braiins.com")
UPDATE_INTERVAL = int(os.getenv("UPDATE_INTERVAL", 300))
MAX_RETRIES = int(os.getenv("MAX_RETRIES", 3))
RETRY_DELAY = int(os.getenv("RETRY_DELAY", 5))
HEADERS = {"Pool-Auth-Token": TOKEN} if TOKEN else {}

os.environ['LSUIElement'] = '1'

class Logger:
    """
    Singleton logger třída pro centralizované logování.
    
    Zajišťuje konzistentní logování napříč celou aplikací
    s rotací log souborů a výstupem do konzole.
    """
    
    _instance = None
    _initialized = False

    def __new__(cls):
        """Implementace singleton pattern."""
        if cls._instance is None:
            cls._instance = super(Logger, cls).__new__(cls)
        return cls._instance

    def __init__(self):
        """Inicializace loggeru pouze jednou."""
        if not self._initialized:
            self._initialized = True
            self._setup_logger()

    def _setup_logger(self):
        """
        Nastavení loggeru s file a console handlery.
        
        Vytvoří rotující log soubor s maximální velikostí 1MB
        a 5 zálohami, plus výstup do konzole.
        """
        # Vytvoření logs adresáře, pokud neexistuje
        logs_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "logs")
        os.makedirs(logs_dir, exist_ok=True)
        
        log_path = os.path.join(logs_dir, "miner.log")
        formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')

        # Handler pro soubor s rotací
        file_handler = RotatingFileHandler(
            log_path, 
            maxBytes=1024*1024,  # 1MB
            backupCount=5
        )
        file_handler.setFormatter(formatter)

        # Handler pro konzoli
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)

        # Nastavení loggeru
        self.logger = logging.getLogger('miner')
        self.logger.setLevel(logging.INFO)
        self.logger.propagate = False
        self.logger.handlers = []
        self.logger.addHandler(file_handler)
        self.logger.addHandler(console_handler)

    def get_logger(self):
        """Vrátí nakonfigurovaný logger instance."""
        return self.logger

# Inicializace loggeru
logger = Logger().get_logger()

# Konfigurace SSL - vypnutí varování pro self-signed certifikáty
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

def check_internet():
    """
    Ověří připojení k internetu pomocí DNS dotazu na Google.
    
    Returns:
        bool: True pokud je připojení dostupné, False jinak
    """
    try:
        socket.create_connection(("8.8.8.8", 53), timeout=3)
        logger.debug("Internet připojení: OK")
        return True
    except OSError:
        logger.warning("Internet připojení: Není dostupné")
        return False


def open_log():
    """
    Otevře log soubor v defaultním textovém editoru.
    
    Používá macOS příkaz 'open' pro otevření souboru.
    """
    log_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "logs", "miner.log")
    if os.path.exists(log_path):
        logger.info(f"Otevirám log soubor: {log_path}")
        subprocess.run(["open", log_path])
    else:
        logger.error(f"Log soubor neexistuje: {log_path}")

class MinerWidget(rumps.App):
    """
    Hlavní třída pro macOS menu bar widget.
    
    Zobrazuje hash rate a teplotu v menu bar s automatickými
    aktualizacemi a možností ručního ovládání.
    """
    
    def __init__(self):
        """
        Inicializace widgetu s menu a spuštěním aktualizačního vlákna.
        """
        super(MinerWidget, self).__init__("Miner", quit_button=None, icon=None)
        self.title = "--"
        self.update_thread = None
        self.running = True
        
        # Nastavení menu
        self.menu = [
            rumps.MenuItem("Aktualizovat", callback=self.force_update),
            rumps.MenuItem("Otevřít log", callback=lambda _: open_log()),
            rumps.MenuItem("Ukončit", callback=self.quit),
            None  # separator
        ]
        
        logger.info("Aplikace inicializována")
        
        # Spuštění aktualizačního vlákna ihned po inicializaci
        self.update_thread = threading.Thread(target=self.update_status, daemon=True)
        self.update_thread.start()

    def force_update(self, _):
        """
        Ruční aktualizace dat z menu.
        
        Args:
            _: Ignorovaný parametr z rumps callback
        """
        logger.info("Ruční aktualizace spuštěna")
        self.update_status_once()
        logger.info("Ruční aktualizace dokončena")

    def update_status_once(self):
        """
        Jednorázová aktualizace stavu widgetu.
        
        Načte hash rate z pool.braiins.com a teplotu z Tuya API,
        převede jednotky na TH/s a aktualizuje titulek v menu bar.
        """
        if not check_internet():
            logger.warning("Není připojení k WiFi")
            self.title = "Offline"
            return

        logger.info("Začínám načítat data z pool.braiins.com")
        profile, workers = self.fetch_data()
        
        # Získání teploty z Tuya API (vždy se pokusíme)
        try:
            logger.info("Získávám teplotu z Tuya API")
            token = get_api.get_access_token()
            status = get_api.get_device_status(token)
            temp_item = next(
                (d for d in status if d.get("code") == "va_temperature"), 
                None
            )
            temp = f"{temp_item['value']/10.0:.1f}" if temp_item else "--"
            logger.info(f"Načtená teplota: {temp}°C")
        except Exception as e:
            logger.error(f"Chyba při získávání teploty: {str(e)}")
            temp = "--"
        
        if profile and workers:
            try:
                # Získání hash rate dat
                data = profile[COIN]
                hr5 = data['hash_rate_5m']
                unit = data['hash_rate_unit']
                logger.info(f"Načtený hash rate: {hr5} {unit}")
                
                # Správný převod jednotek podle skutečné hodnoty z API
                if unit == 'Gh/s':
                    if hr5 >= 1000:  # Pokud je >= 1000 Gh/s, převedeme na TH/s
                        hr5_th = hr5 / 1000
                        display_rate = f"{hr5_th:.1f}TH/s"
                    else:  # Jinak zobrazíme v Gh/s
                        display_rate = f"{hr5:.1f}Gh/s"
                elif unit == 'Ph/s':
                    hr5_th = hr5 * 1000
                    display_rate = f"{hr5_th:.1f}TH/s"
                elif unit == 'TH/s':
                    display_rate = f"{hr5:.1f}TH/s"
                else:
                    display_rate = f"{hr5:.1f}{unit}"
                
                logger.debug(f"Zobrazený hash rate: {display_rate}")
                
                # Aktualizace titulku v menu bar
                new_title = f"{display_rate} {temp}°C"
                logger.info(f"Aktualizuji titulek na: {new_title}")
                self.title = new_title
                
            except Exception as e:
                logger.error(f"Chyba při aktualizaci: {str(e)}")
                self.title = f"Error {temp}°C"
        else:
            logger.warning("Nepodařilo se načíst data z pool.braiins.com")
            # Zobrazíme pouze teplotu pokud není dostupný pool
            self.title = f"-- {temp}°C"

    def fetch_data(self):
        """
        Načte data z pool.braiins.com API s retry mechanismem.
        
        Returns:
            tuple: (profile_data, workers_data) nebo (None, None) při chybě
        """
        if not TOKEN:
            logger.warning("Pool token není nastaven - nelze načíst data z pool.braiins.com")
            return None, None
            
        for attempt in range(MAX_RETRIES):
            try:
                profile_url = f"{BASE_URL}/accounts/profile/json/{COIN}/"
                workers_url = f"{BASE_URL}/accounts/workers/json/{COIN}/"
                logger.info(f"Pokus {attempt + 1}/{MAX_RETRIES} o načtení dat")
                
                # Vytvoření session s vypnutou SSL verifikací
                session = requests.Session()
                session.verify = False
                
                # Načtení profilu
                logger.debug(f"Načítám profil z: {profile_url}")
                profile = session.get(profile_url, headers=HEADERS, timeout=10)
                profile.raise_for_status()
                profile_data = profile.json()
                
                # Načtení workerů
                logger.debug(f"Načítám workery z: {workers_url}")
                workers = session.get(workers_url, headers=HEADERS, timeout=10)
                workers.raise_for_status()
                workers_data = workers.json()
                
                logger.info("Data úspěšně načtena")
                return profile_data, workers_data
                
            except Exception as e:
                logger.error(
                    f"Chyba při načítání dat (pokus {attempt + 1}/{MAX_RETRIES}): {str(e)}"
                )
                if attempt < MAX_RETRIES - 1:
                    logger.info(f"Čekám {RETRY_DELAY} sekund před dalším pokusem")
                    time.sleep(RETRY_DELAY)
                continue
                
        return None, None
            
    def update_status(self):
        """
        Hlavní smyčka pro automatické aktualizace.
        
        Spouští se v samostatném vlákně a aktualizuje data
        každých UPDATE_INTERVAL sekund.
        """
        logger.info("Spouštím automatickou aktualizaci")
        while self.running:
            try:
                self.update_status_once()
                logger.debug(f"Čekám {UPDATE_INTERVAL} sekund před další aktualizací")
                time.sleep(UPDATE_INTERVAL)
            except Exception as e:
                logger.error(f"Chyba v aktualizačním vlákně: {str(e)}")
                time.sleep(RETRY_DELAY)

    def run(self):
        """Spustí hlavní aplikační smyčku."""
        logger.info("Spouštím aplikaci")
        super(MinerWidget, self).run()

    def quit(self):
        """
        Bezpečně ukončí aplikaci a čeká na dokončení vlákna.
        """
        logger.info("Ukončuji aplikaci")
        self.running = False
        
        # Čekání na dokončení aktualizačního vlákna
        if self.update_thread and self.update_thread.is_alive():
            self.update_thread.join(timeout=5)
            
        super(MinerWidget, self).quit()

if __name__ == '__main__':
    """
    Hlavní vstupní bod aplikace.
    
    Nastaví LSUIElement pro skrytí z Docku a spustí widget.
    """
    # Explicitní skrytí z Docku pomocí AppKit
    try:
        import AppKit
        info = AppKit.NSBundle.mainBundle().infoDictionary()
        info['LSUIElement'] = True
    except ImportError:
        pass
    
    # Spuštění aplikace
    app = MinerWidget()
    app.run() 
