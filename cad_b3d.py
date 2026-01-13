from build123d import *
from ocp_vscode import show, set_port, set_defaults, Camera
import math

# --- 1. CONFIGURATION (The Science) ---
# Adjust these variables to change the physics of the device
TARGET_CUT_POINT_MICRONS = 5.0  # Particles larger than this will hit the plate
FLOW_RATE_LPM = 4.0             # Pump flow rate (Liters Per Minute)
NOZZLE_COUNT = 1                # Single Nozzle Design

# Geometric Ratios (Marple & Willeke)
S_W_RATIO = 1.5                 # Jet-to-Plate Distance (Standard: 1.0 - 5.0)
T_W_RATIO = 1.0                 # Nozzle Throat Length (Standard: ~1.0)

# Mechanical dimensions
BODY_DIAMETER = 37.0            # Matches standard 37mm filter cassettes
WALL_THICKNESS = 2.0
CONNECT_HEIGHT = 10.0           # Height of the hose barb

# --- 2. PHYSICS ENGINE (Stokes Law) ---
# We calculate the exact nozzle diameter required to achieve the cut-point
STK_50 = 0.24                   # Stokes number for 50% efficiency (Round Jet)
RHO_P = 1000                    # Particle density (kg/m^3)
AIR_VISCOSITY = 1.81e-5         # Pa*s
Q_m3s = (FLOW_RATE_LPM / 1000) / 60
d50_m = TARGET_CUT_POINT_MICRONS * 1e-6

# Formula derived from Marple/Willeke for Round Jets
numerator = 4 * RHO_P * (d50_m**2) * 1.0 * Q_m3s
denominator = 9 * math.pi * AIR_VISCOSITY * STK_50 * NOZZLE_COUNT
nozzle_diam_m = (numerator / denominator) ** (1/3)
NOZZLE_DIAM_MM = nozzle_diam_m * 1000

# Reynolds Number Check
# Re = (Rho_air * U * W) / Viscosity
# U = Jet Velocity
# W = Nozzle Diameter
jet_area_m2 = NOZZLE_COUNT * math.pi * (nozzle_diam_m / 2)**2
jet_velocity = Q_m3s / jet_area_m2
rho_air = 1.2 # kg/m3 (approx at STP)
reynolds_number = (rho_air * jet_velocity * nozzle_diam_m) / AIR_VISCOSITY

print(f"--- PHYSICS Calculated ---")
print(f"To remove >{TARGET_CUT_POINT_MICRONS}um particles at {FLOW_RATE_LPM} LPM:")
print(f"Drill {NOZZLE_COUNT} nozzles with diameter: {NOZZLE_DIAM_MM:.3f} mm")
print(f"Jet Velocity: {jet_velocity:.1f} m/s")
print(f"Reynolds Number: {reynolds_number:.0f} (Target: 500-3000)")

if not (500 <= reynolds_number <= 3000):
   print(f"WARNING: Reynolds number {reynolds_number:.0f} may be outside ideal range for sharp cutoff.")
else:
   print("PHYSICS CHECK: Reynolds number is valid.")

# --- 3. GEOMETRY ENGINE (The CAD) ---

# Part 1: Nozzle Adapter (To be glued to Cassette Top)
# ----------------------------------------------------
# Simple disk with the precision nozzle hole.
ADAPTER_OD = 15.0 # Diameter of the glue-on disk
# Enforce T/W Ratio for Throat Length
ADAPTER_THICKNESS = NOZZLE_DIAM_MM * T_W_RATIO # T = W * 1.0
print(f"Nozzle Throat Length (T): {ADAPTER_THICKNESS:.3f} mm (T/W = {T_W_RATIO})")

with BuildPart() as nozzle_adapter:
    Cylinder(radius=ADAPTER_OD/2, height=ADAPTER_THICKNESS)
    # Drill the nozzle
    with BuildSketch(Plane.XY):
        Circle(radius=NOZZLE_DIAM_MM/2)
    extrude(amount=ADAPTER_THICKNESS, mode=Mode.SUBTRACT)

# Part 2: Middle Section (Ring + Cup)
# ----------------------------------------------------
# Fits between top and bottom cassette sections.
# User Specs:
# - Bottom: Snug fit INTO standard bottom (Male Boss). OD = 37.4 mm.
# - Top: Snug fit TO standard top (Female Socket). ID = 37.2 mm.

RING_OD = 42.0          # Main Body Diameter (Generic outer shell)
RING_ID_FLOW = 34.0     # Inner Flow Path (Clearance for airflow around cup)
FIT_BOSS_OD = 37.4      # Male Boss at Bottom
FIT_SOCKET_ID = 37.2    # Female Socket at Top

SECTION_HEIGHT = 20.0   # Main Body Height (Shoulder-to-Shoulder)
INTERFACE_HEIGHT = 5.0  # Height of the male boss and depth of top socket

# Enforce S/W Ratio for Jet-to-Plate
S_distance = NOZZLE_DIAM_MM * S_W_RATIO
print(f"Jet-to-Plate Distance (S): {S_distance:.3f} mm (S/W = {S_W_RATIO})")

# Calculate Cup Position
# To maintain physics S_distance, we need to estimate where the nozzle sits.
# If Cassette Top inserts into the Top Socket (Depth 5mm), the Nozzle (glued to Cassette Top) 
# is likely somewhere near the top of the Middle Section or slightly inside.
# Let's assume the Nozzle exit plane aligns with the BOTTOM of the Top Socket (Z = SECTION_HEIGHT - INTERFACE_HEIGHT).
# i.e., The Cassette Top fully seats 5mm deep, and the nozzle is flush with that.
NOZZLE_EXIT_Z = SECTION_HEIGHT - INTERFACE_HEIGHT
CUP_FLOOR_Z = NOZZLE_EXIT_Z - S_distance

