import logging
import ocp_vscode.config
import ocp_vscode.comms
from ocp_vscode import set_port, set_defaults, Camera, show as original_show
import ocp_vscode

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



    # Configure multiple ports
    # 3939 = IDE Extension
    # 3940 = Standalone Web Viewer
    ports = [3939, 3940]
    
    # Broadcast 'show' wrapper
    def broadcast_show(*args, **kwargs):
        for p in ports:
            try:
                set_port(p)
                # Only force camera reset on the first call or maybe both?
                # set_defaults(reset_camera=Camera.RESET) 
                original_show(*args, **kwargs)
                print(f"Sent to port {p}")
            except Exception as e:
                print(f"Failed to send to port {p}: {e}")
                
    # Direct Monkey Patch of ocp_vscode.show provided it was imported AFTER this runs?
    # No, ocp_vscode.show is a function. We can swap it in the module.
    ocp_vscode.show = broadcast_show
    # Also update the imported reference in sys.modules if needed, but mainly for the user script
    # The user script imports 'show' from 'ocp_vscode'.
    # If they imported it BEFORE calling setup_ocp, they have the old reference.
    # We should return the new show or tell them to import it from here.
    # BETTER: In design_4um_impactor, import show from viewer_setup OR just rely on the patch 
    # IF we change the import in design_4um_impactor to `import ocp_vscode` and use `ocp_vscode.show`.
    # BUT, to be least intrusive, let's just use the `setup_ocp` to return the new show function?
    
    # Actually, simpler: in design_4um_impactor.py, we can just call `viewer_setup.show`?
    # Let's just make `viewer_setup` expose a `show` that does this, and update design_4um_impactor to use it.
    
    return True

def show(*args, **kwargs):
    # This is the function exposed by this module
    # It will assume setup_ocp has been called or just loop the ports itself.
    ports = [3939, 3940]
    for p in ports:
        try:
             set_port(p)
             original_show(*args, **kwargs)
             print(f"Sent to port {p}")
        except Exception as e:
             print(f"Failed to send to port {p}: {e}")
