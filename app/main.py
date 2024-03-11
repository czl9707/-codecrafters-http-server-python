import pathlib
import socket
import threading
import argparse
from typing import Dict, Optional


STATIC_DIRECTORY: Optional[pathlib.Path] = None


def resolve_path(path: pathlib.Path) -> Optional[pathlib.Path]:
    if STATIC_DIRECTORY is None:
        return None

    if path.is_absolute():
        if str(path).startswith(str(STATIC_DIRECTORY)):
            return path
    else:
        return STATIC_DIRECTORY.joinpath(path)

    return None


class HTTPRequest:
    method: str
    path: str
    http_version: str
    body: bytes
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
            if len(line) == 0:
                break

            key, value = line.split(b":", maxsplit=1)
            request.headers[key.decode()] = value.decode().strip()

        request.body = b"\r\n".join(line_iter)
        print(request.body)

        return request


def main() -> None:
    arg_parser = argparse.ArgumentParser()
    arg_parser.add_argument("--directory", dest="directory", default=None)
    ns = arg_parser.parse_args()
    global STATIC_DIRECTORY
    STATIC_DIRECTORY = pathlib.Path(ns.directory) if ns.directory is not None else None

    server_socket = socket.create_server(("localhost", 4221), reuse_port=True)
    while True:
        sock, response_addr = server_socket.accept()  # wait for client
        t = threading.Thread(target=lambda: request_handler(sock))
        t.start()


def request_handler(sock: socket.socket) -> None:
    request_bytes = sock.recv(1024)
    request = HTTPRequest.from_bytes(request_bytes)

    headers = {}
    response_body = ""

    response_code = "404 Not Found"
    if request.path == "/":
        response_code = "200 OK"
    elif request.path.startswith("/echo/"):
        response_code = "200 OK"
        response_body = request.path[len("/echo/") :]

        headers["Content-Type"] = "text/plain"
        headers["Content-Length"] = len(response_body)
    elif request.path.startswith("/user-agent"):
        response_code = "200 OK"
        response_body = request.headers.get("User-Agent")

        headers["Content-Type"] = "text/plain"
        headers["Content-Length"] = len(response_body)
    elif request.path.startswith("/files/"):
        if request.method == "GET":
            path = pathlib.Path(request.path[len("/files/") :])
            path = resolve_path(path)
            if path is None or not path.exists():
                response_code = "404 Not Found"
            else:
                with open(path, "r") as f:
                    response_body = f.read()
                response_code = "200 OK"
                headers["Content-Type"] = "application/octet-stream"
                headers["Content-Length"] = len(response_body)
        elif request.method == "POST":
            path = pathlib.Path(request.path[len("/files/") :])
            path = resolve_path(path)
            with open(path, "xb") as f:
                f.write(request.body)
            response_code = "201 Created"

    response_contents = [
        f"{request.http_version} {response_code}",
        *[f"{key}: {value}" for key, value in headers.items()],
        "",
        response_body,
    ]

    sock.send("\r\n".join(response_contents).encode())
    sock.close()


if __name__ == "__main__":
    main()
