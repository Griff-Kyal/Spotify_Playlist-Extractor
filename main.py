import time
import os
import sys
from datetime import datetime
from config import (
    playlist_extract,
    playlist_import,
    run_headless,
    playlist_name
)
from spotify_scraper import main as spotify_scraper
from API_importer import create_playlist_from_csv as spotify_importer

class Logger(object):
    def __init__(self, filename=None):
        os.makedirs("logs", exist_ok=True)
        if filename is None:
            timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
            filename = f"logs/log_{timestamp}.txt"

        self.terminal = sys.stdout
        self.terminal_err = sys.stderr
        self.log = open(filename, "w", encoding="utf-8")

    def write(self, message):
        self.terminal.write(message)
        self.log.write(message)

    def flush(self):
        self.terminal.flush()
        self.log.flush()

os.system('cls' if os.name == 'nt' else 'clear')

logger = Logger()
sys.stdout = logger
sys.stderr = logger

if playlist_extract:
    print(f"Playlist extraction selected. Now beginning to export the playlist into a csv file ...")
    print(f"\n")
    time.sleep(1)
    spotify_scraper(headless=run_headless)
else:
    print(f"Playlist extraction turned off. Continuing to playlist import ...")
    time.sleep(1)

if playlist_import:
    print(f"\n")
    print(f"Playlist import selected. Now importing your playlist to your spotify account ...")
    print(f"\n")
    time.sleep(1)
    spotify_importer('spotify_playlist.csv', playlist_name)
else:
    print(f"\n")
    print(f"Playlist importer turned off. Finishing running code ...")
    print(f"\n")
    time.sleep(1)