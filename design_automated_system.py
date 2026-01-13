import logging
import os
import shutil
from build123d import *
import math

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("AutomatedSystem")

class AutomatedSamplerSystem:
    """
    v47 Automated System.
    Includes:
    - Compressed Sampler (v46 dimensions) - FULL GEOMETRY
    - Geared Cover
    - Docking Chassis
    - Clamp Mechanism
    """
    def __init__(self):
        self.num_slots = 8
        self.cassette_radius = 55.0
        self.filter_r = 35.0
        self.zigzag_width = 3.2
        self.slot_angle = 360.0 / self.num_slots
        
        # v46 Dimensions
        self.base_h = 10.0
        self.lid_h = 6.0
        self.cover_h = 2.0
        
        # Gear Params
        self.gear_module = 1.0
        self.num_teeth = 110 # Approx for R=55
        
    def generate_geared_cover(self):
        """Cover with Gear Teeth on Rim."""
        logger.info("Generating Geared Cover.")
        base_z = self.base_h + self.lid_h # 16.0
        
        with BuildPart() as cover:
            # Main Disc
            with BuildSketch(Plane.XY.offset(base_z)):
                Circle(radius=self.cassette_radius)
            extrude(amount=self.cover_h)
            
            # Subtractions: Pivot & Selector
            with BuildSketch(Plane.XY.offset(base_z)):
                Circle(radius=2.6) # Pivot
                with Locations((15.0, -2.5)):
                    Circle(radius=1.5) # Selector
            extrude(amount=self.cover_h, mode=Mode.SUBTRACT)
            
            # Add Gear Teeth
            # Simple Trapezoidal Teeth
            with BuildSketch(Plane.XY.offset(base_z)):
                with PolarLocations(radius=self.cassette_radius, count=self.num_teeth):
                    Trapezoid(1.5, 1.5, 75, rotation=-90)
            extrude(amount=self.cover_h)
            
        return cover.part

    def generate_chassis(self):
        """Docking Base."""
        logger.info("Generating Chassis.")
        
        # Simple plate with walls
        plate_w = 140.0
        plate_l = 180.0
        
        with BuildPart() as chassis:
            # Base Plate
            with BuildSketch(Plane.XY.offset(-2.0)): # Slightly below cassette
                Rectangle(width=plate_w, height=plate_l)
                Circle(radius=8.0, mode=Mode.SUBTRACT) # Clearance hole for barb
            extrude(amount=2.0)
            
            # Cassette Nest (Ring Wall)
            with BuildSketch(Plane.XY):
                Circle(radius=self.cassette_radius + 1.0) # 1mm Clearance
                Circle(radius=self.cassette_radius - 5.0, mode=Mode.SUBTRACT) # Ledge
            extrude(amount=5.0)
            
            # Motor Mount Block 1 (Rotation)
            # Side of cassette
            with BuildSketch(Plane.XY):
                with Locations((self.cassette_radius + 15, 0)):
                    Rectangle(width=20, height=20)
            extrude(amount=10.0)
            
            # Pivot Block 2 (Clamp Hinge)
            # Rear
            with BuildSketch(Plane.XY):
                with Locations((0, self.cassette_radius + 20)):
                    Rectangle(width=40, height=20)
            extrude(amount=25.0)
            
        return chassis.part

    def generate_clamp_arm(self):
        """Clamping Arm."""
        logger.info("Generating Clamp Arm.")
        
        with BuildPart() as arm:
            # Arm Body
            with BuildSketch(Plane.XY.offset(20.0)):
                with Locations((0, (self.cassette_radius + 20)/2)):
                    Rectangle(width=15, height=(self.cassette_radius + 20))
            extrude(amount=5.0)
            
            # Pressure Pad at (0,0) center
            with BuildSketch(Plane.XY.offset(20.0)):
                Circle(radius=8.0)
            extrude(amount=-2.0, mode=Mode.ADD) # Push down to touch pivot
            
        return arm.part

    def generate_drive_gear(self):
        """Pinion Gear."""
        logger.info("Generating Drive Gear.")
        
        with BuildPart() as gear:
            with BuildSketch(Plane.XY.offset(16.0)): # Improve mesh Z
                Circle(radius=10.0)
                # Teeth
                with PolarLocations(radius=10.0, count=20):
                    Trapezoid(1.5, 1.5, 75, rotation=-90)
            extrude(amount=2.0)
        return gear.part

    def generate_full_components(self):
        """Generate FULL v46 base and lid geometry."""
        logger.info("Generating Full Base and Lid.")
        
        # --- BASE (v46) ---
        with BuildPart() as body:
            # 1. Main Disc
            with BuildSketch(Plane.XY):
                Circle(radius=self.cassette_radius)
            extrude(amount=self.base_h) # 10.0
            
            # 2. Central Shared Plenum
            with BuildSketch(Plane.XY.offset(2.0)):
                Circle(radius=8.0)
            extrude(amount=4.0, mode=Mode.SUBTRACT)
            
            # 3. Filter Seats
            with BuildSketch(Plane.XY.offset(self.base_h - 1.5)): # Z=8.5
                with PolarLocations(radius=self.filter_r, count=self.num_slots):
                    Circle(radius=25.4/2)
            extrude(amount=1.5, mode=Mode.SUBTRACT)
            
            # 4. Grid Supports
            with BuildSketch(Plane.XY.offset(self.base_h - 2.0)): # Z=8.0
                with PolarLocations(radius=self.filter_r, count=self.num_slots):
                    with PolarLocations(radius=7.5, count=6):
                        Circle(radius=3.0)
                    Circle(radius=3.0)
            extrude(amount=0.5, mode=Mode.SUBTRACT)
            
            # 5. Under-Filter Plenums
            with BuildSketch(Plane.XY.offset(2.0)):
                with PolarLocations(radius=self.filter_r, count=self.num_slots):
                    Circle(radius=22.0/2)
                    with Locations((-self.filter_r/2, 0)):
                        Rectangle(width=self.filter_r, height=8.0)
            extrude(amount=6.0, mode=Mode.SUBTRACT)
            
            # 6. Integrated Exhaust Barb
            with BuildSketch(Plane.XY):
                Circle(radius=10.0/2)
            extrude(amount=-20.0, mode=Mode.ADD)
            with BuildSketch(Plane.XY):
                Circle(radius=6.0/2)
            extrude(amount=-22.0, mode=Mode.SUBTRACT)

            # 7. MATING FEATURES
            with BuildSketch(Plane.XY.offset(self.base_h)):
                Circle(radius=self.cassette_radius)
                Circle(radius=54.0, mode=Mode.SUBTRACT)
            extrude(amount=2.0, mode=Mode.ADD)
        
        # --- LID (v46) ---
        base_z = self.base_h # 10.0
        with BuildPart() as lid:
            # 1. Main Lid Disc
            with BuildSketch(Plane.XY.offset(base_z)):
                Circle(radius=self.cassette_radius)
            extrude(amount=self.lid_h) # 6.0
            
            # Mating Recess
            with BuildSketch(Plane.XY.offset(base_z)):
                Circle(radius=self.cassette_radius)
                Circle(radius=54.0, mode=Mode.SUBTRACT)
            extrude(amount=2.0, mode=Mode.SUBTRACT)
            
            # ZIGZAG LOGIC
            def get_amp(r): return 2.5 + (r - 15.0) * (3.5 / 20.0)
            zigzag_points = []
            zigzag_points.append((15.0, -2.5)); zigzag_points.append((15.0, 2.5))
            for r_val in [19, 23, 27, 31, 35]:
                a = get_amp(r_val)
                val1 = a if r_val % 4 == 3 else -a
                if r_val == 19: zigzag_points.extend([(19, a), (19, -a)])
                elif r_val == 23: zigzag_points.extend([(23, -a), (23, a)])
                elif r_val == 27: zigzag_points.extend([(27, a), (27, -a)])
                elif r_val == 31: zigzag_points.extend([(31, -a), (31, a)])
                elif r_val == 35: zigzag_points.extend([(35, a), (35, 0.)])

            # 2. INLETS
            with BuildSketch(Plane.XY.offset(base_z + self.lid_h - 2.0)): # Z=14
                with PolarLocations(radius=0, count=self.num_slots):
                    with Locations((15.0, -2.5)): 
                        Circle(radius=2.0)
            extrude(amount=2.0, mode=Mode.SUBTRACT)
            
            # 3. ZIGZAGS
            with BuildSketch() as unit_zigzag:
                 with BuildLine() as path:
                    Polyline(zigzag_points)
                 make_face(offset(path.line, amount=self.zigzag_width/2))
            with BuildSketch(Plane.XY.offset(base_z + self.lid_h - 2.0)): # Z=14
                with PolarLocations(radius=0, count=self.num_slots):
                    add(unit_zigzag)
            extrude(amount=2.0, mode=Mode.SUBTRACT)
            
            # 4. VERTICAL CHUTES
            with BuildSketch(Plane.XY.offset(base_z)): # Z=10
                with PolarLocations(radius=0, count=self.num_slots):
                    with Locations((35.0, 0)):
                        Rectangle(width=8.0, height=self.zigzag_width, align=(Align.MIN, Align.CENTER))
            extrude(amount=4.0, mode=Mode.SUBTRACT)
            
            # 5. RETENTION RIMS
            with BuildSketch(Plane.XY.offset(base_z)):
                with PolarLocations(radius=0, count=self.num_slots):
                    with Locations((self.filter_r, 0)):
                        Circle(radius=25.2/2) 
                        Circle(radius=21.2/2, mode=Mode.SUBTRACT)
            extrude(amount=-1.5, mode=Mode.ADD) 

            # CENTRAL PIVOT
            with BuildSketch(Plane.XY.offset(base_z + self.lid_h)):
                Circle(radius=2.5) 
            extrude(amount=5.0, mode=Mode.ADD)
            
        return body.part, lid.part

