# 4um Impactor Design

Parametric CAD design for a 4µm aerodynamic impactor using `build123d`.

## Features
- **Standard 37mm Cassette Compatibility**: Drops into standard sampling cassette bottoms.
- **Anti-Spill Cup**: "Lobster pot" design prevents powder loss if tipped.
- **Parametric Physics**: Automatically calculates nozzle diameter based on target cut-point (4µm) and flow rate (4 LPM).

## Usage
1. Install dependencies:
   ```bash
   pip install build123d ocp-vscode
   ```
2. Run the design script:
   ```bash
   python design_4um_impactor.py
   ```
3. View in **OCP CAD Viewer** (VS Code Extension).

## Output
- `impactor_4um_spoked_middle.stl`: Main body with spoke-held cup.
- `impactor_4um_nozzle_ext.stl`: Nozzle adapter.
