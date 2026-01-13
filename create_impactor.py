import logging
import os
from typing import List
from agent_engine import AgenticCADSystem
from config import STANDARD_37MM

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

def create_multi_stage_impactor(flow_rate: float, cutpoints: List[float], output_root: str = "generated_impactors"):
    """
    Orchestrates the creation of a multi-stage impactor system.
    Calculates physics and generates CAD for each stage sequentially.
    """
    agent = AgenticCADSystem(profile=STANDARD_37MM)
    
    # Create a unique project folder
    project_name = f"impactor_{flow_rate}LPM_" + "_".join(map(str, cutpoints))
    project_dir = os.path.join(output_root, project_name)
    
    if not os.path.exists(project_dir):
        os.makedirs(project_dir)
    
    logger.info(f"=== Starting Multi-Stage Generation: {project_name} ===")
    
    for i, cp in enumerate(cutpoints):
        stage_label = f"stage_{i+1}_{cp}um"
        stage_dir = os.path.join(project_dir, stage_label)
        
        result = agent.generate_impactor_stage(flow_rate, cp, stage_name=stage_label)
        agent.export_stage(result, folder=stage_dir)
        
    logger.info("=== All stages generated successfully ===")

if __name__ == "__main__":
    # Example: 3-stage impactor (10um, 5um, 2.5um) at 4 LPM
    create_multi_stage_impactor(flow_rate=4.0, cutpoints=[10.0, 5.0, 2.5])
