import socket
import threading

HOST = '127.0.0.1'
PORT = 12345

server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server.bind((HOST, PORT))
server.listen()

print("Server running...")

def handle_client(client, address):
    print(f"[NEW CONNECTION] {address}")

    while True:
        try:
            message = client.recv(1024).decode()
            if not message:
                break
            print(f"{address}: {message}")
        except:
            break

    print(f"[DISCONNECTED] {address}")
    client.close()

while True:
    client, address = server.accept()
    thread = threading.Thread(target=handle_client, args=(client, address))
    thread.start()