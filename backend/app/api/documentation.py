"""
API endpoints for documentation generation functionality.
"""

from typing import List, Optional, Dict, Any
import logging
from uuid import uuid4
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, Query, BackgroundTasks
from fastapi.responses import Response, FileResponse

from app.models.documentation import (
    DocumentationGenerationRequest,
    BatchDocumentationRequest,
    DocumentationStatus,
    TemplateListResponse,
    DocumentationConfig,
    DocumentationFormat
)
from app.auth.auth_models import User
from app.auth.permissions import require_auth
from app.services.documentation_generator import DocumentationGenerator
from pathlib import Path
import yaml
import json
import hashlib

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/documentation", tags=["documentation"])

# Demo router (no auth required)
demo_router = APIRouter()

# In-memory job storage (in production, use Redis or database)
documentation_jobs: Dict[str, DocumentationStatus] = {}

# In-memory storage for demo documentation (model_id -> latest generated doc)
demo_documentation_cache: Dict[str, Dict[str, Any]] = {}

# File-based cache directory
CACHE_DIR = Path("/tmp/semantic_layer_doc_cache")
CACHE_DIR.mkdir(exist_ok=True)


def _get_cache_filename(model_id: str, template: str) -> Path:
    """Generate cache filename based on model_id and template"""
    cache_key = f"{model_id}_{template}"
    return CACHE_DIR / f"{cache_key}.json"


def _save_to_file_cache(model_id: str, template: str, doc_data: Dict[str, Any]) -> None:
    """Save documentation to file cache"""
    try:
        cache_file = _get_cache_filename(model_id, template)
        with open(cache_file, 'w') as f:
            json.dump(doc_data, f, indent=2)
        logger.info(f"Saved documentation to cache: {cache_file}")
    except Exception as e:
        logger.error(f"Error saving to file cache: {str(e)}")


def _load_from_file_cache(model_id: str, template: str) -> Optional[Dict[str, Any]]:
    """Load documentation from file cache"""
    try:
        cache_file = _get_cache_filename(model_id, template)
        if cache_file.exists():
            with open(cache_file, 'r') as f:
                doc_data = json.load(f)
            logger.info(f"Loaded documentation from cache: {cache_file}")
            return doc_data
    except Exception as e:
        logger.error(f"Error loading from file cache: {str(e)}")
    return None


def get_model_from_file(model_id: str) -> Optional[Dict[str, Any]]:
    """Load a semantic model from file"""
    model_path = Path(f"semantic-models/{model_id}.yml")
    
    if not model_path.exists():
        # Try with .yaml extension
        model_path = Path(f"semantic-models/{model_id}.yaml")
        if not model_path.exists():
            return None
    
    try:
        with open(model_path, 'r') as f:
            return yaml.safe_load(f)
    except Exception as e:
        logger.error(f"Error loading model {model_id}: {str(e)}")
        return None


