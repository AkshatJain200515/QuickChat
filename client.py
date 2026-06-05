import socket

HOST = '127.0.0.1'
PORT = 65432

# Create the client TCP socket
client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

try:
    # Attempt to connect to the server
    client_socket.connect((HOST, PORT))
    print(f"[+] Connected to server at {HOST}:{PORT}")
    
    # Receive up to 1024 bytes of data
    response = client_socket.recv(1024)
    print(f"[Server Response]: {response.decode('utf-8')}")

except ConnectionRefusedError:
    print("[-] Could not connect to the server. Is it running?")
finally:
    # Ensure the socket is closed cleanly
    client_socket.close()
