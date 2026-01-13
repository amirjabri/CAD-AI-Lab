from build123d import *
from ocp_vscode import show, show_object, set_port

# Ensure we're talking to the right port (default 3939)
set_port(3939)

print("Creating a simple box...")
b = Box(10, 20, 30)

print("Sending to OCP Viewer...")
try:
    show(b, "test_box")
    print("Successfully sent 'test_box' to viewer.")
except Exception as e:
    print(f"Error sending to viewer: {e}")
