-- Upgrade geometry columns to support Z dimension
-- Fixes error: Geometry has Z dimension but column does not

BEGIN;

-- Utility Lines: LineString → LineStringZ
DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'utility_lines') THEN
        ALTER TABLE utility_lines
        ALTER COLUMN geometry TYPE geometry(LineStringZ, 2226)
        USING ST_Force3D(geometry);
        RAISE NOTICE 'Upgraded utility_lines.geometry to LineStringZ';
    END IF;
END $$;

-- Utility Structures: Point → PointZ
DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'utility_structures') THEN
        ALTER TABLE utility_structures
        ALTER COLUMN geometry TYPE geometry(PointZ, 2226)
        USING ST_Force3D(geometry);
        RAISE NOTICE 'Upgraded utility_structures.geometry to PointZ';
    END IF;
END $$;

-- Survey Points: Point → PointZ
DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'survey_points') THEN
        ALTER TABLE survey_points
        ALTER COLUMN geometry TYPE geometry(PointZ, 2226)
        USING ST_Force3D(geometry);
        RAISE NOTICE 'Upgraded survey_points.geometry to PointZ';
    END IF;
END $$;

-- Service Connections: LineString → LineStringZ
DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'utility_service_connections') THEN
        ALTER TABLE utility_service_connections
        ALTER COLUMN geometry TYPE geometry(LineStringZ, 2226)
        USING ST_Force3D(geometry);
        RAISE NOTICE 'Upgraded utility_service_connections.geometry to LineStringZ';
    END IF;
END $$;

-- Generic Objects: Geometry → GeometryZ (supports all types)
DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'generic_objects') THEN
        ALTER TABLE generic_objects
        ALTER COLUMN geometry TYPE geometry(GeometryZ, 2226)
        USING ST_Force3D(geometry);
        RAISE NOTICE 'Upgraded generic_objects.geometry to GeometryZ';
    END IF;
END $$;

COMMIT;
