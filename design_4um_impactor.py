from build123d import *
from viewer_setup import setup_ocp, show
import math


# --- 1. CONFIGURATION ---
TARGET_CUT_POINT_MICRONS = 4.0
FLOW_RATE_LPM = 4.0
NOZZLE_COUNT = 1

# Mechanical Mating (Standard 37mm Cassette)
FIT_BOSS_OD = 37.4      # Fits INTO standard bottom
FIT_SOCKET_ID = 37.2    # Receives standard top
FIT_SOCKET_DEPTH = 5.0
RING_OD = 42.0 
WALL = 2.0
SECTION_HEIGHT = 20.0
INTERFACE_HEIGHT = 5.0

# --- 2. PHYSICS ---
STK_50 = 0.24 
RHO_P = 1000
AIR_VISCOSITY = 1.81e-5
Q_m3s = (FLOW_RATE_LPM / 1000) / 60
d50_m = TARGET_CUT_POINT_MICRONS * 1e-6
numerator = 4 * RHO_P * (d50_m**2) * 1.0 * Q_m3s
denominator = 9 * math.pi * AIR_VISCOSITY * STK_50 * NOZZLE_COUNT
nozzle_diam_m = (numerator / denominator) ** (1/3)
NOZZLE_DIAM_MM = nozzle_diam_m * 1000
S_DIST = NOZZLE_DIAM_MM * 1.5

print(f"--- PHYSICS ---")
print(f"Nozzle Diameter: {NOZZLE_DIAM_MM:.3f} mm")
print(f"Jet-to-Plate (S): {S_DIST:.3f} mm")

# --- 3. GEOMETRY ---

# Design Logic:
# The Middle Section has a Cup held by 3 spokes.
# The Cup should be DEEP so the nozzle extends INTO it.
# Nozzle Exit Z position determines everything.

# Let's define the Middle Section Coordinate System:
# Z=0 is the bottom of the main ring body (Top of bottom boss).
# Z=SECTION_HEIGHT is the top of the ring.
# Top Socket Floor is at Z = SECTION_HEIGHT - INTERFACE_HEIGHT = 15.0mm.
# The Standard Top Cassette rests on this floor (Z=15).

# The Nozzle Adapter is glued to the Standard Top.
# So the nozzle starts at Z=15 and extends DOWN.
# How far down?
# We want it to go deep into the cup.
# Let's say we place the Cup Floor at Z = 5.0mm.
CUP_FLOOR_Z = 5.0
CUP_RIM_HEIGHT = 8.0 # Deep cup
CUP_RIM_Z = CUP_FLOOR_Z + CUP_RIM_HEIGHT # Z=13.0

# Nozzle Exit must be at Cup Floor + S + PlateThickness? No, S is distance to surface.
# Nozzle Exit Z = CUP_FLOOR_Z + S_DIST.
# S ~ 4.9mm.
# Nozzle Exit Z = 5.0 + 4.9 = 9.9mm.
NOZZLE_EXIT_Z = CUP_FLOOR_Z + S_DIST

# Anti-Spill Guard Dimensions
GUARD_ID = 9.0 # Inner Diameter of the spill guard lip (Nozzle OD ~5.3mm)
GUARD_HEIGHT = 2.0 # Height of the conical section
GUARD_Z_BOTTOM = CUP_RIM_Z - GUARD_HEIGHT

# Check overlapping:
# Cup Rim is at 13.0mm.
# Nozzle Exit is at 9.9mm.
# The Nozzle is INSIDE the cup vertically (9.9 < 13.0). This creates the "dead area".
# Constraint: Nozzle OD must be smaller than Cup ID.
NOZZLE_WALL_THICK = 1.0
NOZZLE_OUTER_DIAM = NOZZLE_DIAM_MM + (2 * NOZZLE_WALL_THICK) # ~5.3mm
CUP_INNER_DIAM = 20.0 # Plenty of clearance (20 > 5.3)

printValues = f"""
Z Levels:
Top Socket Floor: {SECTION_HEIGHT - INTERFACE_HEIGHT}
Cup Rim: {CUP_RIM_Z}
Nozzle Exit: {NOZZLE_EXIT_Z}
Cup Floor: {CUP_FLOOR_Z}
"""
print(printValues)

