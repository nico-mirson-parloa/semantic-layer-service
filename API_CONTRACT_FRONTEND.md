# API Contract - Frontend Requirements

**Document Version:** 1.0
**Date:** 2025-11-12
**From:** Frontend PM
**To:** Backend PM

---

## Overview

This document outlines the API endpoints required by the frontend application, organized by priority and implementation phase. Each endpoint includes expected request/response formats and critical requirements.

---

## Priority 1: CRITICAL (Required for Phase 2 - Navigation & Layout)

### Health Endpoints

#### 1. Backend Health Check
```
GET /api/health/
```

**Response:**
```json
{
  "status": "healthy",
  "timestamp": "2025-11-12T10:00:00Z",
  "version": "1.0.0"
}
```

**Frontend Usage:** Health indicator in sidebar, polls every 30 seconds

---

#### 2. Databricks Connection Health
```
GET /api/health/databricks
```

**Response:**
```json
{
  "status": "healthy",
  "connected": true,
  "workspace_url": "https://adb-xxx.azuredatabricks.net",
  "timestamp": "2025-11-12T10:00:00Z"
}
```

**Frontend Usage:** Health indicator in sidebar, polls every 30 seconds

**Error Response:**
```json
{
  "status": "unhealthy",
  "connected": false,
  "error": "Connection timeout",
  "timestamp": "2025-11-12T10:00:00Z"
}
```

---

## Priority 2: HIGH (Required for Phase 3 - Core Pages)

### Metadata Endpoints

#### 3. List Catalogs
```
GET /api/metadata/catalogs
```

**Response:**
```json
{
  "catalogs": [
    {
      "name": "production",
      "comment": "Production data catalog"
    },
    {
      "name": "staging",
      "comment": "Staging environment"
    }
  ]
}
```

**Frontend Usage:** MetadataPage tree view root level

---

#### 4. List Schemas
```
GET /api/metadata/schemas?catalog={catalog_name}
```

**Query Parameters:**
- `catalog` (required): Catalog name

**Response:**
```json
{
  "schemas": [
    {
      "name": "gold",
      "catalog": "production",
      "comment": "Gold layer tables"
    },
    {
      "name": "silver",
      "catalog": "production"
    }
  ]
}
```

**Frontend Usage:** MetadataPage tree view, expand catalog to show schemas

---

#### 5. List Tables
```
GET /api/metadata/tables?catalog={catalog}&schema={schema}
```

**Query Parameters:**
- `catalog` (required): Catalog name
- `schema` (required): Schema name

**Response:**
```json
{
  "tables": [
    {
      "name": "amp_all_events_v2",
      "catalog": "production",
      "schema": "gold",
      "table_type": "TABLE",
      "row_count": 1500000,
      "created_at": "2025-01-15T10:00:00Z",
      "updated_at": "2025-11-12T09:30:00Z"
    }
  ]
}
```

**Frontend Usage:** MetadataPage tree view, expand schema to show tables

---

#### 6. List Columns
```
GET /api/metadata/columns?catalog={catalog}&schema={schema}&table={table}
```

**Query Parameters:**
- `catalog` (required): Catalog name
- `schema` (required): Schema name
- `table` (required): Table name

**Response:**
```json
{
  "columns": [
    {
      "name": "event_timestamp",
      "data_type": "TIMESTAMP",
      "nullable": false,
      "comment": "Timestamp when the event occurred",
      "position": 1
    },
    {
      "name": "conversation_id",
      "data_type": "STRING",
      "nullable": false,
      "comment": "Unique identifier for conversation",
      "position": 2
    }
  ],
  "table_info": {
    "catalog": "production",
    "schema": "gold",
    "table": "amp_all_events_v2",
    "column_count": 2
  }
}
```

**Frontend Usage:** MetadataPage detail panel when table is selected

---

#### 7. SQL Autocomplete
```
GET /api/metadata/sql-autocomplete?prefix={prefix}
```

