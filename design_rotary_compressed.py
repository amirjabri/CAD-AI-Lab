import logging
import os
import shutil
from build123d import *
import math

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("RotaryCompressed")

class CompressedRotarySampler:
    """
    v46 Compressed Rotary Assembly (18mm Total).
    - Base: 10mm Thick (Plenums 6mm).
    - Lid: 6mm Thick (Chutes 4mm).
    - Cover: 2mm Thick (At Z=16).
    """
    def __init__(self, num_slots=8):
        self.num_slots = num_slots
        self.filter_r = 35.0 
        self.cassette_radius = 55.0
        self.slot_angle = 360.0 / num_slots
        self.zigzag_width = 3.2
        
        # Dimensions
        self.base_h = 10.0
        self.lid_h = 6.0
        self.cover_h = 2.0
        
        logger.info(f"Initialized Compressed Sampler (18mm Stack).")
        
    def generate_body(self):
        """Compressed Body (10mm)."""
        logger.info(f"Generating Compressed Body.")
        
        with BuildPart() as body:
            # 1. Main Disc
            with BuildSketch(Plane.XY):
                Circle(radius=self.cassette_radius)
            extrude(amount=self.base_h) # 10.0
            
            # 2. Central Shared Plenum (Z=2.0 to 6.0)
            # Was 4mm tall (2 to 6). Keep 4mm? Or also squish?
            # Original: 8mm plenums -> 6mm plenums.
            # Let's keep central plenum 4mm (Z=2..6) to ensure flow.
            with BuildSketch(Plane.XY.offset(2.0)):
                Circle(radius=8.0)
            extrude(amount=4.0, mode=Mode.SUBTRACT)
            
            # 3. Filter Seats (Recessed 1.5mm from top)
            # Top is 10.0. Seat Floor is 8.5.
            with BuildSketch(Plane.XY.offset(self.base_h - 1.5)): # Z=8.5
                with PolarLocations(radius=self.filter_r, count=self.num_slots):
                    Circle(radius=25.4/2)
            extrude(amount=1.5, mode=Mode.SUBTRACT)
            
            # 4. Grid Supports (Z=8.0 to 8.5)
            # Below filter seats.
            with BuildSketch(Plane.XY.offset(self.base_h - 2.0)): # Z=8.0
                with PolarLocations(radius=self.filter_r, count=self.num_slots):
                    with PolarLocations(radius=7.5, count=6):
                        Circle(radius=3.0)
                    Circle(radius=3.0)
            extrude(amount=0.5, mode=Mode.SUBTRACT)
            
            # 5. Under-Filter Plenums & Radial Tunnels
            # Height = 6.0mm (Z=2.0 to 8.0)
            with BuildSketch(Plane.XY.offset(2.0)):
                with PolarLocations(radius=self.filter_r, count=self.num_slots):
                    Circle(radius=22.0/2)
                    with Locations((-self.filter_r/2, 0)):
                        Rectangle(width=self.filter_r, height=8.0)
            extrude(amount=6.0, mode=Mode.SUBTRACT) # Reduced from 8.0
            
            # 6. Integrated Exhaust Barb
            with BuildSketch(Plane.XY):
                Circle(radius=10.0/2)
            extrude(amount=-10.0, mode=Mode.ADD)
            with BuildSketch(Plane.XY):
                Circle(radius=6.0/2)
            extrude(amount=-12.0, mode=Mode.SUBTRACT)

            # 7. MATING FEATURES
            # Lip Up from Z=10.0
            with BuildSketch(Plane.XY.offset(self.base_h)):
                Circle(radius=self.cassette_radius)
                Circle(radius=54.0, mode=Mode.SUBTRACT)
            extrude(amount=2.0, mode=Mode.ADD)
                
        return body.part

    def generate_lid(self):
        """Compressed Lid (6mm). Z=10..16"""
        logger.info(f"Generating Compressed Lid.")
        
        base_z = self.base_h # 10.0
        
        with BuildPart() as lid:
            # 1. Main Lid Disc
            with BuildSketch(Plane.XY.offset(base_z)):
                Circle(radius=self.cassette_radius)
            extrude(amount=self.lid_h) # 6.0
            
            # Mating Recess (Z=10..12)
            with BuildSketch(Plane.XY.offset(base_z)):
                Circle(radius=self.cassette_radius)
                Circle(radius=54.0, mode=Mode.SUBTRACT)
            extrude(amount=2.0, mode=Mode.SUBTRACT)
            
            # ZIGZAG LOGIC (Same)
            def get_amp(r): return 2.5 + (r - 15.0) * (3.5 / 20.0)
            zigzag_points = []
            zigzag_points.append((15.0, -2.5)); zigzag_points.append((15.0, 2.5))
            for r_val in [19, 23, 27, 31, 35]:
                a = get_amp(r_val)
                val1 = a if r_val % 4 == 3 else -a # simple alternating logic check?
                # Actually copying strict logic:
                if r_val == 19: zigzag_points.extend([(19, a), (19, -a)])
                elif r_val == 23: zigzag_points.extend([(23, -a), (23, a)])
                elif r_val == 27: zigzag_points.extend([(27, a), (27, -a)])
                elif r_val == 31: zigzag_points.extend([(31, -a), (31, a)])
                elif r_val == 35: zigzag_points.extend([(35, a), (35, 0.)])

            # 2. INLETS (8x)
            # Top of Lid is now Z=10+6=16.
            # Recess 2mm for zigzags -> Z=14.
            # Inlets go through top 2mm.
            with BuildSketch(Plane.XY.offset(base_z + self.lid_h - 2.0)): # Z=14
                with PolarLocations(radius=0, count=self.num_slots):
                    with Locations((15.0, -2.5)): 
                        Circle(radius=2.0)
            extrude(amount=2.0, mode=Mode.SUBTRACT)
            
            # 3. ZIGZAGS (8x)
            with BuildSketch() as unit_zigzag:
                 with BuildLine() as path:
                    Polyline(zigzag_points)
                 make_face(offset(path.line, amount=self.zigzag_width/2))
            with BuildSketch(Plane.XY.offset(base_z + self.lid_h - 2.0)): # Z=14
                with PolarLocations(radius=0, count=self.num_slots):
                    add(unit_zigzag)
            extrude(amount=2.0, mode=Mode.SUBTRACT)
            
            # 4. VERTICAL CHUTES (8x)
            # Reduced height: 4.0mm (Z=10 to 14)
            with BuildSketch(Plane.XY.offset(base_z)): # Z=10
                with PolarLocations(radius=0, count=self.num_slots):
                    with Locations((35.0, 0)):
                        Rectangle(width=8.0, height=self.zigzag_width, align=(Align.MIN, Align.CENTER))
            extrude(amount=4.0, mode=Mode.SUBTRACT)
            
            # 5. RETENTION RIMS (8x)
            with BuildSketch(Plane.XY.offset(base_z)):
                with PolarLocations(radius=0, count=self.num_slots):
                    with Locations((self.filter_r, 0)):
                        Circle(radius=25.2/2) 
                        Circle(radius=21.2/2, mode=Mode.SUBTRACT)
            extrude(amount=-1.5, mode=Mode.ADD) 

            # CENTRAL PIVOT
            # Start Z=16.
            with BuildSketch(Plane.XY.offset(base_z + self.lid_h)):
                Circle(radius=2.5) 
            extrude(amount=5.0, mode=Mode.ADD)

        return lid.part

    def generate_cover(self):
        """Cover at Z=16..18"""
        base_z = self.base_h + self.lid_h # 16.0
        
        with BuildPart() as cover:
            with BuildSketch(Plane.XY.offset(base_z)):
                Circle(radius=self.cassette_radius)
            extrude(amount=2.0)
            
            with BuildSketch(Plane.XY.offset(base_z)):
                Circle(radius=2.6) # Pivot
                with Locations((15.0, -2.5)):
                    Circle(radius=1.5) # Selector
            extrude(amount=2.0, mode=Mode.SUBTRACT)
            
        return cover.part

