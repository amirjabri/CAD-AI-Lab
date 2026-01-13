import math
from typing import Dict, Tuple

class PhysicsSolver:
    """
    Handles fluid dynamics and particle physics calculations for impactor design.
    Uses Stokes Law and Marple/Willeke empirical constants.
    """
    def __init__(self, air_viscosity: float = 1.81e-5, rho_air: float = 1.2, particle_density_kgm3: float = 1000.0):
        self.air_viscosity = air_viscosity
        self.rho_air = rho_air
        self.particle_density_kgm3 = particle_density_kgm3

    def calculate_nozzle_diameter(self, flow_rate_lpm: float, target_cutpoint_microns: float, 
                                  nozzle_count: int = 1, stk_50: float = 0.24) -> float:
        """
        Calculates the required nozzle diameter (meters) for a desired 50% cutpoint.
        
        Formula: 
        d50 = sqrt( (9 * pi * viscosity * Stk_50 * nozzle_count * W^3) / (4 * rho_p * Q) )
        Rearranged for W (nozzle diameter):
        W = [ (4 * rho_p * d50^2 * Q) / (9 * pi * viscosity * Stk_50 * nozzle_count) ]^(1/3)
        """
        q_m3s = (flow_rate_lpm / 1000.0) / 60.0
        d50_m = target_cutpoint_microns * 1e-6

        num = 4.0 * self.particle_density_kgm3 * (d50_m**2) * q_m3s
        den = 9.0 * math.pi * self.air_viscosity * stk_50 * nozzle_count
        nozzle_diam_m = (num / den) ** (1/3)
        
        return nozzle_diam_m

    def calculate_reynolds(self, flow_rate_lpm: float, nozzle_count: int, nozzle_diam_m: float) -> Tuple[float, float]:
        """Calculates the Reynolds number and jet velocity."""
        q_m3s = (flow_rate_lpm / 1000.0) / 60.0
        jet_area_m2 = nozzle_count * math.pi * (nozzle_diam_m / 2)**2
        jet_velocity = q_m3s / jet_area_m2
        re = (self.rho_air * jet_velocity * nozzle_diam_m) / self.air_viscosity
        return re, jet_velocity

    def get_geometric_constraints(self, flow_rate_lpm: float, target_cutpoint_microns: float, 
                                  nozzle_count: int = 1, s_w_ratio: float = 1.5, t_w_ratio: float = 1.0) -> Dict[str, float]:
        """Returns physical dimensions and validation metrics in millimeters."""
        d_m = self.calculate_nozzle_diameter(flow_rate_lpm, target_cutpoint_microns, nozzle_count)
        d_mm = d_m * 1000.0
        re, vel = self.calculate_reynolds(flow_rate_lpm, nozzle_count, d_m)
        
        return {
            "nozzle_diameter_mm": d_mm,
            "jet_velocity_ms": vel,
            "reynolds_number": re,
            "jet_to_plate_mm": d_mm * s_w_ratio,
            "throat_length_mm": d_mm * t_w_ratio
        }
