import cadquery as cq
from ocp_vscode import show, set_port, set_defaults
import math

# --- 1. CONFIGURATION (The Science) ---
# Adjust these variables to change the physics of the device
TARGET_CUT_POINT_MICRONS = 5.0  # Particles larger than this will hit the plate
FLOW_RATE_LPM = 4.0             # Pump flow rate (Liters Per Minute)
NOZZLE_COUNT = 3                # Number of acceleration jets

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

# Formula derived from Marple/Willeke for Round Jets:
# D_jet = [ (4 * Rho * d50^2 * C * Q) / (9 * pi * Visc * Stk * N) ] ^ (1/3)
# Note: C (Cunningham Slip) ~ 1.0 for >1um particles at STP.
numerator = 4 * RHO_P * (d50_m**2) * 1.0 * Q_m3s
denominator = 9 * math.pi * AIR_VISCOSITY * STK_50 * NOZZLE_COUNT
nozzle_diam_m = (numerator / denominator) ** (1/3)
NOZZLE_DIAM_MM = nozzle_diam_m * 1000

print(f"--- PHYSICS CALCULATED ---")
print(f"To remove >{TARGET_CUT_POINT_MICRONS}um particles at {FLOW_RATE_LPM} LPM:")
print(f"Drill {NOZZLE_COUNT} nozzles with diameter: {NOZZLE_DIAM_MM:.3f} mm")
print(f"Jet Velocity: {(Q_m3s / (NOZZLE_COUNT * math.pi * (nozzle_diam_m/2)**2)):.1f} m/s")

# --- 3. GEOMETRY ENGINE (The CAD) ---

# A. The Inlet Cap (Contains the Acceleration Nozzles)
# ---------------------------------------------------
inlet_cap = (
    cq.Workplane("XY")
    .circle(BODY_DIAMETER/2 + WALL_THICKNESS).extrude(5) # The Flange
    .faces(">Z").workplane().circle(BODY_DIAMETER/2).extrude(10) # The Inlet Tube
    .faces(">Z").hole(BODY_DIAMETER/2 - 2) # Hollow inlet
)

# Drill the precision nozzles in the bottom face of the cap
# We position them in a circle pattern
nozzle_radius = BODY_DIAMETER/4
for i in range(NOZZLE_COUNT):
    angle = i * (360.0 / NOZZLE_COUNT)
    x = nozzle_radius * math.cos(math.radians(angle))
    y = nozzle_radius * math.sin(math.radians(angle))
    
    inlet_cap = (
        inlet_cap.faces("<Z").workplane()
        .moveTo(x, y)
        .hole(NOZZLE_DIAM_MM)
    )

# B. The Impaction Plate Body (The "Cup")
# ---------------------------------------------------
# This piece holds the impaction surface.
# The distance from Nozzle to Plate (S) should be 1.0 to 1.5 x Nozzle Diameter
S_distance = NOZZLE_DIAM_MM * 1.5

impaction_body = (
    cq.Workplane("XY")
    .workplane(offset = -10 - S_distance) # Shift down to create the gap
    .circle(BODY_DIAMETER/2 + WALL_THICKNESS).extrude(10 + S_distance)
    .faces(">Z").hole(BODY_DIAMETER) # Hollow out the chamber
)

# Create the "Pedestal" (Impaction Plate) in the center
# Air hits this, turns, and flows down the sides.
pedestal = (
    cq.Workplane("XY")
    .workplane(offset = -10 - S_distance + 2) # Floor thickness
    .circle(BODY_DIAMETER/2 - 4.0) # Gap of 4mm around edge for airflow
    .extrude(8 + S_distance - 2)
)

impaction_assembly = impaction_body.union(pedestal)

# C. Outlet Cone (Connects to Filter Cassette)
# ---------------------------------------------------
outlet_cone = (
    cq.Workplane("XY")
    .workplane(offset = -10 - S_distance)
    .circle(BODY_DIAMETER/2 + WALL_THICKNESS).extrude(10)
    .faces("<Z").workplane()
    .hole(6.0) # 6mm hole for tubing
)

final_assembly = inlet_cap.union(impaction_assembly).union(outlet_cone)

# Cut a cross-section view so you can see inside
half_view = final_assembly.faces(">Y").workplane().rect(100, 100).cutThruAll()

# --- 4. RENDER ---
set_defaults(reset_camera=True)
show(final_assembly, names=["Full_Impactor"], colors=["alpha_grey"], alpha=0.3)
show(half_view, names=["Cross_Section"], colors=["teal"])
show(inlet_cap, names=["Nozzle_Plate"], position=(50,0,0), colors=["red"])

# --- 5. EXPORT ---
# Uncomment to generate STL for printing
# cq.exporters.export(inlet_cap, 'impactor_nozzle_plate.stl')
# cq.exporters.export(impaction_assembly, 'impactor_body.stl')