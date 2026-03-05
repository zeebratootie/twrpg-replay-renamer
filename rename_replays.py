#!/usr/bin/env python3
"""
Replay Renamer Script
Renames Warcraft 3 replay files based on loot information from localhost:3000 parser
Format: [player-X] - (itemX)
"""

import os
import json
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from datetime import datetime, timedelta
from pathlib import Path
import re
import argparse
import shutil

class ReplayRenamer:
    def __init__(self, replay_folder, parser_url="http://localhost:3000"):
        self.replay_folder = Path(replay_folder)
        self.parser_url = parser_url
        self.last_month = datetime.now() - timedelta(days=30)
        
        # Create a session with connection pooling for faster concurrent requests
        self.session = requests.Session()
        
        # Configure retry strategy
        retry_strategy = Retry(
            total=2,
            backoff_factor=0.1,
            status_forcelist=[429, 500, 502, 503, 504],
        )
        
        # Use HTTPAdapter with connection pooling
        adapter = HTTPAdapter(
            max_retries=retry_strategy,
            pool_connections=16,  # Connection pool size
            pool_maxsize=16       # Max connection pool size
        )
        self.session.mount("http://", adapter)
        self.session.mount("https://", adapter)
        
    def get_file_modified_date(self, file_path):
        """Get the modification date of a file"""
        return datetime.fromtimestamp(os.path.getmtime(file_path))
    
    def is_from_last_month(self, file_path):
        """Check if file was modified in the last month - DISABLED, process all files"""
        # Always return True to process all files regardless of date
        return True
    
    def parse_replay(self, file_path):
        """Send replay file to parser and get loot information"""
        try:
            with open(file_path, 'rb') as f:
                files = {'file': f}  # Use 'file' as field name
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
    
    def extract_loot_info(self, parsed_data):
        """Extract player and loot information from parsed data"""
        if not parsed_data:
            return None
            
        try:
            # Extract data based on the actual parser response structure
            players = []
            items = []
            
            # Get player names from playerData
            if 'playerData' in parsed_data:
                for player in parsed_data['playerData']:
                    if 'playerName' in player:
                        players.append(player['playerName'])
                        
            # Get items from loots array
            if 'loots' in parsed_data:
                for loot in parsed_data['loots']:
                    if 'itemName' in loot:
                        items.append(loot['itemName'])
                    # Also add player name if not already in players list
                    if 'playerName' in loot and loot['playerName'] not in players:
                        players.append(loot['playerName'])
                    
            return {
                'players': players,
                'items': items
            }
        except Exception as e:
            print(f"Error extracting loot info: {e}")
            return None
    
    def generate_new_filename(self, loot_info, original_filename):
        """Generate new filename with all players and their loots"""
        if not loot_info or not loot_info.get('items'):
            return None
            
        # Create player-loot pairs from the parsed data
        player_loots = {}
        
        # Group items by player (assuming we have the raw parsed data available)
        # We'll need to modify extract_loot_info to preserve this relationship
        return None  # Placeholder - need to modify extract_loot_info first
    
    def extract_base_class(self, class_name):
        """Extract base class letters from names like 'amror' -> 'am', 'merch18-fc' -> 'merch', 'th1' -> 'th'
        Known class abbreviations: am, merch, bm, th, knight, druid, dd, etc.
        """
        if not class_name or class_name == "unknown":
            return class_name
        
        base = class_name.lower().strip()
        
        # Remove everything after first hyphen
        if '-' in base:
            base = base.split('-')[0]
        
        # Remove trailing digits
        base = base.rstrip('0123456789')
        
        # Now remove any trailing letters that are NOT part of common class names
        # by finding the longest known class prefix
        known_prefixes = ['merch', 'knight', 'druid', 'th', 'am', 'bm', 'dd', 'ud', 'wim', 'cpal', 'paladin', 'demon', 'mage']
        
        for prefix in sorted(known_prefixes, key=len, reverse=True):
            if base.startswith(prefix):
                return prefix
        
        # If no known prefix found, just return what we have (fallback)
        return base if base else class_name.lower()
    
    def get_player_class(self, parsed_data, player_name):
        """Extract player class from parsed data
        Priority: Chat -l/-load/-save commands from crucibles > playerData (with base extraction) > unknown
        Searches chat history for commands like: crucibles -l merch, crucibles -load am, crucibles -save bm
        """
        if not parsed_data:
            return "unknown"
        
        # HIGHEST PRIORITY: Check chat messages for -l, -load, -save commands
        # Look for any message containing player_name and a class loading command
        if 'chatData' in parsed_data:
            for chat in parsed_data['chatData']:
                chat_player = chat.get('player', '').lower()
                message = chat.get('message', '').lower()
                
                # Check if this chat message is from crucibles (exact match or starts with)
                if chat_player == player_name.lower() or chat_player.startswith(player_name.lower() + '#'):
                    # Priority order: -l > -load > -save
                    
                    # Check for -l command (e.g., "crucibles -l merch" or just "-l merch")
                    if '-l ' in message:
                        parts = message.split('-l ')
                        if len(parts) > 1:
                            class_part = parts[1].split()[0].strip()
                            if class_part and len(class_part) < 20 and class_part not in ['game', 'all']:
                                return class_part
                    
                    # Check for -load command (e.g., "crucibles -load am" or just "-load am")
                    if '-load ' in message:
                        parts = message.split('-load ')
                        if len(parts) > 1:
                            class_part = parts[1].split()[0].strip()
                            if class_part and len(class_part) < 20 and not any(char.isdigit() for char in class_part):
                                return class_part
                    
                    # Check for -save command (e.g., "crucibles -save bm" or "-save am/ror")
                    if '-save ' in message:
                        parts = message.split('-save ')
                        if len(parts) > 1:
                            class_part = parts[1].split()[0].strip()
                            # Handle format like "am/ror" - extract just "am"
                            if '/' in class_part:
                                class_part = class_part.split('/')[0].strip()
                            if class_part and len(class_part) < 20 and class_part not in ['game', 'all']:
                                return class_part
        
        # SECOND PRIORITY: Check playerData (but extract base class from it)
        if 'playerData' in parsed_data:
            for player in parsed_data['playerData']:
                if (player.get('playerName', '').lower() == player_name.lower() or
                    player.get('convertedName', '').lower() == player_name.lower()):
                    # Try to extract class from different possible fields
                    class_value = None
                    if 'class' in player:
                        class_value = player['class']
                    elif 'hero' in player:
                        class_value = player['hero']
                    elif 'race' in player:
                        class_value = player['race']
                    
                    # Extract base class from playerData result (e.g., "am3pgc" -> "am")
                    if class_value:
                        return self.extract_base_class(class_value)
        
        return "unknown"
    
    def generate_player_specific_filename(self, parsed_data, player_name, original_file_path):
        """Generate filename for specific player: playerName - class - loots - [craft] [MM/YYYY]"""
        if not parsed_data or 'loots' not in parsed_data:
            return None
        
        # Convert to Path if it's a string
        if isinstance(original_file_path, str):
            original_file_path = Path(original_file_path)
            
        # Find all loots for this specific player
        player_loots = []
        for loot in parsed_data['loots']:
            loot_player = loot['playerName']
            
            # Clean and compare player names (handle variations like #numbers and parentheses)
            clean_loot_player = re.sub(r'#\d+.*', '', loot_player)
            clean_loot_player = re.sub(r'\([^)]*\)', '', clean_loot_player).strip()
            
            if clean_loot_player.lower() == player_name.lower():
                item_name = re.sub(r'[<>:"/\\|?*]', '', loot['itemName'])
                player_loots.append(item_name)
        
        if not player_loots:
            return None
            
        # Get player class
        player_class = self.get_player_class(parsed_data, player_name)
        
        # Extract base class letters (e.g., "merch18-fc" -> "merch", "th1" -> "th")
        player_class = self.extract_base_class(player_class)
        
        # Get original filename for craft detection
        original_filename = original_file_path.name
        
        # Check if original filename contains "craft"
        craft_suffix = ""
        # Look for patterns like " - craft " or just "craft " in filename
        craft_match = re.search(r'(?:^|\s|\-\s)craft\s+([^\.]+)', original_filename.lower())
        if craft_match:
            craft_item = craft_match.group(1).strip()
            # Clean it
            craft_item = re.sub(r'[<>:"/\\|?*]', '', craft_item)
            craft_suffix = f" - craft {craft_item}"
        
        # Get file modification date for MMM-DD-YY
        mod_date = self.get_file_modified_date(original_file_path)
        date_suffix = f" - {mod_date.strftime('%b-%d-%y')}"
        
        # Create filename: playerName - class - loots [- craft XXX] - MMM-DD-YY
        loots_str = ", ".join(player_loots)
        
        # Calculate max lengths
        # Windows max filename: 255 chars
        # Reserve 50 chars for date and extensions (.w3g)
        max_content_length = 200  # Leave safety margin
        
        if len(loots_str) > max_content_length:
            loots_str = loots_str[:max_content_length] + "..."
        
        # Build the filename
        new_filename = f"{player_name} - {player_class} - {loots_str}{craft_suffix}{date_suffix}.w3g"
        
        # Final cleanup for any invalid characters
        new_filename = re.sub(r'[<>:"/\\|?*]', '', new_filename)
        
        return new_filename
    
    def rename_file(self, old_path, new_name, dry_run=True):
        """Rename the file"""
        old_path = Path(old_path)
        new_path = old_path.parent / new_name
        
        if new_path.exists():
            print(f"Warning: {new_name} already exists, skipping...")
            return False
            
        try:
            if dry_run:
                print(f"DRY RUN: Would rename '{old_path.name}' to '{new_name}'")
                return True
            else:
                old_path.rename(new_path)
                print(f"Renamed '{old_path.name}' to '{new_name}'")
                return True
        except Exception as e:
            print(f"Error renaming {old_path.name}: {e}")
            return False
    
    def test_single_file_for_player(self, filename, player_name):
        """Test the script with a single file for a specific player"""
        file_path = self.replay_folder / filename
        
        if not file_path.exists():
            print(f"File not found: {filename}")
            return False
            
        print(f"Testing with file: {filename}")
        print(f"Looking for player: {player_name}")
        print(f"File path: {file_path}")
        print(f"File size: {file_path.stat().st_size} bytes")
        print(f"Modified: {self.get_file_modified_date(file_path)}")
        
        # Parse the replay
        print("Sending to parser...")
        parsed_data = self.parse_replay(file_path)
        
        if not parsed_data:
            print("Failed to parse replay")
            return False
            
        print("Parser found players:")
        if 'playerData' in parsed_data:
            for player in parsed_data['playerData']:
                print(f"  - {player.get('playerName', 'Unknown')}")
        
        print(f"\nLooking for loots for player: {player_name}")
        
        # Generate player-specific filename
        new_name = self.generate_player_specific_filename(parsed_data, player_name, file_path)
        
        if not new_name:
            print(f"No loots found for player '{player_name}' or failed to generate filename")
            return False
            
        print(f"New filename would be: {new_name}")
        
        # Show what loots were found
        player_loots = []
        for loot in parsed_data.get('loots', []):
            loot_player = loot['playerName']
            clean_loot_player = re.sub(r'#\d+.*', '', loot_player)
            clean_loot_player = re.sub(r'\([^)]*\)', '', clean_loot_player).strip()
            
            if clean_loot_player.lower() == player_name.lower():
                player_loots.append(f"{loot['gameTime']} - {loot['itemName']}")
        
        if player_loots:
            print(f"Found {len(player_loots)} loot(s) for {player_name}:")
            for loot in player_loots:
                print(f"  - {loot}")
        
        # Get player class
        player_class = self.get_player_class(parsed_data, player_name)
        print(f"Player class detected: {player_class}")
        
        return True
    
    def create_player_file(self, original_file_path, player_name, base_output_folder, dry_run=True):
        """Create a new file for specific player based on their loots in organized folder structure"""
        # Parse the replay
        parsed_data = self.parse_replay(original_file_path)
        
        if not parsed_data:
            print(f"Failed to parse {original_file_path}")
            return False
            
        # Generate new filename
        new_name = self.generate_player_specific_filename(parsed_data, player_name, original_file_path)
        
        if not new_name:
            print(f"No loots found for player '{player_name}' in {original_file_path.name}")
            return False
            
        # Extract player class from the filename
        # Format: playerName - class - loots.w3g
        parts = new_name.split(' - ')
        if len(parts) >= 2:
            player_class = parts[1]
        else:
            player_class = "unknown"
        
        # Create organized folder structure: player_name/class/
        output_path = Path(base_output_folder) / player_name / player_class
        
        if not output_path.exists():
            if dry_run:
                print(f"DRY RUN: Would create directory '{output_path}'")
            else:
                output_path.mkdir(parents=True, exist_ok=True)
                print(f"Created directory: {output_path}")
        
        # Create new file path in the organized folder
        new_file_path = output_path / new_name
        
        if new_file_path.exists():
            print(f"File already exists: {new_file_path}")
            return False
            
        try:
            if dry_run:
                print(f"DRY RUN: Would copy '{original_file_path.name}' to '{player_name}/{player_class}/{new_name}'")
                return True
            else:
                # Copy the original file to the new location with new name
                shutil.copy2(original_file_path, new_file_path)
                print(f"Copied to '{player_name}/{player_class}/{new_name}'")
                return True
        except Exception as e:
            print(f"Error creating file: {e}")
            return False
    
    def process_files_for_player(self, player_name, dry_run=True, limit=None, folder="all"):
        """Process all replay files for a specific player and copy to organized folder structure
        
        folder: "main" - only main Replay folder
                "autosaved" - only Autosaved folder (recursive, includes subfolders)
                "all" - both main and Autosaved
        """
        # Search in specified folder(s)
        w3g_files = []
        
        if folder.lower() in ["main", "all"]:
            w3g_files.extend(list(self.replay_folder.glob("*.w3g")))
        
        if folder.lower() in ["autosaved", "all"]:
            autosaved_path = self.replay_folder / "Autosaved"
            if autosaved_path.exists():
                # Recursively search all subfolders in Autosaved
                w3g_files.extend(list(autosaved_path.rglob("*.w3g")))
        
        all_files = [f for f in w3g_files if self.is_from_last_month(f)]
        
        # Limit files if specified
        if limit:
            all_files = all_files[:limit]
        
        # Create base output folder path (in the same Replay directory)
        base_output_folder = self.replay_folder
        
        folder_label = f"({folder})" if folder.lower() != "all" else ""
        print(f"Found {len(w3g_files)} total .w3g files {folder_label}")
        print(f"Processing all {len(all_files)} files")
        print(f"Looking for player: {player_name}")
        print(f"Output structure: {player_name}/<class>/<filename>")
        
        if not all_files:
            print("No files to process")
            return
            
        processed = 0
        successful = 0
        
        for i, file_path in enumerate(all_files, 1):
            progress = f"[{i}/{len(all_files)}]"
            print(f"\n{progress} Processing: {file_path.name}", end=" ", flush=True)
            processed += 1
            
            # Create player-specific file in organized folder structure
            if self.create_player_file(file_path, player_name, base_output_folder, dry_run=dry_run):
                successful += 1
        
        print(f"\n✅ Processed {processed} files, {successful} files created for {player_name}")