# A. Nozzle Insert (Extended Chimney)
# -----------------------------------
# Base Disk: OD 15mm, Thickness 2mm.
# Chimney: OD ~5.3mm, ID ~3.3mm.
# Length: From Z=15 down to Z=9.9. Plus the 2mm base thickness?
# If glued to Z=15 surface, the base is ABOVE Z=15? Or Recessed?
# Typically "glued onto top cassette lid" means inside the outlet hole? 
# Or on the face? Let's assume on the face that mates with our ring.
# BUT our ring has a Socket Floor at Z=15.
# If the user glues it to their lid, and their lid sits on Z=15...
# Then the nozzle starts at Z=15 and goes down.
# Length = 15.0 - NOZZLE_EXIT_Z = 15.0 - 9.9 = 5.1mm extension.
# Plus the base thickness of the adapter itself (embedded in the lid or sitting flush?).
# Let's create a "Top Hat" shape. Brims sits on Z=15? No, that would block the lid seating.
# The Top Cassette has a hole. The adapter likely fits INTO the top cassette hole or sits on the face.
# Safer assumption: The adapter IS the nozzle extension. It has a flange.
# Let's make the flange thin (1mm) and expect it to sit between Lid and Ring (shim)?
# No, user said "fit into standard...". The ring receives the lid.
# Best approach: The nozzle adapter inserts into the TOP of our ring (Socket)?
# User said "glue a nozzle onto the top cassette lid".
# So when they put the lid on, the nozzle sticks down.
# So we just model the nozzle part that extends FROM Z=15 DOWN to Z=9.9.
CHIMNEY_LEN = (SECTION_HEIGHT - INTERFACE_HEIGHT) - NOZZLE_EXIT_Z # 5.1mm
BASE_THICK = 2.0 
# We model it inverted for printing usually, but here orientation matches assembly.

with BuildPart() as nozzle_insert:
    # 1. Base (The part that glues to the lid)
    # Modeled at Z=15 going UP (just for visual context), or simply Z=0 to 2?
    # Let's model it at origin for export.
    Cylinder(radius=15.0/2, height=BASE_THICK)
    # 2. Chimney (Extending down)
    with BuildSketch(Plane.XY):
        Circle(radius=NOZZLE_OUTER_DIAM/2)
    extrude(amount=CHIMNEY_LEN) # Extrudes UP in this local view?
    # Wait, let's make it logical for printing.
    # Flat base on bed. Chimney going up.
    # Total Height = Base + Chimney.
    # Bore hole through all.
    with BuildSketch(Plane.XY):
        Circle(radius=NOZZLE_DIAM_MM/2)
    extrude(amount=BASE_THICK + CHIMNEY_LEN + 1.0, mode=Mode.SUBTRACT)

