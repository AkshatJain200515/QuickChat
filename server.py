import socket
import threading
import config

lock = threading.Lock()
rooms = {"General": set(), "Tech": set()}
usernames = {}
user_rooms = {}

def send_to(sock, message):
    try:
        sock.send(message.encode("utf-8"))
    except Exception:
        pass

def broadcast(room, message, exclude=None):
    with lock:
        members = list(rooms.get(room, set()))
    for member in members:
        if member is not exclude:
            send_to(member, message)

def handle_client(sock, address):
    send_to(sock, f"{config.CMD_NOTIFY}{config.DELIMITER}Connected. Set name with /name")
    try:
        while True:
            data = sock.recv(config.BUFFER_SIZE)
            if not data:
                break

            message = data.decode("utf-8").strip()
            parts = message.split(config.DELIMITER)
            command = parts[0]
            args = parts[1:]

            if command == config.CMD_SET_NAME and args:
                name = args[0].strip()
                with lock:
                    usernames[sock] = name
                send_to(sock, f"{config.CMD_NOTIFY}{config.DELIMITER}Name set to {name}")
                with lock:
                    r_list = ",".join(rooms.keys())
                send_to(sock, f"{config.CMD_ROOM_LIST}{config.DELIMITER}{r_list}")

            elif command == config.CMD_JOIN and args:
                room = args[0].strip()
                with lock:
                    name = usernames.get(sock, "unknown")
                    old_room = user_rooms.get(sock)
                    if old_room and old_room in rooms:
                        rooms[old_room].discard(sock)
                    if room not in rooms:
                        rooms[room] = set()
                    rooms[room].add(sock)
                    user_rooms[sock] = room

                send_to(sock, f"{config.CMD_JOIN_OK}{config.DELIMITER}{room}")
                broadcast(room, f"{config.CMD_NOTIFY}{config.DELIMITER}{name} joined {room}", exclude=sock)

            elif command == config.CMD_SEND and len(args) >= 2:
                room = args[0].strip()
                text = config.DELIMITER.join(args[1:]).strip()
                with lock:
                    name = usernames.get(sock, "unknown")
                msg = f"{config.CMD_MESSAGE}{config.DELIMITER}{room}{config.DELIMITER}{name}{config.DELIMITER}{text}"
                broadcast(room, msg)

    except Exception:
        pass
    finally:
        with lock:
            name = usernames.pop(sock, "unknown")
            room = user_rooms.pop(sock, None)
            if room and room in rooms:
                rooms[room].discard(sock)
        sock.close()
        if room:
            broadcast(room, f"{config.CMD_NOTIFY}{config.DELIMITER}{name} left")

def main():
    server_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server_sock.bind((config.HOST, config.PORT))
    server_sock.listen(5)
    while True:
        client_sock, client_addr = server_sock.accept()
        threading.Thread(target=handle_client, args=(client_sock, client_addr), daemon=True).start()

if __name__ == "__main__":
    main()
