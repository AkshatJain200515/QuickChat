import socket
import threading
import logging
import datetime
import config

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler(config.LOG_FILE),
        logging.StreamHandler()
    ]
)


lock = threading.Lock()

rooms = {}       # room name -> set of sockets in that room
usernames = {}   # socket -> username
user_rooms = {}  # socket -> current room name


def build_msg(*parts):
    # Join command parts with the delimiter from config
    return config.DELIMITER.join(str(p) for p in parts)


def send_to(sock, message):
    # Send a message to one specific client
    try:
        sock.send(message.encode("utf-8"))
    except Exception as e:
        logging.warning(f"Could not send to client: {e}")


def broadcast(room, message, exclude=None):
    # Send a message to everyone in a room
    with lock:
        members = list(rooms.get(room, set()))
    for member in members:
        if member is not exclude:
            send_to(member, message)


def init_rooms():
    # Create the default rooms on startup
    with lock:
        for room_name in config.DEFAULT_ROOMS:
            rooms[room_name] = set()
    logging.info(f"Created default rooms: {config.DEFAULT_ROOMS}")


# --- Command handler functions ---
# Each one handles a specific command sent by the client

def handle_set_name(sock, args):
    # Client wants to register a username
    if len(args) < 1:
        send_to(sock, build_msg(config.CMD_ERROR, "Please provide a username"))
        return

    username = args[0].strip()

    if len(username) == 0 or len(username) > config.MAX_USERNAME_LEN:
        send_to(sock, build_msg(config.CMD_ERROR, f"Username must be 1-{config.MAX_USERNAME_LEN} chars"))
        return

    # Check if username is already taken
    with lock:
        taken = username in usernames.values()

    if taken:
        send_to(sock, build_msg(config.CMD_ERROR, f"Username '{username}' is already taken"))
        return

    with lock:
        # Remove old username if they are changing their name
        old_name = usernames.get(sock)
        usernames[sock] = username

    send_to(sock, build_msg(config.CMD_NOTIFY, f"Welcome {username}! Use /help to see commands."))

    # Send them the list of available rooms
    with lock:
        room_list = ",".join(rooms.keys())
    send_to(sock, build_msg(config.CMD_ROOM_LIST, room_list))
    logging.info(f"User registered: {username}")


def handle_join(sock, args):
    # Client wants to join a room
    if len(args) < 1:
        send_to(sock, build_msg(config.CMD_ERROR, "Please provide a room name"))
        return

    room = args[0].strip()

    with lock:
        username = usernames.get(sock, "unknown")
        old_room = user_rooms.get(sock)

        # Leave the previous room first
        if old_room and old_room in rooms:
            rooms[old_room].discard(sock)

        # Create the room if it doesn't exist yet
        if room not in rooms:
            rooms[room] = set()
            logging.info(f"New room created: '{room}'")

        rooms[room].add(sock)
        user_rooms[sock] = room

    send_to(sock, build_msg(config.CMD_JOIN_OK, room))

    # Send the user list for this room
    with lock:
        members = [usernames.get(m, "?") for m in rooms[room]]
    send_to(sock, build_msg(config.CMD_USER_LIST, room, ",".join(members)))

    # Tell everyone else in the room that this user joined
    broadcast(room, build_msg(config.CMD_NOTIFY, f"{username} joined {room}"), exclude=sock)
    logging.info(f"{username} joined room '{room}'")


def handle_send(sock, args):
    # Client is sending a chat message
    if len(args) < 2:
        send_to(sock, build_msg(config.CMD_ERROR, "Usage: SEND/room/message"))
        return

    room = args[0].strip()
    # Rejoin remaining parts in case the message itself contained the delimiter
    text = config.DELIMITER.join(args[1:]).strip()

    with lock:
        username = usernames.get(sock, "unknown")
        in_room = sock in rooms.get(room, set())

    if not in_room:
        send_to(sock, build_msg(config.CMD_ERROR, f"You are not in room '{room}'"))
        return

    if len(text) > config.MAX_MESSAGE_LEN:
        send_to(sock, build_msg(config.CMD_ERROR, "Message is too long"))
        return

    timestamp = datetime.datetime.now().strftime("%H:%M")
    msg = build_msg(config.CMD_MESSAGE, room, username, text, timestamp)
    broadcast(room, msg)  # send to everyone including the sender
    logging.info(f"[{room}] {username}: {text}")


