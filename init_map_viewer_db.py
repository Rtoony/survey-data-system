"""
Initialize database tables for Map Viewer
"""
import psycopg2
import os
from dotenv import load_dotenv

load_dotenv()

DB_CONFIG = {
    'host': os.getenv('DB_HOST'),
    'port': os.getenv('DB_PORT', '5432'),
    'database': os.getenv('DB_NAME', 'postgres'),
    'user': os.getenv('DB_USER', 'postgres'),
    'password': os.getenv('DB_PASSWORD'),
    'sslmode': 'require',
    'connect_timeout': 10
}

def init_database():
    conn = psycopg2.connect(**DB_CONFIG)
    conn.autocommit = True
    cur = conn.cursor()
    
    print("Creating gis_layers table...")
    cur.execute("""
        CREATE TABLE IF NOT EXISTS gis_layers (
            id TEXT PRIMARY KEY,
            county_id TEXT,
            name TEXT NOT NULL,
            layer_type TEXT NOT NULL,
            url TEXT,
            layer_name TEXT,
            style JSONB,
            enabled BOOLEAN DEFAULT true,
            created_at TIMESTAMP DEFAULT NOW(),
            updated_at TIMESTAMP DEFAULT NOW()
        );
    """)
    
    print("Creating export_jobs table...")
    cur.execute("""
        CREATE TABLE IF NOT EXISTS export_jobs (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            status TEXT NOT NULL DEFAULT 'pending',
            params JSONB NOT NULL,
            download_url TEXT,
            file_size_mb DECIMAL(10,2),
            error_message TEXT,
            created_at TIMESTAMP DEFAULT NOW(),
            expires_at TIMESTAMP
        );
    """)
    
    print("Inserting initial GIS layers...")
    cur.execute("""
        INSERT INTO gis_layers (id, county_id, name, layer_type, url, layer_name, style, enabled) VALUES
        ('parcels', 'sonoma', 'Parcels', 'WFS', 'https://gis.sonomacounty.ca.gov/geoserver/wfs', 'parcels', '{"color": "#FF5733", "weight": 2, "fillOpacity": 0.1}', true),
        ('buildings', 'sonoma', 'Buildings', 'WFS', 'https://gis.sonomacounty.ca.gov/geoserver/wfs', 'buildings', '{"color": "#333333", "weight": 1, "fillOpacity": 0.6}', true),
        ('roads', 'sonoma', 'Roads', 'WFS', 'https://gis.sonomacounty.ca.gov/geoserver/wfs', 'roads', '{"color": "#FFC300", "weight": 2}', true)
        ON CONFLICT (id) DO NOTHING;
    """)
    
    print("Checking created tables...")
    cur.execute("SELECT COUNT(*) FROM gis_layers;")
    count = cur.fetchone()[0]
    print(f"gis_layers has {count} rows")
    
    cur.close()
    conn.close()
    print("Database initialization complete!")

if __name__ == '__main__':
    init_database()
