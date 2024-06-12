from crudeoil.static_vals import TheYuckStuff
import socket
from datetime import datetime
import signal
import sys
import os
from mimetypes import guess_type
from jinja2 import Environment, FileSystemLoader

class CrudeOil:
    def __init__(self, import_name, static_url='/static', static_folder='static', template_folder='templates'):
        #Whatever is empty stays here
        self.routes = {}
        self.route_methods = {}

        #Some important paths
        self.template_folder = self._determine_path(template_folder)
        self.static_folder = self._determine_path(static_folder)

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

    def _determine_path(self, path):
        if os.path.isabs(path):
            return os.path.join(self.root_path, path)
        return path

    def route(self, path, methods=[]):
        def decorator(func):
            self.routes[path] = func
            self.route_methods[path] = methods
            return func
        return decorator

    def _serve_static_file(self, client_address, request_route, timestamp, file_path, client_socket):
        try:
            status_code = 200
            status_code_text = self.http_status_codes[status_code]
            with open(file_path, 'rb') as f:
                content = f.read()
            mime_type, _ = guess_type(file_path)
            response = 'HTTP/1.1 {status_code} {status_code_text}\r\n'
            if mime_type:
                response += f'Content-Type: {mime_type}\r\n'
            response += f'Content-Length: {len(content)}\r\n'
            response += '\r\n'
            print(self.run_request_log.format(
                    client_ip=client_address[0],
                    timestamp=timestamp,
                    request=request_route,
                    status_code=str(status_code)))
            client_socket.sendall(response.encode('utf-8') + content)
        except FileNotFoundError:
            status_code = 404
            status_code_text = self.http_status_codes[status_code]
            response = 'HTTP/1.1 {status_code} {status_code_text}\r\n'
            response += 'Content-Type: text/html\r\n'
            response += '\r\n'
            response += f'<html><body>{status_code} {status_code_text}</body></html>'
            print(self.run_request_log.format(
                    client_ip=client_address[0],
                    timestamp=timestamp,
                    request=request_route,
                    status_code=str(status_code)))
            client_socket.sendall(response.encode('utf-8'))

    def serve(self, path):
        return self.routes[path]()

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
            timestamp = datetime.now().strftime("%d/%b/%Y %H:%M:%S")
            request_route = request.split("\n")[0].strip()
            if request:
                request_line = request.splitlines()[0]
                method, path, _ = request_line.split()
            
                if path in self.routes:
                    if method in self.route_methods[path]:
                        response_json = self.serve(path)
                        if method == 'GET':
                            status_code = response_json["status_code"]
                            status_code_text = self.http_status_codes[status_code]
                            response = f'HTTP/1.1 {status_code} {status_code_text}\r\n'
                            response += f'Content-Type: {response_json["mime"]}\r\n'
                            response += '\r\n'
                            response += str(response_json["payload"])
                            print(self.run_request_log.format(
                                client_ip=client_address[0], 
                                timestamp=timestamp, 
                                request=request_route, 
                                status_code=str(status_code)))
                    else:
                        status_code = 405
                        status_code_text = self.http_status_codes[status_code]
                        response = f'HTTP/1.1 {status_code} {status_code_text}\r\n'
                        response += 'Content-Type: text/html\r\n'
                        response += '\r\n'
                        response += f'<html><body>{status_code} {status_code_text}</body></html>'
                        print(self.run_request_log.format(
                            client_ip=client_address[0], 
                            timestamp=timestamp, 
                            request=request_route, 
                            status_code=str(status_code)))
                elif path.startswith('/static/'):
                    file_path = os.path.join(self.static_folder, path[len('/static/'):])
                    self._serve_static_file(client_address, request_route, timestamp, file_path, client_socket)
                else:
                    status_code = 404
                    status_code_text = self.http_status_codes[status_code]
                    response = f'HTTP/1.1 {status_code} {status_code_text}\r\n'
                    response += 'Content-Type: text/html\r\n'
                    response += '\r\n'
                    response += f'<html><body>{status_code} {status_code_text}</body></html>'
                    print(self.run_request_log.format(
                        client_ip=client_address[0], 
                        timestamp=timestamp, 
                        request=request_route, 
                        status_code=str(status_code)))

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
