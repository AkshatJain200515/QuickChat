import socket
import threading
import config

usernames = {}   
current_room = "General"  

def handle_client(sock, address):
    print(f"[+] Connection established from {address}")
    sock.send(f"NOTIFY{config.DELIMITER}Connected to development build! Set name with SET_NAME/username\n".encode("utf-8"))

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
                username = args[0].strip()
                usernames[sock] = username
                sock.send(f"{config.CMD_NOTIFY}{config.DELIMITER}Welcome {username}!".encode("utf-8"))
                print(f"[DEBUG] User {username} registered from {address}")
                
                
            else:
                sock.send(f"{config.CMD_ERROR}{config.DELIMITER}Command unhandled in early phase".encode("utf-8"))

    except Exception as e:
        print(f"[-] Session error: {e}")
    finally:
        usernames.pop(sock, None)
        sock.close()
        print(f"[-] Connection with {address} terminated.")

def main():
    server_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server_sock.bind((config.HOST, config.PORT))
    server_sock.listen(5)
    print(f"[*] Dev Server listening on {config.HOST}:{config.PORT}")

    while True:
        client_sock, client_addr = server_sock.accept()
        t = threading.Thread(target=handle_client, args=(client_sock, client_addr), daemon=True)
        t.start()

if __name__ == "__main__":
    main()