with BuildPart() as middle_section:
    # 1. Main Body Cylinder (The core ring)
    # Z = 0 to SECTION_HEIGHT
    with BuildSketch(Plane.XY):
        Circle(radius=RING_OD/2)
        Circle(radius=RING_ID_FLOW/2, mode=Mode.SUBTRACT)
    extrude(amount=SECTION_HEIGHT)

    # 2. Male Boss (Bottom)
    # Z = -INTERFACE_HEIGHT to 0
    # Fits INTO cassette bottom.
    with BuildSketch(Plane.XY.offset(-INTERFACE_HEIGHT)):
        Circle(radius=FIT_BOSS_OD/2)
        Circle(radius=RING_ID_FLOW/2, mode=Mode.SUBTRACT) # Continuous flow path
    extrude(amount=INTERFACE_HEIGHT) # Extrude up to Z=0? Yes. (Wait, extrude from -5 up 5 reaches 0).
    
    # 3. Female Socket (Top)
    # Cut into the Main Body from Z=SECTION_HEIGHT down.
    # ID = 37.2mm
    with BuildSketch(Plane.XY.offset(SECTION_HEIGHT)):
        Circle(radius=FIT_SOCKET_ID/2)
    extrude(amount=-INTERFACE_HEIGHT, mode=Mode.SUBTRACT)
    # Note: This broadens the top ID from 34.0 to 37.2. Correct.
    
    # 4. The Impaction Cup
    # Position: Floor at CUP_FLOOR_Z. 
    # Must be supported by struts.
    # Check if CUP_FLOOR_Z is valid (inside the part).
    # S = 3.78 * 1.5 = 5.6 mm.
    # Nozzle Exit = 20 - 5 = 15 mm. (Relative to Z=0 at bottom of shoulder)
    # Cup Floor = 15 - 5.6 = 9.4 mm.
    # This is well inside the 20mm body. Good.
    
    cup_radius = NOZZLE_DIAM_MM * 3
    cup_rim_height = 3.0
    
    # Cup Floor
    with BuildSketch(Plane.XY.offset(CUP_FLOOR_Z)): # Floor surface
        Circle(radius=cup_radius)
    extrude(amount=-2, mode=Mode.ADD) # Extrude DOWN 2mm for thickness
    
    # Cup Rim
    with BuildSketch(Plane.XY.offset(CUP_FLOOR_Z)):
        Circle(radius=cup_radius)
        Circle(radius=cup_radius - 1, mode=Mode.SUBTRACT)
    extrude(amount=cup_rim_height, mode=Mode.ADD)
    
    # 5. Support Struts (Spider Legs)
    # Connect Cup to Wall.
    # Strut Z level: below rim, maybe aligned with floor thickness.
    strut_z_top = CUP_FLOOR_Z
    strut_thickness = 2.0 # Vertical dimension
    
    with BuildSketch(Plane.XY.offset(strut_z_top)) as strut_sk:
        with PolarLocations(radius=(RING_ID_FLOW/4 + cup_radius/2), count=3): # Approximate center of strut
            # Span from Cup (cup_radius) to Wall (RING_ID_FLOW/2).
            # Note: The wall at this Z height (9.4mm) is RING_ID_FLOW (34mm).
            # Span = 34/2 - cup_radius.
            span = (RING_ID_FLOW/2) - cup_radius + 2 # +2 overlap
            Rectangle(width=span, height=2.0) # 2mm wide struts
    extrude(amount=-strut_thickness, mode=Mode.ADD) # Extrude down


# --- 4. RENDER & EXPORT (Main Execution) ---
if __name__ == "__main__":
    # Explicitly set port to match the running backend (3939)
    try:
        from ocp_vscode import set_port
        set_port(3939)
    except ImportError:
        pass

    set_defaults(reset_camera=Camera.RESET)

    # Visual Assembly
    # Move Middle Section down so its top aligns with Nozzle Adapter bottom
    # Nozzle Adapter: Z=0 to 2 (Height 2, centered? No, Cylinder default is centered on Z=0 usually? 
    # Build123d Cylinder centered=True by default. Let's fix positions.)
    # nozzle_adapter (Cylinder, height=2) -> Z from -1 to 1.
    # Let's move it so bottom is at Z=0.
    nozzle_vis = nozzle_adapter.part.move(Location((0,0, ADAPTER_THICKNESS/2)))

    # middle_section
    # We built it from Z = -RING_HEIGHT to 0. Use as is.

    # show(
    #     nozzle_vis, 
    #     names=["Nozzle_Adapter"], 
    #     colors=["red"], 
    #     position=(0,0,5) # Exploded view: Lift nozzle up 5mm
    # )

    try:
        show(
            middle_section.part, 
            names=["Middle_Section"], 
            colors=["teal"],
            # alpha=0.8 # Removed: not supported
        )

        # Cross Section View of Middle Ring
        show(
            middle_section.part - Box(100, 50, 100, align=(Align.CENTER, Align.MIN, Align.CENTER)),
            names=["Middle_Cutaway"],
            colors=["teal"],
            position=(50, 0, 0)
        )
    except Exception as e:
        print(f"Viewer not available ({e}). Skipping display.")

    # Execute Export
    # Change the description string below to name your iteration
    # e.g. "single_nozzle_snug_fit"
    export_design(description="single_nozzle_snug_fit")
