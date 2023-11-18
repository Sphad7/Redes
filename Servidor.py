import socket
import threading
import json

# Cargar el JSON desde el archivo 'artefactos.json'
with open('artefactos.json', 'r') as json_file:
    data_artifacts = json.load(json_file)

# Diccionario para guardar los intercambios
clients_exchange = {}

# Crear un mutex
mutex = threading.Lock()

def handle_client(client_socket, clients, client_names, client_artifacts):
    
    # Recibe el nombre del cliente
    while True:
        name = client_socket.recv(1024).decode("utf-8")
        if is_name_taken(name, client_names):
            client_socket.send("[SERVER] Nombre ya en uso.".encode("utf-8"))
        else:
            welcome_message = f"[SERVER] Cliente {name} conectado."
            print(welcome_message)
            with mutex:
                client_names[client_socket] = name
            break

    # Envía el mensaje de bienvenida al cliente
    welcome_message_client = f"Bienvenid@ al chat de Granjerxs!"
    client_socket.send(welcome_message_client.encode("utf-8"))

    # Notifica a los otros clientes sobre la nueva conexión
    broadcast_message = f"[SERVER] Cliente {name} conectado."
    broadcast(clients, client_socket, broadcast_message)


    # Bucle de artefactos
    while True:
        a = artefactos(client_socket, data_artifacts)
        desition = client_socket.recv(1024).decode("utf-8")
        if (desition.lower() == "si"):
            client_artifacts = a
            with mutex:
                client_names[client_socket] = {'name': name, 'artifacts': client_artifacts}
            break

    # Envía el mensaje de OK
    message_client_ok = f"[SERVER] ¡OK!"
    client_socket.send(message_client_ok.encode("utf-8"))

    # Bucle principal para manejar los mensajes del cliente
    while True:
        try:
            message = client_socket.recv(1024).decode("utf-8")
            if not message:
                break

            # Comandos
            if message.startswith(":q"):
                client_socket.send("[SERVER] ¡Adiós y suerte completando tu colección!".encode("utf-8"))
                remove_client(clients, client_names, client_socket)
                client_socket.close()
                break

            elif message.startswith(":p"):
                _, identifier, private_message = message.split(" ", 2)
                whisp(name, client_names, private_message, identifier)

            elif message.startswith(":u"):
                connected_users = map(lambda x: x['name'], client_names.values())
                connected_users = list(connected_users)
                client_socket.send(f"[SERVER] Usuarios conectados: {', '.join(connected_users)}".encode("utf-8"))

            
            # Emojis
            elif message.startswith(":smile"):
                emoticon_message = ":)"
                broadcast_message = f"{name}: {emoticon_message}"
                broadcast(clients, client_socket, broadcast_message)

            elif message.startswith(":angry"):
                emoticon_message = ">:("
                broadcast_message = f"{name}: {emoticon_message}"
                broadcast(clients, client_socket, broadcast_message)

            elif message.startswith(":combito"):
                emoticon_message = "Q(’- ’Q)"
                broadcast_message = f"{name}: {emoticon_message}"
                broadcast(clients, client_socket, broadcast_message)

            elif message.startswith(":larva"):
                emoticon_message = "¡Larva! (:o)OOOooo"
                broadcast_message = f"{name}: {emoticon_message}"
                broadcast(clients, client_socket, broadcast_message)

            # Logica de artefactos
            elif message.startswith(":artefactos"):
                client_socket.send(f"[SERVER] Tus artefactos son: \n{', '.join(client_artifacts)}".encode("utf-8"))

            elif message.startswith(":artefacto"):
                _, artifact = message.split(" ", 1)
                client_socket.send(f"[SERVER] El artefacto es: {ask_artifact(data_artifacts, artifact)}".encode("utf-8"))

            elif message.startswith(":offer"):
                _, identifier, my_artifact, his_artifact = message.split(" ", 3)
                his_artifact = ask_artifact(data_artifacts, his_artifact)
                my_artifact = ask_artifact(data_artifacts, my_artifact)
                
                # Si tengo el artefacto que quiero intercambiar y si el otro usuario tiene el item que quiero intercambiar
                if (my_artifact in client_artifacts and them_artifact(identifier, his_artifact, client_names)):
                    # Pregunta al usuario correspondiente
                    exchange(name, client_names, f"su {my_artifact} por tu {his_artifact}", identifier)

                    #agregamos en un diccionario los artefactos que se van a cambiar
                    with mutex:
                        clients_exchange[identifier] = str(name), my_artifact, his_artifact
                        #print(f"Tradeo: {clients_exchange}")
                else: 
                    client_socket.send(f"[SERVER] Error de Intercambio".encode("utf-8"))

            elif message.startswith(":accept"):
                #aceptamos la solicitud de intercambio
                accept(name,client_artifacts, clients_exchange,client_names)                             
                clients_exchange.pop(name) 
                #print(f"Aceptado: {clients_exchange}")
                client_socket.send(f"[SERVER] Intercambio aceptado, ahora tus artefactos son: \n{', '.join(client_artifacts)}\n".encode("utf-8"))

            elif message.startswith(":reject"):
                # Mensaje de Intercambio rechazado
                reject_message = f"[SERVER] Rechazaste el intercambio"
                client_socket.send(reject_message.encode("utf-8"))
                
                identifier = clients_exchange[name][0]

                reject(client_names, identifier)
                with mutex:                           
                    clients_exchange.pop(name)
                    #print(f"rechazado: {clients_exchange}") 

            else:
                broadcast_message = f"{name}: {message}"
                broadcast(clients, client_socket, broadcast_message)

        except Exception as e:
            break

    # Elimina al cliente desconectado
    remove_client(clients, client_names, client_socket)

    # Notifica a los demas usuarios
    disconnect_message = f"[SERVER] {name} desconectado."
    broadcast(clients, client_socket, disconnect_message)

    # Cierre de socket
    client_socket.close()    
                
