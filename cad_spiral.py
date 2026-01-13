
from build123d import *
from viewer_setup import setup_ocp, show
from ocp_vscode import Camera
import math

# --- CONFIGURATION ---
W_START = 5.0
W_END = 2.0
WALL_THICKNESS = 1.2
TURNS = 2.5
# Flow Variants: (Flow LPM, Height mm)
# Ratio: 10mm / 4.0LPM = 2.5 mm/LPM
FLOW_VARIANTS = [
    (1.5, 3.75),
    (2.0, 5.0),
    (2.5, 6.25),
    (3.0, 7.5),
    (3.5, 8.75)
]

# Cassette Interfaces
RING_OD = 42.0
FIT_BOSS_OD = 37.4
FIT_SOCKET_ID = 37.2
INTERFACE_HEIGHT = 5.0
INLET_DIAMETER = 6.0
BARB_HEIGHT = 10.0

# --- GEOMETRY HELPERS ---
spiral_outer_r_centerline = (RING_OD / 2) - WALL_THICKNESS - (W_START / 2)
spiral_inner_r_centerline = 4.0 
delta_r = spiral_outer_r_centerline - spiral_inner_r_centerline
b_inward = delta_r / (TURNS * 2 * math.pi)

def polar_spiral_centerline(theta):
    return spiral_outer_r_centerline - b_inward * theta

def width_at_theta(theta):
    fraction = theta / (TURNS * 2 * math.pi)
    return W_START - fraction * (W_START - W_END)

path_outer_wall = []
path_inner_wall = []
steps = 150
total_angle = TURNS * 2 * math.pi
for i in range(steps + 1):
    theta = (i / steps) * total_angle
    r_c = polar_spiral_centerline(theta)
    w = width_at_theta(theta)
    r_out = r_c + w/2
    r_in = r_c - w/2
    path_outer_wall.append( (r_out * math.cos(theta), r_out * math.sin(theta)) )
    path_inner_wall.append( (r_in * math.cos(theta), r_in * math.sin(theta)) )
full_loop_pts = path_outer_wall + path_inner_wall[::-1] + [path_outer_wall[0]]

# --- PART GENERATION FUNCTIONS ---

def generate_body(channel_height):
    with BuildPart() as body:
        body_h = channel_height + 2.0
        
        # 1. Main Housing (Aligned to Z=0)
        Cylinder(radius=RING_OD/2, height=body_h, align=(Align.CENTER, Align.CENTER, Align.MIN))
        
        # 2. Top Rim
        with BuildSketch(Plane.XY.offset(body_h)): 
            Circle(radius=RING_OD/2)
            Circle(radius=(RING_OD/2) - 2.0, mode=Mode.SUBTRACT)
        extrude(amount=2.0)
        
        # 3. Bottom Male Boss
        with BuildSketch(Plane.XY): 
            Circle(radius=FIT_BOSS_OD/2)
            Circle(radius=FIT_BOSS_OD/2 - 2, mode=Mode.SUBTRACT)
        extrude(amount=-INTERFACE_HEIGHT)
        
        # 4. Cut Variable Width Channel
        with BuildSketch(Plane.XY.offset(body_h)):
            with BuildLine() as flow_line:
                Polyline(full_loop_pts) 
            make_face(flow_line.wire()) 
        extrude(amount=-channel_height, mode=Mode.SUBTRACT)
        
        # 5. Exit Hole (8mm)
        with BuildSketch(Plane.XY.offset(body_h + 1.0)): 
            Circle(radius=4.0) 
        extrude(amount=-50.0, mode=Mode.SUBTRACT)
    return body.part

def generate_cover():
    inlet_r_location = spiral_outer_r_centerline
    cover_od = RING_OD - 4.0 - 0.4
    cover_thickness = 2.0
    with BuildPart() as cover:
        Cylinder(radius=cover_od/2, height=cover_thickness, align=(Align.CENTER, Align.CENTER, Align.MIN))
        with BuildSketch(Plane.XY):
            with Locations((inlet_r_location, 0)):
                Circle(radius=INLET_DIAMETER/2)
        extrude(amount=cover_thickness, mode=Mode.SUBTRACT)
    return cover.part

