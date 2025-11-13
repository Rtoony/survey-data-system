--
-- PostgreSQL database dump
--

-- Dumped from database version 16.9 (165f042)
-- Dumped by pg_dump version 16.9

SET statement_timeout = 0;
SET lock_timeout = 0;
SET idle_in_transaction_session_timeout = 0;
SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;
SELECT pg_catalog.set_config('search_path', '', false);
SET check_function_bodies = false;
SET xmloption = content;
SET client_min_messages = warning;
SET row_security = off;

--
-- Name: pg_trgm; Type: EXTENSION; Schema: -; Owner: -
--

CREATE EXTENSION IF NOT EXISTS pg_trgm WITH SCHEMA public;


--
-- Name: EXTENSION pg_trgm; Type: COMMENT; Schema: -; Owner: -
--

COMMENT ON EXTENSION pg_trgm IS 'text similarity measurement and index searching based on trigrams';


--
-- Name: postgis; Type: EXTENSION; Schema: -; Owner: -
--

CREATE EXTENSION IF NOT EXISTS postgis WITH SCHEMA public;


--
-- Name: EXTENSION postgis; Type: COMMENT; Schema: -; Owner: -
--

COMMENT ON EXTENSION postgis IS 'PostGIS geometry and geography spatial types and functions';


--
-- Name: uuid-ossp; Type: EXTENSION; Schema: -; Owner: -
--

CREATE EXTENSION IF NOT EXISTS "uuid-ossp" WITH SCHEMA public;


--
-- Name: EXTENSION "uuid-ossp"; Type: COMMENT; Schema: -; Owner: -
--

COMMENT ON EXTENSION "uuid-ossp" IS 'generate universally unique identifiers (UUIDs)';


--
-- Name: vector; Type: EXTENSION; Schema: -; Owner: -
--

CREATE EXTENSION IF NOT EXISTS vector WITH SCHEMA public;


--
-- Name: EXTENSION vector; Type: COMMENT; Schema: -; Owner: -
--

COMMENT ON EXTENSION vector IS 'vector data type and ivfflat and hnsw access methods';


--
-- Name: abbrev_search_trigger(); Type: FUNCTION; Schema: public; Owner: -
--

CREATE FUNCTION public.abbrev_search_trigger() RETURNS trigger
    LANGUAGE plpgsql
    AS $$
BEGIN
    NEW.search_vector := 
        setweight(to_tsvector('english', COALESCE(NEW.abbreviation, '')), 'A') ||
        setweight(to_tsvector('english', COALESCE(NEW.full_text, '')), 'A') ||
        setweight(to_tsvector('english', COALESCE(NEW.context_usage, '')), 'B');
    RETURN NEW;
END;
$$;


--
-- Name: alignpi_search_trigger(); Type: FUNCTION; Schema: public; Owner: -
--

CREATE FUNCTION public.alignpi_search_trigger() RETURNS trigger
    LANGUAGE plpgsql
    AS $$
BEGIN
    NEW.search_vector := setweight(to_tsvector('english', COALESCE(NEW.notes, '')), 'A');
    RETURN NEW;
END;
$$;


--
-- Name: annotation_search_trigger(); Type: FUNCTION; Schema: public; Owner: -
--

CREATE FUNCTION public.annotation_search_trigger() RETURNS trigger
    LANGUAGE plpgsql
    AS $$
BEGIN
    NEW.search_vector := 
        setweight(to_tsvector('english', COALESCE(NEW.annotation_name, '')), 'A') ||
        setweight(to_tsvector('english', COALESCE(NEW.annotation_type, '')), 'B') ||
        setweight(to_tsvector('english', COALESCE(NEW.description, '')), 'B');
    RETURN NEW;
END;
$$;


--
-- Name: block_search_trigger(); Type: FUNCTION; Schema: public; Owner: -
--

CREATE FUNCTION public.block_search_trigger() RETURNS trigger
    LANGUAGE plpgsql
    AS $$
BEGIN
    NEW.search_vector := setweight(to_tsvector('english', COALESCE(NEW.block_name, '')), 'A');
    RETURN NEW;
END;
$$;


--
-- Name: category_search_trigger(); Type: FUNCTION; Schema: public; Owner: -
--

CREATE FUNCTION public.category_search_trigger() RETURNS trigger
    LANGUAGE plpgsql
    AS $$
BEGIN
    NEW.search_vector := 
        setweight(to_tsvector('english', COALESCE(NEW.category_name, '')), 'A') ||
        setweight(to_tsvector('english', COALESCE(NEW.category_code, '')), 'A') ||
        setweight(to_tsvector('english', COALESCE(NEW.description, '')), 'B');
    RETURN NEW;
END;
$$;


--
-- Name: code_search_trigger(); Type: FUNCTION; Schema: public; Owner: -
--

CREATE FUNCTION public.code_search_trigger() RETURNS trigger
    LANGUAGE plpgsql
    AS $$
BEGIN
    NEW.search_vector := 
        setweight(to_tsvector('english', COALESCE(NEW.code_name, '')), 'A') ||
        setweight(to_tsvector('english', COALESCE(NEW.code_number, '')), 'A') ||
        setweight(to_tsvector('english', COALESCE(NEW.description, '')), 'B') ||
        setweight(to_tsvector('english', COALESCE(NEW.requirements, '')), 'C');
    RETURN NEW;
END;
$$;


--
-- Name: compute_quality_score(integer, integer, boolean, boolean); Type: FUNCTION; Schema: public; Owner: -
--

CREATE FUNCTION public.compute_quality_score(required_fields_filled integer, total_required_fields integer, has_embedding boolean DEFAULT false, has_relationships boolean DEFAULT false) RETURNS numeric
    LANGUAGE plpgsql IMMUTABLE
    AS $$
DECLARE
    completeness_score NUMERIC(4, 3);
    bonus_score NUMERIC(4, 3);
BEGIN
    -- Base score from completeness
    IF total_required_fields > 0 THEN
        completeness_score := (required_fields_filled::NUMERIC / total_required_fields::NUMERIC) * 0.7;
    ELSE
        completeness_score := 0.7;
    END IF;
    
    -- Bonus for having embeddings and relationships
    bonus_score := 0.0;
    IF has_embedding THEN
        bonus_score := bonus_score + 0.15;
    END IF;
    IF has_relationships THEN
        bonus_score := bonus_score + 0.15;
    END IF;
    
    RETURN LEAST(1.0, completeness_score + bonus_score);
END;
$$;


--
-- Name: FUNCTION compute_quality_score(required_fields_filled integer, total_required_fields integer, has_embedding boolean, has_relationships boolean); Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON FUNCTION public.compute_quality_score(required_fields_filled integer, total_required_fields integer, has_embedding boolean, has_relationships boolean) IS 'Compute entity quality score based on completeness, embeddings, and relationships';


--
-- Name: coordsys_search_trigger(); Type: FUNCTION; Schema: public; Owner: -
--

CREATE FUNCTION public.coordsys_search_trigger() RETURNS trigger
    LANGUAGE plpgsql
    AS $$
BEGIN
    NEW.search_vector := 
        setweight(to_tsvector('english', COALESCE(NEW.epsg_code, '')), 'A') ||
        setweight(to_tsvector('english', COALESCE(NEW.system_name, '')), 'A') ||
        setweight(to_tsvector('english', COALESCE(NEW.region, '')), 'B');
    RETURN NEW;
END;
$$;


--
-- Name: ctrlmember_search_trigger(); Type: FUNCTION; Schema: public; Owner: -
--

CREATE FUNCTION public.ctrlmember_search_trigger() RETURNS trigger
    LANGUAGE plpgsql
    AS $$
BEGIN
    NEW.search_vector := setweight(to_tsvector('english', COALESCE(NEW.adjustment_notes, '')), 'A');
    RETURN NEW;
END;
$$;


--
-- Name: ctrlnet_search_trigger(); Type: FUNCTION; Schema: public; Owner: -
--

CREATE FUNCTION public.ctrlnet_search_trigger() RETURNS trigger
    LANGUAGE plpgsql
    AS $$
BEGIN
    NEW.search_vector := 
        setweight(to_tsvector('english', COALESCE(NEW.network_name, '')), 'A') ||
        setweight(to_tsvector('english', COALESCE(NEW.description, '')), 'B');
    RETURN NEW;
END;
$$;


--
-- Name: detail_search_trigger(); Type: FUNCTION; Schema: public; Owner: -
--

CREATE FUNCTION public.detail_search_trigger() RETURNS trigger
    LANGUAGE plpgsql
    AS $$
BEGIN
    NEW.search_vector := 
        setweight(to_tsvector('english', COALESCE(NEW.detail_number, '')), 'A') ||
        setweight(to_tsvector('english', COALESCE(NEW.detail_title, '')), 'A') ||
        setweight(to_tsvector('english', COALESCE(NEW.description, '')), 'B') ||
        setweight(to_tsvector('english', COALESCE(NEW.usage_context, '')), 'C');
    RETURN NEW;
END;
$$;


--
-- Name: dimension_search_trigger(); Type: FUNCTION; Schema: public; Owner: -
--

CREATE FUNCTION public.dimension_search_trigger() RETURNS trigger
    LANGUAGE plpgsql
    AS $$
BEGIN
    NEW.search_vector := 
        setweight(to_tsvector('english', COALESCE(NEW.dimension_type, '')), 'A') ||
        setweight(to_tsvector('english', COALESCE(NEW.dimension_text, '')), 'B');
    RETURN NEW;
END;
$$;




--
-- Name: earthwork_search_trigger(); Type: FUNCTION; Schema: public; Owner: -
--

CREATE FUNCTION public.earthwork_search_trigger() RETURNS trigger
    LANGUAGE plpgsql
    AS $$
BEGIN
    NEW.search_vector := 
        setweight(to_tsvector('english', COALESCE(NEW.material_type, '')), 'A') ||
        setweight(to_tsvector('english', COALESCE(NEW.notes, '')), 'B');
    RETURN NEW;
END;
$$;


--
-- Name: easement_search_trigger(); Type: FUNCTION; Schema: public; Owner: -
--

CREATE FUNCTION public.easement_search_trigger() RETURNS trigger
    LANGUAGE plpgsql
    AS $$
BEGIN
    NEW.search_vector := 
        setweight(to_tsvector('english', COALESCE(NEW.easement_number, '')), 'A') ||
        setweight(to_tsvector('english', COALESCE(NEW.easement_type, '')), 'A') ||
        setweight(to_tsvector('english', COALESCE(NEW.easement_purpose, '')), 'B');
    RETURN NEW;
END;
$$;


--
-- Name: exportjob_search_trigger(); Type: FUNCTION; Schema: public; Owner: -
--

CREATE FUNCTION public.exportjob_search_trigger() RETURNS trigger
    LANGUAGE plpgsql
    AS $$
BEGIN
    NEW.search_vector := 
        setweight(to_tsvector('english', COALESCE(NEW.job_name, '')), 'A') ||
        setweight(to_tsvector('english', COALESCE(NEW.job_type, '')), 'B');
    RETURN NEW;
END;
$$;


--
-- Name: find_related_entities(uuid, integer, character varying[]); Type: FUNCTION; Schema: public; Owner: -
--

CREATE FUNCTION public.find_related_entities(start_entity_id uuid, max_hops integer DEFAULT 2, relationship_types character varying[] DEFAULT NULL::character varying[]) RETURNS TABLE(entity_id uuid, canonical_name character varying, entity_type character varying, hop_distance integer, relationship_path text[])
    LANGUAGE plpgsql
    AS $$
BEGIN
    RETURN QUERY
    WITH RECURSIVE entity_graph AS (
        -- Base case: direct relationships
        SELECT 
            er.object_entity_id as entity_id,
            1 as hop_distance,
            ARRAY[er.predicate] as relationship_path
        FROM entity_relationships er
        WHERE er.subject_entity_id = start_entity_id
            AND (relationship_types IS NULL OR er.relationship_type = ANY(relationship_types))
        
        UNION ALL
        
        -- Recursive case: follow relationships
        SELECT 
            er.object_entity_id,
            eg.hop_distance + 1,
            eg.relationship_path || er.predicate
        FROM entity_relationships er
        JOIN entity_graph eg ON er.subject_entity_id = eg.entity_id
        WHERE eg.hop_distance < max_hops
            AND (relationship_types IS NULL OR er.relationship_type = ANY(relationship_types))
            AND NOT (er.object_entity_id = ANY(SELECT unnest(ARRAY[start_entity_id])))
    )
    SELECT DISTINCT
        eg.entity_id,
        se.canonical_name,
        se.entity_type,
        eg.hop_distance,
        eg.relationship_path
    FROM entity_graph eg
    JOIN standards_entities se ON eg.entity_id = se.entity_id
    ORDER BY eg.hop_distance, se.canonical_name;
END;
$$;


--
-- Name: FUNCTION find_related_entities(start_entity_id uuid, max_hops integer, relationship_types character varying[]); Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON FUNCTION public.find_related_entities(start_entity_id uuid, max_hops integer, relationship_types character varying[]) IS 'GraphRAG multi-hop traversal to find related entities within N hops';


--
-- Name: find_similar_entities(uuid, numeric, integer); Type: FUNCTION; Schema: public; Owner: -
--

CREATE FUNCTION public.find_similar_entities(query_entity_id uuid, similarity_threshold numeric DEFAULT 0.8, max_results integer DEFAULT 20) RETURNS TABLE(entity_id uuid, canonical_name character varying, entity_type character varying, similarity_score numeric)
    LANGUAGE plpgsql
    AS $$
BEGIN
    RETURN QUERY
    SELECT 
        se.entity_id,
        se.canonical_name,
        se.entity_type,
        1 - (e1.embedding <=> e2.embedding) as similarity
    FROM entity_embeddings e1
    JOIN entity_embeddings e2 ON e2.is_current = TRUE
    JOIN standards_entities se ON e2.entity_id = se.entity_id
    WHERE e1.entity_id = query_entity_id
        AND e1.is_current = TRUE
        AND e2.entity_id != query_entity_id
        AND 1 - (e1.embedding <=> e2.embedding) >= similarity_threshold
    ORDER BY similarity DESC
    LIMIT max_results;
END;
$$;


--
-- Name: FUNCTION find_similar_entities(query_entity_id uuid, similarity_threshold numeric, max_results integer); Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON FUNCTION public.find_similar_entities(query_entity_id uuid, similarity_threshold numeric, max_results integer) IS 'Find semantically similar entities using vector embeddings';


--
-- Name: gradlimit_search_trigger(); Type: FUNCTION; Schema: public; Owner: -
--

CREATE FUNCTION public.gradlimit_search_trigger() RETURNS trigger
    LANGUAGE plpgsql
    AS $$
BEGIN
    NEW.search_vector := 
        setweight(to_tsvector('english', COALESCE(NEW.limit_name, '')), 'A') ||
        setweight(to_tsvector('english', COALESCE(NEW.limit_type, '')), 'B') ||
        setweight(to_tsvector('english', COALESCE(NEW.description, '')), 'C');
    RETURN NEW;
END;
$$;


--
-- Name: halign_search_trigger(); Type: FUNCTION; Schema: public; Owner: -
--

CREATE FUNCTION public.halign_search_trigger() RETURNS trigger
    LANGUAGE plpgsql
    AS $$
BEGIN
    NEW.search_vector := 
        setweight(to_tsvector('english', COALESCE(NEW.alignment_name, '')), 'A') ||
        setweight(to_tsvector('english', COALESCE(NEW.description, '')), 'B');
    RETURN NEW;
END;
$$;


--
-- Name: hatch_search_trigger(); Type: FUNCTION; Schema: public; Owner: -
--

CREATE FUNCTION public.hatch_search_trigger() RETURNS trigger
    LANGUAGE plpgsql
    AS $$
BEGIN
    NEW.search_vector := setweight(to_tsvector('english', COALESCE(NEW.hatch_pattern, '')), 'A');
    RETURN NEW;
END;
$$;


--
-- Name: hybrid_search(text, public.vector, character varying[], numeric, integer); Type: FUNCTION; Schema: public; Owner: -
--

CREATE FUNCTION public.hybrid_search(search_query text, vector_query public.vector DEFAULT NULL::public.vector, entity_types character varying[] DEFAULT NULL::character varying[], min_quality_score numeric DEFAULT 0.0, max_results integer DEFAULT 50) RETURNS TABLE(entity_id uuid, canonical_name character varying, entity_type character varying, quality_score numeric, text_rank real, vector_similarity numeric, combined_score numeric)
    LANGUAGE plpgsql
    AS $$
BEGIN
    RETURN QUERY
    SELECT 
        se.entity_id,
        se.canonical_name,
        se.entity_type,
        se.quality_score,
        ts_rank(se.search_vector, plainto_tsquery('english', search_query)) as text_rank,
        CASE 
            WHEN vector_query IS NOT NULL AND ee.embedding IS NOT NULL 
            THEN 1 - (ee.embedding <=> vector_query)
            ELSE 0.0
        END as vector_similarity,
        (
            0.3 * ts_rank(se.search_vector, plainto_tsquery('english', search_query)) +
            0.5 * CASE 
                WHEN vector_query IS NOT NULL AND ee.embedding IS NOT NULL 
                THEN 1 - (ee.embedding <=> vector_query)
                ELSE 0.0
            END +
            0.2 * COALESCE(se.quality_score, 0.0)
        ) as combined_score
    FROM standards_entities se
    LEFT JOIN entity_embeddings ee ON se.entity_id = ee.entity_id AND ee.is_current = TRUE
    WHERE 
        (entity_types IS NULL OR se.entity_type = ANY(entity_types))
        AND (se.quality_score IS NULL OR se.quality_score >= min_quality_score)
        AND (
            se.search_vector @@ plainto_tsquery('english', search_query)
            OR (vector_query IS NOT NULL AND ee.embedding IS NOT NULL)
        )
    ORDER BY combined_score DESC
    LIMIT max_results;
END;
$$;


--
-- Name: FUNCTION hybrid_search(search_query text, vector_query public.vector, entity_types character varying[], min_quality_score numeric, max_results integer); Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON FUNCTION public.hybrid_search(search_query text, vector_query public.vector, entity_types character varying[], min_quality_score numeric, max_results integer) IS 'Hybrid search combining full-text search, vector similarity, and quality scores';


--
-- Name: layer_search_trigger(); Type: FUNCTION; Schema: public; Owner: -
--

CREATE FUNCTION public.layer_search_trigger() RETURNS trigger
    LANGUAGE plpgsql
    AS $$
BEGIN
    NEW.search_vector := 
        setweight(to_tsvector('english', COALESCE(NEW.layer_name, '')), 'A') ||
        setweight(to_tsvector('english', COALESCE(NEW.description, '')), 'B');
    RETURN NEW;
END;
$$;


--
-- Name: material_search_trigger(); Type: FUNCTION; Schema: public; Owner: -
--

CREATE FUNCTION public.material_search_trigger() RETURNS trigger
    LANGUAGE plpgsql
    AS $$
BEGIN
    NEW.search_vector := 
        setweight(to_tsvector('english', COALESCE(NEW.material_name, '')), 'A') ||
        setweight(to_tsvector('english', COALESCE(NEW.description, '')), 'B') ||
        setweight(to_tsvector('english', COALESCE(NEW.specifications, '')), 'C');
    RETURN NEW;
END;
$$;


--
-- Name: note_search_trigger(); Type: FUNCTION; Schema: public; Owner: -
--

CREATE FUNCTION public.note_search_trigger() RETURNS trigger
    LANGUAGE plpgsql
    AS $$
BEGIN
    NEW.search_vector := 
        setweight(to_tsvector('english', COALESCE(NEW.note_title, '')), 'A') ||
        setweight(to_tsvector('english', COALESCE(NEW.note_text, '')), 'B') ||
        setweight(to_tsvector('english', COALESCE(NEW.note_category, '')), 'C');
    RETURN NEW;
END;
$$;


--
-- Name: noteassign_search_trigger(); Type: FUNCTION; Schema: public; Owner: -
--

CREATE FUNCTION public.noteassign_search_trigger() RETURNS trigger
    LANGUAGE plpgsql
    AS $$
BEGIN
    NEW.search_vector := setweight(to_tsvector('english', COALESCE(NEW.layout_name, '')), 'A');
    RETURN NEW;
END;
$$;


--
-- Name: noteset_search_trigger(); Type: FUNCTION; Schema: public; Owner: -
--

CREATE FUNCTION public.noteset_search_trigger() RETURNS trigger
    LANGUAGE plpgsql
    AS $$
BEGIN
    NEW.search_vector := 
        setweight(to_tsvector('english', COALESCE(NEW.set_name, '')), 'A') ||
        setweight(to_tsvector('english', COALESCE(NEW.description, '')), 'B');
    RETURN NEW;
END;
$$;


--
-- Name: parcel_search_trigger(); Type: FUNCTION; Schema: public; Owner: -
--

CREATE FUNCTION public.parcel_search_trigger() RETURNS trigger
    LANGUAGE plpgsql
    AS $$
BEGIN
    NEW.search_vector := 
        setweight(to_tsvector('english', COALESCE(NEW.parcel_number, '')), 'A') ||
        setweight(to_tsvector('english', COALESCE(NEW.parcel_name, '')), 'A') ||
        setweight(to_tsvector('english', COALESCE(NEW.owner_name, '')), 'B') ||
        setweight(to_tsvector('english', COALESCE(NEW.legal_description, '')), 'C');
    RETURN NEW;
END;
$$;


--
-- Name: parcelcorner_search_trigger(); Type: FUNCTION; Schema: public; Owner: -
--

CREATE FUNCTION public.parcelcorner_search_trigger() RETURNS trigger
    LANGUAGE plpgsql
    AS $$
BEGIN
    NEW.search_vector := 
        setweight(to_tsvector('english', COALESCE(NEW.monument_description, '')), 'A') ||
        setweight(to_tsvector('english', COALESCE(NEW.notes, '')), 'B');
    RETURN NEW;
END;
$$;


--
-- Name: pavesect_search_trigger(); Type: FUNCTION; Schema: public; Owner: -
--

CREATE FUNCTION public.pavesect_search_trigger() RETURNS trigger
    LANGUAGE plpgsql
    AS $$
BEGIN
    NEW.search_vector := 
        setweight(to_tsvector('english', COALESCE(NEW.section_name, '')), 'A') ||
        setweight(to_tsvector('english', COALESCE(NEW.section_code, '')), 'A') ||
        setweight(to_tsvector('english', COALESCE(NEW.design_notes, '')), 'B');
    RETURN NEW;
END;
$$;


--
-- Name: projnote_search_trigger(); Type: FUNCTION; Schema: public; Owner: -
--

CREATE FUNCTION public.projnote_search_trigger() RETURNS trigger
    LANGUAGE plpgsql
    AS $$
BEGIN
    NEW.search_vector := 
        setweight(to_tsvector('english', COALESCE(NEW.display_code, '')), 'A') ||
        setweight(to_tsvector('english', COALESCE(NEW.custom_title, '')), 'A') ||
        setweight(to_tsvector('english', COALESCE(NEW.custom_text, '')), 'B');
    RETURN NEW;
END;
$$;


--
-- Name: pvi_search_trigger(); Type: FUNCTION; Schema: public; Owner: -
--

CREATE FUNCTION public.pvi_search_trigger() RETURNS trigger
    LANGUAGE plpgsql
    AS $$
BEGIN
    NEW.search_vector := setweight(to_tsvector('english', COALESCE(NEW.notes, '')), 'A');
    RETURN NEW;
END;
$$;


--
-- Name: row_search_trigger(); Type: FUNCTION; Schema: public; Owner: -
--

CREATE FUNCTION public.row_search_trigger() RETURNS trigger
    LANGUAGE plpgsql
    AS $$
BEGIN
    NEW.search_vector := 
        setweight(to_tsvector('english', COALESCE(NEW.row_name, '')), 'A') ||
        setweight(to_tsvector('english', COALESCE(NEW.row_type, '')), 'B') ||
        setweight(to_tsvector('english', COALESCE(NEW.dedication_info, '')), 'C');
    RETURN NEW;
END;
$$;


--
-- Name: scale_search_trigger(); Type: FUNCTION; Schema: public; Owner: -
--

CREATE FUNCTION public.scale_search_trigger() RETURNS trigger
    LANGUAGE plpgsql
    AS $$
BEGIN
    NEW.search_vector := 
        setweight(to_tsvector('english', COALESCE(NEW.scale_name, '')), 'A') ||
        setweight(to_tsvector('english', COALESCE(NEW.scale_ratio, '')), 'A') ||
        setweight(to_tsvector('english', COALESCE(NEW.use_case, '')), 'B');
    RETURN NEW;
END;
$$;


--
-- Name: sheet_search_trigger(); Type: FUNCTION; Schema: public; Owner: -
--

CREATE FUNCTION public.sheet_search_trigger() RETURNS trigger
    LANGUAGE plpgsql
    AS $$
BEGIN
    NEW.search_vector := 
        setweight(to_tsvector('english', COALESCE(NEW.sheet_code, '')), 'A') ||
        setweight(to_tsvector('english', COALESCE(NEW.sheet_title, '')), 'A') ||
        setweight(to_tsvector('english', COALESCE(NEW.notes, '')), 'B');
    RETURN NEW;
END;
$$;




--
-- Name: sheetrel_search_trigger(); Type: FUNCTION; Schema: public; Owner: -
--

CREATE FUNCTION public.sheetrel_search_trigger() RETURNS trigger
    LANGUAGE plpgsql
    AS $$
BEGIN
    NEW.search_vector := 
        setweight(to_tsvector('english', COALESCE(NEW.relationship_type, '')), 'A') ||
        setweight(to_tsvector('english', COALESCE(NEW.notes, '')), 'B');
    RETURN NEW;
END;
$$;


--
-- Name: sheetrev_search_trigger(); Type: FUNCTION; Schema: public; Owner: -
--

CREATE FUNCTION public.sheetrev_search_trigger() RETURNS trigger
    LANGUAGE plpgsql
    AS $$
BEGIN
    NEW.search_vector := setweight(to_tsvector('english', COALESCE(NEW.description, '')), 'A');
    RETURN NEW;
END;
$$;


--
-- Name: sheetset_search_trigger(); Type: FUNCTION; Schema: public; Owner: -
--

CREATE FUNCTION public.sheetset_search_trigger() RETURNS trigger
    LANGUAGE plpgsql
    AS $$
BEGIN
    NEW.search_vector := 
        setweight(to_tsvector('english', COALESCE(NEW.set_name, '')), 'A') ||
        setweight(to_tsvector('english', COALESCE(NEW.set_number, '')), 'A') ||
        setweight(to_tsvector('english', COALESCE(NEW.transmittal_notes, '')), 'B');
    RETURN NEW;
END;
$$;


--
-- Name: surface_search_trigger(); Type: FUNCTION; Schema: public; Owner: -
--

CREATE FUNCTION public.surface_search_trigger() RETURNS trigger
    LANGUAGE plpgsql
    AS $$
BEGIN
    NEW.search_vector := 
        setweight(to_tsvector('english', COALESCE(NEW.surface_name, '')), 'A') ||
        setweight(to_tsvector('english', COALESCE(NEW.description, '')), 'B');
    RETURN NEW;
