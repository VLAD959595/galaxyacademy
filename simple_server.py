#!/usr/bin/env python3
import http.server
import ssl
import socketserver
import os

PORT = 8443
Handler = http.server.SimpleHTTPRequestHandler

# Создаем самоподписанный сертификат
os.system('openssl req -new -x509 -keyout server.pem -out server.pem -days 365 -nodes -subj "/C=RU/ST=State/L=City/O=Organization/CN=localhost"')

with socketserver.TCPServer(("", PORT), Handler) as httpd:
    context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
    context.load_cert_chain('server.pem')
    httpd.socket = context.wrap_socket(httpd.socket, server_side=True)
    print(f"HTTPS Server running at https://localhost:{PORT}")
    print("Accept certificate warning in browser")
    httpd.serve_forever()