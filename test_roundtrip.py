"""
Test DXF round-trip: Import → Database → Export
"""
import os
import ezdxf
import uuid
from dxf_importer import DXFImporter
from dxf_exporter import DXFExporter

# Database configuration - use DATABASE_URL for Replit/Neon database
import psycopg2
from urllib.parse import urlparse

DATABASE_URL = os.getenv('DATABASE_URL')
if DATABASE_URL:
    parsed = urlparse(DATABASE_URL)
    DB_CONFIG = {
        'host': parsed.hostname,
        'port': parsed.port or 5432,
        'dbname': parsed.path[1:],  # Remove leading /
        'user': parsed.username,
        'password': parsed.password,
        'sslmode': 'require'
    }
else:
    DB_CONFIG = {
        'host': os.getenv('DB_HOST', 'localhost'),
        'port': int(os.getenv('DB_PORT', 5432)),
        'dbname': os.getenv('DB_NAME', 'postgres'),
        'user': os.getenv('DB_USER', 'postgres'),
        'password': os.getenv('DB_PASSWORD', ''),
        'sslmode': os.getenv('DB_SSL_MODE', 'require')
    }

def test_roundtrip():
    """Test complete DXF round-trip workflow."""
    print("=== DXF Round-Trip Test ===\n")
    
    # Define file paths
    input_dxf = "test_sample.dxf"
    output_dxf = "test_output.dxf"
    drawing_id = "10498e54-74a4-4913-bbc6-10710b10a463"  # Use existing test drawing UUID
    
    # Step 1: Import DXF to database
    print(f"Step 1: Importing {input_dxf} to database...")
    importer = DXFImporter(DB_CONFIG)
    import_result = importer.import_dxf(input_dxf, drawing_id)
    
    print(f"  Import Results:")
    print(f"  - Entities: {import_result['entities']}")
    print(f"  - Text: {import_result['text']}")
    print(f"  - Dimensions: {import_result['dimensions']}")
    print(f"  - Hatches: {import_result['hatches']}")
    print(f"  - Layers: {import_result['layers']}")
    
    if import_result['errors']:
        print(f"  - Errors: {import_result['errors']}")
    
    # Step 2: Export from database to DXF
    print(f"\nStep 2: Exporting drawing {drawing_id} to {output_dxf}...")
    exporter = DXFExporter(DB_CONFIG)
    export_result = exporter.export_dxf(
        drawing_id=drawing_id,
        output_path=output_dxf,
        dxf_version='AC1027'
    )
    
    print(f"  Export Results:")
    print(f"  - Entities: {export_result['entities']}")
    print(f"  - Text: {export_result['text']}")
    print(f"  - Dimensions: {export_result['dimensions']}")
    print(f"  - Hatches: {export_result['hatches']}")
    print(f"  - Layers: {export_result['layers']}")
    
    if export_result['errors']:
        print(f"  - Errors: {export_result['errors']}")
    
    # Step 3: Verify exported file
    print(f"\nStep 3: Verifying exported DXF file...")
    if os.path.exists(output_dxf):
        doc = ezdxf.readfile(output_dxf)
        msp = doc.modelspace()
        
        entity_count = len(list(msp))
        layer_count = len(doc.layers)
        
        print(f"  - Exported file exists: ✓")
        print(f"  - Modelspace entities: {entity_count}")
        print(f"  - Layers in DXF: {layer_count}")
        
        # List entity types
        entity_types = {}
        for entity in msp:
            entity_type = entity.dxftype()
            entity_types[entity_type] = entity_types.get(entity_type, 0) + 1
        
        print(f"  - Entity types:")
        for etype, count in entity_types.items():
            print(f"    * {etype}: {count}")
        
        print(f"\n  - Layers:")
        for layer in doc.layers:
            print(f"    * {layer.dxf.name}")
        
        print(f"\n✅ Round-trip test completed successfully!")
        print(f"   Input: {input_dxf}")
        print(f"   Output: {output_dxf}")
        
    else:
        print(f"  ❌ Exported file not found!")
    
if __name__ == '__main__':
    test_roundtrip()