END;
$$;


--
-- Name: surfacefeat_search_trigger(); Type: FUNCTION; Schema: public; Owner: -
--

CREATE FUNCTION public.surfacefeat_search_trigger() RETURNS trigger
    LANGUAGE plpgsql
    AS $$
BEGIN
    NEW.search_vector := 
        setweight(to_tsvector('english', COALESCE(NEW.feature_type, '')), 'A') ||
        setweight(to_tsvector('english', COALESCE(NEW.description, '')), 'B');
    RETURN NEW;
END;
$$;


--
-- Name: surveyobs_search_trigger(); Type: FUNCTION; Schema: public; Owner: -
--

CREATE FUNCTION public.surveyobs_search_trigger() RETURNS trigger
    LANGUAGE plpgsql
    AS $$
BEGIN
    NEW.search_vector := 
        setweight(to_tsvector('english', COALESCE(NEW.observation_type, '')), 'A') ||
        setweight(to_tsvector('english', COALESCE(NEW.notes, '')), 'B');
    RETURN NEW;
END;
$$;


--
-- Name: surveypt_search_trigger(); Type: FUNCTION; Schema: public; Owner: -
--

CREATE FUNCTION public.surveypt_search_trigger() RETURNS trigger
    LANGUAGE plpgsql
    AS $$
BEGIN
    NEW.search_vector := 
        setweight(to_tsvector('english', COALESCE(NEW.point_number, '')), 'A') ||
        setweight(to_tsvector('english', COALESCE(NEW.point_description, '')), 'B') ||
        setweight(to_tsvector('english', COALESCE(NEW.point_type, '')), 'B');
    RETURN NEW;
END;
$$;


--
-- Name: travloop_search_trigger(); Type: FUNCTION; Schema: public; Owner: -
--

CREATE FUNCTION public.travloop_search_trigger() RETURNS trigger
    LANGUAGE plpgsql
    AS $$
BEGIN
    NEW.search_vector := 
        setweight(to_tsvector('english', COALESCE(NEW.loop_name, '')), 'A') ||
        setweight(to_tsvector('english', COALESCE(NEW.description, '')), 'B') ||
        setweight(to_tsvector('english', COALESCE(NEW.adjustment_notes, '')), 'C');
    RETURN NEW;
END;
$$;


--
-- Name: travloopobs_search_trigger(); Type: FUNCTION; Schema: public; Owner: -
--

CREATE FUNCTION public.travloopobs_search_trigger() RETURNS trigger
    LANGUAGE plpgsql
    AS $$
BEGIN
    NEW.search_vector := setweight(to_tsvector('english', COALESCE(NEW.notes, '')), 'A');
    RETURN NEW;
END;
$$;


--
-- Name: tree_search_trigger(); Type: FUNCTION; Schema: public; Owner: -
--

CREATE FUNCTION public.tree_search_trigger() RETURNS trigger
    LANGUAGE plpgsql
    AS $$
BEGIN
    NEW.search_vector := 
        setweight(to_tsvector('english', COALESCE(NEW.tree_number, '')), 'A') ||
        setweight(to_tsvector('english', COALESCE(NEW.species, '')), 'A') ||
        setweight(to_tsvector('english', COALESCE(NEW.common_name, '')), 'A') ||
        setweight(to_tsvector('english', COALESCE(NEW.location_description, '')), 'B');
    RETURN NEW;
END;
$$;


--
-- Name: typsect_search_trigger(); Type: FUNCTION; Schema: public; Owner: -
--

CREATE FUNCTION public.typsect_search_trigger() RETURNS trigger
    LANGUAGE plpgsql
    AS $$
BEGIN
    NEW.search_vector := 
        setweight(to_tsvector('english', COALESCE(NEW.section_name, '')), 'A') ||
        setweight(to_tsvector('english', COALESCE(NEW.section_code, '')), 'A') ||
        setweight(to_tsvector('english', COALESCE(NEW.description, '')), 'B');
    RETURN NEW;
END;
$$;


--
-- Name: update_entity_search_vector(); Type: FUNCTION; Schema: public; Owner: -
--

CREATE FUNCTION public.update_entity_search_vector() RETURNS trigger
    LANGUAGE plpgsql IMMUTABLE
    AS $$
BEGIN
    NEW.search_vector := 
        setweight(to_tsvector('english', coalesce(NEW.canonical_name, '')), 'A') ||
        setweight(to_tsvector('english', coalesce(NEW.description, '')), 'B') ||
        setweight(to_tsvector('english', coalesce(array_to_string(NEW.tags, ' '), '')), 'C');
    RETURN NEW;
END;
$$;


--
-- Name: utilconn_search_trigger(); Type: FUNCTION; Schema: public; Owner: -
--

CREATE FUNCTION public.utilconn_search_trigger() RETURNS trigger
    LANGUAGE plpgsql
    AS $$
BEGIN
    NEW.search_vector := 
        setweight(to_tsvector('english', COALESCE(NEW.connection_type, '')), 'A') ||
        setweight(to_tsvector('english', COALESCE(NEW.notes, '')), 'B');
    RETURN NEW;
END;
$$;


--
-- Name: utilline_search_trigger(); Type: FUNCTION; Schema: public; Owner: -
--

CREATE FUNCTION public.utilline_search_trigger() RETURNS trigger
    LANGUAGE plpgsql
    AS $$
BEGIN
    NEW.search_vector := 
        setweight(to_tsvector('english', COALESCE(NEW.line_number, '')), 'A') ||
        setweight(to_tsvector('english', COALESCE(NEW.utility_system, '')), 'A') ||
        setweight(to_tsvector('english', COALESCE(NEW.line_type, '')), 'B');
    RETURN NEW;
END;
$$;


--
-- Name: utilserv_search_trigger(); Type: FUNCTION; Schema: public; Owner: -
--

CREATE FUNCTION public.utilserv_search_trigger() RETURNS trigger
    LANGUAGE plpgsql
    AS $$
BEGIN
    NEW.search_vector := 
        setweight(to_tsvector('english', COALESCE(NEW.service_address, '')), 'A') ||
        setweight(to_tsvector('english', COALESCE(NEW.customer_account, '')), 'B');
    RETURN NEW;
END;
$$;


--
-- Name: utilstruct_search_trigger(); Type: FUNCTION; Schema: public; Owner: -
--

CREATE FUNCTION public.utilstruct_search_trigger() RETURNS trigger
    LANGUAGE plpgsql
    AS $$
BEGIN
    NEW.search_vector := 
        setweight(to_tsvector('english', COALESCE(NEW.structure_number, '')), 'A') ||
        setweight(to_tsvector('english', COALESCE(NEW.structure_type, '')), 'A') ||
        setweight(to_tsvector('english', COALESCE(NEW.utility_system, '')), 'B');
    RETURN NEW;
END;
$$;


--
-- Name: viewport_search_trigger(); Type: FUNCTION; Schema: public; Owner: -
--

CREATE FUNCTION public.viewport_search_trigger() RETURNS trigger
    LANGUAGE plpgsql
    AS $$
BEGIN
    NEW.search_vector := setweight(to_tsvector('english', COALESCE(NEW.layout_name, '')), 'A');
    RETURN NEW;
END;
$$;


--
-- Name: vprofile_search_trigger(); Type: FUNCTION; Schema: public; Owner: -
--

CREATE FUNCTION public.vprofile_search_trigger() RETURNS trigger
    LANGUAGE plpgsql
    AS $$
BEGIN
    NEW.search_vector := 
        setweight(to_tsvector('english', COALESCE(NEW.profile_name, '')), 'A') ||
        setweight(to_tsvector('english', COALESCE(NEW.description, '')), 'B');
    RETURN NEW;
END;
$$;


--
-- Name: xsection_search_trigger(); Type: FUNCTION; Schema: public; Owner: -
--

CREATE FUNCTION public.xsection_search_trigger() RETURNS trigger
    LANGUAGE plpgsql
    AS $$
BEGIN
    NEW.search_vector := setweight(to_tsvector('english', COALESCE(NEW.description, '')), 'A');
    RETURN NEW;
END;
$$;


--
-- Name: xsectpoint_search_trigger(); Type: FUNCTION; Schema: public; Owner: -
--

CREATE FUNCTION public.xsectpoint_search_trigger() RETURNS trigger
    LANGUAGE plpgsql
    AS $$
BEGIN
    NEW.search_vector := setweight(to_tsvector('english', COALESCE(NEW.notes, '')), 'A');
    RETURN NEW;
END;
$$;


SET default_tablespace = '';

SET default_table_access_method = heap;

--
-- Name: abbreviation_standards; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.abbreviation_standards (
    abbreviation_id uuid DEFAULT gen_random_uuid() NOT NULL,
    entity_id uuid,
    abbreviation character varying(50) NOT NULL,
    full_text character varying(255) NOT NULL,
    category character varying(100),
    discipline character varying(100),
    context_usage text,
    quality_score numeric(3,2) DEFAULT 0.0,
    tags text[],
    attributes jsonb,
    search_vector tsvector,
    usage_frequency integer DEFAULT 0,
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    updated_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP
);


--
-- Name: alignment_pis; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.alignment_pis (
    pi_id uuid DEFAULT gen_random_uuid() NOT NULL,
    entity_id uuid,
    alignment_id uuid,
    pi_number integer NOT NULL,
    station numeric(10,4) NOT NULL,
    geometry public.geometry(PointZ,2226),
    curve_type character varying(50),
    curve_radius numeric(12,4),
    curve_length numeric(12,4),
    delta_angle numeric(10,4),
    tangent_length numeric(12,4),
    spiral_in_length numeric(10,4),
    spiral_out_length numeric(10,4),
    superelevation numeric(6,4),
    notes text,
    quality_score numeric(3,2) DEFAULT 0.0,
    tags text[],
    attributes jsonb,
    search_vector tsvector,
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    updated_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP
);


--
-- Name: annotation_standards; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.annotation_standards (
    annotation_id uuid DEFAULT gen_random_uuid() NOT NULL,
    entity_id uuid,
    annotation_name character varying(255) NOT NULL,
    annotation_type character varying(100),
    text_style character varying(100),
    text_height numeric(10,4),
    leader_type character varying(50),
    arrow_style character varying(50),
    description text,
    quality_score numeric(3,2) DEFAULT 0.0,
    tags text[],
    attributes jsonb,
    search_vector tsvector,
    usage_frequency integer DEFAULT 0,
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    updated_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP
);


--
-- Name: block_definitions; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.block_definitions (
    block_id uuid DEFAULT gen_random_uuid() NOT NULL,
    block_name character varying(255) NOT NULL,
    block_type character varying(50),
    description text,
    category character varying(100),
    insertion_point_x numeric(15,4),
    insertion_point_y numeric(15,4),
    insertion_point_z numeric(15,4),
    has_attributes boolean DEFAULT false,
    is_dynamic boolean DEFAULT false,
    entity_id uuid,
    quality_score numeric(4,3),
    usage_frequency integer DEFAULT 0,
    complexity_score numeric(4,3),
    tags text[],
    attributes jsonb DEFAULT '{}'::jsonb,
    search_vector tsvector,
    dxf_file_path text,
    preview_image_path text,
    is_active boolean DEFAULT true,
    superseded_by uuid,
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    updated_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP
);


--
-- Name: TABLE block_definitions; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON TABLE public.block_definitions IS 'Block definitions - AI-optimized with complexity scoring and usage tracking';


--
-- Name: block_inserts; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.block_inserts (
    insert_id uuid DEFAULT gen_random_uuid() NOT NULL,
    entity_id uuid,
    layer_id uuid,
    block_name character varying(255) NOT NULL,
    insertion_point public.geometry(PointZ) NOT NULL,
    scale_x numeric(10,4) DEFAULT 1.0,
    scale_y numeric(10,4) DEFAULT 1.0,
    scale_z numeric(10,4) DEFAULT 1.0,
    rotation numeric(10,4) DEFAULT 0.0,
    dxf_handle character varying(100),
    quality_score numeric(3,2) DEFAULT 0.0,
    tags text[],
    attributes jsonb,
    search_vector tsvector,
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    updated_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP
);


--
-- Name: block_standards; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.block_standards (
    block_standard_id uuid DEFAULT gen_random_uuid() NOT NULL,
    block_name character varying(255) NOT NULL,
    category character varying(100),
    description text,
    svg_preview text,
    discipline character varying(100)
);


--
-- Name: category_standards; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.category_standards (
    category_id uuid DEFAULT gen_random_uuid() NOT NULL,
    entity_id uuid,
    category_name character varying(100) NOT NULL,
    category_code character varying(50),
    parent_category_id uuid,
    description text,
    discipline character varying(100),
    hierarchy_level integer DEFAULT 0,
    quality_score numeric(3,2) DEFAULT 0.0,
    tags text[],
    attributes jsonb,
    search_vector tsvector,
    usage_frequency integer DEFAULT 0,
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    updated_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP
);


--
-- Name: classification_confidence; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.classification_confidence (
    prediction_id uuid DEFAULT gen_random_uuid() NOT NULL,
    entity_id uuid NOT NULL,
    model_name character varying(255) NOT NULL,
    model_version character varying(100),
    model_id uuid,
    predicted_class character varying(255) NOT NULL,
    confidence_score numeric(5,4) NOT NULL,
    probability_distribution jsonb,
    top_predictions jsonb,
    actual_class character varying(255),
    is_correct boolean,
    feature_importance jsonb,
    explanation text,
    input_features jsonb,
    prediction_context jsonb,
    calibration_score numeric(5,4),
    uncertainty_score numeric(5,4),
    predicted_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP
);


--
-- Name: TABLE classification_confidence; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON TABLE public.classification_confidence IS 'ML classification predictions with confidence scores and explainability';


--
-- Name: code_standards; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.code_standards (
    code_id uuid DEFAULT gen_random_uuid() NOT NULL,
    entity_id uuid,
    code_name character varying(255) NOT NULL,
    code_number character varying(100),
    code_section character varying(100),
    jurisdiction character varying(100),
    description text,
    requirements text,
    effective_date date,
    last_amended date,
    quality_score numeric(3,2) DEFAULT 0.0,
    tags text[],
    attributes jsonb,
    search_vector tsvector,
    usage_frequency integer DEFAULT 0,
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    updated_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP
);


--
-- Name: color_standards; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.color_standards (
    color_id uuid DEFAULT gen_random_uuid() NOT NULL,
    color_name character varying(100) NOT NULL,
    aci_number integer,
    rgb_value character varying(20),
    hex_value character varying(7),
    cmyk_value character varying(30),
    description text,
    usage_context character varying(255),
    discipline character varying(50),
    entity_id uuid,
    quality_score numeric(4,3),
    usage_frequency integer DEFAULT 0,
    tags text[],
    attributes jsonb DEFAULT '{}'::jsonb,
    search_vector tsvector,
    is_active boolean DEFAULT true,
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    updated_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP
);


--
-- Name: TABLE color_standards; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON TABLE public.color_standards IS 'Color standards - AI-optimized with usage tracking and semantic search';


--
-- Name: control_point_membership; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.control_point_membership (
    membership_id uuid DEFAULT gen_random_uuid() NOT NULL,
    entity_id uuid,
    network_id uuid,
    point_id uuid,
    is_fixed_point boolean DEFAULT false,
    adjusted_northing numeric(15,4),
    adjusted_easting numeric(15,4),
    adjusted_elevation numeric(10,4),
    residual_h numeric(10,4),
    residual_v numeric(10,4),
    standard_error_h numeric(10,4),
    standard_error_v numeric(10,4),
    adjustment_notes text,
    quality_score numeric(3,2) DEFAULT 0.0,
    tags text[],
    attributes jsonb,
    search_vector tsvector,
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    updated_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP
);


--
-- Name: coordinate_systems; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.coordinate_systems (
    system_id uuid DEFAULT gen_random_uuid() NOT NULL,
    entity_id uuid,
    epsg_code character varying(20) NOT NULL,
    system_name character varying(255) NOT NULL,
    region character varying(100),
    datum character varying(50),
    units character varying(20),
    zone_number integer,
    notes text,
    is_active boolean DEFAULT true,
    quality_score numeric(3,2) DEFAULT 0.0,
    tags text[],
    attributes jsonb,
    search_vector tsvector,
    usage_frequency integer DEFAULT 0,
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    updated_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP
);


--
-- Name: cross_section_points; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.cross_section_points (
    xsection_point_id uuid DEFAULT gen_random_uuid() NOT NULL,
    entity_id uuid,
    section_id uuid,
    point_number integer NOT NULL,
    cross_offset numeric(12,4),
    elevation numeric(12,4),
    point_type character varying(50),
    slope_ratio character varying(20),
    cut_fill_flag character(1),
    cut_fill_depth numeric(10,4),
    notes text,
    quality_score numeric(3,2) DEFAULT 0.0,
    tags text[],
    attributes jsonb,
    search_vector tsvector,
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    updated_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP
);


--
-- Name: cross_sections; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.cross_sections (
    section_id uuid DEFAULT gen_random_uuid() NOT NULL,
    entity_id uuid,
    alignment_id uuid,
    station numeric(10,4) NOT NULL,
    section_type character varying(50),
    section_geometry public.geometry(LineStringZ,2226) NOT NULL,
    cut_area numeric(12,4),
    fill_area numeric(12,4),
    description text,
    quality_score numeric(3,2) DEFAULT 0.0,
    tags text[],
    attributes jsonb,
    search_vector tsvector,
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    updated_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP
);


--
-- Name: detail_standards; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.detail_standards (
    detail_id uuid DEFAULT gen_random_uuid() NOT NULL,
    entity_id uuid,
    detail_number character varying(50) NOT NULL,
    detail_title character varying(255) NOT NULL,
    detail_category character varying(100),
    description text,
    usage_context text,
    svg_content text,
    thumbnail_url text,
    discipline character varying(100),
    code_references text[],
    quality_score numeric(3,2) DEFAULT 0.0,
    tags text[],
    attributes jsonb,
    search_vector tsvector,
    usage_frequency integer DEFAULT 0,
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    updated_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP
);


--
-- Name: dimension_styles; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.dimension_styles (
    dimension_style_id uuid DEFAULT gen_random_uuid() NOT NULL,
    style_name character varying(255) NOT NULL,
    text_height numeric(10,4),
    arrow_size numeric(10,4),
    extension_line_offset numeric(10,4),
    dimension_line_color integer,
    text_color integer,
    description text
);




--
-- Name: earthwork_balance; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.earthwork_balance (
    balance_id uuid DEFAULT gen_random_uuid() NOT NULL,
    entity_id uuid,
    alignment_id uuid,
    station numeric(10,4),
    cumulative_volume numeric(15,4),
    mass_ordinate numeric(15,4),
    balance_point boolean DEFAULT false,
    free_haul_limit numeric(10,2),
    quality_score numeric(3,2) DEFAULT 0.0,
    tags text[],
    attributes jsonb,
    search_vector tsvector,
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    updated_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP
);


--
-- Name: earthwork_quantities; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.earthwork_quantities (
    earthwork_id uuid DEFAULT gen_random_uuid() NOT NULL,
    entity_id uuid,
    alignment_id uuid,
    start_station numeric(10,4),
    end_station numeric(10,4),
    material_type character varying(100),
    cut_volume numeric(15,4),
    fill_volume numeric(15,4),
    net_volume numeric(15,4),
    shrink_swell numeric(8,4) DEFAULT 1.0,
    haul_distance numeric(10,2),
    overhaul numeric(15,4),
    unit_cost numeric(10,2),
    total_cost numeric(15,2),
    notes text,
    quality_score numeric(3,2) DEFAULT 0.0,
    tags text[],
    attributes jsonb,
    search_vector tsvector,
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    updated_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP
);


--
-- Name: easements; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.easements (
    easement_id uuid DEFAULT gen_random_uuid() NOT NULL,
    entity_id uuid,
    project_id uuid,
    easement_number character varying(100),
    easement_type character varying(100),
    easement_purpose text,
    grantor character varying(255),
    grantee character varying(255),
    recording_info character varying(255),
    recorded_date date,
    width numeric(10,4),
    boundary_geometry public.geometry(GeometryZ,2226) NOT NULL,
    area_sqft numeric(15,4),
    notes text,
    quality_score numeric(3,2) DEFAULT 0.0,
    tags text[],
    attributes jsonb,
    search_vector tsvector,
    usage_frequency integer DEFAULT 0,
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    updated_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP
);


--
-- Name: embedding_models; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.embedding_models (
    model_id uuid DEFAULT gen_random_uuid() NOT NULL,
    model_name character varying(255) NOT NULL,
    model_version character varying(100),
    provider character varying(100),
    dimensions integer NOT NULL,
    model_config jsonb,
    is_active boolean DEFAULT true,
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    updated_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP
);


--
-- Name: TABLE embedding_models; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON TABLE public.embedding_models IS 'Registry of embedding models used for vector generation (OpenAI ada-002, Cohere, local models, etc.)';


--
-- Name: entity_aliases; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.entity_aliases (
    alias_id uuid DEFAULT gen_random_uuid() NOT NULL,
    entity_id uuid NOT NULL,
    alias_name character varying(255) NOT NULL,
    alias_type character varying(50),
    confidence_score numeric(4,3) DEFAULT 1.0,
    source character varying(100),
    is_canonical boolean DEFAULT false,
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP
);


--
-- Name: TABLE entity_aliases; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON TABLE public.entity_aliases IS 'Entity alias resolution - prevents duplicate embeddings and improves entity matching';


--
-- Name: entity_embeddings; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.entity_embeddings (
    embedding_id uuid DEFAULT gen_random_uuid() NOT NULL,
    entity_id uuid NOT NULL,
    model_id uuid NOT NULL,
    embedding public.vector(1536),
    embedding_text text,
    embedding_context jsonb,
    is_current boolean DEFAULT true,
    version integer DEFAULT 1,
    quality_metrics jsonb,
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP
);


--
-- Name: TABLE entity_embeddings; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON TABLE public.entity_embeddings IS 'Centralized vector embeddings with versioning and multi-model support for semantic search';


--
-- Name: entity_relationships; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.entity_relationships (
    relationship_id uuid DEFAULT gen_random_uuid() NOT NULL,
    subject_entity_id uuid NOT NULL,
    predicate character varying(100) NOT NULL,
    object_entity_id uuid NOT NULL,
    relationship_type character varying(50) NOT NULL,
    confidence_score numeric(4,3) DEFAULT 1.0,
    spatial_relationship boolean DEFAULT false,
    engineering_relationship boolean DEFAULT false,
    ai_generated boolean DEFAULT false,
    attributes jsonb,
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    updated_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP
);


--
-- Name: TABLE entity_relationships; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON TABLE public.entity_relationships IS 'Graph edges for GraphRAG - explicit relationships between entities (spatial, engineering, semantic)';


--
-- Name: export_jobs; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.export_jobs (
    job_id uuid DEFAULT gen_random_uuid() NOT NULL,
    entity_id uuid,
    job_name character varying(255) NOT NULL,
    job_type character varying(50),
    export_format character varying(50),
    export_path text,
    status character varying(50) DEFAULT 'pending'::character varying,
    started_at timestamp without time zone,
    completed_at timestamp without time zone,
    error_message text,
    quality_score numeric(3,2) DEFAULT 0.0,
    tags text[],
    attributes jsonb,
    search_vector tsvector,
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    updated_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP
);


--
-- Name: grading_limits; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.grading_limits (
    limit_id uuid DEFAULT gen_random_uuid() NOT NULL,
    entity_id uuid,
    project_id uuid,
    limit_name character varying(255) NOT NULL,
    limit_type character varying(50),
    boundary_geometry public.geometry(PolygonZ,2226) NOT NULL,
    area_sqft numeric(15,4),
    area_acres numeric(15,4),
    max_allowed_area_acres numeric(15,4),
    approval_status character varying(50),
    permit_number character varying(100),
    approved_by character varying(255),
    approval_date date,
    expiration_date date,
    description text,
    notes text,
    quality_score numeric(3,2) DEFAULT 0.0,
    tags text[],
    attributes jsonb,
    search_vector tsvector,
    usage_frequency integer DEFAULT 0,
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    updated_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP
);


--
-- Name: hatch_patterns; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.hatch_patterns (
    hatch_id uuid DEFAULT gen_random_uuid() NOT NULL,
    pattern_name character varying(100) NOT NULL,
    pattern_type character varying(50),
    pattern_definition text,
    description text,
    usage_context character varying(255),
    entity_id uuid,
    quality_score numeric(4,3),
    usage_frequency integer DEFAULT 0,
    tags text[],
    attributes jsonb DEFAULT '{}'::jsonb,
    search_vector tsvector,
    pat_file_path text,
    preview_image_path text,
    is_active boolean DEFAULT true,
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    updated_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP
);


--
-- Name: TABLE hatch_patterns; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON TABLE public.hatch_patterns IS 'Hatch pattern standards - AI-optimized with usage tracking';


--
-- Name: horizontal_alignments; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.horizontal_alignments (
    alignment_id uuid DEFAULT gen_random_uuid() NOT NULL,
    entity_id uuid,
    project_id uuid,
    alignment_name character varying(255) NOT NULL,
    description text,
    alignment_type character varying(50),
    design_speed numeric(6,2),
    alignment_geometry public.geometry(LineStringZ,2226),
    start_station numeric(10,4),
    end_station numeric(10,4),
    created_by character varying(255),
    quality_score numeric(3,2) DEFAULT 0.0,
    tags text[],
    attributes jsonb,
    search_vector tsvector,
    usage_frequency integer DEFAULT 0,
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    updated_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP
);


--
-- Name: layer_standards; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.layer_standards (
    layer_id uuid DEFAULT gen_random_uuid() NOT NULL,
    layer_name character varying(255) NOT NULL,
    color character varying(50),
    color_rgb character varying(20),
    aci_color integer,
    linetype character varying(100),
    lineweight character varying(50),
    description text,
    discipline character varying(50),
    category character varying(100),
    usage_notes text,
    entity_id uuid,
    quality_score numeric(4,3),
    usage_frequency integer DEFAULT 0,
    tags text[],
    attributes jsonb DEFAULT '{}'::jsonb,
    search_vector tsvector,
    is_active boolean DEFAULT true,
    is_deprecated boolean DEFAULT false,
    superseded_by uuid,
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    updated_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP
);


--
-- Name: TABLE layer_standards; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON TABLE public.layer_standards IS 'Layer standards - AI-optimized with quality scores, usage tracking, and semantic search';


--
-- Name: layers; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.layers (
    layer_id uuid DEFAULT gen_random_uuid() NOT NULL,
    entity_id uuid,
    layer_name character varying(255) NOT NULL,
    layer_standard_id uuid,
    color integer,
    color_rgb character varying(50),
    linetype character varying(100),
    lineweight integer,
    is_frozen boolean DEFAULT false,
    is_locked boolean DEFAULT false,
    discipline character varying(100),
    description text,
    quality_score numeric(3,2) DEFAULT 0.0,
    tags text[],
    attributes jsonb,
    search_vector tsvector,
    usage_frequency integer DEFAULT 0,
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    updated_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP
);