**Query Parameters:**
- `prefix` (required): Partial text to autocomplete (min 2 characters)

**Response:**
```json
{
  "suggestions": [
    {
      "value": "production.gold.amp_all_events_v2",
      "type": "table",
      "description": "Activity stream table"
    },
    {
      "value": "conversation_id",
      "type": "column",
      "description": "STRING - Unique conversation identifier"
    },
    {
      "value": "COUNT",
      "type": "function",
      "description": "Aggregate function"
    }
  ]
}
```

**Frontend Usage:** SQLEditor autocomplete dropdown, debounced with 300ms delay

**Notes:**
- Should match table names, column names, SQL keywords, functions
- Case-insensitive matching
- Limit to top 20 suggestions
- Fast response required (<100ms preferred)

---

### Query Endpoints

#### 8. Execute SQL Query
```
POST /api/queries/execute
```

**Request Body:**
```json
{
  "query": "SELECT conversation_id, COUNT(*) as event_count FROM production.gold.amp_all_events_v2 GROUP BY conversation_id LIMIT 10",
  "limit": 1000
}
```

**Request Parameters:**
- `query` (required): SQL query string
- `limit` (optional): Max rows to return, default 1000

**Response:**
```json
{
  "columns": ["conversation_id", "event_count"],
  "rows": [
    {
      "conversation_id": "conv_12345",
      "event_count": 42
    },
    {
      "conversation_id": "conv_67890",
      "event_count": 38
    }
  ],
  "row_count": 2,
  "execution_time_ms": 1523,
  "query_id": "01j2k3m4n5p6q7r8s9t0"
}
```

**Frontend Usage:** QueryLabPage query execution

**Error Response:**
```json
{
  "error": "SQL syntax error",
  "status": "error",
  "details": {
    "line": 1,
    "column": 45,
    "message": "Unexpected token ')'"
  },
  "query_id": "01j2k3m4n5p6q7r8s9t0"
}
```

**Critical Requirements:**
- Must handle queries up to 10,000 characters
- Timeout after 60 seconds
- Return query_id for tracking
- Include execution time in response
- Limit rows to prevent memory issues

---

#### 9. Validate SQL Query
```
POST /api/queries/validate
```

**Request Body:**
```json
{
  "query": "SELECT * FROM production.gold.amp_all_events_v2"
}
```

**Response (Valid):**
```json
{
  "valid": true,
  "message": "Query is valid"
}
```

**Response (Invalid):**
```json
{
  "valid": false,
  "error": "Table 'invalid_table' not found",
  "details": {
    "line": 1,
    "column": 15
  }
}
```

**Frontend Usage:** QueryLabPage "Validate" button

**Notes:**
- Should perform syntax and semantic validation
- Fast response required (<500ms preferred)
- No actual query execution

---

### Metrics Explorer Endpoints

#### 10. List All Metrics
```
GET /api/metrics-explorer/metrics
```

**Response:**
```json
{
  "metrics": [
    {
      "id": "metric_001",
      "name": "Total Conversations",
      "description": "Count of all conversations",
      "type": "simple",
      "category": "Customer",
      "model_name": "amp_metrics",
      "aggregation": "count",
      "created_at": "2025-11-01T10:00:00Z"
    },
    {
      "id": "metric_002",
      "name": "Average Resolution Time",
      "description": "Average time to resolve conversations",
      "type": "derived",
      "category": "Operations",
      "model_name": "amp_metrics",
      "aggregation": "avg",
      "created_at": "2025-11-02T10:00:00Z"
    }
  ],
  "total_count": 2
}
```

**Frontend Usage:** MetricsExplorerPage initial load

---

#### 11. Search Metrics
```
GET /api/metrics-explorer/search?query={query}&category={category}
```

**Query Parameters:**
- `query` (optional): Search text
- `category` (optional): Filter by category (Revenue, Customer, Product, Operations)

