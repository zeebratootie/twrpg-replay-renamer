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

# Try to import ReplayRenamer from various locations
ReplayRenamer = None
try:
    # First try: look in current directory (for bundled .exe)
    current_dir = os.path.dirname(os.path.abspath(__file__))
    if current_dir not in sys.path:
        sys.path.insert(0, current_dir)
    from rename_replays import ReplayRenamer
except ImportError:
    try:
        # Second try: look in parent directory (for script execution)
        parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        if parent_dir not in sys.path:
            sys.path.insert(0, parent_dir)
        from rename_replays import ReplayRenamer
    except ImportError:
        print("WARNING: Could not import ReplayRenamer. Some features may not work.")

class ReplayBatchProcessorGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Replay Batch Processor")
        self.root.geometry("600x700")
        self.root.resizable(True, True)
        
        # Configure style
        self.root.configure(bg="#f0f0f0")
        style = ttk.Style()
        style.theme_use('clam')
        
        self.setup_ui()
        self.load_settings()
        
    def setup_ui(self):
        """Create the user interface"""
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Title
        title_label = ttk.Label(main_frame, text="Replay Batch Processor", 
                               font=("Arial", 16, "bold"))
        title_label.grid(row=0, column=0, columnspan=3, pady=10)
        
        current_row = 1
        
        # Player Name Section
        ttk.Label(main_frame, text="Player Name:", font=("Arial", 10)).grid(
            row=current_row, column=0, sticky=tk.W, pady=5)
        self.player_name_var = tk.StringVar()
        player_entry = ttk.Entry(main_frame, textvariable=self.player_name_var, width=40)
        player_entry.grid(row=current_row, column=1, columnspan=2, sticky=(tk.W, tk.E), padx=5)
        current_row += 1
        
        # Source Folder Section
        ttk.Label(main_frame, text="Source Replay Folder:", font=("Arial", 10)).grid(
            row=current_row, column=0, sticky=tk.W, pady=5)
        self.source_folder_var = tk.StringVar()
        source_entry = ttk.Entry(main_frame, textvariable=self.source_folder_var, width=40)
        source_entry.grid(row=current_row, column=1, sticky=(tk.W, tk.E), padx=5)
        ttk.Button(main_frame, text="Browse...", 
                  command=self.browse_source_folder).grid(row=current_row, column=2, padx=5)
        current_row += 1
        
        # Output Folder Section
        ttk.Label(main_frame, text="Output Folder:", font=("Arial", 10)).grid(
            row=current_row, column=0, sticky=tk.W, pady=5)
        self.output_folder_var = tk.StringVar()
        output_entry = ttk.Entry(main_frame, textvariable=self.output_folder_var, width=40)
        output_entry.grid(row=current_row, column=1, sticky=(tk.W, tk.E), padx=5)
        ttk.Button(main_frame, text="Browse...", 
                  command=self.browse_output_folder).grid(row=current_row, column=2, padx=5)
        current_row += 1
        
        # Parser URL Section
        ttk.Label(main_frame, text="Parser URL:", font=("Arial", 10)).grid(
            row=current_row, column=0, sticky=tk.W, pady=5)
        self.parser_url_var = tk.StringVar(value="http://localhost:3000")
        parser_entry = ttk.Entry(main_frame, textvariable=self.parser_url_var, width=40)
        parser_entry.grid(row=current_row, column=1, columnspan=2, sticky=(tk.W, tk.E), padx=5)
        current_row += 1
        
        # Batch Size Section
        ttk.Label(main_frame, text="Batch Size:", font=("Arial", 10)).grid(
            row=current_row, column=0, sticky=tk.W, pady=5)
        self.batch_size_var = tk.StringVar(value="50")
        batch_entry = ttk.Entry(main_frame, textvariable=self.batch_size_var, width=10)
        batch_entry.grid(row=current_row, column=1, sticky=tk.W, padx=5)
        current_row += 1
        
        # Separator
        ttk.Separator(main_frame, orient='horizontal').grid(
            row=current_row, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=10)
        current_row += 1
        
        # Options Section
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
        
        # Separator
        ttk.Separator(main_frame, orient='horizontal').grid(
            row=current_row, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=10)
        current_row += 1
        
        # Buttons
        button_frame = ttk.Frame(main_frame)
        button_frame.grid(row=current_row, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=10)
        
        ttk.Button(button_frame, text="Start Processing", 
                  command=self.start_processing).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Clear", 
                  command=self.clear_form).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Exit", 
                  command=self.root.quit).pack(side=tk.LEFT, padx=5)
        
        current_row += 1
        
        # Output Log Section
        ttk.Label(main_frame, text="Processing Log:", font=("Arial", 10)).grid(
            row=current_row, column=0, columnspan=3, sticky=tk.W, pady=(10, 5))
        current_row += 1
        
        # Text widget with scrollbar
        log_frame = ttk.Frame(main_frame)
        log_frame.grid(row=current_row, column=0, columnspan=3, sticky=(tk.W, tk.E, tk.N, tk.S), pady=5)
        
        scrollbar = ttk.Scrollbar(log_frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.log_text = tk.Text(log_frame, height=15, width=70, yscrollcommand=scrollbar.set)
        self.log_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.config(command=self.log_text.yview)
        
        # Configure grid weights for resizing
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)
        
    def log_message(self, message, end="\n"):
        """Add a message to the log"""
        self.log_text.insert(tk.END, message + end)
        self.log_text.see(tk.END)
        self.root.update()
        
    def browse_source_folder(self):
        """Browse for source folder"""
        folder = filedialog.askdirectory(title="Select Source Replay Folder")
        if folder:
            self.source_folder_var.set(folder)
            
    def browse_output_folder(self):
        """Browse for output folder"""
        folder = filedialog.askdirectory(title="Select Output Folder")
        if folder:
            self.output_folder_var.set(folder)
            
    def validate_inputs(self):
        """Validate user inputs"""
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
            batch_size = int(self.batch_size_var.get())
            if batch_size <= 0:
                raise ValueError
        except ValueError:
            messagebox.showerror("Error", "Batch size must be a positive integer")
            return False
            
        return True
        
    def start_processing(self):
        """Start processing replays"""
        if not self.validate_inputs():
            return
            
        # Disable button to prevent multiple clicks
        for widget in self.root.winfo_children():
            if isinstance(widget, ttk.Frame):
                for child in widget.winfo_children():
                    if isinstance(child, ttk.Button):
                        child.config(state=tk.DISABLED)
        
        # Run in separate thread to prevent UI freezing
        thread = threading.Thread(target=self._process_thread)
        thread.daemon = True
        thread.start()
        
    def _process_thread(self):
        """Process replays in a separate thread"""
        try:
            # Check if ReplayRenamer is available
            if ReplayRenamer is None:
                self.log_message("\nERROR: ReplayRenamer module not found!")
                self.log_message("Please ensure rename_replays.py exists in the parent directory:")
                self.log_message(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
                messagebox.showerror("Error", "ReplayRenamer module not found. Please check installation.")
                return
            
            player_name = self.player_name_var.get().strip()
            source_folder = self.source_folder_var.get().strip()
            output_folder = self.output_folder_var.get().strip()
            parser_url = self.parser_url_var.get().strip()
            batch_size = int(self.batch_size_var.get())
            dry_run = self.dry_run_var.get()
            
            self.log_message(f"\n{'='*60}")
            self.log_message("Starting Replay Batch Processing")
            self.log_message(f"{'='*60}")
            self.log_message(f"Player Name: {player_name}")
            self.log_message(f"Source Folder: {source_folder}")
            self.log_message(f"Output Folder: {output_folder}")
            self.log_message(f"Parser URL: {parser_url}")
            self.log_message(f"Batch Size: {batch_size}")
            self.log_message(f"Mode: {'DRY RUN' if dry_run else 'EXECUTE'}")
            
            # Get all replay files
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
            
            for i in range(0, len(replay_files), batch_size):
                batch_files = replay_files[i:i+batch_size]
                batch_start = i + 1
                batch_end = min(i + batch_size, len(replay_files))
                
                self.log_message(f"\n{'='*60}")
                self.log_message(f"BATCH {batch_num}/{total_batches} (Files {batch_start}-{batch_end})")
                self.log_message(f"{'='*60}")
                
                successful = 0
                
                for j, file_path in enumerate(batch_files, 1):
                    try:
                        self.log_message(f"[{batch_num}/{total_batches}][{j}/{len(batch_files)}] Processing: {file_path.name}...", end="")
                        
                        if renamer.create_player_file(file_path, player_name, output_path, dry_run=dry_run):
                            successful += 1
                            status = "✓ Would create" if dry_run else "✓ Created"
                            self.log_message(f" {status}")
                        else:
                            self.log_message(f" - Skipped")
                            
                        files_processed += 1
                    except Exception as e:
                        self.log_message(f" ✗ Error: {str(e)[:50]}")
                        files_processed += 1
                
                self.log_message(f"Batch {batch_num} complete: {successful} files processed from {len(batch_files)}")
                total_created += successful
                batch_num += 1
            
            self.log_message(f"\n{'='*60}")
            self.log_message(f"[COMPLETE] Total: {total_created} files {'would be created' if dry_run else 'created'}")
            self.log_message(f"{'='*60}")
            
            if dry_run:
                messagebox.showinfo("Dry Run Complete", 
                                   f"Dry run completed!\n\n{total_created} files would be created.\n\n"
                                   "Uncheck 'Dry Run' and click 'Start Processing' to execute.")
            else:
                messagebox.showinfo("Processing Complete", 
                                   f"Processing completed!\n\n{total_created} files were created.")
                
        except Exception as e:
            self.log_message(f"\n\nERROR: {str(e)}")
            messagebox.showerror("Error", f"An error occurred:\n\n{str(e)}")
            
        finally:
            # Re-enable buttons
            for widget in self.root.winfo_children():
                if isinstance(widget, ttk.Frame):
                    for child in widget.winfo_children():
                        if isinstance(child, ttk.Button):
                            child.config(state=tk.NORMAL)
                            
    def clear_form(self):
        """Clear the form"""
        self.player_name_var.set("")
        self.source_folder_var.set("")
        self.output_folder_var.set("")
        self.log_text.delete(1.0, tk.END)
        
    def load_settings(self):
        """Load saved settings"""
        settings_file = Path(__file__).parent / "settings.json"
        if settings_file.exists():
            try:
                with open(settings_file, 'r') as f:
                    settings = json.load(f)
                    self.player_name_var.set(settings.get("player_name", ""))
                    self.source_folder_var.set(settings.get("source_folder", ""))
                    self.output_folder_var.set(settings.get("output_folder", ""))
                    self.parser_url_var.set(settings.get("parser_url", "http://localhost:3000"))
                    self.batch_size_var.set(settings.get("batch_size", "50"))
            except Exception as e:
                print(f"Could not load settings: {e}")
                
    def save_settings(self):
        """Save settings"""
        settings_file = Path(__file__).parent / "settings.json"
        try:
            settings = {
                "player_name": self.player_name_var.get(),
                "source_folder": self.source_folder_var.get(),
                "output_folder": self.output_folder_var.get(),
                "parser_url": self.parser_url_var.get(),
                "batch_size": self.batch_size_var.get()
            }
            with open(settings_file, 'w') as f:
                json.dump(settings, f, indent=2)
        except Exception as e:
            print(f"Could not save settings: {e}")


def main():
    root = tk.Tk()
    app = ReplayBatchProcessorGUI(root)
    
    # Save settings on close
    def on_closing():
        app.save_settings()
        root.destroy()
    
    root.protocol("WM_DELETE_WINDOW", on_closing)
    root.mainloop()


if __name__ == "__main__":
    main()
