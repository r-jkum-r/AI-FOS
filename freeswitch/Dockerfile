FROM python:3.11-slim

ENV FREESWITCH_PASSWORD=ClueCon
ENV LISTEN_PORT=8021

# Install minimal dependencies for SIP simulation
RUN apt-get update && apt-get install -y \
    netcat-openbsd \
    && rm -rf /var/lib/apt/lists/*

# Create freeswitch working directory
WORKDIR /app

# Create mock FreeSWITCH ESL server
RUN cat > esl_server.py << 'EOFPY' && chmod +x esl_server.py
#!/usr/bin/env python3
import socket
import threading
import sys
from datetime import datetime

PASSWORD = "ClueCon"
PORT = 8021

class ESLServer:
    def __init__(self, password, port):
        self.password = password
        self.port = port
        self.authenticated = False
        
    def handle_client(self, client_socket, addr):
        print(f"[ESL] Client connected from {addr}")
        client_socket.send(b"Content-Type: auth/request\n\n")
        
        try:
            data = client_socket.recv(1024).decode()
            if f"password {self.password}" in data:
                self.authenticated = True
                client_socket.send(b"Content-Type: command/reply\nReply-Text: +OK accepted\n\n")
                print(f"[ESL] Client authenticated")
                
                # Keep connection alive and respond to commands
                while True:
                    data = client_socket.recv(1024).decode()
                    if not data:
                        break
                    
                    if "status" in data:
                        response = "Content-Type: command/reply\nReply-Text: +OK\nChannel-Count: 1\nSession-Count: 1\nCalls-In: 0\nCalls-Out: 0\nIdleCPUUsage: 0.50\nActiveSessions: 1\nVersion: 1.10.11-mock\nUptime: UP 1 months 0 days 0 hours 0 minutes 0 seconds, 1024 session(s)\n\n"
                        client_socket.send(response.encode())
                    else:
                        client_socket.send(b"Content-Type: command/reply\nReply-Text: +OK\n\n")
            else:
                client_socket.send(b"Content-Type: command/reply\nReply-Text: -ERR invalid password\n\n")
                print(f"[ESL] Authentication failed")
        except Exception as e:
            print(f"[ESL] Error: {e}")
        finally:
            client_socket.close()
            print(f"[ESL] Client disconnected from {addr}")
    
    def start(self):
        server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        server.bind(("0.0.0.0", self.port))
        server.listen(5)
        print(f"[ESL] Server listening on port {self.port}")
        
        try:
            while True:
                client_socket, addr = server.accept()
                thread = threading.Thread(target=self.handle_client, args=(client_socket, addr))
                thread.daemon = True
                thread.start()
        except KeyboardInterrupt:
            print("[ESL] Server shutting down")
        finally:
            server.close()

if __name__ == "__main__":
    server = ESLServer(PASSWORD, PORT)
    server.start()
EOFPY

# Expose ESL and SIP ports
EXPOSE 8021 5060/udp 5060/tcp

# Health check - try to connect to ESL port
HEALTHCHECK --interval=15s --timeout=5s --retries=5 \
  CMD nc -z localhost 8021 || exit 1

# Run the mock ESL server
CMD ["python3", "/app/esl_server.py"]
