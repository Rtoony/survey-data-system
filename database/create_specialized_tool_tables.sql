--
-- Create specialized tool tables for ACAD-GIS
-- Tables: bmps, street_lights, pavement_zones
-- Date: 2025-11-16
--

-- ============================================
-- BMPs (Best Management Practices) Table
-- ============================================

CREATE TABLE IF NOT EXISTS public.bmps (
    bmp_id uuid DEFAULT gen_random_uuid() NOT NULL PRIMARY KEY,
    entity_id uuid,
    project_id uuid,
    bmp_type character varying(50),  -- BIORETENTION, BIOSWALE, DETENTION, INFILTRATION
    bmp_name character varying(100),
    area_sqft numeric(10,2),
    volume_cuft numeric(10,2),
    treatment_type character varying(50),  -- FILTRATION, INFILTRATION, DETENTION
    depth_ft numeric(6,2),
    soil_type character varying(100),
    vegetation_type character varying(100),
    geometry public.geometry(Polygon, 2226),
    owner character varying(255),
    install_date date,
    condition character varying(50),
    notes text,
    quality_score numeric(3,2) DEFAULT 0.0,
    tags text[],
    attributes jsonb,
    search_vector tsvector,
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    updated_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP
);

-- Add indexes for BMPs
CREATE INDEX IF NOT EXISTS idx_bmps_project_id ON public.bmps(project_id);
CREATE INDEX IF NOT EXISTS idx_bmps_entity_id ON public.bmps(entity_id);
CREATE INDEX IF NOT EXISTS idx_bmps_bmp_type ON public.bmps(bmp_type);
CREATE INDEX IF NOT EXISTS idx_bmps_geometry ON public.bmps USING GIST(geometry);
CREATE INDEX IF NOT EXISTS idx_bmps_search ON public.bmps USING GIN(search_vector);

-- Add trigger for updated_at
CREATE OR REPLACE FUNCTION update_bmps_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_bmps_updated_at
    BEFORE UPDATE ON public.bmps
    FOR EACH ROW
    EXECUTE FUNCTION update_bmps_updated_at();

-- ============================================
-- Street Lights Table
-- ============================================

CREATE TABLE IF NOT EXISTS public.street_lights (
    light_id uuid DEFAULT gen_random_uuid() NOT NULL PRIMARY KEY,
    entity_id uuid,
    project_id uuid,
    pole_number character varying(50),
    pole_height_ft numeric(5,1),
    lamp_type character varying(50),  -- LED, HPS, MH (Metal Halide), LPS (Low Pressure Sodium)
    wattage integer,
    lumens integer,
    mounting_type character varying(50),  -- POST_TOP, ARM_MOUNT, WALL_MOUNT
    circuit_id character varying(50),
    power_source character varying(100),
    geometry public.geometry(Point, 2226),
    owner character varying(255),
    install_date date,
    condition character varying(50),
    notes text,
    quality_score numeric(3,2) DEFAULT 0.0,
    tags text[],
    attributes jsonb,
    search_vector tsvector,
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    updated_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP
);

-- Add indexes for Street Lights
CREATE INDEX IF NOT EXISTS idx_street_lights_project_id ON public.street_lights(project_id);
CREATE INDEX IF NOT EXISTS idx_street_lights_entity_id ON public.street_lights(entity_id);
CREATE INDEX IF NOT EXISTS idx_street_lights_lamp_type ON public.street_lights(lamp_type);
CREATE INDEX IF NOT EXISTS idx_street_lights_geometry ON public.street_lights USING GIST(geometry);
CREATE INDEX IF NOT EXISTS idx_street_lights_search ON public.street_lights USING GIN(search_vector);

-- Add trigger for updated_at
CREATE OR REPLACE FUNCTION update_street_lights_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_street_lights_updated_at
    BEFORE UPDATE ON public.street_lights
    FOR EACH ROW
    EXECUTE FUNCTION update_street_lights_updated_at();

-- ============================================
-- Pavement Zones Table
-- ============================================

