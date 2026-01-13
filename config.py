from dataclasses import dataclass

@dataclass(frozen=True)
class CassetteProfile:
    """Standard dimensions for a particulate sampling cassette."""
    outer_diameter: float = 42.0
    inner_flow_diameter: float = 34.0
    male_boss_diameter: float = 37.4
    female_socket_diameter: float = 37.2
    interface_height: float = 5.0
    wall_thickness: float = 2.0

# Predefined profiles
STANDARD_37MM = CassetteProfile()

MINIATURE_25MM = CassetteProfile(
    outer_diameter=26.0,
    inner_flow_diameter=22.0,
    male_boss_diameter=24.0,
    female_socket_diameter=24.2, # 0.2mm clearance
    interface_height=3.0,
    wall_thickness=2.0
)
