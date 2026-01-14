# Multiplayer Session Management UI - Visual Documentation

## Overview
This document provides a visual description of the new multiplayer UI screens added to the Roam game client.

## 1. Main Menu Screen (Updated)

```
╔════════════════════════════════════════════════╗
║                                                ║
║                    Roam                        ║
║         press any key to start!                ║
║                                                ║
║         ┌────────────────────┐                 ║
║         │       play         │                 ║
║         └────────────────────┘                 ║
║         ┌────────────────────┐                 ║
║         │   join session     │  ← NEW!        ║
║         └────────────────────┘                 ║
║         ┌────────────────────┐                 ║
║         │      config        │                 ║
║         └────────────────────┘                 ║
║         ┌────────────────────┐                 ║
║         │       quit         │                 ║
║         └────────────────────┘                 ║
║                                                ║
║                v0.x.x                          ║
╚════════════════════════════════════════════════╝
```

**Changes:**
- Added "join session" button between "play" and "config"
- Clicking "join session" takes you to the Join Session Screen

---

## 2. Session Info Screen (NEW)

Displayed after creating a new session (when clicking "play" from main menu).

```
╔════════════════════════════════════════════════╗
║                                                ║
║            Session Created!                    ║
║                                                ║
║     Share this Session ID with friends:        ║
║                                                ║
║   ┌──────────────────────────────────────┐    ║
║   │ 550e8400-e29b-41d4-a716-446655440000 │    ║
║   └──────────────────────────────────────┘    ║
║                                                ║
║   ┌────────────────┐  ┌────────────────┐     ║
║   │ Copy to        │  │ Continue to    │     ║
║   │ Clipboard      │  │ Game           │     ║
║   └────────────────┘  └────────────────┘     ║
║                                                ║
║        ✓ Copied to clipboard!                 ║
║                                                ║
║   Press ENTER to continue or ESC to go back   ║
║                                                ║
╚════════════════════════════════════════════════╝
```

**Features:**
- Displays the newly created session ID prominently
- "Copy to Clipboard" button copies the session ID
- Visual confirmation when copied ("✓ Copied to clipboard!")
- "Continue to Game" button starts the game
- Can also press ENTER to continue

---

## 3. Join Session Screen (NEW)

Accessed by clicking "join session" from the main menu.

```
╔════════════════════════════════════════════════╗
║                                                ║
║              Join Session                      ║
║                                                ║
║           Enter Session ID:                    ║
║                                                ║
║   ┌──────────────────────────────────────┐    ║
║   │ 550e8400-e29b-41d4-a716-446655440000 │    ║
║   └──────────────────────────────────────┘    ║
║                                                ║
║                                                ║
║   ┌──────────┐         ┌──────────┐          ║
║   │   Join   │         │  Cancel  │          ║
║   └──────────┘         └──────────┘          ║
║                                                ║
║          ENTER: Join | ESC: Cancel            ║
║                                                ║
╚════════════════════════════════════════════════╝
```

**Error States:**

```
╔════════════════════════════════════════════════╗
║              Join Session                      ║
║                                                ║
║           Enter Session ID:                    ║
║   ┌──────────────────────────────────────┐    ║
║   │ invalid-session-id                    │    ║
║   └──────────────────────────────────────┘    ║
║                                                ║
║           Session not found                    ║
║                                                ║
╚════════════════════════════════════════════════╝
```

```
╔════════════════════════════════════════════════╗
║              Join Session                      ║
║                                                ║
║           Enter Session ID:                    ║
║   ┌──────────────────────────────────────┐    ║
║   │ full-session-id                       │    ║
║   └──────────────────────────────────────┘    ║
║                                                ║
║      Session is full (max 10 players)         ║
║                                                ║
╚════════════════════════════════════════════════╝
```

**Features:**
- Text input field for session ID
- Real-time error messages (session not found, session full, invalid format)
- Loading indicator while joining
- ENTER key submits, ESC cancels

---

## 4. World Screen (Updated)

The game world now displays session information in the top-right corner.

