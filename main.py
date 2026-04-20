"""
main.py — Launcher for the TCP Chat Application.

What it does:
  1. Starts chat_app_server.py in a background terminal.
  2. Asks how many clients to open (or just press Enter for 1).
  3. Opens each client in its own terminal window (GUI or terminal client).

Usage:
  python main.py              # launches server + prompts for clients
  python main.py --clients 3  # launches server + 3 client windows
  python main.py --terminal   # use terminal client instead of GUI
"""

import subprocess
import sys
import os
import time
import argparse

HERE = os.path.dirname(os.path.abspath(__file__))
SERVER_SCRIPT = os.path.join(HERE, "chat_app_server.py")
CLIENT_SCRIPT = os.path.join(HERE, "chat_app_client.py")
GUI_SCRIPT    = os.path.join(HERE, "chat_gui.py")

PYTHON = sys.executable


def start_server():
    """Launch the server in a new visible terminal window."""
    print("  Starting server...")

    if sys.platform == "win32":
        proc = subprocess.Popen(
            ["start", "cmd", "/k", PYTHON, SERVER_SCRIPT],
            shell=True
        )
    elif sys.platform == "darwin":
        script = (
            f'tell application "Terminal" to do script '
            f'"python3 \\"{SERVER_SCRIPT}\\""'
        )
        proc = subprocess.Popen(["osascript", "-e", script])
    else:
        # Linux — try common terminal emulators in order
        terminals = [
            ["gnome-terminal", "--", PYTHON, SERVER_SCRIPT],
            ["xterm", "-e", PYTHON, SERVER_SCRIPT],
            ["konsole", "-e", PYTHON, SERVER_SCRIPT],
            ["xfce4-terminal", "-e", f"{PYTHON} {SERVER_SCRIPT}"],
        ]
        proc = None
        for cmd in terminals:
            try:
                proc = subprocess.Popen(cmd)
                break
            except FileNotFoundError:
                continue
        if proc is None:
            print("  Could not find a terminal emulator. Starting server in background.")
            proc = subprocess.Popen([PYTHON, SERVER_SCRIPT])

    # Give the server a moment to bind the port
    time.sleep(1.5)
    print("  Server started.\n")
    return proc


def open_client(use_gui=True, index=1):
    """Open a single client in a new terminal window."""
    script = GUI_SCRIPT if use_gui else CLIENT_SCRIPT
    label  = "GUI" if use_gui else "Terminal"
    print(f"  Opening client {index} ({label})...")

    if sys.platform == "win32":
        subprocess.Popen(
            ["start", "cmd", "/k", PYTHON, script],
            shell=True
        )
    elif sys.platform == "darwin":
        cmd_str = f'python3 \\"{script}\\"'
        osascript = (
            f'tell application "Terminal" to do script "{cmd_str}"'
        )
        subprocess.Popen(["osascript", "-e", osascript])
    else:
        terminals = [
            ["gnome-terminal", "--", PYTHON, script],
            ["xterm", "-e", PYTHON, script],
            ["konsole", "-e", PYTHON, script],
            ["xfce4-terminal", "-e", f"{PYTHON} {script}"],
        ]
        launched = False
        for cmd in terminals:
            try:
                subprocess.Popen(cmd)
                launched = True
                break
            except FileNotFoundError:
                continue
        if not launched:
            # Fallback: run directly (blocks, but better than nothing)
            print(f"  No terminal found — running client {index} directly.")
            subprocess.Popen([PYTHON, script])

    time.sleep(0.3)  # slight stagger so windows don't pile up exactly


def check_scripts():
    missing = []
    for name, path in [("Server", SERVER_SCRIPT), ("GUI client", GUI_SCRIPT),
                        ("Terminal client", CLIENT_SCRIPT)]:
        if not os.path.exists(path):
            missing.append(f"  {name}: {path}")
    if missing:
        print("Warning — the following scripts were not found:")
        for m in missing:
            print(m)
        print()


def main():
    parser = argparse.ArgumentParser(description="TCP Chat Launcher")
    parser.add_argument("--clients", type=int, default=None,
                        help="Number of client windows to open (default: ask)")
    parser.add_argument("--terminal", action="store_true",
                        help="Use terminal client instead of GUI")
    parser.add_argument("--no-server", action="store_true",
                        help="Skip starting the server (if already running)")
    args = parser.parse_args()

    print("=" * 48)
    print("       TCP Chat Application Launcher")
    print("=" * 48)
    print()

    check_scripts()

    use_gui = not args.terminal
    client_type = "terminal" if args.terminal else "GUI"

    # ── Start server ────────────────────────────────────────
    if not args.no_server:
        start_server()
    else:
        print("  Skipping server start (--no-server).\n")

    # ── Ask how many clients ─────────────────────────────────
    if args.clients is not None:
        num_clients = args.clients
    else:
        print(f"Client type: {client_type}")
        try:
            raw = input("How many client windows to open? [1]: ").strip()
            num_clients = int(raw) if raw else 1
        except (ValueError, EOFError):
            num_clients = 1

    if num_clients < 1:
        num_clients = 1

    print()
    for i in range(1, num_clients + 1):
        open_client(use_gui=use_gui, index=i)

    print()
    print(f"  {num_clients} client window(s) opened.")
    print()
    print("  Tips:")
    print("  • Run 'python main.py --clients 2' to open 2 clients at once.")
    print("  • Run 'python main.py --terminal' to use the terminal client.")
    print("  • Run 'python main.py --no-server' if the server is already running.")
    print()


if __name__ == "__main__":
    main()
