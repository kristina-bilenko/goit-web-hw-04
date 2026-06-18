import mimetypes
from http.server import HTTPServer, BaseHTTPRequestHandler
import urllib.parse
import socket
import threading
from pathlib import Path
import json
from datetime import datetime

UDP_IP = '127.0.0.1'
UDP_PORT = 5000


class HttpHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        parsed_url = urllib.parse.urlparse(self.path)
        if parsed_url.path == "/":
            self.send_html_file("index.html")
        elif parsed_url.path == "/message.html":
            self.send_html_file("message.html")
        else:
            if Path().joinpath(parsed_url.path[1:]).exists():
                self.send_static()
            else:
                self.send_html_file("error.html", 404)

    def send_html_file(self, filename, status = 200):
        self.send_response(status)
        self.send_header("Content-type", "text/html")
        self.end_headers()
        with open(filename, "rb") as fd:
            self.wfile.write(fd.read())

    def send_static(self):
        self.send_response(200)
        mt = mimetypes.guess_type(self.path)
        if mt[0]:
            self.send_header("Content-type", mt[0])
        else:
            self.send_header("Content-type", "text/plain")
        self.end_headers()
        with open(Path(self.path[1:]), "rb") as file:
            self.wfile.write(file.read())

    def do_POST(self):
        data = self.rfile.read(int(self.headers["Content-Length"]))
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as client_socket:
            client_socket.sendto(data, (UDP_IP, UDP_PORT))
        self.send_response(302)
        self.send_header("Location", "/message.html")
        self.end_headers()

def run(server_class=HTTPServer, handler_class=HttpHandler):
    server_address = ("", 3000)
    http = server_class(server_address, handler_class)
    try:
        http.serve_forever()
    except KeyboardInterrupt:
        http.server_close()

def run_server():
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind((UDP_IP, UDP_PORT))
    try:
        while True:
            data, address = sock.recvfrom(1024)
            data_dict = dict(urllib.parse.parse_qsl(data.decode("utf-8")))
            save_data(data_dict)
    except KeyboardInterrupt:
        print("UDP server stopped")
    finally:
        sock.close()

def save_data(data_dict):
    storage_dir = Path("storage")
    storage_dir.mkdir(exist_ok=True)
    file_path = storage_dir / "data.json"
    data = {}
    if file_path.exists():
        with open(file_path, "r", encoding="utf-8") as file:
            try:
                data = json.load(file)
            except json.JSONDecodeError:
                data = {}
    data[str(datetime.now())] = data_dict
    with open(file_path, "w", encoding="utf-8") as file:
        json.dump(data, file, ensure_ascii=False, indent=4)

def start_http():
    run()

def start_udp():
    run_server()

if __name__ == "__main__":
    http_thread = threading.Thread(target=start_http)
    udp_thread = threading.Thread(target=start_udp)
    http_thread.start()
    udp_thread.start()
    http_thread.join()
    udp_thread.join()

