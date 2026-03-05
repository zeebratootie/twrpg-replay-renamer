#!/usr/bin/env python3
"""
Replay Batch Processor GUI Application
A Windows desktop application for batch processing W3G replay files
"""

import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import threading
import os
from pathlib import Path
import sys
import json
from concurrent.futures import ThreadPoolExecutor, as_completed
import time
import re
import shutil
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from datetime import datetime, timedelta


# ---------------------------------------------------------------------------
# ReplayRenamer - inlined so no external file is needed at runtime
# ---------------------------------------------------------------------------

class ReplayRenamer:
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
        for prefix in sorted(known_prefixes, key=len, reverse=True):
            if base.startswith(prefix):
                return prefix
        return base if base else class_name.lower()

    def get_player_class(self, parsed_data, player_name):
        if not parsed_data:
            return "unknown"
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
                                return class_part
                    if '-load ' in message:
                        parts = message.split('-load ')
                        if len(parts) > 1:
                            class_part = parts[1].split()[0].strip()
                            if class_part and len(class_part) < 20 and not any(c.isdigit() for c in class_part):
                                return class_part
                    if '-save ' in message:
                        parts = message.split('-save ')
                        if len(parts) > 1:
                            class_part = parts[1].split()[0].strip()
                            if '/' in class_part:
                                class_part = class_part.split('/')[0].strip()
                            if class_part and len(class_part) < 20 and class_part not in ['game', 'all']:
                                return class_part
        if 'playerData' in parsed_data:
            for player in parsed_data['playerData']:
                if (player.get('playerName', '').lower() == player_name.lower() or
                        player.get('convertedName', '').lower() == player_name.lower()):
                    class_value = player.get('class') or player.get('hero') or player.get('race')
                    if class_value:
                        return self.extract_base_class(class_value)
        return "unknown"

    def generate_player_specific_filename(self, parsed_data, player_name, original_file_path):
        if not parsed_data or 'loots' not in parsed_data:
            return None
        if isinstance(original_file_path, str):
            original_file_path = Path(original_file_path)
        player_loots = []
        for loot in parsed_data['loots']:
            loot_player = loot['playerName']
            clean_loot_player = re.sub(r'#\d+.*', '', loot_player)
            clean_loot_player = re.sub(r'\([^)]*\)', '', clean_loot_player).strip()
            if clean_loot_player.lower() == player_name.lower():
                item_name = re.sub(r'[<>:"/\\|?*]', '', loot['itemName'])
                player_loots.append(item_name)
        if not player_loots:
            return None
        player_class = self.extract_base_class(self.get_player_class(parsed_data, player_name))
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
        new_filename = f"{player_name} - {player_class} - {loots_str}{craft_suffix}{date_suffix}.w3g"
        new_filename = re.sub(r'[<>:"/\\|?*]', '', new_filename)
        return new_filename

    def create_player_file(self, original_file_path, player_name, base_output_folder, dry_run=True):
        parsed_data = self.parse_replay(original_file_path)
        if not parsed_data:
            print(f"Failed to parse {original_file_path}")
            return False
        new_name = self.generate_player_specific_filename(parsed_data, player_name, original_file_path)
        if not new_name:
            print(f"No loots found for player '{player_name}' in {original_file_path.name}")
            return False
        parts = new_name.split(' - ')
        player_class = parts[1] if len(parts) >= 2 else "unknown"
        output_path = Path(base_output_folder) / player_name / player_class
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
                print(f"DRY RUN: Would copy '{original_file_path.name}' to '{player_name}/{player_class}/{new_name}'")
                return True
            else:
                shutil.copy2(original_file_path, new_file_path)
                print(f"Copied to '{player_name}/{player_class}/{new_name}'")
                return True
        except Exception as e:
            print(f"Error creating file: {e}")
            return False


# ---------------------------------------------------------------------------
# GUI
# ---------------------------------------------------------------------------

class ReplayBatchProcessorGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Replay Batch Processor")
        self.root.geometry("600x700")
        self.root.resizable(True, True)
        self.root.configure(bg="#f0f0f0")
        style = ttk.Style()
        style.theme_use('clam')
        self.setup_ui()
        self.load_settings()

    def setup_ui(self):
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))

        ttk.Label(main_frame, text="Replay Batch Processor",
                  font=("Arial", 16, "bold")).grid(row=0, column=0, columnspan=3, pady=10)

        current_row = 1

        ttk.Label(main_frame, text="Player Name:", font=("Arial", 10)).grid(
            row=current_row, column=0, sticky=tk.W, pady=5)
        self.player_name_var = tk.StringVar()
        ttk.Entry(main_frame, textvariable=self.player_name_var, width=40).grid(
            row=current_row, column=1, columnspan=2, sticky=(tk.W, tk.E), padx=5)
        current_row += 1

        ttk.Label(main_frame, text="Source Replay Folder:", font=("Arial", 10)).grid(
            row=current_row, column=0, sticky=tk.W, pady=5)
        self.source_folder_var = tk.StringVar()
        ttk.Entry(main_frame, textvariable=self.source_folder_var, width=40).grid(
            row=current_row, column=1, sticky=(tk.W, tk.E), padx=5)
        ttk.Button(main_frame, text="Browse...",
                   command=self.browse_source_folder).grid(row=current_row, column=2, padx=5)
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

        options_frame = ttk.LabelFrame(main_frame, text="Options", padding="5")
        options_frame.grid(row=current_row, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=5)
        self.dry_run_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(options_frame, text="Dry Run (preview without creating files)",
                        variable=self.dry_run_var).pack(anchor=tk.W, pady=5)
        self.skip_existing_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(options_frame, text="Skip existing files",
                        variable=self.skip_existing_var).pack(anchor=tk.W, pady=5)
        self.no_prompt_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(options_frame, text="Process all batches without prompting",
                        variable=self.no_prompt_var).pack(anchor=tk.W, pady=5)
        current_row += 1

        ttk.Separator(main_frame, orient='horizontal').grid(
            row=current_row, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=10)
        current_row += 1

        button_frame = ttk.Frame(main_frame)
        button_frame.grid(row=current_row, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=10)
        ttk.Button(button_frame, text="Start Processing",
                   command=self.start_processing).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Clear",
                   command=self.clear_form).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Exit",
                   command=self.root.quit).pack(side=tk.LEFT, padx=5)
        current_row += 1

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

    def log_message(self, message, end="\n"):
        self.log_text.insert(tk.END, message + end)
        self.log_text.see(tk.END)
        self.root.update()

    def browse_source_folder(self):
        folder = filedialog.askdirectory(title="Select Source Replay Folder")
        if folder:
            self.source_folder_var.set(folder)

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
            dry_run = self.dry_run_var.get()
            parallel_threads = int(self.parallel_threads_var.get())

            self.log_message(f"\n{'='*60}")
            self.log_message("Starting Replay Batch Processing")
            self.log_message(f"{'='*60}")
            self.log_message(f"Player Name:   {player_name}")
            self.log_message(f"Source Folder: {source_folder}")
            self.log_message(f"Output Folder: {output_folder}")
            self.log_message(f"Parser URL:    {parser_url}")
            self.log_message(f"Batch Size:    {batch_size}")
            self.log_message(f"Threads:       {parallel_threads}")
            self.log_message(f"Mode:          {'DRY RUN' if dry_run else 'EXECUTE'}")

            source_path = Path(source_folder)
            replay_files = sorted(list(source_path.glob("*.w3g")))

            if not replay_files:
                self.log_message("\nNo .w3g files found in source folder")
                messagebox.showwarning("No Files", "No .w3g files found in the source folder")
                return

            self.log_message(f"\nFound {len(replay_files)} replay files")

            renamer = ReplayRenamer(source_folder, parser_url)
            output_path = Path(output_folder)

            total_created = 0
            files_processed = 0
            batch_num = 1
            total_batches = (len(replay_files) + batch_size - 1) // batch_size
            start_time = time.time()

            for i in range(0, len(replay_files), batch_size):
                batch_files = replay_files[i:i + batch_size]
                batch_start = i + 1
                batch_end = min(i + batch_size, len(replay_files))

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

                        if j % max(1, len(batch_files) // 10) == 0 or j == len(batch_files):
                            elapsed = time.time() - start_time
                            rate = files_processed / elapsed if elapsed > 0 else 0
                            self.log_message(
                                f"  Progress: {j}/{len(batch_files)} files ({rate:.1f} files/sec)")

                self.log_message(
                    f"Batch {batch_num} complete: {batch_successful}/{len(batch_files)} processed")
                total_created += batch_successful
                batch_num += 1

            elapsed = time.time() - start_time
            rate = len(replay_files) / elapsed if elapsed > 0 else 0

            self.log_message(f"\n{'='*60}")
            self.log_message(
                f"[COMPLETE] Total: {total_created} files "
                f"{'would be created' if dry_run else 'created'}")
            self.log_message(
                f"Processed {len(replay_files)} files in {elapsed:.1f}s ({rate:.1f} files/sec)")
            self.log_message(f"{'='*60}")

            if dry_run:
                messagebox.showinfo("Dry Run Complete",
                                    f"Dry run completed!\n\n{total_created} files would be created.\n\n"
                                    f"Speed: {rate:.1f} files/sec\n\n"
                                    "Uncheck 'Dry Run' and click 'Start Processing' to execute.")
            else:
                messagebox.showinfo("Processing Complete",
                                    f"Processing completed!\n\n{total_created} files were created.\n\n"
                                    f"Speed: {rate:.1f} files/sec")

        except Exception as e:
            self.log_message(f"\n\nERROR: {str(e)}")
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
        self.player_name_var.set("")
        self.source_folder_var.set("")
        self.output_folder_var.set("")
        self.log_text.delete(1.0, tk.END)

    def load_settings(self):
        settings_file = Path(__file__).parent / "settings.json"
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
            except Exception as e:
                print(f"Could not load settings: {e}")

    def save_settings(self):
        settings_file = Path(__file__).parent / "settings.json"
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
        except Exception as e:
            print(f"Could not save settings: {e}")


def main():
    root = tk.Tk()
    app = ReplayBatchProcessorGUI(root)

    def on_closing():
        app.save_settings()
        root.destroy()

    root.protocol("WM_DELETE_WINDOW", on_closing)
    root.mainloop()


if __name__ == "__main__":
    main()