def generate_base():
    # v33: Compact 8mm Height + Center Extension.
    base_height = 8.0
    socket_depth = 5.0
    seat_z = base_height - socket_depth # Z = 3.0
    fit_socket_cleaning = FIT_BOSS_OD/2 + 0.1 
    plenum_cleaning = 34.0/2 

    with BuildPart() as base:
        # 1. Main Block
        Cylinder(radius=RING_OD/2, height=base_height, align=(Align.CENTER, Align.CENTER, Align.MIN))
        
        # 2. Add Manifold Solid (The "Half Cylinder" Spine)
        # Starts at Center (X=0) and goes Out.
        # Intersects with Main Block.
        # Will be carved out by Socket/Plenum cuts later.
        
        barb_flow_z = (seat_z + 1.0) / 2 # Z = 2.0
        barb_od_r = INLET_DIAMETER/2 + 1.5 # 4.5mm
        
        with BuildSketch(Plane.YZ): # X=0 Plane
            with Locations((0, barb_flow_z)):
                Circle(radius=barb_od_r)
            # Cut off bottom (Below Z=0)
            with Locations((0, -5.0)):
                Rectangle(width=barb_od_r*3, height=10.0, mode=Mode.SUBTRACT)
        
        # Extrude from Center to Outside (RING_OD/2 + 5.0)
        extrude(amount=RING_OD/2 + 5.0 + 2.0)
        
        # 3. Cut Top Socket (Receiver)
        with BuildSketch(Plane.XY.offset(base_height)):
            Circle(radius=fit_socket_cleaning)
        extrude(amount=-socket_depth, mode=Mode.SUBTRACT)
        
        # 4. Cut Lower Plenum (Collector)
        with BuildSketch(Plane.XY.offset(seat_z)):
            Circle(radius=plenum_cleaning)
        extrude(amount=-(seat_z - 1.0), mode=Mode.SUBTRACT)
        
        # 4b. Vortex Cone (v34 Improvement)
        # Sits on the floor (Z=1.0) to smooth airflow transition.
        # Height 2.0 goes up to Seat level (Z=3.0).
        Cone(bottom_radius=4.0, top_radius=0.0, height=2.0, 
             align=(Align.CENTER, Align.CENTER, Align.MIN)).move(Location((0,0,1.0)))
        
        # 5. Add Ribs
        with BuildSketch(Plane.XY.offset(1.0)):
            Rectangle(width=plenum_cleaning*2, height=1.0)
            Rectangle(width=1.0, height=plenum_cleaning*2)
        extrude(amount=(seat_z - 1.0))
        
        # 6. Barb Tip (The Round End)
        with BuildSketch(Plane.YZ.offset(RING_OD/2 + 5.0)):
            Circle(radius=barb_od_r)
        extrude(amount=BARB_HEIGHT).move(Location((0,0,barb_flow_z)))
        
        # 7. Barb Bore (Hole)
        with BuildSketch(Plane.YZ.offset(RING_OD/2 + 5.0 + BARB_HEIGHT)):
            Circle(radius=INLET_DIAMETER/2)
        extrude(amount=-(BARB_HEIGHT), mode=Mode.SUBTRACT).move(Location((0,0,barb_flow_z)))
        
        # 8. Internal Slot Cut
        # Cut the slot from the outside in, through the spine.
        # Stop at some point? Or cut through to center?
        # Let's cut into the plenum. Center is X=0.
        # Plenum R = 17. The Slot stops at X=0?
        # The Plenum Cut (Step 4) already hollows out the spine for R<17.
        # We just need to connect the Barb Bore to the Plenum.
        # The Bore is at X ~ 26.
        # We need a cut from X=26 inward to X=17 (Plenum wall).
        with BuildSketch(Plane.YZ.offset(RING_OD/2 + 5.0)):
             Rectangle(width=INLET_DIAMETER * 2 - 2.0, height=seat_z - 1.0 - 0.4)
        extrude(amount=-(5.0 + 2.0 + RING_OD/2), mode=Mode.SUBTRACT).move(Location((0,0,barb_flow_z)))
        
    return base.part

# --- EXPORT ---
import os
import shutil

def export_batch():
    base_dir = "iterations"
    if not os.path.exists(base_dir): os.makedirs(base_dir)
    
    # Versioning
    existing_versions = []
    for d in os.listdir(base_dir):
        if d.startswith("v") and "_" in d:
            try: v_num = int(d.split("_")[0][1:])
            except: continue
            existing_versions.append(v_num)
    next_v = max(existing_versions) + 1 if existing_versions else 1
    version_str = f"v{next_v:02d}"
    
    # Export Folder
    folder_name = f"{version_str}_flow_variants"
    output_dir = os.path.join(base_dir, folder_name)
    os.makedirs(output_dir)
    print(f"Saving to: {output_dir}")
    
    # 1. Export Common Parts
    base_part = generate_base()
    cover_part = generate_cover()
    export_stl(base_part, os.path.join(output_dir, f"{version_str}_base_common.stl"))
    export_stl(cover_part, os.path.join(output_dir, f"{version_str}_cover_common.stl"))
    
    # 2. Export Body Variants
    for flow, h in FLOW_VARIANTS:
        print(f"Generating Body for {flow} LPM (H={h}mm)...")
        body_part = generate_body(h)
        fname = f"{version_str}_body_{flow}LPM.stl"
        export_stl(body_part, os.path.join(output_dir, fname))
        
    shutil.copy(__file__, os.path.join(output_dir, f"{version_str}_script_snapshot.py"))
    print(f"Exported Batch: {version_str}")

if __name__ == "__main__":
    try:
        setup_ocp()
        # Show one example (2.0 LPM)
        b = generate_body(5.0)
        c = generate_cover()
        base = generate_base()
        show(b.move(Location((0,0,10))), c.move(Location((0,0,17))), base, names=["Body_2LPM", "Cover", "Base"], colors=["teal", "yellow", "silver"])
    except: pass
    export_batch()

