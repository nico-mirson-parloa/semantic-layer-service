# Deployment Specification

**Document Version:** 1.0
**Last Updated:** 2025-11-04

---

## Table of Contents

1. [Infrastructure Requirements](#1-infrastructure-requirements)
2. [Environment Variables](#2-environment-variables)
3. [Docker Deployment](#3-docker-deployment)
4. [Local Development Setup](#4-local-development-setup)
5. [Production Deployment](#5-production-deployment)
6. [Monitoring & Observability](#6-monitoring--observability)

---

## 1. Infrastructure Requirements

### Minimum Requirements

| Component | Specification | Notes |
|-----------|--------------|-------|
| **CPU** | 2 cores | 4 cores recommended for production |
| **Memory** | 4 GB RAM | 8 GB recommended for production |
| **Storage** | 20 GB | For application and logs |
| **Network** | Outbound HTTPS | To Databricks workspace |

### External Dependencies

1. **Databricks Workspace**
   - Unity Catalog enabled
   - SQL Warehouse (Serverless recommended)
   - Genie Space (optional but recommended)
   - Personal Access Token or OAuth setup

2. **Unity Catalog Volumes** (for semantic model storage)
   - Catalog: `semantic_layer`
   - Schema: `metrics`
   - Volume: `models`
   - Path: `/Volumes/semantic_layer/metrics/`

3. **Network Access**
   - Outbound to `*.cloud.databricks.com` (or your workspace URL)
   - Port 443 (HTTPS) for Databricks API
   - Port 443 for SQL Warehouse JDBC/ODBC

---

## 2. Environment Variables

### Backend Configuration

Create `.env` file in `backend/` directory:

```bash
# ========== Databricks Configuration ==========
# Required: Your Databricks workspace URL (without https://)
DATABRICKS_HOST=your-workspace.cloud.databricks.com

# Required: Personal Access Token or OAuth token
DATABRICKS_TOKEN=your-databricks-token-here

# Required: SQL Warehouse HTTP path
# Find this in SQL Warehouse details page
DATABRICKS_HTTP_PATH=/sql/1.0/warehouses/abc123def456

# Optional: Warehouse ID (alternative to HTTP path)
DATABRICKS_WAREHOUSE_ID=abc123def456

# Optional but recommended: Genie Space ID for NL queries
# Get from Genie room URL: https://<workspace>/genie/rooms/<space-id>
DATABRICKS_GENIE_SPACE_ID=your-genie-space-id

# Optional: Foundation Model endpoint for LLM analysis
DATABRICKS_FOUNDATION_MODEL_ENDPOINT=databricks-meta-llama-3-1-70b-instruct

# ========== Application Settings ==========
# Debug mode (set to false in production)
DEBUG=false

# Semantic model storage paths
SEMANTIC_MODELS_PATH=./semantic-models
VOLUME_BASE_PATH=/Volumes/semantic_layer/metrics

# ========== Feature Flags ==========
# Enable LLM-based table analysis
ENABLE_LLM_ANALYSIS=true
LLM_ANALYSIS_TIMEOUT=30

# ========== Authentication ==========
# Secret key for JWT signing (CHANGE IN PRODUCTION!)
SECRET_KEY=your-secret-key-min-32-characters-long-change-this

# JWT algorithm
ALGORITHM=HS256

# Token expiration (minutes)
ACCESS_TOKEN_EXPIRE_MINUTES=30

# ========== Caching ==========
# Cache TTL in minutes
CACHE_TTL_MINUTES=30
METADATA_CACHE_TTL_MINUTES=5

# ========== External Integrations ==========
# Optional: Slack webhook for alerts
SLACK_WEBHOOK_URL=https://hooks.slack.com/services/YOUR/WEBHOOK/URL
```

### Frontend Configuration

Create `.env` file in `frontend/` directory:

```bash
# Backend API URL
REACT_APP_API_URL=http://localhost:8000

# Optional: Enable debug mode
REACT_APP_DEBUG=false
```

### Security Best Practices

1. **Never commit `.env` files to version control**
2. **Use different tokens for dev/staging/prod**
3. **Rotate tokens every 90 days**
4. **Use service principal tokens in production**
5. **Store secrets in secure vault (AWS Secrets Manager, Azure Key Vault, etc.)**

---

## 3. Docker Deployment

### Docker Compose (Recommended for Local/Development)

Create `docker-compose.yml` in project root:

```yaml
version: '3.8'

services:
  # Backend API Service
  backend:
    build:
      context: ./backend
      dockerfile: Dockerfile
    container_name: semantic-layer-backend
    ports:
      - "8000:8000"
    environment:
      # Pass through all Databricks config
      - DATABRICKS_HOST=${DATABRICKS_HOST}
      - DATABRICKS_TOKEN=${DATABRICKS_TOKEN}
      - DATABRICKS_HTTP_PATH=${DATABRICKS_HTTP_PATH}
      - DATABRICKS_GENIE_SPACE_ID=${DATABRICKS_GENIE_SPACE_ID}
      - SECRET_KEY=${SECRET_KEY}
      - DEBUG=${DEBUG:-false}
    volumes:
      # Mount code for hot-reload in development
      - ./backend/app:/app/app
      # Mount semantic models directory
      - ./semantic-models:/app/semantic-models
    command: uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/api/health/"]
      interval: 30s
      timeout: 10s
      retries: 3

  # Frontend Service
  frontend:
    build:
      context: ./frontend
      dockerfile: Dockerfile
    container_name: semantic-layer-frontend
    ports:
      - "3000:3000"
    environment:
      - REACT_APP_API_URL=http://localhost:8000
    volumes:
      # Mount code for hot-reload
      - ./frontend/src:/app/src
      - ./frontend/public:/app/public
      # Persist node_modules
      - /app/node_modules
    command: npm run dev
    depends_on:
      - backend
    restart: unless-stopped

  # Optional: SQL API Server
  sql-api:
    build:
      context: ./backend
      dockerfile: Dockerfile
    container_name: semantic-layer-sql-api
    ports:
      - "5433:5433"
    environment:
      - DATABRICKS_HOST=${DATABRICKS_HOST}
      - DATABRICKS_TOKEN=${DATABRICKS_TOKEN}
      - DATABRICKS_HTTP_PATH=${DATABRICKS_HTTP_PATH}
    command: python start_sql_server.py
    depends_on:
      - backend
    restart: unless-stopped
```

### Backend Dockerfile

```dockerfile
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create directory for semantic models
RUN mkdir -p /app/semantic-models

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/api/health/ || exit 1

# Run application
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### Frontend Dockerfile

```dockerfile
FROM node:18-alpine

# Set working directory
WORKDIR /app

# Copy package files
COPY package*.json ./

# Install dependencies
RUN npm ci --only=production

# Copy application code
COPY . .

# Build application
RUN npm run build

# Install serve to run production build
RUN npm install -g serve

# Expose port
EXPOSE 3000

# Run production server
CMD ["serve", "-s", "build", "-l", "3000"]
```

### Running with Docker Compose

```bash
# Start all services
docker-compose up -d

# View logs
docker-compose logs -f

# Stop services
docker-compose down

# Rebuild after code changes
docker-compose up -d --build
```

---

## 4. Local Development Setup

### Prerequisites

- Python 3.11+
- Node.js 18+
- Databricks workspace access
- Databricks Personal Access Token

### Backend Setup

```bash
# 1. Create virtual environment
cd backend
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# 2. Install dependencies
pip install -r requirements.txt

# 3. Create .env file (see section 2)
cp .env.example .env
# Edit .env with your Databricks credentials

# 4. Run development server
uvicorn app.main:app --reload --port 8000

# Server will be available at http://localhost:8000
# API docs at http://localhost:8000/docs
```

### Frontend Setup

```bash
# 1. Install dependencies
cd frontend
npm install

# 2. Create .env file
cp .env.example .env
# Edit if needed (defaults to localhost:8000)

# 3. Run development server
npm start

# Server will be available at http://localhost:3000
```

### SQL API Setup (Optional)

```bash
# In backend directory with venv activated
python start_sql_server.py

# SQL API available at localhost:5433
# Connect using PostgreSQL protocol
```

### Development Workflow

1. **Backend Changes:**
   - Edit code in `backend/app/`
   - Server auto-reloads with `--reload` flag
   - Test at `http://localhost:8000/docs`

2. **Frontend Changes:**
   - Edit code in `frontend/src/`
   - Hot module replacement updates instantly
   - View at `http://localhost:3000`

3. **Running Tests:**
   ```bash
   # Backend tests
   cd backend
   pytest

   # Frontend tests
   cd frontend
   npm test
   ```

---

## 5. Production Deployment

### Pre-Deployment Checklist

- [ ] Environment variables configured
- [ ] SECRET_KEY changed to secure random value
- [ ] DEBUG=false in production
- [ ] Databricks service principal token configured
- [ ] Unity Catalog volumes created
- [ ] SQL Warehouse running
- [ ] Health check endpoints verified
- [ ] Logging configured
- [ ] Monitoring alerts set up

### Deployment Options

#### Option 1: Databricks Jobs

Deploy as Databricks jobs for seamless integration:

```python
# databricks-deploy.py
from databricks.sdk import WorkspaceClient

w = WorkspaceClient()

# Create job for backend API
job = w.jobs.create(
    name="semantic-layer-api",
    tasks=[
        {
            "task_key": "api-server",
            "libraries": [{"pypi": {"package": "fastapi==0.104.1"}}, ...],
            "python_wheel_task": {
                "entry_point": "app.main",
                "parameters": ["--host", "0.0.0.0", "--port", "8000"]
            },
            "new_cluster": {
                "spark_version": "13.3.x-scala2.12",
                "node_type_id": "i3.xlarge",
                "num_workers": 2
            }
        }
    ]
)
```

#### Option 2: Kubernetes

```yaml
# kubernetes-deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: semantic-layer-backend
spec:
  replicas: 3
  selector:
    matchLabels:
      app: semantic-layer-backend
  template:
    metadata:
      labels:
        app: semantic-layer-backend
    spec:
      containers:
      - name: backend
        image: your-registry/semantic-layer-backend:latest
        ports:
        - containerPort: 8000
        env:
        - name: DATABRICKS_HOST
          valueFrom:
            secretKeyRef:
              name: databricks-config
              key: host
        - name: DATABRICKS_TOKEN
          valueFrom:
            secretKeyRef:
              name: databricks-config
              key: token
        resources:
          requests:
            memory: "4Gi"
            cpu: "2"
          limits:
            memory: "8Gi"
            cpu: "4"
        livenessProbe:
          httpGet:
            path: /api/health/
            port: 8000
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /api/health/ready
            port: 8000
          initialDelaySeconds: 10
          periodSeconds: 5

---
apiVersion: v1
kind: Service
metadata:
  name: semantic-layer-backend
spec:
  selector:
    app: semantic-layer-backend
  ports:
  - protocol: TCP
    port: 80
    targetPort: 8000
  type: LoadBalancer
```

#### Option 3: Cloud Run (GCP) / App Service (Azure) / ECS (AWS)

**GCP Cloud Run Example:**
```bash
# Build and push image
gcloud builds submit --tag gcr.io/PROJECT_ID/semantic-layer-backend

# Deploy
gcloud run deploy semantic-layer-backend \
  --image gcr.io/PROJECT_ID/semantic-layer-backend \
  --platform managed \
  --region us-central1 \
  --set-env-vars DATABRICKS_HOST=...,DATABRICKS_TOKEN=... \
  --allow-unauthenticated
```

### Production Configuration

```python
# app/core/config.py (production)
class Settings(BaseSettings):
    # Production settings
    debug: bool = False
    log_level: str = "INFO"

    # Security
    secret_key: str = Field(..., min_length=32)  # Enforce minimum length
    cors_origins: List[str] = ["https://yourdomain.com"]

    # Performance
    workers: int = 4
    timeout: int = 60

    # Database connection pooling
    db_pool_size: int = 10
    db_max_overflow: int = 20
```

---

## 6. Monitoring & Observability

### Health Check Endpoints

```bash
# Basic health
curl http://localhost:8000/api/health/

# Databricks connectivity
curl http://localhost:8000/api/health/databricks

# Readiness (all dependencies)
curl http://localhost:8000/api/health/ready
```

### Logging

**Structured JSON Logs:**
```json
{
  "timestamp": "2025-11-04T12:00:00.000Z",
  "level": "info",
  "logger": "app.api.queries",
  "message": "Query executed successfully",
  "query_id": "abc123",
  "duration_ms": 234,
  "user_id": "user@example.com"
}
```

**Log Aggregation:**
- Send logs to Datadog, CloudWatch, or ELK stack
- Configure via environment variables
- Use structured logging for easy parsing

### Metrics to Monitor

| Metric | Target | Alert Threshold |
|--------|--------|----------------|
| API Response Time (p95) | <2s | >5s |
| Error Rate | <1% | >5% |
| Databricks Query Time | <5s | >30s |
| Memory Usage | <80% | >90% |
| CPU Usage | <70% | >85% |
| Active Connections | - | >1000 |

### Alerting

```python
# Example: Slack alert integration
import requests

def send_alert(message: str, severity: str = "warning"):
    """Send alert to Slack"""
    webhook_url = settings.slack_webhook_url
    if not webhook_url:
        return

    payload = {
        "text": f"[{severity.upper()}] Semantic Layer Alert",
        "attachments": [{
            "text": message,
            "color": "danger" if severity == "error" else "warning"
        }]
    }
    requests.post(webhook_url, json=payload)
```

---

## Troubleshooting

### Common Issues

**1. Databricks Connection Failure**
```bash
# Test connection
curl http://localhost:8000/api/health/databricks

# Check environment variables
echo $DATABRICKS_HOST
echo $DATABRICKS_HTTP_PATH

# Verify token
databricks workspace list  # Using Databricks CLI
```

**2. Unity Catalog Volume Access**
```sql
-- Verify volume exists
SHOW VOLUMES IN semantic_layer.metrics;

-- Check permissions
DESCRIBE VOLUME semantic_layer.metrics.models;

-- Test read access
LIST '/Volumes/semantic_layer/metrics/production';
```

**3. Frontend Can't Reach Backend**
```bash
# Check CORS configuration
# Check network connectivity
curl http://localhost:8000/api/health/

# Verify proxy configuration in package.json
"proxy": "http://localhost:8000"
```

**4. High Memory Usage**
```bash
# Check cache size
# Reduce cache TTL
# Increase container memory limits
# Monitor with: docker stats
```

---

## Backup & Disaster Recovery

### Semantic Models Backup

```bash
# Automated backup script
#!/bin/bash
BACKUP_DIR="/backups/semantic-models-$(date +%Y%m%d)"
SOURCE="/Volumes/semantic_layer/metrics"

# Use Databricks CLI or API to copy files
dbfs cp -r $SOURCE $BACKUP_DIR
```

### Database Backup (if using external DB in future)

```bash
# PostgreSQL backup example
pg_dump semantic_layer > backup-$(date +%Y%m%d).sql
```

---

**Next Steps:**
1. Review `11-DEPENDENCIES.md` for all required packages
2. See `08-AUTHENTICATION-AUTHORIZATION.md` for security setup
3. Refer to `03-BACKEND-SPECIFICATION.md` for API details
