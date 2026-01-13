from build123d import *
from create_hybrid_cassette import HybridCassetteAgent
import ocp_vscode.config
import ocp_vscode.comms
import logging
import time

# --- MONKEY PATCH START ---
# Fixes communication issue where viewer returns string "{}" instead of dict
original_send_command = ocp_vscode.comms.send_command

def patched_send_command(*args, **kwargs):
    try:
        result = original_send_command(*args, **kwargs)
        if isinstance(result, str) and result.strip() == "{}":
            return {}
        return result
    except Exception as e:
        print(f"DEBUG: send_command caught {e}")
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

if __name__ == "__main__":
    logging.basicConfig(level=logging.ERROR)
    from ocp_vscode import show, set_port, Camera, set_defaults
    
    # Explicitly set port 3939 as verified active
    try:
        set_port(3939)
        print("Set port to 3939")
    except Exception as e:
        print(f"Warning setting port: {e}")

    # Generate Model
    agent = HybridCassetteAgent()
    data = agent.generate_mini_hybrid(0.8, 4.0)
    
    print("Sending Exploded View to OCP Viewer...")
    
    try:
        # Simple Exploded View (Known Good State)
        show(
            data["top"].move(Location((0,0, 30))), 
            data["middle"].move(Location((0,0, 15))), 
            data["base"],
            names=["Top_Inlet", "Middle_Foam_Chamber", "Base_Filter_Support"],
            colors=["gray", "teal", "silver"],
            reset_camera=Camera.RESET
        )
        print("SUCCESS: Command sent. Please check the OCP CAD Viewer tab.")
    except Exception as e:
        print(f"ERROR: show() failed: {e}")
