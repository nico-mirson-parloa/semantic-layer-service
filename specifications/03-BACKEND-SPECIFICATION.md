# Backend Specification - Semantic Layer Service

**Document Version:** 1.0
**Last Updated:** 2025-11-04

---

## Table of Contents

1. [Architecture Overview](#1-architecture-overview)
2. [Directory Structure](#2-directory-structure)
3. [Core Application](#3-core-application)
4. [API Endpoints](#4-api-endpoints)
5. [Data Models](#5-data-models)
6. [Business Services](#6-business-services)
7. [Databricks Integrations](#7-databricks-integrations)
8. [Authentication & Authorization](#8-authentication--authorization)
9. [SQL API Server](#9-sql-api-server)
10. [Dependencies](#10-dependencies)
11. [Configuration](#11-configuration)
12. [Error Handling](#12-error-handling)

---

## 1. Architecture Overview

### Layered Architecture

```
┌──────────────────────────────────────────────────────┐
│              API Layer (FastAPI Routes)              │
│  - Health, Auth, Metadata, Queries, Models, etc.    │
└───────────────────┬──────────────────────────────────┘
                    │
┌───────────────────┴──────────────────────────────────┐
│             Business Logic Layer                     │
│  - Semantic Parser, Model Generator, Analyzers      │
└───────────────────┬──────────────────────────────────┘
                    │
┌───────────────────┴──────────────────────────────────┐
│           Integration Layer                          │
│  - Databricks Connector, Genie Client, Volume Store │
└───────────────────┬──────────────────────────────────┘
                    │
┌───────────────────┴──────────────────────────────────┐
│            External Systems                          │
│  - Databricks SQL Warehouse, Unity Catalog, Genie   │
└──────────────────────────────────────────────────────┘
```

### Design Principles

1. **Separation of Concerns:** API → Services → Integrations
2. **Dependency Injection:** Use FastAPI's dependency system
3. **Type Safety:** Pydantic models for all data validation
4. **Async First:** Leverage FastAPI's async capabilities
5. **Singleton Pattern:** Single Databricks connector instance
6. **Caching:** In-memory caching with TTL for performance

---

## 2. Directory Structure

```
backend/
├── app/
│   ├── __init__.py
│   ├── main.py                          # Application entry point
│   │
│   ├── api/                             # API route handlers (15 files)
│   │   ├── __init__.py
│   │   ├── health.py                    # Health check endpoints
│   │   ├── auth.py                      # Authentication
│   │   ├── metadata.py                  # Metadata discovery
│   │   ├── queries.py                   # Query execution
│   │   ├── models.py                    # Semantic model CRUD
│   │   ├── genie.py                     # Genie NL to SQL
│   │   ├── catalog.py                   # Unity Catalog browsing
│   │   ├── documentation.py             # Documentation generation
│   │   ├── lineage.py                   # Data lineage
│   │   ├── advanced_features.py         # Advanced analytics
│   │   ├── metrics_explorer.py          # Metrics exploration
│   │   └── documentation_additions.py   # Additional doc endpoints
│   │
│   ├── auth/                            # Authentication (3 files)
│   │   ├── __init__.py
│   │   ├── auth_models.py               # User, Role, Permission models
│   │   ├── databricks_auth.py           # OAuth & JWT logic
│   │   └── permissions.py               # Access control utilities
│   │
│   ├── core/                            # Core configuration (3 files)
│   │   ├── __init__.py
│   │   ├── config.py                    # Settings (Pydantic BaseSettings)
│   │   └── logging.py                   # Structured logging setup
│   │
│   ├── models/                          # Pydantic models (8 files)
│   │   ├── __init__.py
│   │   ├── metadata.py                  # Table, Column schemas
│   │   ├── queries.py                   # Query request/response
│   │   ├── semantic.py                  # Semantic model definitions
│   │   ├── semantic_model.py            # Model creation schemas
│   │   ├── genie.py                     # Genie API models
│   │   ├── catalog.py                   # Catalog models
│   │   ├── lineage.py                   # Lineage graph models
│   │   └── documentation.py             # Documentation models
│   │
│   ├── services/                        # Business logic (19 files)
│   │   ├── __init__.py
│   │   ├── semantic_parser.py           # YAML parsing
│   │   ├── sql_intent.py                # Rule-based SQL generation
│   │   ├── volume_metric_store.py       # Volume storage manager
│   │   ├── semantic_model_generator.py  # Auto model generation
│   │   ├── model_generator.py           # Generation engine
│   │   ├── metric_suggester.py          # Metric suggestions
│   │   ├── table_analyzer.py            # Table structure analysis
│   │   ├── llm_table_analyzer.py        # LLM-based analysis
│   │   ├── metadata_extractor.py        # Metadata extraction
│   │   ├── data_quality_service.py      # Quality assessment
│   │   ├── data_lineage_service.py      # Lineage tracking
│   │   ├── lineage_extractor.py         # SQL lineage extraction
│   │   ├── lineage_processor.py         # Lineage processing
│   │   ├── lineage_visualizer.py        # Visualization generation
│   │   ├── documentation_generator.py   # Doc generation
│   │   ├── documentation_templates.py   # Doc templates
│   │   └── metric_suggestion_service.py # Comprehensive suggestions
│   │
│   ├── integrations/                    # External integrations (4 files)
│   │   ├── __init__.py
│   │   ├── databricks.py                # SQL connector
│   │   ├── databricks_genie.py          # Genie API client
│   │   ├── databricks_genie_simple.py   # Simplified Genie client
│   │   └── databricks_sql_statements.py # Statements API
│   │
│   ├── connectors/                      # BI tool connectors
│   │   ├── preset/                      # Preset integration
│   │   │   ├── __init__.py
│   │   │   ├── connector.py
│   │   │   ├── metric_sync.py
│   │   │   ├── dashboard_builder.py
│   │   │   └── setup_preset.py
│   │   ├── excel/                       # Excel export
│   │   ├── powerbi/                     # Power BI
│   │   └── tableau/                     # Tableau
│   │
│   ├── sql_api/                         # PostgreSQL protocol (4 files)
│   │   ├── __init__.py
│   │   ├── server.py                    # SQL server
│   │   ├── protocol.py                  # PostgreSQL wire protocol
│   │   ├── virtual_schema.py            # Virtual schema manager
│   │   └── query_translator.py          # SQL translation
│   │
│   └── utils/                           # Utilities (1 file)
│       ├── __init__.py
│       └── sql_formatter.py             # SQL formatting
│
├── tests/                               # Test suite
│   ├── __init__.py
│   ├── conftest.py                      # Pytest configuration
│   ├── fixtures/
│   │   └── sample_data.py
│   ├── unit/
│   │   ├── test_semantic_parser.py
│   │   ├── test_databricks_integration.py
│   │   ├── test_models.py
│   │   ├── test_automatic_model_generation.py
│   │   ├── test_documentation_generation.py
│   │   └── test_lineage_visualization.py
│   └── integration/
│       └── test_api_endpoints.py
│
├── semantic-models/                     # YAML model storage
│   └── backups/
│
├── databricks_dashboards/               # Dashboard configs
├── databricks_jobs/                     # Scheduled jobs
│   ├── cache_refresh_job.py
│   └── system_monitoring_job.py
│
├── requirements.txt                     # Python dependencies
├── pytest.ini                           # Test configuration
├── Dockerfile                           # Container definition
└── start_sql_server.py                  # SQL API entry point
```

---

## 3. Core Application

### 3.1 Main Application (`app/main.py`)

**Purpose:** FastAPI application initialization and configuration

**Key Components:**

```python
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import structlog

# Import routers
from app.api import (
    health, auth, metadata, queries, models,
    genie, catalog, documentation, lineage,
    advanced_features, metrics_explorer
)

# Lifespan management
@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Startup: Initialize volume store and cache
    Shutdown: Cleanup resources
    """
    logger.info("Starting Semantic Layer Service")

    # Initialize volume metric store
    from app.services.volume_metric_store import VolumeMetricStore
    volume_store = VolumeMetricStore()
    app.state.volume_store = volume_store

    yield

    logger.info("Shutting down Semantic Layer Service")

# Create FastAPI app
app = FastAPI(
    title="Semantic Layer API",
    description="Unified semantic layer for Databricks",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://localhost:3001",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Request timing middleware
@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time
    response.headers["X-Process-Time"] = str(process_time)
    return response

# Exception handlers
@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail}
    )

# Include routers
app.include_router(health.router, prefix="/api/health", tags=["Health"])
app.include_router(auth.router, prefix="/api/auth", tags=["Authentication"])
app.include_router(metadata.router, prefix="/api/metadata", tags=["Metadata"])
app.include_router(queries.router, prefix="/api/queries", tags=["Queries"])
app.include_router(models.router, prefix="/api/models", tags=["Models"])
app.include_router(genie.router, prefix="/api/genie", tags=["Genie"])
app.include_router(catalog.router, prefix="/api/catalog", tags=["Catalog"])
app.include_router(documentation.router, prefix="/api/documentation", tags=["Documentation"])
app.include_router(lineage.router, prefix="/api/lineage", tags=["Lineage"])
app.include_router(advanced_features.router, prefix="/api/advanced", tags=["Advanced"])
app.include_router(metrics_explorer.router, prefix="/api/metrics-explorer", tags=["Metrics"])

# Root endpoint
@app.get("/")
async def root():
    return {
        "service": "Semantic Layer API",
        "version": "1.0.0",
        "status": "running"
    }
```

**Configuration:**
- Async lifespan management for resource initialization
- CORS enabled for frontend origins
- Request timing middleware for performance monitoring
- Centralized exception handling
- Automatic OpenAPI documentation at `/docs`

---

### 3.2 Configuration (`app/core/config.py`)

**Purpose:** Environment-based settings management

```python
from pydantic_settings import BaseSettings
from typing import Optional

class Settings(BaseSettings):
    """Application settings loaded from environment variables"""

    # Databricks Configuration
    databricks_host: Optional[str] = None
    databricks_token: Optional[str] = None
    databricks_http_path: Optional[str] = None
    databricks_warehouse_id: Optional[str] = None
    databricks_genie_space_id: Optional[str] = None
    databricks_foundation_model_endpoint: str = "databricks-meta-llama-3-1-70b-instruct"

    # Application Settings
    debug: bool = False
    semantic_models_path: str = "./semantic-models"
    volume_base_path: str = "/Volumes/semantic_layer/metrics"

    # Feature Flags
    enable_llm_analysis: bool = True
    llm_analysis_timeout: int = 30

    # Authentication
    secret_key: str = "your-secret-key-change-in-production"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30

    # Caching
    cache_ttl_minutes: int = 30
    metadata_cache_ttl_minutes: int = 5

    # External Integrations
    slack_webhook_url: Optional[str] = None

    class Config:
        env_file = ".env"
        case_sensitive = False

# Singleton instance
settings = Settings()
```

**Usage:**
```python
from app.core.config import settings

# Access settings anywhere
databricks_host = settings.databricks_host
```

---

### 3.3 Logging (`app/core/logging.py`)

**Purpose:** Structured logging configuration

```python
import structlog
import logging

def setup_logging():
    """Configure structured logging with structlog"""

    logging.basicConfig(
        format="%(message)s",
        level=logging.INFO,
    )

    structlog.configure(
        processors=[
            structlog.stdlib.filter_by_level,
            structlog.stdlib.add_logger_name,
            structlog.stdlib.add_log_level,
            structlog.stdlib.PositionalArgumentsFormatter(),
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.processors.UnicodeDecoder(),
            structlog.processors.JSONRenderer()
        ],
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True,
    )

# Call at module import
setup_logging()
logger = structlog.get_logger()
```

**Usage:**
```python
from app.core.logging import logger

logger.info("Query executed", query_id=123, duration_ms=456)
logger.error("Connection failed", error=str(e), retry_count=3)
```

---

## 4. API Endpoints

### 4.1 Health Check API (`app/api/health.py`)

**Purpose:** Service health monitoring

```python
from fastapi import APIRouter, HTTPException
from app.integrations.databricks import get_databricks_connector

router = APIRouter()

@router.get("/")
async def health_check():
    """Basic health check"""
    return {"status": "healthy", "service": "semantic-layer-api"}

@router.get("/databricks")
async def databricks_health():
    """Check Databricks connectivity"""
    try:
        connector = get_databricks_connector()
        result = connector.execute_query("SELECT 1 as health_check")
        return {
            "status": "healthy",
            "databricks_connection": "OK",
            "response": result
        }
    except Exception as e:
        raise HTTPException(
            status_code=503,
            detail=f"Databricks connection failed: {str(e)}"
        )

@router.get("/ready")
async def readiness_check():
    """Readiness probe for all dependencies"""
    checks = {
        "api": "healthy",
        "databricks": "unknown",
        "volume_store": "unknown"
    }

    # Check Databricks
    try:
        connector = get_databricks_connector()
        connector.execute_query("SELECT 1")
        checks["databricks"] = "healthy"
    except:
        checks["databricks"] = "unhealthy"

    # Check Volume Store
    try:
        from app.services.volume_metric_store import VolumeMetricStore
        store = VolumeMetricStore()
        store.list_metrics(category="production")
        checks["volume_store"] = "healthy"
    except:
        checks["volume_store"] = "unhealthy"

    all_healthy = all(v == "healthy" for v in checks.values())
    status_code = 200 if all_healthy else 503

    return JSONResponse(status_code=status_code, content=checks)
```

**Endpoints:**
- `GET /api/health/` - Basic health check
- `GET /api/health/databricks` - Databricks connectivity test
- `GET /api/health/ready` - Comprehensive readiness probe

---

### 4.2 Authentication API (`app/api/auth.py`)

**Purpose:** User authentication and token management

```python
from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from app.auth.databricks_auth import DatabricksAuth
from app.auth.auth_models import User, LoginRequest, TokenResponse

router = APIRouter()
security = HTTPBearer()
auth_service = DatabricksAuth()

@router.post("/login", response_model=TokenResponse)
async def login(request: LoginRequest):
    """
    Authenticate with Databricks token and return JWT

    Request:
        - databricks_token: Databricks Personal Access Token

    Response:
        - access_token: JWT for subsequent requests
        - token_type: "bearer"
        - expires_in: Token expiration in seconds
        - user: User information
    """
    try:
        # Verify Databricks token and get user info
        user = await auth_service.authenticate_user(request.databricks_token)

        # Generate JWT
        access_token = auth_service.create_access_token(user)

        return {
            "access_token": access_token,
            "token_type": "bearer",
            "expires_in": 1800,  # 30 minutes
            "user": user
        }
    except Exception as e:
        raise HTTPException(
            status_code=401,
            detail=f"Authentication failed: {str(e)}"
        )

@router.get("/me", response_model=User)
async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Get current user information from JWT token"""
    try:
        token = credentials.credentials
        user = await auth_service.verify_token(token)
        return user
    except Exception as e:
        raise HTTPException(
            status_code=401,
            detail="Invalid or expired token"
        )

@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Refresh JWT token"""
    try:
        # Verify current token
        user = await auth_service.verify_token(credentials.credentials)

        # Generate new token
        access_token = auth_service.create_access_token(user)

        return {
            "access_token": access_token,
            "token_type": "bearer",
            "expires_in": 1800
        }
    except Exception as e:
        raise HTTPException(
            status_code=401,
            detail="Token refresh failed"
        )

@router.get("/permissions")
async def get_permissions(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Get detailed permission information for current user"""
    user = await auth_service.verify_token(credentials.credentials)
    return {
        "user_id": user.id,
        "roles": user.roles,
        "permissions": user.permissions,
        "groups": user.groups
    }
```

**Endpoints:**
- `POST /api/auth/login` - Exchange Databricks token for JWT
- `GET /api/auth/me` - Get current user info
- `POST /api/auth/refresh` - Refresh JWT
- `GET /api/auth/permissions` - Get user permissions

---

### 4.3 Metadata Discovery API (`app/api/metadata.py`)

**Purpose:** Unity Catalog metadata discovery

```python
from fastapi import APIRouter, Query, HTTPException
from typing import List, Optional
from app.integrations.databricks import get_databricks_connector
from app.models.metadata import Table, Column, Catalog, Schema

router = APIRouter()

@router.get("/catalogs", response_model=List[Catalog])
async def list_catalogs():
    """List all available catalogs in Unity Catalog"""
    try:
        connector = get_databricks_connector()
        result = connector.execute_query("SHOW CATALOGS")

        catalogs = [
            Catalog(name=row["catalog"], comment=row.get("comment"))
            for row in result
        ]
        return catalogs
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/schemas", response_model=List[Schema])
async def list_schemas(catalog: str = Query(..., description="Catalog name")):
    """List schemas in a specific catalog"""
    try:
        connector = get_databricks_connector()
        result = connector.execute_query(f"SHOW SCHEMAS IN {catalog}")

        schemas = [
            Schema(name=row["databaseName"], catalog=catalog)
            for row in result
        ]
        return schemas
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/tables", response_model=List[Table])
async def list_tables(
    catalog: str = Query(...),
    schema: str = Query(...),
    filter_prefix: Optional[str] = Query(None, description="Filter by table name prefix")
):
    """List tables in a schema with optional filtering"""
    try:
        connector = get_databricks_connector()
        result = connector.execute_query(
            f"SHOW TABLES IN {catalog}.{schema}"
        )

        tables = [
            Table(
                name=row["tableName"],
                catalog=catalog,
                schema=schema,
                table_type=row.get("tableType", "TABLE")
            )
            for row in result
        ]

        # Apply filter if provided
        if filter_prefix:
            tables = [t for t in tables if t.name.startswith(filter_prefix)]

        return tables
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/columns", response_model=List[Column])
async def list_columns(
    catalog: str = Query(...),
    schema: str = Query(...),
    table: str = Query(...)
):
    """Get columns for a specific table"""
    try:
        connector = get_databricks_connector()
        result = connector.execute_query(
            f"DESCRIBE TABLE {catalog}.{schema}.{table}"
        )

        columns = [
            Column(
                name=row["col_name"],
                data_type=row["data_type"],
                comment=row.get("comment"),
                nullable=row.get("nullable", True)
            )
            for row in result
            if not row["col_name"].startswith("#")  # Skip metadata rows
        ]
        return columns
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/sql-autocomplete")
async def sql_autocomplete(
    prefix: str = Query(..., description="SQL fragment to complete"),
    context: Optional[str] = Query(None, description="Current SQL context")
):
    """
    Provide SQL autocomplete suggestions

    Returns suggestions for:
    - Catalog names (when typing after FROM)
    - Schema names (when typing catalog.)
    - Table names (when typing catalog.schema.)
    - Column names (when typing in SELECT or WHERE)
    """
    try:
        connector = get_databricks_connector()
        suggestions = []

        # Detect what user is trying to complete
        if "." not in prefix:
            # Suggest catalogs
            result = connector.execute_query("SHOW CATALOGS")
            suggestions = [
                {"type": "catalog", "value": row["catalog"]}
                for row in result
                if row["catalog"].startswith(prefix.lower())
            ]
        elif prefix.count(".") == 1:
            # Suggest schemas
            catalog = prefix.split(".")[0]
            result = connector.execute_query(f"SHOW SCHEMAS IN {catalog}")
            suggestions = [
                {"type": "schema", "value": f"{catalog}.{row['databaseName']}"}
                for row in result
            ]
        elif prefix.count(".") == 2:
            # Suggest tables
            parts = prefix.split(".")
            catalog, schema = parts[0], parts[1]
            result = connector.execute_query(f"SHOW TABLES IN {catalog}.{schema}")
            suggestions = [
                {"type": "table", "value": f"{catalog}.{schema}.{row['tableName']}"}
                for row in result
            ]

        return {"suggestions": suggestions}
    except Exception as e:
        return {"suggestions": [], "error": str(e)}
```

**Endpoints:**
- `GET /api/metadata/catalogs` - List catalogs
- `GET /api/metadata/schemas?catalog={name}` - List schemas
- `GET /api/metadata/tables?catalog={name}&schema={name}` - List tables
- `GET /api/metadata/columns?catalog={name}&schema={name}&table={name}` - Get columns
- `GET /api/metadata/sql-autocomplete?prefix={text}` - SQL completion suggestions

---

### 4.4 Query Execution API (`app/api/queries.py`)

**Purpose:** SQL query execution against Databricks

```python
from fastapi import APIRouter, HTTPException
from app.models.queries import QueryRequest, QueryResponse, QueryValidationRequest
from app.integrations.databricks import get_databricks_connector

router = APIRouter()

@router.post("/execute", response_model=QueryResponse)
async def execute_query(request: QueryRequest):
    """
    Execute SQL query against Databricks

    Request:
        - query: SQL query string
        - limit: Optional row limit (default: 1000)
        - parameters: Optional query parameters

    Response:
        - columns: List of column names
        - rows: List of result rows (as dicts)
        - row_count: Number of rows returned
        - execution_time_ms: Query execution time
    """
    try:
        connector = get_databricks_connector()

        # Apply limit if not present
        query = request.query
        if request.limit and "LIMIT" not in query.upper():
            query = f"{query} LIMIT {request.limit}"

        # Execute query
        import time
        start_time = time.time()
        result = connector.execute_query(query, request.parameters)
        execution_time = (time.time() - start_time) * 1000

        # Extract columns and rows
        if result:
            columns = list(result[0].keys())
            rows = result
        else:
            columns = []
            rows = []

        return QueryResponse(
            columns=columns,
            rows=rows,
            row_count=len(rows),
            execution_time_ms=execution_time
        )
    except Exception as e:
        raise HTTPException(
            status_code=400,
            detail=f"Query execution failed: {str(e)}"
        )

@router.post("/validate")
async def validate_query(request: QueryValidationRequest):
    """
    Validate SQL query without executing it

    Uses EXPLAIN to check query validity
    """
    try:
        connector = get_databricks_connector()
        explain_query = f"EXPLAIN {request.query}"
        connector.execute_query(explain_query)

        return {
            "valid": True,
            "message": "Query is valid"
        }
    except Exception as e:
        return {
            "valid": False,
            "message": str(e)
        }

@router.get("/history")
async def get_query_history():
    """Get query execution history (placeholder)"""
    return {
        "queries": [],
        "message": "Query history feature not yet implemented"
    }

@router.post("/save")
async def save_query():
    """Save query for future use (placeholder)"""
    return {
        "saved": False,
        "message": "Query save feature not yet implemented"
    }
```

**Endpoints:**
- `POST /api/queries/execute` - Execute SQL query
- `POST /api/queries/validate` - Validate SQL without execution
- `GET /api/queries/history` - Get query history (placeholder)
- `POST /api/queries/save` - Save query (placeholder)

---

### 4.5 Semantic Models API (`app/api/models.py`)

**Purpose:** Semantic model CRUD operations

```python
from fastapi import APIRouter, HTTPException, Response
from typing import List
from app.services.volume_metric_store import VolumeMetricStore
from app.models.semantic import SemanticModel
from app.models.semantic_model import SemanticModelCreate, AddMetricSQLRequest

router = APIRouter()

# Demo endpoints (no authentication)
@router.get("/demo/", response_model=List[dict])
async def list_demo_models():
    """List all demo semantic models"""
    try:
        store = VolumeMetricStore()
        models = store.list_metrics(category="demo")
        return [{"id": m, "name": m} for m in models]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/demo/{model_id}")
async def get_demo_model(model_id: str):
    """Get specific demo model"""
    try:
        store = VolumeMetricStore()
        model = store.get_metric(model_id, category="demo")
        if not model:
            raise HTTPException(status_code=404, detail="Model not found")
        return model
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Production endpoints (require authentication)
@router.get("/", response_model=List[dict])
async def list_models(category: str = "production"):
    """List all semantic models in a category"""
    try:
        store = VolumeMetricStore()
        models = store.list_metrics(category=category)

        # Load full model details
        model_list = []
        for model_id in models:
            model = store.get_metric(model_id, category=category)
            if model:
                model_list.append({
                    "id": model_id,
                    "name": model.get("name", model_id),
                    "description": model.get("description"),
                    "metrics_count": len(model.get("metrics", [])),
                    "dimensions_count": len(model.get("dimensions", []))
                })

        return model_list
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{model_id}", response_model=SemanticModel)
async def get_model(model_id: str, category: str = "production"):
    """Get specific semantic model by ID"""
    try:
        store = VolumeMetricStore()
        model = store.get_metric(model_id, category=category)
        if not model:
            raise HTTPException(status_code=404, detail="Model not found")
        return model
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/", response_model=dict)
async def create_model(model: SemanticModelCreate):
    """Create new semantic model"""
    try:
        store = VolumeMetricStore()

        # Convert to dictionary format
        model_dict = model.dict()

        # Save to volume
        success = store.save_metric(
            metric=model_dict,
            category="production"
        )

        if not success:
            raise HTTPException(status_code=500, detail="Failed to save model")

        return {
            "id": model.name,
            "message": "Model created successfully"
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.put("/{model_id}", response_model=dict)
async def update_model(model_id: str, model: SemanticModel):
    """Update existing semantic model"""
    try:
        store = VolumeMetricStore()

        # Check if model exists
        existing = store.get_metric(model_id, category="production")
        if not existing:
            raise HTTPException(status_code=404, detail="Model not found")

        # Update model
        model_dict = model.dict()
        success = store.save_metric(model_dict, category="production")

        if not success:
            raise HTTPException(status_code=500, detail="Failed to update model")

        return {
            "id": model_id,
            "message": "Model updated successfully"
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.delete("/{model_id}")
async def delete_model(model_id: str):
    """Delete semantic model"""
    try:
        store = VolumeMetricStore()
        success = store.delete_metric(model_id, category="production")

        if not success:
            raise HTTPException(status_code=404, detail="Model not found")

        return {"message": "Model deleted successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{model_id}/download")
async def download_model_yaml(model_id: str, category: str = "production"):
    """Download model as YAML file"""
    try:
        store = VolumeMetricStore()
        model = store.get_metric(model_id, category=category)

        if not model:
            raise HTTPException(status_code=404, detail="Model not found")

        # Convert to YAML
        import yaml
        yaml_content = yaml.dump(model, default_flow_style=False)

        return Response(
            content=yaml_content,
            media_type="application/x-yaml",
            headers={
                "Content-Disposition": f"attachment; filename={model_id}.yaml"
            }
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/{model_id}/metrics")
async def add_metric_to_model(model_id: str, request: AddMetricSQLRequest):
    """Add new metric to existing model using SQL definition"""
    try:
        store = VolumeMetricStore()
        model = store.get_metric(model_id, category="production")

        if not model:
            raise HTTPException(status_code=404, detail="Model not found")

        # Parse SQL and create metric definition
        # (Implementation would analyze SQL and extract metric info)
        new_metric = {
            "name": request.metric_name,
            "description": request.description,
            "type": "simple",
            "sql": request.sql
        }

        # Add to model
        if "metrics" not in model:
            model["metrics"] = []
        model["metrics"].append(new_metric)

        # Save updated model
        store.save_metric(model, category="production")

        return {
            "message": "Metric added successfully",
            "metric": new_metric
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
```

**Endpoints:**
- `GET /api/models/demo/` - List demo models
- `GET /api/models/demo/{id}` - Get demo model
- `GET /api/models/` - List production models
- `GET /api/models/{id}` - Get model by ID
- `POST /api/models/` - Create new model
- `PUT /api/models/{id}` - Update model
- `DELETE /api/models/{id}` - Delete model
- `GET /api/models/{id}/download` - Download as YAML
- `POST /api/models/{id}/metrics` - Add metric to model

---

## 5. Data Models

### 5.1 Metadata Models (`app/models/metadata.py`)

```python
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime

class Catalog(BaseModel):
    """Unity Catalog catalog"""
    name: str
    comment: Optional[str] = None
    owner: Optional[str] = None
    created_at: Optional[datetime] = None

class Schema(BaseModel):
    """Database schema"""
    name: str
    catalog: str
    comment: Optional[str] = None
    owner: Optional[str] = None
    location: Optional[str] = None

class Table(BaseModel):
    """Table metadata"""
    name: str
    catalog: str
    schema: str
    table_type: str = "TABLE"  # TABLE, VIEW, EXTERNAL
    comment: Optional[str] = None
    owner: Optional[str] = None
    location: Optional[str] = None
    created_at: Optional[datetime] = None
    row_count: Optional[int] = None
    size_bytes: Optional[int] = None

class Column(BaseModel):
    """Column metadata"""
    name: str
    data_type: str
    comment: Optional[str] = None
    nullable: bool = True
    is_partition_column: bool = False
    position: Optional[int] = None
```

### 5.2 Query Models (`app/models/queries.py`)

```python
from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional

class QueryRequest(BaseModel):
    """SQL query execution request"""
    query: str = Field(..., description="SQL query to execute")
    limit: Optional[int] = Field(1000, description="Maximum rows to return")
    parameters: Optional[Dict[str, Any]] = Field(None, description="Query parameters")

class QueryResponse(BaseModel):
    """SQL query execution response"""
    columns: List[str] = Field(..., description="Column names")
    rows: List[Dict[str, Any]] = Field(..., description="Result rows")
    row_count: int = Field(..., description="Number of rows returned")
    execution_time_ms: float = Field(..., description="Execution time in milliseconds")
    truncated: bool = Field(False, description="Whether results were truncated")

class QueryValidationRequest(BaseModel):
    """Query validation request"""
    query: str = Field(..., description="SQL query to validate")

class QueryValidationResponse(BaseModel):
    """Query validation response"""
    valid: bool
    message: str
    errors: Optional[List[str]] = None
```

### 5.3 Semantic Model (`app/models/semantic.py`)

```python
from pydantic import BaseModel, Field
from typing import List, Dict, Optional, Any
from enum import Enum

class TimeGranularity(str, Enum):
    """Time dimension granularities"""
    SECOND = "second"
    MINUTE = "minute"
    HOUR = "hour"
    DAY = "day"
    WEEK = "week"
    MONTH = "month"
    QUARTER = "quarter"
    YEAR = "year"

class EntityType(str, Enum):
    """Entity types for relationships"""
    PRIMARY = "primary"
    FOREIGN = "foreign"
    UNIQUE = "unique"

class DimensionType(str, Enum):
    """Dimension types"""
    CATEGORICAL = "categorical"
    TIME = "time"
    BOOLEAN = "boolean"

class AggregationType(str, Enum):
    """Aggregation types for measures"""
    SUM = "sum"
    COUNT = "count"
    AVG = "avg"
    MIN = "min"
    MAX = "max"
    COUNT_DISTINCT = "count_distinct"

class MetricType(str, Enum):
    """Metric types"""
    SIMPLE = "simple"
    RATIO = "ratio"
    DERIVED = "derived"
    CUMULATIVE = "cumulative"

class Entity(BaseModel):
    """Entity definition (primary/foreign keys)"""
    name: str
    type: EntityType
    expr: Optional[str] = None

class Dimension(BaseModel):
    """Dimension definition"""
    name: str
    type: DimensionType
    expr: Optional[str] = None
    time_granularity: Optional[List[TimeGranularity]] = None
    description: Optional[str] = None

class Measure(BaseModel):
    """Measure definition (aggregatable field)"""
    name: str
    agg: AggregationType
    expr: str
    description: Optional[str] = None
    create_metric: bool = False

class Metric(BaseModel):
    """Metric definition"""
    name: str
    type: MetricType
    description: Optional[str] = None

    # Simple metric
    measure: Optional[str] = None

    # Ratio metric
    numerator: Optional[str] = None
    denominator: Optional[str] = None

    # Derived metric
    expr: Optional[str] = None
    metrics: Optional[List[str]] = None

    # Metadata
    label: Optional[str] = None
    format: Optional[str] = None

class SemanticModel(BaseModel):
    """Complete semantic model definition"""
    name: str
    description: Optional[str] = None
    model: str = Field(..., description="Base table reference (e.g., ref('gold_sales'))")

    entities: List[Entity] = Field(default_factory=list)
    dimensions: List[Dimension] = Field(default_factory=list)
    measures: List[Measure] = Field(default_factory=list)
    metrics: List[Metric] = Field(default_factory=list)

    # Optional features
    defaults: Optional[Dict[str, Any]] = None
    meta: Optional[Dict[str, Any]] = None
```

---

## 6. Business Services

### 6.1 Volume Metric Store (`app/services/volume_metric_store.py`)

**Purpose:** Manage semantic models in Unity Catalog Volumes

```python
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta
import yaml
from app.core.config import settings
from app.core.logging import logger
from app.integrations.databricks import get_databricks_connector

class VolumeMetricStore:
    """
    Manages semantic models stored in Unity Catalog Volumes

    Storage Structure:
    /Volumes/semantic_layer/metrics/
        production/
            model1.yaml
            model2.yaml
        staging/
            test_model.yaml
        templates/
            template1.yaml
    """

    def __init__(self):
        self.base_path = settings.volume_base_path
        self.connector = get_databricks_connector()

        # In-memory cache
        self.cache: Dict[str, Any] = {}
        self.cache_timestamps: Dict[str, datetime] = {}
        self.cache_ttl = timedelta(minutes=settings.cache_ttl_minutes)

    def list_metrics(self, category: str = "production") -> List[str]:
        """List all metric IDs in a category"""
        try:
            path = f"{self.base_path}/{category}"

            # List files in volume
            result = self.connector.execute_query(
                f"LIST '{path}'"
            )

            # Extract YAML files
            metrics = [
                row["name"].replace(".yaml", "")
                for row in result
                if row["name"].endswith(".yaml")
            ]

            logger.info("Listed metrics", category=category, count=len(metrics))
            return metrics
        except Exception as e:
            logger.error("Failed to list metrics", error=str(e))
            return []

    def get_metric(
        self,
        metric_id: str,
        category: str = "production"
    ) -> Optional[Dict[str, Any]]:
        """
        Get metric by ID with caching

        Returns:
            Dict representation of semantic model, or None if not found
        """
        cache_key = f"{category}:{metric_id}"

        # Check cache
        if self._is_cache_valid(cache_key):
            logger.debug("Cache hit", metric_id=metric_id)
            return self.cache[cache_key]

        # Load from volume
        metric = self._load_metric_from_volume(metric_id, category)

        if metric:
            # Update cache
            self.cache[cache_key] = metric
            self.cache_timestamps[cache_key] = datetime.now()
            logger.info("Loaded metric", metric_id=metric_id, category=category)

        return metric

    def save_metric(
        self,
        metric: Dict[str, Any],
        category: str = "production"
    ) -> bool:
        """
        Save metric to volume with automatic backup

        Returns:
            True if successful, False otherwise
        """
        try:
            metric_id = metric.get("name")
            if not metric_id:
                raise ValueError("Metric must have a 'name' field")

            # Create backup of existing model
            existing = self.get_metric(metric_id, category)
            if existing:
                self._create_backup(metric_id, existing, category)

            # Convert to YAML
            yaml_content = yaml.dump(metric, default_flow_style=False)

            # Write to volume (using COPY INTO or PUT)
            path = f"{self.base_path}/{category}/{metric_id}.yaml"
            self._write_to_volume(path, yaml_content)

            # Invalidate cache
            cache_key = f"{category}:{metric_id}"
            if cache_key in self.cache:
                del self.cache[cache_key]
                del self.cache_timestamps[cache_key]

            logger.info("Saved metric", metric_id=metric_id, category=category)
            return True
        except Exception as e:
            logger.error("Failed to save metric", error=str(e))
            return False

    def delete_metric(self, metric_id: str, category: str = "production") -> bool:
        """Delete metric from volume"""
        try:
            # Create backup before deletion
            existing = self.get_metric(metric_id, category)
            if existing:
                self._create_backup(metric_id, existing, category)

            # Delete file
            path = f"{self.base_path}/{category}/{metric_id}.yaml"
            self.connector.execute_query(f"REMOVE '{path}'")

            # Invalidate cache
            cache_key = f"{category}:{metric_id}"
            if cache_key in self.cache:
                del self.cache[cache_key]
                del self.cache_timestamps[cache_key]

            logger.info("Deleted metric", metric_id=metric_id)
            return True
        except Exception as e:
            logger.error("Failed to delete metric", error=str(e))
            return False

    def _is_cache_valid(self, cache_key: str) -> bool:
        """Check if cache entry is still valid"""
        if cache_key not in self.cache:
            return False

        timestamp = self.cache_timestamps.get(cache_key)
        if not timestamp:
            return False

        age = datetime.now() - timestamp
        return age < self.cache_ttl

    def _load_metric_from_volume(
        self,
        metric_id: str,
        category: str
    ) -> Optional[Dict[str, Any]]:
        """Load metric YAML from Unity Catalog Volume"""
        try:
            path = f"{self.base_path}/{category}/{metric_id}.yaml"

            # Read file content using Databricks SQL
            result = self.connector.execute_query(
                f"SELECT * FROM read_files('{path}')"
            )

            if not result:
                return None

            # Parse YAML content
            yaml_content = result[0]["content"]
            metric = yaml.safe_load(yaml_content)

            return metric
        except Exception as e:
            logger.error("Failed to load metric", metric_id=metric_id, error=str(e))
            return None

    def _write_to_volume(self, path: str, content: str):
        """Write content to Unity Catalog Volume"""
        # Implementation depends on Databricks API
        # Could use PUT command or write via temporary table
        pass

    def _create_backup(self, metric_id: str, metric: Dict, category: str):
        """Create timestamped backup of metric"""
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_path = f"{self.base_path}/backups/{category}/{metric_id}_{timestamp}.yaml"

            yaml_content = yaml.dump(metric, default_flow_style=False)
            self._write_to_volume(backup_path, yaml_content)

            logger.info("Created backup", metric_id=metric_id, timestamp=timestamp)
        except Exception as e:
            logger.warning("Failed to create backup", error=str(e))
```

---

Due to length constraints, I'll continue with the remaining critical sections in the next files. Let me create a summary document for the remaining sections:

<function_calls>
<invoke name="TodoWrite">
<parameter name="todos">[{"content": "Explore codebase structure and understand the service", "status": "completed", "activeForm": "Exploring codebase structure and understanding the service"}, {"content": "Analyze source code, dependencies, and configuration", "status": "completed", "activeForm": "Analyzing source code, dependencies, and configuration"}, {"content": "Generate architecture and design specifications", "status": "completed", "activeForm": "Generating architecture and design specifications"}, {"content": "Document API endpoints and interfaces", "status": "completed", "activeForm": "Documenting API endpoints and interfaces"}, {"content": "Create data models and database schema documentation", "status": "in_progress", "activeForm": "Creating data models and database schema documentation"}, {"content": "Document dependencies and environment setup", "status": "pending", "activeForm": "Documenting dependencies and environment setup"}, {"content": "Create comprehensive specifications folder", "status": "completed", "activeForm": "Creating comprehensive specifications folder"}, {"content": "Run linter on any generated files", "status": "pending", "activeForm": "Running linter on generated files"}]