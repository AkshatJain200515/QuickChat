import socket
import threading
import sys
import config

def receive_loop(sock):
    while True:
        try:
            data = sock.recv(config.BUFFER_SIZE)
            if not data:
                print("\n[-] Disconnected from server pipeline.")
                break
            print(f"\n[Raw Stream]: {data.decode('utf-8')}")
        except Exception:
            break

def main():
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        sock.connect((config.HOST, config.PORT))
        print("[+] Hooked into development host.")
    except Exception as e:
        print(f"[-] Hook failed: {e}")
        sys.exit(1)

    t = threading.Thread(target=receive_loop, args=(sock,), daemon=True)
    t.start()

    print("Use syntax: SET_NAME/yourname OR SEND/General/your message")
    while True:
        try:
            user_raw = input("> ").strip()
            if user_raw == "/quit":
                break
            if user_raw:
                sock.send(user_raw.encode("utf-8"))
        except KeyboardInterrupt:
            break
    sock.close()

if __name__ == "__main__":
    main()
