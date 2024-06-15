from crudeoil.static_vals import TheYuckStuff
import socket
import time
import threading
from datetime import datetime
import signal
import sys
import os
from mimetypes import guess_type
from jinja2 import Environment, FileSystemLoader

class CrudeOil:
    def __init__(
        self, 
        import_name: str, 
        static_url_path: str | None = "/static", 
        static_folder: str | os.PathLike[str] | None = "static", 
        template_folder: str | os.PathLike[str] | None = "templates",
        root_path: str | None = None,
    ):
        #Whatever is empty stays here
        self.routes = {}
        self.route_methods = {}
        self.sse_dict = {}
        self.sse_methods = {}

        #Some important paths
        self.template_folder = self._determine_path(template_folder)
        self.static_folder = self._determine_path(static_folder)
        self.static_url_path = static_url_path + "/"

        #The shit goes here
        self.root_path = os.path.dirname(os.path.abspath(sys.modules[import_name].__file__))
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.env = Environment(loader=FileSystemLoader(self.template_folder))

        #TheYuckStuff goes here
        self.http_status_codes = TheYuckStuff.http_status_codes
        self.run_info = TheYuckStuff.run_info
        self.run_request_log = TheYuckStuff.run_request_log

    def signal_handler(self, sig, frame):
        print("\nServer is shutting down...")
        self.server_socket.close()
        sys.exit(0)

    def _determine_path(self, path: str) -> str:
        if os.path.isabs(path):
            return os.path.join(self.root_path, path)
        return path

    def route(
        self, 
        path: str, 
        methods: list[str] = []) -> callable:
        def decorator(func: callable) -> callable:
            if path not in self.routes and path not in self.sse_dict:
                self.routes[path] = func
                self.route_methods[path] = methods
                return func
            else:
                raise ValueError("Duplicate Route")
        return decorator

    def sse(self, 
            path: str, 
            methods: list[str] = []) -> callable:
        def decorator(func: callable) -> callable:
            if path not in self.sse_dict and path not in self.routes:
                self.sse_dict[path] = func
                self.sse_methods[path] = methods
                return func
            else:
                raise ValueError("Duplicate Route")
        return decorator

    def _build_header(self, headers: tuple[str]) -> str:
        response = ''
        for header in headers:
            response += f'{header}\r\n'
        response += '\r\n'
        return response

    def _page_not_found(
            self, 
            status_code: int | None = 404
        ) -> dict:
        status_code_text = self.http_status_codes[status_code]
        headers = (
            f'HTTP/1.1 {status_code} {status_code_text}',
            f'Content-Type: text/html'
        )
        response = self._build_header(headers)
        response += f'<html><body>{status_code} {status_code_text}</body></html>'
        pnf_resp = {
            "response": response,
            "status_code": status_code
        }
        return pnf_resp

    def _response_check(self, response_json) -> dict:
        default_response = {
            "payload": str(response_json),
            "mime": "text/html",
            "status_code": 200
        }
        if type(response_json).__name__ != "dict":
            return default_response
        else:
            if len(list(response_json.keys())) != 3:
                return default_response
            else:
                rj_keys = list(response_json.keys())
                dr_keys = list(default_response.keys())
                if set(rj_keys) != set(dr_keys):
                    return default_response
                else: 
                    return response_json


    def _serve_static_file(
        self, 
        client_address: str, 
        request_route: str, 
        timestamp: str, 
        file_path: str, 
        client_socket: socket.socket
    ):
        try:
            status_code = 200
            status_code_text = self.http_status_codes[status_code]
            with open(file_path, 'rb') as f:
                content = f.read()
            mime_type, _ = guess_type(file_path)
            headers = (
                f'HTTP/1.1 {status_code} {status_code_text}',
                f'Content-Type: {mime_type}',
                f'Content-Length: {len(content)}'
            )
            response = self._build_header(headers)
            print(self.run_request_log.format(
                    client_ip=client_address[0],
                    timestamp=timestamp,
                    request=request_route,
                    status_code=str(status_code)))
            client_socket.sendall(response.encode('utf-8') + content)
        except FileNotFoundError:
            pnf_resp = self._page_not_found()
            response = pnf_resp["response"]
            print(self.run_request_log.format(
                    client_ip=client_address[0],
                    timestamp=timestamp,
                    request=request_route,
                    status_code=str(pnf_resp["status_code"])))
            client_socket.sendall(response.encode('utf-8'))

    def serve(self, path, category):
        if category == "default":
            return self.routes[path]()

    def default_routes(self, path, method, client_address, timestamp, request_route):
        response_json = self.serve(path, "default")
        response_json = self._response_check(response_json)
        if method == 'GET':
            status_code = response_json["status_code"]
            status_code_text = self.http_status_codes[status_code]
            headers = (
                f'HTTP/1.1 {status_code} {status_code_text}',
                f'Content-Type: {response_json["mime"]}'
            )
            response = self._build_header(headers)
            response += str(response_json["payload"])
            print(self.run_request_log.format(
                client_ip=client_address[0], 
                timestamp=timestamp, 
                request=request_route, 
                status_code=str(status_code)))
        else:
            pnf_resp = self._page_not_found(status_code=405)
            response = pnf_resp["response"]
            print(self.run_request_log.format(
                client_ip=client_address[0], 
                timestamp=timestamp, 
                request=request_route, 
                status_code=str(pnf_resp["status_code"])))
        return response

    def sse_routes(self, path, method, client_address, timestamp, request_route):
        if method == 'GET':
            status_code = 200
            status_code_text = self.http_status_codes[status_code]
            headers = (
                f'HTTP/1.1 {status_code} {status_code_text}',
                f'Content-Type: text/event-stream',
                f'Cache-Control: no-cache',
                f'Connection: keep-alive'
            )
            response = self._build_header(headers)
            print(self.run_request_log.format(
                client_ip=client_address[0], 
                timestamp=timestamp, 
                request=request_route, 
                status_code=str(status_code)))
        return response

    def sse_longrun(self, client_socket, path):
        try:
            sse_generator = self.sse_dict[path]()
            for item in sse_generator:
                client_socket.send(item)
        except BrokenPipeError:
            pass
        finally:
            client_socket.close()


    def run(self, host='localhost', port=5000, debug=False, conn_backlog=5):
        if debug==True:
            self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            debug_state = "on"
        else:
            debug_state = "off"
        self.server_socket.bind((host, port))
        self.server_socket.listen(conn_backlog)

        # Register the signal handler for SIGINT
        signal.signal(signal.SIGINT, self.signal_handler)

        print(self.run_info.format(host=host, port=port, debug_state=debug_state))
        while True:
            client_socket, client_address = self.server_socket.accept()
            request = client_socket.recv(1024).decode('utf-8')
            response = ""
            timestamp = datetime.now().strftime("%d/%b/%Y %H:%M:%S")
            request_route = request.split("\n")[0].strip()
            print(request)
            if request:
                request_line = request.splitlines()[0]
                method, path, _ = request_line.split()
            
                if path in self.sse_dict:
                    if method in self.sse_methods[path]:
                        response = self.sse_routes(path, method, client_address, timestamp, request_route)
                        client_socket.send(response.encode('utf-8'))
                        client_thread = threading.Thread(target=self.sse_longrun, args=(client_socket, path, ))
                        client_thread.start()
                elif path in self.routes:
                    if method in self.route_methods[path]:
                        response = self.default_routes(path, method, client_address, timestamp, request_route)
                    client_socket.sendall(response.encode('utf-8'))
                    client_socket.close()
                elif path.startswith(self.static_url_path):
                    file_path = os.path.join(self.static_folder, path[len(self.static_url_path):])
                    self._serve_static_file(client_address, request_route, timestamp, file_path, client_socket)
                    client_socket.close()
                else:
                    pnf_resp = self._page_not_found()
                    response = pnf_resp["response"]
                    print(self.run_request_log.format(
                        client_ip=client_address[0], 
                        timestamp=timestamp, 
                        request=request_route, 
                        status_code=str(pnf_resp["status_code"])))

                    client_socket.sendall(response.encode('utf-8'))
                    client_socket.close()

def render_template(template_file, mime='text/html', status_code=500, template_args={}):
    local_crudeoil = CrudeOil(__name__)
    template = local_crudeoil.env.get_template(template_file)
    response_body = template.render(template_args)
    return {
                "payload": response_body,
                "mime": mime,
                "status_code": status_code
            }

def response(payload, mime='text/html', status_code=500):
    return {
                "payload": payload,
                "mime": mime,
                "status_code": status_code
            }
