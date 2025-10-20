"""Quick script to explore database schema for CAD standards tables"""
import psycopg2
from psycopg2.extras import RealDictCursor
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

try:
    conn = psycopg2.connect(**DB_CONFIG)
    cur = conn.cursor(cursor_factory=RealDictCursor)
    
    # Get all tables
    cur.execute("""
        SELECT table_name 
        FROM information_schema.tables 
        WHERE table_schema = 'public'
        ORDER BY table_name
    """)
    tables = cur.fetchall()
    
    print("\n=== TABLES IN DATABASE ===\n")
    for table in tables:
        table_name = table['table_name']
        print(f"📊 {table_name}")
        
        # Get row count
        cur.execute(f"SELECT COUNT(*) as count FROM {table_name}")
        count = cur.fetchone()['count']
        print(f"   Rows: {count}")
        
        # Get columns
        cur.execute(f"""
            SELECT column_name, data_type 
            FROM information_schema.columns 
            WHERE table_name = '{table_name}' AND table_schema = 'public'
            ORDER BY ordinal_position
        """)
        columns = cur.fetchall()
        print(f"   Columns: {', '.join([c['column_name'] for c in columns])}")
        print()
    
    cur.close()
    conn.close()
    
except Exception as e:
    print(f"❌ Error: {e}")