def handle_create(sock, args):
    # Client wants to create a new room
    if len(args) < 1:
        send_to(sock, build_msg(config.CMD_ERROR, "Please provide a room name"))
        return

    room = args[0].strip()

    with lock:
        username = usernames.get(sock, "unknown")
        exists = room in rooms

    if exists:
        send_to(sock, build_msg(config.CMD_ERROR, f"Room '{room}' already exists"))
        return

    with lock:
        rooms[room] = set()

    send_to(sock, build_msg(config.CMD_NOTIFY, f"Room '{room}' created. Use /join {room} to enter."))

    # Update the room list for all connected users
    with lock:
        room_list = ",".join(rooms.keys())
        all_sockets = list(usernames.keys())
    for s in all_sockets:
        send_to(s, build_msg(config.CMD_ROOM_LIST, room_list))

    logging.info(f"Room '{room}' created by {username}")


def handle_invite(sock, args):
    # Client wants to invite another user to a room
    if len(args) < 2:
        send_to(sock, build_msg(config.CMD_ERROR, "Usage: /invite <room> <username>"))
        return

    room = args[0].strip()
    target_name = args[1].strip()

    with lock:
        username = usernames.get(sock, "unknown")
        target_sock = next((s for s, u in usernames.items() if u == target_name), None)

    if target_sock is None:
        send_to(sock, build_msg(config.CMD_ERROR, f"User '{target_name}' not found"))
        return

    send_to(target_sock, build_msg(config.CMD_NOTIFY,
            f"{username} invited you to '{room}'. Type /join {room} to join."))
    send_to(sock, build_msg(config.CMD_NOTIFY, f"Invite sent to {target_name}"))
    logging.info(f"{username} invited {target_name} to '{room}'")


def handle_list(sock, args):
    # Send the client an updated list of rooms
    with lock:
        room_list = ",".join(rooms.keys())
    send_to(sock, build_msg(config.CMD_ROOM_LIST, room_list))


def handle_quit(sock, args):
    # Client is disconnecting
    raise ConnectionResetError("Client disconnected")


def handle_leave(sock, args):
    # Client wants to leave their current room but stay connected
    with lock:
        username = usernames.get(sock, "unknown")
        room = user_rooms.get(sock)
        if room and room in rooms:
            rooms[room].discard(sock)
            user_rooms[sock] = None

    if room:
        broadcast(room, build_msg(config.CMD_NOTIFY, f"{username} left {room}"))
        send_to(sock, build_msg(config.CMD_NOTIFY, f"You left {room}. Use /join <room> to join another room."))
        logging.info(f"{username} left room '{room}'")
    else:
        send_to(sock, build_msg(config.CMD_ERROR, "You are not in any room"))


# Map each command string to its handler function
# This makes it easy to add new commands later
COMMAND_HANDLERS = {
    config.CMD_SET_NAME : handle_set_name,
    config.CMD_JOIN     : handle_join,
    config.CMD_SEND     : handle_send,
    config.CMD_CREATE   : handle_create,
    config.CMD_INVITE   : handle_invite,
    config.CMD_LIST     : handle_list,
    config.CMD_QUIT     : handle_quit,
    config.CMD_LEAVE    : handle_leave,
}


def client_thread(sock, address):
    # This function runs in its own thread for each connected client
    logging.info(f"New connection from {address}")
    send_to(sock, build_msg(config.CMD_NOTIFY, "Connected! Set your name with /name <username>"))

    try:
        while True:
            data = sock.recv(config.BUFFER_SIZE)
            if not data:
                break  # client disconnected

            message = data.decode("utf-8").strip()
            if not message:
                continue

            # Split the message into command + arguments
            parts = message.split(config.DELIMITER)
            command = parts[0]
            args = parts[1:]

            handler = COMMAND_HANDLERS.get(command)
            if handler:
                handler(sock, args)
            else:
                send_to(sock, build_msg(config.CMD_ERROR, f"Unknown command: {command}"))

    except ConnectionResetError as e:
        logging.info(f"Client {address} left: {e}")
    except Exception as e:
        logging.error(f"Error handling client {address}: {e}")
    finally:
        # Clean up when the client disconnects
        with lock:
            username = usernames.pop(sock, "unknown")
            room = user_rooms.pop(sock, None)
            if room and room in rooms:
                rooms[room].discard(sock)
        sock.close()

        if room:
            broadcast(room, build_msg(config.CMD_NOTIFY, f"{username} has left the chat"))

        logging.info(f"Cleaned up: {username} from {address}")


def main():
    init_rooms()

    # Create a TCP socket
    # AF_INET = IPv4, SOCK_STREAM = TCP (reliable, ordered delivery)
    server_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server_sock.bind((config.HOST, config.PORT))
    server_sock.listen(5)
    logging.info(f"Server running on {config.HOST}:{config.PORT}")

    try:
        while True:
            client_sock, client_addr = server_sock.accept()
            # Spawn a new thread for this client so other clients aren't blocked
            t = threading.Thread(target=client_thread, args=(client_sock, client_addr), daemon=True)
            t.start()
    except KeyboardInterrupt:
        logging.info("Server stopped.")
    finally:
        server_sock.close()


if __name__ == "__main__":
    main()
