import json
import os
import threading
import time
from http.server import HTTPServer, BaseHTTPRequestHandler


DATA_FILE = os.path.join(os.path.dirname(__file__), '..', 'data', 'alerts.jsonl')
os.makedirs(os.path.dirname(DATA_FILE) or '.', exist_ok=True)

alerts = []
flows = []
capture_running = False
packet_count = 0


class APIHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == '/api/status':
            self._json({'status': 'running' if capture_running else 'idle', 'packets': packet_count, 'flows': len(flows), 'alerts': len(alerts)})
        elif self.path == '/api/alerts':
            self._json(alerts[-50:])
        elif self.path == '/api/flows':
            self._json(flows[-100:])
        elif self.path == '/api/config':
            self._json({'sensitivity': 'medium', 'flowTimeout': 60, 'threshold': 0.7, 'bpfFilter': 'ip'})
        elif self.path == '/':
            self._file(os.path.join(os.path.dirname(__file__), '..', 'web', 'index.html'))
        else:
            self.send_error(404)

    def do_POST(self):
        global capture_running, packet_count
        if self.path == '/api/capture/start':
            capture_running = True
            self._json({'status': 'started'})
        elif self.path == '/api/capture/stop':
            capture_running = False
            self._json({'status': 'stopped'})
        elif self.path == '/api/alerts/clear':
            alerts.clear()
            self._json({'status': 'cleared'})
        else:
            self.send_error(404)

    def _json(self, data):
        self.send_response(200)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        self.wfile.write(json.dumps(data).encode())

    def _file(self, path):
        try:
            with open(path, 'rb') as f:
                self.send_response(200)
                if path.endswith('.html'):
                    self.send_header('Content-Type', 'text/html')
                self.end_headers()
                self.wfile.write(f.read())
        except FileNotFoundError:
            self.send_error(404)

    def log_message(self, format, *args):
        pass


def run_server(host='0.0.0.0', port=8080):
    server = HTTPServer((host, port), APIHandler)
    print(f"ShadowSentinel API server running on http://{host}:{port}")
    server.serve_forever()


def background_simulator():
    global packet_count
    while True:
        if capture_running:
            packet_count += 1
            if len(flows) > 1000:
                flows.clear()
        time.sleep(0.1)


if __name__ == '__main__':
    t = threading.Thread(target=background_simulator, daemon=True)
    t.start()
    run_server()
