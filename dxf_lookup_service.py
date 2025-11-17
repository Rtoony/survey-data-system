"""
DXF Lookup Service
Resolves DXF string names (layers, linetypes, styles) to database UUIDs.
"""

import psycopg2
from psycopg2.extras import RealDictCursor
from typing import Dict, Optional
import uuid


class DXFLookupService:
    """
    Resolves DXF entity names to database foreign key IDs.
    Caches lookups for performance during import/export operations.
    """
    
    def __init__(self, db_config: Dict, conn=None):
        """
        Initialize the lookup service.
        
        Args:
            db_config: Database configuration dictionary
            conn: Optional existing database connection (for transactions)
        """
        self.db_config = db_config
        self.external_conn = conn  # Use provided connection if available
        self._layer_cache = {}      # layer_name -> (layer_id, layer_standard_id)
        self._linetype_cache = {}   # linetype_name -> linetype_standard_id
        self._textstyle_cache = {}  # style_name -> text_style_id
        self._hatch_cache = {}      # pattern_name -> pattern_id
        self._dimstyle_cache = {}   # dimstyle_name -> dimstyle_id
    
    def _get_connection(self):
        """Get database connection (use external or create new)."""
        if self.external_conn:
            return self.external_conn, False  # Don't close external connection
        else:
            return psycopg2.connect(**self.db_config), True  # Close when done
    
    def get_or_create_layer(self, layer_name: str, project_id: str = None,
                           color_aci: int = 7, linetype: str = 'Continuous') -> tuple:
        """
        Get or create a layer and return (layer_id, layer_standard_id).

        Args:
            layer_name: Name of the layer
            project_id: UUID of the project (used for project-level layers)
            color_aci: AutoCAD Color Index (default: 7 = white)
            linetype: Linetype name (default: Continuous)

        Returns:
            Tuple of (layer_id UUID, layer_standard_id UUID or None)
        """
        # Check cache first (use project_id+layer_name for cache key)
        cache_key = f"{project_id}:{layer_name}"
        if cache_key in self._layer_cache:
            return self._layer_cache[cache_key]
        
        conn, should_close = self._get_connection()
        cur = conn.cursor(cursor_factory=RealDictCursor)
        
        try:
            # First, check if layer exists in layer_standards
            cur.execute("""
                SELECT layer_id, layer_name
                FROM layer_standards
                WHERE layer_name = %s
                LIMIT 1
            """, (layer_name,))
            
            layer_standard = cur.fetchone()
            layer_standard_id = layer_standard['layer_id'] if layer_standard else None

            # Check if layer exists in layers table (project-level only)
            if project_id:
                cur.execute("""
                    SELECT layer_id
                    FROM layers
                    WHERE project_id = %s AND layer_name = %s
                    LIMIT 1
                """, (project_id, layer_name))
            else:
                # Lookup without project context
                cur.execute("""
                    SELECT layer_id
                    FROM layers
                    WHERE layer_name = %s
                    LIMIT 1
                """, (layer_name,))

            layer = cur.fetchone()
            
            if layer:
                layer_id = layer['layer_id']
            else:
                # Create new layer in layers table
                if not project_id:
                    raise ValueError("project_id is required to create a new layer")

                layer_id = str(uuid.uuid4())
                cur.execute("""
                    INSERT INTO layers (
                        layer_id, project_id, layer_name, layer_standard_id,
                        color, linetype, is_frozen, is_locked,
                        quality_score, tags, attributes
                    )
                    VALUES (%s::uuid, %s::uuid, %s, %s::uuid, %s, %s, false, false, 0.5, '{}', '{}')
                """, (layer_id, project_id, layer_name, layer_standard_id, color_aci, linetype))
                
                if not self.external_conn:
                    conn.commit()
            
            # Cache the result
            result = (layer_id, layer_standard_id)
            self._layer_cache[cache_key] = result
            
            return result
            
        finally:
            cur.close()
            if should_close:
                conn.close()
    
    def get_or_create_linetype(self, linetype_name: str) -> Optional[str]:
        """
        Get or create a linetype and return its standard ID.
        
        Args:
            linetype_name: Name of the linetype
            
        Returns:
            linetype_standard_id UUID or None
        """
        # Check cache first
        if linetype_name in self._linetype_cache:
            return self._linetype_cache[linetype_name]
        
        # Standard linetypes don't need lookup
        if linetype_name in ['ByLayer', 'ByBlock', 'Continuous']:
            self._linetype_cache[linetype_name] = None
            return None
        
        conn, should_close = self._get_connection()
        cur = conn.cursor(cursor_factory=RealDictCursor)
        
        try:
            # Check if linetype exists in standards
            cur.execute("""
                SELECT linetype_id
                FROM linetypes
                WHERE linetype_name = %s AND is_active = true
                LIMIT 1
            """, (linetype_name,))
            
            linetype = cur.fetchone()
            linetype_id = linetype['linetype_id'] if linetype else None
            
            # Cache the result
            self._linetype_cache[linetype_name] = linetype_id
            
            return linetype_id
            
        finally:
            cur.close()
            if should_close:
                conn.close()
    
    def get_or_create_text_style(self, style_name: str) -> Optional[str]:
        """
        Get or create a text style and return its ID.
        
        Args:
            style_name: Name of the text style
            
        Returns:
            text_style_id UUID or None
        """
        # Check cache first
        if style_name in self._textstyle_cache:
            return self._textstyle_cache[style_name]
        
        # Standard style
        if not style_name or style_name == 'Standard':
            self._textstyle_cache[style_name] = None
            return None
        
        conn, should_close = self._get_connection()
        cur = conn.cursor(cursor_factory=RealDictCursor)
        
        try:
            # Check if text style exists
            cur.execute("""
                SELECT text_style_id
                FROM text_styles
                WHERE style_name = %s
                LIMIT 1
            """, (style_name,))
            
            style = cur.fetchone()
            style_id = style['text_style_id'] if style else None
            
            # Cache the result
            self._textstyle_cache[style_name] = style_id
            
            return style_id
            
        finally:
            cur.close()
            if should_close:
                conn.close()
    
    def get_or_create_hatch_pattern(self, pattern_name: str) -> Optional[str]:
        """
        Get or create a hatch pattern and return its ID.
        
        Args:
            pattern_name: Name of the hatch pattern
            
        Returns:
            hatch_pattern_id UUID or None
        """
        # Check cache first
        if pattern_name in self._hatch_cache:
            return self._hatch_cache[pattern_name]
        
        # SOLID hatch
        if not pattern_name or pattern_name.upper() == 'SOLID':
            self._hatch_cache[pattern_name] = None
            return None
        
        conn, should_close = self._get_connection()
        cur = conn.cursor(cursor_factory=RealDictCursor)
        
        try:
            # Check if hatch pattern exists
            cur.execute("""
                SELECT hatch_id
                FROM hatch_patterns
                WHERE pattern_name = %s
                LIMIT 1
            """, (pattern_name,))
            
            pattern = cur.fetchone()
            pattern_id = pattern['hatch_id'] if pattern else None
            
            # Cache the result
            self._hatch_cache[pattern_name] = pattern_id
            
            return pattern_id
            
        finally:
            cur.close()
            if should_close:
                conn.close()
    
    def get_or_create_dimension_style(self, dimstyle_name: str) -> Optional[str]:
        """
        Get or create a dimension style and return its ID.
        
        Args:
            dimstyle_name: Name of the dimension style
            
        Returns:
            dimension_style_id UUID or None
        """
        # Check cache first
        if dimstyle_name in self._dimstyle_cache:
            return self._dimstyle_cache[dimstyle_name]
        
        # Standard dimension style
        if not dimstyle_name or dimstyle_name == 'Standard':
            self._dimstyle_cache[dimstyle_name] = None
            return None
        
        conn, should_close = self._get_connection()
        cur = conn.cursor(cursor_factory=RealDictCursor)
        
        try:
            # Check if dimension style exists
            cur.execute("""
                SELECT dimstyle_id
                FROM dimension_styles
                WHERE dimstyle_name = %s
                LIMIT 1
            """, (dimstyle_name,))
            
            dimstyle = cur.fetchone()
            dimstyle_id = dimstyle['dimstyle_id'] if dimstyle else None
            
            # Cache the result
            self._dimstyle_cache[dimstyle_name] = dimstyle_id
            
            return dimstyle_id
            
        finally:
            cur.close()
            if should_close:
                conn.close()
    
    def record_layer_usage(self, project_id: str, layer_id: str,
                          layer_standard_id: Optional[str] = None):
        """
        Record that a project uses a specific layer.

        Note: This function is deprecated. The drawing_layer_usage table was removed
        in Migration 009. Layer usage is now tracked implicitly through entity references.

        Args:
            project_id: UUID of the project
            layer_id: UUID of the layer
            layer_standard_id: Optional UUID of the layer standard
        """
        # No-op: drawing_layer_usage table was dropped in Migration 009
        # Layer usage is tracked implicitly through entity references
        pass
    
    def record_linetype_usage(self, project_id: str, linetype_name: str,
                             linetype_standard_id: Optional[str] = None):
        """
        Record that a project uses a specific linetype.

        Note: This function is deprecated. The drawing_linetype_usage table was removed
        in Migration 009. Linetype usage is now tracked implicitly through entity references.

        Args:
            project_id: UUID of the project
            linetype_name: Name of the linetype
            linetype_standard_id: Optional UUID of the linetype standard
        """
        # No-op: drawing_linetype_usage table was dropped in Migration 009
        # Linetype usage is tracked implicitly through entity references
        pass
    
    def clear_cache(self):
        """Clear all cached lookups."""
        self._layer_cache.clear()
        self._linetype_cache.clear()
        self._textstyle_cache.clear()
        self._hatch_cache.clear()
        self._dimstyle_cache.clear()