**Response:**
```json
{
  "metrics": [
    {
      "id": "metric_001",
      "name": "Total Conversations",
      "description": "Count of all conversations",
      "type": "simple",
      "category": "Customer",
      "model_name": "amp_metrics",
      "aggregation": "count",
      "match_score": 0.95
    }
  ],
  "total_count": 1,
  "search_query": "conversation",
  "category_filter": "Customer"
}
```

**Frontend Usage:** MetricsExplorerPage search and filter

**Notes:**
- Should search in name, description, and tags
- Case-insensitive search
- Support partial matches
- Return results ranked by relevance (match_score)

---

## Priority 3: MEDIUM (Required for Phase 4 - ModelsPage)

### Semantic Models Endpoints

#### 12. List Models
```
GET /api/models/?category={category}
```

**Query Parameters:**
- `category` (optional): production, staging, development (default: production)

**Response:**
```json
{
  "models": [
    {
      "id": "model_001",
      "name": "amp_metrics",
      "description": "AMP analytics metrics and dimensions",
      "category": "production",
      "entity_count": 3,
      "dimension_count": 15,
      "measure_count": 8,
      "metric_count": 12,
      "created_at": "2025-10-01T10:00:00Z",
      "updated_at": "2025-11-10T14:30:00Z"
    }
  ],
  "total_count": 1
}
```

**Frontend Usage:** ModelsPage model list

---

#### 13. Get Model Details
```
GET /api/models/{model_id}?category={category}
```

**Path Parameters:**
- `model_id` (required): Model identifier

**Query Parameters:**
- `category` (optional): production, staging, development (default: production)

**Response:**
```json
{
  "id": "model_001",
  "name": "amp_metrics",
  "description": "AMP analytics metrics and dimensions",
  "category": "production",
  "model": "production.gold.amp_all_events_v2",
  "entities": [
    {
      "name": "conversation",
      "description": "Conversation entity",
      "expr": "conversation_id",
      "primary": true
    }
  ],
  "dimensions": [
    {
      "name": "event_source",
      "description": "Source system of the event",
      "type": "categorical",
      "expr": "event_source"
    }
  ],
  "measures": [
    {
      "name": "event_count",
      "description": "Count of events",
      "agg": "count",
      "expr": "1"
    }
  ],
  "metrics": [
    {
      "name": "total_conversations",
      "description": "Total number of conversations",
      "type": "simple",
      "type_params": {
        "measure": "event_count"
      }
    }
  ],
  "created_at": "2025-10-01T10:00:00Z",
  "updated_at": "2025-11-10T14:30:00Z"
}
```

**Frontend Usage:** ModelDetailModal display

---

#### 14. Create Model
```
POST /api/models/
```

**Request Body:**
```json
{
  "name": "new_model",
  "description": "New semantic model",
  "category": "development",
  "model": "production.gold.my_table",
  "entities": [...],
  "dimensions": [...],
  "measures": [...],
  "metrics": [...]
}
```

**Response:**
```json
{
  "id": "model_002",
  "name": "new_model",
  "message": "Model created successfully"
}
```

**Frontend Usage:** ModelsPage create action

---

#### 15. Update Model
```
PUT /api/models/{model_id}
```

**Path Parameters:**
- `model_id` (required): Model identifier

**Request Body:**
```json
{
  "description": "Updated description",
  "dimensions": [...],
  "metrics": [...]
}
```

**Response:**
```json
{
  "id": "model_001",
  "message": "Model updated successfully"
}
```

**Frontend Usage:** ModelDetailModal save action

---

#### 16. Delete Model
```
DELETE /api/models/{model_id}
```

**Path Parameters:**
- `model_id` (required): Model identifier

**Response:**
```json
{
  "message": "Model deleted successfully"
}
```

**Frontend Usage:** ModelsPage delete action

**Notes:**
- Should require confirmation
- Should check if model is being used before deleting

