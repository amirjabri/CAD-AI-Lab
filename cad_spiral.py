
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
    (3.5, 8.75),
    (4.0, 10.0) # Added per user request
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
    # v56 Refactor: Flat Circular Base (Simple Puck)
    # No protruding barb, just a central hole.
    
    base_height = 10.0 
    socket_depth = 5.0
    seat_z = base_height - socket_depth # Z = 5.0
    
    fit_socket_cleaning = FIT_BOSS_OD/2 + 0.1 
    plenum_cleaning = 34.0/2 
    
    # Exit Hole Dims (1/4" OD clearance? or ID?)
    # User asked for "1/4 inch barb in the middle" before, but now "no holes".
    # We will provide a 6.35mm (1/4") hole which fits standard tubing/fittings.
    exit_hole_r = 6.35 / 2 

    with BuildPart() as base:
        # 1. Main Block (Solid Cylinder)
        Cylinder(radius=RING_OD/2, height=base_height, align=(Align.CENTER, Align.CENTER, Align.MIN))
        
        # 2. Cut Top Socket (Receiver for Body)
        # Sits at the top (Z=10), goes down 5mm.
        with BuildSketch(Plane.XY.offset(base_height)):
            Circle(radius=fit_socket_cleaning)
        extrude(amount=-socket_depth, mode=Mode.SUBTRACT)
        
        # 3. Cut Internal Plenum (Collector)
        # Sits at Seat Level (Z=5), goes down to Floor (Z=1).
        # Floor thickness = 1.0mm
        with BuildSketch(Plane.XY.offset(seat_z)):
            Circle(radius=plenum_cleaning)
        extrude(amount=-(seat_z - 1.0), mode=Mode.SUBTRACT)
        
        # 4. Cut Central Exit Hole (Through Floor)
        # Goes from Floor (Z=1) down to Bottom (Z=0).
        with BuildSketch(Plane.XY.offset(1.0)):
            Circle(radius=exit_hole_r)
        extrude(amount=-(1.0 + 1.0), mode=Mode.SUBTRACT) # Cut through bottom
        
        # 5. Add Ribs (Support for Filter Disk)
        # Sits on Floor (Z=1), height up to Seat (Z=5).
        with BuildSketch(Plane.XY.offset(1.0)):
            Rectangle(width=plenum_cleaning*2, height=1.0)
            Rectangle(width=1.0, height=plenum_cleaning*2)
            Circle(radius=exit_hole_r + 0.5, mode=Mode.SUBTRACT) # Clear extraction hole
        extrude(amount=(seat_z - 1.0))
        
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
        # Show 4.0 LPM (Height 10.0) based on user request
        b = generate_body(10.0)
        c = generate_cover()
        base = generate_base()
        show(b.move(Location((0,0,10))), c.move(Location((0,0,17+5))), base, names=["Body_4LPM", "Cover", "Base"], colors=["teal", "yellow", "silver"])
    except: pass
    export_batch()

