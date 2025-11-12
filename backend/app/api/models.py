"""
Semantic models API endpoints
"""
from fastapi import APIRouter, HTTPException, UploadFile, File, Depends
from typing import List, Dict, Any, Optional
import structlog
import yaml
from pathlib import Path
from datetime import datetime

from app.models.semantic import (
    SemanticModel,
    SemanticModelCreate,
    AddMetricSQLRequest,
    EnhancedSemanticModel,
    CacheConfig,
    GovernanceMetadata
)
from app.services.semantic_parser import SemanticModelParser
from app.services.volume_metric_store import VolumeMetricStore
from app.auth import get_current_user, require_permission, Permission, User
from app.auth.permissions import check_volume_access, filter_metrics_by_access, get_accessible_categories
from app.core.config import settings

# Create separate router for demo endpoints without auth
demo_router = APIRouter()

router = APIRouter()
logger = structlog.get_logger()

# Global volume store instance
volume_store = VolumeMetricStore()


@demo_router.get("/")
async def list_demo_models() -> List[Dict[str, Any]]:
    """List semantic models from local filesystem for demo purposes (no auth required)."""
    try:
        models_path = Path(settings.semantic_models_path)
        models = []
        
        if models_path.exists():
            for yaml_file in models_path.glob("*.yml"):
                try:
                    with open(yaml_file, 'r') as f:
                        content = yaml.safe_load(f)
                    
                    # Extract basic info from YAML
                    if content and isinstance(content, dict):
                        # Handle both semantic_model wrapper and direct format
                        model_data = content.get('semantic_model', content)
                        if isinstance(model_data, dict):
                            models.append({
                                "id": yaml_file.stem,
                                "name": model_data.get("name", yaml_file.stem),
                                "description": model_data.get("description", ""),
                                "file_path": str(yaml_file),
                                "metrics": model_data.get("metrics", []),
                                "measures": model_data.get("measures", []),
                                "dimensions": model_data.get("dimensions", []),
                                "entities": model_data.get("entities", []),
                                "metadata": model_data.get("metadata", {})
                            })
                except Exception as e:
                    logger.warning(f"Failed to load demo model {yaml_file}", error=str(e))
        
        logger.info(f"Listed {len(models)} demo semantic models")
        return models
        
    except Exception as e:
        logger.error("Failed to list demo models", error=str(e))
        raise HTTPException(status_code=500, detail=f"Failed to list demo models: {str(e)}")


