from build123d import *
from viewer_setup import setup_ocp, show
import math

# --- CONFIGURATION ---
TARGET_CUT_POINT_MICRONS = 4.0
FLOW_VARIANTS = [4.0, 2.5] # LPM
NOZZLE_COUNT = 1

# Mechanical Mating (Standard 37mm Cassette)
FIT_BOSS_OD = 37.4      
FIT_SOCKET_ID = 37.2    
FIT_SOCKET_DEPTH = 5.0
RING_OD = 42.0 
WALL = 2.0
SECTION_HEIGHT = 15.0 # Compact
INTERFACE_HEIGHT = 5.0

# Base Geometry (Common)
CUP_FLOOR_Z = 2.0 
CUP_RIM_HEIGHT = 8.0 
CUP_RIM_Z = CUP_FLOOR_Z + CUP_RIM_HEIGHT 
GUARD_ID = 6.0 
GUARD_HEIGHT = 2.0 
GUARD_Z_BOTTOM = CUP_RIM_Z - GUARD_HEIGHT
CUP_INNER_DIAM = 12.0 # Mini Cup

def calculate_physics(flow_lpm):
    STK_50 = 0.24 
    RHO_P = 1000
    AIR_VISCOSITY = 1.81e-5
    Q_m3s = (flow_lpm / 1000) / 60
    d50_m = TARGET_CUT_POINT_MICRONS * 1e-6
    numerator = 4 * RHO_P * (d50_m**2) * 1.0 * Q_m3s
    denominator = 9 * math.pi * AIR_VISCOSITY * STK_50 * NOZZLE_COUNT
    nozzle_diam_m = (numerator / denominator) ** (1/3)
    nozzle_diam_mm = nozzle_diam_m * 1000
    s_dist = nozzle_diam_mm * 1.5
    return nozzle_diam_mm, s_dist

def generate_integrated_body():
    # Merged Housing + Spokes + Cup (One Piece)
    
    CUP_OD = CUP_INNER_DIAM + 2.0 # 1mm wall -> 14mm OD
    
    with BuildPart() as integrated_body:
        # 1. Main Housing Ring (Outer)
        with BuildSketch(Plane.XY):
            Circle(radius=RING_OD/2); Circle(radius=RING_OD/2 - WALL, mode=Mode.SUBTRACT)
        extrude(amount=SECTION_HEIGHT)
        
        # 2. Bottom Boss (Interface)
        with BuildSketch(Plane.XY.offset(-INTERFACE_HEIGHT)):
            Circle(radius=FIT_BOSS_OD/2); Circle(radius=FIT_BOSS_OD/2 - WALL, mode=Mode.SUBTRACT)
        extrude(amount=INTERFACE_HEIGHT)
        
        # 2.5 Reinforcement Flange (Floor) - Bridges Ring to Boss
        with BuildSketch(Plane.XY):
            Circle(radius=RING_OD/2); Circle(radius=FIT_BOSS_OD/2 - WALL, mode=Mode.SUBTRACT) 
        extrude(amount=2.0)
        
        # 3. Top Socket (Cutout)
        with BuildSketch(Plane.XY.offset(SECTION_HEIGHT)):
            Circle(radius=FIT_SOCKET_ID/2)
        extrude(amount=-INTERFACE_HEIGHT, mode=Mode.SUBTRACT)
        
        # 4. Filter Support Ribs? (Optional - maybe later)
        
        # 5. The Cup (Centered)
        with BuildSketch(Plane.XY.offset(CUP_FLOOR_Z)):
            Circle(radius=CUP_OD/2); Circle(radius=CUP_INNER_DIAM/2, mode=Mode.SUBTRACT)
        extrude(amount=CUP_RIM_HEIGHT)
        
        # Cup Floor
        with BuildSketch(Plane.XY.offset(CUP_FLOOR_Z)):
             Circle(radius=CUP_OD/2)
        extrude(amount=-1.5) # Down to fuse with flange or just thick floor
        
        # 6. Anti-Spill Guard
        with BuildPart() as guard:
            with BuildSketch(Plane.XY.offset(GUARD_Z_BOTTOM)):
                Circle(radius=CUP_INNER_DIAM/2); Circle(radius=CUP_INNER_DIAM/2 - 0.1, mode=Mode.SUBTRACT) 
            with BuildSketch(Plane.XY.offset(CUP_RIM_Z)):
                Circle(radius=CUP_INNER_DIAM/2); Circle(radius=GUARD_ID/2, mode=Mode.SUBTRACT) 
            loft()
        add(guard.part)
        
        # 7. Spokes (Connecting Cup to Housing)
        # Positioned mid-cup
        SPOKE_Z = CUP_FLOOR_Z + 2.0
        spoke_th = 2.0
        
        # Calculate gap
        # Housing Inner R = RING_OD/2 - WALL = 19mm
        # Cup Outer R = 7mm
        # Center R = (19+7)/2 = 13mm
        # Length = 19-7 = 12mm
        
        with BuildSketch(Plane.XY.offset(SPOKE_Z)): 
            with PolarLocations(radius=13.0, count=3):
                 Rectangle(width=12.2, height=spoke_th) # 12.2 to verify Overlap
        extrude(amount=4.0) # Tall spokes for strength
        
    return integrated_body.part