@router.post("/generate")
async def generate_documentation(
    request: DocumentationGenerationRequest,
    current_user: User = Depends(require_auth)
) -> Dict[str, Any]:
    """
    Generate documentation for a semantic model.
    
    Args:
        request: Documentation generation request
        current_user: Authenticated user
        model_manager: Model manager service
        
    Returns:
        Generated documentation or job status
    """
    try:
        # Get the model
        model = get_model_from_file(request.model_id)
        if not model:
            raise HTTPException(status_code=404, detail=f"Model not found: {request.model_id}")
        
        # Create documentation config
        config = request.options or DocumentationConfig(
            format=request.format,
            template=request.template
        )
        
        # Generate documentation
        generator = DocumentationGenerator()
        doc = generator.generate_documentation(model, config)
        
        return {
            "success": True,
            "documentation": {
                "format": doc.format.value,
                "content": doc.content if isinstance(doc.content, str) else None,
                "content_type": doc.content_type,
                "filename": doc.filename,
                "size_bytes": doc.size_bytes,
                "metadata": doc.metadata
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error generating documentation: {str(e)}")
        return {
            "success": False,
            "error": str(e)
        }


@router.post("/batch")
async def generate_batch_documentation(
    request: BatchDocumentationRequest,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(require_auth)
) -> Dict[str, Any]:
    """
    Generate documentation for multiple models (async).
    
    Args:
        request: Batch documentation request
        background_tasks: FastAPI background tasks
        current_user: Authenticated user
        model_manager: Model manager service
        
    Returns:
        Job ID for tracking progress
    """
    try:
        # Validate all models exist
        models = []
        for model_id in request.model_ids:
            model = get_model_from_file(model_id)
            if not model:
                raise HTTPException(
                    status_code=404,
                    detail=f"Model not found: {model_id}"
                )
            models.append(model)
        
        # Create job
        job_id = str(uuid4())
        job_status = DocumentationStatus(
            job_id=job_id,
            status="pending",
            progress=0.0,
            total_models=len(models)
        )
        documentation_jobs[job_id] = job_status
        
        # Start background task
        background_tasks.add_task(
            _process_batch_documentation,
            job_id,
            models,
            request
        )
        
        return {
            "success": True,
            "job_id": job_id,
            "message": f"Documentation generation started for {len(models)} models"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error starting batch documentation: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


async def _process_batch_documentation(
    job_id: str,
    models: List[Dict[str, Any]],
    request: BatchDocumentationRequest
):
    """Background task to process batch documentation"""
    job_status = documentation_jobs.get(job_id)
    if not job_status:
        return
    
    try:
        job_status.status = "processing"
        generator = DocumentationGenerator()
        
        # Create config
        config = request.options or DocumentationConfig(
            format=request.format,
            template=request.template
        )
        
        if request.combine:
            # Generate combined documentation
            doc = generator.generate_multi_model_documentation(models, config)
            
            # Store result (in production, save to storage)
            job_status.result_url = f"/api/v1/documentation/download/{job_id}"
        else:
            # Generate individual documentations
            for i, model in enumerate(models):
                doc = generator.generate_documentation(model, config)
                job_status.models_processed = i + 1
                job_status.progress = (i + 1) / len(models) * 100
        
        job_status.status = "completed"
        job_status.progress = 100.0
        job_status.completed_at = datetime.utcnow()
        
    except Exception as e:
        logger.error(f"Error in batch documentation: {str(e)}")
        job_status.status = "failed"
        job_status.errors = [str(e)]


@router.get("/status/{job_id}")
async def get_documentation_status(
    job_id: str,
    current_user: User = Depends(require_auth)
) -> DocumentationStatus:
    """
    Get status of documentation generation job.
    
    Args:
        job_id: Job ID
        current_user: Authenticated user
        
    Returns:
        DocumentationStatus object
    """
    job_status = documentation_jobs.get(job_id)
    if not job_status:
        raise HTTPException(status_code=404, detail="Job not found")
    
    return job_status


@router.get("/templates")
async def list_documentation_templates(
    current_user: User = Depends(require_auth)
) -> TemplateListResponse:
    """
    List available documentation templates.
    
    Args:
        current_user: Authenticated user
        
    Returns:
        List of available templates
    """
    from app.services.documentation_templates import TemplateManager
    
    template_manager = TemplateManager()
    templates = template_manager.get_available_templates()
    
    return TemplateListResponse(
        templates=list(templates.values()),
        custom_templates_enabled=True
    )


@router.get("/export")
async def export_documentation(
    model_id: str = Query(..., description="Model ID"),
    format: DocumentationFormat = Query(DocumentationFormat.PDF, description="Export format"),
    template: str = Query("standard", description="Template to use"),
    current_user: User = Depends(require_auth)
) -> Response:
    """
    Export documentation in specified format.
    
    Args:
        model_id: Model ID
        format: Export format
        template: Template name
        current_user: Authenticated user
        model_manager: Model manager service
        
    Returns:
        File response with documentation
    """
    try:
        # Get the model
        model = get_model_from_file(model_id)
        if not model:
            raise HTTPException(status_code=404, detail=f"Model not found: {model_id}")
        
        # Generate documentation
        config = DocumentationConfig(format=format, template=template)
        generator = DocumentationGenerator()
        doc = generator.generate_documentation(model, config)
        
        # Return appropriate response
        if isinstance(doc.content, bytes):
            return Response(
                content=doc.content,
                media_type=doc.content_type,
                headers={
                    "Content-Disposition": f"attachment; filename={doc.filename}"
                }
            )
        else:
            return Response(
                content=doc.content,
                media_type=doc.content_type,
                headers={
                    "Content-Disposition": f"attachment; filename={doc.filename}"
                }
            )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error exporting documentation: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/preview/{model_id}")
async def preview_documentation(
    model_id: str,
    template: str = Query("standard", description="Template to use"),
    current_user: User = Depends(require_auth)
) -> Dict[str, Any]:
    """
    Preview documentation in markdown format.
    
    Args:
        model_id: Model ID
        template: Template name
        current_user: Authenticated user
        model_manager: Model manager service
        
    Returns:
        Documentation preview
    """
    try:
        # Get the model
        model = get_model_from_file(model_id)
        if not model:
            raise HTTPException(status_code=404, detail=f"Model not found: {model_id}")
        
        # Generate markdown preview
        config = DocumentationConfig(
            format=DocumentationFormat.MARKDOWN,
            template=template,
            include_examples=True,
            include_lineage=True
        )
        
        generator = DocumentationGenerator()
        doc = generator.generate_documentation(model, config)
        
        return {
            "success": True,
            "preview": {
                "content": doc.content,
                "metadata": doc.metadata,
                "template": template
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error generating preview: {str(e)}")
        return {
            "success": False,
            "error": str(e)
        }


# Demo endpoints (no auth required)
@demo_router.post("/generate")
async def generate_documentation_demo(
    request: DocumentationGenerationRequest
) -> Dict[str, Any]:
    """Generate documentation for a semantic model (demo - no auth required)."""
    try:
        # Get the model
        model = get_model_from_file(request.model_id)
        if not model:
            raise HTTPException(status_code=404, detail=f"Model not found: {request.model_id}")
        
        # Create documentation config
        config = request.options or DocumentationConfig(
            format=request.format,
            template=request.template
        )
        
        # Generate documentation with LLM enabled for demo
        generator = DocumentationGenerator(use_llm=True)
        doc = generator.generate_documentation(model, config)
        
        # Store the generated documentation for preview
        doc_data = {
            "format": doc.format.value,
            "content": doc.content if isinstance(doc.content, str) else None,
            "content_type": doc.content_type,
            "filename": doc.filename,
            "size_bytes": doc.size_bytes,
            "metadata": doc.metadata,
            "template": config.template,
            "generated_at": datetime.utcnow().isoformat()
        }
        
        # Store in cache with model_id as key
        demo_documentation_cache[request.model_id] = doc_data
        
        # Also save to file cache for persistence
        _save_to_file_cache(request.model_id, config.template, doc_data)
        
        return {
            "success": True,
            "documentation": doc_data
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error generating documentation: {str(e)}")
        return {
            "success": False,
            "error": str(e)
        }


@demo_router.get("/preview/{model_id}")
async def preview_documentation_demo(
    model_id: str,
    template: str = Query("standard", description="Template to use"),
    quick: bool = Query(False, description="Generate quick preview without LLM")
) -> Dict[str, Any]:
    """Preview documentation in markdown format (demo - no auth required)."""
    try:
        # First check if we have cached documentation in memory
        if model_id in demo_documentation_cache:
            cached_doc = demo_documentation_cache[model_id]
            # Return the cached documentation
            return {
                "success": True,
                "format": cached_doc.get("format", "markdown"),
                "content": cached_doc.get("content", ""),
                "metadata": {
                    "generated_at": cached_doc.get("generated_at"),
                    "template_used": cached_doc.get("template", template),
                    "model_version": cached_doc.get("metadata", {}).get("model_version", "1.0.0"),
                    "model_name": cached_doc.get("metadata", {}).get("model_name")
                }
            }
        
        # Check file cache if not in memory
        cached_doc = _load_from_file_cache(model_id, template)
        if cached_doc:
            # Store in memory cache for faster access
            demo_documentation_cache[model_id] = cached_doc
            return {
                "success": True,
                "format": cached_doc.get("format", "markdown"),
                "content": cached_doc.get("content", ""),
                "metadata": {
                    "generated_at": cached_doc.get("generated_at"),
                    "template_used": cached_doc.get("template", template),
                    "model_version": cached_doc.get("metadata", {}).get("model_version", "1.0.0"),
                    "model_name": cached_doc.get("metadata", {}).get("model_name")
                }
            }
        
        # If no cached documentation, generate preview on the fly
        model = get_model_from_file(model_id)
        if not model:
            raise HTTPException(status_code=404, detail=f"Model not found: {model_id}")
        
        # Generate markdown preview with LLM enabled for demo (unless quick mode)
        config = DocumentationConfig(
            format=DocumentationFormat.MARKDOWN,
            template=template,
            include_examples=True,
            include_lineage=True
        )
        
        # Use LLM only if not requesting quick preview
        generator = DocumentationGenerator(use_llm=not quick)
        doc = generator.generate_documentation(model, config)
        
        # Store in cache for future use
        doc_data = {
            "format": doc.format.value,
            "content": doc.content if isinstance(doc.content, str) else None,
            "content_type": doc.content_type,
            "filename": doc.filename,
            "size_bytes": doc.size_bytes,
            "metadata": doc.metadata,
            "template": template,
            "generated_at": datetime.utcnow().isoformat()
        }
        demo_documentation_cache[model_id] = doc_data
        
        # Also save to file cache
        _save_to_file_cache(model_id, template, doc_data)
        
        return {
            "success": True,
            "format": doc.format.value,
            "content": doc.content,
            "metadata": {
                "generated_at": doc.metadata.get("generated_at"),
                "template_used": template,
                "model_version": doc.metadata.get("model_version", "1.0.0")
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error generating preview: {str(e)}")
        return {
            "success": False,
            "error": str(e)
        }

@demo_router.get("/recent")
async def get_recent_documentations_demo() -> Dict[str, Any]:
    """Get list of recently generated documentations (demo - no auth required)."""
    try:
        # Convert cache to list format with model info
        recent_docs = []
        for model_id, doc_data in demo_documentation_cache.items():
            recent_docs.append({
                "model_id": model_id,
                "model_name": doc_data.get("metadata", {}).get("model_name", model_id),
                "format": doc_data.get("format", "markdown"),
                "template": doc_data.get("template", "standard"),
                "generated_at": doc_data.get("generated_at"),
                "size_bytes": doc_data.get("size_bytes", 0)
            })
        
        # Sort by generated_at (most recent first)
        recent_docs.sort(key=lambda x: x.get("generated_at", ""), reverse=True)
        
        # Limit to last 10
        recent_docs = recent_docs[:10]
        
        return {
            "success": True,
            "documentations": recent_docs,
            "total": len(recent_docs)
        }
        
    except Exception as e:
        logger.error(f"Error getting recent documentations: {str(e)}")
        return {
            "success": False,
            "error": str(e),
            "documentations": []
        }


@demo_router.post("/export")
async def export_documentation_demo(
    request: Dict[str, Any]
) -> Response:
    """Export documentation to various formats (demo - no auth required)."""
    try:
        content = request.get('content', '')
        format = request.get('format', 'markdown')
        filename = request.get('filename', 'documentation')
        
        # Handle different formats
        if format == 'markdown':
            media_type = "text/markdown"
            file_content = content.encode('utf-8')
            extension = "md"
        elif format == 'html':
            media_type = "text/html"
            # Simple HTML wrapper
            html_content = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>{filename}</title>
    <style>
        body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; padding: 2rem; max-width: 1200px; margin: 0 auto; }}
        pre {{ background: #f5f5f5; padding: 1rem; overflow-x: auto; }}
        code {{ background: #f5f5f5; padding: 0.2rem 0.4rem; }}
    </style>
</head>
<body>
    {content}
</body>
</html>"""
            file_content = html_content.encode('utf-8')
            extension = "html"
        elif format == 'json':
            media_type = "application/json"
            file_content = content.encode('utf-8')
            extension = "json"
        else:
            # Default to text
            media_type = "text/plain"
            file_content = content.encode('utf-8')
            extension = "txt"
        
        return Response(
            content=file_content,
            media_type=media_type,
            headers={
                "Content-Disposition": f"attachment; filename={filename}.{extension}"
            }
        )
        
    except Exception as e:
        logger.error(f"Error exporting documentation: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
