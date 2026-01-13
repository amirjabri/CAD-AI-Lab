import os
from build123d import *
from viewer_setup import setup_ocp, show

def load_v28():
    setup_ocp()
    
    base_dir = "iterations/v28_flow_variants"
    
    # Common parts
    base_stl = os.path.join(base_dir, "v28_base_common.stl")
    cover_stl = os.path.join(base_dir, "v28_cover_common.stl")
    
    base_shp = import_stl(base_stl)
    cover_shp = import_stl(cover_stl)
    
    # Body variants
    variants = [
        "v28_body_1.5LPM.stl",
        "v28_body_2.0LPM.stl",
        "v28_body_2.5LPM.stl",
        "v28_body_3.0LPM.stl",
        "v28_body_3.5LPM.stl"
    ]
    
    shapes_to_show = []
    names_to_show = []
    colors_to_show = []
    
    spacing = 60.0
    
    for i, v_name in enumerate(variants):
        path = os.path.join(base_dir, v_name)
        if os.path.exists(path):
            body = import_stl(path)
            
            # Position in a row
            loc = Location((i * spacing, 0, 0))
            
            # Add Body
            shapes_to_show.append(body.move(loc))
            names_to_show.append(v_name)
            colors_to_show.append("teal")
            
            # Add Base (Common)
            shapes_to_show.append(base_shp.move(loc))
            names_to_show.append(f"Base_{i}")
            colors_to_show.append("silver")

            # Add Cover (Common) - Exploded up
            # shape.bounding_box().max.Z? Let's guess Z=40
            cover_loc = loc * Location((0,0, 40))
            shapes_to_show.append(cover_shp.move(cover_loc))
            names_to_show.append(f"Cover_{i}")
            colors_to_show.append("orange")
            
    show(*shapes_to_show, names=names_to_show, colors=colors_to_show)
    print(f"Loaded {len(variants)} variants of V28.")

if __name__ == "__main__":
    load_v28()
