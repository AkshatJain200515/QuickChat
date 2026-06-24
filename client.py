
import socket
import threading
import sys
import config

# ANSI escape codes for colored terminal output
RESET   = "\033[0m"
BOLD    = "\033[1m"
RED     = "\033[91m"
GREEN   = "\033[92m"
YELLOW  = "\033[93m"
CYAN    = "\033[96m"
MAGENTA = "\033[95m"
DIM     = "\033[2m"

# Global state
current_room = None
username = None
sock = None
running = True


def build_msg(*parts):
    return config.DELIMITER.join(str(p) for p in parts)


def send_cmd(*parts):
    # Send a command to the server
    try:
        sock.send(build_msg(*parts).encode("utf-8"))
    except Exception as e:
        print(f"{RED}[ERROR] Could not send message: {e}{RESET}")


def receive_thread():
    # Runs in background, prints any message received from the server
    global running, current_room

    while running:
        try:
            data = sock.recv(config.BUFFER_SIZE)
            if not data:
                print(f"\n{RED}Disconnected from server.{RESET}")
                running = False
                break

            message = data.decode("utf-8").strip()
            if not message:
                continue

            parts = message.split(config.DELIMITER)
            command = parts[0]
            args = parts[1:]

            if command == config.CMD_MESSAGE:
                # A chat message: show sender and text
                room      = args[0] if len(args) > 0 else "?"
                sender    = args[1] if len(args) > 1 else "?"
                text      = args[2] if len(args) > 2 else ""
                timestamp = args[3] if len(args) > 3 else ""

                color = GREEN if sender == username else CYAN
                print(f"\r{DIM}[{timestamp}]{RESET} {color}{BOLD}{sender}{RESET}: {text}")
                print(f"{DIM}[{current_room or '?'}] > {RESET}", end="", flush=True)

            elif command == config.CMD_JOIN_OK:
                current_room = args[0] if args else "?"
                print(f"\n{YELLOW}--- Joined room: {current_room} ---{RESET}")

            elif command == config.CMD_USER_LIST:
                room  = args[0] if args else "?"
                users = args[1].split(",") if len(args) > 1 else []
                print(f"{MAGENTA}Users in {room}: {', '.join(users)}{RESET}")

            elif command == config.CMD_ROOM_LIST:
                rooms = args[0].split(",") if args else []
                print(f"{MAGENTA}Available rooms: {', '.join(rooms)}{RESET}")

            elif command == config.CMD_NOTIFY:
                text = args[0] if args else ""
                print(f"{YELLOW}*** {text} ***{RESET}")
                print(f"{DIM}[{current_room or '?'}] > {RESET}", end="", flush=True)

            elif command == config.CMD_ERROR:
                text = args[0] if args else "Unknown error"
                print(f"{RED}[!] {text}{RESET}")

        except OSError:
            break
        except Exception as e:
            print(f"{RED}[Receive error] {e}{RESET}")
            break


def parse_input(user_input):
    # Handle user commands and plain text messages
    user_input = user_input.strip()
    if not user_input:
        return

    if user_input.startswith("/name "):
        name = user_input[6:].strip()
        send_cmd(config.CMD_SET_NAME, name)
        global username
        username = name

    elif user_input.startswith("/join "):
        room = user_input[6:].strip()
        send_cmd(config.CMD_JOIN, room)

    elif user_input.startswith("/create "):
        room = user_input[8:].strip()
        send_cmd(config.CMD_CREATE, room)

    elif user_input.startswith("/invite "):
        # Format: /invite <room> <username>
        parts = user_input[8:].strip().split(" ", 1)
        if len(parts) == 2:
            send_cmd(config.CMD_INVITE, parts[0], parts[1])
        else:
            print(f"{RED}Usage: /invite <room> <username>{RESET}")

    elif user_input == "/rooms":
        send_cmd(config.CMD_LIST)

    elif user_input == "/quit":
        send_cmd(config.CMD_QUIT)
        global running
        running = False
        sock.close()
        sys.exit(0)

    elif user_input == "/help":
        print(f"""
{YELLOW}Commands:{RESET}
  /name <username>         - set your display name
  /join <room>             - join a room
  /create <room>           - create a new room
  /invite <room> <user>    - invite someone to a room
  /rooms                   - list all rooms
  /quit                    - disconnect
  <anything else>          - send a message to current room
""")

    else:
        # Plain text = send as chat message to current room
        if current_room is None:
            print(f"{RED}[!] Join a room first with /join <room>{RESET}")
        else:
            send_cmd(config.CMD_SEND, current_room, user_input)


def main():
    global sock, running

    print(f"{CYAN}PyChat - B205 Computer Networks{RESET}")
    print(f"Connecting to {config.HOST}:{config.PORT}...")

    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        sock.connect((config.HOST, config.PORT))
    except ConnectionRefusedError:
        print(f"{RED}Could not connect. Is the server running?{RESET}")
        sys.exit(1)

    print(f"{GREEN}Connected! Type /help for commands.{RESET}\n")

    # Start background thread to receive messages
    t = threading.Thread(target=receive_thread, daemon=True)
    t.start()

    try:
        while running:
            prompt = f"{DIM}[{current_room or 'no room'}] > {RESET}"
            try:
                user_input = input(prompt)
            except EOFError:
                break
            parse_input(user_input)

    except KeyboardInterrupt:
        print(f"\n{YELLOW}Disconnecting...{RESET}")
        send_cmd(config.CMD_QUIT)
    finally:
        running = False
        sock.close()


if __name__ == "__main__":
    main()
