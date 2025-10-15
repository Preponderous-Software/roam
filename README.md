# Roam
This game allows you to explore a procedurally-generated 2D world and interact with your surroundings.

## Planning Document
The planning document can be found [here](./PLANNING.md)

## Controls

### Pygame UI (Default)
Key | Action
------------ | -------------
w | move up
a | move left
s | move down
d | move right
shift | run
ctrl | crouch
left mouse | gather
right mouse | place
1-0 | select item in hotbar
i | open/close inventory
print screen | take screenshot
esc | quit

### Text UI
Key | Action
------------ | -------------
w | move up
a | move left
s | move down
d | move right
g | gather
p | place
1-0 | select item in hotbar
i | inventory (not yet implemented)
o | options (not yet implemented)
q | quit

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

#### Text-Based UI Mode
You can also run the game with a text-based UI instead of the standard pygame UI:
> python src/roam.py --text

Or use the short form:
> python src/roam.py -t

To see all available options:
> python src/roam.py --help

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
