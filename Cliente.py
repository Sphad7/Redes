import socket
import threading

def receive_messages(client_socket):
    while True:
        try:
            message = client_socket.recv(1024).decode("utf-8")
            print(message)

            # Nombre ya ocupado
            if message == "[SERVER] Nombre ya en uso.":
                name = input("Ingresa tu nombre: ")
                client_socket.send(name.encode("utf-8"))

            if message == "[SERVER] Cuéntame, ¿qué artefactos tienes?":
                artifacts = input("Ingresa tus artefactos: ")
                client_socket.send(artifacts.encode("utf-8"))

            if message == "[SERVER] ¿Está Bien?":
                desition = input("Ingresa tus respuesta: ")
                client_socket.send(desition.encode("utf-8"))

            if message == "[SERVER] ¡OK!":
                while True:
                    message_client = input()
                    client_socket.send(message_client.encode("utf-8"))
                    if (message_client.startswith(":q")):
                        break
                break

        except Exception as e:
            print(f"[ERROR] {e}")
            break

def start_client():
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client_socket.connect(("127.0.0.1", 5555))  # Conéctate al servidor en el localhost y puerto 5555

    # Inicia un hilo para recibir mensajes del servidor
    receive_thread = threading.Thread(target=receive_messages, args=(client_socket,))
    receive_thread.start()

    # Ingresar nombre de usuario
    name = input("Ingresa tu nombre: ")
    client_socket.send(name.encode("utf-8"))

    receive_messages(client_socket)

if __name__ == "__main__":
    start_client()
