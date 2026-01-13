import logging
import os
from typing import Dict, Any, List

from build123d import *
from physics_solver import PhysicsSolver
from templates import CADTemplates
from config import CassetteProfile, STANDARD_37MM

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

class AgenticCADSystem:
    """Orchestrates physics calculations and CAD generation using a profile-based approach."""
    
    def __init__(self, profile: CassetteProfile = STANDARD_37MM):
        self.profile = profile
        self.physics = PhysicsSolver()
        self.templates = CADTemplates()
        
    def generate_impactor_stage(self, flow_rate_lpm: float, target_cutpoint: float, 
                                stage_name: str = "stage") -> Dict[str, Any]:
        """Generates a complete impactor stage assembly and its nozzle plate."""
        logger.info(f"Generating stage: {stage_name} (Cutpoint: {target_cutpoint}um at {flow_rate_lpm}LPM)")
        
        constraints = self.physics.get_geometric_constraints(flow_rate_lpm, target_cutpoint)
        d_mm = constraints["nozzle_diameter_mm"]
        s_mm = constraints["jet_to_plate_mm"]
        t_mm = constraints["throat_length_mm"]
        
        logger.info(f"Physics Results -> Nozzle: {d_mm:.3f}mm, S-distance: {s_mm:.2f}mm")

        # 1. Nozzle Plate
        # Uses female socket diameter for a drop-in fit
        nozzle_plate = self.templates.nozzle_plate(
            diameter=self.profile.female_socket_diameter,
            thickness=t_mm,
            nozzle_diam=d_mm
        )

        # 2. Body
        # Body height is derived from S-distance + safety margin for the cup and flow
        clearance_margin = 10.0
        body_height = s_mm + clearance_margin
        
        body = self.templates.impaction_body(
            od=self.profile.outer_diameter,
            id_flow=self.profile.inner_flow_diameter,
            height=body_height,
            boss_od=self.profile.male_boss_diameter,
            boss_height=self.profile.interface_height,
            socket_id=self.profile.female_socket_diameter,
            socket_depth=self.profile.interface_height
        )

        # 3. Impaction Cup
        # Rule of thumb: Cup radius ~ 3x nozzle diameter
        cup_radius = d_mm * 3.0
        cup = self.templates.impaction_cup(radius=cup_radius, rim_height=3.0)

        # 4. Assembly Logic
        # Nozzle exit is flush with the bottom of the internal socket
        nozzle_exit_z = body_height - self.profile.interface_height
        cup_floor_z = nozzle_exit_z - s_mm
        
        cup_placed = cup.move(Location((0, 0, cup_floor_z)))
        
        # Combine and add supports
        stage_assembly = body + cup_placed
        stage_assembly = self.templates.add_struts(
            stage_assembly,
            inner_radius=cup_radius,
            outer_radius=self.profile.inner_flow_diameter / 2,
            z_pos=cup_floor_z,
            count=3
        )

        return {
            "assembly": stage_assembly,
            "nozzle": nozzle_plate,
            "constraints": constraints,
            "metadata": {
                "stage_name": stage_name,
                "body_height": body_height,
                "cup_floor_z": cup_floor_z
            }
        }

    def export_stage(self, stage_data: Dict[str, Any], folder: str = "output") -> None:
        """Exports the assembly and nozzle to STL files."""
        if not os.path.exists(folder):
            os.makedirs(folder)
            
        name = stage_data["metadata"]["stage_name"]
        body_path = os.path.join(folder, f"{name}_body.stl")
        nozzle_path = os.path.join(folder, f"{name}_nozzle.stl")
        
        export_stl(stage_data["assembly"], body_path)
        export_stl(stage_data["nozzle"], nozzle_path)
        logger.info(f"STLs exported successfully to: {folder}")

if __name__ == "__main__":
    # Test execution
    agent = AgenticCADSystem()
    result = agent.generate_impactor_stage(4.0, 5.0, stage_name="refactored_test")
    agent.export_stage(result)
