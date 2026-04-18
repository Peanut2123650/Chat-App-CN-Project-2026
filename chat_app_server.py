import socket
import threading
from datetime import datetime

HOST = '127.0.0.1'
PORT = 12345

server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
server.bind((HOST, PORT))
server.listen()

print("Server running...")

clients = {}
clients_lock = threading.Lock()


def broadcast(message, sender_client=None):
    with clients_lock:
        targets = list(clients.values())
    for client in targets:
        if client != sender_client:
            try:
                client.send(message.encode())
            except:
                pass


def handle_client(client, username):
    print(f"[NEW CONNECTION] {username}")

    while True:
        try:
            message = client.recv(1024).decode()

            if not message:
                break

            # /list
            if message.strip() == "/list":
                with clients_lock:
                    user_list = ", ".join(clients.keys())
                client.send(f"Active users: {user_list}".encode())
                continue

            # /exit
            if message.strip() == "/exit":
                client.send("Disconnecting...".encode())
                break

            # /msg
            if message.startswith("/msg"):
                parts = message.split(" ", 2)
                if len(parts) < 3:
                    client.send("Invalid format. Use: /msg username message".encode())
                    continue
                target_user = parts[1]
                private_msg = parts[2]
                time = datetime.now().strftime("%H:%M")
                with clients_lock:
                    target = clients.get(target_user)
                if target:
                    target.send(f"[{time}] [Private] {username}: {private_msg}".encode())
                    client.send(f"[{time}] [Private to {target_user}]: {private_msg}".encode())
                else:
                    client.send(f"User '{target_user}' not found. Use /list to see active users.".encode())
                continue

            # normal message
            time = datetime.now().strftime("%H:%M")
            formatted = f"[{time}] {username}: {message}"
            print(formatted)
            broadcast(formatted, client)

        except:
            break

    print(f"[DISCONNECTED] {username}")
    with clients_lock:
        del clients[username]
    client.close()
    broadcast(f"{username} left the chat")


def setup_client(client, address):
    try:
        client.send("USERNAME".encode())
        username = client.recv(1024).decode().strip()

        if not username:
            client.close()
            return

        with clients_lock:
            if username in clients:
                client.send("Username already taken. Please reconnect with a different username.".encode())
                client.close()
                return
            clients[username] = client

        join_msg = f"{username} joined the chat"
        print(join_msg)
        broadcast(join_msg)
        handle_client(client, username)
    except:
        client.close()


while True:
    client, address = server.accept()
    thread = threading.Thread(target=setup_client, args=(client, address))
    thread.daemon = True
    thread.start()