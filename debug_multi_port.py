import socket
import json

def check_port(port):
    print(f"Checking port {port}...")
    try:
        with socket.create_connection(("localhost", port), timeout=1) as sock:
            print(f"  SUCCESS: Port {port} is listening.")
            try:
                # Try simple status probe
                sock.sendall(b'{"command": "status"}\n')
                data = sock.recv(1024).decode()
                print(f"  RESPONSE: {data[:100]}")
            except:
                print("  No response to status probe.")
    except:
        print(f"  Port {port} closed.")

if __name__ == "__main__":
    for port in [3939, 9090, 9091, 9092, 41715]:
        check_port(port)
