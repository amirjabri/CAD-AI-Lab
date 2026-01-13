from build123d import *
from typing import Optional

class CADTemplates:
    """Library of reusable parameterized CAD components for air sampling hardware."""
    
    @staticmethod
    def nozzle_plate(diameter: float, thickness: float, nozzle_diam: float, nozzle_count: int = 1) -> Compound:
        """Creates a circular plate with precision nozzle orifices."""
        with BuildPart() as p:
            Cylinder(radius=diameter/2, height=thickness)
            with BuildSketch(Plane.XY) as s:
                if nozzle_count == 1:
                    Circle(radius=nozzle_diam/2)
                else:
                    with PolarLocations(radius=nozzle_diam*1.5, count=nozzle_count):
                        Circle(radius=nozzle_diam/2)
            extrude(amount=thickness, mode=Mode.SUBTRACT)
        return p.part

    @staticmethod
    def impaction_body(od: float, id_flow: float, height: float, 
                        boss_od: float, boss_height: float, 
                        socket_id: float, socket_depth: float) -> Compound:
        """Creates the main cylindrical housing with male/female interface fits."""
        with BuildPart() as p:
            # Main Housing
            Cylinder(radius=od/2, height=height, align=(Align.CENTER, Align.CENTER, Align.MIN))
            
            # Male Boss (Bottom Interface)
            if boss_height > 0:
                with BuildSketch(Plane.XY):
                    Circle(radius=boss_od/2)
                    Circle(radius=id_flow/2, mode=Mode.SUBTRACT)
                extrude(amount=-boss_height)
            
            # Female Socket (Top Interface)
            if socket_depth > 0:
                with BuildSketch(Plane.XY.offset(height)):
                    Circle(radius=socket_id/2)
                extrude(amount=-socket_depth, mode=Mode.SUBTRACT)
            
            # Central Flow Path
            if height > 0:
                with BuildSketch(Plane.XY):
                    Circle(radius=id_flow/2)
                extrude(amount=height, mode=Mode.SUBTRACT)
            
        return p.part

    @staticmethod
    def impaction_cup(radius: float, rim_height: float, floor_thickness: float = 2.0, 
                       wall_thickness: float = 1.0) -> Compound:
        """Creates an impaction cup (collection surface) with a raised rim."""
        with BuildPart() as p:
            Cylinder(radius=radius, height=floor_thickness, align=(Align.CENTER, Align.CENTER, Align.MIN))
            with BuildSketch(Plane.XY.offset(floor_thickness)):
                Circle(radius=radius)
                Circle(radius=radius - wall_thickness, mode=Mode.SUBTRACT)
            extrude(amount=rim_height)
        return p.part

    @staticmethod
    def add_struts(part: Compound, inner_radius: float, outer_radius: float, 
                    z_pos: float, count: int = 3, width: float = 2.0, 
                    thickness: float = 2.0) -> Compound:
        """Adds radial support struts to connect internal components to the housing wall."""
        span = outer_radius - inner_radius + 2.0 # Ensure overlap
        with BuildPart() as p:
            add(part)
            with BuildSketch(Plane.XY.offset(z_pos)):
                with PolarLocations(radius=(inner_radius + outer_radius)/2, count=count):
                    Rectangle(width=span, height=width)
            extrude(amount=thickness)
        return p.part

    @staticmethod
    def foam_chamber(od: float, id_chamber: float, height: float, 
                     boss_od: float, boss_height: float, 
                     socket_id: float, socket_depth: float) -> Compound:
        """Creates a housing for a foam pre-fractionator."""
        with BuildPart() as p:
            # Main cylindrical body
            Cylinder(radius=od/2, height=height, align=(Align.CENTER, Align.CENTER, Align.MIN))
            
            # Male Boss (Bottom)
            if boss_height > 0:
                with BuildSketch(Plane.XY):
                    Circle(radius=boss_od/2)
                    Circle(radius=id_chamber/2, mode=Mode.SUBTRACT)
                extrude(amount=-boss_height)
            
            # Female Socket (Top)
            if socket_depth > 0:
                with BuildSketch(Plane.XY.offset(height)):
                    Circle(radius=socket_id/2)
                extrude(amount=-socket_depth, mode=Mode.SUBTRACT)

            # Internal Chamber for Foam
            if height > 0:
                with BuildSketch(Plane.XY):
                    Circle(radius=id_chamber/2)
                extrude(amount=height, mode=Mode.SUBTRACT)
        return p.part

    @staticmethod
    def filter_support(od: float, id_bore: float, height: float, 
                       boss_od: float, boss_height: float, 
                       socket_id: float, socket_depth: float) -> Compound:
        """Creates a base support for a 25mm PVC filter."""
        with BuildPart() as p:
            Cylinder(radius=od/2, height=height, align=(Align.CENTER, Align.CENTER, Align.MIN))
            
            # Socket for Filter/O-Ring
            if socket_depth > 0:
                with BuildSketch(Plane.XY.offset(height)):
                    Circle(radius=socket_id/2)
                extrude(amount=-socket_depth, mode=Mode.SUBTRACT)

            # Central flow tube (outlet)
            if height > 0:
                with BuildSketch(Plane.XY):
                    Circle(radius=id_bore/2)
                extrude(amount=height, mode=Mode.SUBTRACT)
            
            # Hose Barb/Interface (Simulated as male boss for now)
            if boss_height > 0:
                with BuildSketch(Plane.XY):
                    Circle(radius=boss_od/2)
                    Circle(radius=id_bore/2, mode=Mode.SUBTRACT)
                extrude(amount=-boss_height)
        return p.part
