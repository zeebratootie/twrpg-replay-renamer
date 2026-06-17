#!/usr/bin/env python3
"""
Replay Batch Processor GUI Application
A Windows desktop application for batch processing W3G replay files with date filtering support
"""

import tkinter as tk
from tkinter import filedialog, messagebox, ttk, simpledialog
import calendar as _calendar
import threading
import os
from pathlib import Path
import sys
import json
import socket
import subprocess
import atexit
from concurrent.futures import ThreadPoolExecutor, as_completed
import time
import re
import shutil
import requests
import logging
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from datetime import datetime, timedelta

# Import configuration and date filtering modules
from config import ConfigManager
from date_filter import DateFilter
from logging_setup import setup_logging

__version__ = "2.2.1"


# ---------------------------------------------------------------------------
# Local parser server auto-start
# Launches the Node "replay-parser" project on port 3000 when the app opens,
# so the user doesn't have to start it manually.
# ---------------------------------------------------------------------------

def _port_is_open(host, port, timeout=0.5):
    try:
        with socket.create_connection((host, port), timeout=timeout):
            return True
    except OSError:
        return False


def _app_base_dir():
    """Directory the app runs from (exe dir when frozen, else this script's dir)."""
    if getattr(sys, 'frozen', False):
        return Path(sys.executable).resolve().parent
    return Path(__file__).resolve().parent


def _default_source_folder():
    """The current user's Warcraft III replay folder, used as the default source."""
    return str(Path.home() / 'Documents' / 'Warcraft III' / 'Replay')


def _default_output_folder():
    """Default place to write sorted replays: Desktop/replay-output."""
    return str(Path.home() / 'Desktop' / 'replay-output')


def _resource_dirs():
    """Directories to search for the bundled/sibling parser executable."""
    base = _app_base_dir()
    dirs = [base] + list(base.parents)
    # PyInstaller onefile extraction dir (if the parser exe is bundled in)
    meipass = getattr(sys, '_MEIPASS', None)
    if meipass:
        dirs.insert(0, Path(meipass))
    return dirs


# Filename patterns for a standalone (pkg-built) parser executable.
PARSER_EXE_PATTERNS = ('replay-parser-win-x64.exe', 'replay-parser.exe',
                       'replay-parser*.exe', '*replay*parser*.exe')


def find_parser_exe(config_value=None):
    """Locate a standalone parser .exe (no Node.js required) for distribution.

    Searches an optional configured path, then the app directory, its parents,
    and the PyInstaller bundle dir. Never matches the app's own executable.
    """
    candidates = []
    if config_value:
        candidates.append(Path(config_value))
    for d in _resource_dirs():
        for pat in PARSER_EXE_PATTERNS:
            try:
                candidates.extend(sorted(d.glob(pat)))
            except OSError:
                continue
    for c in candidates:
        try:
            name = c.name.lower()
            if not c.is_file() or 'parser' not in name:
                continue
            if name.startswith('replaybatch'):  # never launch ourselves
                continue
            return c.resolve()
        except OSError:
            continue
    return None


def find_parser_dir(config_value=None):
    """Locate the replay-parser node project (a folder containing src/index.js).

    Searches an optional configured path first, then walks up the directory tree
    from the app location looking for a sibling ``replay-parser`` folder.
    """
    candidates = []
    if config_value:
        candidates.append(Path(config_value))
    base = _app_base_dir()
    for parent in [base] + list(base.parents):
        candidates.append(parent / 'replay-parser')
    for cand in candidates:
        try:
            if (cand / 'src' / 'index.js').exists():
                return cand.resolve()
        except OSError:
            continue
    return None


class ParserServerManager:
    """Starts and stops the local Node replay-parser server."""

    def __init__(self, parser_url='http://localhost:3000', parser_dir=None, parser_exe=None):
        self.process = None
        self.host = 'localhost'
        self.port = self._port_from_url(parser_url)
        self.parser_dir = parser_dir
        self.parser_exe = parser_exe
        self.started_by_us = False
        self.status = ''

    @staticmethod
    def _port_from_url(url):
        m = re.search(r':(\d+)', url or '')
        return int(m.group(1)) if m else 3000

    def ensure_running(self, log=print):
        """Make sure the parser is reachable; start it if needed. Returns bool."""
        if _port_is_open(self.host, self.port):
            self.status = f"Parser already running on port {self.port}"
            log(self.status)
            return True

        # 1) Prefer the replay-parser source folder via Node (always the latest
        #    parser code, e.g. hero-class detection). Used on the dev machine.
        parser_dir = find_parser_dir(self.parser_dir)
        node = shutil.which('node') if parser_dir else None
        if parser_dir and node:
            log(f"Starting parser from source: {parser_dir} (Node) ...")
            return self._launch([node, str(parser_dir / 'src' / 'index.js')],
                                str(parser_dir), log)

        # 2) Fallback: a standalone parser .exe - works on any machine with no
        #    Node.js install (this is what gets shared with friends).
        parser_exe = find_parser_exe(self.parser_exe)
        if parser_exe:
            log(f"Starting bundled parser: {parser_exe.name} ...")
            return self._launch([str(parser_exe)], str(parser_exe.parent), log)

        if parser_dir and not node:
            self.status = ("Found parser source but Node.js is not installed, and no "
                           "parser .exe was found - cannot auto-start the parser.")
        else:
            self.status = ("No parser found. Place 'replay-parser-win-x64.exe' next to "
                           "this app, or start the parser manually on port "
                           f"{self.port}.")
        log(self.status)
        return False

    def _launch(self, args, cwd, log):
        """Launch a parser process and wait for the port to come up."""
        creationflags = getattr(subprocess, 'CREATE_NO_WINDOW', 0) if os.name == 'nt' else 0
        try:
            self.process = subprocess.Popen(
                args, cwd=cwd,
                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                creationflags=creationflags,
            )
            self.started_by_us = True
        except Exception as e:
            self.status = f"Failed to start parser: {e}"
            log(self.status)
            return False

        # Wait (up to ~20s) for the server to start listening.
        for _ in range(40):
            if _port_is_open(self.host, self.port):
                self.status = f"Parser started on port {self.port}"
                log(self.status)
                return True
            if self.process.poll() is not None:
                self.status = "Parser process exited unexpectedly"
                log(self.status)
                return False
            time.sleep(0.5)

        self.status = "Parser did not start responding in time"
        log(self.status)
        return False

    def stop(self):
        """Stop the parser if we started it (kills the cluster process tree)."""
        if not self.started_by_us or not self.process or self.process.poll() is not None:
            return
        try:
            if os.name == 'nt':
                subprocess.run(
                    ['taskkill', '/F', '/T', '/PID', str(self.process.pid)],
                    stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                )
            else:
                self.process.terminate()
        except Exception:
            pass


# ---------------------------------------------------------------------------
# ReplayRenamer - inlined so no external file is needed at runtime
# ---------------------------------------------------------------------------

