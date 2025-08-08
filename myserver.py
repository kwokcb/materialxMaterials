import http.server
import socketserver
import signal
import argparse

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

def main():
    # Get PORT argument
    parser = argparse.ArgumentParser()
    parser.add_argument("-p", "--port", default=8000, type=int, help="port number to listen on")
    args = parser.parse_args()
    if args.port:
        PORT = args.port

    signal.signal(signal.SIGINT, signal_handler)

    print("Serving at port: ", PORT)
    with socketserver.TCPServer(("", PORT), MyHTTPRequestHandler) as httpd:
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            pass
        httpd.server_close()

if __name__ == "__main__":
    main()