def generate_nozzle(flow_lpm):
    d_mm, s_dist = calculate_physics(flow_lpm)
    print(f"[{flow_lpm} LPM] Nozzle: {d_mm:.3f}mm, S: {s_dist:.3f}mm")
    
    NOZZLE_EXIT_Z = CUP_FLOOR_Z + s_dist
    
    # 4mm OD Request
    NOZZLE_OUTER_DIAM = 4.0 
    
    # Check Wall Thickness
    wall_thick = (NOZZLE_OUTER_DIAM - d_mm) / 2
    if wall_thick < 0.3:
        print(f"WARNING: Nozzle wall is thin ({wall_thick:.3f}mm)")

    CHIMNEY_LEN = (SECTION_HEIGHT - INTERFACE_HEIGHT) - NOZZLE_EXIT_Z
    BASE_THICK = 2.0
    
    with BuildPart() as nozzle:
        Cylinder(radius=15.0/2, height=BASE_THICK)
        with BuildSketch(Plane.XY):
            Circle(radius=NOZZLE_OUTER_DIAM/2)
        extrude(amount=CHIMNEY_LEN) 
        with BuildSketch(Plane.XY):
            Circle(radius=d_mm/2)
        extrude(amount=BASE_THICK + CHIMNEY_LEN + 1.0, mode=Mode.SUBTRACT)
        
    return nozzle.part

if __name__ == "__main__":
    try:
        setup_ocp()
        
        # Common Integrated Body
        body = generate_integrated_body()
        export_stl(body, "impactor_integrated_body_common.stl")
        
        # Show Common Body
        show(body, names=["Integrated_Body"], colors=["silver"])
        
        # Weights
        vol = body.volume
        print(f"\n--- INTEGRATED BODY WEIGHT ---")
        print(f"Volume: {vol:.2f} mm^3")
        print(f"Weight (PLA): {(vol * 1.24)/1000.0:.3f} g")
        print(f"Weight (Resin): {(vol * 1.15)/1000.0:.3f} g")
        print(f"------------------------------\n")
        
        # Variants
        offset_x = 0
        for flow in FLOW_VARIANTS:
            nozzle = generate_nozzle(flow)
            
            # Orient Nozzle
            nozzle_vis = nozzle.rotate(Axis.X, 180).move(Location((offset_x, 0, SECTION_HEIGHT - INTERFACE_HEIGHT + 2.0)))
            
            if offset_x != 0:
                 show(
                    body.move(Location((offset_x, 0, 0))), 
                    nozzle_vis,
                    names=[f"Body_{flow}", f"Nozzle_{flow}LPM"],
                    colors=["silver", "teal"]
                 )
            else:
                 show(nozzle_vis, names=[f"Nozzle_{flow}LPM"], colors=["teal"])
            
            export_stl(nozzle, f"impactor_nozzle_{flow}LPM.stl")
            offset_x += 60 
            
        print("Integrated Generation Complete.")
        
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