# B. Middle Section (Ring + Spokes + Cup)
# ---------------------------------------
with BuildPart() as middle_section:
    # 1. Main Housing Ring
    with BuildSketch(Plane.XY):
        Circle(radius=RING_OD/2)
        Circle(radius=RING_OD/2 - WALL, mode=Mode.SUBTRACT)
    extrude(amount=SECTION_HEIGHT)
    
    # 2. Bottom Boss (Interface)
    with BuildSketch(Plane.XY.offset(-INTERFACE_HEIGHT)):
        Circle(radius=FIT_BOSS_OD/2)
        Circle(radius=FIT_BOSS_OD/2 - WALL, mode=Mode.SUBTRACT)
    extrude(amount=INTERFACE_HEIGHT)
    
    # 3. Top Socket (Cutout for Lid)
    with BuildSketch(Plane.XY.offset(SECTION_HEIGHT)):
        Circle(radius=FIT_SOCKET_ID/2)
    extrude(amount=-INTERFACE_HEIGHT, mode=Mode.SUBTRACT)
    
    # 4. The Cup
    # Positioned at Z=CUP_FLOOR_Z
    with BuildSketch(Plane.XY.offset(CUP_FLOOR_Z)):
        Circle(radius=CUP_INNER_DIAM/2 + 1.0) # Wall thickness 1mm
    extrude(amount=CUP_RIM_HEIGHT) # Wall up
    
    with BuildSketch(Plane.XY.offset(CUP_FLOOR_Z)):
        Circle(radius=CUP_INNER_DIAM/2)
    extrude(amount=CUP_RIM_HEIGHT, mode=Mode.SUBTRACT) # Hollow
    
    # 6. Anti-Spill Guard (Conical Lip at Rim)
    # Reduces Opening from 20mm to 9mm
    # Cone: Top ID=9mm (Z=13), Bottom ID=20mm (Z=11)
    with BuildSketch(Plane.XY.offset(GUARD_Z_BOTTOM)):
         Circle(radius=CUP_INNER_DIAM/2)
         Circle(radius=GUARD_ID/2, mode=Mode.SUBTRACT)
    # Extrude tapered up to close it? No, we want a cone wall.
    # Let's simple Loft two profiles.
    # Profile 1 at Z=11: ID 20 (Matches Cup Wall)
    # Profile 2 at Z=13: ID 9 (Constriction)
    # We add this material inside the cup void?
    # No, we already hollowed the cup.
    # We need to ADD material back.
    # But wait, we hollowed the full cylinder.
    # Let's create the spill guard as a separate solid and ADD it.
    
    # Solid Ring with Conical inner face
    # Outer diam = Cup Outer (Inner + Wall*2) or Just Cup Inner?
    # Let's stick to Cup Inner to avoid making wall thicker outside.
    # So we are filling the inside from R=10 down to R=4.5.
    
    with BuildPart() as guard:
        with BuildSketch(Plane.XY.offset(GUARD_Z_BOTTOM)):
            Circle(radius=CUP_INNER_DIAM/2) # OD 20
            Circle(radius=CUP_INNER_DIAM/2 - 0.1, mode=Mode.SUBTRACT) # Thin ring at bottom
        with BuildSketch(Plane.XY.offset(CUP_RIM_Z)):
            Circle(radius=CUP_INNER_DIAM/2) # OD 20
            Circle(radius=GUARD_ID/2, mode=Mode.SUBTRACT) # ID 9
        loft()
    add(guard.part)
    
    # Cup Floor
    with BuildSketch(Plane.XY.offset(CUP_FLOOR_Z)):
        Circle(radius=CUP_INNER_DIAM/2 + 1.0)
    extrude(amount=-1.5) # Floor thickness down
    
    # 5. Spokes (Connecting Cup to Housing)
    # Where to attach? At the Rim (Z=13) or Body?
    # Rim is close to air path. Body is better.
    # Let's attach at Z = CUP_FLOOR_Z + 4.0 (Mid-cup)
    SPOKE_Z = CUP_FLOOR_Z + 4.0

    # Calculate Gap
    # Ring Inner Radius = RING_OD/2 - WALL = 21 - 2 = 19mm
    # Cup Outer Radius = CUP_INNER_DIAM/2 + 1.0 = 10 + 1 = 11mm
    # Gap = 19 - 11 = 8mm
    # Center of Gap = CupOuter + Gap/2 = 11 + 4 = 15mm
    
    GAP_START = CUP_INNER_DIAM/2 + 1.0 # 11mm
    GAP_END = RING_OD/2 - WALL # 19mm
    GAP_WIDTH = GAP_END - GAP_START # 8mm
    GAP_CENTER = GAP_START + GAP_WIDTH/2
    
    with BuildSketch(Plane.XY.offset(SPOKE_Z)) as spoke_sk:
        with PolarLocations(radius=GAP_CENTER, count=3):
            # Rectangle spanning the exact gap with slight overlap
            Rectangle(width=GAP_WIDTH + 1.0, height=2.0)
    extrude(amount=2.0) # Thickness of spoke

# --- EXPORT ---
if __name__ == "__main__":
    try:
        setup_ocp()
        
        # VISUAL ASSEMBLY
        
        # Nozzle: Needs to be flipped and moved to Z=15 (Base at 15, Chimney down)
        # In our part build: Z=0 is base, Chimney is +Z.
        # We need to Rotate 180 X?
        nozzle_inv = nozzle_insert.part.rotate(Axis.X, 180)
        # Now Base is at Z=0, Chimney is -Z.
        # Move Base to Z=15 + Base_Thick (so flat face is at 15)
        # Wait, if we glue it, the flat face is at 15.
        nozzle_vis = nozzle_inv.move(Location((0,0, SECTION_HEIGHT - INTERFACE_HEIGHT + BASE_THICK)))

        show(
            middle_section.part,
            nozzle_vis,
            names=["Spoked_Middle_Section", "Nozzle_Extension"],
            colors=["teal", "red"]
        )
    except Exception as e:
        print(f"Error communicating with OCP Viewer: {e}")
        import traceback
        traceback.print_exc()
        
    export_stl(middle_section.part, "impactor_4um_spoked_middle.stl")
    export_stl(nozzle_insert.part, "impactor_4um_nozzle_ext.stl")
    print("Files Exported")
