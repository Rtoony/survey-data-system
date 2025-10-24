"""Create a simple test DXF file for round-trip testing."""
import ezdxf

# Create new DXF document
doc = ezdxf.new('R2013')

# Add a layer
doc.layers.add('WALLS', color=1)
doc.layers.add('DIMENSIONS', color=5)
doc.layers.add('TEXT', color=3)

# Get modelspace
msp = doc.modelspace()

# Add some entities
# Line
msp.add_line((0, 0), (10, 10), dxfattribs={'layer': 'WALLS'})

# Polyline
msp.add_lwpolyline([(0, 0), (10, 0), (10, 5), (5, 5), (0, 0)], dxfattribs={'layer': 'WALLS'})

# Circle
msp.add_circle((5, 5), radius=2.5, dxfattribs={'layer': 'WALLS'})

# Arc
msp.add_arc((15, 5), radius=3, start_angle=0, end_angle=180, dxfattribs={'layer': 'WALLS'})

# Text
msp.add_text('TEST TEXT', dxfattribs={
    'layer': 'TEXT',
    'height': 0.5,
    'insert': (2, 8),
    'rotation': 0
})

# Dimension
msp.add_linear_dim(
    base=(0, -2),
    p1=(0, 0),
    p2=(10, 0),
    dimstyle='Standard',
    dxfattribs={'layer': 'DIMENSIONS'}
)

# Save
doc.saveas('test_sample.dxf')
print("✓ Created test_sample.dxf with:")
print("  - 1 Line")
print("  - 1 Polyline")
print("  - 1 Circle")
print("  - 1 Arc")
print("  - 1 Text")
print("  - 1 Dimension")
print("  - 3 Layers: WALLS, DIMENSIONS, TEXT")
