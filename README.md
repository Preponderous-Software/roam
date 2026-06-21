# Roam
Roam is a **single-player** game that allows you to explore a procedurally-generated 2D world and interact with your surroundings. There are currently no plans to add multiplayer.

## Planning Document
The planning document can be found [here](./PLANNING.md)

## Controls
Key | Action
------------ | -------------
W / A / S / D (or Arrow Keys) | Move up / left / down / right
Shift | Run
Ctrl | Crouch
G | Gather / Harvest mature crop
F | Place item / Interact
X | Look (examine the tile you are facing)
Left Mouse | Gather / Pick up / Harvest mature crop
Right Mouse | Place item / Plant seed on grass
1-0 | Select hotbar slot
`[` / `]` | Cycle hotbar left / right
Scroll Wheel | Cycle through hotbar
I | Open / Close inventory
M | Toggle minimap
= / - | Minimap zoom in / out
C | Toggle camera follow mode
F1 (or H) | Toggle controls help overlay
F3 (or `\`) | Toggle debug info
L | Open Codex
Print Screen | Take screenshot
Esc | Quit (main menu) / Open menu (world) / Go back (other screens)
Left Mouse (outside inventory panel) | Drop entire cursor stack (inventory screen)
Middle Mouse (outside inventory panel) | Drop single item from cursor (inventory screen)
Right Mouse (inventory slot) | Select inventory slot (inventory screen)

> **Tip:** Keybindings are configurable in-game. Open the options menu and select **Controls** to view or remap bindings. Remapped keys are respected across all screens (world, inventory, stats, etc.).
>
> **Tip:** On keyboards without F-keys (e.g. Android / Userland), use **H** for the help overlay and **`\`** for debug info.

## Download & Install (recommended)
The easiest way to play Roam — no Python and no command line. Grab the latest build from the [Releases page](https://github.com/Preponderous-Software/roam/releases):

- **Windows:** `Roam-<version>-Setup.exe` — a standard installer that adds Start Menu/Desktop shortcuts and an uninstaller. Prefer no install? Use `Roam-<version>-windows-portable.zip`.
- **macOS:** `Roam-<version>.dmg` — open it and drag `Roam.app` to Applications.

These builds aren't code-signed yet, so on first run Windows SmartScreen shows an "unknown publisher" prompt (choose **More info → Run anyway**) and macOS Gatekeeper may block the app (right-click it → **Open**). See issues #393 / #396.

## Run from Source (for developers)
Want the latest code, or to contribute? Run Roam from a clone. (To just play, use the [download above](#download--install-recommended).)
### Clone
1. If you don't have git installed, install it from [here](https://git-scm.com/downloads).
2. Clone the repository with the following command:
> git clone https://github.com/Preponderous-Software/roam.git

### Install Dependencies
3. If you don't have python installed, install it from [here](https://www.python.org/downloads/).
4. Install pygame with the following command:
> pip install pygame --pre
5. Install rest of dependencies with the following command:
> pip install -r requirements.txt

### Run
6. Run the game with the following command:
> python src/roam.py

To run in **text / TUI mode** (no pygame window — plays entirely in your terminal, no display server required):
> python src/roam.py --text

## Run Script (Linux Only)
There is also a run.sh script you can execute if you're on linux which will automatically attempt to install the dependencies for you.

## Windows setup script (run from source)
If you're [running from source](#run-from-source-for-developers) on Windows, `install.ps1` is a setup *script* — the from-source counterpart to `run.sh`. It checks that Python and pip are available, installs the dependencies, and creates Desktop and Start Menu shortcuts so you can launch the game without using the command line. (For a normal install, use the `RoamSetup.exe` **installer** from [Download & Install](#download--install-recommended) instead — it needs no Python.)

1. [Clone or download](#clone) the repository.
2. Right-click `install.ps1` and choose **Run with PowerShell**.
   - If Windows blocks the script, open PowerShell in the project folder and run:
     > powershell -ExecutionPolicy Bypass -File .\install.ps1
3. Follow the prompts. When it finishes, launch Roam from the **Roam** Desktop/Start Menu shortcut, or by double-clicking `run.bat`.

If Python is not installed, the wizard opens the [Python download page](https://www.python.org/downloads/) for you — install it (make sure **Add python.exe to PATH** is checked) and run the wizard again.

### Building a standalone executable (advanced)
A self-contained Windows build that bundles Python and all dependencies can be produced with [PyInstaller](https://pyinstaller.org/):

> pip install -r requirements.txt pyinstaller
> pyinstaller roam.spec --noconfirm

This writes `dist\Roam\Roam.exe` along with its bundled `assets`, `schemas`, and `config.yml`. You can verify the bundle without launching the game using `dist\Roam\Roam.exe --selftest`.

To produce a setup wizard (a `RoamSetup.exe` that installs the game with Start Menu/Desktop shortcuts and an uninstaller), build the executable above, then compile the [Inno Setup](https://jrsoftware.org/isinfo.php) script with Inno Setup 6:

> "C:\Program Files (x86)\Inno Setup 6\ISCC.exe" roam.iss

This writes `installer-output\RoamSetup.exe`. Run it (or `RoamSetup.exe /VERYSILENT` for an unattended install) to install Roam into `Program Files`; user data is kept under `%APPDATA%\Roam`.

#### macOS
On macOS the same spec produces an app bundle (`dist/Roam.app`). Build it, then wrap it in a disk image:

> pip install -r requirements.txt pyinstaller
> pyinstaller roam.spec --noconfirm
> hdiutil create -volname Roam -srcfolder dist/Roam.app -ov -format UDZO dist/Roam.dmg

Open `Roam.dmg` and drag `Roam.app` to Applications. User data (saves, settings, screenshots) is kept under `~/Library/Application Support/Roam`.

### Where your data is stored
On Windows, Roam keeps your user data under `%APPDATA%\Roam` (e.g. `C:\Users\<you>\AppData\Roaming\Roam`) so it stays with your account and works even when the game is installed to a read-only location like `Program Files`. This includes:
- **Saves** — `%APPDATA%\Roam\saves`
- **Settings** — `%APPDATA%\Roam\config.yml` (seeded from the shipped defaults on first run)
- **Screenshots** — `%APPDATA%\Roam\screenshots`

On Linux and macOS these stay next to the game (`saves/`, `config.yml`, `screenshots/`). You can override the save location by setting `pathToSaveDirectory` in `config.yml`.

## Support
You can find the support discord server [here](https://discord.gg/49J4RHQxhy).

## Authors and acknowledgement
### Developers
Name | Main Contributions
------------ | -------------
Daniel McCoy Stephenson | Creator

## Libraries
This project makes use of [graphik](https://github.com/Preponderous-Software/graphik) and [py_env_lib](https://github.com/Preponderous-Software/py_env_lib).

## 📄 License

This project is licensed under the **Preponderous Non-Commercial License (Preponderous-NC)**.  
It is free to use, modify, and self-host for **non-commercial** purposes, but **commercial use requires a separate license**.

> **Disclaimer:** *Preponderous Software is not a legal entity.*  
> All rights to works published under this license are reserved by the copyright holder, **Daniel McCoy Stephenson**.

Full license text:  
[https://github.com/Preponderous-Software/preponderous-nc-license/blob/main/LICENSE.md](https://github.com/Preponderous-Software/preponderous-nc-license/blob/main/LICENSE.md)