--
-- Name: layout_viewports; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.layout_viewports (
    viewport_id uuid DEFAULT gen_random_uuid() NOT NULL,
    entity_id uuid,
    layout_name character varying(255) NOT NULL,
    viewport_number integer,
    center_point public.geometry(PointZ),
    width numeric(12,4),
    height numeric(12,4),
    scale_factor numeric(12,6),
    view_direction jsonb,
    is_active boolean DEFAULT true,
    quality_score numeric(3,2) DEFAULT 0.0,
    tags text[],
    attributes jsonb,
    search_vector tsvector,
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    updated_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP
);


--
-- Name: linetypes; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.linetypes (
    linetype_id uuid DEFAULT gen_random_uuid() NOT NULL,
    linetype_name character varying(100) NOT NULL,
    pattern_definition text,
    description text,
    usage_context character varying(255),
    entity_id uuid,
    quality_score numeric(4,3),
    usage_frequency integer DEFAULT 0,
    tags text[],
    attributes jsonb DEFAULT '{}'::jsonb,
    search_vector tsvector,
    is_active boolean DEFAULT true,
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    updated_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP
);


--
-- Name: TABLE linetypes; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON TABLE public.linetypes IS 'Linetype standards - AI-optimized with usage tracking';


--
-- Name: material_standards; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.material_standards (
    material_id uuid DEFAULT gen_random_uuid() NOT NULL,
    entity_id uuid,
    material_name character varying(255) NOT NULL,
    material_type character varying(100),
    description text,
    specifications text,
    manufacturer character varying(255),
    product_code character varying(100),
    cost_per_unit numeric(10,2),
    unit_of_measure character varying(50),
    environmental_rating character varying(50),
    quality_score numeric(3,2) DEFAULT 0.0,
    tags text[],
    attributes jsonb,
    search_vector tsvector,
    usage_frequency integer DEFAULT 0,
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    updated_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP
);


--
-- Name: standards_entities; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.standards_entities (
    entity_id uuid DEFAULT gen_random_uuid() NOT NULL,
    entity_type character varying(50) NOT NULL,
    canonical_name character varying(255) NOT NULL,
    source_table character varying(100) NOT NULL,
    source_id uuid NOT NULL,
    aliases text[],
    display_name character varying(255),
    description text,
    tags text[],
    status character varying(50) DEFAULT 'active'::character varying,
    quality_score numeric(4,3),
    attributes jsonb,
    search_vector tsvector,
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    updated_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP
);


--
-- Name: TABLE standards_entities; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON TABLE public.standards_entities IS 'Unified entity registry - every CAD standard, drawing element, survey point gets a canonical identity for AI reasoning';


--
-- Name: mv_entity_graph_summary; Type: MATERIALIZED VIEW; Schema: public; Owner: -
--

CREATE MATERIALIZED VIEW public.mv_entity_graph_summary AS
 SELECT se.entity_id,
    se.entity_type,
    se.canonical_name,
    se.quality_score,
    count(DISTINCT er_out.relationship_id) AS outgoing_relationship_count,
    array_agg(DISTINCT er_out.predicate) FILTER (WHERE (er_out.predicate IS NOT NULL)) AS outgoing_predicates,
    count(DISTINCT er_in.relationship_id) AS incoming_relationship_count,
    array_agg(DISTINCT er_in.predicate) FILTER (WHERE (er_in.predicate IS NOT NULL)) AS incoming_predicates,
    (count(DISTINCT er_out.relationship_id) + count(DISTINCT er_in.relationship_id)) AS total_connectivity,
    count(DISTINCT er_out.relationship_id) FILTER (WHERE (er_out.spatial_relationship = true)) AS spatial_relationship_count,
    count(DISTINCT er_out.relationship_id) FILTER (WHERE (er_out.engineering_relationship = true)) AS engineering_relationship_count,
    count(DISTINCT er_out.relationship_id) FILTER (WHERE (er_out.ai_generated = true)) AS ai_generated_relationship_count,
    se.created_at,
    se.updated_at
   FROM ((public.standards_entities se
     LEFT JOIN public.entity_relationships er_out ON ((se.entity_id = er_out.subject_entity_id)))
     LEFT JOIN public.entity_relationships er_in ON ((se.entity_id = er_in.object_entity_id)))
  GROUP BY se.entity_id, se.entity_type, se.canonical_name, se.quality_score, se.created_at, se.updated_at
  WITH NO DATA;


--
-- Name: MATERIALIZED VIEW mv_entity_graph_summary; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON MATERIALIZED VIEW public.mv_entity_graph_summary IS 'Pre-computed relationship statistics for GraphRAG queries';


--
-- Name: survey_points; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.survey_points (
    point_id uuid DEFAULT gen_random_uuid() NOT NULL,
    entity_id uuid,
    project_id uuid,
    point_number character varying(50) NOT NULL,
    point_description text,
    point_code character varying(50),
    point_type character varying(50),
    geometry public.geometry(PointZ,2226) NOT NULL,
    northing numeric(15,4),
    easting numeric(15,4),
    elevation numeric(10,4),
    coordinate_system character varying(100),
    epsg_code character varying(20),
    survey_date date,
    surveyed_by character varying(255),
    survey_method character varying(100),
    instrument_used character varying(100),
    horizontal_accuracy numeric(8,4),
    vertical_accuracy numeric(8,4),
    accuracy_units character varying(20) DEFAULT 'Feet'::character varying,
    quality_code character varying(50),
    is_control_point boolean DEFAULT false,
    is_active boolean DEFAULT true,
    superseded_by uuid,
    notes text,
    quality_score numeric(3,2) DEFAULT 0.0,
    tags text[],
    attributes jsonb,
    search_vector tsvector,
    usage_frequency integer DEFAULT 0,
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    updated_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP
);


--
-- Name: mv_spatial_clusters; Type: MATERIALIZED VIEW; Schema: public; Owner: -
--

CREATE MATERIALIZED VIEW public.mv_spatial_clusters AS
 SELECT project_id,
    point_type,
    public.st_clusterkmeans(geometry, 10) OVER (PARTITION BY project_id, point_type) AS cluster_id,
    point_id,
    point_number,
    geometry,
    entity_id,
    quality_score
   FROM public.survey_points sp
  WHERE (geometry IS NOT NULL)
  WITH NO DATA;


--
-- Name: MATERIALIZED VIEW mv_spatial_clusters; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON MATERIALIZED VIEW public.mv_spatial_clusters IS 'K-means spatial clustering of survey points for pattern recognition';


--
-- Name: mv_survey_points_enriched; Type: MATERIALIZED VIEW; Schema: public; Owner: -
--

CREATE MATERIALIZED VIEW public.mv_survey_points_enriched AS
 SELECT sp.point_id,
    sp.project_id,
    sp.point_number,
    sp.point_description,
    sp.point_type,
    sp.geometry,
    sp.northing,
    sp.easting,
    sp.elevation,
    sp.quality_score,
    sp.entity_id,
    se.canonical_name,
    se.tags,
    ( SELECT count(*) AS count
           FROM public.survey_points sp2
          WHERE ((sp2.project_id = sp.project_id) AND (sp2.point_id <> sp.point_id) AND public.st_dwithin(sp.geometry, sp2.geometry, (100)::double precision))) AS nearby_point_count,
    ( SELECT min(public.st_distance(sp.geometry, cp.geometry)) AS min
           FROM public.survey_points cp
          WHERE ((cp.project_id = sp.project_id) AND (cp.is_control_point = true) AND (cp.point_id <> sp.point_id))) AS distance_to_nearest_control,
    sp.created_at,
    sp.updated_at
   FROM (public.survey_points sp
     LEFT JOIN public.standards_entities se ON ((sp.entity_id = se.entity_id)))
  WITH NO DATA;


--
-- Name: MATERIALIZED VIEW mv_survey_points_enriched; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON MATERIALIZED VIEW public.mv_survey_points_enriched IS 'Pre-computed enriched survey points with spatial context for fast AI queries';


--
-- Name: network_metrics; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.network_metrics (
    metric_id uuid DEFAULT gen_random_uuid() NOT NULL,
    entity_id uuid NOT NULL,
    degree_centrality numeric(8,6),
    betweenness_centrality numeric(8,6),
    closeness_centrality numeric(8,6),
    eigenvector_centrality numeric(8,6),
    pagerank_score numeric(8,6),
    clustering_coefficient numeric(5,4),
    average_path_length numeric(8,2),
    eccentricity integer,
    direct_connections integer DEFAULT 0,
    two_hop_connections integer DEFAULT 0,
    total_reachable_nodes integer DEFAULT 0,
    community_id uuid,
    community_size integer,
    influence_score numeric(8,6),
    trust_score numeric(5,4),
    attributes jsonb DEFAULT '{}'::jsonb,
    computed_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    updated_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP
);


--
-- Name: TABLE network_metrics; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON TABLE public.network_metrics IS 'Graph analysis metrics for GraphRAG and network analysis';


--
-- Name: note_block_type_associations; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.note_block_type_associations (
    association_id uuid DEFAULT gen_random_uuid() NOT NULL,
    note_id integer NOT NULL,
    block_type character varying(100),
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP
);


--
-- Name: TABLE note_block_type_associations; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON TABLE public.note_block_type_associations IS 'Links standard notes to specific CAD block types (future feature)';


--
-- Name: note_callouts; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.note_callouts (
    callout_id uuid DEFAULT gen_random_uuid() NOT NULL,
    assignment_id uuid NOT NULL,
    location_x double precision,
    location_y double precision,
    callout_style character varying(50),
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP
);


--
-- Name: TABLE note_callouts; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON TABLE public.note_callouts IS 'Spatial locations on drawings where notes are called out (future feature)';


--
-- Name: parcel_corners; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.parcel_corners (
    corner_id uuid DEFAULT gen_random_uuid() NOT NULL,
    entity_id uuid,
    parcel_id uuid,
    survey_point_id uuid,
    corner_number integer,
    corner_type character varying(50),
    monument_type character varying(50),
    monument_description text,
    bearing_to_next numeric(10,4),
    distance_to_next numeric(12,4),
    curve_data jsonb,
    notes text,
    quality_score numeric(3,2) DEFAULT 0.0,
    tags text[],
    attributes jsonb,
    search_vector tsvector,
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    updated_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP
);


--
-- Name: parcels; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.parcels (
    parcel_id uuid DEFAULT gen_random_uuid() NOT NULL,
    entity_id uuid,
    project_id uuid,
    parcel_number character varying(100),
    parcel_name character varying(255),
    owner_name character varying(255),
    owner_address text,
    legal_description text,
    area_sqft numeric(15,4),
    area_acres numeric(15,4),
    perimeter numeric(12,4),
    zoning character varying(100),
    land_use character varying(100),
    assessed_value numeric(15,2),
    boundary_geometry public.geometry(PolygonZ,2226) NOT NULL,
    notes text,
    quality_score numeric(3,2) DEFAULT 0.0,
    tags text[],
    attributes jsonb,
    search_vector tsvector,
    usage_frequency integer DEFAULT 0,
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    updated_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP
);


--
-- Name: pavement_sections; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.pavement_sections (
    section_id uuid DEFAULT gen_random_uuid() NOT NULL,
    entity_id uuid,
    project_id uuid,
    alignment_id uuid,
    section_name character varying(255) NOT NULL,
    section_code character varying(50),
    start_station numeric(10,4),
    end_station numeric(10,4),
    pavement_type character varying(50),
    design_life_years integer,
    traffic_index numeric(8,2),
    design_esal numeric(15,2),
    layer_structure jsonb,
    total_thickness_in numeric(6,2),
    subgrade_r_value integer,
    subgrade_cbr integer,
    design_notes text,
    quality_score numeric(3,2) DEFAULT 0.0,
    tags text[],
    attributes jsonb,
    search_vector tsvector,
    usage_frequency integer DEFAULT 0,
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    updated_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP
);


--
-- Name: plot_styles; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.plot_styles (
    plot_style_id uuid DEFAULT gen_random_uuid() NOT NULL,
    plot_style_name character varying(100) NOT NULL,
    style_type character varying(50),
    description text,
    color_mode character varying(50),
    lineweight_mode character varying(50),
    linetype_mode character varying(50),
    entity_id uuid,
    quality_score numeric(4,3),
    usage_frequency integer DEFAULT 0,
    tags text[],
    attributes jsonb DEFAULT '{}'::jsonb,
    search_vector tsvector,
    ctb_file_path text,
    stb_file_path text,
    is_active boolean DEFAULT true,
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    updated_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP
);


--
-- Name: TABLE plot_styles; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON TABLE public.plot_styles IS 'Plot style standards - AI-optimized with usage tracking';


--
-- Name: profile_pvis; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.profile_pvis (
    pvi_id uuid DEFAULT gen_random_uuid() NOT NULL,
    entity_id uuid,
    profile_id uuid,
    pvi_number integer NOT NULL,
    station numeric(10,4) NOT NULL,
    elevation numeric(12,4),
    grade_in numeric(8,4),
    grade_out numeric(8,4),
    vertical_curve_length numeric(10,4),
    k_value numeric(10,4),
    high_low_point_station numeric(10,4),
    high_low_point_elevation numeric(12,4),
    notes text,
    quality_score numeric(3,2) DEFAULT 0.0,
    tags text[],
    attributes jsonb,
    search_vector tsvector,
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    updated_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP
);


--
-- Name: project_details; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.project_details (
    project_id uuid NOT NULL,
    project_address text,
    project_city character varying(100),
    project_state character varying(2),
    project_zip character varying(10),
    engineer_name character varying(200),
    engineer_license character varying(50),
    jurisdiction character varying(200),
    permit_number character varying(100),
    contact_name character varying(200),
    contact_phone character varying(20),
    contact_email character varying(200),
    notes text,
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    updated_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP
);


--
-- Name: project_sheet_notes; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.project_sheet_notes (
    project_note_id uuid DEFAULT gen_random_uuid() NOT NULL,
    entity_id uuid,
    set_id uuid NOT NULL,
    standard_note_id uuid,
    display_code character varying(20) NOT NULL,
    custom_title character varying(255),
    custom_text text,
    is_modified boolean DEFAULT false,
    sort_order integer DEFAULT 0,
    quality_score numeric(3,2) DEFAULT 0.0,
    tags text[],
    attributes jsonb,
    search_vector tsvector,
    usage_frequency integer DEFAULT 0,
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    updated_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP
);


--
-- Name: projects; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.projects (
    project_id uuid DEFAULT gen_random_uuid() NOT NULL,
    project_name character varying(255) NOT NULL,
    project_number character varying(100),
    client_name character varying(255),
    description text,
    entity_id uuid,
    quality_score numeric(4,3),
    tags text[],
    attributes jsonb DEFAULT '{}'::jsonb,
    search_vector tsvector,
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    updated_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP
);


--
-- Name: TABLE projects; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON TABLE public.projects IS 'Projects table - AI-optimized with entity linking, quality scores, and semantic search';


--
-- Name: right_of_way; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.right_of_way (
    row_id uuid DEFAULT gen_random_uuid() NOT NULL,
    entity_id uuid,
    project_id uuid,
    row_name character varying(255) NOT NULL,
    row_type character varying(50),
    ownership character varying(255),
    jurisdiction character varying(255),
    dedication_info text,
    dedication_date date,
    width numeric(10,4),
    boundary_geometry public.geometry(GeometryZ,2226) NOT NULL,
    area_sqft numeric(15,4),
    notes text,
    quality_score numeric(3,2) DEFAULT 0.0,
    tags text[],
    attributes jsonb,
    search_vector tsvector,
    usage_frequency integer DEFAULT 0,
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    updated_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP
);


--
-- Name: sheet_category_standards; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.sheet_category_standards (
    category_id uuid DEFAULT gen_random_uuid() NOT NULL,
    category_code character varying(20) NOT NULL,
    category_name character varying(100) NOT NULL,
    default_hierarchy_number integer NOT NULL,
    description text,
    is_active boolean DEFAULT true,
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP
);


--
-- Name: TABLE sheet_category_standards; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON TABLE public.sheet_category_standards IS 'Standard sheet categories with hierarchy ordering';


--
-- Name: sheet_note_sets; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.sheet_note_sets (
    set_id uuid DEFAULT gen_random_uuid() NOT NULL,
    entity_id uuid,
    project_id uuid NOT NULL,
    set_name character varying(255) NOT NULL,
    description text,
    discipline character varying(50),
    is_active boolean DEFAULT false,
    quality_score numeric(3,2) DEFAULT 0.0,
    tags text[],
    attributes jsonb,
    search_vector tsvector,
    usage_frequency integer DEFAULT 0,
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    updated_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP
);


--
-- Name: sheet_relationships; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.sheet_relationships (
    relationship_id uuid DEFAULT gen_random_uuid() NOT NULL,
    entity_id uuid,
    source_sheet_id uuid NOT NULL,
    target_sheet_id uuid NOT NULL,
    relationship_type character varying(50) NOT NULL,
    notes text,
    quality_score numeric(3,2) DEFAULT 0.0,
    tags text[],
    attributes jsonb,
    search_vector tsvector,
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    updated_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP
);


--
-- Name: sheet_revisions; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.sheet_revisions (
    revision_id uuid DEFAULT gen_random_uuid() NOT NULL,
    entity_id uuid,
    sheet_id uuid NOT NULL,
    revision_number integer NOT NULL,
    revision_date date NOT NULL,
    description text,
    revised_by character varying(200),
    quality_score numeric(3,2) DEFAULT 0.0,
    tags text[],
    attributes jsonb,
    search_vector tsvector,
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    updated_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP
);


--
-- Name: sheet_templates; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.sheet_templates (
    template_id uuid DEFAULT gen_random_uuid() NOT NULL,
    template_name character varying(100),
    sheet_size character varying(20),
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP
);


--
-- Name: sheets; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.sheets (
    sheet_id uuid DEFAULT gen_random_uuid() NOT NULL,
    entity_id uuid,
    set_id uuid NOT NULL,
    sheet_number integer,
    sheet_code character varying(50) NOT NULL,
    sheet_title character varying(300) NOT NULL,
    discipline_code character varying(10),
    sheet_type character varying(50),
    category_code character varying(20),
    sheet_hierarchy_number integer,
    scale character varying(50),
    sheet_size character varying(20) DEFAULT '24x36'::character varying,
    template_id uuid,
    revision_number integer DEFAULT 0,
    revision_date date,
    notes text,
    quality_score numeric(3,2) DEFAULT 0.0,
    tags text[],
    attributes jsonb,
    search_vector tsvector,
    usage_frequency integer DEFAULT 0,
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    updated_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP
);


--
-- Name: site_trees; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.site_trees (
    tree_id uuid DEFAULT gen_random_uuid() NOT NULL,
    entity_id uuid,
    project_id uuid,
    survey_point_id uuid,
    tree_number character varying(50),
    species character varying(100),
    common_name character varying(100),
    dbh_inches numeric(6,2),
    tree_height_ft numeric(6,2),
    canopy_spread_ft numeric(6,2),
    condition character varying(50),
    protection_status character varying(100),
    location_description text,
    planting_date date,
    notes text,
    quality_score numeric(3,2) DEFAULT 0.0,
    tags text[],
    attributes jsonb,
    search_vector tsvector,
    usage_frequency integer DEFAULT 0,
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    updated_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP
);


--
-- Name: spatial_statistics; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.spatial_statistics (
    stat_id uuid DEFAULT gen_random_uuid() NOT NULL,
    project_id uuid NOT NULL,
    region_name character varying(255),
    region_geometry public.geometry(Polygon,2226),
    point_count integer,
    point_density numeric(12,4),
    points_per_acre numeric(10,2),
    min_elevation numeric(10,4),
    max_elevation numeric(10,4),
    mean_elevation numeric(10,4),
    elevation_variance numeric(12,4),
    elevation_std_dev numeric(10,4),
    spatial_dispersion numeric(12,4),
    nearest_neighbor_index numeric(8,4),
    clustering_coefficient numeric(5,4),
    control_point_count integer DEFAULT 0,
    topo_point_count integer DEFAULT 0,
    tree_count integer DEFAULT 0,
    utility_count integer DEFAULT 0,
    area_square_feet numeric(15,2),
    area_acres numeric(10,3),
    attributes jsonb DEFAULT '{}'::jsonb,
    computed_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    updated_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP
);


--
-- Name: TABLE spatial_statistics; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON TABLE public.spatial_statistics IS 'Pre-computed spatial statistics for ML feature engineering';


--
-- Name: standard_notes; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.standard_notes (
    note_id uuid DEFAULT gen_random_uuid() NOT NULL,
    entity_id uuid,
    note_title character varying(255) NOT NULL,
    note_text text NOT NULL,
    note_category character varying(100),
    discipline character varying(50),
    sort_order integer DEFAULT 0,
    quality_score numeric(3,2) DEFAULT 0.0,
    tags text[],
    attributes jsonb,
    search_vector tsvector,
    usage_frequency integer DEFAULT 0,
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    updated_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP
);


--
-- Name: surface_features; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.surface_features (
    feature_id uuid DEFAULT gen_random_uuid() NOT NULL,
    entity_id uuid,
    project_id uuid,
    survey_point_id uuid,
    feature_type character varying(100),
    geometry public.geometry(GeometryZ,2226) NOT NULL,
    material character varying(100),
    dimensions jsonb,
    description text,
    notes text,
    quality_score numeric(3,2) DEFAULT 0.0,
    tags text[],
    attributes jsonb,
    search_vector tsvector,
    usage_frequency integer DEFAULT 0,
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    updated_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP
);


--
-- Name: surface_models; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.surface_models (
    surface_id uuid DEFAULT gen_random_uuid() NOT NULL,
    entity_id uuid,
    project_id uuid,
    surface_name character varying(255) NOT NULL,
    surface_type character varying(50),
    description text,
    data_source character varying(255),
    point_count integer,
    triangle_count integer,
    min_elevation numeric(12,4),
    max_elevation numeric(12,4),
    bounding_box jsonb,
    file_reference text,
    created_by character varying(255),
    quality_score numeric(3,2) DEFAULT 0.0,
    tags text[],
    attributes jsonb,
    search_vector tsvector,
    usage_frequency integer DEFAULT 0,
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    updated_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP
);


--
-- Name: survey_control_network; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.survey_control_network (
    network_id uuid DEFAULT gen_random_uuid() NOT NULL,
    entity_id uuid,
    project_id uuid,
    network_name character varying(255) NOT NULL,
    network_type character varying(50),
    network_order character varying(50),
    description text,
    adjustment_method character varying(100),
    adjustment_date date,
    adjustment_software character varying(100),
    standard_error_h numeric(10,4),
    standard_error_v numeric(10,4),
    confidence_level numeric(5,2),
    is_active boolean DEFAULT true,
    notes text,
    quality_score numeric(3,2) DEFAULT 0.0,
    tags text[],
    attributes jsonb,
    search_vector tsvector,
    usage_frequency integer DEFAULT 0,
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    updated_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP
);


--
-- Name: survey_observations; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.survey_observations (
    observation_id uuid DEFAULT gen_random_uuid() NOT NULL,
    entity_id uuid,
    project_id uuid,
    session_id character varying(100),
    observation_type character varying(50) NOT NULL,
    observation_date date,
    observation_time time without time zone,
    instrument_station_point_id uuid,
    backsight_point_id uuid,
    target_point_id uuid,
    horizontal_angle numeric(12,6),
    vertical_angle numeric(12,6),
    slope_distance numeric(12,4),
    horizontal_distance numeric(12,4),
    vertical_distance numeric(12,4),
    instrument_height numeric(8,4),
    target_height numeric(8,4),
    temperature_f numeric(6,2),
    pressure_inhg numeric(6,2),
    ppm_correction numeric(8,4),
    standard_deviation numeric(10,6),
    rejected boolean DEFAULT false,
    raw_data jsonb,
    notes text,
    quality_score numeric(3,2) DEFAULT 0.0,
    tags text[],
    attributes jsonb,
    search_vector tsvector,
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    updated_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP
);


--
-- Name: temporal_changes; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.temporal_changes (
    change_id uuid DEFAULT gen_random_uuid() NOT NULL,
    entity_id uuid NOT NULL,
    change_type character varying(50) NOT NULL,
    change_description text,
    changed_fields text[],
    state_before jsonb,
    state_after jsonb,
    state_diff jsonb,
    change_magnitude numeric(8,6),
    significance_score numeric(5,4),
    geometry_before public.geometry(GeometryZ,2226),
    geometry_after public.geometry(GeometryZ,2226),
    spatial_displacement numeric(12,4),
    changed_by character varying(255),
    change_source character varying(100),
    change_reason text,
    change_timestamp timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP
);


--
-- Name: TABLE temporal_changes; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON TABLE public.temporal_changes IS 'Temporal change tracking for ML time-series analysis and audit trails';


--
-- Name: text_styles; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.text_styles (
    style_id uuid DEFAULT gen_random_uuid() NOT NULL,
    style_name character varying(100) NOT NULL,
    font_name character varying(100),
    font_file character varying(255),
    height numeric(10,4),
    width_factor numeric(5,3),
    oblique_angle numeric(5,2),
    description text,
    usage_context character varying(255),
    discipline character varying(50),
    entity_id uuid,
    quality_score numeric(4,3),
    usage_frequency integer DEFAULT 0,
    tags text[],
    attributes jsonb DEFAULT '{}'::jsonb,
    search_vector tsvector,
    is_active boolean DEFAULT true,
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    updated_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP
);


--
-- Name: TABLE text_styles; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON TABLE public.text_styles IS 'Text style standards - AI-optimized with usage tracking';


--
-- Name: traverse_loop_observations; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.traverse_loop_observations (
    loop_observation_id uuid DEFAULT gen_random_uuid() NOT NULL,
    entity_id uuid,
    loop_id uuid,
    observation_id uuid,
    sequence_order integer NOT NULL,
    point_id uuid,
    bearing_from_prev numeric(10,4),
    distance_from_prev numeric(12,4),
    adjusted_bearing numeric(10,4),
    adjusted_distance numeric(12,4),
    notes text,
    quality_score numeric(3,2) DEFAULT 0.0,
    tags text[],
    attributes jsonb,
    search_vector tsvector,
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    updated_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP
);


--
-- Name: traverse_loops; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.traverse_loops (
    loop_id uuid DEFAULT gen_random_uuid() NOT NULL,
    entity_id uuid,
    project_id uuid,
    loop_name character varying(255) NOT NULL,
    description text,
    loop_type character varying(50),
    adjustment_method character varying(100),
    adjustment_date date,
    angular_misclosure numeric(12,6),
    linear_misclosure numeric(12,4),
    closure_ratio character varying(50),
    closure_error_h numeric(10,4),
    closure_error_v numeric(10,4),
    adjustment_notes text,
    quality_score numeric(3,2) DEFAULT 0.0,
    tags text[],
    attributes jsonb,
    search_vector tsvector,
    usage_frequency integer DEFAULT 0,
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    updated_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP
);


