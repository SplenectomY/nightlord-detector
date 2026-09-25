# nightlord-detector

External overlay for **Elden Ring Nightreign** Deep of Night. It reads the Night 1 / Night 2 healthbar title from the screen and shows:

```
Possible Nightlords:
 42.1%  Gladius, Beast of Night  [Holy]
 31.8%  Heolstor, the Nightlord  [Holy]
```

Prediction tables are copied from [nightlord.app](https://nightlord.app/) — only the bosses that site uses for Deep of Night guesswork. Field bosses and anything else on a healthbar are ignored.

This process never injects into `nightreign.exe`, never reads game memory, and never sends input to the game. It screenshots a crop of the desktop the same way a snipping tool would, then draws a separate always-on-top window.

That is the lowest-risk design against Easy Anti-Cheat. It is still not a FromSoftware blessing. Do not combine this with trainers, injected overlays, or EAC toggles.

## Requirements

- Windows, borderless-windowed Nightreign (exclusive fullscreen fights the overlay)
- Python 3.11+
- [Tesseract OCR](https://github.com/UB-Mannheim/tesseract/wiki) on PATH (`tesseract --version` should work)

## Install

```powershell
git clone https://github.com/SplenectomY/nightlord-detector.git
cd nightlord-detector
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python -m nightlord_detector
```

The debug console opens by default.

```powershell
python -m nightlord_detector --no-debug
python -m nightlord_detector --hz 1.5 --monitor 1
```

## Windows

| Window | Purpose |
|---|---|
| Overlay | Click-through `Possible Nightlords` list |
| Debug console | Live OCR, match scores, manual Night 1 / Night 2 / depth, ROI sliders, log |
| Small controller | Just so the process has a root window |

## Hotkeys

| Key | Action |
|---|---|
| F6 | Assign the current OCR hit as Night 1 |
| F7 | Assign the current OCR hit as Night 2 |
| F8 | Toggle overlay |
| F9 | Toggle debug console |
| F10 | Reset the run |

If the first Night 1-class title stays on screen long enough at ≥86 match score, it is auto-assigned. A later different title becomes Night 2.

## Calibrating the nameplate crop

Nightreign puts the boss title on a gold plate above the healthbar, near the top center. Default ROI is 28% in from the left, 4% down, 44% wide, 10% tall.

If OCR is garbage:

1. Keep the debug console open during a Night boss.
2. Drag the ROI sliders until `raw:` shows something like `Bell Bearing Hunter`.
3. Confirm the ranked list highlights the right key.

English UI only for now. Aliases cover duo nameplates (`Demi-Human Queen`, `Godskin Apostle`, `Mohg, Lord of Blood`, …).

## What it will and will not detect

Detected (nightlord.app lists):

- Night 1: Battlefield Commander, Bell Bearing Hunter, Centipede Demon, Demi-Human Queen & Swordmaster, Gaping Dragon, Grafted Monarch, Night's Cavalry Duo, Royal Revenant, Smelter Demon, The Duke's Dear Freja, Tibia Mariner, Ulcerated Tree Spirit, Valiant Gargoyle, Wormface, plus Forsaken Hollows Death Knight / Demon in Pain / Divine Beast Warrior / Great Red Bear
- Night 2: Ancient Dragon, Crucible Knight & Golden Hippopotamus, Dancer, Death Rite Bird, Draconic Tree Sentinel, Fallingstar Beast, Fell Omen, Godskin Duo, Great Wyrm, Nameless King, Nox Dragonkin Soldier, Outland Commander, Tree Sentinel, plus Artorias / Dancing Lion / Lord of Blood / Demon Prince

Ignored on purpose: field bosses, castle bosses, evergaol bosses, NPCs.

Heolstor can appear with almost every pool, so he stays on the list until a pair rules him out. Depth 3–5 priors also split regular vs Everdark percentages when both are possible.

## Safety

- Separate process
- `mss` desktop capture of one rectangle, default 2 Hz
- Overlay is a normal topmost window (no `WDA_EXCLUDEFROMCAPTURE`)
- No `ReadProcessMemory`, no DLL, no input injection

Play in borderless windowed. Test OCR in a private session first and tighten the ROI before you trust auto-assign.

## Tests

```powershell
pip install pytest
pytest
```

## Credit

Combination table and depth priors come from the public logic on [nightlord.app](https://nightlord.app/). Fan project, not affiliated with FromSoftware or Bandai Namco.