def export_batch(body, lid, cover):
    base_dir = "iterations"
    if not os.path.exists(base_dir): os.makedirs(base_dir)
    
    # Versioning
    existing = []
    for d in os.listdir(base_dir):
        if d.startswith("v") and "_" in d:
            try: v_num = int(d.split("_")[0][1:])
            except: continue
            existing.append(v_num)
    next_v = max(existing) + 1 if existing else 1
    version_str = f"v{next_v:02d}"
    
    folder_name = f"{version_str}_copressed_drone"
    output_dir = os.path.join(base_dir, folder_name)
    os.makedirs(output_dir)
    
    export_stl(body, os.path.join(output_dir, f"{version_str}_compressed_body.stl"))
    export_stl(lid, os.path.join(output_dir, f"{version_str}_compressed_lid.stl"))
    export_stl(cover, os.path.join(output_dir, f"{version_str}_cover.stl"))
    
    shutil.copy(__file__, os.path.join(output_dir, f"{version_str}_script_snapshot.py"))
    logger.info(f"Design saved to: {output_dir}")
    return version_str, output_dir

if __name__ == "__main__":
    sampler = CompressedRotarySampler()
    body_p = sampler.generate_body()
    lid_p = sampler.generate_lid()
    cover_p = sampler.generate_cover()
    
    version, path = export_batch(body_p, lid_p, cover_p)
    
    try:
        from ocp_vscode import show, Camera, set_port
        set_port(3939)
        
        # Slightly exploded view
        show(
            body_p, 
            lid_p.translate((0,0,10)), 
            cover_p.translate((0,0,30)), 
            names=[f"{version}_Base_10mm", f"{version}_Lid_6mm", f"{version}_Cover"],
            reset_camera=Camera.RESET
        )
    except ImportError:
        pass