--
-- Name: typical_sections; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.typical_sections (
    typical_section_id uuid DEFAULT gen_random_uuid() NOT NULL,
    entity_id uuid,
    project_id uuid,
    section_name character varying(255) NOT NULL,
    section_code character varying(50),
    road_type character varying(100),
    design_speed_mph integer,
    lane_count integer,
    lane_width_ft numeric(6,2),
    shoulder_width_left_ft numeric(6,2),
    shoulder_width_right_ft numeric(6,2),
    slope_cut character varying(20),
    slope_fill character varying(20),
    curb_height_in numeric(6,2),
    crown_slope_pct numeric(6,4),
    superelevation_max_pct numeric(6,4),
    section_data jsonb,
    description text,
    quality_score numeric(3,2) DEFAULT 0.0,
    tags text[],
    attributes jsonb,
    search_vector tsvector,
    usage_frequency integer DEFAULT 0,
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    updated_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP
);


--
-- Name: utility_lines; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.utility_lines (
    line_id uuid DEFAULT gen_random_uuid() NOT NULL,
    entity_id uuid,
    project_id uuid,
    line_number character varying(50),
    utility_system character varying(100) NOT NULL,
    line_type character varying(100),
    material character varying(100),
    diameter_mm integer,
    invert_elevation_start numeric(10,4),
    invert_elevation_end numeric(10,4),
    slope numeric(8,4),
    length numeric(12,4),
    flow_direction character varying(50),
    design_flow numeric(12,4),
    capacity numeric(12,4),
    pressure_psi numeric(8,2),
    from_structure_id uuid,
    to_structure_id uuid,
    geometry public.geometry(LineStringZ,2226) NOT NULL,
    owner character varying(255),
    install_date date,
    condition character varying(50),
    notes text,
    quality_score numeric(3,2) DEFAULT 0.0,
    tags text[],
    attributes jsonb,
    search_vector tsvector,
    usage_frequency integer DEFAULT 0,
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    updated_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP
);


--
-- Name: utility_network_connectivity; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.utility_network_connectivity (
    connection_id uuid DEFAULT gen_random_uuid() NOT NULL,
    entity_id uuid,
    from_element_id uuid NOT NULL,
    from_element_type character varying(50) NOT NULL,
    to_element_id uuid NOT NULL,
    to_element_type character varying(50) NOT NULL,
    connection_type character varying(50),
    flow_direction character varying(50),
    notes text,
    quality_score numeric(3,2) DEFAULT 0.0,
    tags text[],
    attributes jsonb,
    search_vector tsvector,
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    updated_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP
);


--
-- Name: utility_service_connections; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.utility_service_connections (
    service_id uuid DEFAULT gen_random_uuid() NOT NULL,
    entity_id uuid,
    line_id uuid,
    structure_id uuid,
    service_point_geometry public.geometry(PointZ,2226),
    service_type character varying(50),
    service_address character varying(255),
    size_mm integer,
    material character varying(100),
    customer_account character varying(100),
    install_date date,
    notes text,
    quality_score numeric(3,2) DEFAULT 0.0,
    tags text[],
    attributes jsonb,
    search_vector tsvector,
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    updated_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP
);


--
-- Name: utility_structures; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.utility_structures (
    structure_id uuid DEFAULT gen_random_uuid() NOT NULL,
    entity_id uuid,
    project_id uuid,
    survey_point_id uuid,
    structure_number character varying(50),
    structure_type character varying(100),
    utility_system character varying(100),
    rim_elevation numeric(10,4),
    invert_elevation numeric(10,4),
    rim_geometry public.geometry(PointZ,2226),
    size_mm integer,
    material character varying(100),
    manhole_depth_ft numeric(6,2),
    condition character varying(50),
    owner character varying(255),
    install_date date,
    notes text,
    quality_score numeric(3,2) DEFAULT 0.0,
    tags text[],
    attributes jsonb,
    search_vector tsvector,
    usage_frequency integer DEFAULT 0,
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    updated_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP
);


--
-- Name: vertical_profiles; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.vertical_profiles (
    profile_id uuid DEFAULT gen_random_uuid() NOT NULL,
    entity_id uuid,
    alignment_id uuid,
    profile_name character varying(255) NOT NULL,
    description text,
    profile_type character varying(50),
    quality_score numeric(3,2) DEFAULT 0.0,
    tags text[],
    attributes jsonb,
    search_vector tsvector,
    usage_frequency integer DEFAULT 0,
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    updated_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP
);


--
-- Name: abbreviation_standards abbreviation_standards_abbreviation_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.abbreviation_standards
    ADD CONSTRAINT abbreviation_standards_abbreviation_key UNIQUE (abbreviation);


--
-- Name: abbreviation_standards abbreviation_standards_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.abbreviation_standards
    ADD CONSTRAINT abbreviation_standards_pkey PRIMARY KEY (abbreviation_id);


--
-- Name: alignment_pis alignment_pis_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.alignment_pis
    ADD CONSTRAINT alignment_pis_pkey PRIMARY KEY (pi_id);


--
-- Name: annotation_standards annotation_standards_annotation_name_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.annotation_standards
    ADD CONSTRAINT annotation_standards_annotation_name_key UNIQUE (annotation_name);


--
-- Name: annotation_standards annotation_standards_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.annotation_standards
    ADD CONSTRAINT annotation_standards_pkey PRIMARY KEY (annotation_id);


--
-- Name: block_definitions block_definitions_block_name_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.block_definitions
    ADD CONSTRAINT block_definitions_block_name_key UNIQUE (block_name);


--
-- Name: block_definitions block_definitions_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.block_definitions
    ADD CONSTRAINT block_definitions_pkey PRIMARY KEY (block_id);


--
-- Name: block_inserts block_inserts_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.block_inserts
    ADD CONSTRAINT block_inserts_pkey PRIMARY KEY (insert_id);


--
-- Name: block_standards block_standards_block_name_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.block_standards
    ADD CONSTRAINT block_standards_block_name_key UNIQUE (block_name);


--
-- Name: block_standards block_standards_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.block_standards
    ADD CONSTRAINT block_standards_pkey PRIMARY KEY (block_standard_id);


--
-- Name: category_standards category_standards_category_name_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.category_standards
    ADD CONSTRAINT category_standards_category_name_key UNIQUE (category_name);


--
-- Name: category_standards category_standards_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.category_standards
    ADD CONSTRAINT category_standards_pkey PRIMARY KEY (category_id);


--
-- Name: classification_confidence classification_confidence_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.classification_confidence
    ADD CONSTRAINT classification_confidence_pkey PRIMARY KEY (prediction_id);


--
-- Name: code_standards code_standards_code_name_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.code_standards
    ADD CONSTRAINT code_standards_code_name_key UNIQUE (code_name);


--
-- Name: code_standards code_standards_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.code_standards
    ADD CONSTRAINT code_standards_pkey PRIMARY KEY (code_id);


--
-- Name: color_standards color_standards_color_name_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.color_standards
    ADD CONSTRAINT color_standards_color_name_key UNIQUE (color_name);


--
-- Name: color_standards color_standards_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.color_standards
    ADD CONSTRAINT color_standards_pkey PRIMARY KEY (color_id);


--
-- Name: control_point_membership control_point_membership_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.control_point_membership
    ADD CONSTRAINT control_point_membership_pkey PRIMARY KEY (membership_id);


--
-- Name: coordinate_systems coordinate_systems_epsg_code_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.coordinate_systems
    ADD CONSTRAINT coordinate_systems_epsg_code_key UNIQUE (epsg_code);


--
-- Name: coordinate_systems coordinate_systems_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.coordinate_systems
    ADD CONSTRAINT coordinate_systems_pkey PRIMARY KEY (system_id);


--
-- Name: cross_section_points cross_section_points_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.cross_section_points
    ADD CONSTRAINT cross_section_points_pkey PRIMARY KEY (xsection_point_id);


--
-- Name: cross_sections cross_sections_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.cross_sections
    ADD CONSTRAINT cross_sections_pkey PRIMARY KEY (section_id);


--
-- Name: detail_standards detail_standards_detail_number_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.detail_standards
    ADD CONSTRAINT detail_standards_detail_number_key UNIQUE (detail_number);


--
-- Name: detail_standards detail_standards_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.detail_standards
    ADD CONSTRAINT detail_standards_pkey PRIMARY KEY (detail_id);


--
-- Name: dimension_styles dimension_styles_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.dimension_styles
    ADD CONSTRAINT dimension_styles_pkey PRIMARY KEY (dimension_style_id);


--
-- Name: dimension_styles dimension_styles_style_name_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.dimension_styles
    ADD CONSTRAINT dimension_styles_style_name_key UNIQUE (style_name);


--
-- Name: drawing_dimensions drawing_dimensions_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.drawing_dimensions
    ADD CONSTRAINT drawing_dimensions_pkey PRIMARY KEY (dimension_id);


--
-- Name: drawing_entities drawing_entities_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.drawing_entities
    ADD CONSTRAINT drawing_entities_pkey PRIMARY KEY (entity_id);


--
-- Name: drawing_hatches drawing_hatches_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.drawing_hatches
    ADD CONSTRAINT drawing_hatches_pkey PRIMARY KEY (hatch_id);


--
-- Name: drawing_layer_usage drawing_layer_usage_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.drawing_layer_usage
    ADD CONSTRAINT drawing_layer_usage_pkey PRIMARY KEY (usage_id);


--
-- Name: drawing_linetype_usage drawing_linetype_usage_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.drawing_linetype_usage
    ADD CONSTRAINT drawing_linetype_usage_pkey PRIMARY KEY (usage_id);


--
-- Name: drawing_scale_standards drawing_scale_standards_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.drawing_scale_standards
    ADD CONSTRAINT drawing_scale_standards_pkey PRIMARY KEY (scale_id);


--
-- Name: drawing_scale_standards drawing_scale_standards_scale_name_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.drawing_scale_standards
    ADD CONSTRAINT drawing_scale_standards_scale_name_key UNIQUE (scale_name);


--
-- Name: drawing_text drawing_text_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.drawing_text
    ADD CONSTRAINT drawing_text_pkey PRIMARY KEY (text_id);


--
-- Name: earthwork_balance earthwork_balance_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.earthwork_balance
    ADD CONSTRAINT earthwork_balance_pkey PRIMARY KEY (balance_id);


--
-- Name: earthwork_quantities earthwork_quantities_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.earthwork_quantities
    ADD CONSTRAINT earthwork_quantities_pkey PRIMARY KEY (earthwork_id);


--
-- Name: easements easements_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.easements
    ADD CONSTRAINT easements_pkey PRIMARY KEY (easement_id);


--
-- Name: embedding_models embedding_models_model_name_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.embedding_models
    ADD CONSTRAINT embedding_models_model_name_key UNIQUE (model_name);


--
-- Name: embedding_models embedding_models_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.embedding_models
    ADD CONSTRAINT embedding_models_pkey PRIMARY KEY (model_id);


--
-- Name: entity_aliases entity_aliases_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.entity_aliases
    ADD CONSTRAINT entity_aliases_pkey PRIMARY KEY (alias_id);


--
-- Name: entity_embeddings entity_embeddings_entity_id_model_id_version_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.entity_embeddings
    ADD CONSTRAINT entity_embeddings_entity_id_model_id_version_key UNIQUE (entity_id, model_id, version);


--
-- Name: entity_embeddings entity_embeddings_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.entity_embeddings
    ADD CONSTRAINT entity_embeddings_pkey PRIMARY KEY (embedding_id);


--
-- Name: entity_relationships entity_relationships_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.entity_relationships
    ADD CONSTRAINT entity_relationships_pkey PRIMARY KEY (relationship_id);


--
-- Name: entity_relationships entity_relationships_subject_entity_id_predicate_object_ent_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.entity_relationships
    ADD CONSTRAINT entity_relationships_subject_entity_id_predicate_object_ent_key UNIQUE (subject_entity_id, predicate, object_entity_id);


--
-- Name: export_jobs export_jobs_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.export_jobs
    ADD CONSTRAINT export_jobs_pkey PRIMARY KEY (job_id);


--
-- Name: grading_limits grading_limits_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.grading_limits
    ADD CONSTRAINT grading_limits_pkey PRIMARY KEY (limit_id);


--
-- Name: hatch_patterns hatch_patterns_pattern_name_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.hatch_patterns
    ADD CONSTRAINT hatch_patterns_pattern_name_key UNIQUE (pattern_name);


--
-- Name: hatch_patterns hatch_patterns_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.hatch_patterns
    ADD CONSTRAINT hatch_patterns_pkey PRIMARY KEY (hatch_id);


--
-- Name: horizontal_alignments horizontal_alignments_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.horizontal_alignments
    ADD CONSTRAINT horizontal_alignments_pkey PRIMARY KEY (alignment_id);


--
-- Name: layer_standards layer_standards_layer_name_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.layer_standards
    ADD CONSTRAINT layer_standards_layer_name_key UNIQUE (layer_name);


--
-- Name: layer_standards layer_standards_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.layer_standards
    ADD CONSTRAINT layer_standards_pkey PRIMARY KEY (layer_id);


--
-- Name: layers layers_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.layers
    ADD CONSTRAINT layers_pkey PRIMARY KEY (layer_id);


--
-- Name: layout_viewports layout_viewports_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.layout_viewports
    ADD CONSTRAINT layout_viewports_pkey PRIMARY KEY (viewport_id);


--
-- Name: linetypes linetypes_linetype_name_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.linetypes
    ADD CONSTRAINT linetypes_linetype_name_key UNIQUE (linetype_name);


--
-- Name: linetypes linetypes_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.linetypes
    ADD CONSTRAINT linetypes_pkey PRIMARY KEY (linetype_id);


--
-- Name: material_standards material_standards_material_name_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.material_standards
    ADD CONSTRAINT material_standards_material_name_key UNIQUE (material_name);


--
-- Name: material_standards material_standards_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.material_standards
    ADD CONSTRAINT material_standards_pkey PRIMARY KEY (material_id);


--
-- Name: network_metrics network_metrics_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.network_metrics
    ADD CONSTRAINT network_metrics_pkey PRIMARY KEY (metric_id);


--
-- Name: note_block_type_associations note_block_type_associations_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.note_block_type_associations
    ADD CONSTRAINT note_block_type_associations_pkey PRIMARY KEY (association_id);


--
-- Name: note_callouts note_callouts_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.note_callouts
    ADD CONSTRAINT note_callouts_pkey PRIMARY KEY (callout_id);


--
-- Name: parcel_corners parcel_corners_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.parcel_corners
    ADD CONSTRAINT parcel_corners_pkey PRIMARY KEY (corner_id);


--
-- Name: parcels parcels_parcel_number_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.parcels
    ADD CONSTRAINT parcels_parcel_number_key UNIQUE (parcel_number);


--
-- Name: parcels parcels_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.parcels
    ADD CONSTRAINT parcels_pkey PRIMARY KEY (parcel_id);


--
-- Name: pavement_sections pavement_sections_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.pavement_sections
    ADD CONSTRAINT pavement_sections_pkey PRIMARY KEY (section_id);


--
-- Name: plot_styles plot_styles_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.plot_styles
    ADD CONSTRAINT plot_styles_pkey PRIMARY KEY (plot_style_id);


--
-- Name: plot_styles plot_styles_plot_style_name_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.plot_styles
    ADD CONSTRAINT plot_styles_plot_style_name_key UNIQUE (plot_style_name);


--
-- Name: profile_pvis profile_pvis_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.profile_pvis
    ADD CONSTRAINT profile_pvis_pkey PRIMARY KEY (pvi_id);


--
-- Name: project_details project_details_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.project_details
    ADD CONSTRAINT project_details_pkey PRIMARY KEY (project_id);


--
-- Name: project_sheet_notes project_sheet_notes_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.project_sheet_notes
    ADD CONSTRAINT project_sheet_notes_pkey PRIMARY KEY (project_note_id);


--
-- Name: projects projects_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.projects
    ADD CONSTRAINT projects_pkey PRIMARY KEY (project_id);


--
-- Name: right_of_way right_of_way_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.right_of_way
    ADD CONSTRAINT right_of_way_pkey PRIMARY KEY (row_id);


--
-- Name: sheet_category_standards sheet_category_standards_category_code_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.sheet_category_standards
    ADD CONSTRAINT sheet_category_standards_category_code_key UNIQUE (category_code);


--
-- Name: sheet_category_standards sheet_category_standards_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.sheet_category_standards
    ADD CONSTRAINT sheet_category_standards_pkey PRIMARY KEY (category_id);


--
-- Name: sheet_drawing_assignments sheet_drawing_assignments_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.sheet_drawing_assignments
    ADD CONSTRAINT sheet_drawing_assignments_pkey PRIMARY KEY (assignment_id);


--
-- Name: sheet_drawing_assignments sheet_drawing_assignments_sheet_id_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.sheet_drawing_assignments
    ADD CONSTRAINT sheet_drawing_assignments_sheet_id_key UNIQUE (sheet_id);


--
-- Name: sheet_note_assignments sheet_note_assignments_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.sheet_note_assignments
    ADD CONSTRAINT sheet_note_assignments_pkey PRIMARY KEY (assignment_id);


--
-- Name: sheet_note_sets sheet_note_sets_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.sheet_note_sets
    ADD CONSTRAINT sheet_note_sets_pkey PRIMARY KEY (set_id);


--
-- Name: sheet_relationships sheet_relationships_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.sheet_relationships
    ADD CONSTRAINT sheet_relationships_pkey PRIMARY KEY (relationship_id);


--
-- Name: sheet_relationships sheet_relationships_source_sheet_id_target_sheet_id_relatio_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.sheet_relationships
    ADD CONSTRAINT sheet_relationships_source_sheet_id_target_sheet_id_relatio_key UNIQUE (source_sheet_id, target_sheet_id, relationship_type);


--
-- Name: sheet_revisions sheet_revisions_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.sheet_revisions
    ADD CONSTRAINT sheet_revisions_pkey PRIMARY KEY (revision_id);


--
-- Name: sheet_sets sheet_sets_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.sheet_sets
    ADD CONSTRAINT sheet_sets_pkey PRIMARY KEY (set_id);


--
-- Name: sheet_templates sheet_templates_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.sheet_templates
    ADD CONSTRAINT sheet_templates_pkey PRIMARY KEY (template_id);


--
-- Name: sheets sheets_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.sheets
    ADD CONSTRAINT sheets_pkey PRIMARY KEY (sheet_id);


--
-- Name: sheets sheets_set_id_sheet_code_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.sheets
    ADD CONSTRAINT sheets_set_id_sheet_code_key UNIQUE (set_id, sheet_code);


--
-- Name: sheets sheets_set_id_sheet_number_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.sheets
    ADD CONSTRAINT sheets_set_id_sheet_number_key UNIQUE (set_id, sheet_number);


--
-- Name: site_trees site_trees_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.site_trees
    ADD CONSTRAINT site_trees_pkey PRIMARY KEY (tree_id);


--
-- Name: spatial_statistics spatial_statistics_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.spatial_statistics
    ADD CONSTRAINT spatial_statistics_pkey PRIMARY KEY (stat_id);


--
-- Name: standard_notes standard_notes_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.standard_notes
    ADD CONSTRAINT standard_notes_pkey PRIMARY KEY (note_id);


--
-- Name: standards_entities standards_entities_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.standards_entities
    ADD CONSTRAINT standards_entities_pkey PRIMARY KEY (entity_id);


--
-- Name: standards_entities standards_entities_source_table_source_id_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.standards_entities
    ADD CONSTRAINT standards_entities_source_table_source_id_key UNIQUE (source_table, source_id);


--
-- Name: surface_features surface_features_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.surface_features
    ADD CONSTRAINT surface_features_pkey PRIMARY KEY (feature_id);


--
-- Name: surface_models surface_models_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.surface_models
    ADD CONSTRAINT surface_models_pkey PRIMARY KEY (surface_id);


--
-- Name: survey_control_network survey_control_network_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.survey_control_network
    ADD CONSTRAINT survey_control_network_pkey PRIMARY KEY (network_id);


--
-- Name: survey_observations survey_observations_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.survey_observations
    ADD CONSTRAINT survey_observations_pkey PRIMARY KEY (observation_id);


--
-- Name: survey_points survey_points_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.survey_points
    ADD CONSTRAINT survey_points_pkey PRIMARY KEY (point_id);


--
-- Name: temporal_changes temporal_changes_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.temporal_changes
    ADD CONSTRAINT temporal_changes_pkey PRIMARY KEY (change_id);


--
-- Name: text_styles text_styles_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.text_styles
    ADD CONSTRAINT text_styles_pkey PRIMARY KEY (style_id);


--
-- Name: text_styles text_styles_style_name_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.text_styles
    ADD CONSTRAINT text_styles_style_name_key UNIQUE (style_name);


--
-- Name: traverse_loop_observations traverse_loop_observations_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.traverse_loop_observations
    ADD CONSTRAINT traverse_loop_observations_pkey PRIMARY KEY (loop_observation_id);


--
-- Name: traverse_loops traverse_loops_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.traverse_loops
    ADD CONSTRAINT traverse_loops_pkey PRIMARY KEY (loop_id);


--
-- Name: typical_sections typical_sections_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.typical_sections
    ADD CONSTRAINT typical_sections_pkey PRIMARY KEY (typical_section_id);


--
-- Name: utility_lines utility_lines_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.utility_lines
    ADD CONSTRAINT utility_lines_pkey PRIMARY KEY (line_id);


--
-- Name: utility_network_connectivity utility_network_connectivity_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.utility_network_connectivity
    ADD CONSTRAINT utility_network_connectivity_pkey PRIMARY KEY (connection_id);


--
-- Name: utility_service_connections utility_service_connections_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.utility_service_connections
    ADD CONSTRAINT utility_service_connections_pkey PRIMARY KEY (service_id);


--
-- Name: utility_structures utility_structures_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.utility_structures
    ADD CONSTRAINT utility_structures_pkey PRIMARY KEY (structure_id);


--
-- Name: vertical_profiles vertical_profiles_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.vertical_profiles
    ADD CONSTRAINT vertical_profiles_pkey PRIMARY KEY (profile_id);


--
-- Name: idx_abbrev_attributes; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_abbrev_attributes ON public.abbreviation_standards USING gin (attributes);


--
-- Name: idx_abbrev_category; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_abbrev_category ON public.abbreviation_standards USING btree (category);


--
-- Name: idx_abbrev_discipline; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_abbrev_discipline ON public.abbreviation_standards USING btree (discipline);


--
-- Name: idx_abbrev_entity; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_abbrev_entity ON public.abbreviation_standards USING btree (entity_id);


--
-- Name: idx_abbrev_quality; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_abbrev_quality ON public.abbreviation_standards USING btree (quality_score DESC);


--
-- Name: idx_abbrev_search; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_abbrev_search ON public.abbreviation_standards USING gin (search_vector);


--
-- Name: idx_abbrev_tags; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_abbrev_tags ON public.abbreviation_standards USING gin (tags);


--
-- Name: idx_abbrev_usage; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_abbrev_usage ON public.abbreviation_standards USING btree (usage_frequency DESC);


--
-- Name: idx_alias_canonical; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_alias_canonical ON public.entity_aliases USING btree (is_canonical) WHERE (is_canonical = true);


--
-- Name: idx_alias_entity; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_alias_entity ON public.entity_aliases USING btree (entity_id);


--
-- Name: idx_alias_name; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_alias_name ON public.entity_aliases USING btree (alias_name);


--
-- Name: idx_alias_type; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_alias_type ON public.entity_aliases USING btree (alias_type);


--
-- Name: idx_alignpi_alignment; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_alignpi_alignment ON public.alignment_pis USING btree (alignment_id);


--
-- Name: idx_alignpi_attributes; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_alignpi_attributes ON public.alignment_pis USING gin (attributes);


--
-- Name: idx_alignpi_entity; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_alignpi_entity ON public.alignment_pis USING btree (entity_id);


--
-- Name: idx_alignpi_geom; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_alignpi_geom ON public.alignment_pis USING gist (geometry);


--
-- Name: idx_alignpi_quality; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_alignpi_quality ON public.alignment_pis USING btree (quality_score DESC);


--
-- Name: idx_alignpi_search; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_alignpi_search ON public.alignment_pis USING gin (search_vector);


--
-- Name: idx_alignpi_tags; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_alignpi_tags ON public.alignment_pis USING gin (tags);


--
-- Name: idx_annotation_attributes; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_annotation_attributes ON public.annotation_standards USING gin (attributes);


--
-- Name: idx_annotation_entity; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_annotation_entity ON public.annotation_standards USING btree (entity_id);


--
-- Name: idx_annotation_quality; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_annotation_quality ON public.annotation_standards USING btree (quality_score DESC);


--
-- Name: idx_annotation_search; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_annotation_search ON public.annotation_standards USING gin (search_vector);


--
-- Name: idx_annotation_tags; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_annotation_tags ON public.annotation_standards USING gin (tags);


--
-- Name: idx_annotation_type; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_annotation_type ON public.annotation_standards USING btree (annotation_type);


--
-- Name: idx_annotation_usage; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_annotation_usage ON public.annotation_standards USING btree (usage_frequency DESC);


--
-- Name: idx_block_active; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_block_active ON public.block_definitions USING btree (is_active) WHERE (is_active = true);


--
-- Name: idx_block_attributes; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_block_attributes ON public.block_definitions USING gin (attributes);


--
-- Name: idx_block_category; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_block_category ON public.block_definitions USING btree (category);


--
-- Name: idx_block_complexity; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_block_complexity ON public.block_definitions USING btree (complexity_score DESC NULLS LAST);


--
-- Name: idx_block_entity; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_block_entity ON public.block_definitions USING btree (entity_id);


--
-- Name: idx_block_frequency; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_block_frequency ON public.block_definitions USING btree (usage_frequency DESC);


--
-- Name: idx_block_name; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_block_name ON public.block_definitions USING btree (block_name);


--
-- Name: idx_block_quality; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_block_quality ON public.block_definitions USING btree (quality_score DESC NULLS LAST);


--
-- Name: idx_block_search; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_block_search ON public.block_definitions USING gin (search_vector);


--
-- Name: idx_block_tags; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_block_tags ON public.block_definitions USING gin (tags);


--
-- Name: idx_block_type; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_block_type ON public.block_definitions USING btree (block_type);


--
-- Name: idx_blockinsert_attributes; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_blockinsert_attributes ON public.block_inserts USING gin (attributes);


--
-- Name: idx_blockinsert_entity; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_blockinsert_entity ON public.block_inserts USING btree (entity_id);


--
-- Name: idx_blockinsert_geom; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_blockinsert_geom ON public.block_inserts USING gist (insertion_point);


--
-- Name: idx_blockinsert_layer; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_blockinsert_layer ON public.block_inserts USING btree (layer_id);


--
-- Name: idx_blockinsert_name; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_blockinsert_name ON public.block_inserts USING btree (block_name);


--
-- Name: idx_blockinsert_quality; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_blockinsert_quality ON public.block_inserts USING btree (quality_score DESC);


--
-- Name: idx_blockinsert_search; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_blockinsert_search ON public.block_inserts USING gin (search_vector);


--
-- Name: idx_blockinsert_tags; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_blockinsert_tags ON public.block_inserts USING gin (tags);


--
-- Name: idx_canonical_name; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_canonical_name ON public.standards_entities USING btree (canonical_name);


--
-- Name: idx_category_attributes; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_category_attributes ON public.category_standards USING gin (attributes);


--
-- Name: idx_category_discipline; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_category_discipline ON public.category_standards USING btree (discipline);


