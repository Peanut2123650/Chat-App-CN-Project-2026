import socket
import threading
import sys
from datetime import datetime

HOST = '127.0.0.1'
PORT = 12345

client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
client.connect((HOST, PORT))

username = input("Enter your username: ")

current_input = ""
input_lock = threading.Lock()
stop_event = threading.Event()

# ── platform setup ──────────────────────────────────────────
if sys.platform == "win32":
    import msvcrt

    def read_char():
        return msvcrt.getwch()

else:
    import tty, termios

    def read_char():
        fd = sys.stdin.fileno()
        old = termios.tcgetattr(fd)
        try:
            tty.setraw(fd)
            return sys.stdin.read(1)
        finally:
            termios.tcsetattr(fd, termios.TCSADRAIN, old)
# ────────────────────────────────────────────────────────────


def reprint_input():
    sys.stdout.write(f"You: {current_input}")
    sys.stdout.flush()


def receive():
    while not stop_event.is_set():
        try:
            message = client.recv(1024).decode()
            if message == "USERNAME":
                client.send(username.encode())
            elif message == "Disconnecting...":
                with input_lock:
                    sys.stdout.write("\r" + " " * (len("You: ") + len(current_input)) + "\r")
                    print(message)
                stop_event.set()
            elif message.startswith("Username already taken"):
                print(f"\n{message}")
                stop_event.set()
            else:
                with input_lock:
                    sys.stdout.write("\r" + " " * (len("You: ") + len(current_input)) + "\r")
                    print(message)
                    reprint_input()
        except:
            if not stop_event.is_set():
                print("\nDisconnected from server.")
            stop_event.set()


def write():
    global current_input
    sys.stdout.write("You: ")
    sys.stdout.flush()

    while not stop_event.is_set():
        char = read_char()

        with input_lock:
            if char in ("\r", "\n"):
                message = current_input
                current_input = ""
                print()
                if message.strip():
                    try:
                        client.send(message.encode())
                        if not message.strip().startswith("/"):
                            time = datetime.now().strftime("%H:%M")
                            print(f"[{time}] You: {message}")
                    except:
                        stop_event.set()
                        break
                if not stop_event.is_set():
                    reprint_input()
            elif char in ("\x08", "\x7f"):  # backspace
                if current_input:
                    current_input = current_input[:-1]
                    sys.stdout.write("\b \b")
                    sys.stdout.flush()
            elif char == "\x03":  # Ctrl+C
                stop_event.set()
                break
            else:
                current_input += char
                sys.stdout.write(char)
                sys.stdout.flush()

    client.close()
    sys.exit(0)


threading.Thread(target=receive, daemon=True).start()
write()