@demo_router.get("/{model_id}")
async def get_demo_model(model_id: str) -> Dict[str, Any]:
    """Get a specific semantic model from local filesystem for demo purposes (no auth required)."""
    try:
        models_path = Path(settings.semantic_models_path)
        model_file = models_path / f"{model_id}.yml"
        
        if not model_file.exists():
            raise HTTPException(status_code=404, detail=f"Demo model {model_id} not found")
        
        # Read the raw YAML content as string
        with open(model_file, 'r') as f:
            raw_yaml_content = f.read()
            
        # Also parse the YAML for structured access
        with open(model_file, 'r') as f:
            content = yaml.safe_load(f)
        
        # Handle both semantic_model wrapper and direct format
        model_data = content.get('semantic_model', content) if content else {}
        
        return {
            "id": model_id,
            "name": model_data.get("name", model_id),
            "description": model_data.get("description", ""),
            "file_path": str(model_file),
            "full_content": content,
            "model_data": model_data,
            "raw": content,  # Parsed content for frontend compatibility
            "raw_yaml": raw_yaml_content  # Raw YAML string for display
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get demo model {model_id}", error=str(e))
        raise HTTPException(status_code=500, detail=f"Failed to get demo model: {str(e)}")


@router.get("/", response_model=List[EnhancedSemanticModel])
async def list_models(
    category: str = "production_models",
    current_user: User = Depends(get_current_user)
) -> List[EnhancedSemanticModel]:
    """List semantic models from Unity Catalog Volumes with access control."""
    try:
        # Check if user can access this category
        volume_path = f"/Volumes/semantic_layer/metrics/{category}"
        if not check_volume_access(current_user, volume_path, "read"):
            raise HTTPException(
                status_code=403, 
                detail=f"Access denied to {category} category"
            )
        
        # Get metric names from volume
        metric_names = volume_store.list_metrics(category)
        models = []
        
        for metric_name in metric_names:
            try:
                enhanced_model = volume_store.get_metric(metric_name, category)
                if enhanced_model:
                    models.append(enhanced_model)
            except Exception as e:
                logger.warning(f"Failed to load model {metric_name}", error=str(e))
        
        # Filter by access permissions
        accessible_models = []
        for model in models:
            governance = model.governance or GovernanceMetadata()
            from app.auth.permissions import check_metric_access
            if check_metric_access(current_user, model.name, "read", governance.access_level):
                accessible_models.append(model)
        
        logger.info(
            "Listed semantic models", 
            category=category, 
            total=len(models),
            accessible=len(accessible_models),
            user=current_user.email
        )
        return accessible_models
        
    except Exception as e:
        logger.error("Failed to list models", error=str(e))
        raise HTTPException(status_code=500, detail=f"Failed to list models: {str(e)}")


@router.get("/{model_id}")
async def get_model(
    model_id: str,
    category: str = "production_models",
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """Get a specific semantic model from volume with access control."""
    try:
        # Check volume access
        volume_path = f"/Volumes/semantic_layer/metrics/{category}"
        if not check_volume_access(current_user, volume_path, "read"):
            raise HTTPException(
                status_code=403,
                detail=f"Access denied to {category} category"
            )
        
        # Load model from volume
        enhanced_model = volume_store.get_metric(model_id, category)
        if not enhanced_model:
            raise HTTPException(status_code=404, detail=f"Model {model_id} not found")
        
        # Check metric-level access
        governance = enhanced_model.governance or GovernanceMetadata()
        from app.auth.permissions import check_metric_access
        if not check_metric_access(current_user, model_id, "read", governance.access_level):
            raise HTTPException(
                status_code=403,
                detail=f"Access denied to metric {model_id}"
            )
        
        # Try to parse with SemanticModelParser for backward compatibility
        parsed_model = None
        try:
            parser = SemanticModelParser()
            model_dict = enhanced_model.model_dump()
            parsed_model = parser.parse({"semantic_model": model_dict})
        except Exception as parse_error:
            logger.warning(f"Failed to parse model {model_id} with SemanticModelParser", error=str(parse_error))
        
        return {
            "id": model_id,
            "category": category,
            "enhanced_model": enhanced_model,
            "parsed": parsed_model,
            "cache_stats": {
                "usage_count": enhanced_model.usage_count,
                "last_accessed": enhanced_model.last_accessed
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get model {model_id}", error=str(e))
        raise HTTPException(status_code=500, detail=f"Failed to get model: {str(e)}")


@router.post("/")
@require_permission(Permission.METRIC_CREATE)
async def create_model(
    model: SemanticModelCreate,
    category: str = "staging_models",
    cache_config: Optional[CacheConfig] = None,
    governance: Optional[GovernanceMetadata] = None,
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """Create a new semantic model in Unity Catalog Volume."""
    try:
        # Check volume write access
        volume_path = f"/Volumes/semantic_layer/metrics/{category}"
        if not check_volume_access(current_user, volume_path, "write"):
            raise HTTPException(
                status_code=403,
                detail=f"Access denied to write to {category} category"
            )
        
        # Check if model already exists
        if volume_store.get_metric(model.name, category):
            raise HTTPException(status_code=409, detail=f"Model {model.name} already exists")
        
        # Create enhanced semantic model
        enhanced_model = EnhancedSemanticModel(
            id=model.name,
            name=model.name,
            description=model.description,
            file_path=f"/Volumes/semantic_layer/metrics/{category}/{model.name}.yml",
            version="1.0.0",
            owner=current_user.email,
            cache_config=cache_config,
            governance=governance or GovernanceMetadata(
                access_level="internal",
                approval_required=category == "production_models"
            ),
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        
        # Add the semantic model structure
        enhanced_model.model = model.model
        enhanced_model.entities = model.entities
        enhanced_model.dimensions = model.dimensions
        enhanced_model.measures = model.measures
        enhanced_model.metrics = model.metrics
        
        # Save to volume
        success = volume_store.save_metric(enhanced_model, category)
        if not success:
            raise HTTPException(status_code=500, detail="Failed to save model to volume")
        
        logger.info(
            f"Created semantic model {model.name}",
            category=category,
            user=current_user.email
        )
        
        return {
            "id": model.name,
            "name": model.name,
            "category": category,
            "volume_path": enhanced_model.file_path,
            "message": "Model created successfully"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to create model", error=str(e))
        raise HTTPException(status_code=500, detail=f"Failed to create model: {str(e)}")


@router.post("/metrics/sql")
async def add_sql_metric(req: AddMetricSQLRequest) -> Dict[str, Any]:
    """Append or upsert a SQL-defined metric into a semantic model YAML file.

    If the model YAML does not exist, it will be created minimalistically.
    If the metric name exists, it will be updated in-place.
    """
    try:
        models_path = Path(settings.semantic_models_path)
        models_path.mkdir(parents=True, exist_ok=True)

        filename = f"{req.model_name.lower().replace(' ', '_')}.yml"
        file_path = models_path / filename

        content: Dict[str, Any] = {"semantic_model": {}}
        if file_path.exists():
            with open(file_path, 'r') as f:
                content = yaml.safe_load(f) or content

        sm = content.setdefault("semantic_model", {})
        sm.setdefault("name", req.model_name)
        if req.model_description:
            sm.setdefault("description", req.model_description)
        metrics = sm.setdefault("metrics", [])

        # Represent the metric in YAML as sql-based metric block
        metric_block = {
            "name": req.metric.name,
            "description": req.metric.description or "",
            "natural_language": req.metric.natural_language or "",
            "sql": req.metric.sql,
        }
        if req.metric.tags:
            metric_block["tags"] = req.metric.tags

        # Upsert by metric name
        updated = False
        for i, m in enumerate(metrics):
            if isinstance(m, dict) and m.get("name") == req.metric.name:
                metrics[i] = metric_block
                updated = True
                break
        if not updated:
            metrics.append(metric_block)

        with open(file_path, 'w') as f:
            yaml.dump(content, f, default_flow_style=False, sort_keys=False)

        logger.info("SQL metric saved", model=req.model_name, metric=req.metric.name)
        return {
            "model": req.model_name,
            "metric": req.metric.name,
            "file_path": str(file_path),
            "updated": updated,
            "message": "Metric updated" if updated else "Metric added",
        }
    except Exception as e:
        logger.error("Failed to save SQL metric", error=str(e))
        raise HTTPException(status_code=500, detail=f"Failed to save SQL metric: {str(e)}")


@router.put("/{model_id}")
async def update_model(model_id: str, model: SemanticModelCreate) -> Dict[str, Any]:
    """Update an existing semantic model"""
    try:
        model_path = Path(settings.semantic_models_path) / f"{model_id}.yml"
        
        if not model_path.exists():
            raise HTTPException(status_code=404, detail=f"Model {model_id} not found")
        
        # Create the updated YAML structure
        model_data = {
            "semantic_model": {
                "name": model.name,
                "description": model.description,
                "model": model.model,
                "entities": model.entities,
                "dimensions": model.dimensions,
                "measures": model.measures,
                "metrics": model.metrics
            }
        }
        
        # Save to file
        with open(model_path, 'w') as f:
            yaml.dump(model_data, f, default_flow_style=False, sort_keys=False)
        
        logger.info(f"Updated semantic model {model_id}")
        
        return {
            "id": model_id,
            "name": model.name,
            "message": "Model updated successfully"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to update model {model_id}", error=str(e))
        raise HTTPException(status_code=500, detail=f"Failed to update model: {str(e)}")


@router.delete("/{model_id}")
async def delete_model(model_id: str) -> Dict[str, Any]:
    """Delete a semantic model"""
    try:
        model_path = Path(settings.semantic_models_path) / f"{model_id}.yml"
        
        if not model_path.exists():
            raise HTTPException(status_code=404, detail=f"Model {model_id} not found")
        
        model_path.unlink()
        logger.info(f"Deleted semantic model {model_id}")
        
        return {
            "id": model_id,
            "message": "Model deleted successfully"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete model {model_id}", error=str(e))
        raise HTTPException(status_code=500, detail=f"Failed to delete model: {str(e)}")


@router.post("/upload")
async def upload_model(file: UploadFile = File(...)) -> Dict[str, Any]:
    """Upload a YAML semantic model file"""
    try:
        if not file.filename.endswith(('.yml', '.yaml')):
            raise HTTPException(status_code=400, detail="File must be a YAML file")
        
        # Read and validate the content
        content = await file.read()
        model_data = yaml.safe_load(content)
        
        # Parse to validate structure
        parser = SemanticModelParser()
        parser.parse(model_data)
        
        # Save the file
        models_path = Path(settings.semantic_models_path)
        models_path.mkdir(parents=True, exist_ok=True)
        
        file_path = models_path / file.filename
        with open(file_path, 'wb') as f:
            f.write(content)
        
        logger.info(f"Uploaded semantic model {file.filename}")
        
        return {
            "filename": file.filename,
            "message": "Model uploaded successfully"
        }
        
    except yaml.YAMLError as e:
        raise HTTPException(status_code=400, detail=f"Invalid YAML: {str(e)}")
    except Exception as e:
        logger.error("Failed to upload model", error=str(e))
        raise HTTPException(status_code=500, detail=f"Failed to upload model: {str(e)}")