--
-- Name: idx_category_entity; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_category_entity ON public.category_standards USING btree (entity_id);


--
-- Name: idx_category_parent; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_category_parent ON public.category_standards USING btree (parent_category_id);


--
-- Name: idx_category_quality; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_category_quality ON public.category_standards USING btree (quality_score DESC);


--
-- Name: idx_category_search; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_category_search ON public.category_standards USING gin (search_vector);


--
-- Name: idx_category_tags; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_category_tags ON public.category_standards USING gin (tags);


--
-- Name: idx_category_usage; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_category_usage ON public.category_standards USING btree (usage_frequency DESC);


--
-- Name: idx_classification_class; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_classification_class ON public.classification_confidence USING btree (predicted_class);


--
-- Name: idx_classification_confidence; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_classification_confidence ON public.classification_confidence USING btree (confidence_score DESC);


--
-- Name: idx_classification_correct; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_classification_correct ON public.classification_confidence USING btree (is_correct) WHERE (is_correct IS NOT NULL);


--
-- Name: idx_classification_entity; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_classification_entity ON public.classification_confidence USING btree (entity_id);


--
-- Name: idx_classification_features; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_classification_features ON public.classification_confidence USING gin (input_features);


--
-- Name: idx_classification_importance; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_classification_importance ON public.classification_confidence USING gin (feature_importance);


--
-- Name: idx_classification_model; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_classification_model ON public.classification_confidence USING btree (model_name);


--
-- Name: idx_code_attributes; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_code_attributes ON public.code_standards USING gin (attributes);


--
-- Name: idx_code_entity; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_code_entity ON public.code_standards USING btree (entity_id);


--
-- Name: idx_code_jurisdiction; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_code_jurisdiction ON public.code_standards USING btree (jurisdiction);


--
-- Name: idx_code_quality; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_code_quality ON public.code_standards USING btree (quality_score DESC);


--
-- Name: idx_code_search; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_code_search ON public.code_standards USING gin (search_vector);


--
-- Name: idx_code_tags; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_code_tags ON public.code_standards USING gin (tags);


--
-- Name: idx_code_usage; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_code_usage ON public.code_standards USING btree (usage_frequency DESC);


--
-- Name: idx_color_aci; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_color_aci ON public.color_standards USING btree (aci_number);


--
-- Name: idx_color_active; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_color_active ON public.color_standards USING btree (is_active) WHERE (is_active = true);


--
-- Name: idx_color_attributes; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_color_attributes ON public.color_standards USING gin (attributes);


--
-- Name: idx_color_discipline; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_color_discipline ON public.color_standards USING btree (discipline);


--
-- Name: idx_color_entity; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_color_entity ON public.color_standards USING btree (entity_id);


--
-- Name: idx_color_name; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_color_name ON public.color_standards USING btree (color_name);


--
-- Name: idx_color_quality; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_color_quality ON public.color_standards USING btree (quality_score DESC NULLS LAST);


--
-- Name: idx_color_search; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_color_search ON public.color_standards USING gin (search_vector);


--
-- Name: idx_color_tags; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_color_tags ON public.color_standards USING gin (tags);


--
-- Name: idx_coordsys_attributes; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_coordsys_attributes ON public.coordinate_systems USING gin (attributes);


--
-- Name: idx_coordsys_entity; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_coordsys_entity ON public.coordinate_systems USING btree (entity_id);


--
-- Name: idx_coordsys_epsg; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_coordsys_epsg ON public.coordinate_systems USING btree (epsg_code);


--
-- Name: idx_coordsys_quality; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_coordsys_quality ON public.coordinate_systems USING btree (quality_score DESC);


--
-- Name: idx_coordsys_search; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_coordsys_search ON public.coordinate_systems USING gin (search_vector);


--
-- Name: idx_coordsys_tags; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_coordsys_tags ON public.coordinate_systems USING gin (tags);


--
-- Name: idx_coordsys_usage; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_coordsys_usage ON public.coordinate_systems USING btree (usage_frequency DESC);


--
-- Name: idx_ctrlmember_attributes; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_ctrlmember_attributes ON public.control_point_membership USING gin (attributes);


--
-- Name: idx_ctrlmember_entity; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_ctrlmember_entity ON public.control_point_membership USING btree (entity_id);


--
-- Name: idx_ctrlmember_network; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_ctrlmember_network ON public.control_point_membership USING btree (network_id);


--
-- Name: idx_ctrlmember_point; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_ctrlmember_point ON public.control_point_membership USING btree (point_id);


--
-- Name: idx_ctrlmember_quality; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_ctrlmember_quality ON public.control_point_membership USING btree (quality_score DESC);


--
-- Name: idx_ctrlmember_search; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_ctrlmember_search ON public.control_point_membership USING gin (search_vector);


--
-- Name: idx_ctrlmember_tags; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_ctrlmember_tags ON public.control_point_membership USING gin (tags);


--
-- Name: idx_ctrlnet_attributes; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_ctrlnet_attributes ON public.survey_control_network USING gin (attributes);


--
-- Name: idx_ctrlnet_entity; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_ctrlnet_entity ON public.survey_control_network USING btree (entity_id);


--
-- Name: idx_ctrlnet_project; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_ctrlnet_project ON public.survey_control_network USING btree (project_id);


--
-- Name: idx_ctrlnet_quality; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_ctrlnet_quality ON public.survey_control_network USING btree (quality_score DESC);


--
-- Name: idx_ctrlnet_search; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_ctrlnet_search ON public.survey_control_network USING gin (search_vector);


--
-- Name: idx_ctrlnet_tags; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_ctrlnet_tags ON public.survey_control_network USING gin (tags);


--
-- Name: idx_ctrlnet_type; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_ctrlnet_type ON public.survey_control_network USING btree (network_type);


--
-- Name: idx_ctrlnet_usage; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_ctrlnet_usage ON public.survey_control_network USING btree (usage_frequency DESC);


--
-- Name: idx_detail_attributes; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_detail_attributes ON public.detail_standards USING gin (attributes);


--
-- Name: idx_detail_category; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_detail_category ON public.detail_standards USING btree (detail_category);


--
-- Name: idx_detail_codes; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_detail_codes ON public.detail_standards USING gin (code_references);


--
-- Name: idx_detail_discipline; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_detail_discipline ON public.detail_standards USING btree (discipline);


--
-- Name: idx_detail_entity; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_detail_entity ON public.detail_standards USING btree (entity_id);


--
-- Name: idx_detail_quality; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_detail_quality ON public.detail_standards USING btree (quality_score DESC);


--
-- Name: idx_detail_search; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_detail_search ON public.detail_standards USING gin (search_vector);


--
-- Name: idx_detail_tags; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_detail_tags ON public.detail_standards USING gin (tags);


--
-- Name: idx_detail_usage; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_detail_usage ON public.detail_standards USING btree (usage_frequency DESC);


--
-- Name: idx_dimension_attributes; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_dimension_attributes ON public.drawing_dimensions USING gin (attributes);


--
-- Name: idx_dimension_entity; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_dimension_entity ON public.drawing_dimensions USING btree (entity_id);


--
-- Name: idx_dimension_layer; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_dimension_layer ON public.drawing_dimensions USING btree (layer_id);


--
-- Name: idx_dimension_quality; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_dimension_quality ON public.drawing_dimensions USING btree (quality_score DESC);


--
-- Name: idx_dimension_search; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_dimension_search ON public.drawing_dimensions USING gin (search_vector);


--
-- Name: idx_dimension_tags; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_dimension_tags ON public.drawing_dimensions USING gin (tags);


--
-- Name: idx_dimension_type; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_dimension_type ON public.drawing_dimensions USING btree (dimension_type);


--
-- Name: idx_drawingent_attributes; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_drawingent_attributes ON public.drawing_entities USING gin (attributes);


--
-- Name: idx_drawingent_geom; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_drawingent_geom ON public.drawing_entities USING gist (geometry);


--
-- Name: idx_drawingent_layer; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_drawingent_layer ON public.drawing_entities USING btree (layer_id);


--
-- Name: idx_drawingent_quality; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_drawingent_quality ON public.drawing_entities USING btree (quality_score DESC);


--
-- Name: idx_drawingent_search; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_drawingent_search ON public.drawing_entities USING gin (search_vector);


--
-- Name: idx_drawingent_space; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_drawingent_space ON public.drawing_entities USING btree (space_type);


--
-- Name: idx_drawingent_standards_entity; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_drawingent_standards_entity ON public.drawing_entities USING btree (standards_entity_id);


--
-- Name: idx_drawingent_tags; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_drawingent_tags ON public.drawing_entities USING gin (tags);


--
-- Name: idx_drawingent_type; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_drawingent_type ON public.drawing_entities USING btree (entity_type);


--
-- Name: idx_drawings_attributes; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_drawings_attributes ON public.drawings USING gin (attributes);


--
-- Name: idx_drawings_complexity; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_drawings_complexity ON public.drawings USING btree (complexity_score DESC NULLS LAST);


--
-- Name: idx_drawings_created; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_drawings_created ON public.drawings USING btree (created_at DESC);


--
-- Name: idx_drawings_discipline; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_drawings_discipline ON public.drawings USING btree (discipline);


--
-- Name: idx_drawings_entity; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_drawings_entity ON public.drawings USING btree (entity_id);


--
-- Name: idx_drawings_name; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_drawings_name ON public.drawings USING btree (drawing_name);


--
-- Name: idx_drawings_number; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_drawings_number ON public.drawings USING btree (drawing_number);


--
-- Name: idx_drawings_project; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_drawings_project ON public.drawings USING btree (project_id);


--
-- Name: idx_drawings_quality; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_drawings_quality ON public.drawings USING btree (quality_score DESC NULLS LAST);


--
-- Name: idx_drawings_search; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_drawings_search ON public.drawings USING gin (search_vector);


--
-- Name: idx_drawings_tags; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_drawings_tags ON public.drawings USING gin (tags);


--
-- Name: idx_drawings_type; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_drawings_type ON public.drawings USING btree (drawing_type);


--
-- Name: idx_drawingtext_attributes; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_drawingtext_attributes ON public.drawing_text USING gin (attributes);


--
-- Name: idx_drawingtext_entity; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_drawingtext_entity ON public.drawing_text USING btree (entity_id);


--
-- Name: idx_drawingtext_geom; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_drawingtext_geom ON public.drawing_text USING gist (insertion_point);


--
-- Name: idx_drawingtext_layer; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_drawingtext_layer ON public.drawing_text USING btree (layer_id);


--
-- Name: idx_drawingtext_quality; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_drawingtext_quality ON public.drawing_text USING btree (quality_score DESC);


--
-- Name: idx_drawingtext_search; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_drawingtext_search ON public.drawing_text USING gin (search_vector);


--
-- Name: idx_drawingtext_space; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_drawingtext_space ON public.drawing_text USING btree (space_type);


--
-- Name: idx_drawingtext_tags; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_drawingtext_tags ON public.drawing_text USING gin (tags);


--
-- Name: idx_earthbal_alignment; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_earthbal_alignment ON public.earthwork_balance USING btree (alignment_id);


--
-- Name: idx_earthbal_attributes; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_earthbal_attributes ON public.earthwork_balance USING gin (attributes);


--
-- Name: idx_earthbal_entity; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_earthbal_entity ON public.earthwork_balance USING btree (entity_id);


--
-- Name: idx_earthbal_quality; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_earthbal_quality ON public.earthwork_balance USING btree (quality_score DESC);


--
-- Name: idx_earthbal_search; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_earthbal_search ON public.earthwork_balance USING gin (search_vector);


--
-- Name: idx_earthbal_station; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_earthbal_station ON public.earthwork_balance USING btree (station);


--
-- Name: idx_earthbal_tags; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_earthbal_tags ON public.earthwork_balance USING gin (tags);


--
-- Name: idx_earthwork_alignment; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_earthwork_alignment ON public.earthwork_quantities USING btree (alignment_id);


--
-- Name: idx_earthwork_attributes; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_earthwork_attributes ON public.earthwork_quantities USING gin (attributes);


--
-- Name: idx_earthwork_entity; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_earthwork_entity ON public.earthwork_quantities USING btree (entity_id);


--
-- Name: idx_earthwork_material; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_earthwork_material ON public.earthwork_quantities USING btree (material_type);


--
-- Name: idx_earthwork_quality; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_earthwork_quality ON public.earthwork_quantities USING btree (quality_score DESC);


--
-- Name: idx_earthwork_search; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_earthwork_search ON public.earthwork_quantities USING gin (search_vector);


--
-- Name: idx_earthwork_tags; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_earthwork_tags ON public.earthwork_quantities USING gin (tags);


--
-- Name: idx_easement_attributes; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_easement_attributes ON public.easements USING gin (attributes);


--
-- Name: idx_easement_entity; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_easement_entity ON public.easements USING btree (entity_id);


--
-- Name: idx_easement_geom; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_easement_geom ON public.easements USING gist (boundary_geometry);


--
-- Name: idx_easement_project; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_easement_project ON public.easements USING btree (project_id);


--
-- Name: idx_easement_quality; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_easement_quality ON public.easements USING btree (quality_score DESC);


--
-- Name: idx_easement_search; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_easement_search ON public.easements USING gin (search_vector);


--
-- Name: idx_easement_tags; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_easement_tags ON public.easements USING gin (tags);


--
-- Name: idx_easement_type; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_easement_type ON public.easements USING btree (easement_type);


--
-- Name: idx_easement_usage; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_easement_usage ON public.easements USING btree (usage_frequency DESC);


--
-- Name: idx_embedding_models_active; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_embedding_models_active ON public.embedding_models USING btree (is_active) WHERE (is_active = true);


--
-- Name: idx_embedding_models_name; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_embedding_models_name ON public.embedding_models USING btree (model_name);


--
-- Name: idx_embeddings_current; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_embeddings_current ON public.entity_embeddings USING btree (entity_id, is_current) WHERE (is_current = true);


--
-- Name: idx_embeddings_entity; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_embeddings_entity ON public.entity_embeddings USING btree (entity_id);


--
-- Name: idx_embeddings_model; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_embeddings_model ON public.entity_embeddings USING btree (model_id);


--
-- Name: idx_embeddings_vector; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_embeddings_vector ON public.entity_embeddings USING ivfflat (embedding public.vector_cosine_ops) WITH (lists='100');


--
-- Name: idx_entity_aliases; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_entity_aliases ON public.standards_entities USING gin (aliases);


--
-- Name: idx_entity_attributes; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_entity_attributes ON public.standards_entities USING gin (attributes);


--
-- Name: idx_entity_quality; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_entity_quality ON public.standards_entities USING btree (quality_score DESC NULLS LAST);


--
-- Name: idx_entity_search; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_entity_search ON public.standards_entities USING gin (search_vector);


--
-- Name: idx_entity_status; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_entity_status ON public.standards_entities USING btree (status);


--
-- Name: idx_entity_tags; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_entity_tags ON public.standards_entities USING gin (tags);


--
-- Name: idx_entity_type; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_entity_type ON public.standards_entities USING btree (entity_type);


--
-- Name: idx_exportjobs_attributes; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_exportjobs_attributes ON public.export_jobs USING gin (attributes);


--
-- Name: idx_exportjobs_entity; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_exportjobs_entity ON public.export_jobs USING btree (entity_id);


--
-- Name: idx_exportjobs_quality; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_exportjobs_quality ON public.export_jobs USING btree (quality_score DESC);


--
-- Name: idx_exportjobs_search; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_exportjobs_search ON public.export_jobs USING gin (search_vector);


--
-- Name: idx_exportjobs_status; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_exportjobs_status ON public.export_jobs USING btree (status);


--
-- Name: idx_exportjobs_tags; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_exportjobs_tags ON public.export_jobs USING gin (tags);


--
-- Name: idx_exportjobs_type; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_exportjobs_type ON public.export_jobs USING btree (job_type);


--
-- Name: idx_gradlimit_attributes; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_gradlimit_attributes ON public.grading_limits USING gin (attributes);


--
-- Name: idx_gradlimit_entity; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_gradlimit_entity ON public.grading_limits USING btree (entity_id);


--
-- Name: idx_gradlimit_geom; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_gradlimit_geom ON public.grading_limits USING gist (boundary_geometry);


--
-- Name: idx_gradlimit_project; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_gradlimit_project ON public.grading_limits USING btree (project_id);


--
-- Name: idx_gradlimit_quality; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_gradlimit_quality ON public.grading_limits USING btree (quality_score DESC);


--
-- Name: idx_gradlimit_search; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_gradlimit_search ON public.grading_limits USING gin (search_vector);


--
-- Name: idx_gradlimit_status; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_gradlimit_status ON public.grading_limits USING btree (approval_status);


--
-- Name: idx_gradlimit_tags; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_gradlimit_tags ON public.grading_limits USING gin (tags);


--
-- Name: idx_gradlimit_type; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_gradlimit_type ON public.grading_limits USING btree (limit_type);


--
-- Name: idx_gradlimit_usage; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_gradlimit_usage ON public.grading_limits USING btree (usage_frequency DESC);


--
-- Name: idx_halign_attributes; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_halign_attributes ON public.horizontal_alignments USING gin (attributes);


--
-- Name: idx_halign_entity; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_halign_entity ON public.horizontal_alignments USING btree (entity_id);


--
-- Name: idx_halign_geom; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_halign_geom ON public.horizontal_alignments USING gist (alignment_geometry);


--
-- Name: idx_halign_project; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_halign_project ON public.horizontal_alignments USING btree (project_id);


--
-- Name: idx_halign_quality; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_halign_quality ON public.horizontal_alignments USING btree (quality_score DESC);


--
-- Name: idx_halign_search; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_halign_search ON public.horizontal_alignments USING gin (search_vector);


--
-- Name: idx_halign_tags; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_halign_tags ON public.horizontal_alignments USING gin (tags);


--
-- Name: idx_halign_type; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_halign_type ON public.horizontal_alignments USING btree (alignment_type);


--
-- Name: idx_halign_usage; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_halign_usage ON public.horizontal_alignments USING btree (usage_frequency DESC);


--
-- Name: idx_hatch_active; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_hatch_active ON public.hatch_patterns USING btree (is_active) WHERE (is_active = true);


--
-- Name: idx_hatch_attributes; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_hatch_attributes ON public.hatch_patterns USING gin (attributes);


--
-- Name: idx_hatch_name; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_hatch_name ON public.hatch_patterns USING btree (pattern_name);


--
-- Name: idx_hatch_quality; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_hatch_quality ON public.hatch_patterns USING btree (quality_score DESC NULLS LAST);


--
-- Name: idx_hatch_search; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_hatch_search ON public.hatch_patterns USING gin (search_vector);


--
-- Name: idx_hatch_tags; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_hatch_tags ON public.hatch_patterns USING gin (tags);


--
-- Name: idx_hatch_type; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_hatch_type ON public.hatch_patterns USING btree (pattern_type);


--
-- Name: idx_hatches_attributes; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_hatches_attributes ON public.drawing_hatches USING gin (attributes);


--
-- Name: idx_hatches_entity; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_hatches_entity ON public.drawing_hatches USING btree (entity_id);


--
-- Name: idx_hatches_geom; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_hatches_geom ON public.drawing_hatches USING gist (boundary_geometry);


--
-- Name: idx_hatches_layer; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_hatches_layer ON public.drawing_hatches USING btree (layer_id);


--
-- Name: idx_hatches_pattern; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_hatches_pattern ON public.drawing_hatches USING btree (hatch_pattern);


--
-- Name: idx_hatches_quality; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_hatches_quality ON public.drawing_hatches USING btree (quality_score DESC);


--
-- Name: idx_hatches_search; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_hatches_search ON public.drawing_hatches USING gin (search_vector);


--
-- Name: idx_hatches_tags; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_hatches_tags ON public.drawing_hatches USING gin (tags);


--
-- Name: idx_layer_active; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_layer_active ON public.layer_standards USING btree (is_active) WHERE (is_active = true);


--
-- Name: idx_layer_category; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_layer_category ON public.layer_standards USING btree (category);


--
-- Name: idx_layer_frequency; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_layer_frequency ON public.layer_standards USING btree (usage_frequency DESC);


--
-- Name: idx_layer_name; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_layer_name ON public.layer_standards USING btree (layer_name);


--
-- Name: idx_layers_attributes; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_layers_attributes ON public.layers USING gin (attributes);


--
-- Name: idx_layers_discipline; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_layers_discipline ON public.layers USING btree (discipline);


--
-- Name: idx_layers_entity; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_layers_entity ON public.layers USING btree (entity_id);


--
-- Name: idx_layers_quality; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_layers_quality ON public.layers USING btree (quality_score DESC);


--
-- Name: idx_layers_search; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_layers_search ON public.layers USING gin (search_vector);


--
-- Name: idx_layers_standard; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_layers_standard ON public.layers USING btree (layer_standard_id);


--
-- Name: idx_layers_tags; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_layers_tags ON public.layers USING gin (tags);


--
-- Name: idx_layers_usage; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_layers_usage ON public.layers USING btree (usage_frequency DESC);


--
-- Name: idx_linetype_active; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_linetype_active ON public.linetypes USING btree (is_active) WHERE (is_active = true);


--
-- Name: idx_linetype_attributes; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_linetype_attributes ON public.linetypes USING gin (attributes);


--
-- Name: idx_linetype_entity; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_linetype_entity ON public.linetypes USING btree (entity_id);


--
-- Name: idx_linetype_name; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_linetype_name ON public.linetypes USING btree (linetype_name);


--
-- Name: idx_linetype_quality; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_linetype_quality ON public.linetypes USING btree (quality_score DESC NULLS LAST);


--
-- Name: idx_linetype_search; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_linetype_search ON public.linetypes USING gin (search_vector);


--
-- Name: idx_linetype_tags; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_linetype_tags ON public.linetypes USING gin (tags);


--
-- Name: idx_material_attributes; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_material_attributes ON public.material_standards USING gin (attributes);


--
-- Name: idx_material_entity; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_material_entity ON public.material_standards USING btree (entity_id);


--
-- Name: idx_material_quality; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_material_quality ON public.material_standards USING btree (quality_score DESC);


--
-- Name: idx_material_search; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_material_search ON public.material_standards USING gin (search_vector);


--
-- Name: idx_material_tags; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_material_tags ON public.material_standards USING gin (tags);


--
-- Name: idx_material_type; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_material_type ON public.material_standards USING btree (material_type);


--
-- Name: idx_material_usage; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_material_usage ON public.material_standards USING btree (usage_frequency DESC);


--
-- Name: idx_mv_graph_summary_connectivity; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_mv_graph_summary_connectivity ON public.mv_entity_graph_summary USING btree (total_connectivity DESC);


--
-- Name: idx_mv_graph_summary_pk; Type: INDEX; Schema: public; Owner: -
--

CREATE UNIQUE INDEX idx_mv_graph_summary_pk ON public.mv_entity_graph_summary USING btree (entity_id);


--
-- Name: idx_mv_graph_summary_quality; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_mv_graph_summary_quality ON public.mv_entity_graph_summary USING btree (quality_score DESC NULLS LAST);


--
-- Name: idx_mv_graph_summary_type; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_mv_graph_summary_type ON public.mv_entity_graph_summary USING btree (entity_type);


--
-- Name: idx_mv_spatial_clusters_cluster; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_mv_spatial_clusters_cluster ON public.mv_spatial_clusters USING btree (cluster_id);


--
-- Name: idx_mv_spatial_clusters_geometry; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_mv_spatial_clusters_geometry ON public.mv_spatial_clusters USING gist (geometry);


--
-- Name: idx_mv_spatial_clusters_project; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_mv_spatial_clusters_project ON public.mv_spatial_clusters USING btree (project_id);


--
-- Name: idx_mv_spatial_clusters_type; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_mv_spatial_clusters_type ON public.mv_spatial_clusters USING btree (point_type);


--
-- Name: idx_mv_survey_enriched_entity; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_mv_survey_enriched_entity ON public.mv_survey_points_enriched USING btree (entity_id);


--
-- Name: idx_mv_survey_enriched_geometry; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_mv_survey_enriched_geometry ON public.mv_survey_points_enriched USING gist (geometry);


--
-- Name: idx_mv_survey_enriched_pk; Type: INDEX; Schema: public; Owner: -
--

CREATE UNIQUE INDEX idx_mv_survey_enriched_pk ON public.mv_survey_points_enriched USING btree (point_id);


--
-- Name: idx_mv_survey_enriched_project; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_mv_survey_enriched_project ON public.mv_survey_points_enriched USING btree (project_id);


--
-- Name: idx_mv_survey_enriched_type; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_mv_survey_enriched_type ON public.mv_survey_points_enriched USING btree (point_type);


--
-- Name: idx_network_metrics_attributes; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_network_metrics_attributes ON public.network_metrics USING gin (attributes);


--
-- Name: idx_network_metrics_betweenness; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_network_metrics_betweenness ON public.network_metrics USING btree (betweenness_centrality DESC NULLS LAST);


--
-- Name: idx_network_metrics_community; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_network_metrics_community ON public.network_metrics USING btree (community_id);


--
-- Name: idx_network_metrics_degree; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_network_metrics_degree ON public.network_metrics USING btree (degree_centrality DESC NULLS LAST);


--
-- Name: idx_network_metrics_entity; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_network_metrics_entity ON public.network_metrics USING btree (entity_id);


--
-- Name: idx_network_metrics_pagerank; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_network_metrics_pagerank ON public.network_metrics USING btree (pagerank_score DESC NULLS LAST);


--
-- Name: idx_note_attributes; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_note_attributes ON public.standard_notes USING gin (attributes);


--
-- Name: idx_note_category; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_note_category ON public.standard_notes USING btree (note_category);


--
-- Name: idx_note_discipline; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_note_discipline ON public.standard_notes USING btree (discipline);


--
-- Name: idx_note_entity; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_note_entity ON public.standard_notes USING btree (entity_id);


--
-- Name: idx_note_quality; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_note_quality ON public.standard_notes USING btree (quality_score DESC);


--
-- Name: idx_note_search; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_note_search ON public.standard_notes USING gin (search_vector);


--
-- Name: idx_note_tags; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_note_tags ON public.standard_notes USING gin (tags);


--
-- Name: idx_note_usage; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_note_usage ON public.standard_notes USING btree (usage_frequency DESC);


--
-- Name: idx_noteassign_attributes; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_noteassign_attributes ON public.sheet_note_assignments USING gin (attributes);


--
-- Name: idx_noteassign_entity; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_noteassign_entity ON public.sheet_note_assignments USING btree (entity_id);


--
-- Name: idx_noteassign_projnote; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_noteassign_projnote ON public.sheet_note_assignments USING btree (project_note_id);


--
-- Name: idx_noteassign_quality; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_noteassign_quality ON public.sheet_note_assignments USING btree (quality_score DESC);


--
-- Name: idx_noteassign_search; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_noteassign_search ON public.sheet_note_assignments USING gin (search_vector);


--
-- Name: idx_noteassign_tags; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_noteassign_tags ON public.sheet_note_assignments USING gin (tags);


--
-- Name: idx_notesets_attributes; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_notesets_attributes ON public.sheet_note_sets USING gin (attributes);


--
-- Name: idx_notesets_discipline; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_notesets_discipline ON public.sheet_note_sets USING btree (discipline);


