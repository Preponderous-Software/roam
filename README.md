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
Left Mouse | Gather / Pick up
Right Mouse | Place item
1-0 | Select hotbar slot
Scroll Wheel | Cycle through hotbar
I | Open / Close inventory
M | Toggle minimap
+/- | Resize minimap
C | Toggle camera follow mode
F1 | Toggle controls help overlay
F3 | Toggle debug info
Print Screen | Take screenshot
Esc | Quit (main menu) / Open menu (world) / Go back (other screens)
Left Mouse (outside inventory panel) | Drop entire cursor stack (inventory screen)
Middle Mouse (outside inventory panel) | Drop single item from cursor (inventory screen)
Right Mouse (inventory slot) | Select inventory slot (inventory screen)

> **Tip:** Keybindings are configurable in-game. Open the options menu and select **Controls** to view or remap bindings. Remapped keys are respected across all screens (world, inventory, stats, etc.).

## Clone and Run
### Clone
1. If you don't have git installed, install it from [here](https://git-scm.com/downloads).
2. Clone the repository with the following command:
> git clone https://github.com/Stephenson-Software/Roam.git

### Install Dependencies
3. If you don't have python installed, install it from [here](https://www.python.org/downloads/).
4. Install pygame with the following command:
> pip install pygame --pre
5. Install rest of dependencies with the following command:
> pip install -r requirements.txt

### Run
6. Run the game with the following command:
> python src/roam.py

## Run Script (Linux Only)
There is also a run.sh script you can execute if you're on linux which will automatically attempt to install the dependencies for you.

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
