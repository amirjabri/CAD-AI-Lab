import socket
import json

def check_ocp_listener(port=3939):
    print(f"Checking for OCP Viewer on localhost:{port}...")
    try:
        with socket.create_connection(("localhost", port), timeout=2) as sock:
            print(f"SUCCESS: Something is listening on port {port}.")
            
            # Try to send a status command
            status_cmd = {"command": "status", "version": "1.0"}
            sock.sendall(json.dumps(status_cmd).encode())
            
            data = sock.recv(4096).decode()
            print(f"RECEIVED: {data}")
            
            if "status" in data.lower():
                print("CONFIRMED: OCP Viewer is responding correctly.")
            else:
                print("WARNING: Received unexpected response. Is this the OCP Viewer?")
    except ConnectionRefusedError:
        print(f"FAILED: Connection refused on port {port}. The viewer is likely not running or listening on a different port.")
    except socket.timeout:
        print(f"FAILED: Connection timed out on port {port}.")
    except Exception as e:
        print(f"ERROR: {e}")

if __name__ == "__main__":
    check_ocp_listener(3939)
