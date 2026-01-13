import os
import sys

def load_latest_source():
    base_dir = "iterations"
    if not os.path.exists(base_dir):
        print("No iterations directory found.")
        return

    # Find latest folder
    folders = [d for d in os.listdir(base_dir) if os.path.isdir(os.path.join(base_dir, d)) and d.startswith("v")]
    if not folders:
        print("No designs found.")
        return
    
    folders.sort()
    latest_folder = folders[-1]
    full_path = os.path.join(base_dir, latest_folder)
    print(f"Found latest iteration: {latest_folder}")

    # Find python snapshot
    py_files = [f for f in os.listdir(full_path) if f.endswith(".py") and "script_snapshot" in f]
    if not py_files:
        print("No script snapshot found in latest iteration.")
        return

    target_file = os.path.join(full_path, py_files[0])
    print(f"Loading script: {target_file}")

    with open(target_file, "r") as f:
        lines = f.readlines()

    new_lines = []
    # Add header
    new_lines.append("import ocp_vscode\n")
    new_lines.append("ocp_vscode.set_port(3939)\n")

    for line in lines:
        stripped = line.strip()
        # Check if it's the specific call to export_batch we want to disable
        # usually `export_batch(body_p, lid_p)`
        # Make sure it's not the definition `def export_batch`
        if stripped.startswith("export_batch") and not stripped.startswith("def "):
            new_lines.append(f"# {line}")
        else:
            new_lines.append(line)

    # Write to a temporary runner
    runner_path = "temp_viewer_runner.py"
    with open(runner_path, "w") as f:
        f.writelines(new_lines)

    print(f"Running temporary script: {runner_path}")
    
    # We execute it as a subprocess to ensure clean state
    import subprocess
    subprocess.run([sys.executable, runner_path])

if __name__ == "__main__":
    load_latest_source()
