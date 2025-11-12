"""
Main FastAPI application for Semantic Layer Service with enhanced features:
- Unity Catalog Volumes integration
- Role-based authentication
- Performance monitoring
- Caching capabilities
"""
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
import structlog
import time

from app.api import health, metadata, queries, models, genie, auth, advanced_features, metrics_explorer, catalog
from app.api.documentation import router as documentation_router, demo_router as documentation_demo_router
from app.api.lineage import router as lineage_router
from app.core.config import settings
from app.core.logging import setup_logging
from app.services.volume_metric_store import VolumeMetricStore

# Setup structured logging
setup_logging()
logger = structlog.get_logger()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Handle application startup and shutdown with enhanced initialization."""
    logger.info("Starting Enhanced Semantic Layer Service", version="0.2.0")
    
    # Initialize volume store and cache
    try:
        volume_store = VolumeMetricStore()
        app.state.volume_store = volume_store
        logger.info("Volume store initialized successfully")
    except Exception as e:
        logger.warning(f"Volume store initialization failed: {e}")
        app.state.volume_store = None
    
    yield
    
    # Cleanup on shutdown
    logger.info("Shutting down Enhanced Semantic Layer Service")


# Create FastAPI app
app = FastAPI(
    title="Enhanced Semantic Layer Service",
    description="""
    Enterprise-grade semantic layer API with:
    - Unity Catalog Volumes integration for scalable metric storage
    - Role-based authentication and access control
    - Intelligent caching and pre-aggregation
    - Real-time monitoring and alerting
    - Natural language query generation via Databricks Genie
    """,
    version="0.2.0",
    lifespan=lifespan
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:3001"],  # Frontend URLs
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Request timing middleware for performance monitoring
@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    """Add processing time header and log request metrics."""
    start_time = time.time()
    
    # Process request
    response = await call_next(request)
    
    # Calculate processing time
    process_time = time.time() - start_time
    process_time_ms = int(process_time * 1000)
    
    # Add header
    response.headers["X-Process-Time"] = str(process_time_ms)
    
    # Log request for monitoring (exclude health checks to reduce noise)
    if not request.url.path.startswith("/api/health"):
        logger.info(
            "Request processed",
            method=request.method,
            path=request.url.path,
            status_code=response.status_code,
            process_time_ms=process_time_ms,
            user_agent=request.headers.get("user-agent", "unknown")
        )
    
    return response


# Global exception handler
@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """Handle HTTP exceptions with structured logging."""
    logger.error(
        "HTTP Exception",
        method=request.method,
        path=request.url.path,
        status_code=exc.status_code,
        detail=exc.detail
    )
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail}
    )

# Include routers
# IMPORTANT: Include demo routers FIRST to avoid auth middleware conflicts
app.include_router(models.demo_router, prefix="/api/models/demo", tags=["demo-models"])
app.include_router(advanced_features.demo_router, prefix="/api/advanced/demo", tags=["advanced-demo"])
app.include_router(documentation_demo_router, prefix="/api/documentation/demo", tags=["demo-documentation"])

# Then include authenticated routers
app.include_router(auth.router, prefix="/api/auth", tags=["authentication"])
app.include_router(health.router, prefix="/api/health", tags=["health"])
app.include_router(metadata.router, prefix="/api/metadata", tags=["metadata"])
app.include_router(queries.router, prefix="/api/queries", tags=["queries"])
app.include_router(models.router, prefix="/api/models", tags=["models"])
app.include_router(genie.router, prefix="/api/genie", tags=["genie"])
app.include_router(advanced_features.router, prefix="/api/advanced", tags=["advanced"])
app.include_router(metrics_explorer.router, prefix="/api/metrics-explorer", tags=["metrics-explorer"])
app.include_router(catalog.router, prefix="/api/catalog", tags=["catalog"])
app.include_router(documentation_router, tags=["documentation"])
app.include_router(lineage_router, tags=["lineage"])


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "name": "Semantic Layer Service",
        "version": "0.1.0",
        "docs": "/docs",
        "health": "/api/health"
    }

# Direct demo endpoints - no auth
@app.get("/api/models-demo")
async def get_demo_models():
    """Get demo models without authentication"""
    from pathlib import Path
    import yaml
    from datetime import datetime
    
    models_path = Path("semantic-models")
    models = []
    
    if models_path.exists():
        for yaml_file in models_path.glob("*.yml"):
            try:
                with open(yaml_file, 'r') as f:
                    content = yaml.safe_load(f)
                
                if content and isinstance(content, dict):
                    # Handle both semantic_model wrapper and direct format
                    model_data = content.get('semantic_model', content)
                    if isinstance(model_data, dict):
                        model_name = model_data.get('name', yaml_file.stem)
                        
                        # Count metrics, dimensions, and entities
                        metrics_count = len(model_data.get('metrics', []))
                        dimensions_count = len(model_data.get('dimensions', []))
                        entities_count = len(model_data.get('entities', []))
                        measures_count = len(model_data.get('measures', []))
                        
                        # Get file timestamps
                        stat = yaml_file.stat()
                        created_at = datetime.fromtimestamp(stat.st_ctime).isoformat()
                        updated_at = datetime.fromtimestamp(stat.st_mtime).isoformat()
                        
                        models.append({
                            "id": yaml_file.stem,
                            "name": model_name,
                            "description": model_data.get('description', f'Semantic model for {model_name}'),
                            "version": "1.0.0",  # Default version
                            "created_at": created_at,
                            "updated_at": updated_at,
                            "metrics_count": metrics_count,
                            "dimensions_count": dimensions_count,
                            "entities_count": entities_count,
                            "measures_count": measures_count,
                            "file_path": str(yaml_file)
                        })
            except Exception as e:
                logger.error(f"Error reading {yaml_file}: {e}")
    
    return models

@app.get("/api/models-demo/{model_id}")
async def get_demo_model(model_id: str):
    """Get a specific demo model without authentication"""
    from pathlib import Path
    import yaml
    
    model_path = Path(f"semantic-models/{model_id}.yml")
    
    if not model_path.exists():
        raise HTTPException(status_code=404, detail=f"Model {model_id} not found")
    
    try:
        with open(model_path, 'r') as f:
            content = yaml.safe_load(f)
            
        # Also read raw YAML for display
        with open(model_path, 'r') as f:
            raw_yaml = f.read()
        
        if content and isinstance(content, dict):
            return {
                "id": model_id,
                "name": content.get('name', model_id),
                "description": content.get('description', f'Semantic model for {model_id}'),
                "metrics": content.get('metrics', []),
                "dimensions": content.get('dimensions', []),
                "measures": content.get('measures', []),
                "entities": content.get('entities', []),
                "raw_yaml": raw_yaml,
                "last_modified": model_path.stat().st_mtime
            }
    except Exception as e:
        logger.error(f"Error reading {model_path}: {e}")
        raise HTTPException(status_code=500, detail=f"Error reading model: {str(e)}")

@app.get("/api/models-demo/{model_id}/download")
async def download_demo_model(model_id: str):
    """Download a semantic model as YAML file"""
    from pathlib import Path
    from fastapi.responses import FileResponse
    
    model_path = Path(f"semantic-models/{model_id}.yml")
    
    if not model_path.exists():
        raise HTTPException(status_code=404, detail=f"Model {model_id} not found")
    
    return FileResponse(
        path=str(model_path),
        filename=f"{model_id}.yml",
        media_type="application/x-yaml"
    )

@app.put("/api/models-demo/{model_id}")
async def update_demo_model(model_id: str, yaml_content: dict):
    """Update a semantic model with new YAML content"""
    from pathlib import Path
    import yaml
    from datetime import datetime
    
    model_path = Path(f"semantic-models/{model_id}.yml")
    
    try:
        # Validate YAML content
        raw_yaml = yaml_content.get('raw_yaml', '')
        if not raw_yaml:
            raise HTTPException(status_code=400, detail="No YAML content provided")
        
        # Parse YAML to validate syntax
        try:
            parsed_content = yaml.safe_load(raw_yaml)
            if not isinstance(parsed_content, dict):
                raise HTTPException(status_code=400, detail="Invalid YAML structure")
        except yaml.YAMLError as e:
            raise HTTPException(status_code=400, detail=f"Invalid YAML syntax: {str(e)}")
        
        # Create backup if file exists
        if model_path.exists():
            backup_path = Path(f"semantic-models/backups/{model_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.yml")
            backup_path.parent.mkdir(exist_ok=True)
            with open(model_path, 'r') as src, open(backup_path, 'w') as dst:
                dst.write(src.read())
        
        # Save the updated YAML
        with open(model_path, 'w') as f:
            f.write(raw_yaml)
        
        logger.info(f"Updated semantic model {model_id}", file_path=str(model_path))
        
        return {
            "success": True,
            "message": f"Model {model_id} updated successfully",
            "last_modified": model_path.stat().st_mtime
        }
        
    except Exception as e:
        logger.error(f"Error updating {model_path}: {e}")
        raise HTTPException(status_code=500, detail=f"Error updating model: {str(e)}")
