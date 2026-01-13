import os
from build123d import *
from ocp_vscode import show, Camera, set_defaults

def browse():
    base_dir = "iterations"
    if not os.path.exists(base_dir):
        print(f"No 'iterations' folder found at {os.getcwd()}")
        return

    # Find version folders
    folders = []
    for d in os.listdir(base_dir):
        path = os.path.join(base_dir, d)
        if os.path.isdir(path) and d.startswith("v"):
            folders.append(d)
    
    folders.sort() # v01, v02...
    
    if not folders:
        print("No designs found.")
        return

    print("\n--- SAVED DESIGNS ---")
    for i, folder in enumerate(folders):
        print(f"[{i+1}] {folder}")
    print("---------------------")
    
    try:
        choice = input("Select design to view (Number): ")
        idx = int(choice) - 1
        selected_folder = folders[idx]
    except (ValueError, IndexError):
        print("Invalid selection.")
        return
    
    full_path = os.path.join(base_dir, selected_folder)
    print(f"\nLoading: {selected_folder}...")
    
    # Find STLs in that folder
    stls = [f for f in os.listdir(full_path) if f.lower().endswith(".stl")]
    
    shapes_to_show = []
    names = []
    colors = []
    
    current_color_idx = 0
    palette = ["red", "teal", "orange", "blue", "yellow"]
    
    for stl_file in stls:
        stl_path = os.path.join(full_path, stl_file)
        try:
            # Import using build123d's Mesher/Importer
            # Note: direct import_stl usually returns a Mesh object
            # We need to ensure we have the right import function
            # build123d > 0.4 has import_stl in global or importers
            print(f"  - {stl_file}")
            
            # Using Mesher to import? Or simple import_stl?
            # Let's try the direct import.
            imported_shape = import_stl(stl_path)
            
            print(f"    -> Loaded object type: {type(imported_shape)}")
            
            # Check validity and attempt repair if needed
            if hasattr(imported_shape, "is_valid") and not imported_shape.is_valid:
                print("    -> Invalid geometry detected. Attempting repair...")
                try:
                    # Try fix() if available (OCP/Topological fix)
                    if hasattr(imported_shape, "fix"):
                        imported_shape = imported_shape.fix()
                        print(f"    -> Repair complete. Valid: {imported_shape.is_valid}")
                except Exception as e:
                    print(f"    -> Repair failed: {e}")

            if hasattr(imported_shape, "bounding_box"):
                bbox = imported_shape.bounding_box()
                print(f"    -> BBox: {bbox}")
            
            shapes_to_show.append(imported_shape)
            names.append(stl_file)
            colors.append(palette[current_color_idx % len(palette)])
            current_color_idx += 1
            
        except Exception as e:
            print(f"Failed to load {stl_file}: {e}")

    if shapes_to_show:
        print("Displaying in OCP Viewer...")
        # Explicitly set port to match the running backend (3939)
        # This fixes 'Port could not be cast to integer' errors
        try:
             from ocp_vscode import set_port
             set_port(3939)
        except ImportError:
             pass

        set_defaults(reset_camera=Camera.RESET)
        # Unpack the list with * so ocp-vscode sees multiple objects
        show(*shapes_to_show, names=names, colors=colors)
    else:
        print("No STL files found in this version folder.")

if __name__ == "__main__":
    browse()
