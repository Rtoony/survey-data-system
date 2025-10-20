"""
ACAD=GIS Enhanced FastAPI Server
Adds CRUD operations, file upload, and export functionality
"""

from fastapi import FastAPI, HTTPException, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, FileResponse
from typing import List, Dict, Any, Optional
from pydantic import BaseModel
import uvicorn
import os
import tempfile
from datetime import datetime

# Import your database module
import database

app = FastAPI(
    title="ACAD=GIS Enhanced API",
    description="REST API with full CRUD operations",
    version="2.0.0"
)

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ============================================
# PYDANTIC MODELS
# ============================================

class ProjectCreate(BaseModel):
    project_name: str
    project_number: Optional[str] = None
    client_name: Optional[str] = None
    description: Optional[str] = None

class ProjectUpdate(BaseModel):
    project_name: Optional[str] = None
    project_number: Optional[str] = None
    client_name: Optional[str] = None
    description: Optional[str] = None

class DrawingCreate(BaseModel):
    project_id: str
    drawing_name: str
    drawing_number: Optional[str] = None
    drawing_type: Optional[str] = None
    scale: Optional[str] = None
    description: Optional[str] = None

class DrawingUpdate(BaseModel):
    drawing_name: Optional[str] = None
    drawing_number: Optional[str] = None
    drawing_type: Optional[str] = None
    scale: Optional[str] = None
    description: Optional[str] = None

# ============================================
# CIVILMICROTOOLS MODELS (stubs)
# ============================================

class PipeNetworkCreate(BaseModel):
    project_id: Optional[str] = None
    name: Optional[str] = None
    description: Optional[str] = None

class StructureCreate(BaseModel):
    network_id: Optional[str] = None
    type: Optional[str] = None
    rim_elev: Optional[float] = None
    sump_depth: Optional[float] = None

class PipeCreate(BaseModel):
    network_id: Optional[str] = None
    up_structure_id: Optional[str] = None
    down_structure_id: Optional[str] = None
    diameter_mm: Optional[float] = None
    material: Optional[str] = None
    slope: Optional[float] = None

class AlignmentCreate(BaseModel):
    project_id: Optional[str] = None
    name: Optional[str] = None
    design_speed: Optional[float] = None

class BMPCreate(BaseModel):
    project_id: Optional[str] = None
    type: Optional[str] = None
    area_acres: Optional[float] = None
    drainage_area_acres: Optional[float] = None

class UtilityCreate(BaseModel):
    project_id: Optional[str] = None
    company: Optional[str] = None
    type: Optional[str] = None

class ConflictCreate(BaseModel):
    project_id: Optional[str] = None
    utility_id: Optional[str] = None
    description: Optional[str] = None

# ============================================
# HEALTH CHECK
# ============================================

@app.get("/")
def root():
    return {
        "status": "online",
        "message": "ACAD=GIS Enhanced API Server",
        "version": "2.0.0"
    }

@app.get("/api/health")
def health_check():
    try:
        with database.get_db_connection() as conn:
            result = database.execute_single("SELECT COUNT(*) as count FROM projects")
            return {
                "status": "healthy",
                "database": "connected",
                "projects_count": result['count']
            }
    except Exception as e:
        return JSONResponse(
            status_code=503,
            content={
                "status": "unhealthy",
                "database": "disconnected",
                "error": str(e)
            }
        )

# ============================================
# STATISTICS
# ============================================

@app.get("/api/stats")
def get_statistics():
    try:
        stats = {}
        
        result = database.execute_single("SELECT COUNT(*) as count FROM projects")
        stats['total_projects'] = result['count']
        
        result = database.execute_single("SELECT COUNT(*) as count FROM drawings")
        stats['total_drawings'] = result['count']
        
        result = database.execute_single("SELECT COUNT(*) as count FROM block_definitions")
        stats['total_symbols'] = result['count']
        
        result = database.execute_single("SELECT COUNT(*) as count FROM layer_standards")
        stats['total_layers'] = result['count']
        
        recent_drawings = database.execute_query(
            "SELECT drawing_name, created_at FROM drawings ORDER BY created_at DESC LIMIT 5"
        )
        stats['recent_drawings'] = recent_drawings
        
        return stats
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get statistics: {str(e)}")