CREATE TABLE IF NOT EXISTS public.pavement_zones (
    zone_id uuid DEFAULT gen_random_uuid() NOT NULL PRIMARY KEY,
    entity_id uuid,
    project_id uuid,
    zone_name character varying(100),
    pavement_type character varying(50),  -- ASPHALT, CONCRETE, PERMEABLE, GRAVEL, PAVER
    area_sqft numeric(10,2),
    thickness_inches numeric(4,1),
    material_spec character varying(100),
    subgrade_type character varying(50),
    structural_section character varying(100),
    traffic_category character varying(50),  -- LIGHT, MEDIUM, HEAVY
    geometry public.geometry(Polygon, 2226),
    owner character varying(255),
    install_date date,
    condition character varying(50),
    notes text,
    quality_score numeric(3,2) DEFAULT 0.0,
    tags text[],
    attributes jsonb,
    search_vector tsvector,
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    updated_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP
);

-- Add indexes for Pavement Zones
CREATE INDEX IF NOT EXISTS idx_pavement_zones_project_id ON public.pavement_zones(project_id);
CREATE INDEX IF NOT EXISTS idx_pavement_zones_entity_id ON public.pavement_zones(entity_id);
CREATE INDEX IF NOT EXISTS idx_pavement_zones_pavement_type ON public.pavement_zones(pavement_type);
CREATE INDEX IF NOT EXISTS idx_pavement_zones_geometry ON public.pavement_zones USING GIST(geometry);
CREATE INDEX IF NOT EXISTS idx_pavement_zones_search ON public.pavement_zones USING GIN(search_vector);

-- Add trigger for updated_at
CREATE OR REPLACE FUNCTION update_pavement_zones_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_pavement_zones_updated_at
    BEFORE UPDATE ON public.pavement_zones
    FOR EACH ROW
    EXECUTE FUNCTION update_pavement_zones_updated_at();

-- ============================================
-- Comments for documentation
-- ============================================

COMMENT ON TABLE public.bmps IS 'Best Management Practices for stormwater treatment and drainage';
COMMENT ON TABLE public.street_lights IS 'Street lighting infrastructure and electrical systems';
COMMENT ON TABLE public.pavement_zones IS 'Pavement areas with material specifications and structural sections';

COMMENT ON COLUMN public.bmps.bmp_type IS 'Type of BMP: BIORETENTION, BIOSWALE, DETENTION, INFILTRATION';
COMMENT ON COLUMN public.bmps.treatment_type IS 'Treatment mechanism: FILTRATION, INFILTRATION, DETENTION';
COMMENT ON COLUMN public.bmps.geometry IS 'Polygon geometry in SRID 2226 (CA State Plane Zone 2)';

COMMENT ON COLUMN public.street_lights.lamp_type IS 'Lamp technology: LED, HPS (High Pressure Sodium), MH (Metal Halide), LPS';
COMMENT ON COLUMN public.street_lights.geometry IS 'Point geometry in SRID 2226 (CA State Plane Zone 2)';

COMMENT ON COLUMN public.pavement_zones.pavement_type IS 'Pavement surface type: ASPHALT, CONCRETE, PERMEABLE, GRAVEL, PAVER';
COMMENT ON COLUMN public.pavement_zones.geometry IS 'Polygon geometry in SRID 2226 (CA State Plane Zone 2)';

-- ============================================
-- Grant permissions (adjust as needed)
-- ============================================

-- Note: Adjust these grants based on your actual user roles
-- GRANT SELECT, INSERT, UPDATE, DELETE ON public.bmps TO your_app_user;
-- GRANT SELECT, INSERT, UPDATE, DELETE ON public.street_lights TO your_app_user;
-- GRANT SELECT, INSERT, UPDATE, DELETE ON public.pavement_zones TO your_app_user;

-- ============================================
-- Verification queries
-- ============================================

-- Uncomment to verify table creation:
-- SELECT table_name FROM information_schema.tables
-- WHERE table_schema = 'public'
-- AND table_name IN ('bmps', 'street_lights', 'pavement_zones');
