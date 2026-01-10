# Roam
This game allows you to explore a procedurally-generated 2D world and interact with your surroundings.

## Architecture

Roam uses a **client-server architecture** implemented in **[PR #242 - Implement client-server architecture with Spring Boot backend, REST API, pygame client, and Docker support](https://github.com/Preponderous-Software/roam-prototype/pull/242)**:

- **Server (Spring Boot - Java)**: Authoritative source for all game state and business logic
  - Manages player state, inventory, entities, and world generation
  - Exposes REST API endpoints under `/api/v1/*`
  - See [server/README.md](./server/README.md) for API documentation
  
- **Client (Python)**: Handles presentation and user interaction only
  - Renders UI using pygame
  - Communicates with server via REST API
  - Contains no business logic

For detailed architecture documentation, see [ARCHITECTURE.md](./docs/ARCHITECTURE.md).

## Planning Document
The planning document can be found [here](./docs/PLANNING.md)

## Controls
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

## Setup and Run

### Option 1: Docker (Recommended)

The easiest way to run Roam is using Docker:

```bash
# Start the server
docker compose up -d roam-server

# Run client (on host)
cd src
python3 roam_client.py
```

See [DOCKER.md](./docs/DOCKER.md) for complete Docker documentation.

### Option 2: Manual Setup

#### Prerequisites
- **Java 17 or higher** - [Download Java](https://adoptium.net/)
- **Maven 3.6 or higher** - [Download Maven](https://maven.apache.org/download.cgi)
- **Python 3.8 or higher** - [Download Python](https://www.python.org/downloads/)
- **Git** - [Download Git](https://git-scm.com/downloads)

### Clone Repository
```bash
git clone https://github.com/Stephenson-Software/Roam.git
cd Roam
```

### Start the Server

1. Navigate to the server directory:
```bash
cd server
```

2. Build the server:
```bash
mvn clean install
```

3. Run the server:
```bash
mvn spring-boot:run
```

The server will start on `http://localhost:8080`. Keep this terminal window open.

### Start the Client

#### Option 1: New Server-Backed Client (Recommended)

The new client application (`src/roam_client.py`) uses the Spring Boot backend for all game logic.

1. Open a new terminal and navigate to the src directory:
```bash
cd src
```

2. Install Python dependencies (if not already installed):
```bash
pip install -r ../requirements.txt
```

3. Run the client:
```bash
python3 roam_client.py
```

Or use the provided script:
```bash
./run_client.sh
```

The client will connect to the server and start a new game session.

**Features**:
- ✅ No business logic in client (all on server)
- ✅ Real-time server communication via REST API
- ✅ Player movement, inventory, and energy management
- ✅ Clean separation of UI and game logic

See [src/CLIENT_README.md](./src/CLIENT_README.md) for detailed documentation.

#### Option 2: Original Python Client (Now Server-Backed)

The original Python client (`src/roam.py`) has been refactored to use the server-backed architecture.

**Features**:
- ✅ Server-backed game logic (no local business logic)
- ✅ Rich visual experience with multiple screens
- ✅ Player movement, inventory, and energy management via REST API
- ✅ All game state mutations through server

**Requirements**:
- Spring Boot server must be running
- Python 3.8+ with dependencies installed

**Usage**:

1. Ensure the Spring Boot server is running (see above)

2. Open a new terminal and navigate to the src directory:
```bash
cd src
```

3. Install Python dependencies (if not already installed):
```bash
pip install -r ../requirements.txt
```

4. Run the client:
```bash
python3 roam.py
```

Or with custom server URL:
```bash
python3 roam.py http://localhost:8080
```

**Controls**:
- WASD/Arrows: Move player
- Space: Stop movement
- G: Toggle gathering
- I: Open inventory
- E: Consume food
- ESC: Open menu

**Note**: This client now uses the server for all game logic. Complex features like world generation and entity management will be added in Phase 4 of the migration (server-side implementation).

See [CLIENT_REFACTORING_SUMMARY.md](./CLIENT_REFACTORING_SUMMARY.md) and [REFACTORING_NOTES.md](./REFACTORING_NOTES.md) for detailed information about the refactoring.

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
