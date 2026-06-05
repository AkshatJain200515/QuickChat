import socket

# Define connection constants
HOST = '127.0.0.1'  # Localhost
PORT = 65432        # Arbitrary non-privileged port

# Create a TCP socket (AF_INET = IPv4, SOCK_STREAM = TCP)
server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

# Bind the socket to the address and port
server_socket.bind((HOST, PORT))

# Listen for incoming connections (max backlog of 5)
server_socket.listen(5)
print(f"[*] Server listening on {HOST}:{PORT}...")

try:
    # Accept a single incoming connection
    client_socket, client_address = server_socket.accept()
    print(f"[+] Accepted connection from {client_address}")
    
    # Send an initial welcome byte-string to the client
    client_socket.sendall(b"Welcome to the Chat Server Boilerplate!\n")
    
    # Close the client socket connection
    client_socket.close()
finally:
    # Clean up the server socket
    server_socket.close()
    print("[*] Server shut down.")
