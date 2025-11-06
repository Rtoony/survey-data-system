"""
Pipe-Structure Spatial Connection Tool
Automatically connects pipes to structures based on spatial proximity.
"""

import os
import psycopg2
from psycopg2.extras import RealDictCursor
from typing import Dict, List, Optional, Tuple


class PipeStructureConnector:
    """Automatically connects pipes to structures based on endpoint proximity."""
    
    def __init__(self, tolerance_feet: float = 2.0):
        """
        Initialize connector with spatial tolerance.
        
        Args:
            tolerance_feet: Maximum distance in feet to snap pipe endpoint to structure
        """
        self.tolerance_feet = tolerance_feet
    
    def get_db_connection(self):
        """Create database connection."""
        return psycopg2.connect(
            host=os.environ.get('PGHOST', 'localhost'),
            port=os.environ.get('PGPORT', '5432'),
            database=os.environ.get('PGDATABASE', 'postgres'),
            user=os.environ.get('PGUSER', 'postgres'),
            password=os.environ.get('PGPASSWORD', '')
        )
    
    def connect_network_pipes(self, network_id: str) -> Dict:
        """
        Connect all pipes in a network to nearby structures.
        
        Args:
            network_id: The pipe network UUID
            
        Returns:
            Dictionary with connection results
        """
        conn = self.get_db_connection()
        
        try:
            # Get all pipes and structures in this network
            pipes = self._get_network_pipes(conn, network_id)
            structures = self._get_network_structures(conn, network_id)
            
            connected_count = 0
            unconnected_start = []
            unconnected_end = []
            
            for pipe in pipes:
                from_struct = self._find_nearest_structure(
                    pipe['start_point'], 
                    structures, 
                    self.tolerance_feet
                )
                to_struct = self._find_nearest_structure(
                    pipe['end_point'], 
                    structures, 
                    self.tolerance_feet
                )
                
                # Preserve existing connections if no new structure found
                new_from_id = from_struct['structure_id'] if from_struct else pipe['from_structure_id']
                new_to_id = to_struct['structure_id'] if to_struct else pipe['to_structure_id']
                
                # Update pipe connections
                updated = self._update_pipe_connections(
                    conn, 
                    pipe['line_id'],
                    new_from_id,
                    new_to_id
                )
                
                if updated:
                    if from_struct and to_struct:
                        connected_count += 1
                    else:
                        if not from_struct:
                            unconnected_start.append(pipe['line_number'] or pipe['line_id'])
                        if not to_struct:
                            unconnected_end.append(pipe['line_number'] or pipe['line_id'])
            
            conn.close()
            
            return {
                'success': True,
                'total_pipes': len(pipes),
                'fully_connected': connected_count,
                'partially_connected': len(unconnected_start) + len(unconnected_end),
                'unconnected_start': unconnected_start[:10],  # First 10
                'unconnected_end': unconnected_end[:10],
                'tolerance_feet': self.tolerance_feet
            }
            
        except Exception as e:
            conn.close()
            return {
                'success': False,
                'error': str(e)
            }
    
    def _get_network_pipes(self, conn, network_id: str) -> List[Dict]:
        """Get all pipes in a network with their geometries."""
        cur = conn.cursor(cursor_factory=RealDictCursor)
        
        cur.execute("""
            SELECT 
                ul.line_id,
                ul.line_number,
                ul.from_structure_id,
                ul.to_structure_id,
                ST_StartPoint(ul.geometry) as start_geom,
                ST_EndPoint(ul.geometry) as end_geom,
                ST_X(ST_StartPoint(ul.geometry)) as start_x,
                ST_Y(ST_StartPoint(ul.geometry)) as start_y,
                ST_X(ST_EndPoint(ul.geometry)) as end_x,
                ST_Y(ST_EndPoint(ul.geometry)) as end_y
            FROM utility_lines ul
            INNER JOIN utility_network_memberships unm ON ul.line_id = unm.line_id
            WHERE unm.network_id = %s
        """, (network_id,))
        
        pipes = []
        for row in cur.fetchall():
            pipes.append({
                'line_id': str(row['line_id']),
                'line_number': row['line_number'],
                'from_structure_id': str(row['from_structure_id']) if row['from_structure_id'] else None,
                'to_structure_id': str(row['to_structure_id']) if row['to_structure_id'] else None,
                'start_point': (row['start_x'], row['start_y']),
                'end_point': (row['end_x'], row['end_y'])
            })
        
        cur.close()
        return pipes
    
    def _get_network_structures(self, conn, network_id: str) -> List[Dict]:
        """Get all structures in a network with their geometries."""
        cur = conn.cursor(cursor_factory=RealDictCursor)
        
        cur.execute("""
            SELECT 
                us.structure_id,
                us.structure_number,
                us.structure_type,
                ST_X(us.rim_geometry) as x,
                ST_Y(us.rim_geometry) as y
            FROM utility_structures us
            INNER JOIN utility_network_memberships unm ON us.structure_id = unm.structure_id
            WHERE unm.network_id = %s
        """, (network_id,))
        
        structures = []
        for row in cur.fetchall():
            structures.append({
                'structure_id': str(row['structure_id']),
                'structure_number': row['structure_number'],
                'structure_type': row['structure_type'],
                'point': (row['x'], row['y'])
            })
        
        cur.close()
        return structures
    
    def _find_nearest_structure(
        self, 
        point: Tuple[float, float], 
        structures: List[Dict],
        tolerance: float
    ) -> Optional[Dict]:
        """
        Find the nearest structure to a point within tolerance.
        
        Args:
            point: (x, y) coordinates
            structures: List of structure dictionaries
            tolerance: Maximum distance in feet
            
        Returns:
            Nearest structure dictionary or None
        """
        if not structures:
            return None
        
        nearest = None
        min_distance = float('inf')
        
        for struct in structures:
            distance = self._calculate_distance(point, struct['point'])
            if distance < min_distance and distance <= tolerance:
                min_distance = distance
                nearest = struct
        
        return nearest
    
    def _calculate_distance(
        self, 
        point1: Tuple[float, float], 
        point2: Tuple[float, float]
    ) -> float:
        """Calculate Euclidean distance between two points."""
        dx = point1[0] - point2[0]
        dy = point1[1] - point2[1]
        return (dx**2 + dy**2)**0.5
    
    def _update_pipe_connections(
        self,
        conn,
        line_id: str,
        from_structure_id: Optional[str],
        to_structure_id: Optional[str]
    ) -> bool:
        """
        Update pipe from/to structure connections.
        Note: Caller should pass existing IDs when no new structure found.
        """
        cur = conn.cursor()
        
        try:
            cur.execute("""
                UPDATE utility_lines
                SET from_structure_id = %s,
                    to_structure_id = %s
                WHERE line_id = %s
            """, (from_structure_id, to_structure_id, line_id))
            
            conn.commit()
            cur.close()
            return True
            
        except Exception as e:
            print(f"Error updating pipe connections: {e}")
            conn.rollback()
            cur.close()
            return False


def test_connector():
    """Test function to run connector on first network."""
    connector = PipeStructureConnector(tolerance_feet=5.0)
    
    conn = connector.get_db_connection()
    cur = conn.cursor()
    
    # Get first network
    cur.execute("SELECT network_id FROM pipe_networks LIMIT 1")
    result = cur.fetchone()
    
    if result:
        network_id = str(result[0])
        print(f"Testing connector on network: {network_id}")
        
        results = connector.connect_network_pipes(network_id)
        
        print("\n" + "="*60)
        print("CONNECTION RESULTS")
        print("="*60)
        print(f"Total pipes: {results.get('total_pipes', 0)}")
        print(f"Fully connected: {results.get('fully_connected', 0)}")
        print(f"Partially connected: {results.get('partially_connected', 0)}")
        print(f"Tolerance: {results.get('tolerance_feet', 0)} feet")
        
        if results.get('unconnected_start'):
            print(f"\nUnconnected starts: {results['unconnected_start']}")
        if results.get('unconnected_end'):
            print(f"Unconnected ends: {results['unconnected_end']}")
    
    cur.close()
    conn.close()


if __name__ == '__main__':
    test_connector()