# ============================================
# PROJECTS - FULL CRUD
# ============================================

@app.get("/api/projects")
def get_projects():
    """Get all projects with drawing counts"""
    try:
        query = """
            SELECT 
                p.*,
                COUNT(d.drawing_id) as drawing_count
            FROM projects p
            LEFT JOIN drawings d ON p.project_id = d.project_id
            GROUP BY p.project_id
            ORDER BY p.created_at DESC
        """
        projects = database.execute_query(query)
        return projects
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get projects: {str(e)}")

@app.get("/api/projects/{project_id}")
def get_project(project_id: str):
    """Get single project details"""
    try:
        project = database.get_project(project_id)
        if not project:
            raise HTTPException(status_code=404, detail="Project not found")
        return project
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get project: {str(e)}")

@app.post("/api/projects")
def create_project(project: ProjectCreate):
    """Create new project"""
    try:
        project_id = database.create_project(
            project_name=project.project_name,
            project_number=project.project_number,
            client_name=project.client_name,
            description=project.description
        )
        
        return {
            "project_id": project_id,
            "message": "Project created successfully"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create project: {str(e)}")

@app.put("/api/projects/{project_id}")
def update_project(project_id: str, project: ProjectUpdate):
    """Update existing project"""
    try:
        # Check if project exists
        existing = database.get_project(project_id)
        if not existing:
            raise HTTPException(status_code=404, detail="Project not found")
        
        # Build update query dynamically based on provided fields
        update_fields = []
        params = []
        
        if project.project_name is not None:
            update_fields.append("project_name = %s")
            params.append(project.project_name)
        if project.project_number is not None:
            update_fields.append("project_number = %s")
            params.append(project.project_number)
        if project.client_name is not None:
            update_fields.append("client_name = %s")
            params.append(project.client_name)
        if project.description is not None:
            update_fields.append("description = %s")
            params.append(project.description)
        
        if not update_fields:
            return {"message": "No fields to update"}
        
        update_fields.append("updated_at = CURRENT_TIMESTAMP")
        params.append(project_id)
        
        query = f"UPDATE projects SET {', '.join(update_fields)} WHERE project_id = %s"
        database.execute_query(query, tuple(params))
        
        return {"message": "Project updated successfully"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to update project: {str(e)}")

@app.delete("/api/projects/{project_id}")
def delete_project(project_id: str):
    """Delete project (will cascade to drawings if configured)"""
    try:
        # Check if project exists
        existing = database.get_project(project_id)
        if not existing:
            raise HTTPException(status_code=404, detail="Project not found")
        
        # Check if project has drawings
        drawings = database.execute_query(
            "SELECT COUNT(*) as count FROM drawings WHERE project_id = %s",
            (project_id,)
        )
        drawing_count = drawings[0]['count'] if drawings else 0
        
        if drawing_count > 0:
            # You might want to prevent deletion or cascade
            # For now, we'll prevent it and return an error
            raise HTTPException(
                status_code=400,
                detail=f"Cannot delete project with {drawing_count} drawings. Delete drawings first."
            )
        
        database.execute_query("DELETE FROM projects WHERE project_id = %s", (project_id,))
        
        return {"message": "Project deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to delete project: {str(e)}")

# ============================================
# DRAWINGS - FULL CRUD
# ============================================

@app.get("/api/projects/{project_id}/drawings")
def get_project_drawings(project_id: str):
    """Get all drawings for a project"""
    try:
        query = """
            SELECT 
                drawing_id,
                drawing_name,
                drawing_number,
                drawing_type,
                scale,
                description,
                created_at,
                updated_at,
                is_georeferenced,
                CASE 
                    WHEN dxf_content IS NOT NULL THEN true 
                    ELSE false 
                END as has_content
            FROM drawings
            WHERE project_id = %s
            ORDER BY drawing_number, drawing_name
        """
        drawings = database.execute_query(query, (project_id,))
        return drawings
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get drawings: {str(e)}")

@app.get("/api/drawings")
def get_all_drawings(limit: int = 100, search: Optional[str] = None):
    """Get all drawings with optional search"""
    try:
        if search:
            query = """
                SELECT 
                    d.drawing_id,
                    d.drawing_name,
                    d.drawing_number,
                    d.drawing_type,
                    d.scale,
                    d.created_at,
                    d.is_georeferenced,
                    d.drawing_epsg_code,
                    d.drawing_coordinate_system,
                    p.project_name,
                    p.project_id,
                    p.project_number,
                    CASE 
                        WHEN d.dxf_content IS NOT NULL THEN true 
                        ELSE false 
                    END as has_content
                FROM drawings d
                LEFT JOIN projects p ON d.project_id = p.project_id
                WHERE d.drawing_name ILIKE %s OR d.drawing_number ILIKE %s OR p.project_name ILIKE %s
                ORDER BY d.created_at DESC
                LIMIT %s
            """
            search_term = f"%{search}%"
            drawings = database.execute_query(query, (search_term, search_term, search_term, limit))
        else:
            query = """
                SELECT 
                    d.drawing_id,
                    d.drawing_name,
                    d.drawing_number,
                    d.drawing_type,
                    d.scale,
                    d.created_at,
                    d.is_georeferenced,
                    d.drawing_epsg_code,
                    d.drawing_coordinate_system,
                    p.project_name,
                    p.project_id,
                    p.project_number,
                    CASE 
                        WHEN d.dxf_content IS NOT NULL THEN true 
                        ELSE false 
                    END as has_content
                FROM drawings d
                LEFT JOIN projects p ON d.project_id = p.project_id
                ORDER BY d.created_at DESC
                LIMIT %s
            """
            drawings = database.execute_query(query, (limit,))
        
        return drawings
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get drawings: {str(e)}")

@app.get("/api/drawings/{drawing_id}")
def get_drawing(drawing_id: str):
    """Get basic drawing information"""
    try:
        drawing = database.get_drawing(drawing_id)
        if not drawing:
            raise HTTPException(status_code=404, detail="Drawing not found")
        
        if 'dxf_content' in drawing:
            drawing['has_dxf_content'] = drawing['dxf_content'] is not None
            del drawing['dxf_content']
        
        return drawing
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get drawing: {str(e)}")

@app.post("/api/drawings")
def create_drawing(drawing: DrawingCreate):
    """Create new drawing"""
    try:
        drawing_id = database.create_drawing(
            project_id=drawing.project_id,
            drawing_name=drawing.drawing_name,
            drawing_number=drawing.drawing_number,
            drawing_type=drawing.drawing_type,
            scale=drawing.scale,
            description=drawing.description
        )
        
        return {
            "drawing_id": drawing_id,
            "message": "Drawing created successfully"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create drawing: {str(e)}")

@app.put("/api/drawings/{drawing_id}")
def update_drawing(drawing_id: str, drawing: DrawingUpdate):
    """Update existing drawing"""
    try:
        # Check if drawing exists
        existing = database.get_drawing(drawing_id)
        if not existing:
            raise HTTPException(status_code=404, detail="Drawing not found")
        
        # Build update query dynamically
        update_fields = []
        params = []
        
        if drawing.drawing_name is not None:
            update_fields.append("drawing_name = %s")
            params.append(drawing.drawing_name)
        if drawing.drawing_number is not None:
            update_fields.append("drawing_number = %s")
            params.append(drawing.drawing_number)
        if drawing.drawing_type is not None:
            update_fields.append("drawing_type = %s")
            params.append(drawing.drawing_type)
        if drawing.scale is not None:
            update_fields.append("scale = %s")
            params.append(drawing.scale)
        if drawing.description is not None:
            update_fields.append("description = %s")
            params.append(drawing.description)
        
        if not update_fields:
            return {"message": "No fields to update"}
        
        update_fields.append("updated_at = CURRENT_TIMESTAMP")
        params.append(drawing_id)
        
        query = f"UPDATE drawings SET {', '.join(update_fields)} WHERE drawing_id = %s"
        database.execute_query(query, tuple(params))
        
        return {"message": "Drawing updated successfully"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to update drawing: {str(e)}")

@app.delete("/api/drawings/{drawing_id}")
def delete_drawing(drawing_id: str):
    """Delete drawing"""
    try:
        # Check if drawing exists
        existing = database.get_drawing(drawing_id)
        if not existing:
            raise HTTPException(status_code=404, detail="Drawing not found")
        
        # Delete associated data first (layers, inserts, etc.)
        database.execute_query("DELETE FROM block_inserts WHERE drawing_id = %s", (drawing_id,))
        database.execute_query("DELETE FROM layers WHERE drawing_id = %s", (drawing_id,))
        database.execute_query("DELETE FROM drawings WHERE drawing_id = %s", (drawing_id,))
        
        return {"message": "Drawing deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to delete drawing: {str(e)}")

# ============================================
# DRAWING VIEWER DATA
# ============================================

@app.get("/api/drawings/{drawing_id}/render")
def get_drawing_render_data(drawing_id: str, limit: int = 2500):
    """Get all data needed to render a drawing"""
    try:
        # Get basic drawing info
        drawing = database.get_drawing(drawing_id)
        if not drawing:
            raise HTTPException(status_code=404, detail="Drawing not found")
        
        # Get layers
        layers = database.get_layers(drawing_id)
        
        # Get block inserts with symbol details
        query = """
            SELECT 
                bi.insert_id,
                bi.insert_x,
                bi.insert_y,
                bi.insert_z,
                bi.scale_x,
                bi.scale_y,
                bi.rotation,
                bi.layout_name,
                bi.metadata,
                bd.block_id,
                bd.block_name,
                bd.svg_content,
                bd.category,
                bd.domain,
                bd.semantic_type,
                bd.semantic_label,
                bd.description as block_description,
                bd.svg_viewbox
            FROM block_inserts bi
            JOIN block_definitions bd ON bi.block_id = bd.block_id
            WHERE bi.drawing_id = %s
            ORDER BY bi.created_at
            LIMIT %s
        """
        inserts = database.execute_query(query, (drawing_id, limit))
        
        # Calculate drawing bounds
        bounds = calculate_drawing_bounds(inserts)
        
        # Check total count
        count_query = "SELECT COUNT(*) as total_count FROM block_inserts WHERE drawing_id = %s"
        total_result = database.execute_single(count_query, (drawing_id,))
        total_inserts = total_result['total_count'] if total_result else 0
        is_truncated = total_inserts > limit
        
        return {
            "drawing": {
                "drawing_id": drawing['drawing_id'],
                "drawing_name": drawing['drawing_name'],
                "drawing_number": drawing.get('drawing_number'),
                "is_georeferenced": drawing.get('is_georeferenced', False),
                "drawing_coordinate_system": drawing.get('drawing_coordinate_system'),
                "drawing_epsg_code": drawing.get('drawing_epsg_code')
            },
            "layers": layers,
            "inserts": inserts,
            "bounds": bounds,
            "stats": {
                "insert_count": len(inserts),
                "total_inserts": total_inserts,
                "is_truncated": is_truncated,
                "layer_count": len(layers)
            }
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get drawing data: {str(e)}")

@app.get("/api/drawings/{drawing_id}/extent")
def get_drawing_extent(drawing_id: str):
    """Return full drawing bounds (no row limit) and EPSG code.

    Bounds are computed from all block_inserts for the drawing. If no inserts
    exist, returns count=0 and zero bounds so clients can handle gracefully.
    """
    try:
        drawing = database.get_drawing(drawing_id)
        if not drawing:
            raise HTTPException(status_code=404, detail="Drawing not found")

        bounds_row = database.execute_single(
            """
            SELECT
                MIN(insert_x) AS min_x,
                MIN(insert_y) AS min_y,
                MAX(insert_x) AS max_x,
                MAX(insert_y) AS max_y,
                COUNT(*)      AS feature_count
            FROM block_inserts
            WHERE drawing_id = %s
            """,
            (drawing_id,)
        )

        feature_count = bounds_row.get('feature_count', 0) if bounds_row else 0
        if not bounds_row or bounds_row['min_x'] is None or bounds_row['min_y'] is None:
            # No symbol data yet; return empty bounds
            bounds = {"min_x": 0, "min_y": 0, "max_x": 0, "max_y": 0}
        else:
            bounds = {
                "min_x": float(bounds_row['min_x']),
                "min_y": float(bounds_row['min_y']),
                "max_x": float(bounds_row['max_x']),
                "max_y": float(bounds_row['max_y'])
            }

        return {
            "drawing_epsg_code": drawing.get('drawing_epsg_code'),
            "bounds": bounds,
            "stats": {"feature_count": feature_count}
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get drawing extent: {str(e)}")

def calculate_drawing_bounds(inserts):
    """Calculate bounding box for drawing"""
    if not inserts:
        return {"min_x": 0, "max_x": 0, "min_y": 0, "max_y": 0}
    
    min_x = min_y = float('inf')
    max_x = max_y = float('-inf')
    
    for insert in inserts:
        if insert.get('insert_x') is not None:
            min_x = min(min_x, insert['insert_x'])
            max_x = max(max_x, insert['insert_x'])
        if insert.get('insert_y') is not None:
            min_y = min(min_y, insert['insert_y'])
            max_y = max(max_y, insert['insert_y'])
    
    return {
        "min_x": min_x if min_x != float('inf') else 0,
        "max_x": max_x if max_x != float('-inf') else 0,
        "min_y": min_y if min_y != float('inf') else 0,
        "max_y": max_y if max_y != float('-inf') else 0
    }

# ============================================
# IMPORT/EXPORT
# ============================================

@app.post("/api/import/dxf")
async def import_dxf(
    file: UploadFile = File(...),
    project_id: str = Form(...),
    drawing_name: Optional[str] = Form(None),
    is_georeferenced: bool = Form(False),
    epsg_code: Optional[str] = Form(None)
):
    """Import DXF file"""
    try:
        # Validate file type
        if not file.filename.endswith('.dxf'):
            raise HTTPException(status_code=400, detail="Only DXF files are supported")
        
        # Save file temporarily
        with tempfile.NamedTemporaryFile(delete=False, suffix='.dxf') as tmp:
            content = await file.read()
            tmp.write(content)
            tmp_path = tmp.name
        
        # TODO: Process DXF file using your import script
        # For now, return a placeholder response
        drawing_name = drawing_name or file.filename.replace('.dxf', '')
        
        return {
            "success": True,
            "message": f"DXF file '{file.filename}' uploaded successfully",
            "drawing_name": drawing_name,
            "file_size": len(content),
            "note": "Processing functionality needs to be implemented"
        }
        
        # Clean up temp file
        # os.unlink(tmp_path)
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to import DXF: {str(e)}")

@app.get("/api/export/{drawing_id}")
def export_drawing(drawing_id: str, format: str = "dxf"):
    """Export drawing to DXF or other format"""
    try:
        drawing = database.get_drawing(drawing_id)
        if not drawing:
            raise HTTPException(status_code=404, detail="Drawing not found")
        
        # TODO: Implement actual export logic
        # For now, return a placeholder
        return {
            "success": False,
            "message": "Export functionality needs to be implemented",
            "drawing_id": drawing_id,
            "format": format
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to export drawing: {str(e)}")

@app.post("/api/export/{format}")
def export_generic(format: str, payload: Dict[str, Any] = None):
    return {
        "success": True,
        "message": f"Export stub: {format}",
        "request": payload or {}
    }

# ============================================
# CIVILMICROTOOLS STUB ENDPOINTS
# ============================================

# Pipe Networks
@app.get("/api/pipe-networks")
def list_pipe_networks():
    return []

@app.post("/api/pipe-networks")
def create_pipe_network(payload: PipeNetworkCreate):
    return {"network_id": "stub", "message": "Pipe network creation stub"}

@app.get("/api/pipe-networks/{network_id}")
def get_pipe_network(network_id: str):
    return {"network_id": network_id, "message": "Pipe network get stub"}

@app.put("/api/pipe-networks/{network_id}")
def update_pipe_network(network_id: str, payload: PipeNetworkCreate):
    return {"network_id": network_id, "message": "Pipe network update stub"}

@app.delete("/api/pipe-networks/{network_id}")
def delete_pipe_network(network_id: str):
    return {"network_id": network_id, "message": "Pipe network delete stub"}

# Pipes
@app.get("/api/pipes")
def list_pipes():
    return []

@app.post("/api/pipes")
def create_pipe(payload: PipeCreate):
    return {"pipe_id": "stub", "message": "Pipe creation stub"}

@app.get("/api/pipes/{pipe_id}")
def get_pipe(pipe_id: str):
    return {"pipe_id": pipe_id, "message": "Pipe get stub"}

@app.put("/api/pipes/{pipe_id}")
def update_pipe(pipe_id: str, payload: PipeCreate):
    return {"pipe_id": pipe_id, "message": "Pipe update stub"}

@app.delete("/api/pipes/{pipe_id}")
def delete_pipe(pipe_id: str):
    return {"pipe_id": pipe_id, "message": "Pipe delete stub"}

# Structures
@app.get("/api/structures")
def list_structures():
    return []

@app.post("/api/structures")
def create_structure(payload: StructureCreate):
    return {"structure_id": "stub", "message": "Structure creation stub"}

@app.get("/api/structures/{structure_id}")
def get_structure(structure_id: str):
    return {"structure_id": structure_id, "message": "Structure get stub"}

@app.put("/api/structures/{structure_id}")
def update_structure(structure_id: str, payload: StructureCreate):
    return {"structure_id": structure_id, "message": "Structure update stub"}

@app.delete("/api/structures/{structure_id}")
def delete_structure(structure_id: str):
    return {"structure_id": structure_id, "message": "Structure delete stub"}

# Alignments
@app.get("/api/alignments")
def list_alignments():
    return []

@app.post("/api/alignments")
def create_alignment(payload: AlignmentCreate):
    return {"alignment_id": "stub", "message": "Alignment creation stub"}

@app.get("/api/alignments/{alignment_id}")
def get_alignment(alignment_id: str):
    return {"alignment_id": alignment_id, "message": "Alignment get stub"}

@app.put("/api/alignments/{alignment_id}")
def update_alignment(alignment_id: str, payload: AlignmentCreate):
    return {"alignment_id": alignment_id, "message": "Alignment update stub"}

@app.delete("/api/alignments/{alignment_id}")
def delete_alignment(alignment_id: str):
    return {"alignment_id": alignment_id, "message": "Alignment delete stub"}

@app.get("/api/alignments/{alignment_id}/horizontal-elements")
def list_horizontal_elements(alignment_id: str):
    return []

@app.post("/api/alignments/{alignment_id}/horizontal-elements")
def create_horizontal_element(alignment_id: str, payload: Dict[str, Any]):
    return {"element_id": "stub", "message": "Horizontal element creation stub"}

@app.get("/api/alignments/{alignment_id}/vertical-elements")
def list_vertical_elements(alignment_id: str):
    return []

@app.post("/api/alignments/{alignment_id}/vertical-elements")
def create_vertical_element(alignment_id: str, payload: Dict[str, Any]):
    return {"element_id": "stub", "message": "Vertical element creation stub"}

# BMPs
@app.get("/api/bmps")
def list_bmps():
    return []

@app.post("/api/bmps")
def create_bmp(payload: BMPCreate):
    return {"bmp_id": "stub", "message": "BMP creation stub"}

@app.get("/api/bmps/{bmp_id}")
def get_bmp(bmp_id: str):
    return {"bmp_id": bmp_id, "message": "BMP get stub"}

@app.put("/api/bmps/{bmp_id}")
def update_bmp(bmp_id: str, payload: BMPCreate):
    return {"bmp_id": bmp_id, "message": "BMP update stub"}

@app.delete("/api/bmps/{bmp_id}")
def delete_bmp(bmp_id: str):
    return {"bmp_id": bmp_id, "message": "BMP delete stub"}

@app.get("/api/bmps/{bmp_id}/inspections")
def list_bmp_inspections(bmp_id: str):
    return []

@app.post("/api/bmps/{bmp_id}/inspections")
def create_bmp_inspection(bmp_id: str, payload: Dict[str, Any]):
    return {"inspection_id": "stub", "message": "BMP inspection creation stub"}

@app.get("/api/bmps/{bmp_id}/maintenance")
def list_bmp_maintenance(bmp_id: str):
    return []

@app.post("/api/bmps/{bmp_id}/maintenance")
def create_bmp_maintenance(bmp_id: str, payload: Dict[str, Any]):
    return {"record_id": "stub", "message": "BMP maintenance creation stub"}

# Utilities & Conflicts
@app.get("/api/utilities")
def list_utilities():
    return []

@app.post("/api/utilities")
def create_utility(payload: UtilityCreate):
    return {"utility_id": "stub", "message": "Utility creation stub"}

@app.get("/api/utilities/{utility_id}")
def get_utility(utility_id: str):
    return {"utility_id": utility_id, "message": "Utility get stub"}

@app.put("/api/utilities/{utility_id}")
def update_utility(utility_id: str, payload: UtilityCreate):
    return {"utility_id": utility_id, "message": "Utility update stub"}

@app.delete("/api/utilities/{utility_id}")
def delete_utility(utility_id: str):
    return {"utility_id": utility_id, "message": "Utility delete stub"}

@app.get("/api/conflicts")
def list_conflicts():
    return []

@app.post("/api/conflicts")
def create_conflict(payload: ConflictCreate):
    return {"conflict_id": "stub", "message": "Conflict creation stub"}

@app.put("/api/conflicts/{conflict_id}")
def update_conflict(conflict_id: str, payload: Dict[str, Any]):
    return {"conflict_id": conflict_id, "message": "Conflict update stub"}

# GeoJSON endpoints (empty feature collections)
def _empty_fc():
    return {"type": "FeatureCollection", "features": []}

@app.get("/api/pipes/geojson")
def pipes_geojson(bbox: Optional[str] = None, srid: Optional[int] = None, limit: Optional[int] = None):
    return _empty_fc()

@app.get("/api/structures/geojson")
def structures_geojson(bbox: Optional[str] = None, srid: Optional[int] = None, limit: Optional[int] = None):
    return _empty_fc()

@app.get("/api/alignments/{alignment_id}/geojson")
def alignment_geojson(alignment_id: str):
    return _empty_fc()

@app.get("/api/bmps/geojson")
def bmps_geojson(bbox: Optional[str] = None, srid: Optional[int] = None, type: Optional[str] = None):
    return _empty_fc()

# Validation stubs
@app.post("/api/validate/pipe-slope")
def validate_pipe_slope(scope: Dict[str, Any]):
    return {"success": True, "message": "Validation stub: pipe slope", "results": []}

@app.post("/api/validate/velocity")
def validate_velocity(scope: Dict[str, Any]):
    return {"success": True, "message": "Validation stub: velocity", "results": []}

@app.post("/api/clash-detection")
def clash_detection(scope: Dict[str, Any]):
    return {"success": True, "message": "Clash detection stub", "conflicts": []}

# ============================================
# RUN SERVER
# ============================================

if __name__ == "__main__":
    print("🚀 Starting ACAD=GIS Enhanced API Server...")
    print("📡 Server running at: http://localhost:8000")
    print("📖 API Docs at: http://localhost:8000/docs")
    print("🔥 Press CTRL+C to stop")
    print("")
    uvicorn.run(app, host="0.0.0.0", port=8000)
