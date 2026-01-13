import os
import logging
from build123d import *
import ocp_vscode.config
import ocp_vscode.comms

# --- MONKEY PATCH START ---
original_send_command = ocp_vscode.comms.send_command
def patched_send_command(*args, **kwargs):
    try:
        result = original_send_command(*args, **kwargs)
        if isinstance(result, str) and result.strip() == "{}":
            return {}
        return result
    except Exception:
        return {}

ocp_vscode.comms.send_command = patched_send_command

original_status = ocp_vscode.config.status
def patched_status(*args, **kwargs):
    try:
        return original_status(*args, **kwargs)
    except Exception:
        return {}
ocp_vscode.config.status = patched_status
# --- MONKEY PATCH END ---

def show_latest():
    base_dir = "iterations"
    if not os.path.exists(base_dir):
        print(f"No 'iterations' folder found.")
        return

    folders = [d for d in os.listdir(base_dir) if os.path.isdir(os.path.join(base_dir, d)) and d.startswith("v")]
    if not folders:
        print("No designs found.")
        return
    
    folders.sort()
    latest_folder = folders[-1]
    full_path = os.path.join(base_dir, latest_folder)
    print(f"Loading latest iteration: {latest_folder}")

    from ocp_vscode import show, set_port, Camera, set_defaults
    set_port(3939)
    set_defaults(reset_camera=Camera.RESET)

    stls = [f for f in os.listdir(full_path) if f.lower().endswith(".stl")]
    shapes = []
    names = []
    
    for stl_file in stls:
        stl_path = os.path.join(full_path, stl_file)
        try:
            shape = import_stl(stl_path)
            shapes.append(shape)
            names.append(stl_file)
        except Exception as e:
            print(f"Failed to load {stl_file}: {e}")

    if shapes:
        print(f"Sending {len(shapes)} shapes to OCP Viewer on port 3939...")
        # Explode lid if present
        for i, name in enumerate(names):
            if "lid" in name.lower():
                shapes[i] = shapes[i].translate((0,0,60))
                names[i] = name + " (Exploded 60mm)"
        
        show(*shapes, names=names)
        print("Success!")
    else:
        print("No STLs found in the latest iteration.")

if __name__ == "__main__":
    logging.basicConfig(level=logging.ERROR)
    show_latest()
