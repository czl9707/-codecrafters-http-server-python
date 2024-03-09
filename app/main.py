# Uncomment this to pass the first stage
import socket
import threading


def main():
    # You can use print statements as follows for debugging, they'll be visible when running tests.
    print("Logs from your program will appear here!")

    server_socket = socket.create_server(("localhost", 4221), reuse_port=True)
    while True:
        sock, response_addr = server_socket.accept()  # wait for client
        request_handler(sock, response_addr)


def request_handler(sock: socket.socket, response_addr) -> None:
    request = sock.recv(1024)
    response = b"HTTP/1.1 200 OK\r\n\r\n"
    sock.send(response)
    sock.close()


if __name__ == "__main__":
    main()