# Maps short in-game load-codes (typed via -l/-load/-save) and class shorthands
# to their full TWRPG class display names. Entries not present here - including
# already-resolved hero classes like "Arcane Mage" - pass through unchanged.
# Canonical names come from twrpg-info/heros.json (heroClass).
CLASS_DISPLAY_NAMES = {
    'merch': 'Merchant',
    'am': 'Arcane Mage',
    'fm': 'Fire Mage',
    'lm': 'Lightning Mage',
    'wm': 'Water Mage',
    'wim': 'Wind Mage',
    'mage': 'Mage',
    'pal': 'Paladin',
    'pala': 'Paladin',
    'paladin': 'Paladin',
    'cpal': 'Paladin',
    'crusader': 'Crusader',
    'kn': 'Knight',
    'knight': 'Knight',
    'th': 'Thunderer',
    'ele': 'Elementalist',
    'ss': 'Sword Saint',
    'se': 'Sword Enchanter',
    'bm': 'Bow Master',
    'witch': 'Witch',
    'sniper': 'Sniper',
    'priest': 'Priest',
    'rp': 'Reaper',
    'reaper': 'Reaper',
}

class ReplayRenamer:
    # Game-action / transaction pseudo-items that appear in loot data but are not
    # real item drops. Excluded from generated filenames.
    NOISE_PREFIXES = ('wish', 'ticket', 'trade ', 'exchange ', 'purchase ',
                      'destroy ', 'forfeit', 'sacrifice', 'super reverse',
                      'change difficulty')
    NOISE_EXACT = {'craft'}
    NOISE_CONTAINS = ('expedition', 'conversion')

    def __init__(self, replay_folder, parser_url="http://localhost:3000"):
        self.replay_folder = Path(replay_folder)
        self.parser_url = parser_url
        self.last_month = datetime.now() - timedelta(days=30)

        self.session = requests.Session()
        retry_strategy = Retry(
            total=2,
            backoff_factor=0.1,
            status_forcelist=[429, 500, 502, 503, 504],
        )
        adapter = HTTPAdapter(
            max_retries=retry_strategy,
            pool_connections=16,
            pool_maxsize=16
        )
        self.session.mount("http://", adapter)
        self.session.mount("https://", adapter)

    def get_file_modified_date(self, file_path):
        return datetime.fromtimestamp(os.path.getmtime(file_path))

    def is_from_last_month(self, file_path):
        return True

    def _is_noise_item(self, name):
        """True for blank names and game-action pseudo-items (wish, sacrifice,
        ticket, change difficulty, forfeit loot, purchase rare items, etc.)."""
        n = (name or '').strip().lower()
        if not n:
            return True
        if n in self.NOISE_EXACT:
            return True
        if n.startswith(self.NOISE_PREFIXES):
            return True
        if any(tok in n for tok in self.NOISE_CONTAINS):
            return True
        return False

    def parse_replay(self, file_path):
        try:
            with open(file_path, 'rb') as f:
                files = {'file': f}
                response = self.session.post(f"{self.parser_url}/parse-w3g", files=files, timeout=30)
            if response.status_code == 200:
                return response.json()
            else:
                print(f"  Parser error: {response.status_code}")
                return None
        except requests.exceptions.Timeout:
            print(f"  Parser timeout")
            return None
        except requests.exceptions.ConnectionError:
            print(f"  Connection error")
            return None
        except Exception as e:
            print(f"  Error: {str(e)[:50]}")
            return None

    def extract_base_class(self, class_name):
        if not class_name or class_name == "unknown":
            return class_name
        base = class_name.lower().strip()
        if '-' in base:
            base = base.split('-')[0]
        base = base.rstrip('0123456789')
        known_prefixes = ['merch', 'knight', 'druid', 'paladin', 'demon', 'mage',
                          'cpal', 'wim', 'th', 'am', 'bm', 'dd', 'ud']
        matched = base
        for prefix in sorted(known_prefixes, key=len, reverse=True):
            if base.startswith(prefix):
                matched = prefix
                break
        matched = matched if matched else class_name.lower()
        # Convert short load-codes (e.g. 'merch', 'cpal') to full class names.
        # Unmapped codes pass through unchanged.
        return CLASS_DISPLAY_NAMES.get(matched, matched)

    def _get_hero_class(self, parsed_data, player_name):
        """Class derived from the hero the player actually used in-game.

        Reads playerData[].hero.heroClass (the parser maps the replay's hero
        unit to its class via heros.json). Returns a clean class name or None.
        This is far more reliable than parsing chat -l/-load/-save text.
        """
        target = (player_name or '').lower().strip()
        for player in parsed_data.get('playerData', []):
            pn = (player.get('playerName') or '').lower()
            cn = re.sub(r'\([^)]*\)', '', (player.get('convertedName') or '')).strip().lower()
            if pn == target or pn.split('#')[0] == target or cn == target:
                hero = player.get('hero')
                if isinstance(hero, dict) and hero.get('heroClass'):
                    return re.sub(r'[<>:"/\\|?*]', '', hero['heroClass']).strip()
                return None
        return None

    def get_player_class(self, parsed_data, player_name):
        if not parsed_data:
            return "unknown"
        # HIGHEST PRIORITY: the actual hero the player used in-game, derived from
        # the replay's action data (the parser identifies it as the first hero the
        # player controls after their starting footman). This is the most reliable
        # signal, so it wins over the chat declaration below.
        hero_class = self._get_hero_class(parsed_data, player_name)
        if hero_class:
            return hero_class
        # NEXT: playerData class/race from the parser.
        if 'playerData' in parsed_data:
            for player in parsed_data['playerData']:
                if (player.get('playerName', '').lower() == player_name.lower() or
                        player.get('convertedName', '').lower() == player_name.lower()):
                    class_value = player.get('class') or player.get('race')
                    if class_value:
                        return self.extract_base_class(class_value)
        # LAST RESORT: the player's own -l / -load / -save chat declaration. Used
        # only when the reliable in-game data above could not identify the hero.
        if 'chatData' in parsed_data:
            for chat in parsed_data['chatData']:
                chat_player = chat.get('player', '').lower()
                message = chat.get('message', '').lower()
                if chat_player == player_name.lower() or chat_player.startswith(player_name.lower() + '#'):
                    if '-l ' in message:
                        parts = message.split('-l ')
                        if len(parts) > 1:
                            class_part = parts[1].split()[0].strip()
                            if class_part and len(class_part) < 20 and class_part not in ['game', 'all']:
                                return self.extract_base_class(class_part)
                    if '-load ' in message:
                        parts = message.split('-load ')
                        if len(parts) > 1:
                            class_part = parts[1].split()[0].strip()
                            if class_part and len(class_part) < 20 and not any(c.isdigit() for c in class_part):
                                return self.extract_base_class(class_part)
                    if '-save ' in message:
                        parts = message.split('-save ')
                        if len(parts) > 1:
                            class_part = parts[1].split()[0].strip()
                            if '/' in class_part:
                                class_part = class_part.split('/')[0].strip()
                            if class_part and len(class_part) < 20 and class_part not in ['game', 'all']:
                                return self.extract_base_class(class_part)
        return "unknown"

    def get_canonical_player_name(self, parsed_data, player_name):
        """Return the player's name exactly as it appears in the replay.

        The user types a search term (e.g. "crucibles"); the replay may store it
        as "Crucibles" or "crucibles#1234". This resolves the canonical account
        name from the parsed data so it can be used as the output folder name.
        Falls back to the searched term if no match is found.
        """
        target = (player_name or '').lower().strip()
        canonical = None

        if parsed_data and 'playerData' in parsed_data:
            for player in parsed_data['playerData']:
                pn = (player.get('playerName') or '').strip()
                cn = (player.get('convertedName') or '').strip()
                clean_cn = re.sub(r'\([^)]*\)', '', cn).strip()
                if pn.lower() == target or clean_cn.lower() == target:
                    canonical = pn or clean_cn
                    break

        if not canonical and parsed_data and 'loots' in parsed_data:
            for loot in parsed_data['loots']:
                raw = loot.get('playerName', '')
                clean = re.sub(r'#\d+.*', '', raw)
                clean = re.sub(r'\([^)]*\)', '', clean).strip()
                if clean.lower() == target:
                    canonical = clean
                    break

        if not canonical:
            canonical = player_name

        # Sanitise so it is safe to use as a folder/file name.
        canonical = re.sub(r'[<>:"/\\|?*]', '', canonical).strip()
        return canonical or player_name

    def generate_player_specific_filename(self, parsed_data, player_name, original_file_path,
                                          display_name=None):
        if not parsed_data or 'loots' not in parsed_data:
            return None
        if isinstance(original_file_path, str):
            original_file_path = Path(original_file_path)
        from collections import OrderedDict
        loot_counts = OrderedDict()
        for loot in parsed_data['loots']:
            loot_player = loot.get('playerName', '')
            clean_loot_player = re.sub(r'#\d+.*', '', loot_player)
            clean_loot_player = re.sub(r'\([^)]*\)', '', clean_loot_player).strip()
            if clean_loot_player.lower() != player_name.lower():
                continue
            raw_name = loot.get('itemName')
            if self._is_noise_item(raw_name):
                continue
            item_name = re.sub(r'[<>:"/\\|?*]', '', raw_name).strip()
            if not item_name:
                continue
            loot_counts[item_name] = loot_counts.get(item_name, 0) + 1
        if not loot_counts:
            return None
        # Group duplicates: two "Prius Gold Coin" -> "Prius Gold Coin x2"
        player_loots = [f"{name} x{count}" if count > 1 else name
                        for name, count in loot_counts.items()]
        player_class = self.get_player_class(parsed_data, player_name)
        original_filename = original_file_path.name
        craft_suffix = ""
        craft_match = re.search(r'(?:^|\s|\-\s)craft\s+([^\.]+)', original_filename.lower())
        if craft_match:
            craft_item = re.sub(r'[<>:"/\\|?*]', '', craft_match.group(1).strip())
            craft_suffix = f" - craft {craft_item}"
        mod_date = self.get_file_modified_date(original_file_path)
        date_suffix = f" - {mod_date.strftime('%b-%d-%y')}"
        loots_str = ", ".join(player_loots)
        if len(loots_str) > 200:
            loots_str = loots_str[:200] + "..."
        name_prefix = display_name or player_name
        new_filename = f"{name_prefix} - {player_class} - {loots_str}{craft_suffix}{date_suffix}.w3g"
        new_filename = re.sub(r'[<>:"/\\|?*]', '', new_filename)
        return new_filename

    def create_player_file(self, original_file_path, player_name, base_output_folder, dry_run=True):
        parsed_data = self.parse_replay(original_file_path)
        if not parsed_data:
            print(f"Failed to parse {original_file_path}")
            return False
        # Use the player's real name from the replay as the folder/file name.
        canonical_name = self.get_canonical_player_name(parsed_data, player_name)
        new_name = self.generate_player_specific_filename(
            parsed_data, player_name, original_file_path, display_name=canonical_name)
        if not new_name:
            print(f"No loots found for player '{player_name}' in {original_file_path.name}")
            return False
        parts = new_name.split(' - ')
        player_class = parts[1] if len(parts) >= 2 else "unknown"
        output_path = Path(base_output_folder) / canonical_name / player_class
        if not output_path.exists():
            if dry_run:
                print(f"DRY RUN: Would create directory '{output_path}'")
            else:
                output_path.mkdir(parents=True, exist_ok=True)
        new_file_path = output_path / new_name
        if new_file_path.exists():
            print(f"File already exists: {new_file_path}")
            return False
        try:
            if dry_run:
                print(f"DRY RUN: Would copy '{original_file_path.name}' to '{canonical_name}/{player_class}/{new_name}'")
                return True
            else:
                shutil.copy2(original_file_path, new_file_path)
                print(f"Copied to '{canonical_name}/{player_class}/{new_name}'")
                return True
        except Exception as e:
            print(f"Error creating file: {e}")
            return False


