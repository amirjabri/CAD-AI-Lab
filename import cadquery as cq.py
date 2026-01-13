import cadquery as cq
from ocp_vscode import show

# Create a simple cube
box = cq.Workplane("XY").box(10, 10, 10)

# Send to viewer
show(box)