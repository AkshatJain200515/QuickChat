import socket
import threading
import sys
import config

current_room = None
username = None
sock = None

def receive_thread():
    global current_room
    while True:
        try:
            data = sock.recv(config.BUFFER_SIZE)
            if not data:
                break
            parts = data.decode("utf-8").strip().split(config.DELIMITER)
            cmd = parts[0]
            args = parts[1:]

            if cmd == config.CMD_MESSAGE:
                print(f"\n[{args[0]}] {args[1]}: {args[2]}")
            elif cmd == config.CMD_JOIN_OK:
                current_room = args[0]
                print(f"\n--- Joined: {current_room} ---")
            elif cmd == config.CMD_ROOM_LIST:
                print(f"\nRooms: {args[0]}")
            elif cmd == config.CMD_NOTIFY:
                print(f"\n*** {args[0]} ***")
            print(f"[{current_room or 'no room'}] > ", end="", flush=True)
        except Exception:
            break

def main():
    global sock, username
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.connect((config.HOST, config.PORT))
    
    threading.Thread(target=receive_thread, daemon=True).start()

    while True:
        try:
            inp = input(f"[{current_room or 'no room'}] > ").strip()
            if not inp: continue
            
            if inp.startswith("/name "):
                username = inp[6:].strip()
                sock.send(f"{config.CMD_SET_NAME}{config.DELIMITER}{username}".encode("utf-8"))
            elif inp.startswith("/join "):
                sock.send(f"{config.CMD_JOIN}{config.DELIMITER}{inp[6:].strip()}".encode("utf-8"))
            elif inp == "/quit":
                break
            else:
                if current_room:
                    sock.send(f"{config.CMD_SEND}{config.DELIMITER}{current_room}{config.DELIMITER}{inp}".encode("utf-8"))
                else:
                    print("Join a room first.")
        except (KeyboardInterrupt, EOFError):
            break
    sock.close()

if __name__ == "__main__":
    main()
