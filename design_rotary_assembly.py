import logging
import os
import shutil
from build123d import *
import math

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("RotaryAssembly")

class RotarySampler:
    """
    v45 Rotary Assembly.
    - Base: SAME as v44 (Perfect Body).
    - Lid: Modified v44 with central pivot.
    - Cover: NEW selection disc.
    """
    def __init__(self, num_slots=8):
        self.num_slots = num_slots
        self.filter_r = 35.0 
        self.cassette_radius = 55.0
        self.slot_angle = 360.0 / num_slots
        self.zigzag_width = 3.2
        logger.info(f"Initialized Rotary Sampler with {self.num_slots} slots.")
        
    def generate_static_body(self):
        """EXACT COPY of v44/v41.1 'Perfect' Static Body."""
        logger.info(f"Generating Perfect Static Body (110mm).")
        
        with BuildPart() as body:
            # 1. Main Disc (12mm thick)
            with BuildSketch(Plane.XY):
                Circle(radius=self.cassette_radius)
            extrude(amount=12.0)
            
            # 2. Central Shared Plenum (Z=2.0 to 6.0)
            with BuildSketch(Plane.XY.offset(2.0)):
                Circle(radius=8.0)
            extrude(amount=4.0, mode=Mode.SUBTRACT)
            
            # 3. 8 Filter Seats (Recessed 1.5mm from top)
            with BuildSketch(Plane.XY.offset(10.5)):
                with PolarLocations(radius=self.filter_r, count=self.num_slots):
                    Circle(radius=25.4/2)
            extrude(amount=1.5, mode=Mode.SUBTRACT)
            
            # 4. 8 Grid Supports (Z=10.0 to 10.5)
            with BuildSketch(Plane.XY.offset(10.0)):
                with PolarLocations(radius=self.filter_r, count=self.num_slots):
                    with PolarLocations(radius=7.5, count=6):
                        Circle(radius=3.0)
                    Circle(radius=3.0)
            extrude(amount=0.5, mode=Mode.SUBTRACT)
            
            # 5. 8 Under-Filter Plenums & Radial Tunnels
            with BuildSketch(Plane.XY.offset(2.0)):
                with PolarLocations(radius=self.filter_r, count=self.num_slots):
                    Circle(radius=22.0/2)
                    with Locations((-self.filter_r/2, 0)):
                        Rectangle(width=self.filter_r, height=8.0)
            extrude(amount=8.0, mode=Mode.SUBTRACT)
            
            # 6. Integrated Exhaust Barb (Bottom)
            with BuildSketch(Plane.XY):
                Circle(radius=10.0/2)
            extrude(amount=-10.0, mode=Mode.ADD)
            with BuildSketch(Plane.XY):
                Circle(radius=6.0/2) # Bore
            extrude(amount=-12.0, mode=Mode.SUBTRACT)

            # 7. MATING FEATURES
            with BuildSketch(Plane.XY.offset(12.0)):
                Circle(radius=self.cassette_radius)
                Circle(radius=54.0, mode=Mode.SUBTRACT)
            extrude(amount=2.0, mode=Mode.ADD)
                
        return body.part

    def generate_static_lid_with_pivot(self):
        """Modified Lid with Central Pivot. Z=12..20"""
        logger.info(f"Generating Rotary Lid (with Pivot).")
        
        with BuildPart() as lid:
            # 1. Main Lid Disc (Z=12..20)
            with BuildSketch(Plane.XY.offset(12.0)):
                Circle(radius=self.cassette_radius)
            extrude(amount=8.0)
            
            # Mating Recess
            with BuildSketch(Plane.XY.offset(12.0)):
                Circle(radius=self.cassette_radius)
                Circle(radius=54.0, mode=Mode.SUBTRACT)
            extrude(amount=2.0, mode=Mode.SUBTRACT)
            
            # ZIGZAG LOGIC (Same as v44)
            def get_amp(r):
                return 2.5 + (r - 15.0) * (3.5 / 20.0)

            zigzag_points = []
            zigzag_points.append((15.0, -2.5))
            zigzag_points.append((15.0, 2.5))
            a19 = get_amp(19.0)
            zigzag_points.append((19.0, a19))
            zigzag_points.append((19.0, -a19))
            a23 = get_amp(23.0)
            zigzag_points.append((23.0, -a23))
            zigzag_points.append((23.0, a23))
            a27 = get_amp(27.0)
            zigzag_points.append((27.0, a27))
            zigzag_points.append((27.0, -a27))
            a31 = get_amp(31.0)
            zigzag_points.append((31.0, -a31))
            zigzag_points.append((31.0, a31))
            a35 = get_amp(35.0)
            zigzag_points.append((35.0, a35))
            zigzag_points.append((35.0, 0.0))
            
            # 2. INLETS (8x)
            with BuildSketch(Plane.XY.offset(18.0)):
                with PolarLocations(radius=0, count=self.num_slots):
                    with Locations((15.0, -2.5)): 
                        Circle(radius=2.0)
            extrude(amount=2.0, mode=Mode.SUBTRACT)
            
            # 3. ZIGZAGS (8x)
            with BuildSketch() as unit_zigzag:
                 with BuildLine() as path:
                    Polyline(zigzag_points)
                 make_face(offset(path.line, amount=self.zigzag_width/2))
            with BuildSketch(Plane.XY.offset(18.0)):
                with PolarLocations(radius=0, count=self.num_slots):
                    add(unit_zigzag)
            extrude(amount=2.0, mode=Mode.SUBTRACT)
            
            # 4. VERTICAL CHUTES (8x)
            with BuildSketch(Plane.XY.offset(12.0)):
                with PolarLocations(radius=0, count=self.num_slots):
                    with Locations((35.0, 0)):
                        Rectangle(width=8.0, height=self.zigzag_width, align=(Align.MIN, Align.CENTER))
            extrude(amount=6.0, mode=Mode.SUBTRACT)
            
            # 5. RETENTION RIMS (8x)
            with BuildSketch(Plane.XY.offset(12.0)):
                with PolarLocations(radius=0, count=self.num_slots):
                    with Locations((self.filter_r, 0)):
                        Circle(radius=25.2/2) 
                        Circle(radius=21.2/2, mode=Mode.SUBTRACT)
            extrude(amount=-1.5, mode=Mode.ADD) 

            # --- NEW: CENTRAL PIVOT ---
            # Z=20 (Top of lid) -> Up 5mm
            with BuildSketch(Plane.XY.offset(20.0)):
                Circle(radius=2.5) # 5mm Diameter
            extrude(amount=5.0, mode=Mode.ADD)

        return lid.part

    def generate_rotary_cover(self):
        """Selector Cover. Z=20..22"""
        logger.info(f"Generating Rotary Cover.")
        
        with BuildPart() as cover:
            # Main Disc
            with BuildSketch(Plane.XY.offset(20.0)):
                Circle(radius=self.cassette_radius)
            extrude(amount=2.0)
            
            # Holes
            with BuildSketch(Plane.XY.offset(20.0)):
                # 1. Central Pivot Clearance
                Circle(radius=2.6) # 5.2mm Diameter
                
                # 2. Selector Hole (Matches Inlet Position)
                # Inlets are at (15, -2.5) in local coords rotated. 
                # Actually, in the Lid generation:
                # `with Locations((15.0, -2.5))` inside PolarLocations.
                # The "Inlet" is the start of the zigzag.
                # However, for a selector, we probably want to align with the Inlet hole.
                # Let's align with the *first* slot's inlet to start.
                # Slot 0 Inlet is at (15.0, -2.5).
                
                # Wait, (15.0, -2.5) is just cartesian shift from center? No.
                # It is inside `with PolarLocations(radius=0, count=self.num_slots): with Locations((15.0, -2.5)):`
                # So for angle=0, the Location is (15.0, -2.5).
                # The hole radius is 2.0.
                # Our cover hole should be larger, say 3.0mm (R=1.5).
                
                with Locations((15.0, -2.5)):
                    Circle(radius=1.5)
                    
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
    
    folder_name = f"{version_str}_rotary_cover"
    output_dir = os.path.join(base_dir, folder_name)
    os.makedirs(output_dir)
    
    export_stl(body, os.path.join(output_dir, f"{version_str}_body.stl"))
    export_stl(lid, os.path.join(output_dir, f"{version_str}_lid_pivot.stl"))
    export_stl(cover, os.path.join(output_dir, f"{version_str}_cover.stl"))
    
    shutil.copy(__file__, os.path.join(output_dir, f"{version_str}_script_snapshot.py"))
    logger.info(f"Design saved to: {output_dir}")
    return version_str

if __name__ == "__main__":
    sampler = RotarySampler()
    body_p = sampler.generate_static_body()
    lid_p = sampler.generate_static_lid_with_pivot()
    cover_p = sampler.generate_rotary_cover()
    
    version = export_batch(body_p, lid_p, cover_p)
    
    try:
        from ocp_vscode import show, Camera, set_port
        set_port(3939)
        
        # Show exploded view
        # Body at Z=0
        # Lid at Z=0 (Normal pos)
        # Cover at Z=30 (Exploded upwards by 10mm from its 20mm start)
        
        show(
            body_p, 
            lid_p.translate((0,0,20)), # Explode Lid too
            cover_p.translate((0,0,60)), # Explode Cover more
            names=[f"{version}_Body", f"{version}_Lid_Pivot", f"{version}_Cover"],
            reset_camera=Camera.RESET
        )
    except ImportError:
        pass
