import logging
import os
import math
from build123d import *
from viewer_setup import setup_ocp, show
from agent_engine import AgenticCADSystem
from config import MINIATURE_25MM
from templates import CADTemplates
from physics_solver import PhysicsSolver

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

class HybridCassetteAgent(AgenticCADSystem):
    """Specialized agent for generating hybrid impactor/foam mini-cassettes."""
    
    def __init__(self):
        super().__init__(profile=MINIATURE_25MM)
        
    def generate_mini_hybrid(self, flow_rate_lpm: float, target_cutpoint: float):
        logger.info(f"Designing Hybrid Miniature Cassette (0.8 LPM, {target_cutpoint}um cutpoint)")
        
        # 1. Physics for the primary impactor nozzle
        constraints = self.physics.get_geometric_constraints(flow_rate_lpm, target_cutpoint)
        d_mm = constraints["nozzle_diameter_mm"]
        s_mm = constraints["jet_to_plate_mm"]
        t_mm = constraints["throat_length_mm"]
        
        # v8: Combined Upper Body (Top + Middle) for Printability & Compactness
        # Stack: 
        #   Base Interface (Lip) -> Foam (10mm) -> Gap (6mm) -> Top Plate (2mm)
        #   Total Height above interface = 18mm.
        
        upper_height = 18.0
        foam_sq_size = 15.0
        lip_id = 13.0 # Constriction to hold foam
        
        with BuildPart() as upper:
            # Main Body
            Cylinder(radius=self.profile.outer_diameter/2, height=upper_height, align=(Align.CENTER, Align.CENTER, Align.MIN))
            
            # Male Interface Boss (Bottom) - Acts as the Retention Lip
            with BuildSketch(Plane.XY):
                Circle(radius=self.profile.male_boss_diameter/2)
                # Constricted opening (Retention Lip)
                Circle(radius=lip_id/2, mode=Mode.SUBTRACT)
            extrude(amount=-self.profile.interface_height)
            
            # Internal Foam Chamber (Square)
            # Starts at Z=0 (bottom of main body, top of boss).
            # Height = 10 (Foam) + 6 (Gap) = 16mm.
            with BuildSketch(Plane.XY):
                Rectangle(width=foam_sq_size, height=foam_sq_size)
            extrude(amount=16.0, mode=Mode.SUBTRACT)
            
            # Nozzle (Top Plate)
            # Drilled from top (Z=18) down to match chamber (Z=16).
            with BuildSketch(Plane.XY.offset(upper_height)):
                Circle(radius=d_mm/2)
            extrude(amount=-2.0, mode=Mode.SUBTRACT)
            
        upper_body = upper.part

        # 4. Base Section: Filter Support with Side Barb (Support-Free)
        # v8: Added 45-degree chamfer support to barb.
        base_height = 10.0 
        
        with BuildPart() as base:
            # Main Cylindrical Body
            Cylinder(radius=self.profile.outer_diameter/2, height=base_height, align=(Align.CENTER, Align.CENTER, Align.MIN))
            
            # Filter Socket (Top)
            socket_depth = 2.0
            socket_id = 25.4 
            with BuildSketch(Plane.XY.offset(base_height)):
                Circle(radius=socket_id/2)
            extrude(amount=-socket_depth, mode=Mode.SUBTRACT)
            
            # Internal Air Chamber
            chamber_floor_z = 2.0
            chamber_ceiling_z = base_height - socket_depth
            with BuildSketch(Plane.XY.offset(chamber_floor_z)):
                Circle(radius=self.profile.inner_flow_diameter/2)
            extrude(amount=chamber_ceiling_z - chamber_floor_z, mode=Mode.SUBTRACT)
            
            # Filter Support Floor (and slots)
            internal_ceiling_z = base_height - socket_depth - 2.0
            # Recut chamber floor to define thickness
            with BuildSketch(Plane.XY.offset(chamber_floor_z)):
                Circle(radius=self.profile.inner_flow_diameter/2)
            extrude(amount=internal_ceiling_z - chamber_floor_z, mode=Mode.SUBTRACT)
            
            # Cut Airflow Slots
            with BuildSketch(Plane.XY.offset(internal_ceiling_z)):
                with PolarLocations(radius=15.0/2, count=6): 
                    SlotOverall(width=6.0, height=2.0, rotation=90)
            extrude(amount=2.0, mode=Mode.SUBTRACT)
            
            # SIDE BARB (Outlet) with Support Chamfer
            barb_z = (chamber_floor_z + internal_ceiling_z) / 2
            barb_od = 6.0
            barb_id = 3.0
            barb_len = 8.0
            
            # Barb Stem
            with BuildSketch(Plane.YZ.offset(self.profile.outer_diameter/2)):
                Circle(radius=barb_od/2)
            extrude(amount=barb_len)
            
            # Support Chamfer (Wedge)
            # Create a triangle under the barb.
            # Triangle in Plane.XZ? 
            # Vertices: (OD/2, 0, barb_z - r), (OD/2 + len, 0, barb_z - r), (OD/2, 0, barb_z - r - len) -> 45 deg?
            # Actually easier to just loft or extrude a triangle.
            # Let's use a simple wedge block intersected with the cylinder?
            # Or just sketch on Side View (Plane.XZ) and revolve? No, it's straight.
            # Sketch on Plane.XZ (Side profile).
            # Barb extends +X.
            # Triangle:
            # P1: (OD/2, barb_z - barb_od/2)  <- Under barb root
            # P2: (OD/2 + barb_len - 2, barb_z - barb_od/2) <- Under barb tip (minus tip lip)
            # P3: (OD/2, barb_z - barb_od/2 - (barb_len-2)) <- Down wall 45 deg
            
            chamfer_len = barb_len - 1.0 # Stop slightly before tip
            with BuildSketch(Plane.XZ): # X=Right, Y=Up (local) mapped to global X, Z
                Polygon([
                    (self.profile.outer_diameter/2, barb_z - barb_od/2),
                    (self.profile.outer_diameter/2 + chamfer_len, barb_z - barb_od/2),
                    (self.profile.outer_diameter/2, barb_z - barb_od/2 - chamfer_len)
                ])
            # Extrude width of the barb (e.g. barb_od)
            extrude(amount=barb_od/2, both=True)
            
            # Cut Bore through Barb
            with BuildSketch(Plane.YZ.offset(self.profile.outer_diameter/2 + barb_len)):
                Circle(radius=barb_id/2)
            extrude(amount=-(barb_len + 5.0), mode=Mode.SUBTRACT)
            
            # MOUNTING LOOP
            # Same as before
            loop_width = 8.0
            loop_thick = 5.0
            loop_protrusion = 8.0
            hole_x = -self.profile.outer_diameter/2 - loop_protrusion/2
            
            with BuildSketch(Plane.YZ.offset(-self.profile.outer_diameter/2)):
                Rectangle(width=loop_thick, height=loop_width)
            extrude(amount=-loop_protrusion)
            
            with BuildSketch(Plane.XY.offset(barb_z - loop_width/2 - 1)):
                 with Locations((hole_x, 0)):
                     Circle(radius=2.0)
            extrude(amount=loop_width + 5.0, mode=Mode.SUBTRACT)
            
        base_section = base.part

        # Return updated structure (2 parts)
        return {
            "upper": upper_body,
            "base": base_section,
            "physics": constraints,
            "metadata": {
                "flow_rate": flow_rate_lpm,
                "cutpoint": target_cutpoint,
                "nozzle_diam": d_mm,
                "design": "v8_compact_printable"
            }
        }

    def generate_badge_hybrid(self, flow_rate_lpm: float, target_cutpoint: float):
        """
        Generates v19 'Overlap Fix' Badge (55x28x9mm).
        - Increased spacing between foam and filter.
        - Simplified geometry.
        """
        logger.info(f"Designing Overlap Fix Badge (v19) (0.8 LPM, {target_cutpoint}um cutpoint)")

        # Physics
        constraints = self.physics.get_geometric_constraints(flow_rate_lpm, target_cutpoint)
        d_mm = constraints["nozzle_diameter_mm"]
        
        # Dimensions (Slim but slightly longer)
        badge_length = 55.0 
        badge_width = 32.0 
        fillet_r = 4.0
        
        base_h = 4.0 
        lid_h = 5.0
        
        # Spacing (Narrowed v33.2)
        foam_x = -22.0  # Inlet Start X
        foam_y = -10.0  # Inlet Start Y
        filter_x = 13.0
        
        # Foam (Base)
        foam_sq = 15.0
        foam_shelf_z = 1.0 # Thin floor
        
        # Filter (Lid)
        filter_od = 25.0 
        
        # 1. Base Section (4mm Thick)
        with BuildPart() as base:
            with BuildSketch(Plane.XY):
                Rectangle(width=badge_length, height=badge_width)
                fillet(vertices(), radius=fillet_r)
            extrude(amount=base_h)
            
            # 2. Narrowed Zigzag Impactor Channel (v33.2) - 6 Passes
            # Passes at X = -22.0, -18.0, -14.0, -10.0, -6.0, -2.0 (4.0mm pitch)
            compact_points = [
                (-22.0, -10.0), (-22.0, 10.0),
                (-18.0, 10.0), (-18.0, -10.0),
                (-14.0, -10.0), (-14.0, 10.0),
                (-10.0, 10.0), (-10.0, -10.0),
                (-6.0, -10.0), (-6.0, 10.0),
                (-2.0, 10.0), (-2.0, 0.0)
            ]
            
            with BuildLine(Plane.XY.offset(2.0)) as zigzag_path:
                Polyline(compact_points)
            
            with BuildSketch(Plane.XY.offset(2.0)): 
                make_face(offset(zigzag_path.line, amount=3.2/2))
            extrude(amount=2.0, mode=Mode.SUBTRACT)

            # 3. Internal Tunnel (Connects Spiral to Filter)
            base_floor_z = 0.5
            tunnel_w = (filter_x - foam_x) + 5.0
            tunnel_h = 10.0 # Slightly narrower than the seal
            with BuildSketch(Plane.XY.offset(base_floor_z)):
                with Locations(((foam_x + filter_x)/2, 0)):
                     Rectangle(width=tunnel_w, height=tunnel_h)
            extrude(amount=1.5 - base_floor_z, mode=Mode.SUBTRACT)

            # 4. Connection from Zigzag to Tunnel
            with BuildSketch(Plane.XY.offset(1.5)):
                with Locations((-2.0, 0)): # End of 6th pass
                    Rectangle(width=filter_x - (-2.0) + 1.0, height=3.2, align=(Align.MIN, Align.CENTER))
            extrude(amount=1.0, mode=Mode.SUBTRACT) 

            # Exit Hole from Tunnel to Filter (Restored in v21)
            with BuildSketch(Plane.XY.offset(base_floor_z)):
                 with Locations((filter_x, 0)):
                     Circle(radius=10.0/2)
            extrude(amount=base_h, mode=Mode.SUBTRACT)

            # Perimeter Lip (v23)
            with BuildSketch(Plane.XY.offset(base_h)):
                with BuildSketch() as s1:
                    Rectangle(width=badge_length, height=badge_width)
                    fillet(vertices(), radius=fillet_r)
                with BuildSketch(mode=Mode.SUBTRACT) as s2:
                    Rectangle(width=badge_length - 2.0, height=badge_width - 2.0)
                    fillet(vertices(), radius=fillet_r - 1.0)
            extrude(amount=1.0)

            # Internal Seal Rim (v33.2: Narrowed for Zigzag)
            with BuildSketch(Plane.XY.offset(base_h)):
                with Locations((-12.0, 0)): # Centered between -22 and -2
                    Rectangle(width=24.0, height=24.0)
                    Rectangle(width=22.0, height=22.0, mode=Mode.SUBTRACT)
            extrude(amount=1.0)

            # Filter Pinch Rim (v26) - OD 25mm, ID 23mm landing on filter edge
            with BuildSketch(Plane.XY.offset(base_h)):
                with Locations((filter_x, 0)):
                    Circle(radius=25.0/2)
                    Circle(radius=23.0/2, mode=Mode.SUBTRACT)
            extrude(amount=1.55) # Taller to reach into lid seat

        base_part = base.part
        
        # 2. Lid (Holds Filter and Nozzle)
        with BuildPart() as top:
            with BuildSketch(Plane.XY):
                Rectangle(width=badge_length, height=badge_width)
                fillet(vertices(), radius=fillet_r)
            extrude(amount=lid_h)

            # Perimeter Recess (v23)
            with BuildSketch(Plane.XY):
                with BuildSketch() as s3:
                    Rectangle(width=badge_length, height=badge_width)
                    fillet(vertices(), radius=fillet_r)
                with BuildSketch(mode=Mode.SUBTRACT) as s4:
                    Rectangle(width=badge_length - 2.4, height=badge_width - 2.4)
                    fillet(vertices(), radius=fillet_r - 1.2)
            extrude(amount=1.2, mode=Mode.SUBTRACT)

            # Internal Seal Recess (v33.2: Narrowed for Zigzag)
            with BuildSketch(Plane.XY):
                with Locations((-12.0, 0)):
                    Rectangle(width=24.4, height=24.4)
                    Rectangle(width=21.6, height=21.6, mode=Mode.SUBTRACT)
            extrude(amount=1.2, mode=Mode.SUBTRACT)

            # (PVC Filter Seal Recess removed in v26 - rim fits in existing filter seat)
            
            # A. Inlet Side (Flat for v31)
            # Recess removed to keep lid ceiling flat above zigzag

            # (Rest of geometry...)
            # Nozzle Hole (Moved to Zigzag Start)
            with BuildSketch(Plane.XY):
                with Locations((foam_x, foam_y)):
                    Circle(radius=d_mm/2)
            extrude(amount=lid_h, mode=Mode.SUBTRACT)


            # B. Filter Side
            # 1. (Receiver Socket removed in v20)
            
            # 2. Primary 25mm PVC Seat
            # Z=0 to 2.5. Deepened for Cellulose Support Pad (v35.1)
            # Gap = 2.5 - 1.55 (Pinch) = 0.95mm for 1.0mm Stack.
            with BuildSketch(Plane.XY):
                with Locations((filter_x, 0)):
                    Circle(radius=25.4/2)
            extrude(amount=2.5, mode=Mode.SUBTRACT) 

            # 3. Grid Support at Z=2.5 to 3.0 (Shifted up 1.0mm)
            with BuildSketch(Plane.XY.offset(2.5)):
                with Locations((filter_x, 0)):
                    with PolarLocations(radius=7.5, count=6):
                        Circle(radius=3.0)
                    Circle(radius=3.0)
            extrude(amount=0.5, mode=Mode.SUBTRACT)
            
            # 4. Outlet Plenum (Z=3.0 to 4.0)
            with BuildSketch(Plane.XY.offset(3.0)):
                with Locations((filter_x, 0)):
                    Circle(radius=22.0/2)
            extrude(amount=1.0, mode=Mode.SUBTRACT) # Leaves 1mm roof (Total Lid H=5, cut up to 4)
            
            # 5. Support-Free Circular Barb (v34 Refined)
            # Updated for 1/4" tubing and low resistance (v35.2)
            barb_od = 6.5 # Approx 1/4" (6.35mm) with stretch fit
            barb_id = 4.0 # Large bore for low resistance
            barb_len = 8.0 # Longer for security
            barb_z = 2.5 # Mid-height for hose alignment
            
            with BuildPart() as barb:
                # A. Support Block (Transition from side wall to tube)
                # This provides a 45-degree slope to avoid supports
                with BuildSketch(Plane.YZ.offset(badge_length/2)):
                    with Locations((0, barb_z)):
                        Rectangle(width=barb_od, height=barb_od)
                extrude(amount=1.5) # Small stub
                # Sloped chamfer underneath for printability
                chamfer(barb.edges().filter_by(Axis.X), 1.0) # Simple slope
                
                # B. Main Circular Barb (Perfectly vertical/cylindrical)
                with BuildSketch(Plane.YZ.offset(badge_length/2 + 1.5)):
                    with Locations((0, barb_z)):
                        Circle(radius=barb_od/2)
                extrude(amount=barb_len - 1.5)
                
                # C. Bore through entire assembly
                with BuildSketch(Plane.YZ.offset(filter_x)):
                    with Locations((0, barb_z)):
                        Circle(radius=barb_id/2)
                extrude(amount=badge_length/2 - filter_x + barb_len + 1.0, mode=Mode.SUBTRACT)
            
            add(barb)
            # Ensure lid is bored through to barb
            with BuildSketch(Plane.YZ.offset(filter_x)):
                with Locations((0, barb_z)):
                    Circle(radius=barb_id/2)
            extrude(amount=10.0, mode=Mode.SUBTRACT)

            # 6. Attachment Loop (v28) - opposite to barb
            loop_w = 8.0
            loop_p = 8.0
            loop_thick = lid_h
            with BuildPart() as loop:
                with BuildSketch(Plane.YZ.offset(-badge_length/2)):
                    with Locations((0, lid_h/2)):
                        Rectangle(width=loop_thick, height=loop_w)
                extrude(amount=-loop_p)
                # Hole
                with BuildSketch(Plane.XY.offset(lid_h/2)):
                    with Locations((-badge_length/2 - loop_p/2, 0)):
                        Circle(radius=4.0/2)
                extrude(amount=lid_h + 2.0, mode=Mode.SUBTRACT, both=True)
            add(loop)

        top_part = top.part
            
        return {
            "top": top_part,
            "base": base_part,
            "physics": constraints,
            "metadata": { "design": "v35_optimized_grid" }
        }


    def export_hybrid(self, data, folder="hybrid_mini_cassette"):
        import os
        
        design_version = data["metadata"].get("design", "v_unknown")
        # Create a version-specific subfolder
        export_path = os.path.join(folder, design_version)
        if not os.path.exists(export_path): os.makedirs(export_path)
        
        if "design" in data["metadata"] and (data["metadata"]["design"] == "v9_flat_badge" or data["metadata"]["design"] == "v10_ultra_flat" or data["metadata"]["design"] == "v11_3mm_foam" or data["metadata"]["design"] == "v12_ultra_compact" or data["metadata"]["design"] == "v13_inverted_stages" or data["metadata"]["design"] == "v14_standpipe" or data["metadata"]["design"] == "v15_lid_correction" or data["metadata"]["design"] == "v16_support_free" or data["metadata"]["design"] == "v17_foam_restored" or data["metadata"]["design"] == "v18_ultra_slim" or data["metadata"]["design"] == "v19_overlap_fix" or data["metadata"]["design"] == "v20_no_standpipe" or data["metadata"]["design"] == "v21_airflow_restored" or data["metadata"]["design"] == "v22_foam_support" or data["metadata"]["design"] == "v23_lip_mating" or data["metadata"]["design"] == "v24_internal_seal" or data["metadata"]["design"] == "v25_pvc_seal" or data["metadata"]["design"] == "v26_filter_pinch" or data["metadata"]["design"] == "v27_wider_walls" or data["metadata"]["design"] == "v28_attachment_loop" or data["metadata"]["design"] == "v29_spiral_impactor" or data["metadata"]["design"] == "v30_zigzag_impactor" or data["metadata"]["design"] == "v31_flat_lid" or data["metadata"]["design"] == "v32_optimized_zigzag" or data["metadata"]["design"] == "v33_compressed_zigzag" or data["metadata"]["design"] == "v33_narrow_zigzag" or data["metadata"]["design"] == "v34_support_free_barb" or data["metadata"]["design"] == "v35_optimized_grid"):
             export_stl(data["top"], os.path.join(export_path, "badge_lid_nozzle.stl"))
             export_stl(data["base"], os.path.join(export_path, "badge_base_chambers.stl"))
             logger.info(f"Badge kit ({data['metadata']['design']}) exported to {export_path}")
             return
            
        # Clean up legacy files if they exist to avoid confusion?
        # optional.
        
        logger.info(f"Hybrid kit (v8) exported to {folder}")

