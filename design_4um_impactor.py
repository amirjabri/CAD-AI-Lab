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
SECTION_HEIGHT = 20.0
INTERFACE_HEIGHT = 5.0

# Base Geometry (Common)
CUP_FLOOR_Z = 5.0
CUP_RIM_HEIGHT = 8.0 
CUP_RIM_Z = CUP_FLOOR_Z + CUP_RIM_HEIGHT 
GUARD_ID = 9.0 
GUARD_HEIGHT = 2.0 
GUARD_Z_BOTTOM = CUP_RIM_Z - GUARD_HEIGHT
CUP_INNER_DIAM = 20.0 

def calculate_physics(flow_lpm):
    # Physics Calculation
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

def generate_middle_holder():
    # Common Part
    HOLDER_ID = 22.0 
    HOLDER_WALL = 1.0
    HOLDER_HEIGHT = 6.0 
    HOLDER_Z = CUP_FLOOR_Z + 2.0 
    
    with BuildPart() as holder_assy:
        with BuildSketch(Plane.XY):
            Circle(radius=RING_OD/2); Circle(radius=RING_OD/2 - WALL, mode=Mode.SUBTRACT)
        extrude(amount=SECTION_HEIGHT)
        
        # 2. Bottom Boss (Interface)
        with BuildSketch(Plane.XY.offset(-INTERFACE_HEIGHT)):
            Circle(radius=FIT_BOSS_OD/2); Circle(radius=FIT_BOSS_OD/2 - WALL, mode=Mode.SUBTRACT)
        extrude(amount=INTERFACE_HEIGHT)
        
        # 2.5 Reinforcement Flange
        with BuildSketch(Plane.XY):
            Circle(radius=RING_OD/2)
            Circle(radius=FIT_BOSS_OD/2 - WALL, mode=Mode.SUBTRACT) 
        extrude(amount=2.0)
        
        # 3. Top Socket (Cutout for Lid)
        with BuildSketch(Plane.XY.offset(SECTION_HEIGHT)):
            Circle(radius=FIT_SOCKET_ID/2)
        extrude(amount=-INTERFACE_HEIGHT, mode=Mode.SUBTRACT)
        
        with BuildSketch(Plane.XY.offset(HOLDER_Z)):
            Circle(radius=HOLDER_ID/2 + HOLDER_WALL); Circle(radius=HOLDER_ID/2, mode=Mode.SUBTRACT)
        extrude(amount=HOLDER_HEIGHT)
        
        spoke_th = 2.0
        with BuildSketch(Plane.XY.offset(HOLDER_Z + 1.0)): 
            with PolarLocations(radius=(RING_OD/4 + HOLDER_ID/4), count=3):
                 Rectangle(width=(RING_OD/2 - WALL) - (HOLDER_ID/2), height=spoke_th)
        extrude(amount=4.0)
    return holder_assy.part

def generate_removable_cup():
    # Common Part
    CUP_FIT_OD = 22.1 # 0.1mm Interference
    with BuildPart() as cup:
        with BuildSketch(Plane.XY.offset(CUP_FLOOR_Z)):
            Circle(radius=CUP_FIT_OD/2); Circle(radius=CUP_INNER_DIAM/2, mode=Mode.SUBTRACT)
        extrude(amount=CUP_RIM_HEIGHT)
        
        with BuildSketch(Plane.XY.offset(CUP_FLOOR_Z)):
             Circle(radius=CUP_FIT_OD/2)
        extrude(amount=-1.5) 
        
        # Guard
        with BuildPart() as guard:
            with BuildSketch(Plane.XY.offset(GUARD_Z_BOTTOM)):
                Circle(radius=CUP_INNER_DIAM/2); Circle(radius=CUP_INNER_DIAM/2 - 0.1, mode=Mode.SUBTRACT) 
            with BuildSketch(Plane.XY.offset(CUP_RIM_Z)):
                Circle(radius=CUP_INNER_DIAM/2); Circle(radius=GUARD_ID/2, mode=Mode.SUBTRACT) 
            loft()
        add(guard.part)
        
        # Handle
        with BuildSketch(Plane.XY.offset(CUP_FLOOR_Z - 1.5)):
            Rectangle(width=8.0, height=2.0)
        extrude(amount=-3.0)
    return cup.part

def generate_nozzle(flow_lpm):
    d_mm, s_dist = calculate_physics(flow_lpm)
    print(f"[{flow_lpm} LPM] Nozzle: {d_mm:.3f}mm, S: {s_dist:.3f}mm")
    
    NOZZLE_EXIT_Z = CUP_FLOOR_Z + s_dist
    CHIMNEY_LEN = (SECTION_HEIGHT - INTERFACE_HEIGHT) - NOZZLE_EXIT_Z
    BASE_THICK = 2.0
    NOZZLE_WALL_THICK = 1.0
    NOZZLE_OUTER_DIAM = d_mm + (2 * NOZZLE_WALL_THICK)
    
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
        
        # Common Parts
        holder = generate_middle_holder()
        cup = generate_removable_cup()
        
        export_stl(holder, "impactor_holder_ring_common.stl")
        export_stl(cup, "impactor_removable_cup_common.stl")
        
        # Show Common (Center)
        show(holder, cup, names=["Common_Holder", "Common_Cup"], colors=["silver", "red"])
        
        # Variants
        offset_x = 0
        for flow in FLOW_VARIANTS:
            nozzle = generate_nozzle(flow)
            
            # Orient Nozzle for assembly view (Flip and Move)
            nozzle_vis = nozzle.rotate(Axis.X, 180).move(Location((offset_x, 0, SECTION_HEIGHT - INTERFACE_HEIGHT + 2.0)))
            
            # Show ghost holder/cup for context at offset?
            if offset_x != 0:
                 # Group them for a single show call per variant location to avoid overwriting or confusion
                 show(
                    holder.move(Location((offset_x, 0, 0))),
                    cup.move(Location((offset_x, 0, 0))), 
                    nozzle_vis,
                    names=[f"Holder_{flow}", f"Cup_{flow}", f"Nozzle_{flow}LPM"],
                    colors=["silver", "red", "teal"]
                 )
            else:
                 # At 0,0, just add the nozzle to the existing view
                 show(nozzle_vis, names=[f"Nozzle_{flow}LPM"], colors=["teal"])
            
            # Export
            export_stl(nozzle, f"impactor_nozzle_{flow}LPM.stl")

            offset_x += 60 # Move next one over
            
        print("Batch Generation Complete.")
        
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
