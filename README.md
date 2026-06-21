# Replay Renamer

A Windows app that batch-renames Warcraft 3 TWRPG replay files (`.w3g`) so each filename shows the player's class and game info. The replay parser is built in — no Python, Node, or separate setup needed.

## Install

Download the latest `.exe` from the [Releases](https://github.com/zeebratootie/twrpg-replay-renamer/releases) page and double-click it. That's all.

> If Windows SmartScreen warns about an unknown publisher, click **More info → Run anyway**.

## Use

1. **Player Name** — the character/player name you want to filter and rename for (e.g. `crucibles`).
2. **Source Replay Folder** — Browse to the folder with your `.w3g` files (your Warcraft III `Replay` folder).
3. **Output Folder** — Browse to where renamed copies should go.
4. Click **Start Processing**.

Renamed files are **copied** (never moved) into per-player, per-class subfolders.

### Options worth knowing

- **Search subfolders (recursive)** — on by default; scans every subfolder of the source. Uncheck to scan only the top level.
- **Date Filtering** — process all files, or restrict to a From/To range.
- **Dry Run** — preview what would be renamed without writing files. Run this first if unsure, then uncheck and run for real.

Your settings and per-player profiles are saved automatically next to the app, so you don't re-enter them each time.

## Troubleshooting

- **No `.w3g` files found** — check the Source folder path, and make sure *Search subfolders* is on if your replays are nested.
- **Something failed mid-run** — read the **Processing Log** at the bottom of the window; it lists each file and any error.
