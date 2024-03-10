# Uncomment this to pass the first stage
import socket
import threading
from typing import Dict


class HTTPRequest:
    method: str
    path: str
    http_version: str
    headers: Dict[str, str]

    def __init__(self) -> None:
        self.headers = {}

    @staticmethod
    def from_bytes(request_bytes: bytes) -> "HTTPRequest":
        request = HTTPRequest()

        line_iter = iter(request_bytes.split(b"\r\n"))
        line = next(line_iter)
        request.method, request.path, request.http_version = [
            b.decode() for b in line.split(b" ")
        ]

        for line in line_iter:
            if len(line.strip()) == 0:
                continue

            key, value = line.split(b":", maxsplit=1)
            request.headers[key.decode()] = value.decode().strip()

        return request


def main() -> None:
    server_socket = socket.create_server(("localhost", 4221), reuse_port=True)
    while True:
        sock, response_addr = server_socket.accept()  # wait for client
        request_handler(sock)


def request_handler(sock: socket.socket) -> None:
    request_bytes = sock.recv(1024)
    request = HTTPRequest.from_bytes(request_bytes)

    if request.path == "/":
        response_code = "200 OK"
    else:
        response_code = "404 Not Found"

    response_bytes = f"{request.http_version} {response_code}\r\n\r\n".encode()

    sock.send(response_bytes)
    sock.close()


if __name__ == "__main__":
    main()