---

#### 17. Download Model YAML
```
GET /api/models/{model_id}/download
```

**Path Parameters:**
- `model_id` (required): Model identifier

**Response:**
- Content-Type: `application/x-yaml` or `text/yaml`
- File download with name: `{model_name}.yml`

**Frontend Usage:** ModelsPage download action

---

## Priority 4: LOW (Required for Phase 5 - Advanced Features)

### Catalog Endpoints (for AI Model Generation)

#### 18. Get Gold Tables
```
GET /api/catalog/gold-tables
```

**Response:**
```json
{
  "tables": [
    {
      "catalog": "production",
      "schema": "gold",
      "name": "amp_all_events_v2",
      "row_count": 1500000,
      "column_count": 25,
      "has_semantic_model": false
    }
  ]
}
```

**Frontend Usage:** AutoModelGeneration component - table selection

---

#### 19. Analyze Table
```
POST /api/catalog/analyze-table
```

**Request Body:**
```json
{
  "catalog": "production",
  "schema": "gold",
  "table": "amp_all_events_v2"
}
```

**Response:**
```json
{
  "table": "production.gold.amp_all_events_v2",
  "row_count": 1500000,
  "columns": [...],
  "sample_data": [...],
  "suggested_entities": ["conversation_id", "tenant_id"],
  "suggested_dimensions": ["event_source", "event_name"],
  "suggested_measures": ["event_count", "unique_conversations"]
}
```

**Frontend Usage:** AutoModelGeneration component - analysis step

---

#### 20. Generate Model
```
POST /api/catalog/generate-model
```

**Request Body:**
```json
{
  "analysis": {...},
  "model_name": "generated_model",
  "selected_dimensions": ["event_source", "event_name"],
  "selected_measures": ["event_count"],
  "customizations": {...}
}
```

**Response:**
```json
{
  "model": {...},
  "yaml": "semantic_models:\n  - name: generated_model\n    ..."
}
```

**Frontend Usage:** AutoModelGeneration component - generation step

---

### Documentation Endpoints

#### 21. Generate Documentation
```
POST /api/documentation/generate
```

**Request Body:**
```json
{
  "model_id": "model_001",
  "format": "markdown"
}
```

**Request Parameters:**
- `model_id` (required): Model identifier
- `format` (required): markdown, html, pdf

**Response:**
```json
{
  "documentation": "# Model: amp_metrics\n\n...",
  "format": "markdown",
  "generated_at": "2025-11-12T10:00:00Z"
}
```

**Frontend Usage:** DocumentationPage generate action

---

#### 22. List Documentation
```
GET /api/documentation/models
```

**Response:**
```json
{
  "models": [
    {
      "model_id": "model_001",
      "model_name": "amp_metrics",
      "has_documentation": true,
      "last_generated": "2025-11-10T10:00:00Z"
    }
  ]
}
```

**Frontend Usage:** DocumentationPage model list

---

### Lineage Endpoints

#### 23. Get Table Lineage
```
GET /api/lineage/tables/{catalog}.{schema}.{table}
```

**Path Parameters:**
- `catalog`, `schema`, `table`: Table identifier

**Response:**
```json
{
  "table": "production.gold.amp_all_events_v2",
  "upstream": [
    {
      "table": "production.silver.amp_events",
      "type": "table"
    }
  ],
  "downstream": [
    {
      "model": "amp_metrics",
      "type": "semantic_model"
    }
  ]
}
```

**Frontend Usage:** LineageVisualizationPage graph

---

#### 24. Get Model Lineage
```
GET /api/lineage/models/{model_id}
```

**Path Parameters:**
- `model_id` (required): Model identifier

**Response:**
```json
{
  "model": "amp_metrics",
  "source_tables": [
    "production.gold.amp_all_events_v2"
  ],
  "dependent_models": [],
  "dependent_dashboards": []
}
```

