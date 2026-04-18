import socket
import threading

HOST = '127.0.0.1'
PORT = 12345

server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server.bind((HOST, PORT))
server.listen()

print("Server running...")

clients = {}   # username : client_socket


def broadcast(message, sender_client=None):
    for client in clients.values():
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

            # 🔥 PRIVATE MESSAGE
            if message.startswith("/msg"):
                parts = message.split(" ", 2)

                if len(parts) < 3:
                    client.send("Invalid format. Use: /msg username message".encode())
                    continue

                target_user = parts[1]
                private_msg = parts[2]

                if target_user in clients:
                    # send to receiver
                    clients[target_user].send(
                        f"[Private] {username}: {private_msg}".encode()
                    )

                    # send confirmation to sender
                    client.send(
                        f"[Private to {target_user}]: {private_msg}".encode()
                    )
                else:
                    client.send("User not found".encode())

            # 🔹 NORMAL MESSAGE
            else:
                formatted = f"{username}: {message}"
                print(formatted)
                broadcast(formatted, client)

        except:
            break

    print(f"[DISCONNECTED] {username}")

    del clients[username]
    client.close()

    broadcast(f"{username} left the chat")


while True:
    client, address = server.accept()

    client.send("USERNAME".encode())
    username = client.recv(1024).decode()

    clients[username] = client

    join_msg = f"{username} joined the chat"
    print(join_msg)
    broadcast(join_msg)

    thread = threading.Thread(target=handle_client, args=(client, username))
    thread.start()