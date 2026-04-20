# Chat-App-CN-Project-2026
A multi-client chat application built using socket programming in Python. It uses TCP and a client–server architecture to enable real-time communication between users, supporting features like broadcast messaging and private messaging.


## Files

| File | Purpose |
|------|---------|
| `chat_app_server.py` | Server — run this first, always |
| `chat_app_client.py` | Terminal client |
| `chat_gui.py` | GUI client |
| `main.py` | Launcher — automates everything |

---

## Quick Start

**Easiest way — use the launcher:**
```bash
python main.py
```
This starts the server and asks how many client windows to open.

---

## Launcher Options

```bash
python main.py                           # server + 1 GUI client
python main.py --clients 2               # server + 2 GUI clients
python main.py --clients 3 --terminal    # server + 3 terminal clients
python main.py --no-server --clients 1   # add a client to an already-running server
```

---

## Manual Setup (without launcher)

Open each in its own terminal window:

```bash
# Terminal 1 — always start the server first
python chat_app_server.py

# Terminal 2 — open a GUI client
python chat_gui.py

# Terminal 3 — open another client (GUI or terminal)
python chat_gui.py
python chat_app_client.py   # terminal version
```

You can mix GUI and terminal clients freely — they all connect to the same server.

---

## Commands (in any client)

| Command | What it does |
|---------|-------------|
| `/list` | Show all currently connected users |
| `/msg <username> <message>` | Send a private message to a specific user |
| `/help` | Show all available commands |
| `/exit` | Disconnect cleanly |

---

## Username Rules

- Cannot be empty
- Max 20 characters
- No spaces
- Must be unique (no two users with the same name)

If your username is rejected you will be prompted to try again — no need to restart.

---

## Requirements

- Python 3.x (no external libraries needed)
- `tkinter` for the GUI client — comes bundled with Python on Windows and macOS
  - Linux: `sudo apt install python3-tk`

---

## Planned Features

- TLS encryption (`ssl` module)
- Message history for newly joined users
- File transfer