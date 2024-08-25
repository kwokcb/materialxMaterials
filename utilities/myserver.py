import http.server
import socketserver
import signal

PORT = 8000

class MyHTTPRequestHandler(http.server.SimpleHTTPRequestHandler):
    def end_headers(self):
        self.send_header("Cache-Control", "no-cache, no-store, must-revalidate")
        self.send_header("Pragma", "no-cache")
        self.send_header("Expires", "0")
        super().end_headers()

def signal_handler(sig, frame):
    print('Exiting server...')
    httpd.server_close()
    exit(0)

signal.signal(signal.SIGINT, signal_handler)

print("Serving at port: ", PORT)
with socketserver.TCPServer(("", PORT), MyHTTPRequestHandler) as httpd:
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        pass
    httpd.server_close()
