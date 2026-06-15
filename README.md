# Replay Batch Processor GUI Application

A Windows desktop application for batch-processing Warcraft 3 replay files (`.w3g`) with a friendly graphical interface. It parses each replay, extracts the player's class and loot, and copies the file into an organized `player / class` folder structure with a descriptive name.

## ✨ Features

- **Single self-contained .exe** — the replay parser is **bundled inside** the app and starts automatically. No Node.js, no Python, no separate parser file.
- **Recursive search** — optionally scan every subfolder of your source folder (toggle, on by default).
- **Full class names** — output uses real class names (Merchant, Paladin, Arcane Mage, …) instead of raw load-codes (`merch`, `cpal`, `am`, …).
- **Player filtering** — process replays for a specific player.
- **Flexible paths** — configure source and output folders.
- **Concurrent processing** — multithreaded with HTTP connection pooling for fast bulk runs.
- **Date filtering** — process all files or restrict to a date range.
- **Settings persistence** — multiple named configs saved between sessions.
- **Live progress log** — real-time updates, progress bar, and ETA.

## 🚀 Quick Start

### Option 1: Download the release ⭐ (easiest)

1. Download `ReplayBatchProcessor-vX.Y.Z.exe` from the [Releases](https://github.com/zeebratootie/twrpg-replay-renamer/releases) page.
2. Double-click it.
3. That's it — the parser is embedded and launches itself on the first run.

**Requirements: none.** No Python, no Node.js, no separate parser. Just Windows x64.

> First launch is slightly slower because the app extracts the bundled parser to a temp folder, then it runs normally.

### Option 2: Run from source (developers)

```bash
pip install -r requirements.txt
python replay_batch_gui.py
```

Running from source, the app prefers a sibling `replay-parser` Node project (so you always get the latest parser code). Make sure Node.js is installed for that path, or drop a standalone `replay-parser-win-x64.exe` next to the app.

### Option 3: Build your own single-file .exe

```bash
pip install -r requirements.txt
# Place replay-parser-win-x64.exe next to the spec so it gets bundled in
python build.py
# Output: dist/ReplayBatchProcessor.exe  (parser embedded)
```

## 📖 Usage

1. **Enter Player Name** — the character/account to filter by (e.g. `crucibles`).
2. **Select Source Replay Folder** — the folder with your `.w3g` files.
3. **Search subfolders (recursive)** — leave checked to include every subfolder, or uncheck to scan only the top level.
4. **Select Output Folder** — where organized copies are written.
5. **Date Filtering (optional)** — process all files, or set a From/To range.
6. **Click Start Processing** and watch the Processing Log.

Output files are **copied** (never moved) to:

```
output_folder/<playerName>/<class>/<playerName> - <class> - <items> - <MMM-DD-YY>.w3g
```

### Class names

Class is resolved from the in-game hero, then chat load commands (`-l`, `-load`, `-save`), then player data. Short load-codes are mapped to full display names, e.g.:

| Code | Class | Code | Class |
|------|-------|------|-------|
| merch | Merchant | th | Thunderer |
| am | Arcane Mage | kn / knight | Knight |
| wim | Wind Mage | ele | Elementalist |
| pala / cpal | Paladin | ss | Sword Saint |

Codes that aren't recognized pass through unchanged.

## ⚙️ Configuration

Settings are saved to INI files in the app folder (multiple named configs are supported via the dropdown). Defaults: `parser_url=http://localhost:3000`, `batch_size=500`, `parallel_threads=8`. The `recursive` toggle and date filters are persisted too.

The parser endpoint is `POST /parse-w3g`. With the release .exe the parser is embedded and managed automatically; you only need to point `parser_url` somewhere if you run your own parser elsewhere.

## 🛠️ Troubleshooting

- **Icon still shows an old image** — that's Windows' icon cache keyed by filename. Each release uses a versioned filename to avoid it; you can also run `ie4uinit.exe -ClearIconCache`.
- **"No .w3g files found"** — check the source path; enable *Search subfolders* if your replays are nested.
- **App won't start (from source)** — run `python replay_batch_gui.py` from a terminal to see errors; ensure Python 3.8+.

## 📁 Source files

- `replay_batch_gui.py` — main GUI app (with an inlined copy of the renamer so the .exe needs no external files).
- `rename_replays.py` — standalone CLI renamer / renaming logic.
- `config.py`, `date_filter.py`, `logging_setup.py` — support modules.
- `build.py`, `ReplayBatchProcessor.spec` — PyInstaller build (bundles the parser).
- `requirements.txt` — Python dependencies.

## 📜 License

[MIT](LICENSE) © zeebratootie