def main():
    parser = argparse.ArgumentParser(description='Process W3G replay files for specific players')
    parser.add_argument('player_name', nargs='?', help='Player name to filter (e.g., crucibles, yumeshinoroi)')
    parser.add_argument('folder', nargs='?', default="all", help='Which folder to process: main, autosaved, or all (default: all)')
    parser.add_argument('--dry-run', action='store_true', default=True, help='Show what would be done without actually doing it')
    parser.add_argument('--execute', action='store_true', help='Actually create the files (overrides dry-run)')
    parser.add_argument('--test-file', default="am - aegis of storm.w3g", help='File to use for testing')
    parser.add_argument('--limit', type=int, default=None, help='Limit number of files to process (e.g., --limit 100)')
    
    args = parser.parse_args()
    
    # Configuration
    replay_folder = r"c:\Users\Admin\Desktop\Git\replay-project\Replay"
    
    renamer = ReplayRenamer(replay_folder)
    
    if not args.player_name:
        print("Usage: python rename_replays.py <player_name> [folder] [--execute] [--limit N]")
        print("  player_name: Player name to filter (e.g., crucibles, yumeshinoroi)")
        print("  folder: Which folder to process - main, autosaved, or all (default: all)")
        print("")
        print("Examples:")
        print("  python rename_replays.py crucibles")
        print("  python rename_replays.py crucibles autosaved --execute")
        print("  python rename_replays.py crucibles autosaved --limit 100")
        print("  python rename_replays.py crucibles all --execute")
        return
    
    # Test with one file first
    print(f"Testing with player '{args.player_name}' on file '{args.test_file}'...")
    
    if renamer.test_single_file_for_player(args.test_file, args.player_name):
        print(f"\nTest successful for player '{args.player_name}'!")
        
        # Ask user if they want to continue
        response = input(f"\nDo you want to process all replay files for {args.player_name}? (y/N): ")
        if response.lower() == 'y':
            dry_run = not args.execute
            
            if dry_run:
                print("Running in DRY RUN mode (use --execute to actually create files)")
            
            renamer.process_files_for_player(args.player_name, dry_run=dry_run, folder=args.folder, limit=args.limit)
            
            if dry_run and not args.execute:
                real_run = input("\nDo you want to actually create the files? (y/N): ")
                if real_run.lower() == 'y':
                    renamer.process_files_for_player(args.player_name, dry_run=False)
    else:
        print(f"Test failed for player '{args.player_name}'. Check if player exists in the replay or parser connection.")

if __name__ == "__main__":
    main()