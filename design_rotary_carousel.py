import logging
import os
import shutil
from build123d import *
import math

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("RotaryCarousel")

class FinalCompactSampler:
    """Consolidated 2-part static assembly (v56). 
    Base: 110mm / 8-Filters (v41.1 Perfect).
    Lid: 8 Distinct Units (Inlet/Impactor/Rim) generated via PolarLocations array.
    """
    def __init__(self, num_slots=8):
        self.num_slots = num_slots
        self.filter_r = 35.0 # R=35 (2mm gaps between 25.4mm Circles)
        self.cassette_radius = 55.0 # Total 110mm
        self.slot_angle = 360.0 / num_slots
        self.zigzag_width = 3.2
        logger.info(f"Initialized Sampler with {self.num_slots} slots.")
        
    def generate_static_body(self):
        """EXACT RESTORATION of v41.1 'Perfect' Static Body. Z=0..12"""
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

            # 7. MATING FEATURES (v58) (Add to Body)
            # A. Outer Lip (Male on Body)
            # Extrude R=54..55mm Up by 2.0mm
            with BuildSketch(Plane.XY.offset(12.0)):
                Circle(radius=self.cassette_radius)
                Circle(radius=54.0, mode=Mode.SUBTRACT)
            extrude(amount=2.0, mode=Mode.ADD)
            
            # B. Central Connection REMOVED (v58)
                
        return body.part

    def generate_static_lid(self):
        """Lid with 8 units arrayed via PolarLocations. Z=12..20"""
        logger.info(f"Generating Static Lid v58 (Outer Lip Only).")
        
        with BuildPart() as lid:
            # 1. Main Lid Disc (Z=12..20)
            with BuildSketch(Plane.XY.offset(12.0)):
                Circle(radius=self.cassette_radius)
            extrude(amount=8.0)
            
            # MATING FEATURES (v58) (Add to Lid)
            # A. Outer Recess (Female on Lid)
            # Cut Ring R=54..55mm at bottom (Z=12..14)
            with BuildSketch(Plane.XY.offset(12.0)):
                Circle(radius=self.cassette_radius)
                Circle(radius=54.0, mode=Mode.SUBTRACT)
            extrude(amount=2.0, mode=Mode.SUBTRACT)
            
            # B. Central Connection REMOVED (v58)

            # A. Zigzag Geometry (Variable Amplitude Pie-Shape)
            # ... rest of the code ...
            
            # --- DEFINE UNIT GEOMETRY (Angle 0) ---
            
            # A. Zigzag Geometry (Variable Amplitude Pie-Shape)
            # Inner (R=15) Amp = 2.5
            # Outer (R=35) Amp = 6.0
            def get_amp(r):
                # Linear interpolation: 2.5 at 15 -> 6.0 at 35
                return 2.5 + (r - 15.0) * (3.5 / 20.0)

            zigzag_points = []
            # Start at Inlet (15, -2.5)
            zigzag_points.append((15.0, -2.5))
            zigzag_points.append((15.0, 2.5)) # Up to Amp
            
            # R=19
            a19 = get_amp(19.0)
            zigzag_points.append((19.0, a19))
            zigzag_points.append((19.0, -a19))
            
            # R=23
            a23 = get_amp(23.0)
            zigzag_points.append((23.0, -a23))
            zigzag_points.append((23.0, a23))
            
            # R=27
            a27 = get_amp(27.0)
            zigzag_points.append((27.0, a27))
            zigzag_points.append((27.0, -a27))
            
            # R=31
            a31 = get_amp(31.0)
            zigzag_points.append((31.0, -a31))
            zigzag_points.append((31.0, a31))
            
            # R=35 (Exit)
            a35 = get_amp(35.0)
            zigzag_points.append((35.0, a35))
            zigzag_points.append((35.0, 0.0))
            
            # --- ARRAY OPERATIONS ---
            
            # 2. INLETS (8x)
            with BuildSketch(Plane.XY.offset(18.0)):
                with PolarLocations(radius=0, count=self.num_slots):
                    with Locations((15.0, -2.5)): 
                        Circle(radius=2.0)
            extrude(amount=2.0, mode=Mode.SUBTRACT)
            
            # 3. ZIGZAGS (8x)
            # Create Unit Sketch first
            with BuildSketch() as unit_zigzag:
                 with BuildLine() as path:
                    Polyline(zigzag_points)
                 make_face(offset(path.line, amount=self.zigzag_width/2))
            
            # Array the Unit Sketch
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
                            
        return lid.part

def export_batch(body, lid):
    """Automatic Versioning and STL Export."""
    base_dir = "iterations"
    if not os.path.exists(base_dir): os.makedirs(base_dir)
    
    # Simple Versioning
    existing = []
    for d in os.listdir(base_dir):
        if d.startswith("v") and "_" in d:
            try: v_num = int(d.split("_")[0][1:])
            except: continue
            existing.append(v_num)
    next_v = max(existing) + 1 if existing else 56
    version_str = f"v{next_v:02d}"
    
    # Output Folder
    folder_name = f"{version_str}_polar_refactor_fix"
    output_dir = os.path.join(base_dir, folder_name)
    os.makedirs(output_dir)
    
    # Exports
    export_stl(body, os.path.join(output_dir, f"{version_str}_perfect_body.stl"))
    export_stl(lid, os.path.join(output_dir, f"{version_str}_replicated_lid.stl"))
    
    # Script Snapshot
    shutil.copy(__file__, os.path.join(output_dir, f"{version_str}_script_snapshot.py"))
    logger.info(f"Design saved to: {output_dir}")

if __name__ == "__main__":
    sampler = FinalCompactSampler()
    body_p = sampler.generate_static_body()
    lid_p = sampler.generate_static_lid()
    
    # Export designs automatically
    export_batch(body_p, lid_p)
    
    try:
        from ocp_vscode import show, Camera
        # Clear inspection view: Explode by 60mm
        show(body_p, lid_p.translate((0,0,60)),
             reset_camera=Camera.RESET,
             names=["Perfect Base", "8-Unit Polar Lid"])
        logger.info("Sent v56 Polar-Refactored design to OCP Viewer")
    except ImportError:
        pass