# ---------------------------------------------------------------------------
# Date picker - a small tkinter-only calendar popup (no external deps)
# ---------------------------------------------------------------------------

class DatePickerPopup(tk.Toplevel):
    """A lightweight modal calendar that writes YYYY-MM-DD into a StringVar."""

    def __init__(self, parent, target_var, anchor=None):
        super().__init__(parent)
        self.target_var = target_var
        self.title("Pick a date")
        self.resizable(False, False)
        self.transient(parent)

        try:
            cur = datetime.strptime(target_var.get().strip(), '%Y-%m-%d')
        except (ValueError, AttributeError):
            cur = datetime.now()
        self.year = cur.year
        self.month = cur.month

        self.body = ttk.Frame(self, padding=6)
        self.body.pack()
        self._build()

        # Position near the field that opened us (fall back to cursor area).
        self.update_idletasks()
        if anchor is not None:
            x = anchor.winfo_rootx()
            y = anchor.winfo_rooty() + anchor.winfo_height()
            self.geometry(f"+{x}+{y}")
        self.grab_set()
        self.bind("<Escape>", lambda e: self.destroy())

    def _build(self):
        for w in self.body.winfo_children():
            w.destroy()

        header = ttk.Frame(self.body)
        header.grid(row=0, column=0, columnspan=7, sticky=(tk.W, tk.E), pady=(0, 6))
        ttk.Button(header, text="<", width=3, command=self._prev_month).pack(side=tk.LEFT)
        ttk.Label(header, text=f"{_calendar.month_name[self.month]} {self.year}",
                  font=("Arial", 10, "bold"), anchor="center").pack(
            side=tk.LEFT, expand=True, fill=tk.X)
        ttk.Button(header, text=">", width=3, command=self._next_month).pack(side=tk.LEFT)

        for col, name in enumerate(["Su", "Mo", "Tu", "We", "Th", "Fr", "Sa"]):
            ttk.Label(self.body, text=name, width=3, anchor="center",
                      font=("Arial", 8, "bold")).grid(row=1, column=col, padx=1, pady=1)

        cal = _calendar.Calendar(firstweekday=6)  # weeks start on Sunday
        row = 2
        for week in cal.monthdayscalendar(self.year, self.month):
            for col, day in enumerate(week):
                if day == 0:
                    continue
                ttk.Button(self.body, text=str(day), width=3,
                           command=lambda d=day: self._select(d)).grid(
                    row=row, column=col, padx=1, pady=1)
            row += 1

        footer = ttk.Frame(self.body)
        footer.grid(row=row, column=0, columnspan=7, sticky=(tk.W, tk.E), pady=(6, 0))
        ttk.Button(footer, text="Today", command=self._today).pack(
            side=tk.LEFT, expand=True, fill=tk.X, padx=1)
        ttk.Button(footer, text="Clear", command=self._clear).pack(
            side=tk.LEFT, expand=True, fill=tk.X, padx=1)

    def _prev_month(self):
        self.month -= 1
        if self.month < 1:
            self.month, self.year = 12, self.year - 1
        self._build()

    def _next_month(self):
        self.month += 1
        if self.month > 12:
            self.month, self.year = 1, self.year + 1
        self._build()

    def _select(self, day):
        self.target_var.set(f"{self.year:04d}-{self.month:02d}-{day:02d}")
        self.destroy()

    def _today(self):
        self.target_var.set(datetime.now().strftime('%Y-%m-%d'))
        self.destroy()

    def _clear(self):
        self.target_var.set('')
        self.destroy()


