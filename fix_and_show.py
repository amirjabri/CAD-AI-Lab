from build123d import *
from create_hybrid_cassette import HybridCassetteAgent
import ocp_vscode.config
import ocp_vscode.comms
import json
import logging

# Monkey-patch to handle the weird string response from OCP Viewer
original_send_command = ocp_vscode.comms.send_command

def patched_send_command(*args, **kwargs):
    result = original_send_command(*args, **kwargs)
    if isinstance(result, str) and result == "{}":
        return {}
    return result

ocp_vscode.comms.send_command = patched_send_command

# Also patch status directly for extra safety
original_status = ocp_vscode.config.status
def patched_status(*args, **kwargs):
    try:
        return original_status(*args, **kwargs)
    except Exception:
        return {}
ocp_vscode.config.status = patched_status

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    from ocp_vscode import show, set_port, Camera, set_defaults

    agent = HybridCassetteAgent()
    data = agent.generate_mini_hybrid(0.8, 4.0)
    
    # Create the full assembly
    top_z = data["metadata"]["middle_height"] - 4.0
    assembly = data["base"] + data["middle"] + data["top"].move(Location((0,0, top_z)))
    
    # Create the views
    exploded_shapes = [
        data["top"].move(Location((0,0, 30))), 
        data["middle"].move(Location((0,0, 15))), 
        data["base"]
    ]
    exploded_names = ["Top_Exploded", "Middle_Exploded", "Base_Exploded"]
    exploded_colors = ["gray", "teal", "silver"]
    
    cutaway = assembly - Box(100, 50, 100, align=(Align.CENTER, Align.MIN, Align.CENTER))

    # Broadcast to all likely ports
    potential_ports = [3939, 9090, 9091, 9092, 9093, 41715]
    
    print("Broadcasting to ports:", potential_ports)
    
    for port in potential_ports:
        print(f"Trying port {port}...")
        try:
            set_port(port)
            set_defaults(reset_camera=Camera.RESET)
            
            # 1. Exploded View
            show(
                *exploded_shapes,
                names=exploded_names,
                colors=exploded_colors,
                position=(40, 0, 0)
            )
            
            # 2. Cross-Section View
            show(
                cutaway,
                names=["Hybrid_Cutaway"],
                colors=["teal"],
                position=(-40, 0, 0)
            )
            print(f"  SUCCESS sending to {port}")
        except Exception as e:
            print(f"  Failed on {port}: {e}")
            
    print("Broadcast complete.")