if __name__ == "__main__":
    try:
        if not setup_ocp():
             logger.warning("Viewer setup failed, proceeding with generation only.")
             has_viewer = False
        else:
             has_viewer = True
    except ImportError:
        has_viewer = False
        logger.warning("OCP Viewer not available")

    try:
        agent = HybridCassetteAgent()
        
        # 1. Generate Badge (4.0 LPM)
        print("Generating Badge Hybrid (4.0 LPM)...")
        badge_4 = agent.generate_badge_hybrid(4.0, 4.0)
        agent.export_hybrid(badge_4)

        # 2. Generate Badge (2.5 LPM)
        print("Generating Badge Hybrid (2.5 LPM)...")
        badge_2_5 = agent.generate_badge_hybrid(2.5, 4.0)
        agent.export_hybrid(badge_2_5)
        
        if has_viewer:
            # Visualize both side-by-side
            show(
                badge_4["base"].move(Location((0, -40, 0))), 
                badge_4["top"].move(Location((0, -40, 20))),
                badge_2_5["base"].move(Location((0, 40, 0))),
                badge_2_5["top"].move(Location((0, 40, 20))),
                names=["Base 4.0LPM", "Lid 4.0LPM", "Base 2.5LPM", "Lid 2.5LPM"],
                colors=["silver", "teal", "silver", "orange"] 
            )
            logger.info("Sent 4.0 and 2.5 LPM models to OCP Viewer")
            
    except Exception as e:
        logger.error(f"Failed: {e}")
        import traceback
        traceback.print_exc()