# Funcion para pedirle los artefactos al usuario
def artefactos(client_socket, data_artifacts):
    # Pregunta por los artefactos y los envía al cliente
    ask_for_artifacts = f"[SERVER] Cuéntame, ¿qué artefactos tienes?"
    client_socket.send(ask_for_artifacts.encode("utf-8"))

    # Recibe los artefactos del cliente
    artifacts = client_socket.recv(1024).decode("utf-8")
        
    # Convertir la cadena de artefactos a una lista de números
    artifacts_list = [int(num) for num in artifacts.split(", ")]

    # Obtener los nombres de los artefactos correspondientes a los números en la lista
    artifacts_names = [data_artifacts[str(num)] for num in artifacts_list if str(num) in data_artifacts]

    # Enviar listas de artefactos al cliente        
    client_socket.send(f"[SERVER] Tus artefactos son: \n{', '.join(artifacts_names)}".encode("utf-8"))

    # Pregunta por los artefactos y los envía al cliente
    Desition = f"[SERVER] ¿Está Bien?"
    client_socket.send(Desition.encode("utf-8"))

    return artifacts_names

#función para aceptar intercambio, modifica los artefactos del que solicita y acepta el intercambio
def accept(name,client_artifacts, clients_exchange, client_names):
    for nombre, cambio in clients_exchange.items():
        if name == nombre:
            try:
                sender, his_artifact, my_artifact = cambio
                with mutex:
                    client_artifacts.remove(my_artifact)
                    client_artifacts.append(his_artifact)
                #intercambiamos los artefactos del que solicitó el intercambio
                trade_artifact(sender,his_artifact,my_artifact,client_names)   
            except Exception as e:
                print(f"[ERROR] {e}")

#función para rechaza intercambio, avisa al que propuso el intercambio que el intercambio fue rechazado
def reject(client_names, identifier):
    for socket, data in client_names.items():
        nombre = data['name']
        if nombre == identifier:
            try:
                reject = f"[SERVER] Intercambio rechazado"
                socket.send(reject.encode("utf-8"))
            except Exception as e:
                print(f"[ERROR] {e}")

#Función utilizada para cambiar los artefactos de quién pidió el interacambio
def trade_artifact(sender, his_artifact, my_artifact, client_names):
    for socket, data in client_names.items():
        nombre = data['name']
        if nombre == sender :
            try:
                
                with mutex:
                    data["artifacts"].remove(his_artifact)
                    data["artifacts"].append(my_artifact)   

                accept = f"[SERVER] Intercambio realizado, tus artefactos ahora son: \n{', '.join(data['artifacts'])}"
                socket.send(accept.encode("utf-8"))
            except Exception as e:
                print(f"[ERROR] {e}")
             

def them_artifact(identifier, his_artifact, client_names):
    for socket, data in client_names.items():
        nombre = data['name']
        artefactos = data['artifacts']
        if nombre == identifier and his_artifact in artefactos:
            return True
    print(f"his_artifact = {his_artifact}")
    return False

# Devuelve el artefacto segun el id
def ask_artifact(data_artifacts, artifact):
    # Obtener los nombres de los artefactos correspondientes a los números en la lista
    artifact_name = data_artifacts[artifact]
    return artifact_name


# Mandar mensaje a todos los usuarios
def broadcast(clients, sender_socket, message):
    for client in clients:
        # Evitar mandar mensaje al propio emisor
        if client != sender_socket:
            try:
                client.send(message.encode("utf-8"))
            except Exception as e:
                print(f"[ERROR] {e}")


# Susurrar a otro usuario
def whisp(name, client_names, message, identifier):
    for socket, data in client_names.items():
        nombre = data['name']
        if nombre == identifier:
            try:
                whispeo = f"{name} te susurra: {message}"
                socket.send(whispeo.encode("utf-8"))
            except Exception as e:
                print(f"[ERROR] {e}")


# Mensaje de intercambio al usuario
def exchange(name, client_names, message, identifier):
    for socket, data in client_names.items():
        nombre = data['name']
        if nombre == identifier:
            try:
                whispeo = f"[SERVER] {name} quiere intercambiar {message}"
                socket.send(whispeo.encode("utf-8"))
            except Exception as e:
                print(f"[ERROR] {e}")


# Eliminar cliente del servidor
def remove_client(clients, client_names, client_socket):
    if client_socket in clients:
        with mutex:
            client_info = client_names.pop(client_socket, "Usuario Desconocido")
        #print(f'{client_info}') <- Comprobar que obtiene client_info
        if client_info != "Usuario Desconocido":
            name = client_info.get("name", "Usuario Desconocido")
            print(f"[SERVER] Cliente {name} desconectado.")
            clients.remove(client_socket)


# Verifica si el nombre ya está en uso por otro cliente.
def is_name_taken(name, client_names):
    with mutex:
        return name.lower() in map(lambda x: x['name'].lower(), client_names.values())


def start_server():

    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind(("0.0.0.0", 5555))
    server.listen(3)

    print("[SERVER] Esperando conexiones...")

    clients = [] #nombres 
    client_names = {} #socket e identificador
    client_artifacts = [] #artefactos del cliente

    while True:
        client_socket, addr = server.accept()
        clients.append(client_socket)

        # Inicia un hilo para manejar cada cliente
        client_handler = threading.Thread(target=handle_client, args=(client_socket, clients, client_names, client_artifacts))
        client_handler.start()

if __name__ == "__main__":
    start_server()