def export_batch(system):
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
    
    folder_name = f"{version_str}_automated_system"
    output_dir = os.path.join(base_dir, folder_name)
    os.makedirs(output_dir)
    
    # Generate
    cover = system.generate_geared_cover()
    chassis = system.generate_chassis()
    arm = system.generate_clamp_arm()
    gear = system.generate_drive_gear()
    # USE FULL COMPONENTS NOW
    base, lid = system.generate_full_components()
    
    export_stl(cover, os.path.join(output_dir, f"{version_str}_geared_cover.stl"))
    export_stl(chassis, os.path.join(output_dir, f"{version_str}_chassis.stl"))
    export_stl(arm, os.path.join(output_dir, f"{version_str}_clamp_arm.stl"))
    export_stl(gear, os.path.join(output_dir, f"{version_str}_drive_gear.stl"))
    export_stl(base, os.path.join(output_dir, f"{version_str}_perfect_body.stl"))
    export_stl(lid, os.path.join(output_dir, f"{version_str}_lid_pivot.stl"))
    
    shutil.copy(__file__, os.path.join(output_dir, f"{version_str}_script_snapshot.py"))
    
    return version_str, (cover, chassis, arm, gear, base, lid)

if __name__ == "__main__":
    sys = AutomatedSamplerSystem()
    version, parts = export_batch(sys)
    (cover, chassis, arm, gear, base, lid) = parts
    
    try:
        from ocp_vscode import show, Camera, set_port
        set_port(3939)
        
        show(
            chassis,
            base,
            lid,
            cover, # At Z=16
            gear.translate((66, 0, 0)), # Mesh
            arm,
            names=[
                "Chassis", "Base (v46 Full)", "Lid (v46 Full)", 
                "Geared Cover", "Drive Gear", "Clamp Arm"
            ],
            colors=["silver", "blue", "cyan", "red", "gold", "orange"],
            reset_camera=Camera.RESET
        )
    except ImportError:
        pass
