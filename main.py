from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
from jinja2 import Environment, FileSystemLoader
import json
import os
from datetime import datetime
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
STORAGE_DIR = os.path.join(ROOT_DIR, 'storage')
DATA_FILE = os.path.join(STORAGE_DIR, 'data.json')
STATIC_FILES = {'/style.css': 'style.css', '/logo.png': 'logo.png'}
HTML_FILES = {'/': 'index.html', '/message.html': 'message.html'}

env = Environment(loader=FileSystemLoader(ROOT_DIR))

os.makedirs(STORAGE_DIR, exist_ok=True)
if not os.path.exists(DATA_FILE):
    with open(DATA_FILE, 'w') as f:
        json.dump({}, f)


class SimpleHTTPRequestHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        parsed_path = urlparse(self.path)
        route = parsed_path.path
        logger.info(f"Received GET request for {route}")

        if route in STATIC_FILES:
            self.serve_static_file(STATIC_FILES[route])
        elif route in HTML_FILES:
            self.serve_html_file(HTML_FILES[route])
        elif route == '/read':
            self.serve_read_page()
        else:
            logger.warning(f"404 Not Found for {route}")
            self.serve_html_file('error.html', status=404)

    def do_POST(self):
        parsed_path = urlparse(self.path)
        if parsed_path.path == '/message':
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            data = parse_qs(post_data.decode('utf-8'))
            username = data.get('username', [''])[0]
            message = data.get('message', [''])[0]

            logger.info(f"Received POST request for {parsed_path.path} with data: {data}")

            if username and message:
                self.save_message(username, message)
                self.send_response(302)
                self.send_header('Location', '/')
                self.end_headers()
                logger.info("Message saved successfully")
            else:
                logger.warning("Invalid POST data")
                self.serve_html_file('error.html', status=400)
        else:
            logger.warning(f"404 Not Found for {parsed_path.path}")
            self.serve_html_file('error.html', status=404)

    def serve_static_file(self, filename):
        try:
            with open(filename, 'rb') as file:
                self.send_response(200)
                self.end_headers()
                self.wfile.write(file.read())
                logger.info(f"Served static file {filename}")
        except FileNotFoundError:
            logger.error(f"Static file not found: {filename}")
            self.serve_html_file('error.html', status=404)

    def serve_html_file(self, filename, status=200):
        try:
            with open(filename, 'r', encoding='utf-8') as file:
                self.send_response(status)
                self.send_header('Content-type', 'text/html')
                self.end_headers()
                self.wfile.write(file.read().encode('utf-8'))
                logger.info(f"Served HTML file {filename} with status {status}")
        except FileNotFoundError:
            logger.error(f"HTML file not found: {filename}")
            self.serve_html_file('error.html', status=404)

    def serve_read_page(self):
        try:
            with open(DATA_FILE, 'r') as file:
                data = json.load(file)

            messages = [{'timestamp': timestamp, 'username': info['username'], 'message': info['message']}
                        for timestamp, info in data.items()]
            template = env.get_template('read.html')
            content = template.render(messages=messages)

            self.send_response(200)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            self.wfile.write(content.encode('utf-8'))
            logger.info("Served /read page with messages")
        except Exception as e:
            logger.error(f"Error serving /read page: {e}")
            self.serve_html_file('error.html', status=500)

    def save_message(self, username, message):
        timestamp = datetime.now().isoformat()
        try:
            with open(DATA_FILE, 'r+') as file:
                data = json.load(file)
                data[timestamp] = {'username': username, 'message': message}
                file.seek(0)
                json.dump(data, file, indent=4)
                logger.info(f"Message saved: {username} - {message}")
        except Exception as e:
            with open(DATA_FILE, 'w') as file:
                json.dump({timestamp: {'username': username, 'message': message}}, file)
                logger.error(f"Error saving message, created new data.json: {e}")


def run(server_class=HTTPServer, handler_class=SimpleHTTPRequestHandler):
    server_address = ('', 3000)
    httpd = server_class(server_address, handler_class)
    logger.info("Server started at http://localhost:3000")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        httpd.server_close()
        logger.info("Server stopped.")


if __name__ == '__main__':
    run()