--
-- Name: idx_notesets_entity; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_notesets_entity ON public.sheet_note_sets USING btree (entity_id);


--
-- Name: idx_notesets_project; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_notesets_project ON public.sheet_note_sets USING btree (project_id);


--
-- Name: idx_notesets_quality; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_notesets_quality ON public.sheet_note_sets USING btree (quality_score DESC);


--
-- Name: idx_notesets_search; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_notesets_search ON public.sheet_note_sets USING gin (search_vector);


--
-- Name: idx_notesets_tags; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_notesets_tags ON public.sheet_note_sets USING gin (tags);


--
-- Name: idx_notesets_usage; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_notesets_usage ON public.sheet_note_sets USING btree (usage_frequency DESC);


--
-- Name: idx_parcel_attributes; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_parcel_attributes ON public.parcels USING gin (attributes);


--
-- Name: idx_parcel_entity; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_parcel_entity ON public.parcels USING btree (entity_id);


--
-- Name: idx_parcel_geom; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_parcel_geom ON public.parcels USING gist (boundary_geometry);


--
-- Name: idx_parcel_owner; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_parcel_owner ON public.parcels USING btree (owner_name);


--
-- Name: idx_parcel_project; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_parcel_project ON public.parcels USING btree (project_id);


--
-- Name: idx_parcel_quality; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_parcel_quality ON public.parcels USING btree (quality_score DESC);


--
-- Name: idx_parcel_search; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_parcel_search ON public.parcels USING gin (search_vector);


--
-- Name: idx_parcel_tags; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_parcel_tags ON public.parcels USING gin (tags);


--
-- Name: idx_parcel_usage; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_parcel_usage ON public.parcels USING btree (usage_frequency DESC);


--
-- Name: idx_parcel_zoning; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_parcel_zoning ON public.parcels USING btree (zoning);


--
-- Name: idx_parcelcorner_attributes; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_parcelcorner_attributes ON public.parcel_corners USING gin (attributes);


--
-- Name: idx_parcelcorner_entity; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_parcelcorner_entity ON public.parcel_corners USING btree (entity_id);


--
-- Name: idx_parcelcorner_parcel; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_parcelcorner_parcel ON public.parcel_corners USING btree (parcel_id);


--
-- Name: idx_parcelcorner_quality; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_parcelcorner_quality ON public.parcel_corners USING btree (quality_score DESC);


--
-- Name: idx_parcelcorner_search; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_parcelcorner_search ON public.parcel_corners USING gin (search_vector);


--
-- Name: idx_parcelcorner_surveypoint; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_parcelcorner_surveypoint ON public.parcel_corners USING btree (survey_point_id);


--
-- Name: idx_parcelcorner_tags; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_parcelcorner_tags ON public.parcel_corners USING gin (tags);


--
-- Name: idx_pavesect_alignment; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_pavesect_alignment ON public.pavement_sections USING btree (alignment_id);


--
-- Name: idx_pavesect_attributes; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_pavesect_attributes ON public.pavement_sections USING gin (attributes);


--
-- Name: idx_pavesect_entity; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_pavesect_entity ON public.pavement_sections USING btree (entity_id);


--
-- Name: idx_pavesect_layers; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_pavesect_layers ON public.pavement_sections USING gin (layer_structure);


--
-- Name: idx_pavesect_project; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_pavesect_project ON public.pavement_sections USING btree (project_id);


--
-- Name: idx_pavesect_quality; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_pavesect_quality ON public.pavement_sections USING btree (quality_score DESC);


--
-- Name: idx_pavesect_search; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_pavesect_search ON public.pavement_sections USING gin (search_vector);


--
-- Name: idx_pavesect_tags; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_pavesect_tags ON public.pavement_sections USING gin (tags);


--
-- Name: idx_pavesect_type; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_pavesect_type ON public.pavement_sections USING btree (pavement_type);


--
-- Name: idx_pavesect_usage; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_pavesect_usage ON public.pavement_sections USING btree (usage_frequency DESC);


--
-- Name: idx_plotstyle_active; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_plotstyle_active ON public.plot_styles USING btree (is_active) WHERE (is_active = true);


--
-- Name: idx_plotstyle_attributes; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_plotstyle_attributes ON public.plot_styles USING gin (attributes);


--
-- Name: idx_plotstyle_entity; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_plotstyle_entity ON public.plot_styles USING btree (entity_id);


--
-- Name: idx_plotstyle_name; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_plotstyle_name ON public.plot_styles USING btree (plot_style_name);


--
-- Name: idx_plotstyle_quality; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_plotstyle_quality ON public.plot_styles USING btree (quality_score DESC NULLS LAST);


--
-- Name: idx_plotstyle_search; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_plotstyle_search ON public.plot_styles USING gin (search_vector);


--
-- Name: idx_plotstyle_tags; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_plotstyle_tags ON public.plot_styles USING gin (tags);


--
-- Name: idx_plotstyle_type; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_plotstyle_type ON public.plot_styles USING btree (style_type);


--
-- Name: idx_projects_attributes; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_projects_attributes ON public.projects USING gin (attributes);


--
-- Name: idx_projects_client; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_projects_client ON public.projects USING btree (client_name);


--
-- Name: idx_projects_created; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_projects_created ON public.projects USING btree (created_at DESC);


--
-- Name: idx_projects_entity; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_projects_entity ON public.projects USING btree (entity_id);


--
-- Name: idx_projects_name; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_projects_name ON public.projects USING btree (project_name);


--
-- Name: idx_projects_number; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_projects_number ON public.projects USING btree (project_number);


--
-- Name: idx_projects_quality; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_projects_quality ON public.projects USING btree (quality_score DESC NULLS LAST);


--
-- Name: idx_projects_search; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_projects_search ON public.projects USING gin (search_vector);


--
-- Name: idx_projects_tags; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_projects_tags ON public.projects USING gin (tags);


--
-- Name: idx_projnotes_attributes; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_projnotes_attributes ON public.project_sheet_notes USING gin (attributes);


--
-- Name: idx_projnotes_entity; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_projnotes_entity ON public.project_sheet_notes USING btree (entity_id);


--
-- Name: idx_projnotes_quality; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_projnotes_quality ON public.project_sheet_notes USING btree (quality_score DESC);


--
-- Name: idx_projnotes_search; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_projnotes_search ON public.project_sheet_notes USING gin (search_vector);


--
-- Name: idx_projnotes_set; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_projnotes_set ON public.project_sheet_notes USING btree (set_id);


--
-- Name: idx_projnotes_standard; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_projnotes_standard ON public.project_sheet_notes USING btree (standard_note_id);


--
-- Name: idx_projnotes_tags; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_projnotes_tags ON public.project_sheet_notes USING gin (tags);


--
-- Name: idx_projnotes_usage; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_projnotes_usage ON public.project_sheet_notes USING btree (usage_frequency DESC);


--
-- Name: idx_pvi_attributes; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_pvi_attributes ON public.profile_pvis USING gin (attributes);


--
-- Name: idx_pvi_entity; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_pvi_entity ON public.profile_pvis USING btree (entity_id);


--
-- Name: idx_pvi_profile; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_pvi_profile ON public.profile_pvis USING btree (profile_id);


--
-- Name: idx_pvi_quality; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_pvi_quality ON public.profile_pvis USING btree (quality_score DESC);


--
-- Name: idx_pvi_search; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_pvi_search ON public.profile_pvis USING gin (search_vector);


--
-- Name: idx_pvi_tags; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_pvi_tags ON public.profile_pvis USING gin (tags);


--
-- Name: idx_rel_ai; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_rel_ai ON public.entity_relationships USING btree (ai_generated) WHERE (ai_generated = true);


--
-- Name: idx_rel_attributes; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_rel_attributes ON public.entity_relationships USING gin (attributes);


--
-- Name: idx_rel_confidence; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_rel_confidence ON public.entity_relationships USING btree (confidence_score DESC);


--
-- Name: idx_rel_object; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_rel_object ON public.entity_relationships USING btree (object_entity_id);


--
-- Name: idx_rel_predicate; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_rel_predicate ON public.entity_relationships USING btree (predicate);


--
-- Name: idx_rel_spatial; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_rel_spatial ON public.entity_relationships USING btree (spatial_relationship) WHERE (spatial_relationship = true);


--
-- Name: idx_rel_subject; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_rel_subject ON public.entity_relationships USING btree (subject_entity_id);


--
-- Name: idx_rel_type; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_rel_type ON public.entity_relationships USING btree (relationship_type);


--
-- Name: idx_row_attributes; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_row_attributes ON public.right_of_way USING gin (attributes);


--
-- Name: idx_row_entity; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_row_entity ON public.right_of_way USING btree (entity_id);


--
-- Name: idx_row_geom; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_row_geom ON public.right_of_way USING gist (boundary_geometry);


--
-- Name: idx_row_jurisdiction; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_row_jurisdiction ON public.right_of_way USING btree (jurisdiction);


--
-- Name: idx_row_project; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_row_project ON public.right_of_way USING btree (project_id);


--
-- Name: idx_row_quality; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_row_quality ON public.right_of_way USING btree (quality_score DESC);


--
-- Name: idx_row_search; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_row_search ON public.right_of_way USING gin (search_vector);


--
-- Name: idx_row_tags; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_row_tags ON public.right_of_way USING gin (tags);


--
-- Name: idx_row_type; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_row_type ON public.right_of_way USING btree (row_type);


--
-- Name: idx_row_usage; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_row_usage ON public.right_of_way USING btree (usage_frequency DESC);


--
-- Name: idx_scale_attributes; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_scale_attributes ON public.drawing_scale_standards USING gin (attributes);


--
-- Name: idx_scale_entity; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_scale_entity ON public.drawing_scale_standards USING btree (entity_id);


--
-- Name: idx_scale_quality; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_scale_quality ON public.drawing_scale_standards USING btree (quality_score DESC);


--
-- Name: idx_scale_search; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_scale_search ON public.drawing_scale_standards USING gin (search_vector);


--
-- Name: idx_scale_tags; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_scale_tags ON public.drawing_scale_standards USING gin (tags);


--
-- Name: idx_scale_type; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_scale_type ON public.drawing_scale_standards USING btree (drawing_type);


--
-- Name: idx_scale_usage; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_scale_usage ON public.drawing_scale_standards USING btree (usage_frequency DESC);


--
-- Name: idx_sheetdrawing_attributes; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_sheetdrawing_attributes ON public.sheet_drawing_assignments USING gin (attributes);


--
-- Name: idx_sheetdrawing_entity; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_sheetdrawing_entity ON public.sheet_drawing_assignments USING btree (entity_id);


--
-- Name: idx_sheetdrawing_quality; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_sheetdrawing_quality ON public.sheet_drawing_assignments USING btree (quality_score DESC);


--
-- Name: idx_sheetdrawing_search; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_sheetdrawing_search ON public.sheet_drawing_assignments USING gin (search_vector);


--
-- Name: idx_sheetdrawing_sheet; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_sheetdrawing_sheet ON public.sheet_drawing_assignments USING btree (sheet_id);


--
-- Name: idx_sheetdrawing_tags; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_sheetdrawing_tags ON public.sheet_drawing_assignments USING gin (tags);


--
-- Name: idx_sheetrel_attributes; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_sheetrel_attributes ON public.sheet_relationships USING gin (attributes);


--
-- Name: idx_sheetrel_entity; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_sheetrel_entity ON public.sheet_relationships USING btree (entity_id);


--
-- Name: idx_sheetrel_quality; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_sheetrel_quality ON public.sheet_relationships USING btree (quality_score DESC);


--
-- Name: idx_sheetrel_search; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_sheetrel_search ON public.sheet_relationships USING gin (search_vector);


--
-- Name: idx_sheetrel_source; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_sheetrel_source ON public.sheet_relationships USING btree (source_sheet_id);


--
-- Name: idx_sheetrel_tags; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_sheetrel_tags ON public.sheet_relationships USING gin (tags);


--
-- Name: idx_sheetrel_target; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_sheetrel_target ON public.sheet_relationships USING btree (target_sheet_id);


--
-- Name: idx_sheetrel_type; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_sheetrel_type ON public.sheet_relationships USING btree (relationship_type);


--
-- Name: idx_sheetrev_attributes; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_sheetrev_attributes ON public.sheet_revisions USING gin (attributes);


--
-- Name: idx_sheetrev_entity; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_sheetrev_entity ON public.sheet_revisions USING btree (entity_id);


--
-- Name: idx_sheetrev_number; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_sheetrev_number ON public.sheet_revisions USING btree (revision_number);


--
-- Name: idx_sheetrev_quality; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_sheetrev_quality ON public.sheet_revisions USING btree (quality_score DESC);


--
-- Name: idx_sheetrev_search; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_sheetrev_search ON public.sheet_revisions USING gin (search_vector);


--
-- Name: idx_sheetrev_sheet; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_sheetrev_sheet ON public.sheet_revisions USING btree (sheet_id);


--
-- Name: idx_sheetrev_tags; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_sheetrev_tags ON public.sheet_revisions USING gin (tags);


--
-- Name: idx_sheets_attributes; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_sheets_attributes ON public.sheets USING gin (attributes);


--
-- Name: idx_sheets_category; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_sheets_category ON public.sheets USING btree (category_code);


--
-- Name: idx_sheets_entity; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_sheets_entity ON public.sheets USING btree (entity_id);


--
-- Name: idx_sheets_quality; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_sheets_quality ON public.sheets USING btree (quality_score DESC);


--
-- Name: idx_sheets_search; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_sheets_search ON public.sheets USING gin (search_vector);


--
-- Name: idx_sheets_set; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_sheets_set ON public.sheets USING btree (set_id);


--
-- Name: idx_sheets_tags; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_sheets_tags ON public.sheets USING gin (tags);


--
-- Name: idx_sheets_type; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_sheets_type ON public.sheets USING btree (sheet_type);


--
-- Name: idx_sheets_usage; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_sheets_usage ON public.sheets USING btree (usage_frequency DESC);


--
-- Name: idx_sheetsets_attributes; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_sheetsets_attributes ON public.sheet_sets USING gin (attributes);


--
-- Name: idx_sheetsets_discipline; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_sheetsets_discipline ON public.sheet_sets USING btree (discipline);


--
-- Name: idx_sheetsets_entity; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_sheetsets_entity ON public.sheet_sets USING btree (entity_id);


--
-- Name: idx_sheetsets_project; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_sheetsets_project ON public.sheet_sets USING btree (project_id);


--
-- Name: idx_sheetsets_quality; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_sheetsets_quality ON public.sheet_sets USING btree (quality_score DESC);


--
-- Name: idx_sheetsets_search; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_sheetsets_search ON public.sheet_sets USING gin (search_vector);


--
-- Name: idx_sheetsets_status; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_sheetsets_status ON public.sheet_sets USING btree (status);


--
-- Name: idx_sheetsets_tags; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_sheetsets_tags ON public.sheet_sets USING gin (tags);


--
-- Name: idx_sheetsets_usage; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_sheetsets_usage ON public.sheet_sets USING btree (usage_frequency DESC);


--
-- Name: idx_spatial_stats_attributes; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_spatial_stats_attributes ON public.spatial_statistics USING gin (attributes);


--
-- Name: idx_spatial_stats_density; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_spatial_stats_density ON public.spatial_statistics USING btree (point_density DESC NULLS LAST);


--
-- Name: idx_spatial_stats_project; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_spatial_stats_project ON public.spatial_statistics USING btree (project_id);


--
-- Name: idx_spatial_stats_region; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_spatial_stats_region ON public.spatial_statistics USING gist (region_geometry);


--
-- Name: idx_surface_attributes; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_surface_attributes ON public.surface_models USING gin (attributes);


--
-- Name: idx_surface_entity; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_surface_entity ON public.surface_models USING btree (entity_id);


--
-- Name: idx_surface_project; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_surface_project ON public.surface_models USING btree (project_id);


--
-- Name: idx_surface_quality; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_surface_quality ON public.surface_models USING btree (quality_score DESC);


--
-- Name: idx_surface_search; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_surface_search ON public.surface_models USING gin (search_vector);


--
-- Name: idx_surface_tags; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_surface_tags ON public.surface_models USING gin (tags);


--
-- Name: idx_surface_type; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_surface_type ON public.surface_models USING btree (surface_type);


--
-- Name: idx_surface_usage; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_surface_usage ON public.surface_models USING btree (usage_frequency DESC);


--
-- Name: idx_surfacefeat_attributes; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_surfacefeat_attributes ON public.surface_features USING gin (attributes);


--
-- Name: idx_surfacefeat_entity; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_surfacefeat_entity ON public.surface_features USING btree (entity_id);


--
-- Name: idx_surfacefeat_geom; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_surfacefeat_geom ON public.surface_features USING gist (geometry);


--
-- Name: idx_surfacefeat_project; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_surfacefeat_project ON public.surface_features USING btree (project_id);


--
-- Name: idx_surfacefeat_quality; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_surfacefeat_quality ON public.surface_features USING btree (quality_score DESC);


--
-- Name: idx_surfacefeat_search; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_surfacefeat_search ON public.surface_features USING gin (search_vector);


--
-- Name: idx_surfacefeat_surveypoint; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_surfacefeat_surveypoint ON public.surface_features USING btree (survey_point_id);


--
-- Name: idx_surfacefeat_tags; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_surfacefeat_tags ON public.surface_features USING gin (tags);


--
-- Name: idx_surfacefeat_type; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_surfacefeat_type ON public.surface_features USING btree (feature_type);


--
-- Name: idx_surfacefeat_usage; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_surfacefeat_usage ON public.surface_features USING btree (usage_frequency DESC);


--
-- Name: idx_surveyobs_attributes; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_surveyobs_attributes ON public.survey_observations USING gin (attributes);


--
-- Name: idx_surveyobs_entity; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_surveyobs_entity ON public.survey_observations USING btree (entity_id);


--
-- Name: idx_surveyobs_project; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_surveyobs_project ON public.survey_observations USING btree (project_id);


--
-- Name: idx_surveyobs_quality; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_surveyobs_quality ON public.survey_observations USING btree (quality_score DESC);


--
-- Name: idx_surveyobs_rawdata; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_surveyobs_rawdata ON public.survey_observations USING gin (raw_data);


--
-- Name: idx_surveyobs_search; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_surveyobs_search ON public.survey_observations USING gin (search_vector);


--
-- Name: idx_surveyobs_session; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_surveyobs_session ON public.survey_observations USING btree (session_id);


--
-- Name: idx_surveyobs_tags; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_surveyobs_tags ON public.survey_observations USING gin (tags);


--
-- Name: idx_surveyobs_type; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_surveyobs_type ON public.survey_observations USING btree (observation_type);


--
-- Name: idx_surveypts_attributes; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_surveypts_attributes ON public.survey_points USING gin (attributes);


--
-- Name: idx_surveypts_code; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_surveypts_code ON public.survey_points USING btree (point_code);


--
-- Name: idx_surveypts_entity; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_surveypts_entity ON public.survey_points USING btree (entity_id);


--
-- Name: idx_surveypts_geom; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_surveypts_geom ON public.survey_points USING gist (geometry);


--
-- Name: idx_surveypts_project; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_surveypts_project ON public.survey_points USING btree (project_id);


--
-- Name: idx_surveypts_quality; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_surveypts_quality ON public.survey_points USING btree (quality_score DESC);


--
-- Name: idx_surveypts_search; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_surveypts_search ON public.survey_points USING gin (search_vector);


--
-- Name: idx_surveypts_tags; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_surveypts_tags ON public.survey_points USING gin (tags);


--
-- Name: idx_surveypts_type; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_surveypts_type ON public.survey_points USING btree (point_type);


--
-- Name: idx_surveypts_usage; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_surveypts_usage ON public.survey_points USING btree (usage_frequency DESC);


--
-- Name: idx_temporal_changes_after; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_temporal_changes_after ON public.temporal_changes USING gin (state_after);


--
-- Name: idx_temporal_changes_before; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_temporal_changes_before ON public.temporal_changes USING gin (state_before);


--
-- Name: idx_temporal_changes_entity; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_temporal_changes_entity ON public.temporal_changes USING btree (entity_id);


--
-- Name: idx_temporal_changes_fields; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_temporal_changes_fields ON public.temporal_changes USING gin (changed_fields);


--
-- Name: idx_temporal_changes_magnitude; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_temporal_changes_magnitude ON public.temporal_changes USING btree (change_magnitude DESC NULLS LAST);


--
-- Name: idx_temporal_changes_timestamp; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_temporal_changes_timestamp ON public.temporal_changes USING btree (change_timestamp DESC);


--
-- Name: idx_temporal_changes_type; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_temporal_changes_type ON public.temporal_changes USING btree (change_type);


--
-- Name: idx_textstyle_active; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_textstyle_active ON public.text_styles USING btree (is_active) WHERE (is_active = true);


--
-- Name: idx_textstyle_attributes; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_textstyle_attributes ON public.text_styles USING gin (attributes);


--
-- Name: idx_textstyle_discipline; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_textstyle_discipline ON public.text_styles USING btree (discipline);


--
-- Name: idx_textstyle_entity; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_textstyle_entity ON public.text_styles USING btree (entity_id);


--
-- Name: idx_textstyle_name; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_textstyle_name ON public.text_styles USING btree (style_name);


--
-- Name: idx_textstyle_quality; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_textstyle_quality ON public.text_styles USING btree (quality_score DESC NULLS LAST);


--
-- Name: idx_textstyle_search; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_textstyle_search ON public.text_styles USING gin (search_vector);


--
-- Name: idx_textstyle_tags; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_textstyle_tags ON public.text_styles USING gin (tags);


--
-- Name: idx_travloop_attributes; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_travloop_attributes ON public.traverse_loops USING gin (attributes);


--
-- Name: idx_travloop_entity; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_travloop_entity ON public.traverse_loops USING btree (entity_id);


--
-- Name: idx_travloop_project; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_travloop_project ON public.traverse_loops USING btree (project_id);


--
-- Name: idx_travloop_quality; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_travloop_quality ON public.traverse_loops USING btree (quality_score DESC);


--
-- Name: idx_travloop_search; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_travloop_search ON public.traverse_loops USING gin (search_vector);


--
-- Name: idx_travloop_tags; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_travloop_tags ON public.traverse_loops USING gin (tags);


--
-- Name: idx_travloop_type; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_travloop_type ON public.traverse_loops USING btree (loop_type);


--
-- Name: idx_travloop_usage; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_travloop_usage ON public.traverse_loops USING btree (usage_frequency DESC);


--
-- Name: idx_travloopobs_attributes; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_travloopobs_attributes ON public.traverse_loop_observations USING gin (attributes);


--
-- Name: idx_travloopobs_entity; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_travloopobs_entity ON public.traverse_loop_observations USING btree (entity_id);


--
-- Name: idx_travloopobs_loop; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_travloopobs_loop ON public.traverse_loop_observations USING btree (loop_id);


--
-- Name: idx_travloopobs_obs; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_travloopobs_obs ON public.traverse_loop_observations USING btree (observation_id);


--
-- Name: idx_travloopobs_point; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_travloopobs_point ON public.traverse_loop_observations USING btree (point_id);


--
-- Name: idx_travloopobs_quality; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_travloopobs_quality ON public.traverse_loop_observations USING btree (quality_score DESC);


--
-- Name: idx_travloopobs_search; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_travloopobs_search ON public.traverse_loop_observations USING gin (search_vector);


--
-- Name: idx_travloopobs_tags; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_travloopobs_tags ON public.traverse_loop_observations USING gin (tags);


--
-- Name: idx_trees_attributes; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_trees_attributes ON public.site_trees USING gin (attributes);


--
-- Name: idx_trees_entity; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_trees_entity ON public.site_trees USING btree (entity_id);


--
-- Name: idx_trees_project; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_trees_project ON public.site_trees USING btree (project_id);


--
-- Name: idx_trees_quality; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_trees_quality ON public.site_trees USING btree (quality_score DESC);


--
-- Name: idx_trees_search; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_trees_search ON public.site_trees USING gin (search_vector);


--
-- Name: idx_trees_species; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_trees_species ON public.site_trees USING btree (species);


--
-- Name: idx_trees_surveypoint; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_trees_surveypoint ON public.site_trees USING btree (survey_point_id);


--
-- Name: idx_trees_tags; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_trees_tags ON public.site_trees USING gin (tags);


--
-- Name: idx_trees_usage; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_trees_usage ON public.site_trees USING btree (usage_frequency DESC);


--
-- Name: idx_typsect_attributes; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_typsect_attributes ON public.typical_sections USING gin (attributes);


--
-- Name: idx_typsect_entity; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_typsect_entity ON public.typical_sections USING btree (entity_id);


--
-- Name: idx_typsect_project; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_typsect_project ON public.typical_sections USING btree (project_id);


--
-- Name: idx_typsect_quality; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_typsect_quality ON public.typical_sections USING btree (quality_score DESC);


--
-- Name: idx_typsect_roadtype; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_typsect_roadtype ON public.typical_sections USING btree (road_type);


--
-- Name: idx_typsect_search; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_typsect_search ON public.typical_sections USING gin (search_vector);


--
-- Name: idx_typsect_sectiondata; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_typsect_sectiondata ON public.typical_sections USING gin (section_data);


--
-- Name: idx_typsect_tags; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_typsect_tags ON public.typical_sections USING gin (tags);


--
-- Name: idx_typsect_usage; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_typsect_usage ON public.typical_sections USING btree (usage_frequency DESC);


--
-- Name: idx_utilconn_attributes; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_utilconn_attributes ON public.utility_network_connectivity USING gin (attributes);


--
-- Name: idx_utilconn_entity; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_utilconn_entity ON public.utility_network_connectivity USING btree (entity_id);


--
-- Name: idx_utilconn_from; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_utilconn_from ON public.utility_network_connectivity USING btree (from_element_id);


--
-- Name: idx_utilconn_quality; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_utilconn_quality ON public.utility_network_connectivity USING btree (quality_score DESC);


--
-- Name: idx_utilconn_search; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_utilconn_search ON public.utility_network_connectivity USING gin (search_vector);


--
-- Name: idx_utilconn_tags; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_utilconn_tags ON public.utility_network_connectivity USING gin (tags);


--
-- Name: idx_utilconn_to; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_utilconn_to ON public.utility_network_connectivity USING btree (to_element_id);


--
-- Name: idx_utilconn_type; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_utilconn_type ON public.utility_network_connectivity USING btree (connection_type);


--
-- Name: idx_utilline_attributes; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_utilline_attributes ON public.utility_lines USING gin (attributes);


--
-- Name: idx_utilline_entity; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_utilline_entity ON public.utility_lines USING btree (entity_id);


--
-- Name: idx_utilline_from; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_utilline_from ON public.utility_lines USING btree (from_structure_id);


--
-- Name: idx_utilline_geom; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_utilline_geom ON public.utility_lines USING gist (geometry);


--
-- Name: idx_utilline_project; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_utilline_project ON public.utility_lines USING btree (project_id);


--
-- Name: idx_utilline_quality; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_utilline_quality ON public.utility_lines USING btree (quality_score DESC);


--
-- Name: idx_utilline_search; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_utilline_search ON public.utility_lines USING gin (search_vector);


