
import cad_b3d
from build123d import BuildPart
from ocp_vscode import show, set_port, Camera, set_defaults

def main():
    print("\n--- DESIGN PART VIEWER ---")
    
    # Inspect cad_b3d module for BuildPart objects
    available_parts = {}
    for name, obj in vars(cad_b3d).items():
        if isinstance(obj, BuildPart):
            available_parts[name] = obj
            
    if not available_parts:
        print("No design parts found in cad_b3d.py")
        return

    part_names = list(available_parts.keys())
    part_names.sort()

    for i, name in enumerate(part_names):
        print(f"[{i+1}] {name}")
    print(f"[{len(part_names)+1}] ALL PARTS")
    print("--------------------------")
    
    try:
        choice = input("Select part to view (Number): ")
        idx = int(choice) - 1
    except ValueError:
        print("Invalid input.")
        return

    # Setup Viewer
    try:
        set_port(3939)
    except ImportError:
        pass
    set_defaults(reset_camera=Camera.RESET)

    try:
        if idx == len(part_names):
            # Show ALL
            shapes = [available_parts[n].part for n in part_names]
            colors = ["red", "teal", "orange", "blue"][:len(shapes)]
            print(f"Viewing ALL: {', '.join(part_names)}")
            show(*shapes, names=part_names, colors=colors)
            
        elif 0 <= idx < len(part_names):
            # Show Specific
            name = part_names[idx]
            part = available_parts[name]
            print(f"Viewing: {name}")
            show(part.part, names=[name], colors=["teal"])
        else:
            print("Invalid selection.")
    except Exception as e:
        print(f"\nError: Could not connect to OCP Viewer ({e}).")
        print("Please ensure the OCP CAD Viewer extension is active in VS Code.")

if __name__ == "__main__":
    main()