# ---------------------------------------------------------------------------
# GUI
# ---------------------------------------------------------------------------

class ReplayBatchProcessorGUI:
    # Color palette for a cleaner look
    BG = "#f4f6f8"
    CARD = "#ffffff"
    ACCENT = "#2d8cff"
    ACCENT_DK = "#1f6fd6"
    SUCCESS = "#28a745"
    SUCCESS_DK = "#1e7e34"
    TEXT = "#1b2733"
    MUTED = "#6b7785"

    def __init__(self, root, config_manager: ConfigManager):
        self.root = root
        self.root.title(f"Replay Batch Processor v{__version__}")
        self.root.geometry("720x820")
        self.root.minsize(680, 700)
        self.root.resizable(True, True)
        self.root.configure(bg=self.BG)

        # Store config manager
        self.config = config_manager

        # Player-profile / auto-save state
        self._config_dir = _app_base_dir()      # where .ini profiles live (exe dir when frozen)
        self._profile_paths = {}                 # display name -> .ini Path
        self._loading = False                    # guard so loads don't trigger auto-save
        self._autosave_job = None                # pending debounced auto-save callback id

        # Window icon (generated at build/run time when Pillow is available)
        try:
            icon_path = _app_base_dir() / "app_icon.ico"
            if icon_path.exists():
                self.root.iconbitmap(default=str(icon_path))
        except Exception:
            pass

        # Theme + custom styles
        style = ttk.Style()
        style.theme_use('clam')
        self._configure_styles(style)

        self.setup_ui()
        self.load_settings()
        self._install_autosave_traces()

        # Ask for the player name first thing when there isn't one yet.
        self.root.after(150, self.prompt_initial_player)

    def _configure_styles(self, style):
        """Define the ttk styles used across the app for a cleaner appearance."""
        style.configure('.', background=self.BG, foreground=self.TEXT,
                        font=('Segoe UI', 10))
        style.configure('TFrame', background=self.BG)
        style.configure('TLabel', background=self.BG, foreground=self.TEXT)
        style.configure('TCheckbutton', background=self.BG)
        style.configure('Title.TLabel', font=('Segoe UI Semibold', 20),
                        foreground=self.TEXT)
        style.configure('Subtitle.TLabel', font=('Segoe UI', 9.5),
                        foreground=self.MUTED)
        style.configure('Section.TLabel', font=('Segoe UI Semibold', 11),
                        foreground=self.ACCENT_DK)
        style.configure('Hint.TLabel', font=('Segoe UI', 8.5), foreground=self.MUTED)
        style.configure('TLabelframe', background=self.BG, bordercolor="#d7dde3")
        style.configure('TLabelframe.Label', background=self.BG,
                        foreground=self.ACCENT_DK, font=('Segoe UI Semibold', 10))
        style.configure('TButton', font=('Segoe UI', 10), padding=(10, 5))
        style.configure('TEntry', padding=4)
        style.configure('TCombobox', padding=4)

        # Primary call-to-action button (green)
        style.configure('Accent.TButton', font=('Segoe UI Semibold', 10),
                        padding=(16, 7), foreground='white', background=self.SUCCESS,
                        bordercolor=self.SUCCESS_DK)
        style.map('Accent.TButton',
                  background=[('active', self.SUCCESS_DK), ('pressed', self.SUCCESS_DK)],
                  foreground=[('disabled', '#e8e8e8')])

        # Compact icon button (calendar / add)
        style.configure('Icon.TButton', padding=(4, 2), font=('Segoe UI', 10))

        # Thicker, colored progress bar
        style.configure('App.Horizontal.TProgressbar', thickness=20,
                        background=self.ACCENT, troughcolor="#e3e8ee",
                        bordercolor="#e3e8ee", lightcolor=self.ACCENT,
                        darkcolor=self.ACCENT)

    def setup_ui(self):
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))

        header = ttk.Frame(main_frame)
        header.grid(row=0, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(0, 12))
        ttk.Label(header, text="Replay Batch Processor",
                  style='Title.TLabel').pack(anchor=tk.W)
        ttk.Label(header,
                  text="Sort Warcraft III replays into per-player loot folders",
                  style='Subtitle.TLabel').pack(anchor=tk.W)

        current_row = 1

        ttk.Label(main_frame, text="Player:", font=("Arial", 10)).grid(
            row=current_row, column=0, sticky=tk.W, pady=5)
        self.player_name_var = tk.StringVar()
        self.player_dropdown = ttk.Combobox(main_frame, textvariable=self.player_name_var,
                                            width=37)
        self.player_dropdown.grid(row=current_row, column=1, sticky=(tk.W, tk.E), padx=5)
        self.player_dropdown.bind('<<ComboboxSelected>>', self.on_player_selected)
        ttk.Button(main_frame, text="+ Add New",
                   command=self.add_new_player).grid(row=current_row, column=2, padx=5)
        current_row += 1

        ttk.Label(main_frame, text="Source Replay Folder:", font=("Arial", 10)).grid(
            row=current_row, column=0, sticky=tk.W, pady=5)
        self.source_folder_var = tk.StringVar()
        ttk.Entry(main_frame, textvariable=self.source_folder_var, width=40).grid(
            row=current_row, column=1, sticky=(tk.W, tk.E), padx=5)
        ttk.Button(main_frame, text="Browse...",
                   command=self.browse_source_folder).grid(row=current_row, column=2, padx=5)
        current_row += 1

        self.recursive_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(main_frame, text="Search subfolders (recursive)",
                        variable=self.recursive_var).grid(
            row=current_row, column=1, sticky=tk.W, pady=(0, 2))
        current_row += 1

        ttk.Label(main_frame, text="Output Folder:", font=("Arial", 10)).grid(
            row=current_row, column=0, sticky=tk.W, pady=5)
        self.output_folder_var = tk.StringVar()
        ttk.Entry(main_frame, textvariable=self.output_folder_var, width=40).grid(
            row=current_row, column=1, sticky=(tk.W, tk.E), padx=5)
        ttk.Button(main_frame, text="Browse...",
                   command=self.browse_output_folder).grid(row=current_row, column=2, padx=5)
        current_row += 1

        ttk.Label(main_frame, text="Parser URL:", font=("Arial", 10)).grid(
            row=current_row, column=0, sticky=tk.W, pady=5)
        self.parser_url_var = tk.StringVar(value="http://localhost:3000")
        ttk.Entry(main_frame, textvariable=self.parser_url_var, width=40).grid(
            row=current_row, column=1, columnspan=2, sticky=(tk.W, tk.E), padx=5)
        current_row += 1

        ttk.Label(main_frame, text="Batch Size:", font=("Arial", 10)).grid(
            row=current_row, column=0, sticky=tk.W, pady=5)
        self.batch_size_var = tk.StringVar(value="500")
        ttk.Entry(main_frame, textvariable=self.batch_size_var, width=10).grid(
            row=current_row, column=1, sticky=tk.W, padx=5)
        ttk.Label(main_frame, text="(higher = faster for 5000+ files)", font=("Arial", 8)).grid(
            row=current_row, column=2, sticky=tk.W, padx=5)
        current_row += 1

        ttk.Label(main_frame, text="Parallel Threads:", font=("Arial", 10)).grid(
            row=current_row, column=0, sticky=tk.W, pady=5)
        self.parallel_threads_var = tk.StringVar(value="8")
        ttk.Entry(main_frame, textvariable=self.parallel_threads_var, width=10).grid(
            row=current_row, column=1, sticky=tk.W, padx=5)
        ttk.Label(main_frame, text="(more = faster, 4-16 recommended)", font=("Arial", 8)).grid(
            row=current_row, column=2, sticky=tk.W, padx=5)
        current_row += 1

        ttk.Separator(main_frame, orient='horizontal').grid(
            row=current_row, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=10)
        current_row += 1

        # Date Filter Section
        ttk.Label(main_frame, text="Date Filtering (Optional)", style='Section.TLabel').grid(
            row=current_row, column=0, columnspan=3, sticky=tk.W, pady=(10, 5))
        current_row += 1

        self.all_dates_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(main_frame, text="All dates (process every file, no date filter)",
                        variable=self.all_dates_var,
                        command=self._toggle_date_inputs).grid(
            row=current_row, column=0, columnspan=3, sticky=tk.W, pady=(0, 2))
        current_row += 1

        ttk.Label(main_frame, text="Date From:", font=("Arial", 10)).grid(
            row=current_row, column=0, sticky=tk.W, pady=5)
        self.date_from_var = tk.StringVar()
        date_from_frame = ttk.Frame(main_frame)
        date_from_frame.grid(row=current_row, column=1, sticky=tk.W, padx=5)
        self.date_from_entry = ttk.Entry(date_from_frame, textvariable=self.date_from_var, width=15)
        self.date_from_entry.pack(side=tk.LEFT)
        self.date_from_btn = ttk.Button(date_from_frame, text="\U0001F4C5", width=3,
                                        style='Icon.TButton',
                                        command=lambda: self._pick_date(self.date_from_var,
                                                                        self.date_from_entry))
        self.date_from_btn.pack(side=tk.LEFT, padx=(4, 0))
        ttk.Label(main_frame, text="(default: 30 days ago)", font=("Arial", 8)).grid(
            row=current_row, column=2, sticky=tk.W, padx=5)
        current_row += 1

        ttk.Label(main_frame, text="Date To:", font=("Arial", 10)).grid(
            row=current_row, column=0, sticky=tk.W, pady=5)
        self.date_to_var = tk.StringVar()
        date_to_frame = ttk.Frame(main_frame)
        date_to_frame.grid(row=current_row, column=1, sticky=tk.W, padx=5)
        self.date_to_entry = ttk.Entry(date_to_frame, textvariable=self.date_to_var, width=15)
        self.date_to_entry.pack(side=tk.LEFT)
        self.date_to_btn = ttk.Button(date_to_frame, text="\U0001F4C5", width=3,
                                      style='Icon.TButton',
                                      command=lambda: self._pick_date(self.date_to_var,
                                                                      self.date_to_entry))
        self.date_to_btn.pack(side=tk.LEFT, padx=(4, 0))
        ttk.Label(main_frame, text="(default: today)", font=("Arial", 8)).grid(
            row=current_row, column=2, sticky=tk.W, padx=5)
        current_row += 1

        ttk.Separator(main_frame, orient='horizontal').grid(
            row=current_row, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=10)
        current_row += 1

        # Processing behaviour is fixed: always execute (no dry run), always skip
        # existing files, and always process every batch without prompting.
        # Each player is its own saved profile (selected via the Player dropdown
        # above); settings auto-save as you change them.
        ttk.Label(main_frame,
                  text="Tip: each player is a saved profile - pick one above to load its "
                       "folders, or '+ Add New'. Changes save automatically.",
                  style='Hint.TLabel', wraplength=660).grid(
            row=current_row, column=0, columnspan=3, sticky=tk.W, pady=(0, 5))
        current_row += 1

        button_frame = ttk.Frame(main_frame)
        button_frame.grid(row=current_row, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=10)
        ttk.Button(button_frame, text="▶  Start Processing", style='Accent.TButton',
                   command=self.start_processing).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Clear",
                   command=self.clear_form).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Open Output",
                   command=self.open_output_folder).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Exit",
                   command=self.root.quit).pack(side=tk.LEFT, padx=5)
        current_row += 1

        # Progress bar + live status (files done, percentage, rate, ETA)
        progress_frame = ttk.Frame(main_frame)
        progress_frame.grid(row=current_row, column=0, columnspan=3,
                            sticky=(tk.W, tk.E), pady=(5, 0))
        progress_frame.columnconfigure(0, weight=1)

        self.progress_var = tk.DoubleVar(value=0)
        self.progress_bar = ttk.Progressbar(
            progress_frame, orient='horizontal', mode='determinate',
            variable=self.progress_var, maximum=100,
            style='App.Horizontal.TProgressbar')
        self.progress_bar.grid(row=0, column=0, sticky=(tk.W, tk.E), padx=(0, 10))

        self.progress_pct_var = tk.StringVar(value="0%")
        ttk.Label(progress_frame, textvariable=self.progress_pct_var,
                  font=("Arial", 10, "bold"), width=6).grid(row=0, column=1, sticky=tk.E)

        self.progress_status_var = tk.StringVar(value="Idle")
        ttk.Label(main_frame, textvariable=self.progress_status_var,
                  font=("Arial", 9)).grid(row=current_row + 1, column=0, columnspan=3,
                                          sticky=tk.W, pady=(2, 5))
        current_row += 2

        ttk.Label(main_frame, text="Processing Log:", font=("Arial", 10)).grid(
            row=current_row, column=0, columnspan=3, sticky=tk.W, pady=(10, 5))
        current_row += 1

        log_frame = ttk.Frame(main_frame)
        log_frame.grid(row=current_row, column=0, columnspan=3,
                       sticky=(tk.W, tk.E, tk.N, tk.S), pady=5)
        scrollbar = ttk.Scrollbar(log_frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.log_text = tk.Text(log_frame, height=15, width=70, yscrollcommand=scrollbar.set)
        self.log_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.config(command=self.log_text.yview)

        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)
        # Let the log row absorb all extra vertical space so there is no dead
        # gap below the Processing Log when the window is tall.
        main_frame.rowconfigure(current_row, weight=1)

    def log_message(self, message, end="\n"):
        self.log_text.insert(tk.END, message + end)
        self.log_text.see(tk.END)
        self.root.update()

    def reset_progress(self, status="Idle"):
        self.progress_var.set(0)
        self.progress_pct_var.set("0%")
        self.progress_status_var.set(status)
        self.root.update_idletasks()

    def update_progress(self, done, total, rate=0.0):
        """Update the progress bar and status label (called from worker thread)."""
        pct = (done / total * 100) if total else 0
        self.progress_var.set(pct)
        self.progress_pct_var.set(f"{pct:.0f}%")
        eta_str = ""
        if rate > 0 and done < total:
            remaining = (total - done) / rate
            eta_str = f" | ETA {self._format_eta(remaining)}"
        rate_str = f" | {rate:.1f} files/sec" if rate > 0 else ""
        self.progress_status_var.set(
            f"Processed {done}/{total} files{rate_str}{eta_str}")
        self.root.update_idletasks()

    @staticmethod
    def _format_eta(seconds):
        seconds = int(seconds)
        if seconds >= 3600:
            return f"{seconds // 3600}h {(seconds % 3600) // 60}m"
        if seconds >= 60:
            return f"{seconds // 60}m {seconds % 60}s"
        return f"{seconds}s"

    def browse_source_folder(self):
        folder = filedialog.askdirectory(title="Select Source Replay Folder")
        if folder:
            self.source_folder_var.set(folder)

    def open_output_folder(self):
        """Open the configured output folder in the system file browser."""
        folder = self.output_folder_var.get().strip()
        if not folder or not Path(folder).exists():
            messagebox.showwarning("Open Output",
                                   "Output folder does not exist yet. Run processing first.")
            return
        try:
            if hasattr(os, 'startfile'):
                os.startfile(folder)
        except Exception as e:
            messagebox.showerror("Open Output", f"Could not open folder:\n{e}")

    def browse_output_folder(self):
        folder = filedialog.askdirectory(title="Select Output Folder")
        if folder:
            self.output_folder_var.set(folder)

    def validate_inputs(self):
        player_name = self.player_name_var.get().strip()
        source_folder = self.source_folder_var.get().strip()
        output_folder = self.output_folder_var.get().strip()

        if not player_name:
            messagebox.showerror("Error", "Please enter a player name")
            return False
        if not source_folder:
            messagebox.showerror("Error", "Please select a source folder")
            return False
        if not Path(source_folder).exists():
            messagebox.showerror("Error", f"Source folder does not exist: {source_folder}")
            return False
        if not output_folder:
            messagebox.showerror("Error", "Please select an output folder")
            return False
        if not Path(output_folder).exists():
            try:
                Path(output_folder).mkdir(parents=True, exist_ok=True)
            except Exception as e:
                messagebox.showerror("Error", f"Cannot create output folder: {e}")
                return False
        try:
            if int(self.batch_size_var.get()) <= 0:
                raise ValueError
        except ValueError:
            messagebox.showerror("Error", "Batch size must be a positive integer")
            return False
        try:
            pt = int(self.parallel_threads_var.get())
            if pt <= 0 or pt > 32:
                raise ValueError
        except ValueError:
            messagebox.showerror("Error", "Parallel threads must be between 1 and 32")
            return False
        return True

    def _set_buttons(self, state):
        for widget in self.root.winfo_children():
            if isinstance(widget, ttk.Frame):
                for child in widget.winfo_children():
                    if isinstance(child, ttk.Button):
                        child.config(state=state)

    def start_processing(self):
        if not self.validate_inputs():
            return
        self._set_buttons(tk.DISABLED)
        thread = threading.Thread(target=self._process_thread)
        thread.daemon = True
        thread.start()

    def _process_thread(self):
        try:
            player_name = self.player_name_var.get().strip()
            source_folder = self.source_folder_var.get().strip()
            output_folder = self.output_folder_var.get().strip()
            parser_url = self.parser_url_var.get().strip()
            batch_size = int(self.batch_size_var.get())
            dry_run = False  # Always execute (dry run option removed)
            parallel_threads = int(self.parallel_threads_var.get())
            
            # Get and validate date filters ("All dates" bypasses filtering)
            all_dates = self.all_dates_var.get()
            date_from = None
            date_to = None

            if not all_dates:
                date_from_str = self.date_from_var.get().strip()
                date_to_str = self.date_to_var.get().strip()
                try:
                    if date_from_str:
                        date_from = datetime.strptime(date_from_str, '%Y-%m-%d')
                    if date_to_str:
                        date_to = datetime.strptime(date_to_str, '%Y-%m-%d')
                except ValueError as e:
                    self.log_message(f"\nERROR: Invalid date format. Use YYYY-MM-DD (e.g., 2024-01-15)")
                    messagebox.showerror("Date Format Error", f"Invalid date format:\n{str(e)}")
                    return

            # Create date filter (disabled when both bounds are None / All dates)
            date_filter = DateFilter(date_from, date_to)

            self.log_message(f"\n{'='*60}")
            self.log_message("Starting Replay Batch Processing")
            self.log_message(f"{'='*60}")
            self.log_message(f"Player Name:   {player_name}")
            self.log_message(f"Source Folder: {source_folder}")
            self.log_message(f"Output Folder: {output_folder}")
            self.log_message(f"Parser URL:    {parser_url}")
            self.log_message(f"Batch Size:    {batch_size}")
            self.log_message(f"Threads:       {parallel_threads}")
            self.log_message(f"Mode:          EXECUTE")
            
            # Log date filter status
            if date_filter.enabled:
                filter_str = "Date Filter: Enabled"
                if date_from:
                    filter_str += f" | From: {date_from.strftime('%Y-%m-%d')}"
                if date_to:
                    filter_str += f" | To: {date_to.strftime('%Y-%m-%d')}"
                self.log_message(filter_str)
            else:
                self.log_message("Date Filter: Disabled (processing all files)")

            source_path = Path(source_folder)
            recursive = self.recursive_var.get()
            pattern_glob = source_path.rglob if recursive else source_path.glob
            replay_files = sorted(list(pattern_glob("*.w3g")))
            if recursive:
                self.log_message("Searching subfolders (recursive)")

            if not replay_files:
                self.log_message("\nNo .w3g files found in source folder")
                messagebox.showwarning("No Files", "No .w3g files found in the source folder")
                return

            self.log_message(f"\nFound {len(replay_files)} replay files in source folder")
            
            # Filter files by date
            filtered_files = []
            skipped_files = []
            
            for file_path in replay_files:
                should_process, skip_reason = date_filter.should_process(file_path)
                if should_process:
                    filtered_files.append(file_path)
                else:
                    skipped_files.append((file_path, skip_reason))
            
            if skipped_files:
                self.log_message(f"Skipped {len(skipped_files)} files due to date filter:")
                for skipped_file, reason in skipped_files[:5]:  # Show first 5
                    self.log_message(f"  - {skipped_file.name}: {reason}")
                if len(skipped_files) > 5:
                    self.log_message(f"  ... and {len(skipped_files) - 5} more")
            
            if not filtered_files:
                self.log_message("\nNo files match the date filter criteria")
                messagebox.showwarning("No Files", "No files match the date filter criteria")
                return
            
            self.log_message(f"Processing {len(filtered_files)} files (after date filtering)")

            renamer = ReplayRenamer(source_folder, parser_url)
            output_path = Path(output_folder)

            total_files = len(filtered_files)
            total_created = 0
            files_processed = 0
            batch_num = 1
            total_batches = (len(filtered_files) + batch_size - 1) // batch_size
            start_time = time.time()
            self.reset_progress("Processing...")

            for i in range(0, len(filtered_files), batch_size):
                batch_files = filtered_files[i:i + batch_size]
                batch_start = i + 1
                batch_end = min(i + batch_size, len(filtered_files))

                self.log_message(f"\n{'='*60}")
                self.log_message(f"BATCH {batch_num}/{total_batches} (Files {batch_start}-{batch_end})")
                self.log_message(f"{'='*60}")

                batch_successful = 0

                with ThreadPoolExecutor(max_workers=parallel_threads) as executor:
                    future_to_file = {
                        executor.submit(
                            self._process_single_file,
                            file_path, player_name, output_path, dry_run, renamer
                        ): file_path
                        for file_path in batch_files
                    }
                    for j, future in enumerate(as_completed(future_to_file), 1):
                        file_path = future_to_file[future]
                        try:
                            if future.result():
                                batch_successful += 1
                        except Exception as e:
                            self.log_message(f"[Error] {file_path.name}: {str(e)[:50]}")
                        files_processed += 1

                        # Drive the progress bar on every file (smooth movement).
                        elapsed = time.time() - start_time
                        rate = files_processed / elapsed if elapsed > 0 else 0
                        self.update_progress(files_processed, total_files, rate)

                        if j % max(1, len(batch_files) // 10) == 0 or j == len(batch_files):
                            self.log_message(
                                f"  Progress: {j}/{len(batch_files)} files ({rate:.1f} files/sec)")

                self.log_message(
                    f"Batch {batch_num} complete: {batch_successful}/{len(batch_files)} processed")
                total_created += batch_successful
                batch_num += 1

            elapsed = time.time() - start_time
            rate = len(filtered_files) / elapsed if elapsed > 0 else 0

            self.update_progress(total_files, total_files, rate)
            self.progress_status_var.set(
                f"Done - {total_created} files created from {total_files} processed "
                f"({rate:.1f} files/sec)")

            self.log_message(f"\n{'='*60}")
            self.log_message(f"[COMPLETE] Total: {total_created} files created")
            self.log_message(
                f"Processed {len(filtered_files)} files in {elapsed:.1f}s ({rate:.1f} files/sec)")
            if len(skipped_files) > 0:
                self.log_message(f"Skipped {len(skipped_files)} files (date filter)")
            self.log_message(f"{'='*60}")

            messagebox.showinfo("Processing Complete",
                                f"Processing completed!\n\n{total_created} files were created.\n\n"
                                f"Speed: {rate:.1f} files/sec")

            # Open the output folder in Explorer so results are immediately visible.
            try:
                if hasattr(os, 'startfile') and Path(output_folder).exists():
                    os.startfile(output_folder)
            except Exception as e:
                logging.warning(f"Could not open output folder: {e}")

        except Exception as e:
            self.log_message(f"\n\nERROR: {str(e)}")
            self.progress_status_var.set(f"Error: {str(e)[:60]}")
            messagebox.showerror("Error", f"An error occurred:\n\n{str(e)}")
        finally:
            self._set_buttons(tk.NORMAL)

    def _process_single_file(self, file_path: Path, player_name: str, output_path: Path,
                             dry_run: bool, renamer) -> bool:
        try:
            return renamer.create_player_file(file_path, player_name, output_path, dry_run=dry_run)
        except Exception:
            return False

    def clear_form(self):
        # Player profiles auto-save, so "Clear" just clears the log and progress
        # display rather than wiping the selected profile's fields.
        self.log_text.delete(1.0, tk.END)
        self.reset_progress("Idle")

    # ------------------------------------------------------------------
    # Date picker
    # ------------------------------------------------------------------

    def _pick_date(self, target_var, anchor):
        DatePickerPopup(self.root, target_var, anchor)

    def _toggle_date_inputs(self):
        """Disable the date inputs when 'All dates' is checked."""
        state = 'disabled' if self.all_dates_var.get() else 'normal'
        for w in (self.date_from_entry, self.date_from_btn,
                  self.date_to_entry, self.date_to_btn):
            try:
                w.config(state=state)
            except Exception:
                pass

    # ------------------------------------------------------------------
    # Player profiles + auto-save
    # ------------------------------------------------------------------

    def _install_autosave_traces(self):
        """Persist the current player's profile automatically when fields change."""
        for var in (self.player_name_var, self.source_folder_var, self.output_folder_var,
                    self.parser_url_var, self.batch_size_var, self.parallel_threads_var,
                    self.date_from_var, self.date_to_var, self.all_dates_var):
            var.trace_add('write', self._on_field_changed)

    def _on_field_changed(self, *_):
        if self._loading:
            return
        # Debounce: collapse rapid keystrokes into a single save.
        if self._autosave_job is not None:
            try:
                self.root.after_cancel(self._autosave_job)
            except Exception:
                pass
        self._autosave_job = self.root.after(700, self._do_autosave)

    def _do_autosave(self):
        self._autosave_job = None
        try:
            self._write_current_settings()
            self.config.save_config()
            self._save_settings_json()
            # Keep the dropdown label in sync if the player name changed.
            self._populate_player_dropdown(select=self.player_name_var.get().strip())
            logging.debug("Auto-saved profile")
        except Exception as e:
            logging.warning(f"Auto-save failed: {e}")

    def _write_current_settings(self):
        """Copy all form fields into the active ConfigManager (without saving)."""
        self.config.set('player_name', self.player_name_var.get())
        self.config.set('input_folder', self.source_folder_var.get())
        self.config.set('output_folder', self.output_folder_var.get())
        self.config.set('parser_url', self.parser_url_var.get())
        self.config.set('batch_size', self.batch_size_var.get())
        self.config.set('parallel_threads', self.parallel_threads_var.get())
        self.config.set('date_from', self.date_from_var.get())
        self.config.set('date_to', self.date_to_var.get())
        self.config.set('all_dates', str(self.all_dates_var.get()))
        self.config.set('recursive', str(self.recursive_var.get()))

    def _list_player_profiles(self):
        """Return {display_name: Path} for every .ini profile in the config dir."""
        profiles = {}
        try:
            entries = []  # (player_name, Path)
            for ini in sorted(self._config_dir.glob('*.ini')):
                try:
                    cm = ConfigManager(str(ini))
                    name = (cm.get('player_name', default='') or '').strip()
                except Exception:
                    name = ''
                entries.append((name or ini.stem, ini))

            # Disambiguate identical player names using the file stem, e.g.
            # "crucibles [cedric]" so duplicate profiles stay distinguishable.
            counts = {}
            for name, _ in entries:
                counts[name] = counts.get(name, 0) + 1
            for name, ini in entries:
                display = name if counts[name] == 1 else f"{name} [{ini.stem}]"
                profiles[display] = ini
        except Exception as e:
            logging.warning(f"Could not list player profiles: {e}")
        return profiles

    def _populate_player_dropdown(self, select=None):
        """Refresh the player dropdown values; optionally keep a name selected."""
        try:
            self._profile_paths = self._list_player_profiles()
            names = sorted(self._profile_paths.keys(), key=str.lower)
            self.player_dropdown['values'] = names
            if select:
                # Don't clobber what the user is typing; just leave the var as-is.
                self.player_name_var.set(select)
        except Exception as e:
            logging.warning(f"Could not populate player dropdown: {e}")

    def on_player_selected(self, event=None):
        """Load the selected player's saved profile."""
        try:
            selected = self.player_name_var.get().strip()
            path = self._profile_paths.get(selected)
            if not path or not Path(path).exists():
                return
            self.config = ConfigManager(str(path))
            logging.info(f"Loaded profile for player '{selected}'")
            self.load_settings()
        except Exception as e:
            logging.error(f"Could not load player profile: {e}")

    def add_new_player(self):
        """Create a new player profile, keeping the current folders as a starting point."""
        name = simpledialog.askstring("Add New Player", "Enter new player name:",
                                      parent=self.root)
        if not name or not name.strip():
            return
        self._create_player_profile(name.strip())

    def _create_player_profile(self, name):
        """Create/select a player profile on disk for the given name."""
        safe = re.sub(r'[<>:"/\\|?*]', '', name) or "player"
        path = self._config_dir / f"{safe}.ini"
        try:
            self.config = ConfigManager(str(path))
            self.player_name_var.set(name)
            # Persist immediately so the profile exists on disk.
            self._write_current_settings()
            self.config.save_config()
            self._populate_player_dropdown(select=name)
            self.player_dropdown.set(name)
            logging.info(f"Created new player profile '{name}' at {path.name}")
        except Exception as e:
            logging.error(f"Could not create new player profile: {e}")
            messagebox.showerror("Error", f"Could not create player profile:\n{e}")

    def prompt_initial_player(self):
        """On startup, ask for the player name first when none is selected yet."""
        if self.player_name_var.get().strip():
            return
        name = simpledialog.askstring(
            "Player Name",
            "Enter the player name to sort replays for:",
            parent=self.root)
        if name and name.strip():
            self._create_player_profile(name.strip())

    def load_settings(self):
        """Load settings from the active profile (and settings.json for back-compat)."""
        self._loading = True  # suppress auto-save while we populate fields
        try:
            # Try loading from the active config first (via config manager)
            self.player_name_var.set(self.config.get('player_name', default=''))
            # Default the source to the current user's WC3 replay folder when unset.
            src = (self.config.get('input_folder', default='') or '').strip()
            if not src or src in ('./input', '.\\input'):
                src = _default_source_folder()
            self.source_folder_var.set(src)
            # Default the output to Desktop/replay-output when unset, and create it.
            out = (self.config.get('output_folder', default='') or '').strip()
            if not out or out in ('./output', '.\\output'):
                out = _default_output_folder()
            try:
                Path(out).mkdir(parents=True, exist_ok=True)
            except Exception as e:
                logging.warning(f"Could not create default output folder '{out}': {e}")
            self.output_folder_var.set(out)
            self.parser_url_var.set(self.config.get('parser_url', default='http://localhost:3000'))
            self.batch_size_var.set(str(self.config.get_int('batch_size', default=500)))
            self.parallel_threads_var.set(str(self.config.get_int('parallel_threads', default=8)))

            # Load date filters - if empty, show the calculated defaults
            date_from_config = self.config.get('date_from', default='').strip()
            date_to_config = self.config.get('date_to', default='').strip()

            # If both empty, populate with calculated defaults (last 30 days)
            if not date_from_config and not date_to_config:
                from datetime import datetime, timedelta
                date_from_default = (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d')
                date_to_default = datetime.now().strftime('%Y-%m-%d')
                self.date_from_var.set(date_from_default)
                self.date_to_var.set(date_to_default)
            else:
                self.date_from_var.set(date_from_config)
                self.date_to_var.set(date_to_config)

            # "All dates" toggle (disables the date inputs when on). Defaults ON so
            # a fresh profile processes every replay regardless of date.
            self.all_dates_var.set(self.config.get_bool('all_dates', default=True))
            self.recursive_var.set(self.config.get_bool('recursive', default=True))
            self._toggle_date_inputs()

            logging.info("Loaded settings from active profile")

            # Populate the player dropdown and keep the current player selected
            self._populate_player_dropdown(select=self.player_name_var.get().strip())
        except Exception as e:
            logging.warning(f"Could not load settings from profile: {e}")
            # Fall back to settings.json if available
            self._load_settings_json()
        finally:
            self._loading = False
    
    def _load_settings_json(self):
        """Load settings from legacy settings.json for backward compatibility"""
        settings_file = self._config_dir / "settings.json"
        if settings_file.exists():
            try:
                with open(settings_file, 'r') as f:
                    settings = json.load(f)
                    self.player_name_var.set(settings.get("player_name", ""))
                    self.source_folder_var.set(settings.get("source_folder", ""))
                    self.output_folder_var.set(settings.get("output_folder", ""))
                    self.parser_url_var.set(settings.get("parser_url", "http://localhost:3000"))
                    self.batch_size_var.set(settings.get("batch_size", "500"))
                    self.parallel_threads_var.set(settings.get("parallel_threads", "8"))
                    logging.info("Loaded settings from legacy settings.json")
            except Exception as e:
                logging.warning(f"Could not load legacy settings: {e}")

    def save_settings(self):
        """Save the active player's profile and the legacy settings.json."""
        try:
            self._write_current_settings()
            self.config.save_config()
            logging.info("Saved settings to active profile")
        except Exception as e:
            logging.warning(f"Could not save settings to profile: {e}")

        # Also save to legacy settings.json for backward compatibility
        self._save_settings_json()

    def _save_settings_json(self):
        """Save settings to legacy settings.json for backward compatibility"""
        settings_file = self._config_dir / "settings.json"
        try:
            settings = {
                "player_name": self.player_name_var.get(),
                "source_folder": self.source_folder_var.get(),
                "output_folder": self.output_folder_var.get(),
                "parser_url": self.parser_url_var.get(),
                "batch_size": self.batch_size_var.get(),
                "parallel_threads": self.parallel_threads_var.get()
            }
            with open(settings_file, 'w') as f:
                json.dump(settings, f, indent=2)
            logging.debug("Saved settings to legacy settings.json")
        except Exception as e:
            logging.warning(f"Could not save legacy settings: {e}")


def main():
    # Initialize logging
    setup_logging(log_level='INFO', log_file='replay_processor.log', console_output=True)
    logger = logging.getLogger(__name__)
    logger.info("Starting Replay Batch Processor")
    
    # Initialize configuration manager (next to the exe/script, not the CWD,
    # so profiles persist correctly when running as a frozen .exe).
    config_path = _app_base_dir() / 'config.ini'
    config_manager = ConfigManager(str(config_path))
    logger.info(f"Loaded configuration from {config_path}")
    
    # Create GUI with config manager
    root = tk.Tk()
    app = ReplayBatchProcessorGUI(root, config_manager)

    # Auto-start the local replay parser (port 3000) in the background so the
    # user doesn't have to launch it manually. Logs progress into the GUI.
    parser_url = config_manager.get('parser_url', default='http://localhost:3000')
    parser_dir_cfg = (config_manager.get('parser_dir', default='') or '').strip()
    parser_exe_cfg = (config_manager.get('parser_exe', default='') or '').strip()
    parser_manager = ParserServerManager(parser_url, parser_dir_cfg or None,
                                         parser_exe_cfg or None)
    app.parser_manager = parser_manager
    atexit.register(parser_manager.stop)

    def _gui_log(msg):
        root.after(0, lambda: app.log_message(msg))

    def _start_parser():
        parser_manager.ensure_running(log=_gui_log)

    threading.Thread(target=_start_parser, daemon=True).start()

    def on_closing():
        logger.info("Closing application")
        app.save_settings()
        parser_manager.stop()
        root.destroy()

    root.protocol("WM_DELETE_WINDOW", on_closing)
    root.mainloop()


if __name__ == "__main__":
    main()
