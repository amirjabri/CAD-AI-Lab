from ocp_vscode import set_port, status
import logging

logging.basicConfig(level=logging.DEBUG)

def check():
    try:
        set_port(3939)
        print("Set port to 3939")
        s = status()
        print(f"Status: {s}")
    except Exception as e:
        print(f"Caught Error: {e}")

if __name__ == "__main__":
    check()
