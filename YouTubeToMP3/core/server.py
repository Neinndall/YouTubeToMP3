import http.server
import socketserver
import json
import threading
import urllib.parse
import os
import subprocess

PORT = 48123

class ServerState:
    def __init__(self):
        self.is_downloading = False
        self.progress = 0.0
        self.status_message = "Ready to download"
        self.current_title = ""
        self.speed = ""
        self.eta = ""
        self.last_downloaded = None
        self.last_error = None
        self.download_queue_callback = None
        self.output_folder = os.path.join(os.path.expanduser("~"), "Music", "YouTube MP3")

    def update_progress(self, data: dict):
        status = data.get('status')
        if status == 'downloading':
            self.is_downloading = True
            self.progress = data.get('percent', 0.0)
            self.speed = data.get('speed', '')
            self.eta = data.get('eta', '')
            self.current_title = data.get('title', self.current_title)
            self.status_message = f"Downloading ({self.progress:.0f}%)"
        elif status == 'converting':
            self.status_message = "Converting to MP3 & embedding album art..."
            self.progress = 100.0
        elif status == 'finished':
            self.is_downloading = False
            self.progress = 100.0
            self.status_message = "Download completed!"
            self.last_downloaded = data.get('filepath')
            self.current_title = data.get('title', '')
        elif status == 'error':
            self.is_downloading = False
            self.status_message = "Download error"
            self.last_error = data.get('error')

state = ServerState()

class ApiRequestHandler(http.server.BaseHTTPRequestHandler):
    def _send_cors_headers(self):
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type, Authorization')

    def do_OPTIONS(self):
        self.send_response(200)
        self._send_cors_headers()
        self.end_headers()

    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        params = urllib.parse.parse_qs(parsed.query)

        if parsed.path in ('/', '/ping', '/health'):
            self.send_response(200)
            self._send_cors_headers()
            self.send_header('Content-Type', 'application/json; charset=utf-8')
            self.end_headers()
            payload = {
                "status": "ok",
                "app": "YouTubeToMP3",
                "version": "1.0.0",
                "output_folder": state.output_folder
            }
            self.wfile.write(json.dumps(payload).encode('utf-8'))

        elif parsed.path == '/status':
            self.send_response(200)
            self._send_cors_headers()
            self.send_header('Content-Type', 'application/json; charset=utf-8')
            self.end_headers()
            payload = {
                "is_downloading": state.is_downloading,
                "progress": state.progress,
                "status_message": state.status_message,
                "title": state.current_title,
                "speed": state.speed,
                "eta": state.eta,
                "last_downloaded": state.last_downloaded,
                "last_error": state.last_error
            }
            self.wfile.write(json.dumps(payload).encode('utf-8'))

        elif parsed.path == '/download':
            url = params.get('url', [None])[0]
            quality = params.get('quality', ['320'])[0]
            if not url:
                self.send_response(400)
                self._send_cors_headers()
                self.send_header('Content-Type', 'application/json; charset=utf-8')
                self.end_headers()
                self.wfile.write(json.dumps({"error": "Missing 'url' parameter."}).encode('utf-8'))
                return

            if state.download_queue_callback:
                state.download_queue_callback(url, quality)
                self.send_response(200)
                self._send_cors_headers()
                self.send_header('Content-Type', 'application/json; charset=utf-8')
                self.end_headers()
                self.wfile.write(json.dumps({"success": True, "message": "Download queued."}).encode('utf-8'))
            else:
                self.send_response(503)
                self._send_cors_headers()
                self.send_header('Content-Type', 'application/json; charset=utf-8')
                self.end_headers()
                self.wfile.write(json.dumps({"error": "Download manager not ready."}).encode('utf-8'))

        elif parsed.path == '/open_folder':
            folder = state.output_folder
            if os.path.exists(folder):
                subprocess.Popen(f'explorer "{os.path.abspath(folder)}"')
            self.send_response(200)
            self._send_cors_headers()
            self.send_header('Content-Type', 'application/json; charset=utf-8')
            self.end_headers()
            self.wfile.write(json.dumps({"success": True}).encode('utf-8'))

        else:
            self.send_response(404)
            self._send_cors_headers()
            self.end_headers()

    def do_POST(self):
        parsed = urllib.parse.urlparse(self.path)
        content_length = int(self.headers.get('Content-Length', 0))
        post_data = self.rfile.read(content_length) if content_length > 0 else b'{}'
        
        try:
            data = json.loads(post_data.decode('utf-8')) if post_data else {}
        except Exception:
            data = {}

        if parsed.path == '/download':
            url = data.get('url')
            quality = data.get('quality', '320')
            if not url:
                self.send_response(400)
                self._send_cors_headers()
                self.send_header('Content-Type', 'application/json; charset=utf-8')
                self.end_headers()
                self.wfile.write(json.dumps({"error": "Field 'url' is required."}).encode('utf-8'))
                return

            if state.download_queue_callback:
                state.download_queue_callback(url, quality)
                self.send_response(200)
                self._send_cors_headers()
                self.send_header('Content-Type', 'application/json; charset=utf-8')
                self.end_headers()
                self.wfile.write(json.dumps({"success": True, "message": "Download initiated."}).encode('utf-8'))
            else:
                self.send_response(503)
                self._send_cors_headers()
                self.send_header('Content-Type', 'application/json; charset=utf-8')
                self.end_headers()
                self.wfile.write(json.dumps({"error": "Download manager not ready."}).encode('utf-8'))

        elif parsed.path == '/open_folder':
            folder = state.output_folder
            if os.path.exists(folder):
                subprocess.Popen(f'explorer "{os.path.abspath(folder)}"')
            self.send_response(200)
            self._send_cors_headers()
            self.send_header('Content-Type', 'application/json; charset=utf-8')
            self.end_headers()
            self.wfile.write(json.dumps({"success": True}).encode('utf-8'))

        else:
            self.send_response(404)
            self._send_cors_headers()
            self.end_headers()

    def log_message(self, format, *args):
        # Suppress request logging from flooding the terminal
        return

class ReusableTCPServer(socketserver.ThreadingTCPServer):
    allow_reuse_address = True

def start_server_thread(download_callback=None, output_folder=None, port=PORT):
    """Starts the background HTTP API server."""
    if download_callback:
        state.download_queue_callback = download_callback
    if output_folder:
        state.output_folder = output_folder

    server = ReusableTCPServer(("127.0.0.1", port), ApiRequestHandler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    return server, thread
