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

# Z Levels:
# Z=0 is the bottom of the main ring body (Top of bottom boss).
# Z=SECTION_HEIGHT is the top of the ring.
# Nozzle Exit Z = CUP_FLOOR_Z + S_DIST
CUP_FLOOR_Z = 5.0
CUP_RIM_HEIGHT = 8.0 # Deep cup
CUP_RIM_Z = CUP_FLOOR_Z + CUP_RIM_HEIGHT # Z=13.0
NOZZLE_EXIT_Z = CUP_FLOOR_Z + S_DIST

# Anti-Spill Guard Dimensions
GUARD_ID = 9.0 # Inner Diameter of the spill guard lip
GUARD_HEIGHT = 2.0 
GUARD_Z_BOTTOM = CUP_RIM_Z - GUARD_HEIGHT

NOZZLE_WALL_THICK = 1.0
NOZZLE_OUTER_DIAM = NOZZLE_DIAM_MM + (2 * NOZZLE_WALL_THICK)
CUP_INNER_DIAM = 20.0 

# A. Nozzle Insert (Extended Chimney)
CHIMNEY_LEN = (SECTION_HEIGHT - INTERFACE_HEIGHT) - NOZZLE_EXIT_Z # 5.1mm
BASE_THICK = 2.0 

with BuildPart() as nozzle_insert:
    # 1. Base (The part that glues to the lid)
    Cylinder(radius=15.0/2, height=BASE_THICK)
    # 2. Chimney (Extending down)
    with BuildSketch(Plane.XY):
        Circle(radius=NOZZLE_OUTER_DIAM/2)
    extrude(amount=CHIMNEY_LEN) 
    # Bore hole through all.
    with BuildSketch(Plane.XY):
        Circle(radius=NOZZLE_DIAM_MM/2)
    extrude(amount=BASE_THICK + CHIMNEY_LEN + 1.0, mode=Mode.SUBTRACT)

# B. Middle Section Components (Refactored for Press Fit)

def generate_middle_holder():
    # Ring that mounts to the cassette wall and holds the cup in the center.
    # Includes: Housing Ring, Spokes, and Central Holder Ring.
    
    HOLDER_ID = 22.0 # ID of the central ring that receives the cup
    HOLDER_WALL = 1.0
    HOLDER_HEIGHT = 6.0 
    HOLDER_Z = CUP_FLOOR_Z + 2.0 # Positioned around the cup's mid-section
    
    with BuildPart() as holder_assy:
        # 1. Main Housing Ring (Outer)
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
        
        # 4. Central Holder Ring (Inner)
        with BuildSketch(Plane.XY.offset(HOLDER_Z)):
            Circle(radius=HOLDER_ID/2 + HOLDER_WALL)
            Circle(radius=HOLDER_ID/2, mode=Mode.SUBTRACT)
        extrude(amount=HOLDER_HEIGHT)
        
        # 5. Spokes (Connecting Holder to Housing)
        # Create 3 spokes at 120 degrees
        spoke_th = 2.0
        with BuildSketch(Plane.XY.offset(HOLDER_Z + 1.0)): # Slightly offset from bottom of holder
            with PolarLocations(radius=(RING_OD/4 + HOLDER_ID/4), count=3):
                 # Length = (RING_ID - HOLDER_OD)/2 roughly
                 # Width needs to bridge the gap
                 Rectangle(width=(RING_OD/2 - WALL) - (HOLDER_ID/2), height=spoke_th)
        extrude(amount=4.0)
        
    return holder_assy.part

def generate_removable_cup():
    # The actual cup that pops into the holder.
    # OD needs to match HOLDER_ID (Press fit).
    
    # 0.1mm Interference for Press Fit (User request: "pop in")
    CUP_FIT_OD = 22.1 
    
    with BuildPart() as cup:
        # 1. Cup Wall
        with BuildSketch(Plane.XY.offset(CUP_FLOOR_Z)):
            Circle(radius=CUP_FIT_OD/2) # Outer
            Circle(radius=CUP_INNER_DIAM/2, mode=Mode.SUBTRACT) # Inner (20mm)
        extrude(amount=CUP_RIM_HEIGHT)
        
        # 2. Cup Floor
        with BuildSketch(Plane.XY.offset(CUP_FLOOR_Z)):
             Circle(radius=CUP_FIT_OD/2)
        extrude(amount=-1.5) # Floor thickness down
        
        # 3. Anti-Spill Guard (Lobster Trap) - ADDED ON TOP
        with BuildPart() as guard:
            with BuildSketch(Plane.XY.offset(GUARD_Z_BOTTOM)):
                Circle(radius=CUP_INNER_DIAM/2) # OD 20
                Circle(radius=CUP_INNER_DIAM/2 - 0.1, mode=Mode.SUBTRACT) 
            with BuildSketch(Plane.XY.offset(CUP_RIM_Z)):
                Circle(radius=CUP_INNER_DIAM/2) 
                Circle(radius=GUARD_ID/2, mode=Mode.SUBTRACT) # ID 9
            loft()
        add(guard.part)
        
        # 4. Handle / Grip (Bottom Tab for Removal)
        with BuildSketch(Plane.XY.offset(CUP_FLOOR_Z - 1.5)):
            Rectangle(width=8.0, height=2.0)
        extrude(amount=-3.0)
        
    return cup.part


# --- 4. EXPORT & VIEW ---
if __name__ == "__main__":
    try:
        setup_ocp()
        
        holder = generate_middle_holder()
        cup = generate_removable_cup()
        nozzle = nozzle_insert.part.rotate(Axis.X, 180).move(Location((0,0, SECTION_HEIGHT - INTERFACE_HEIGHT + BASE_THICK)))
        
        # Visualize Assembled
        # Cup is already modeled in position (Z=5)
        # Holder is modeled in position
        
        show(
            holder, 
            cup, 
            nozzle, 
            names=["Cassette_Holder", "PopIn_Cup", "Nozzle"], 
            colors=["silver", "red", "teal"]
        )
        
        print("Visualizing Press-Fit Cup Assembly.")
        
        export_stl(holder, "impactor_holder_ring.stl")
        export_stl(cup, "impactor_removable_cup.stl")
        export_stl(nozzle_insert.part, "impactor_nozzle.stl")
        
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        
    print("Files Exported")
