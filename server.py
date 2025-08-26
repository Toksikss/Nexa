import socket
import threading

HOST = "0.0.0.0"
PORT = 8080

clients = []


def broadcast(message, sender_socket):

    for client in clients:
        if client != sender_socket:
            try:
                client.sendall(message)
            except:
                clients.remove(client)


def handle_client(client_socket):
    try:
        username = client_socket.recv(1024).decode("utf-8")
        welcome = f"MSG::Система: {username} приєднався до чату"
        print(welcome)
        broadcast(welcome.encode("utf-8"), client_socket)

        while True:
            msg = client_socket.recv(65536)
            if not msg:
                break

            decoded = msg.decode("utf-8", errors="ignore")

            # Якщо це фото
            if decoded.startswith("IMG::"):
                print(f"{username} надіслав фото")
                broadcast(msg, client_socket)
            else:
                # Текстове повідомлення
                full_msg = f"MSG::{username}: {decoded}"
                print(full_msg)
                broadcast(full_msg.encode("utf-8"), client_socket)

    except Exception as e:
        print(f"Помилка з {username}: {e}")
    finally:
        if client_socket in clients:
            clients.remove(client_socket)
        leave_msg = f"MSG::Система: {username} вийшов з чату"
        print(leave_msg)
        broadcast(leave_msg.encode("utf-8"), client_socket)
        client_socket.close()


def start_server():
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.bind((HOST, PORT))
    server_socket.listen()
    print(f"Сервер запущено на {HOST}:{PORT}")

    while True:
        client_socket, addr = server_socket.accept()
        clients.append(client_socket)
        print(f"Підключився {addr}")
        threading.Thread(target=handle_client, args=(client_socket,), daemon=True).start()


if __name__ == "__main__":
    start_server()