**Frontend Usage:** LineageVisualizationPage graph

---

## Global Requirements

### CORS Configuration

**Required Headers:**
```
Access-Control-Allow-Origin: http://localhost:3000
Access-Control-Allow-Methods: GET, POST, PUT, DELETE, OPTIONS
Access-Control-Allow-Headers: Content-Type, Authorization
Access-Control-Max-Age: 3600
```

**Note:** In production, configure appropriate origin domain

---

### Error Response Format

All error responses should follow this format:

```json
{
  "status": "error",
  "error": "Human-readable error message",
  "error_code": "ERROR_CODE",
  "details": {
    "field": "Additional context"
  },
  "timestamp": "2025-11-12T10:00:00Z"
}
```

**Common Error Codes:**
- `VALIDATION_ERROR` (400)
- `UNAUTHORIZED` (401)
- `FORBIDDEN` (403)
- `NOT_FOUND` (404)
- `INTERNAL_ERROR` (500)
- `DATABRICKS_ERROR` (502)

---

### Authentication

**Question for Backend PM:** Is authentication required?

If yes, expected flow:
1. Frontend sends Databricks token
2. Backend validates and returns JWT
3. Frontend includes JWT in Authorization header for all subsequent requests

**Request Header:**
```
Authorization: Bearer {jwt_token}
```

---

### Rate Limiting

**Question for Backend PM:** Are there rate limits?

If yes, include in response headers:
```
X-RateLimit-Limit: 1000
X-RateLimit-Remaining: 999
X-RateLimit-Reset: 1699876543
```

---

## Testing & Mock Data

### Mock Server Setup

For frontend development before backend is ready, we'll use:
- MSW (Mock Service Worker) for API mocking
- Mock data generators for realistic test data

**Request:** Can Backend PM provide sample response data for critical endpoints?

---

## Communication Protocol

### API Questions/Issues
- Use GitHub issues with label `api-contract`
- Tag Backend PM for urgent questions
- Expected response time: 4 hours for blockers, 24 hours for clarifications

### API Changes
- Backend PM must notify Frontend PM 24 hours before breaking changes
- Use semantic versioning for API (v1, v2)
- Include deprecation warnings in responses

### Development Coordination
- Backend endpoints ready notification via Slack
- Frontend testing feedback via GitHub issues
- Weekly sync meeting to review progress

---

## Priority Schedule

### Week 1 (Phase 2-3)
**Required by Backend:**
- [ ] Health endpoints (1-2)
- [ ] Metadata endpoints (3-7)
- [ ] Query execution endpoint (8)
- [ ] Metrics list endpoint (10)

### Week 2 (Phase 4)
**Required by Backend:**
- [ ] Query validation endpoint (9)
- [ ] Metrics search endpoint (11)
- [ ] All Semantic Models endpoints (12-17)

### Week 3 (Phase 5)
**Required by Backend:**
- [ ] Catalog endpoints (18-20)
- [ ] Documentation endpoints (21-22)
- [ ] Lineage endpoints (23-24)

---

## Open Questions for Backend PM

1. **Authentication:**
   - Is authentication required for API access?
   - If yes, what's the auth flow and token format?

2. **Databricks Token:**
   - Should users provide their own Databricks token?
   - Or does backend use service account?

3. **Rate Limiting:**
   - Are there rate limits on API endpoints?
   - What are the limits per endpoint?

4. **WebSocket Support:**
   - Any plans for real-time updates (query status, health changes)?
   - Or should we use polling?

5. **Pagination:**
   - Which endpoints need pagination?
   - What's the pagination format (offset/limit, cursor, page number)?

6. **Query Execution:**
   - Maximum query execution time?
   - How to handle long-running queries?
   - Support for query cancellation?

7. **Error Handling:**
   - Specific error codes we should handle differently?
   - Retry strategy for transient errors?

---

**Please review and confirm API contract. Let me know if any adjustments needed!**
