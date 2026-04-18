import socket
import threading

HOST = '127.0.0.1'
PORT = 12345

client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
client.connect((HOST, PORT))

username = input("Enter your username: ")


def receive():
    while True:
        try:
            message = client.recv(1024).decode()

            if message == "USERNAME":
                client.send(username.encode())
            else:
                print(message)

        except:
            print("Disconnected from server")
            client.close()
            break


def write():
    while True:
        try:
            message = input("You: ")
            client.send(message.encode())
        except:
            break


# Start both threads
threading.Thread(target=receive).start()
threading.Thread(target=write).start()