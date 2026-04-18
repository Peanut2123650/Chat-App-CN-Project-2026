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

            print(f"{username}: {message}")
            broadcast(f"{username}: {message}", client)

        except:
            break

    print(f"[DISCONNECTED] {username}")

    del clients[username]
    client.close()

    broadcast(f"{username} left the chat")


while True:
    client, address = server.accept()

    # Ask for username
    client.send("USERNAME".encode())
    username = client.recv(1024).decode()

    clients[username] = client

    print(f"{username} joined the chat")

    broadcast(f"{username} joined the chat")

    thread = threading.Thread(target=handle_client, args=(client, username))
    thread.start()