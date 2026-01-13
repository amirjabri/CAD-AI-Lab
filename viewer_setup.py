import logging
import ocp_vscode.config
import ocp_vscode.comms
from ocp_vscode import set_port, set_defaults, Camera, show

def setup_ocp(port=3939, log_level=logging.ERROR):
    """
    Configures OCP Viewer with a monkey patch to handle connection errors gracefully.
    Also sets the default port and camera behavior.
    """
    # Configure Logging
    logging.basicConfig(level=log_level)
    
    # --- MONKEY PATCH START ---
    # Patches send_command and status to return empty dicts instead of raising exceptions
    # when the viewer is in an inconsistent state or connection fails.
    
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

    # Set Defaults
    try:
        set_port(port)
        set_defaults(reset_camera=Camera.RESET)
        print(f"OCP Viewer configured on port {port} (patched).")
        return True
    except Exception as e:
        print(f"Failed to configure OCP Viewer: {e}")
        return False
