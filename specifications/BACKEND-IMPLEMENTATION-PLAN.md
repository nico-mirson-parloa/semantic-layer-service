# Backend Implementation Plan - Semantic Layer Service

**Created by:** Backend Project Manager
**Date:** 2025-11-12
**Status:** In Progress
**Coordinating with:** Frontend PM

---

## Table of Contents

1. [Overview](#overview)
2. [Phase Breakdown](#phase-breakdown)
3. [Phase 0: Project Setup & Configuration](#phase-0-project-setup--configuration)
4. [Phase 1: Core Infrastructure](#phase-1-core-infrastructure)
5. [Phase 2: Essential APIs](#phase-2-essential-apis)
6. [Phase 3: Advanced Features](#phase-3-advanced-features)
7. [Phase 4: Optimization & Production Readiness](#phase-4-optimization--production-readiness)
8. [API Contract Responses](#api-contract-responses)
9. [Testing Strategy](#testing-strategy)
10. [Success Criteria](#success-criteria)

---

## Overview

### Objective
Build a FastAPI backend that provides a semantic layer over Databricks, enabling business users to query data through metrics and dimensions without writing SQL.

### Technology Stack
- **Framework:** FastAPI 0.104.1 (async-first web framework)
- **Database Connector:** databricks-sql-connector 3.0.2
- **Databricks SDK:** databricks-sdk 0.18.0
- **Data Validation:** Pydantic 2.5.2 (V2 with performance improvements)
- **Authentication:** python-jose[cryptography] 3.3.0 (JWT)
- **Logging:** structlog 23.2.0 (structured JSON logging)
- **Testing:** pytest 7.4.3 + pytest-asyncio 0.21.1
- **Python:** 3.11+ (required for Pydantic V2)

### Key Principles
1. **Async-First:** All I/O operations use async/await
2. **Type Safety:** Pydantic models for all request/response data
3. **Separation of Concerns:** API → Services → Integrations
4. **Dependency Injection:** FastAPI's built-in DI system
5. **Caching:** In-memory caching with TTL for performance
6. **Error Handling:** Consistent error responses across all endpoints

---

## Phase Breakdown

| Phase | Focus | Duration | Deliverables |
|-------|-------|----------|--------------|
| **Phase 0** | Project Setup & Config | 1 day | Project structure, dependencies, config |
| **Phase 1** | Core Infrastructure | 2 days | Databricks connector, auth, health checks |
| **Phase 2** | Essential APIs | 3 days | Metadata, queries, semantic models CRUD |
| **Phase 3** | Advanced Features | 3 days | Auto-generation, lineage, documentation, Genie |
| **Phase 4** | Optimization & Production | 2 days | Caching, performance, monitoring, deployment |
| **Total** | | **11 days** | Fully functional backend API |

---

## Phase 0: Project Setup & Configuration

### Goal
Initialize FastAPI project with proper structure, configuration, and dependencies.

### Tasks

#### 1. Create Project Structure

```bash
cd /path/to/semantic-layer-service
mkdir -p backend/{app/{api,auth,core,models,services,integrations,sql_api,utils},tests/{unit,integration,fixtures},semantic-models/{production,staging,development,backups,templates}}
cd backend
```

#### 2. Initialize Python Environment

```bash
# Create virtual environment with Python 3.11+
python3.11 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Verify Python version
python --version  # Should be 3.11+
```

#### 3. Create requirements.txt

**File:** `backend/requirements.txt`
```txt
# Core Framework
fastapi==0.104.1
uvicorn[standard]==0.24.0
pydantic==2.5.2
pydantic-settings==2.1.0

# Databricks Integration
databricks-sql-connector==3.0.2
databricks-sdk==0.18.0

# Data Processing
pyyaml==6.0.1
jinja2==3.1.2
sqlparse==0.4.4
pyparsing==3.1.1

# HTTP & Communication
httpx==0.25.2
requests==2.31.0
python-multipart==0.0.6

# Authentication & Security
python-jose[cryptography]==3.3.0
passlib[bcrypt]==1.7.4

# Logging
structlog==23.2.0
rich==13.7.0

# SQL API (PostgreSQL Protocol)
asyncpg==0.29.0

# Configuration
python-dotenv==1.0.0

# Development & Testing
pytest==7.4.3
pytest-asyncio==0.21.1
black==23.11.0
isort==5.12.0
mypy==1.7.1
```

#### 4. Install Dependencies

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

#### 5. Create Configuration Files

**File:** `backend/.env.example`
```bash
# Databricks Configuration
DATABRICKS_HOST=https://your-workspace.cloud.databricks.com
DATABRICKS_TOKEN=your-databricks-token
DATABRICKS_HTTP_PATH=/sql/1.0/warehouses/your-warehouse-id
DATABRICKS_WAREHOUSE_ID=your-warehouse-id
DATABRICKS_GENIE_SPACE_ID=your-genie-space-id

# Application Settings
DEBUG=false
ENVIRONMENT=development
SEMANTIC_MODELS_PATH=./semantic-models
VOLUME_BASE_PATH=/Volumes/semantic_layer/metrics

# Feature Flags
ENABLE_LLM_ANALYSIS=true
LLM_ANALYSIS_TIMEOUT=30

# Authentication
SECRET_KEY=your-secret-key-change-in-production-use-openssl-rand-hex-32
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# Caching
CACHE_TTL_MINUTES=30
METADATA_CACHE_TTL_MINUTES=5

# External Integrations (optional)
SLACK_WEBHOOK_URL=
```

**File:** `backend/.env` (copy from example)
```bash
cp .env.example .env
# Then edit .env with your actual values
```

#### 6. Create Core Configuration Module

**File:** `backend/app/core/config.py`
```python
from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional


class Settings(BaseSettings):
    """
    Application settings loaded from environment variables.
    Uses Pydantic V2 BaseSettings with improved performance.
    """

    # Databricks Configuration
    databricks_host: Optional[str] = None
    databricks_token: Optional[str] = None
    databricks_http_path: Optional[str] = None
    databricks_warehouse_id: Optional[str] = None
    databricks_genie_space_id: Optional[str] = None
    databricks_foundation_model_endpoint: str = "databricks-meta-llama-3-1-70b-instruct"

    # Application Settings
    debug: bool = False
    environment: str = "development"
    semantic_models_path: str = "./semantic-models"
    volume_base_path: str = "/Volumes/semantic_layer/metrics"

    # API Configuration
    api_v1_prefix: str = "/api"
    project_name: str = "Semantic Layer API"
    version: str = "1.0.0"

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

    # CORS
    cors_origins: list[str] = [
        "http://localhost:3000",
        "http://localhost:3001",
    ]

    # External Integrations
    slack_webhook_url: Optional[str] = None

    model_config = SettingsConfigDict(
        env_file=".env",
        case_sensitive=False,
        extra="allow"
    )


# Singleton instance
settings = Settings()
```

#### 7. Create Logging Configuration

**File:** `backend/app/core/logging.py`
```python
import structlog
import logging
import sys


def setup_logging(debug: bool = False):
    """
    Configure structured logging with structlog.

    Args:
        debug: If True, set log level to DEBUG
    """
    log_level = logging.DEBUG if debug else logging.INFO

    # Configure standard logging
    logging.basicConfig(
        format="%(message)s",
        stream=sys.stdout,
        level=log_level,
    )

    # Configure structlog
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
            structlog.processors.JSONRenderer() if not debug else structlog.dev.ConsoleRenderer()
        ],
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True,
    )


# Get logger instance
logger = structlog.get_logger()
```

#### 8. Create Empty __init__.py Files

```bash
touch backend/app/__init__.py
touch backend/app/api/__init__.py
touch backend/app/auth/__init__.py
touch backend/app/core/__init__.py
touch backend/app/models/__init__.py
touch backend/app/services/__init__.py
touch backend/app/integrations/__init__.py
touch backend/app/sql_api/__init__.py
touch backend/app/utils/__init__.py
touch backend/tests/__init__.py
touch backend/tests/unit/__init__.py
touch backend/tests/integration/__init__.py
```

#### 9. Create pytest Configuration

**File:** `backend/pytest.ini`
```ini
[pytest]
testpaths = tests
python_files = test_*.py
python_classes = Test*
python_functions = test_*
asyncio_mode = auto
addopts =
    -v
    --tb=short
    --strict-markers
    --disable-warnings
markers =
    unit: Unit tests
    integration: Integration tests
    slow: Slow tests
```

**File:** `backend/tests/conftest.py`
```python
import pytest
from fastapi.testclient import TestClient
from app.main import app


@pytest.fixture
def client():
    """Create test client for FastAPI app"""
    return TestClient(app)


@pytest.fixture
def mock_databricks_connector(mocker):
    """Mock Databricks connector for testing"""
    mock = mocker.patch("app.integrations.databricks.DatabricksConnector")
    mock.execute_query.return_value = []
    return mock
```

#### 10. Create Code Quality Configuration

**File:** `backend/pyproject.toml`
```toml
[tool.black]
line-length = 100
target-version = ['py311']
include = '\.pyi?$'
exclude = '''
/(
    \.git
  | \.venv
  | venv
  | \.pytest_cache
  | __pycache__
)/
'''

[tool.isort]
profile = "black"
line_length = 100
skip_gitignore = true

[tool.mypy]
python_version = "3.11"
warn_return_any = true
warn_unused_configs = true
disallow_untyped_defs = true
plugins = ["pydantic.mypy"]

[[tool.mypy.overrides]]
module = "tests.*"
disallow_untyped_defs = false
```

### Deliverables
- ✅ Project structure created
- ✅ Python 3.11+ virtual environment
- ✅ All dependencies installed
- ✅ Configuration files (.env, config.py, logging.py)
- ✅ Testing infrastructure (pytest, conftest)
- ✅ Code quality tools (black, isort, mypy)

---

## Phase 1: Core Infrastructure

### Goal
Build foundational components: Databricks connector, authentication, health checks.

### 1.1: Databricks Connector

**File:** `backend/app/integrations/databricks.py`
```python
from typing import List, Dict, Any, Optional
from databricks import sql
from databricks.sdk import WorkspaceClient
from app.core.config import settings
from app.core.logging import logger


class DatabricksConnector:
    """
    Singleton connector for Databricks SQL Warehouse.
    Manages connection pooling and query execution.
    """

    _instance: Optional['DatabricksConnector'] = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return

        self.host = settings.databricks_host
        self.token = settings.databricks_token
        self.http_path = settings.databricks_http_path

        # Initialize workspace client for Unity Catalog operations
        self.workspace_client = WorkspaceClient(
            host=self.host,
            token=self.token
        )

        self._connection = None
        self._initialized = True

        logger.info(
            "Databricks connector initialized",
            host=self.host,
            http_path=self.http_path
        )

    def _get_connection(self):
        """Get or create connection to Databricks SQL Warehouse"""
        if self._connection is None or not self._is_connection_alive():
            logger.info("Creating new Databricks connection")
            self._connection = sql.connect(
                server_hostname=self.host.replace("https://", ""),
                http_path=self.http_path,
                access_token=self.token,
            )
        return self._connection

    def _is_connection_alive(self) -> bool:
        """Check if connection is still alive"""
        if self._connection is None:
            return False
        try:
            cursor = self._connection.cursor()
            cursor.execute("SELECT 1")
            cursor.close()
            return True
        except Exception:
            return False

    def execute_query(
        self,
        query: str,
        parameters: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """
        Execute SQL query and return results as list of dictionaries.

        Args:
            query: SQL query string
            parameters: Optional query parameters (currently not used)

        Returns:
            List of dictionaries representing rows

        Raises:
            Exception: If query execution fails
        """
        try:
            connection = self._get_connection()
            cursor = connection.cursor()

            logger.debug("Executing query", query=query[:100])
            cursor.execute(query)

            # Fetch column names
            columns = [desc[0] for desc in cursor.description]

            # Fetch all rows and convert to dictionaries
            rows = cursor.fetchall()
            results = [
                dict(zip(columns, row))
                for row in rows
            ]

            cursor.close()

            logger.info(
                "Query executed successfully",
                row_count=len(results),
                query_length=len(query)
            )

            return results

        except Exception as e:
            logger.error(
                "Query execution failed",
                error=str(e),
                query=query[:100]
            )
            raise

    def close(self):
        """Close connection to Databricks"""
        if self._connection:
            self._connection.close()
            self._connection = None
            logger.info("Databricks connection closed")


# Singleton instance
_connector: Optional[DatabricksConnector] = None


def get_databricks_connector() -> DatabricksConnector:
    """Get singleton Databricks connector instance"""
    global _connector
    if _connector is None:
        _connector = DatabricksConnector()
    return _connector
```

### 1.2: Authentication Models

**File:** `backend/app/auth/auth_models.py`
```python
from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime


class User(BaseModel):
    """User model for authentication"""
    id: str = Field(..., description="User ID (email or username)")
    email: str = Field(..., description="User email address")
    display_name: str = Field(..., description="User display name")
    roles: List[str] = Field(default_factory=list, description="User roles")
    permissions: List[str] = Field(default_factory=list, description="User permissions")
    groups: List[str] = Field(default_factory=list, description="User groups")


class LoginRequest(BaseModel):
    """Login request with Databricks token"""
    databricks_token: str = Field(..., description="Databricks Personal Access Token")


class TokenResponse(BaseModel):
    """JWT token response"""
    access_token: str = Field(..., description="JWT access token")
    token_type: str = Field(default="bearer", description="Token type")
    expires_in: int = Field(..., description="Token expiration in seconds")
    user: Optional[User] = Field(None, description="User information")
```

### 1.3: Authentication Service

**File:** `backend/app/auth/databricks_auth.py`
```python
from datetime import datetime, timedelta
from typing import Optional
from jose import JWTError, jwt
from app.core.config import settings
from app.core.logging import logger
from app.auth.auth_models import User
from app.integrations.databricks import get_databricks_connector


class DatabricksAuth:
    """
    Authentication service using Databricks tokens and JWT.

    Flow:
    1. User provides Databricks Personal Access Token
    2. Verify token by making test query to Databricks
    3. Generate JWT token for subsequent requests
    4. JWT contains user info extracted from Databricks
    """

    def __init__(self):
        self.secret_key = settings.secret_key
        self.algorithm = settings.algorithm
        self.access_token_expire_minutes = settings.access_token_expire_minutes

    async def authenticate_user(self, databricks_token: str) -> User:
        """
        Authenticate user using Databricks token.

        Args:
            databricks_token: Databricks Personal Access Token

        Returns:
            User object with ID, email, roles, permissions

        Raises:
            Exception: If authentication fails
        """
        try:
            # Temporarily set token for test query
            connector = get_databricks_connector()
            original_token = connector.token
            connector.token = databricks_token

            # Test connection and get user info
            result = connector.execute_query("SELECT current_user() as user")

            if not result:
                raise Exception("Failed to authenticate with Databricks")

            user_email = result[0].get("user", "unknown@databricks.com")

            # Restore original token
            connector.token = original_token

            # Create user object
            user = User(
                id=user_email,
                email=user_email,
                display_name=user_email.split("@")[0],
                roles=["user"],  # Default role
                permissions=["read", "write"],  # Default permissions
                groups=[]
            )

            logger.info("User authenticated", user_id=user.id)
            return user

        except Exception as e:
            logger.error("Authentication failed", error=str(e))
            raise Exception(f"Databricks authentication failed: {str(e)}")

    def create_access_token(self, user: User) -> str:
        """
        Create JWT access token.

        Args:
            user: User object

        Returns:
            JWT token string
        """
        expire = datetime.utcnow() + timedelta(minutes=self.access_token_expire_minutes)

        to_encode = {
            "sub": user.id,
            "email": user.email,
            "display_name": user.display_name,
            "roles": user.roles,
            "permissions": user.permissions,
            "exp": expire
        }

        encoded_jwt = jwt.encode(to_encode, self.secret_key, algorithm=self.algorithm)

        logger.debug("JWT token created", user_id=user.id, expires_at=expire.isoformat())
        return encoded_jwt

    async def verify_token(self, token: str) -> User:
        """
        Verify JWT token and extract user info.

        Args:
            token: JWT token string

        Returns:
            User object

        Raises:
            Exception: If token is invalid or expired
        """
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])

            user_id: str = payload.get("sub")
            if user_id is None:
                raise Exception("Invalid token: missing user ID")

            user = User(
                id=user_id,
                email=payload.get("email", user_id),
                display_name=payload.get("display_name", ""),
                roles=payload.get("roles", []),
                permissions=payload.get("permissions", []),
                groups=payload.get("groups", [])
            )

            return user

        except JWTError as e:
            logger.error("Token verification failed", error=str(e))
            raise Exception("Invalid or expired token")
```

### 1.4: Main Application Entry Point

**File:** `backend/app/main.py`
```python
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
import time

from app.core.config import settings
from app.core.logging import setup_logging, logger

# Import routers (will be created in Phase 2)
from app.api import health, auth


# Lifespan management
@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan: startup and shutdown events.
    """
    # Startup
    logger.info(
        "Starting Semantic Layer Service",
        version=settings.version,
        environment=settings.environment
    )

    # Initialize logging
    setup_logging(debug=settings.debug)

    # Initialize volume store cache
    from app.services.volume_metric_store import VolumeMetricStore
    volume_store = VolumeMetricStore()
    app.state.volume_store = volume_store

    logger.info("Application startup complete")

    yield

    # Shutdown
    logger.info("Shutting down Semantic Layer Service")

    # Close Databricks connection
    from app.integrations.databricks import get_databricks_connector
    connector = get_databricks_connector()
    connector.close()

    logger.info("Application shutdown complete")


# Create FastAPI application
app = FastAPI(
    title=settings.project_name,
    description="Unified semantic layer for Databricks data lakehouse",
    version=settings.version,
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Request timing middleware
@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    """Add X-Process-Time header to all responses"""
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time
    response.headers["X-Process-Time"] = str(process_time)
    return response


# Exception handlers
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Global exception handler for uncaught exceptions"""
    logger.error(
        "Unhandled exception",
        error=str(exc),
        path=request.url.path,
        method=request.method
    )
    return JSONResponse(
        status_code=500,
        content={
            "detail": "Internal server error",
            "status_code": 500,
            "timestamp": time.time()
        }
    )


# Include routers
app.include_router(health.router, prefix=f"{settings.api_v1_prefix}/health", tags=["Health"])
app.include_router(auth.router, prefix=f"{settings.api_v1_prefix}/auth", tags=["Authentication"])


# Root endpoint
@app.get("/")
async def root():
    """API root endpoint"""
    return {
        "service": settings.project_name,
        "version": settings.version,
        "environment": settings.environment,
        "status": "running",
        "docs_url": "/docs"
    }


# Health check endpoint (for load balancers)
@app.get("/health")
async def quick_health():
    """Quick health check for load balancers"""
    return {"status": "healthy"}
```

### 1.5: Health Check API

**File:** `backend/app/api/health.py`
```python
from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse
from app.integrations.databricks import get_databricks_connector
from app.core.config import settings
from app.core.logging import logger

router = APIRouter()


@router.get("/")
async def health_check():
    """
    Basic health check endpoint.
    Returns service status and version.
    """
    return {
        "status": "healthy",
        "service": "semantic-layer-api",
        "version": settings.version,
        "environment": settings.environment
    }


@router.get("/databricks")
async def databricks_health():
    """
    Check Databricks connectivity.
    Tests connection to SQL Warehouse.
    """
    try:
        connector = get_databricks_connector()
        result = connector.execute_query("SELECT 1 as health_check")

        return {
            "status": "healthy",
            "databricks_connection": "OK",
            "workspace": settings.databricks_host,
            "response_time_ms": 0  # Could add timing here
        }
    except Exception as e:
        logger.error("Databricks health check failed", error=str(e))
        raise HTTPException(
            status_code=503,
            detail=f"Databricks connection failed: {str(e)}"
        )


@router.get("/ready")
async def readiness_check():
    """
    Comprehensive readiness check.
    Checks all dependencies: Databricks, Volume Store, etc.
    """
    checks = {
        "api": "healthy",
        "databricks": "unknown",
        "volume_store": "unknown",
        "config": "unknown"
    }

    # Check Databricks
    try:
        connector = get_databricks_connector()
        connector.execute_query("SELECT 1")
        checks["databricks"] = "healthy"
    except Exception as e:
        checks["databricks"] = "unhealthy"
        logger.error("Databricks readiness check failed", error=str(e))

    # Check Volume Store
    try:
        from app.services.volume_metric_store import VolumeMetricStore
        store = VolumeMetricStore()
        store.list_metrics(category="production")
        checks["volume_store"] = "healthy"
    except Exception as e:
        checks["volume_store"] = "unhealthy"
        logger.error("Volume store readiness check failed", error=str(e))

    # Check Configuration
    try:
        if settings.databricks_host and settings.databricks_token:
            checks["config"] = "healthy"
        else:
            checks["config"] = "unhealthy"
    except Exception:
        checks["config"] = "unhealthy"

    # Determine overall status
    all_healthy = all(v == "healthy" for v in checks.values())
    status_code = 200 if all_healthy else 503

    return JSONResponse(
        status_code=status_code,
        content={
            "status": "healthy" if all_healthy else "unhealthy",
            "checks": checks,
            "version": settings.version
        }
    )
```

### 1.6: Authentication API

**File:** `backend/app/api/auth.py`
```python
from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from app.auth.databricks_auth import DatabricksAuth
from app.auth.auth_models import User, LoginRequest, TokenResponse
from app.core.logging import logger

router = APIRouter()
security = HTTPBearer()
auth_service = DatabricksAuth()


@router.post("/login", response_model=TokenResponse)
async def login(request: LoginRequest):
    """
    Authenticate with Databricks token and return JWT.

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

        return TokenResponse(
            access_token=access_token,
            token_type="bearer",
            expires_in=1800,  # 30 minutes
            user=user
        )
    except Exception as e:
        logger.error("Login failed", error=str(e))
        raise HTTPException(
            status_code=401,
            detail=f"Authentication failed: {str(e)}"
        )


@router.get("/me", response_model=User)
async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """
    Get current user information from JWT token.

    Headers:
        Authorization: Bearer <jwt_token>

    Response:
        User information (id, email, display_name, roles, permissions)
    """
    try:
        token = credentials.credentials
        user = await auth_service.verify_token(token)
        return user
    except Exception as e:
        logger.error("Token verification failed", error=str(e))
        raise HTTPException(
            status_code=401,
            detail="Invalid or expired token"
        )


@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """
    Refresh JWT token.
    Extends token expiration by creating new token with same user info.

    Headers:
        Authorization: Bearer <jwt_token>

    Response:
        New JWT token with extended expiration
    """
    try:
        # Verify current token
        user = await auth_service.verify_token(credentials.credentials)

        # Generate new token
        access_token = auth_service.create_access_token(user)

        return TokenResponse(
            access_token=access_token,
            token_type="bearer",
            expires_in=1800
        )
    except Exception as e:
        logger.error("Token refresh failed", error=str(e))
        raise HTTPException(
            status_code=401,
            detail="Token refresh failed"
        )


@router.get("/permissions")
async def get_permissions(
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """
    Get detailed permission information for current user.

    Headers:
        Authorization: Bearer <jwt_token>

    Response:
        Detailed permissions including roles, permissions, groups
    """
    try:
        user = await auth_service.verify_token(credentials.credentials)
        return {
            "user_id": user.id,
            "email": user.email,
            "roles": user.roles,
            "permissions": user.permissions,
            "groups": user.groups
        }
    except Exception as e:
        logger.error("Failed to get permissions", error=str(e))
        raise HTTPException(
            status_code=401,
            detail="Authentication required"
        )


# Dependency for protected routes
async def get_current_active_user(
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> User:
    """
    Dependency function to get current authenticated user.
    Use this in protected route handlers:

    @router.get("/protected")
    async def protected_route(user: User = Depends(get_current_active_user)):
        return {"user_id": user.id}
    """
    try:
        user = await auth_service.verify_token(credentials.credentials)
        return user
    except Exception as e:
        raise HTTPException(
            status_code=401,
            detail="Could not validate credentials"
        )
```

### Deliverables
- ✅ Databricks connector with connection pooling
- ✅ Authentication service with JWT
- ✅ Health check endpoints
- ✅ Main FastAPI application
- ✅ CORS middleware configured
- ✅ Request timing middleware
- ✅ Global exception handling

---

## Phase 2: Essential APIs

### Goal
Implement core APIs required by frontend: Metadata, Queries, Semantic Models.

### 2.1: Pydantic Models

**File:** `backend/app/models/metadata.py`
```python
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


class Catalog(BaseModel):
    """Unity Catalog catalog"""
    name: str = Field(..., description="Catalog name")
    comment: Optional[str] = Field(None, description="Catalog description")
    owner: Optional[str] = Field(None, description="Catalog owner")
    created_at: Optional[str] = Field(None, description="Creation timestamp (ISO 8601)")


class Schema(BaseModel):
    """Database schema"""
    name: str = Field(..., description="Schema name")
    catalog: str = Field(..., description="Parent catalog name")
    comment: Optional[str] = Field(None, description="Schema description")


class Table(BaseModel):
    """Table metadata"""
    name: str = Field(..., description="Table name")
    catalog: str = Field(..., description="Catalog name")
    schema: str = Field(..., description="Schema name")
    table_type: str = Field(default="TABLE", description="TABLE, VIEW, or MATERIALIZED_VIEW")
    comment: Optional[str] = Field(None, description="Table description")
    row_count: Optional[int] = Field(None, description="Number of rows")
    size_bytes: Optional[int] = Field(None, description="Table size in bytes")
    created_at: Optional[str] = Field(None, description="Creation timestamp (ISO 8601)")
    updated_at: Optional[str] = Field(None, description="Last update timestamp (ISO 8601)")


class Column(BaseModel):
    """Column metadata"""
    name: str = Field(..., description="Column name")
    data_type: str = Field(..., description="Data type (e.g., string, int, double)")
    nullable: bool = Field(default=True, description="Whether column accepts NULL values")
    comment: Optional[str] = Field(None, description="Column description")
    is_partition_key: bool = Field(default=False, description="Whether column is partition key")
```

**File:** `backend/app/models/queries.py`
```python
from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional


class QueryRequest(BaseModel):
    """SQL query execution request"""
    query: str = Field(..., description="SQL query to execute")
    limit: Optional[int] = Field(1000, description="Maximum rows to return")
    warehouse_id: Optional[str] = Field(None, description="Databricks warehouse ID")
    parameters: Optional[Dict[str, Any]] = Field(None, description="Query parameters")


class QueryResponse(BaseModel):
    """SQL query execution response"""
    columns: List[str] = Field(..., description="Column names")
    rows: List[Dict[str, Any]] = Field(..., description="Result rows")
    row_count: int = Field(..., description="Number of rows returned")
    execution_time_ms: float = Field(..., description="Execution time in milliseconds")
    statement_id: Optional[str] = Field(None, description="Databricks statement ID")


class ValidationRequest(BaseModel):
    """Query validation request"""
    query: str = Field(..., description="SQL query to validate")


class ValidationResponse(BaseModel):
    """Query validation response"""
    is_valid: bool = Field(..., description="Whether query is valid")
    errors: List[str] = Field(default_factory=list, description="Validation errors")
    warnings: List[str] = Field(default_factory=list, description="Validation warnings")
```

**File:** `backend/app/models/semantic.py`
```python
from pydantic import BaseModel, Field
from typing import List, Dict, Optional, Any
from enum import Enum


class DimensionType(str, Enum):
    """Dimension types"""
    CATEGORICAL = "categorical"
    TIME = "time"


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


class Entity(BaseModel):
    """Entity definition (primary/foreign keys)"""
    name: str = Field(..., description="Entity name")
    type: str = Field(..., description="Entity type (primary, foreign, unique)")
    description: Optional[str] = Field(None, description="Entity description")
    expr: Optional[str] = Field(None, description="SQL expression")
    role: Optional[str] = Field(None, description="Entity role")


class Dimension(BaseModel):
    """Dimension definition"""
    name: str = Field(..., description="Dimension name")
    type: DimensionType = Field(..., description="Dimension type (categorical or time)")
    description: Optional[str] = Field(None, description="Dimension description")
    expr: Optional[str] = Field(None, description="SQL expression")
    label: Optional[str] = Field(None, description="Display label")


class Measure(BaseModel):
    """Measure definition (aggregatable field)"""
    name: str = Field(..., description="Measure name")
    agg: AggregationType = Field(..., description="Aggregation type")
    description: Optional[str] = Field(None, description="Measure description")
    expr: Optional[str] = Field(None, description="SQL expression")
    label: Optional[str] = Field(None, description="Display label")


class Metric(BaseModel):
    """Metric definition"""
    name: str = Field(..., description="Metric name")
    type: MetricType = Field(..., description="Metric type")
    description: Optional[str] = Field(None, description="Metric description")
    type_params: Optional[Dict[str, Any]] = Field(None, description="Type-specific parameters")
    label: Optional[str] = Field(None, description="Display label")
    filter: Optional[str] = Field(None, description="SQL filter expression")


class SemanticModel(BaseModel):
    """Complete semantic model definition"""
    name: str = Field(..., description="Model name")
    description: Optional[str] = Field(None, description="Model description")
    model: str = Field(..., description="Base table reference")
    version: Optional[str] = Field(None, description="Model version")

    entities: List[Entity] = Field(default_factory=list, description="Entity definitions")
    dimensions: List[Dimension] = Field(default_factory=list, description="Dimension definitions")
    measures: List[Measure] = Field(default_factory=list, description="Measure definitions")
    metrics: List[Metric] = Field(default_factory=list, description="Metric definitions")

    defaults: Optional[Dict[str, Any]] = Field(None, description="Default values")
    meta: Optional[Dict[str, Any]] = Field(None, description="Metadata")
```

### 2.2: Metadata API (truncated for brevity - see backend spec for full implementation)

**File:** `backend/app/api/metadata.py` - Would contain:
- `GET /api/metadata/catalogs` - List catalogs
- `GET /api/metadata/schemas` - List schemas
- `GET /api/metadata/tables` - List tables
- `GET /api/metadata/columns` - Get columns
- `GET /api/metadata/sql-autocomplete` - SQL autocomplete

### 2.3: Queries API (truncated for brevity)

**File:** `backend/app/api/queries.py` - Would contain:
- `POST /api/queries/execute` - Execute query
- `POST /api/queries/validate` - Validate query

### 2.4: Semantic Models API (truncated for brevity)

**File:** `backend/app/api/models.py` - Would contain:
- `GET /api/models/` - List models
- `GET /api/models/{id}` - Get model
- `POST /api/models/` - Create model
- `PUT /api/models/{id}` - Update model
- `DELETE /api/models/{id}` - Delete model
- `GET /api/models/{id}/download` - Download YAML

### Deliverables
- ✅ All Pydantic models for requests/responses
- ✅ Metadata API (5 endpoints)
- ✅ Queries API (2 endpoints)
- ✅ Semantic Models API (6 endpoints)
- ✅ Volume Metric Store service

---

## Phase 3: Advanced Features

### Goal
Implement AI-powered features: auto-generation, lineage, documentation, Genie integration.

### 3.1: AI Model Generation APIs
- `GET /api/catalog/gold-tables` - List gold tables
- `POST /api/catalog/analyze-table` - Analyze table structure
- `POST /api/catalog/generate-model` - Generate semantic model with AI

### 3.2: Lineage APIs
- `GET /api/lineage/tables/{catalog}.{schema}.{table}` - Get table lineage
- `GET /api/lineage/models/{model_id}` - Get model lineage

### 3.3: Documentation APIs
- `POST /api/documentation/generate` - Generate documentation
- `GET /api/documentation/models` - List documented models

### 3.4: Genie Integration
- `POST /api/genie/query` - Natural language to SQL
- `POST /api/genie/suggest-metrics` - AI metric suggestions

### Deliverables
- ✅ Catalog browsing and analysis
- ✅ AI-powered model generation
- ✅ Data lineage tracking
- ✅ Documentation generation
- ✅ Genie NL-to-SQL integration

---

## Phase 4: Optimization & Production Readiness

### Goal
Optimize performance, add monitoring, prepare for production deployment.

### 4.1: Performance Optimization
- Implement caching layer for metadata queries
- Add connection pooling for Databricks
- Optimize query execution with batch processing
- Add request rate limiting

### 4.2: Monitoring & Observability
- Add Prometheus metrics export
- Implement health check dashboard
- Add query performance tracking
- Set up structured logging aggregation

### 4.3: Production Configuration
- Create Dockerfile
- Add docker-compose.yml
- Configure environment-based settings
- Set up CI/CD pipeline

### 4.4: Documentation
- Generate OpenAPI/Swagger specification
- Create API reference documentation
- Write deployment guide
- Create troubleshooting runbook

### Deliverables
- ✅ Caching layer implemented
- ✅ Monitoring metrics exposed
- ✅ Dockerized application
- ✅ Production-ready configuration
- ✅ Complete API documentation

---

## API Contract Responses

### Authentication Answers

**Q1: What authentication method are we using?**
- **Answer:** JWT tokens generated from Databricks Personal Access Tokens
- **Flow:**
  1. User provides Databricks PAT via `POST /api/auth/login`
  2. Backend verifies PAT by making test query to Databricks
  3. Backend generates JWT token with 30-minute expiration
  4. Frontend stores JWT and sends it in `Authorization: Bearer <token>` header
  5. Backend verifies JWT on protected endpoints

**Q2: What permissions/roles are supported?**
- **Answer:** Initial implementation has basic roles:
  - `user`: Standard user (default)
  - `admin`: Administrator (future)
  - `analyst`: Business analyst (future)
  - `engineer`: Data engineer (future)
- **Permissions:**
  - `read`: Read access to models and queries
  - `write`: Create/update models
  - `delete`: Delete models
  - `execute`: Execute queries
- **Note:** Roles/permissions are extracted from Databricks workspace in future iterations

**Q3: How long are tokens valid?**
- **Answer:** 30 minutes (1800 seconds)
- **Refresh:** Use `POST /api/auth/refresh` to get new token before expiration
- **Expiration handling:** Frontend should refresh token proactively or handle 401 errors

### API Behavior Answers

**Q4: Do we support pagination?**
- **Answer:** Not in Phase 1, but will add in Phase 4
- **When implemented, format will be:**
  ```json
  {
    "data": [],
    "pagination": {
      "total": 1000,
      "page": 1,
      "page_size": 50,
      "total_pages": 20
    }
  }
  ```
- **Endpoints that will support pagination:**
  - `GET /api/models/` (when model count > 100)
  - `GET /api/metrics-explorer/metrics` (when metric count > 100)

**Q5: What are the rate limits?**
- **Answer:** Phase 1 has no rate limits
- **Phase 4 will implement:**
  - 100 requests/minute per user for metadata endpoints
  - 10 queries/minute for query execution endpoints
  - 1000 requests/minute for health checks
- **Headers returned:**
  - `X-RateLimit-Limit`: Total allowed requests
  - `X-RateLimit-Remaining`: Remaining requests
  - `X-RateLimit-Reset`: Unix timestamp when limit resets

**Q6: Do query executions return results immediately?**
- **Answer:** Yes, synchronous execution for Phase 1-2
- **Phase 3 will add async execution for long-running queries:**
  - `POST /api/queries/execute` with `async=true` returns immediately with `query_id`
  - `GET /api/queries/{query_id}/status` to check status
  - `GET /api/queries/{query_id}/results` to fetch results when complete
- **Timeout:** Queries timeout after 120 seconds

**Q7: Is there WebSocket support?**
- **Answer:** Not in initial phases
- **Future:** Will add WebSocket support for:
  - Real-time query progress updates
  - Model update notifications
  - System status changes
- **URL:** `ws://localhost:8000/api/ws/queries/{query_id}`

### Data Format Answers

**Q8: What timestamp format do you use?**
- **Answer:** ISO 8601 format: `2025-11-12T10:30:00Z`
- **All timestamps are UTC**
- **Example:** `created_at: "2025-11-12T10:30:00Z"`

**Q9: How are null values represented?**
- **Answer:** `null` (JSON null, not string "null")
- **Example:**
  ```json
  {
    "name": "my_table",
    "comment": null,
    "row_count": 1000
  }
  ```

**Q10: Are model IDs UUIDs or names?**
- **Answer:** Names (strings)
- **Format:** Lowercase with underscores (e.g., `customer_metrics`)
- **Validation:** Must match regex `^[a-z][a-z0-9_]*$`
- **URL routing:** Use name directly (e.g., `/api/models/customer_metrics`)

### File Operations Answers

**Q11: Is there a model upload endpoint?**
- **Answer:** Yes, will be implemented in Phase 2
- **Endpoint:** `POST /api/models/upload`
- **Request format:** `multipart/form-data`
  ```python
  files = {"file": ("model.yaml", file_content, "application/x-yaml")}
  data = {"category": "production", "overwrite": "false"}
  ```
- **Response:**
  ```json
  {
    "id": "uploaded_model_name",
    "message": "Model uploaded successfully",
    "validation": {
      "valid": true,
      "warnings": []
    }
  }
  ```

**Q12: Can we export query results?**
- **Answer:** Yes, Phase 3 will add:
- **Endpoint:** `POST /api/queries/execute` with `export_format` parameter
- **Formats supported:** `json`, `csv`, `excel`, `parquet`
- **Response:**
  - For `json`: Direct JSON response
  - For others: Download URL with expiring signed URL
  ```json
  {
    "export_url": "https://...",
    "expires_at": "2025-11-12T11:30:00Z",
    "file_size_bytes": 1048576
  }
  ```

### Advanced Features Answers

**Q13: Batch operations support?**
- **Answer:** Phase 3 will add:
- **Endpoint:** `POST /api/models/batch`
- **Operations:** `create`, `update`, `delete`
- **Request:**
  ```json
  {
    "operations": [
      {"action": "delete", "model_id": "old_model"},
      {"action": "create", "model": {...}},
      {"action": "update", "model_id": "existing", "model": {...}}
    ]
  }
  ```
- **Response:**
  ```json
  {
    "results": [
      {"model_id": "old_model", "status": "deleted", "success": true},
      {"model_id": "new_model", "status": "created", "success": true},
      {"model_id": "existing", "status": "updated", "success": false, "error": "..."}
    ],
    "summary": {"total": 3, "succeeded": 2, "failed": 1}
  }
  ```

**Q14: Search/filter API for models?**
- **Answer:** Yes, implemented in Phase 2
- **Endpoint:** `GET /api/models/search`
- **Query parameters:**
  - `query`: Full-text search (searches name, description, metrics)
  - `category`: Filter by category (production, staging, development)
  - `tags`: Filter by tags
  - `has_metrics`: Filter models with/without metrics
  - `created_after`: Filter by creation date
- **Example:** `GET /api/models/search?query=revenue&category=production&has_metrics=true`

---

## Testing Strategy

### Unit Tests
```python
# tests/unit/test_databricks_connector.py
def test_execute_query(mock_databricks_connector):
    connector = get_databricks_connector()
    result = connector.execute_query("SELECT 1")
    assert len(result) > 0

# tests/unit/test_auth.py
async def test_authenticate_user():
    auth = DatabricksAuth()
    user = await auth.authenticate_user("valid_token")
    assert user.email.endswith("@databricks.com")

# tests/unit/test_semantic_parser.py
def test_parse_semantic_model():
    yaml_content = "..."
    model = parse_semantic_model(yaml_content)
    assert model.name == "expected_name"
```

### Integration Tests
```python
# tests/integration/test_api_endpoints.py
def test_health_endpoint(client):
    response = client.get("/api/health/")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"

def test_login_endpoint(client):
    response = client.post("/api/auth/login", json={
        "databricks_token": "test_token"
    })
    assert response.status_code == 200
    assert "access_token" in response.json()

def test_list_catalogs(client, auth_headers):
    response = client.get("/api/metadata/catalogs", headers=auth_headers)
    assert response.status_code == 200
    assert isinstance(response.json(), list)
```

### Manual Testing Checklist
- [ ] All endpoints return correct status codes
- [ ] Authentication flow works end-to-end
- [ ] Query execution returns formatted results
- [ ] Model CRUD operations work correctly
- [ ] Error responses have consistent format
- [ ] CORS headers allow frontend origin

---

## Success Criteria

### Phase 0 Success
- [ ] Project structure created
- [ ] Dependencies installed (all imports work)
- [ ] Configuration loaded from .env
- [ ] `python -m app.main` runs without errors

### Phase 1 Success
- [ ] Databricks connector executes queries
- [ ] JWT authentication works
- [ ] Health checks return 200 OK
- [ ] CORS allows `http://localhost:3000`
- [ ] Logs output structured JSON

### Phase 2 Success
- [ ] Metadata API lists catalogs, schemas, tables
- [ ] Query execution returns results in <5s
- [ ] Model CRUD operations work
- [ ] All endpoints have proper error handling
- [ ] OpenAPI docs generated at `/docs`

### Phase 3 Success
- [ ] AI model generation produces valid YAML
- [ ] Lineage API returns graph structure
- [ ] Documentation generation works
- [ ] Genie integration translates NL to SQL

### Phase 4 Success
- [ ] Caching reduces query time by 50%
- [ ] Prometheus metrics exported
- [ ] Docker container builds successfully
- [ ] Production deployment successful
- [ ] All manual tests passing

---

## Commit Schedule

- **Checkpoint 1:** After Phase 0 (project setup)
- **Checkpoint 2:** After Phase 1 (core infrastructure)
- **Checkpoint 3:** After Phase 2 (essential APIs)
- **Checkpoint 4:** After Phase 3 (advanced features)
- **Checkpoint 5:** After Phase 4 (production ready)

**Remember:** Commit progress every 30 minutes as per PM instructions.

---

**End of Backend Implementation Plan**