--
-- Name: idx_utilline_system; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_utilline_system ON public.utility_lines USING btree (utility_system);


--
-- Name: idx_utilline_tags; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_utilline_tags ON public.utility_lines USING gin (tags);


--
-- Name: idx_utilline_to; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_utilline_to ON public.utility_lines USING btree (to_structure_id);


--
-- Name: idx_utilline_usage; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_utilline_usage ON public.utility_lines USING btree (usage_frequency DESC);


--
-- Name: idx_utilserv_attributes; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_utilserv_attributes ON public.utility_service_connections USING gin (attributes);


--
-- Name: idx_utilserv_entity; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_utilserv_entity ON public.utility_service_connections USING btree (entity_id);


--
-- Name: idx_utilserv_geom; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_utilserv_geom ON public.utility_service_connections USING gist (service_point_geometry);


--
-- Name: idx_utilserv_line; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_utilserv_line ON public.utility_service_connections USING btree (line_id);


--
-- Name: idx_utilserv_quality; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_utilserv_quality ON public.utility_service_connections USING btree (quality_score DESC);


--
-- Name: idx_utilserv_search; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_utilserv_search ON public.utility_service_connections USING gin (search_vector);


--
-- Name: idx_utilserv_structure; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_utilserv_structure ON public.utility_service_connections USING btree (structure_id);


--
-- Name: idx_utilserv_tags; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_utilserv_tags ON public.utility_service_connections USING gin (tags);


--
-- Name: idx_utilserv_type; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_utilserv_type ON public.utility_service_connections USING btree (service_type);


--
-- Name: idx_utilstruct_attributes; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_utilstruct_attributes ON public.utility_structures USING gin (attributes);


--
-- Name: idx_utilstruct_entity; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_utilstruct_entity ON public.utility_structures USING btree (entity_id);


--
-- Name: idx_utilstruct_geom; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_utilstruct_geom ON public.utility_structures USING gist (rim_geometry);


--
-- Name: idx_utilstruct_project; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_utilstruct_project ON public.utility_structures USING btree (project_id);


--
-- Name: idx_utilstruct_quality; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_utilstruct_quality ON public.utility_structures USING btree (quality_score DESC);


--
-- Name: idx_utilstruct_search; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_utilstruct_search ON public.utility_structures USING gin (search_vector);


--
-- Name: idx_utilstruct_surveypoint; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_utilstruct_surveypoint ON public.utility_structures USING btree (survey_point_id);


--
-- Name: idx_utilstruct_system; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_utilstruct_system ON public.utility_structures USING btree (utility_system);


--
-- Name: idx_utilstruct_tags; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_utilstruct_tags ON public.utility_structures USING gin (tags);


--
-- Name: idx_utilstruct_type; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_utilstruct_type ON public.utility_structures USING btree (structure_type);


--
-- Name: idx_utilstruct_usage; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_utilstruct_usage ON public.utility_structures USING btree (usage_frequency DESC);


--
-- Name: idx_viewports_attributes; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_viewports_attributes ON public.layout_viewports USING gin (attributes);


--
-- Name: idx_viewports_entity; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_viewports_entity ON public.layout_viewports USING btree (entity_id);


--
-- Name: idx_viewports_geom; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_viewports_geom ON public.layout_viewports USING gist (center_point);


--
-- Name: idx_viewports_layout; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_viewports_layout ON public.layout_viewports USING btree (layout_name);


--
-- Name: idx_viewports_quality; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_viewports_quality ON public.layout_viewports USING btree (quality_score DESC);


--
-- Name: idx_viewports_search; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_viewports_search ON public.layout_viewports USING gin (search_vector);


--
-- Name: idx_viewports_tags; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_viewports_tags ON public.layout_viewports USING gin (tags);


--
-- Name: idx_vprofile_alignment; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_vprofile_alignment ON public.vertical_profiles USING btree (alignment_id);


--
-- Name: idx_vprofile_attributes; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_vprofile_attributes ON public.vertical_profiles USING gin (attributes);


--
-- Name: idx_vprofile_entity; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_vprofile_entity ON public.vertical_profiles USING btree (entity_id);


--
-- Name: idx_vprofile_quality; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_vprofile_quality ON public.vertical_profiles USING btree (quality_score DESC);


--
-- Name: idx_vprofile_search; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_vprofile_search ON public.vertical_profiles USING gin (search_vector);


--
-- Name: idx_vprofile_tags; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_vprofile_tags ON public.vertical_profiles USING gin (tags);


--
-- Name: idx_vprofile_type; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_vprofile_type ON public.vertical_profiles USING btree (profile_type);


--
-- Name: idx_vprofile_usage; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_vprofile_usage ON public.vertical_profiles USING btree (usage_frequency DESC);


--
-- Name: idx_xsection_alignment; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_xsection_alignment ON public.cross_sections USING btree (alignment_id);


--
-- Name: idx_xsection_attributes; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_xsection_attributes ON public.cross_sections USING gin (attributes);


--
-- Name: idx_xsection_entity; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_xsection_entity ON public.cross_sections USING btree (entity_id);


--
-- Name: idx_xsection_geom; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_xsection_geom ON public.cross_sections USING gist (section_geometry);


--
-- Name: idx_xsection_quality; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_xsection_quality ON public.cross_sections USING btree (quality_score DESC);


--
-- Name: idx_xsection_search; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_xsection_search ON public.cross_sections USING gin (search_vector);


--
-- Name: idx_xsection_station; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_xsection_station ON public.cross_sections USING btree (station);


--
-- Name: idx_xsection_tags; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_xsection_tags ON public.cross_sections USING gin (tags);


--
-- Name: idx_xsectpoint_attributes; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_xsectpoint_attributes ON public.cross_section_points USING gin (attributes);


--
-- Name: idx_xsectpoint_entity; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_xsectpoint_entity ON public.cross_section_points USING btree (entity_id);


--
-- Name: idx_xsectpoint_quality; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_xsectpoint_quality ON public.cross_section_points USING btree (quality_score DESC);


--
-- Name: idx_xsectpoint_search; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_xsectpoint_search ON public.cross_section_points USING gin (search_vector);


--
-- Name: idx_xsectpoint_section; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_xsectpoint_section ON public.cross_section_points USING btree (section_id);


--
-- Name: idx_xsectpoint_tags; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_xsectpoint_tags ON public.cross_section_points USING gin (tags);


--
-- Name: abbreviation_standards abbrev_search_update; Type: TRIGGER; Schema: public; Owner: -
--

CREATE TRIGGER abbrev_search_update BEFORE INSERT OR UPDATE ON public.abbreviation_standards FOR EACH ROW EXECUTE FUNCTION public.abbrev_search_trigger();


--
-- Name: alignment_pis alignpi_search_update; Type: TRIGGER; Schema: public; Owner: -
--

CREATE TRIGGER alignpi_search_update BEFORE INSERT OR UPDATE ON public.alignment_pis FOR EACH ROW EXECUTE FUNCTION public.alignpi_search_trigger();


--
-- Name: annotation_standards annotation_search_update; Type: TRIGGER; Schema: public; Owner: -
--

CREATE TRIGGER annotation_search_update BEFORE INSERT OR UPDATE ON public.annotation_standards FOR EACH ROW EXECUTE FUNCTION public.annotation_search_trigger();


--
-- Name: block_inserts block_search_update; Type: TRIGGER; Schema: public; Owner: -
--

CREATE TRIGGER block_search_update BEFORE INSERT OR UPDATE ON public.block_inserts FOR EACH ROW EXECUTE FUNCTION public.block_search_trigger();


--
-- Name: category_standards category_search_update; Type: TRIGGER; Schema: public; Owner: -
--

CREATE TRIGGER category_search_update BEFORE INSERT OR UPDATE ON public.category_standards FOR EACH ROW EXECUTE FUNCTION public.category_search_trigger();


--
-- Name: code_standards code_search_update; Type: TRIGGER; Schema: public; Owner: -
--

CREATE TRIGGER code_search_update BEFORE INSERT OR UPDATE ON public.code_standards FOR EACH ROW EXECUTE FUNCTION public.code_search_trigger();


--
-- Name: coordinate_systems coordsys_search_update; Type: TRIGGER; Schema: public; Owner: -
--

CREATE TRIGGER coordsys_search_update BEFORE INSERT OR UPDATE ON public.coordinate_systems FOR EACH ROW EXECUTE FUNCTION public.coordsys_search_trigger();


--
-- Name: control_point_membership ctrlmember_search_update; Type: TRIGGER; Schema: public; Owner: -
--

CREATE TRIGGER ctrlmember_search_update BEFORE INSERT OR UPDATE ON public.control_point_membership FOR EACH ROW EXECUTE FUNCTION public.ctrlmember_search_trigger();


--
-- Name: survey_control_network ctrlnet_search_update; Type: TRIGGER; Schema: public; Owner: -
--

CREATE TRIGGER ctrlnet_search_update BEFORE INSERT OR UPDATE ON public.survey_control_network FOR EACH ROW EXECUTE FUNCTION public.ctrlnet_search_trigger();


--
-- Name: detail_standards detail_search_update; Type: TRIGGER; Schema: public; Owner: -
--

CREATE TRIGGER detail_search_update BEFORE INSERT OR UPDATE ON public.detail_standards FOR EACH ROW EXECUTE FUNCTION public.detail_search_trigger();


--
-- Name: earthwork_quantities earthwork_search_update; Type: TRIGGER; Schema: public; Owner: -
--

CREATE TRIGGER earthwork_search_update BEFORE INSERT OR UPDATE ON public.earthwork_quantities FOR EACH ROW EXECUTE FUNCTION public.earthwork_search_trigger();


--
-- Name: easements easement_search_update; Type: TRIGGER; Schema: public; Owner: -
--

CREATE TRIGGER easement_search_update BEFORE INSERT OR UPDATE ON public.easements FOR EACH ROW EXECUTE FUNCTION public.easement_search_trigger();


--
-- Name: export_jobs exportjob_search_update; Type: TRIGGER; Schema: public; Owner: -
--

CREATE TRIGGER exportjob_search_update BEFORE INSERT OR UPDATE ON public.export_jobs FOR EACH ROW EXECUTE FUNCTION public.exportjob_search_trigger();


--
-- Name: grading_limits gradlimit_search_update; Type: TRIGGER; Schema: public; Owner: -
--

CREATE TRIGGER gradlimit_search_update BEFORE INSERT OR UPDATE ON public.grading_limits FOR EACH ROW EXECUTE FUNCTION public.gradlimit_search_trigger();


--
-- Name: horizontal_alignments halign_search_update; Type: TRIGGER; Schema: public; Owner: -
--

CREATE TRIGGER halign_search_update BEFORE INSERT OR UPDATE ON public.horizontal_alignments FOR EACH ROW EXECUTE FUNCTION public.halign_search_trigger();


--
-- Name: drawing_hatches hatch_search_update; Type: TRIGGER; Schema: public; Owner: -
--

CREATE TRIGGER hatch_search_update BEFORE INSERT OR UPDATE ON public.drawing_hatches FOR EACH ROW EXECUTE FUNCTION public.hatch_search_trigger();


--
-- Name: layers layer_search_update; Type: TRIGGER; Schema: public; Owner: -
--

CREATE TRIGGER layer_search_update BEFORE INSERT OR UPDATE ON public.layers FOR EACH ROW EXECUTE FUNCTION public.layer_search_trigger();


--
-- Name: material_standards material_search_update; Type: TRIGGER; Schema: public; Owner: -
--

CREATE TRIGGER material_search_update BEFORE INSERT OR UPDATE ON public.material_standards FOR EACH ROW EXECUTE FUNCTION public.material_search_trigger();


--
-- Name: standard_notes note_search_update; Type: TRIGGER; Schema: public; Owner: -
--

CREATE TRIGGER note_search_update BEFORE INSERT OR UPDATE ON public.standard_notes FOR EACH ROW EXECUTE FUNCTION public.note_search_trigger();


--
-- Name: sheet_note_assignments noteassign_search_update; Type: TRIGGER; Schema: public; Owner: -
--

CREATE TRIGGER noteassign_search_update BEFORE INSERT OR UPDATE ON public.sheet_note_assignments FOR EACH ROW EXECUTE FUNCTION public.noteassign_search_trigger();


--
-- Name: sheet_note_sets noteset_search_update; Type: TRIGGER; Schema: public; Owner: -
--

CREATE TRIGGER noteset_search_update BEFORE INSERT OR UPDATE ON public.sheet_note_sets FOR EACH ROW EXECUTE FUNCTION public.noteset_search_trigger();


--
-- Name: parcels parcel_search_update; Type: TRIGGER; Schema: public; Owner: -
--

CREATE TRIGGER parcel_search_update BEFORE INSERT OR UPDATE ON public.parcels FOR EACH ROW EXECUTE FUNCTION public.parcel_search_trigger();


--
-- Name: parcel_corners parcelcorner_search_update; Type: TRIGGER; Schema: public; Owner: -
--

CREATE TRIGGER parcelcorner_search_update BEFORE INSERT OR UPDATE ON public.parcel_corners FOR EACH ROW EXECUTE FUNCTION public.parcelcorner_search_trigger();


--
-- Name: pavement_sections pavesect_search_update; Type: TRIGGER; Schema: public; Owner: -
--

CREATE TRIGGER pavesect_search_update BEFORE INSERT OR UPDATE ON public.pavement_sections FOR EACH ROW EXECUTE FUNCTION public.pavesect_search_trigger();


--
-- Name: project_sheet_notes projnote_search_update; Type: TRIGGER; Schema: public; Owner: -
--

CREATE TRIGGER projnote_search_update BEFORE INSERT OR UPDATE ON public.project_sheet_notes FOR EACH ROW EXECUTE FUNCTION public.projnote_search_trigger();


--
-- Name: profile_pvis pvi_search_update; Type: TRIGGER; Schema: public; Owner: -
--

CREATE TRIGGER pvi_search_update BEFORE INSERT OR UPDATE ON public.profile_pvis FOR EACH ROW EXECUTE FUNCTION public.pvi_search_trigger();


--
-- Name: right_of_way row_search_update; Type: TRIGGER; Schema: public; Owner: -
--

CREATE TRIGGER row_search_update BEFORE INSERT OR UPDATE ON public.right_of_way FOR EACH ROW EXECUTE FUNCTION public.row_search_trigger();


--
-- Name: sheets sheet_search_update; Type: TRIGGER; Schema: public; Owner: -
--

CREATE TRIGGER sheet_search_update BEFORE INSERT OR UPDATE ON public.sheets FOR EACH ROW EXECUTE FUNCTION public.sheet_search_trigger();


--
-- Name: sheet_relationships sheetrel_search_update; Type: TRIGGER; Schema: public; Owner: -
--

CREATE TRIGGER sheetrel_search_update BEFORE INSERT OR UPDATE ON public.sheet_relationships FOR EACH ROW EXECUTE FUNCTION public.sheetrel_search_trigger();


--
-- Name: sheet_revisions sheetrev_search_update; Type: TRIGGER; Schema: public; Owner: -
--

CREATE TRIGGER sheetrev_search_update BEFORE INSERT OR UPDATE ON public.sheet_revisions FOR EACH ROW EXECUTE FUNCTION public.sheetrev_search_trigger();


--
-- Name: surface_models surface_search_update; Type: TRIGGER; Schema: public; Owner: -
--

CREATE TRIGGER surface_search_update BEFORE INSERT OR UPDATE ON public.surface_models FOR EACH ROW EXECUTE FUNCTION public.surface_search_trigger();


--
-- Name: surface_features surfacefeat_search_update; Type: TRIGGER; Schema: public; Owner: -
--

CREATE TRIGGER surfacefeat_search_update BEFORE INSERT OR UPDATE ON public.surface_features FOR EACH ROW EXECUTE FUNCTION public.surfacefeat_search_trigger();


--
-- Name: survey_observations surveyobs_search_update; Type: TRIGGER; Schema: public; Owner: -
--

CREATE TRIGGER surveyobs_search_update BEFORE INSERT OR UPDATE ON public.survey_observations FOR EACH ROW EXECUTE FUNCTION public.surveyobs_search_trigger();


--
-- Name: survey_points surveypt_search_update; Type: TRIGGER; Schema: public; Owner: -
--

CREATE TRIGGER surveypt_search_update BEFORE INSERT OR UPDATE ON public.survey_points FOR EACH ROW EXECUTE FUNCTION public.surveypt_search_trigger();


--
-- Name: traverse_loops travloop_search_update; Type: TRIGGER; Schema: public; Owner: -
--

CREATE TRIGGER travloop_search_update BEFORE INSERT OR UPDATE ON public.traverse_loops FOR EACH ROW EXECUTE FUNCTION public.travloop_search_trigger();


--
-- Name: traverse_loop_observations travloopobs_search_update; Type: TRIGGER; Schema: public; Owner: -
--

CREATE TRIGGER travloopobs_search_update BEFORE INSERT OR UPDATE ON public.traverse_loop_observations FOR EACH ROW EXECUTE FUNCTION public.travloopobs_search_trigger();


--
-- Name: site_trees tree_search_update; Type: TRIGGER; Schema: public; Owner: -
--

CREATE TRIGGER tree_search_update BEFORE INSERT OR UPDATE ON public.site_trees FOR EACH ROW EXECUTE FUNCTION public.tree_search_trigger();


--
-- Name: standards_entities trigger_update_entity_search_vector; Type: TRIGGER; Schema: public; Owner: -
--

CREATE TRIGGER trigger_update_entity_search_vector BEFORE INSERT OR UPDATE OF canonical_name, description, tags ON public.standards_entities FOR EACH ROW EXECUTE FUNCTION public.update_entity_search_vector();


--
-- Name: typical_sections typsect_search_update; Type: TRIGGER; Schema: public; Owner: -
--

CREATE TRIGGER typsect_search_update BEFORE INSERT OR UPDATE ON public.typical_sections FOR EACH ROW EXECUTE FUNCTION public.typsect_search_trigger();


--
-- Name: utility_network_connectivity utilconn_search_update; Type: TRIGGER; Schema: public; Owner: -
--

CREATE TRIGGER utilconn_search_update BEFORE INSERT OR UPDATE ON public.utility_network_connectivity FOR EACH ROW EXECUTE FUNCTION public.utilconn_search_trigger();


--
-- Name: utility_lines utilline_search_update; Type: TRIGGER; Schema: public; Owner: -
--

CREATE TRIGGER utilline_search_update BEFORE INSERT OR UPDATE ON public.utility_lines FOR EACH ROW EXECUTE FUNCTION public.utilline_search_trigger();


--
-- Name: utility_service_connections utilserv_search_update; Type: TRIGGER; Schema: public; Owner: -
--

CREATE TRIGGER utilserv_search_update BEFORE INSERT OR UPDATE ON public.utility_service_connections FOR EACH ROW EXECUTE FUNCTION public.utilserv_search_trigger();


--
-- Name: utility_structures utilstruct_search_update; Type: TRIGGER; Schema: public; Owner: -
--

CREATE TRIGGER utilstruct_search_update BEFORE INSERT OR UPDATE ON public.utility_structures FOR EACH ROW EXECUTE FUNCTION public.utilstruct_search_trigger();


--
-- Name: layout_viewports viewport_search_update; Type: TRIGGER; Schema: public; Owner: -
--

CREATE TRIGGER viewport_search_update BEFORE INSERT OR UPDATE ON public.layout_viewports FOR EACH ROW EXECUTE FUNCTION public.viewport_search_trigger();


--
-- Name: vertical_profiles vprofile_search_update; Type: TRIGGER; Schema: public; Owner: -
--

CREATE TRIGGER vprofile_search_update BEFORE INSERT OR UPDATE ON public.vertical_profiles FOR EACH ROW EXECUTE FUNCTION public.vprofile_search_trigger();


--
-- Name: cross_sections xsection_search_update; Type: TRIGGER; Schema: public; Owner: -
--

CREATE TRIGGER xsection_search_update BEFORE INSERT OR UPDATE ON public.cross_sections FOR EACH ROW EXECUTE FUNCTION public.xsection_search_trigger();


--
-- Name: cross_section_points xsectpoint_search_update; Type: TRIGGER; Schema: public; Owner: -
--

CREATE TRIGGER xsectpoint_search_update BEFORE INSERT OR UPDATE ON public.cross_section_points FOR EACH ROW EXECUTE FUNCTION public.xsectpoint_search_trigger();


--
-- Name: abbreviation_standards abbreviation_standards_entity_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.abbreviation_standards
    ADD CONSTRAINT abbreviation_standards_entity_id_fkey FOREIGN KEY (entity_id) REFERENCES public.standards_entities(entity_id) ON DELETE SET NULL;


--
-- Name: alignment_pis alignment_pis_alignment_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.alignment_pis
    ADD CONSTRAINT alignment_pis_alignment_id_fkey FOREIGN KEY (alignment_id) REFERENCES public.horizontal_alignments(alignment_id) ON DELETE CASCADE;


--
-- Name: alignment_pis alignment_pis_entity_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.alignment_pis
    ADD CONSTRAINT alignment_pis_entity_id_fkey FOREIGN KEY (entity_id) REFERENCES public.standards_entities(entity_id) ON DELETE SET NULL;


--
-- Name: annotation_standards annotation_standards_entity_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.annotation_standards
    ADD CONSTRAINT annotation_standards_entity_id_fkey FOREIGN KEY (entity_id) REFERENCES public.standards_entities(entity_id) ON DELETE SET NULL;


--
-- Name: block_definitions block_definitions_entity_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.block_definitions
    ADD CONSTRAINT block_definitions_entity_id_fkey FOREIGN KEY (entity_id) REFERENCES public.standards_entities(entity_id) ON DELETE SET NULL;


--
-- Name: block_definitions block_definitions_superseded_by_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.block_definitions
    ADD CONSTRAINT block_definitions_superseded_by_fkey FOREIGN KEY (superseded_by) REFERENCES public.block_definitions(block_id) ON DELETE SET NULL;


--
-- Name: block_inserts block_inserts_entity_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.block_inserts
    ADD CONSTRAINT block_inserts_entity_id_fkey FOREIGN KEY (entity_id) REFERENCES public.standards_entities(entity_id) ON DELETE SET NULL;


--
-- Name: block_inserts block_inserts_layer_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.block_inserts
    ADD CONSTRAINT block_inserts_layer_id_fkey FOREIGN KEY (layer_id) REFERENCES public.layers(layer_id) ON DELETE SET NULL;


--
-- Name: category_standards category_standards_entity_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.category_standards
    ADD CONSTRAINT category_standards_entity_id_fkey FOREIGN KEY (entity_id) REFERENCES public.standards_entities(entity_id) ON DELETE SET NULL;


--
-- Name: category_standards category_standards_parent_category_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.category_standards
    ADD CONSTRAINT category_standards_parent_category_id_fkey FOREIGN KEY (parent_category_id) REFERENCES public.category_standards(category_id);


--
-- Name: classification_confidence classification_confidence_entity_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.classification_confidence
    ADD CONSTRAINT classification_confidence_entity_id_fkey FOREIGN KEY (entity_id) REFERENCES public.standards_entities(entity_id) ON DELETE CASCADE;


--
-- Name: classification_confidence classification_confidence_model_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.classification_confidence
    ADD CONSTRAINT classification_confidence_model_id_fkey FOREIGN KEY (model_id) REFERENCES public.embedding_models(model_id) ON DELETE SET NULL;


--
-- Name: code_standards code_standards_entity_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.code_standards
    ADD CONSTRAINT code_standards_entity_id_fkey FOREIGN KEY (entity_id) REFERENCES public.standards_entities(entity_id) ON DELETE SET NULL;


--
-- Name: color_standards color_standards_entity_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.color_standards
    ADD CONSTRAINT color_standards_entity_id_fkey FOREIGN KEY (entity_id) REFERENCES public.standards_entities(entity_id) ON DELETE SET NULL;


--
-- Name: control_point_membership control_point_membership_entity_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.control_point_membership
    ADD CONSTRAINT control_point_membership_entity_id_fkey FOREIGN KEY (entity_id) REFERENCES public.standards_entities(entity_id) ON DELETE SET NULL;


--
-- Name: control_point_membership control_point_membership_network_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.control_point_membership
    ADD CONSTRAINT control_point_membership_network_id_fkey FOREIGN KEY (network_id) REFERENCES public.survey_control_network(network_id) ON DELETE CASCADE;


--
-- Name: control_point_membership control_point_membership_point_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.control_point_membership
    ADD CONSTRAINT control_point_membership_point_id_fkey FOREIGN KEY (point_id) REFERENCES public.survey_points(point_id) ON DELETE CASCADE;


--
-- Name: coordinate_systems coordinate_systems_entity_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.coordinate_systems
    ADD CONSTRAINT coordinate_systems_entity_id_fkey FOREIGN KEY (entity_id) REFERENCES public.standards_entities(entity_id) ON DELETE SET NULL;


--
-- Name: cross_section_points cross_section_points_entity_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.cross_section_points
    ADD CONSTRAINT cross_section_points_entity_id_fkey FOREIGN KEY (entity_id) REFERENCES public.standards_entities(entity_id) ON DELETE SET NULL;


--
-- Name: cross_section_points cross_section_points_section_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.cross_section_points
    ADD CONSTRAINT cross_section_points_section_id_fkey FOREIGN KEY (section_id) REFERENCES public.cross_sections(section_id) ON DELETE CASCADE;


--
-- Name: cross_sections cross_sections_alignment_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.cross_sections
    ADD CONSTRAINT cross_sections_alignment_id_fkey FOREIGN KEY (alignment_id) REFERENCES public.horizontal_alignments(alignment_id) ON DELETE CASCADE;


--
-- Name: cross_sections cross_sections_entity_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.cross_sections
    ADD CONSTRAINT cross_sections_entity_id_fkey FOREIGN KEY (entity_id) REFERENCES public.standards_entities(entity_id) ON DELETE SET NULL;


--
-- Name: detail_standards detail_standards_entity_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.detail_standards
    ADD CONSTRAINT detail_standards_entity_id_fkey FOREIGN KEY (entity_id) REFERENCES public.standards_entities(entity_id) ON DELETE SET NULL;


--
-- Name: drawing_dimensions drawing_dimensions_entity_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.drawing_dimensions
    ADD CONSTRAINT drawing_dimensions_entity_id_fkey FOREIGN KEY (entity_id) REFERENCES public.standards_entities(entity_id) ON DELETE SET NULL;


--
-- Name: drawing_dimensions drawing_dimensions_layer_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.drawing_dimensions
    ADD CONSTRAINT drawing_dimensions_layer_id_fkey FOREIGN KEY (layer_id) REFERENCES public.layers(layer_id) ON DELETE SET NULL;


--
-- Name: drawing_entities drawing_entities_layer_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.drawing_entities
    ADD CONSTRAINT drawing_entities_layer_id_fkey FOREIGN KEY (layer_id) REFERENCES public.layers(layer_id) ON DELETE SET NULL;


--
-- Name: drawing_entities drawing_entities_standards_entity_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.drawing_entities
    ADD CONSTRAINT drawing_entities_standards_entity_id_fkey FOREIGN KEY (standards_entity_id) REFERENCES public.standards_entities(entity_id) ON DELETE SET NULL;


