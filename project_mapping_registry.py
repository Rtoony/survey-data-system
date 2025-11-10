"""
Project Mapping Registry
Metadata-driven configuration for project-entity mapping tables
"""

PROJECT_MAPPING_REGISTRY = {
    'clients': {
        'table_name': 'project_clients',
        'mapping_id_column': 'mapping_id',
        'entity_id_column': 'client_id',
        'entity_table': 'clients',
        'entity_pk': 'client_id',
        'display_name': 'Client',
        'display_name_plural': 'Clients',
        'display_fields': ['client_name', 'contact_name', 'contact_email', 'contact_phone'],
        'list_query': """
            SELECT 
                pc.mapping_id,
                pc.client_id,
                c.client_name,
                c.contact_name,
                c.contact_email,
                c.contact_phone,
                c.city,
                c.state,
                pc.is_primary,
                pc.relationship_notes,
                pc.display_order,
                pc.created_at,
                pc.updated_at
            FROM project_clients pc
            JOIN clients c ON pc.client_id = c.client_id
            WHERE pc.project_id = %s
              AND pc.is_active = true
            ORDER BY pc.is_primary DESC, pc.display_order, c.client_name
        """,
        'available_query': """
            SELECT 
                client_id,
                client_name,
                contact_name,
                contact_email,
                contact_phone,
                city,
                state
            FROM clients
            WHERE is_active = true
              AND client_id NOT IN (
                  SELECT client_id 
                  FROM project_clients 
                  WHERE project_id = %s AND is_active = true
              )
            ORDER BY client_name
        """
    },
    
    'vendors': {
        'table_name': 'project_vendors',
        'mapping_id_column': 'mapping_id',
        'entity_id_column': 'vendor_id',
        'entity_table': 'vendors',
        'entity_pk': 'vendor_id',
        'display_name': 'Vendor',
        'display_name_plural': 'Vendors',
        'display_fields': ['vendor_name', 'contact_name', 'contact_email', 'contact_phone'],
        'list_query': """
            SELECT 
                pv.mapping_id,
                pv.vendor_id,
                v.vendor_name,
                v.contact_name,
                v.contact_email,
                v.contact_phone,
                v.specialty,
                v.city,
                v.state,
                pv.is_primary,
                pv.relationship_notes,
                pv.display_order,
                pv.created_at,
                pv.updated_at
            FROM project_vendors pv
            JOIN vendors v ON pv.vendor_id = v.vendor_id
            WHERE pv.project_id = %s
              AND pv.is_active = true
            ORDER BY pv.is_primary DESC, pv.display_order, v.vendor_name
        """,
        'available_query': """
            SELECT 
                vendor_id,
                vendor_name,
                contact_name,
                contact_email,
                contact_phone,
                specialty,
                city,
                state
            FROM vendors
            WHERE is_active = true
              AND vendor_id NOT IN (
                  SELECT vendor_id 
                  FROM project_vendors 
                  WHERE project_id = %s AND is_active = true
              )
            ORDER BY vendor_name
        """
    },
    
    'municipalities': {
        'table_name': 'project_municipalities',
        'mapping_id_column': 'mapping_id',
        'entity_id_column': 'municipality_id',
        'entity_table': 'municipalities',
        'entity_pk': 'municipality_id',
        'display_name': 'Municipality',
        'display_name_plural': 'Municipalities',
        'display_fields': ['municipality_name', 'county', 'state', 'permit_portal_url'],
        'list_query': """
            SELECT 
                pm.mapping_id,
                pm.municipality_id,
                m.municipality_name,
                m.municipality_type,
                m.county,
                m.state,
                m.permit_portal_url,
                m.cad_standards_url,
                pm.is_primary,
                pm.relationship_notes,
                pm.display_order,
                pm.created_at,
                pm.updated_at
            FROM project_municipalities pm
            JOIN municipalities m ON pm.municipality_id = m.municipality_id
            WHERE pm.project_id = %s
              AND pm.is_active = true
            ORDER BY pm.is_primary DESC, pm.display_order, m.municipality_name
        """,
        'available_query': """
            SELECT 
                municipality_id,
                municipality_name,
                municipality_type,
                county,
                state,
                permit_portal_url,
                cad_standards_url
            FROM municipalities
            WHERE is_active = true
              AND municipality_id NOT IN (
                  SELECT municipality_id 
                  FROM project_municipalities 
                  WHERE project_id = %s AND is_active = true
              )
            ORDER BY municipality_name
        """
    },
    
    'coordinate_systems': {
        'table_name': 'project_coordinate_systems',
        'mapping_id_column': 'mapping_id',
        'entity_id_column': 'system_id',
        'entity_table': 'coordinate_systems',
        'entity_pk': 'system_id',
        'display_name': 'Coordinate System',
        'display_name_plural': 'Coordinate Systems',
        'display_fields': ['system_name', 'epsg_code', 'datum', 'units'],
        'list_query': """
            SELECT 
                pcs.mapping_id,
                pcs.system_id,
                cs.system_name,
                cs.epsg_code,
                cs.datum,
                cs.units,
                cs.zone_number,
                cs.region,
                pcs.is_primary,
                pcs.relationship_notes,
                pcs.display_order,
                pcs.created_at,
                pcs.updated_at
            FROM project_coordinate_systems pcs
            JOIN coordinate_systems cs ON pcs.system_id = cs.system_id
            WHERE pcs.project_id = %s
              AND pcs.is_active = true
            ORDER BY pcs.is_primary DESC, pcs.display_order, cs.system_name
        """,
        'available_query': """
            SELECT 
                system_id,
                system_name,
                epsg_code,
                datum,
                units,
                zone_number,
                region
            FROM coordinate_systems
            WHERE is_active = true
              AND system_id NOT IN (
                  SELECT system_id 
                  FROM project_coordinate_systems 
                  WHERE project_id = %s AND is_active = true
              )
            ORDER BY system_name
        """
    },
    
    'survey_point_descriptions': {
        'table_name': 'project_survey_point_descriptions',
        'mapping_id_column': 'mapping_id',
        'entity_id_column': 'description_id',
        'entity_table': 'survey_point_descriptions',
        'entity_pk': 'description_id',
        'display_name': 'Survey Point Description',
        'display_name_plural': 'Survey Point Descriptions',
        'display_fields': ['code', 'description', 'category', 'discipline'],
        'list_query': """
            SELECT 
                pspd.mapping_id,
                pspd.description_id,
                spd.code,
                spd.description,
                spd.category,
                spd.discipline,
                spd.symbol_reference,
                spd.layer_suggestion,
                pspd.is_primary,
                pspd.relationship_notes,
                pspd.display_order,
                pspd.created_at,
                pspd.updated_at
            FROM project_survey_point_descriptions pspd
            JOIN survey_point_descriptions spd ON pspd.description_id = spd.description_id
            WHERE pspd.project_id = %s
              AND pspd.is_active = true
            ORDER BY pspd.is_primary DESC, pspd.display_order, spd.code
        """,
        'available_query': """
            SELECT 
                description_id,
                code,
                description,
                category,
                discipline,
                symbol_reference,
                layer_suggestion
            FROM survey_point_descriptions
            WHERE is_active = true
              AND description_id NOT IN (
                  SELECT description_id 
                  FROM project_survey_point_descriptions 
                  WHERE project_id = %s AND is_active = true
              )
            ORDER BY code
        """
    },
    
    'gis_layers': {
        'table_name': 'project_gis_layers',
        'mapping_id_column': 'mapping_id',
        'entity_id_column': 'layer_id',
        'entity_table': 'gis_data_layers',
        'entity_pk': 'layer_id',
        'display_name': 'GIS Data Layer',
        'display_name_plural': 'GIS Data Layers',
        'display_fields': ['name', 'jurisdiction', 'category', 'rest_url'],
        'list_query': """
            SELECT 
                pgl.mapping_id,
                pgl.layer_id,
                gdl.name,
                gdl.jurisdiction,
                gdl.category,
                gdl.rest_url,
                gdl.status,
                pgl.is_primary,
                pgl.relationship_notes,
                pgl.display_order,
                pgl.created_at,
                pgl.updated_at
            FROM project_gis_layers pgl
            JOIN gis_data_layers gdl ON pgl.layer_id = gdl.layer_id
            WHERE pgl.project_id = %s
              AND pgl.is_active = true
            ORDER BY pgl.is_primary DESC, pgl.display_order, gdl.name
        """,
        'available_query': """
            SELECT 
                layer_id,
                name,
                jurisdiction,
                category,
                rest_url,
                status
            FROM gis_data_layers
            WHERE is_active = true
              AND layer_id NOT IN (
                  SELECT layer_id 
                  FROM project_gis_layers 
                  WHERE project_id = %s AND is_active = true
              )
            ORDER BY name
        """
    }
}


def get_entity_config(entity_type):
    """Get configuration for entity type or raise ValueError"""
    if entity_type not in PROJECT_MAPPING_REGISTRY:
        raise ValueError(f"Invalid entity type: {entity_type}")
    return PROJECT_MAPPING_REGISTRY[entity_type]


def get_supported_entity_types():
    """Get list of all supported entity types"""
    return list(PROJECT_MAPPING_REGISTRY.keys())