```
╔════════════════════════════════════════════════╗
║                                ┌─────────────┐ ║
║  [Energy Bar]                  │ Players: 3/10│ ║
║                                │ ★ Alice      │ ║
║                                │   Bob        │ ║
║                                │   Charlie    │ ║
║                                └─────────────┘ ║
║                                                ║
║            [Game World View]                   ║
║               [Player]                         ║
║             [Entities]                         ║
║                                                ║
║                                                ║
║  [Inventory Preview Bar]                       ║
║  [1][2][3][4][5][6][7][8][9][0]               ║
╚════════════════════════════════════════════════╝
```

**Features:**
- Semi-transparent overlay in top-right corner
- Shows current player count (e.g., "3/10")
- Lists player usernames
- Session owner marked with ★ symbol
- Shows max 8 players (displays "and X more..." if more than 8)

---

## 5. Options Screen (Updated)

The options screen now includes a "leave session" button for non-owner players.

```
╔════════════════════════════════════════════════╗
║                                                ║
║         ┌────────────────────┐                 ║
║         │    main menu       │                 ║
║         └────────────────────┘                 ║
║         ┌────────────────────┐                 ║
║         │      stats         │                 ║
║         └────────────────────┘                 ║
║         ┌────────────────────┐                 ║
║         │    inventory       │                 ║
║         └────────────────────┘                 ║
║         ┌────────────────────┐                 ║
║         │  leave session     │  ← NEW!        ║
║         └────────────────────┘                 ║
║                                                ║
║                                                ║
║         ┌────────────────────┐                 ║
║         │       back         │                 ║
║         └────────────────────┘                 ║
║                                                ║
╚════════════════════════════════════════════════╝
```

**Features:**
- "leave session" button appears only when in a multiplayer session
- Button is disabled for session owner (shows error if clicked)
- Returns to main menu after leaving session

**Error State (Session Owner):**

```
╔════════════════════════════════════════════════╗
║         ┌────────────────────┐                 ║
║         │  leave session     │                 ║
║         └────────────────────┘                 ║
║                                                ║
║        Session owner cannot leave              ║
║                                                ║
╚════════════════════════════════════════════════╝
```

---

## User Flows

### Flow 1: Creating and Hosting a Session

1. Start at Main Menu
2. Click "play" button
3. Session Info Screen appears with session ID
4. Copy session ID to share with friends
5. Click "Continue to Game"
6. World Screen displays with session info overlay

### Flow 2: Joining an Existing Session

1. Start at Main Menu
2. Click "join session" button
3. Join Session Screen appears
4. Enter session ID received from friend
5. Click "Join" or press ENTER
6. On success, World Screen loads
7. On error, error message displays

### Flow 3: Leaving a Session

1. In game world, press ESC
2. Options Screen appears
3. Click "leave session" button
4. Returns to Main Menu

---

## API Integration

All screens use the `RoamAPIClient` class with these new methods:

- `join_session(session_id: str)` - Join an existing session
- `leave_session(session_id: Optional[str])` - Leave current session
- `get_players(session_id: Optional[str])` - Get list of players in session

These methods communicate with the server REST API:
- `POST /api/v1/session/{sessionId}/join`
- `POST /api/v1/session/{sessionId}/leave`
- `GET /api/v1/session/{sessionId}/players`

---

## Implementation Details

### Files Modified:
- `src/client/api_client.py` - Added multiplayer methods
- `src/screen/screenType.py` - Added screen type constants
- `src/screen/mainMenuScreen.py` - Added join session button
- `src/screen/optionsScreen.py` - Added leave session functionality
- `src/screen/serverBackedWorldScreen.py` - Added session info overlay
- `src/roam.py` - Integrated new screens into main loop

### Files Created:
- `src/screen/sessionInfoScreen.py` - Session ID display screen
- `src/screen/joinSessionScreen.py` - Join session input screen

### Key Design Decisions:
1. Session ID displayed immediately after creation for easy sharing
2. Clipboard copy functionality using pygame.scrap module
3. Real-time player count and list in game overlay
4. Session owner cannot leave (must close session through main menu)
5. Clear error messages for common scenarios (full, not found, invalid)