--
-- Name: drawing_hatches drawing_hatches_entity_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.drawing_hatches
    ADD CONSTRAINT drawing_hatches_entity_id_fkey FOREIGN KEY (entity_id) REFERENCES public.standards_entities(entity_id) ON DELETE SET NULL;


--
-- Name: drawing_hatches drawing_hatches_layer_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.drawing_hatches
    ADD CONSTRAINT drawing_hatches_layer_id_fkey FOREIGN KEY (layer_id) REFERENCES public.layers(layer_id) ON DELETE SET NULL;


--
-- Name: drawing_scale_standards drawing_scale_standards_entity_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.drawing_scale_standards
    ADD CONSTRAINT drawing_scale_standards_entity_id_fkey FOREIGN KEY (entity_id) REFERENCES public.standards_entities(entity_id) ON DELETE SET NULL;


--
-- Name: drawing_text drawing_text_entity_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.drawing_text
    ADD CONSTRAINT drawing_text_entity_id_fkey FOREIGN KEY (entity_id) REFERENCES public.standards_entities(entity_id) ON DELETE SET NULL;


--
-- Name: drawing_text drawing_text_layer_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.drawing_text
    ADD CONSTRAINT drawing_text_layer_id_fkey FOREIGN KEY (layer_id) REFERENCES public.layers(layer_id) ON DELETE SET NULL;


--
-- Name: drawings drawings_entity_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.drawings
    ADD CONSTRAINT drawings_entity_id_fkey FOREIGN KEY (entity_id) REFERENCES public.standards_entities(entity_id) ON DELETE SET NULL;


--
-- Name: drawings drawings_project_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.drawings
    ADD CONSTRAINT drawings_project_id_fkey FOREIGN KEY (project_id) REFERENCES public.projects(project_id) ON DELETE CASCADE;


--
-- Name: earthwork_balance earthwork_balance_alignment_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.earthwork_balance
    ADD CONSTRAINT earthwork_balance_alignment_id_fkey FOREIGN KEY (alignment_id) REFERENCES public.horizontal_alignments(alignment_id) ON DELETE CASCADE;


--
-- Name: earthwork_balance earthwork_balance_entity_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.earthwork_balance
    ADD CONSTRAINT earthwork_balance_entity_id_fkey FOREIGN KEY (entity_id) REFERENCES public.standards_entities(entity_id) ON DELETE SET NULL;


--
-- Name: earthwork_quantities earthwork_quantities_alignment_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.earthwork_quantities
    ADD CONSTRAINT earthwork_quantities_alignment_id_fkey FOREIGN KEY (alignment_id) REFERENCES public.horizontal_alignments(alignment_id) ON DELETE CASCADE;


--
-- Name: earthwork_quantities earthwork_quantities_entity_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.earthwork_quantities
    ADD CONSTRAINT earthwork_quantities_entity_id_fkey FOREIGN KEY (entity_id) REFERENCES public.standards_entities(entity_id) ON DELETE SET NULL;


--
-- Name: easements easements_entity_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.easements
    ADD CONSTRAINT easements_entity_id_fkey FOREIGN KEY (entity_id) REFERENCES public.standards_entities(entity_id) ON DELETE SET NULL;


--
-- Name: easements easements_project_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.easements
    ADD CONSTRAINT easements_project_id_fkey FOREIGN KEY (project_id) REFERENCES public.projects(project_id) ON DELETE CASCADE;


--
-- Name: entity_aliases entity_aliases_entity_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.entity_aliases
    ADD CONSTRAINT entity_aliases_entity_id_fkey FOREIGN KEY (entity_id) REFERENCES public.standards_entities(entity_id) ON DELETE CASCADE;


--
-- Name: entity_embeddings entity_embeddings_entity_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.entity_embeddings
    ADD CONSTRAINT entity_embeddings_entity_id_fkey FOREIGN KEY (entity_id) REFERENCES public.standards_entities(entity_id) ON DELETE CASCADE;


--
-- Name: entity_embeddings entity_embeddings_model_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.entity_embeddings
    ADD CONSTRAINT entity_embeddings_model_id_fkey FOREIGN KEY (model_id) REFERENCES public.embedding_models(model_id) ON DELETE CASCADE;


--
-- Name: entity_relationships entity_relationships_object_entity_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.entity_relationships
    ADD CONSTRAINT entity_relationships_object_entity_id_fkey FOREIGN KEY (object_entity_id) REFERENCES public.standards_entities(entity_id) ON DELETE CASCADE;


--
-- Name: entity_relationships entity_relationships_subject_entity_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.entity_relationships
    ADD CONSTRAINT entity_relationships_subject_entity_id_fkey FOREIGN KEY (subject_entity_id) REFERENCES public.standards_entities(entity_id) ON DELETE CASCADE;


--
-- Name: export_jobs export_jobs_entity_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.export_jobs
    ADD CONSTRAINT export_jobs_entity_id_fkey FOREIGN KEY (entity_id) REFERENCES public.standards_entities(entity_id) ON DELETE SET NULL;


--
-- Name: grading_limits grading_limits_entity_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.grading_limits
    ADD CONSTRAINT grading_limits_entity_id_fkey FOREIGN KEY (entity_id) REFERENCES public.standards_entities(entity_id) ON DELETE SET NULL;


--
-- Name: grading_limits grading_limits_project_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.grading_limits
    ADD CONSTRAINT grading_limits_project_id_fkey FOREIGN KEY (project_id) REFERENCES public.projects(project_id) ON DELETE CASCADE;


--
-- Name: hatch_patterns hatch_patterns_entity_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.hatch_patterns
    ADD CONSTRAINT hatch_patterns_entity_id_fkey FOREIGN KEY (entity_id) REFERENCES public.standards_entities(entity_id) ON DELETE SET NULL;


--
-- Name: horizontal_alignments horizontal_alignments_entity_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.horizontal_alignments
    ADD CONSTRAINT horizontal_alignments_entity_id_fkey FOREIGN KEY (entity_id) REFERENCES public.standards_entities(entity_id) ON DELETE SET NULL;


--
-- Name: horizontal_alignments horizontal_alignments_project_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.horizontal_alignments
    ADD CONSTRAINT horizontal_alignments_project_id_fkey FOREIGN KEY (project_id) REFERENCES public.projects(project_id) ON DELETE CASCADE;


--
-- Name: layer_standards layer_standards_entity_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.layer_standards
    ADD CONSTRAINT layer_standards_entity_id_fkey FOREIGN KEY (entity_id) REFERENCES public.standards_entities(entity_id) ON DELETE SET NULL;


--
-- Name: layer_standards layer_standards_superseded_by_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.layer_standards
    ADD CONSTRAINT layer_standards_superseded_by_fkey FOREIGN KEY (superseded_by) REFERENCES public.layer_standards(layer_id) ON DELETE SET NULL;


--
-- Name: layers layers_entity_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.layers
    ADD CONSTRAINT layers_entity_id_fkey FOREIGN KEY (entity_id) REFERENCES public.standards_entities(entity_id) ON DELETE SET NULL;


--
-- Name: layout_viewports layout_viewports_entity_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.layout_viewports
    ADD CONSTRAINT layout_viewports_entity_id_fkey FOREIGN KEY (entity_id) REFERENCES public.standards_entities(entity_id) ON DELETE SET NULL;


--
-- Name: linetypes linetypes_entity_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.linetypes
    ADD CONSTRAINT linetypes_entity_id_fkey FOREIGN KEY (entity_id) REFERENCES public.standards_entities(entity_id) ON DELETE SET NULL;


--
-- Name: material_standards material_standards_entity_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.material_standards
    ADD CONSTRAINT material_standards_entity_id_fkey FOREIGN KEY (entity_id) REFERENCES public.standards_entities(entity_id) ON DELETE SET NULL;


--
-- Name: network_metrics network_metrics_entity_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.network_metrics
    ADD CONSTRAINT network_metrics_entity_id_fkey FOREIGN KEY (entity_id) REFERENCES public.standards_entities(entity_id) ON DELETE CASCADE;


--
-- Name: parcel_corners parcel_corners_entity_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.parcel_corners
    ADD CONSTRAINT parcel_corners_entity_id_fkey FOREIGN KEY (entity_id) REFERENCES public.standards_entities(entity_id) ON DELETE SET NULL;


--
-- Name: parcel_corners parcel_corners_parcel_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.parcel_corners
    ADD CONSTRAINT parcel_corners_parcel_id_fkey FOREIGN KEY (parcel_id) REFERENCES public.parcels(parcel_id) ON DELETE CASCADE;


--
-- Name: parcel_corners parcel_corners_survey_point_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.parcel_corners
    ADD CONSTRAINT parcel_corners_survey_point_id_fkey FOREIGN KEY (survey_point_id) REFERENCES public.survey_points(point_id) ON DELETE SET NULL;


--
-- Name: parcels parcels_entity_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.parcels
    ADD CONSTRAINT parcels_entity_id_fkey FOREIGN KEY (entity_id) REFERENCES public.standards_entities(entity_id) ON DELETE SET NULL;


--
-- Name: parcels parcels_project_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.parcels
    ADD CONSTRAINT parcels_project_id_fkey FOREIGN KEY (project_id) REFERENCES public.projects(project_id) ON DELETE CASCADE;


--
-- Name: pavement_sections pavement_sections_alignment_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.pavement_sections
    ADD CONSTRAINT pavement_sections_alignment_id_fkey FOREIGN KEY (alignment_id) REFERENCES public.horizontal_alignments(alignment_id) ON DELETE SET NULL;


--
-- Name: pavement_sections pavement_sections_entity_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.pavement_sections
    ADD CONSTRAINT pavement_sections_entity_id_fkey FOREIGN KEY (entity_id) REFERENCES public.standards_entities(entity_id) ON DELETE SET NULL;


--
-- Name: pavement_sections pavement_sections_project_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.pavement_sections
    ADD CONSTRAINT pavement_sections_project_id_fkey FOREIGN KEY (project_id) REFERENCES public.projects(project_id) ON DELETE CASCADE;


--
-- Name: plot_styles plot_styles_entity_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.plot_styles
    ADD CONSTRAINT plot_styles_entity_id_fkey FOREIGN KEY (entity_id) REFERENCES public.standards_entities(entity_id) ON DELETE SET NULL;


--
-- Name: profile_pvis profile_pvis_entity_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.profile_pvis
    ADD CONSTRAINT profile_pvis_entity_id_fkey FOREIGN KEY (entity_id) REFERENCES public.standards_entities(entity_id) ON DELETE SET NULL;


--
-- Name: profile_pvis profile_pvis_profile_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.profile_pvis
    ADD CONSTRAINT profile_pvis_profile_id_fkey FOREIGN KEY (profile_id) REFERENCES public.vertical_profiles(profile_id) ON DELETE CASCADE;


--
-- Name: project_sheet_notes project_sheet_notes_entity_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.project_sheet_notes
    ADD CONSTRAINT project_sheet_notes_entity_id_fkey FOREIGN KEY (entity_id) REFERENCES public.standards_entities(entity_id) ON DELETE SET NULL;


--
-- Name: project_sheet_notes project_sheet_notes_set_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.project_sheet_notes
    ADD CONSTRAINT project_sheet_notes_set_id_fkey FOREIGN KEY (set_id) REFERENCES public.sheet_note_sets(set_id) ON DELETE CASCADE;


--
-- Name: project_sheet_notes project_sheet_notes_standard_note_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.project_sheet_notes
    ADD CONSTRAINT project_sheet_notes_standard_note_id_fkey FOREIGN KEY (standard_note_id) REFERENCES public.standard_notes(note_id) ON DELETE SET NULL;


--
-- Name: projects projects_entity_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.projects
    ADD CONSTRAINT projects_entity_id_fkey FOREIGN KEY (entity_id) REFERENCES public.standards_entities(entity_id) ON DELETE SET NULL;


--
-- Name: right_of_way right_of_way_entity_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.right_of_way
    ADD CONSTRAINT right_of_way_entity_id_fkey FOREIGN KEY (entity_id) REFERENCES public.standards_entities(entity_id) ON DELETE SET NULL;


--
-- Name: right_of_way right_of_way_project_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.right_of_way
    ADD CONSTRAINT right_of_way_project_id_fkey FOREIGN KEY (project_id) REFERENCES public.projects(project_id) ON DELETE CASCADE;


--
-- Name: sheet_drawing_assignments sheet_drawing_assignments_entity_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.sheet_drawing_assignments
    ADD CONSTRAINT sheet_drawing_assignments_entity_id_fkey FOREIGN KEY (entity_id) REFERENCES public.standards_entities(entity_id) ON DELETE SET NULL;


--
-- Name: sheet_drawing_assignments sheet_drawing_assignments_sheet_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.sheet_drawing_assignments
    ADD CONSTRAINT sheet_drawing_assignments_sheet_id_fkey FOREIGN KEY (sheet_id) REFERENCES public.sheets(sheet_id) ON DELETE CASCADE;


--
-- Name: sheet_note_assignments sheet_note_assignments_entity_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.sheet_note_assignments
    ADD CONSTRAINT sheet_note_assignments_entity_id_fkey FOREIGN KEY (entity_id) REFERENCES public.standards_entities(entity_id) ON DELETE SET NULL;


--
-- Name: sheet_note_assignments sheet_note_assignments_project_note_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.sheet_note_assignments
    ADD CONSTRAINT sheet_note_assignments_project_note_id_fkey FOREIGN KEY (project_note_id) REFERENCES public.project_sheet_notes(project_note_id) ON DELETE CASCADE;


--
-- Name: sheet_note_sets sheet_note_sets_entity_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.sheet_note_sets
    ADD CONSTRAINT sheet_note_sets_entity_id_fkey FOREIGN KEY (entity_id) REFERENCES public.standards_entities(entity_id) ON DELETE SET NULL;


--
-- Name: sheet_note_sets sheet_note_sets_project_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.sheet_note_sets
    ADD CONSTRAINT sheet_note_sets_project_id_fkey FOREIGN KEY (project_id) REFERENCES public.projects(project_id) ON DELETE CASCADE;


--
-- Name: sheet_relationships sheet_relationships_entity_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.sheet_relationships
    ADD CONSTRAINT sheet_relationships_entity_id_fkey FOREIGN KEY (entity_id) REFERENCES public.standards_entities(entity_id) ON DELETE SET NULL;


--
-- Name: sheet_relationships sheet_relationships_source_sheet_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.sheet_relationships
    ADD CONSTRAINT sheet_relationships_source_sheet_id_fkey FOREIGN KEY (source_sheet_id) REFERENCES public.sheets(sheet_id) ON DELETE CASCADE;


--
-- Name: sheet_relationships sheet_relationships_target_sheet_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.sheet_relationships
    ADD CONSTRAINT sheet_relationships_target_sheet_id_fkey FOREIGN KEY (target_sheet_id) REFERENCES public.sheets(sheet_id) ON DELETE CASCADE;


--
-- Name: sheet_revisions sheet_revisions_entity_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.sheet_revisions
    ADD CONSTRAINT sheet_revisions_entity_id_fkey FOREIGN KEY (entity_id) REFERENCES public.standards_entities(entity_id) ON DELETE SET NULL;


--
-- Name: sheet_revisions sheet_revisions_sheet_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.sheet_revisions
    ADD CONSTRAINT sheet_revisions_sheet_id_fkey FOREIGN KEY (sheet_id) REFERENCES public.sheets(sheet_id) ON DELETE CASCADE;


--
-- Name: sheet_sets sheet_sets_entity_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.sheet_sets
    ADD CONSTRAINT sheet_sets_entity_id_fkey FOREIGN KEY (entity_id) REFERENCES public.standards_entities(entity_id) ON DELETE SET NULL;


--
-- Name: sheet_sets sheet_sets_project_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.sheet_sets
    ADD CONSTRAINT sheet_sets_project_id_fkey FOREIGN KEY (project_id) REFERENCES public.projects(project_id) ON DELETE CASCADE;


--
-- Name: sheets sheets_entity_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.sheets
    ADD CONSTRAINT sheets_entity_id_fkey FOREIGN KEY (entity_id) REFERENCES public.standards_entities(entity_id) ON DELETE SET NULL;


--
-- Name: sheets sheets_set_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.sheets
    ADD CONSTRAINT sheets_set_id_fkey FOREIGN KEY (set_id) REFERENCES public.sheet_sets(set_id) ON DELETE CASCADE;


--
-- Name: site_trees site_trees_entity_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.site_trees
    ADD CONSTRAINT site_trees_entity_id_fkey FOREIGN KEY (entity_id) REFERENCES public.standards_entities(entity_id) ON DELETE SET NULL;


--
-- Name: site_trees site_trees_project_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.site_trees
    ADD CONSTRAINT site_trees_project_id_fkey FOREIGN KEY (project_id) REFERENCES public.projects(project_id) ON DELETE CASCADE;


--
-- Name: site_trees site_trees_survey_point_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.site_trees
    ADD CONSTRAINT site_trees_survey_point_id_fkey FOREIGN KEY (survey_point_id) REFERENCES public.survey_points(point_id) ON DELETE SET NULL;


--
-- Name: spatial_statistics spatial_statistics_project_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.spatial_statistics
    ADD CONSTRAINT spatial_statistics_project_id_fkey FOREIGN KEY (project_id) REFERENCES public.projects(project_id) ON DELETE CASCADE;


--
-- Name: standard_notes standard_notes_entity_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.standard_notes
    ADD CONSTRAINT standard_notes_entity_id_fkey FOREIGN KEY (entity_id) REFERENCES public.standards_entities(entity_id) ON DELETE SET NULL;


--
-- Name: surface_features surface_features_entity_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.surface_features
    ADD CONSTRAINT surface_features_entity_id_fkey FOREIGN KEY (entity_id) REFERENCES public.standards_entities(entity_id) ON DELETE SET NULL;


--
-- Name: surface_features surface_features_project_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.surface_features
    ADD CONSTRAINT surface_features_project_id_fkey FOREIGN KEY (project_id) REFERENCES public.projects(project_id) ON DELETE CASCADE;


--
-- Name: surface_features surface_features_survey_point_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.surface_features
    ADD CONSTRAINT surface_features_survey_point_id_fkey FOREIGN KEY (survey_point_id) REFERENCES public.survey_points(point_id) ON DELETE SET NULL;


--
-- Name: surface_models surface_models_entity_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.surface_models
    ADD CONSTRAINT surface_models_entity_id_fkey FOREIGN KEY (entity_id) REFERENCES public.standards_entities(entity_id) ON DELETE SET NULL;


--
-- Name: surface_models surface_models_project_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.surface_models
    ADD CONSTRAINT surface_models_project_id_fkey FOREIGN KEY (project_id) REFERENCES public.projects(project_id) ON DELETE CASCADE;


--
-- Name: survey_control_network survey_control_network_entity_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.survey_control_network
    ADD CONSTRAINT survey_control_network_entity_id_fkey FOREIGN KEY (entity_id) REFERENCES public.standards_entities(entity_id) ON DELETE SET NULL;


--
-- Name: survey_control_network survey_control_network_project_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.survey_control_network
    ADD CONSTRAINT survey_control_network_project_id_fkey FOREIGN KEY (project_id) REFERENCES public.projects(project_id) ON DELETE CASCADE;


--
-- Name: survey_observations survey_observations_backsight_point_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.survey_observations
    ADD CONSTRAINT survey_observations_backsight_point_id_fkey FOREIGN KEY (backsight_point_id) REFERENCES public.survey_points(point_id) ON DELETE SET NULL;


--
-- Name: survey_observations survey_observations_entity_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.survey_observations
    ADD CONSTRAINT survey_observations_entity_id_fkey FOREIGN KEY (entity_id) REFERENCES public.standards_entities(entity_id) ON DELETE SET NULL;


--
-- Name: survey_observations survey_observations_instrument_station_point_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.survey_observations
    ADD CONSTRAINT survey_observations_instrument_station_point_id_fkey FOREIGN KEY (instrument_station_point_id) REFERENCES public.survey_points(point_id) ON DELETE SET NULL;


--
-- Name: survey_observations survey_observations_project_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.survey_observations
    ADD CONSTRAINT survey_observations_project_id_fkey FOREIGN KEY (project_id) REFERENCES public.projects(project_id) ON DELETE CASCADE;


--
-- Name: survey_observations survey_observations_target_point_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.survey_observations
    ADD CONSTRAINT survey_observations_target_point_id_fkey FOREIGN KEY (target_point_id) REFERENCES public.survey_points(point_id) ON DELETE SET NULL;


--
-- Name: survey_points survey_points_entity_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.survey_points
    ADD CONSTRAINT survey_points_entity_id_fkey FOREIGN KEY (entity_id) REFERENCES public.standards_entities(entity_id) ON DELETE SET NULL;


--
-- Name: survey_points survey_points_project_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.survey_points
    ADD CONSTRAINT survey_points_project_id_fkey FOREIGN KEY (project_id) REFERENCES public.projects(project_id) ON DELETE CASCADE;


--
-- Name: survey_points survey_points_superseded_by_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.survey_points
    ADD CONSTRAINT survey_points_superseded_by_fkey FOREIGN KEY (superseded_by) REFERENCES public.survey_points(point_id) ON DELETE SET NULL;


--
-- Name: temporal_changes temporal_changes_entity_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.temporal_changes
    ADD CONSTRAINT temporal_changes_entity_id_fkey FOREIGN KEY (entity_id) REFERENCES public.standards_entities(entity_id) ON DELETE CASCADE;


--
-- Name: text_styles text_styles_entity_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.text_styles
    ADD CONSTRAINT text_styles_entity_id_fkey FOREIGN KEY (entity_id) REFERENCES public.standards_entities(entity_id) ON DELETE SET NULL;


--
-- Name: traverse_loop_observations traverse_loop_observations_entity_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.traverse_loop_observations
    ADD CONSTRAINT traverse_loop_observations_entity_id_fkey FOREIGN KEY (entity_id) REFERENCES public.standards_entities(entity_id) ON DELETE SET NULL;


--
-- Name: traverse_loop_observations traverse_loop_observations_loop_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.traverse_loop_observations
    ADD CONSTRAINT traverse_loop_observations_loop_id_fkey FOREIGN KEY (loop_id) REFERENCES public.traverse_loops(loop_id) ON DELETE CASCADE;


--
-- Name: traverse_loop_observations traverse_loop_observations_observation_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.traverse_loop_observations
    ADD CONSTRAINT traverse_loop_observations_observation_id_fkey FOREIGN KEY (observation_id) REFERENCES public.survey_observations(observation_id) ON DELETE CASCADE;


--
-- Name: traverse_loop_observations traverse_loop_observations_point_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.traverse_loop_observations
    ADD CONSTRAINT traverse_loop_observations_point_id_fkey FOREIGN KEY (point_id) REFERENCES public.survey_points(point_id) ON DELETE CASCADE;


--
-- Name: traverse_loops traverse_loops_entity_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.traverse_loops
    ADD CONSTRAINT traverse_loops_entity_id_fkey FOREIGN KEY (entity_id) REFERENCES public.standards_entities(entity_id) ON DELETE SET NULL;


--
-- Name: traverse_loops traverse_loops_project_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.traverse_loops
    ADD CONSTRAINT traverse_loops_project_id_fkey FOREIGN KEY (project_id) REFERENCES public.projects(project_id) ON DELETE CASCADE;


--
-- Name: typical_sections typical_sections_entity_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.typical_sections
    ADD CONSTRAINT typical_sections_entity_id_fkey FOREIGN KEY (entity_id) REFERENCES public.standards_entities(entity_id) ON DELETE SET NULL;


--
-- Name: typical_sections typical_sections_project_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.typical_sections
    ADD CONSTRAINT typical_sections_project_id_fkey FOREIGN KEY (project_id) REFERENCES public.projects(project_id) ON DELETE CASCADE;


--
-- Name: utility_lines utility_lines_entity_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.utility_lines
    ADD CONSTRAINT utility_lines_entity_id_fkey FOREIGN KEY (entity_id) REFERENCES public.standards_entities(entity_id) ON DELETE SET NULL;


--
-- Name: utility_lines utility_lines_from_structure_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.utility_lines
    ADD CONSTRAINT utility_lines_from_structure_id_fkey FOREIGN KEY (from_structure_id) REFERENCES public.utility_structures(structure_id) ON DELETE SET NULL;


--
-- Name: utility_lines utility_lines_project_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.utility_lines
    ADD CONSTRAINT utility_lines_project_id_fkey FOREIGN KEY (project_id) REFERENCES public.projects(project_id) ON DELETE CASCADE;


--
-- Name: utility_lines utility_lines_to_structure_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.utility_lines
    ADD CONSTRAINT utility_lines_to_structure_id_fkey FOREIGN KEY (to_structure_id) REFERENCES public.utility_structures(structure_id) ON DELETE SET NULL;


--
-- Name: utility_network_connectivity utility_network_connectivity_entity_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.utility_network_connectivity
    ADD CONSTRAINT utility_network_connectivity_entity_id_fkey FOREIGN KEY (entity_id) REFERENCES public.standards_entities(entity_id) ON DELETE SET NULL;


--
-- Name: utility_service_connections utility_service_connections_entity_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.utility_service_connections
    ADD CONSTRAINT utility_service_connections_entity_id_fkey FOREIGN KEY (entity_id) REFERENCES public.standards_entities(entity_id) ON DELETE SET NULL;


--
-- Name: utility_service_connections utility_service_connections_line_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.utility_service_connections
    ADD CONSTRAINT utility_service_connections_line_id_fkey FOREIGN KEY (line_id) REFERENCES public.utility_lines(line_id) ON DELETE CASCADE;


--
-- Name: utility_service_connections utility_service_connections_structure_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.utility_service_connections
    ADD CONSTRAINT utility_service_connections_structure_id_fkey FOREIGN KEY (structure_id) REFERENCES public.utility_structures(structure_id) ON DELETE SET NULL;


--
-- Name: utility_structures utility_structures_entity_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.utility_structures
    ADD CONSTRAINT utility_structures_entity_id_fkey FOREIGN KEY (entity_id) REFERENCES public.standards_entities(entity_id) ON DELETE SET NULL;


--
-- Name: utility_structures utility_structures_project_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.utility_structures
    ADD CONSTRAINT utility_structures_project_id_fkey FOREIGN KEY (project_id) REFERENCES public.projects(project_id) ON DELETE CASCADE;


--
-- Name: utility_structures utility_structures_survey_point_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.utility_structures
    ADD CONSTRAINT utility_structures_survey_point_id_fkey FOREIGN KEY (survey_point_id) REFERENCES public.survey_points(point_id) ON DELETE SET NULL;


--
-- Name: vertical_profiles vertical_profiles_alignment_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.vertical_profiles
    ADD CONSTRAINT vertical_profiles_alignment_id_fkey FOREIGN KEY (alignment_id) REFERENCES public.horizontal_alignments(alignment_id) ON DELETE CASCADE;


--
-- Name: vertical_profiles vertical_profiles_entity_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.vertical_profiles
    ADD CONSTRAINT vertical_profiles_entity_id_fkey FOREIGN KEY (entity_id) REFERENCES public.standards_entities(entity_id) ON DELETE SET NULL;


--
-- PostgreSQL database dump complete
--

