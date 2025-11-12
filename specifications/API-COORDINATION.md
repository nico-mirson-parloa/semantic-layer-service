# API Coordination - Frontend ↔ Backend

**Created by:** Frontend Project Manager
**For:** Backend Project Manager
**Date:** 2025-11-12
**Status:** Pending Backend Confirmation

---

## Purpose

This document outlines the API contracts that the frontend requires from the backend. It serves as a coordination point between Frontend and Backend teams to ensure smooth integration.

---

## API Contract Requirements

### Base Configuration

```
Base URL (Development): http://localhost:8000
Base URL (Production): https://api.semanticlayer.yourdomain.com

Authentication: Bearer Token (JWT)
Header: Authorization: Bearer <token>

Content-Type: application/json
Accept: application/json
```

### CORS Requirements

**Development:**
- Allow origin: `http://localhost:3000`
- Allow methods: `GET, POST, PUT, DELETE, OPTIONS`
- Allow headers: `Content-Type, Authorization`
- Allow credentials: `true`

**Production:**
- Configure based on deployment URL

---

## Critical Endpoints (Priority 1 - Week 1)

These endpoints are needed immediately for core functionality.

### 1. Health & Status

```
GET /api/health/
Response: {
  status: "healthy" | "degraded" | "unhealthy",
  version: string,
  databricks_connected: boolean,
  checks: {
    database: boolean,
    cache: boolean,
    external_apis: boolean
  }
}
```

```
GET /api/health/databricks
Response: {
  connected: boolean,
  workspace_url?: string,
  error?: string
}
```

### 2. Authentication

```
POST /api/auth/login
Request: {
  databricks_token: string
}
Response: {
  access_token: string,
  token_type: "bearer",
  user: {
    id: string,
    email: string,
    display_name: string,
    roles: string[],
    permissions: string[]
  }
}
```

```
GET /api/auth/me
Headers: Authorization: Bearer <token>
Response: {
  id: string,
  email: string,
  display_name: string,
  roles: string[],
  permissions: string[]
}
```

### 3. Metadata Discovery

```
GET /api/metadata/catalogs
Response: {
  catalogs: [
    {
      name: string,
      comment?: string,
      created_at?: string
    }
  ]
}
```

```
GET /api/metadata/schemas?catalog=<catalog_name>
Response: {
  schemas: [
    {
      name: string,
      catalog: string,
      comment?: string
    }
  ]
}
```

```
GET /api/metadata/tables?catalog=<catalog>&schema=<schema>
Response: {
  tables: [
    {
      name: string,
      catalog: string,
      schema: string,
      table_type: "TABLE" | "VIEW" | "MATERIALIZED_VIEW",
      row_count?: number,
      size_bytes?: number,
      comment?: string,
      created_at?: string,
      updated_at?: string
    }
  ]
}
```

```
GET /api/metadata/columns?catalog=<catalog>&schema=<schema>&table=<table>
Response: {
  columns: [
    {
      name: string,
      data_type: string,
      nullable: boolean,
      comment?: string,
      is_partition_key?: boolean
    }
  ]
}
```

### 4. Query Execution

```
POST /api/queries/execute
Request: {
  query: string,
  limit?: number,
  warehouse_id?: string
}
Response: {
  columns: string[],
  rows: Record<string, any>[],
  row_count: number,
  execution_time_ms: number,
  statement_id?: string
}
```

```
POST /api/queries/validate
Request: {
  query: string
}
Response: {
  is_valid: boolean,
  errors: string[],
  warnings: string[]
}
```

### 5. Semantic Models (Basic CRUD)

```
GET /api/models/?category=<production|staging|development>
Response: {
  models: [
    {
      name: string,
      description?: string,
      model: string,
      version?: string,
      entities: Entity[],
      dimensions: Dimension[],
      measures: Measure[],
      metrics?: Metric[]
    }
  ]
}
```

```
GET /api/models/<model_id>?category=<category>
Response: {
  name: string,
  description?: string,
  model: string,
  version?: string,
  entities: Entity[],
  dimensions: Dimension[],
  measures: Measure[],
  metrics?: Metric[]
}
```

```
POST /api/models/
Request: {
  name: string,
  description?: string,
  model: string,
  entities: Entity[],
  dimensions: Dimension[],
  measures: Measure[],
  metrics?: Metric[]
}
Response: {
  id: string,
  message: "Model created successfully"
}
```

```
PUT /api/models/<model_id>
Request: (Same as POST)
Response: {
  message: "Model updated successfully"
}
```

```
DELETE /api/models/<model_id>
Response: {
  message: "Model deleted successfully"
}
```

```
GET /api/models/<model_id>/download
Response: Blob (YAML file)
Content-Type: application/x-yaml
Content-Disposition: attachment; filename="<model_id>.yml"
```

---

## Important Endpoints (Priority 2 - Week 2)

### 6. Metrics Explorer

```
GET /api/metrics-explorer/metrics
Response: {
  metrics: [
    {
      id: string,
      name: string,
      description?: string,
      type: "simple" | "ratio" | "derived",
      model_name: string,
      category?: string
    }
  ]
}
```

```
GET /api/metrics-explorer/search?query=<query>&category=<category>
Response: (Same structure as above)
```

### 7. Catalog (For Auto-Generation)

```
GET /api/catalog/gold-tables
Response: {
  tables: [
    {
      name: string,
      catalog: string,
      schema: string,
      row_count: number,
      column_count: number,
      comment?: string
    }
  ]
}
```

```
POST /api/catalog/analyze-table
Request: {
  catalog: string,
  schema: string,
  table: string
}
Response: {
  table_info: {
    name: string,
    catalog: string,
    schema: string,
    columns: Column[]
  },
  analysis: {
    suggested_entities: string[],
    suggested_dimensions: string[],
    suggested_measures: string[],
    suggested_metrics: string[]
  }
}
```

```
POST /api/catalog/generate-model
Request: {
  analysis: { ... },
  model_name: string,
  description?: string,
  customizations?: {
    selected_dimensions: string[],
    selected_measures: string[],
    selected_metrics: string[]
  }
}
Response: {
  model: SemanticModel,
  yaml_content: string
}
```

---

## Advanced Endpoints (Priority 3 - Week 3)

### 8. Documentation

```
POST /api/documentation/generate
Request: {
  model_id: string,
  format: "markdown" | "html" | "pdf"
}
Response: {
  content: string,
  download_url?: string
}
```

```
GET /api/documentation/models
Response: {
  models: [
    {
      model_id: string,
      model_name: string,
      has_documentation: boolean,
      last_generated?: string
    }
  ]
}
```

### 9. Lineage

```
GET /api/lineage/tables/<catalog>.<schema>.<table>
Response: {
  table: {
    name: string,
    catalog: string,
    schema: string
  },
  upstream: [
    {
      name: string,
      catalog: string,
      schema: string,
      type: "TABLE" | "VIEW"
    }
  ],
  downstream: [
    {
      name: string,
      catalog: string,
      schema: string,
      type: "TABLE" | "VIEW"
    }
  ]
}
```

```
GET /api/lineage/models/<model_id>
Response: {
  model: {
    name: string,
    id: string
  },
  source_tables: [
    {
      catalog: string,
      schema: string,
      table: string
    }
  ],
  dependencies: {
    upstream_models: string[],
    downstream_dashboards: string[]
  }
}
```

### 10. Genie (Natural Language)

```
POST /api/genie/query
Request: {
  query: string (natural language)
}
Response: {
  sql: string,
  result: QueryResult,
  confidence: number
}
```

```
POST /api/genie/suggest-metrics
Request: {
  table_info: {
    catalog: string,
    schema: string,
    table: string,
    columns: Column[]
  }
}
Response: {
  suggestions: [
    {
      name: string,
      description: string,
      type: "simple" | "ratio",
      definition: string
    }
  ]
}
```

### 11. SQL Autocomplete

```
GET /api/metadata/sql-autocomplete?prefix=<prefix>
Response: {
  suggestions: [
    {
      value: string,
      type: "table" | "column" | "keyword" | "function",
      description?: string,
      schema?: string
    }
  ]
}
```

---

## Error Response Format

All error responses should follow this structure:

```json
{
  "detail": "Human-readable error message",
  "status_code": 400 | 401 | 403 | 404 | 500,
  "timestamp": "2025-11-12T10:30:00Z",
  "error_code": "OPTIONAL_ERROR_CODE",
  "field_errors": {
    "field_name": ["error message 1", "error message 2"]
  }
}
```

### HTTP Status Codes

- `200 OK` - Successful GET, PUT, DELETE
- `201 Created` - Successful POST (resource creation)
- `204 No Content` - Successful DELETE (no response body)
- `400 Bad Request` - Invalid request data
- `401 Unauthorized` - Missing or invalid authentication
- `403 Forbidden` - Valid auth but insufficient permissions
- `404 Not Found` - Resource not found
- `422 Unprocessable Entity` - Validation errors
- `500 Internal Server Error` - Server-side error

---

## Data Type Definitions

### Entity
```typescript
{
  name: string,
  type: string,
  description?: string,
  expr?: string,
  role?: string
}
```

### Dimension
```typescript
{
  name: string,
  type: "categorical" | "time",
  description?: string,
  expr?: string,
  label?: string
}
```

### Measure
```typescript
{
  name: string,
  agg: "sum" | "count" | "avg" | "min" | "max" | "count_distinct",
  description?: string,
  expr?: string,
  label?: string
}
```

### Metric
```typescript
{
  name: string,
  description?: string,
  type: "simple" | "ratio" | "derived",
  type_params?: {
    numerator?: string,
    denominator?: string,
    expr?: string,
    measures?: string[]
  },
  label?: string,
  filter?: string
}
```

---

## Questions for Backend PM

### Authentication & Security
1. **Q:** What authentication method are we using? JWT, OAuth, Databricks token passthrough?
   - **Frontend needs:** JWT token with expiration time, refresh token flow if applicable

2. **Q:** What permissions/roles are supported?
   - **Frontend needs:** List of roles (admin, analyst, viewer) and permissions for UI feature gating

3. **Q:** How long are tokens valid?
   - **Frontend needs:** Token expiration time to handle refresh or re-login

### API Behavior
4. **Q:** Do we support pagination for large result sets?
   - **Frontend needs:** Confirm pagination structure if applicable:
     ```json
     {
       "data": [],
       "total": 1000,
       "page": 1,
       "page_size": 50
     }
     ```

5. **Q:** What are the rate limits for API endpoints?
   - **Frontend needs:** Rate limit info to implement client-side throttling

6. **Q:** Do query executions return results immediately or require polling?
   - **Frontend needs:** If async, provide status endpoint: `GET /api/queries/<query_id>/status`

7. **Q:** Is there WebSocket support for real-time query progress?
   - **Frontend needs:** WebSocket URL and message format if applicable

### Data Formats
8. **Q:** What timestamp format do you use?
   - **Frontend needs:** Prefer ISO 8601 (e.g., `2025-11-12T10:30:00Z`)

9. **Q:** How are null values represented in query results?
   - **Frontend needs:** Confirm `null` vs `"null"` vs empty string

10. **Q:** Are model IDs UUIDs or names?
    - **Frontend needs:** Confirm ID format for URL routing

### File Operations
11. **Q:** Is there a model upload endpoint for YAML files?
    - **Frontend needs:** `POST /api/models/upload` with multipart/form-data support

12. **Q:** Can we export query results to CSV/Excel?
    - **Frontend needs:** Export endpoint with format parameter

### Advanced Features
13. **Q:** Does the backend support batch operations?
    - **Frontend needs:** Endpoint to delete/update multiple models at once

14. **Q:** Is there a search/filter API for models?
    - **Frontend needs:** `GET /api/models/search?query=X&filters=Y`

---

## Testing Coordination

### Mock Data Needed
- Sample catalog/schema/table data for development
- Sample semantic model YAML files
- Sample query results with various data types

### Shared Testing Environment
- **Development API:** `http://localhost:8000`
- **Staging API:** TBD
- **Test Databricks Workspace:** TBD

### Integration Testing
- Coordinate on end-to-end test scenarios
- Share Postman/Insomnia collections
- Define test data sets

---

## Timeline Coordination

| Week | Frontend Focus | Backend Dependencies |
|------|----------------|---------------------|
| Week 1 | Core infrastructure, authentication, basic CRUD | Health, Auth, Metadata, Query, Models (basic) |
| Week 2 | Metrics Explorer, Catalog browsing | Metrics API, Catalog API |
| Week 3 | Auto-generation, Lineage, Documentation | Genie, Lineage, Documentation APIs |

---

## Communication Protocol

### Daily Sync
- Quick 15-min standup to discuss blockers
- Share API changes immediately via Slack/Teams

### API Changes
- Notify frontend team 24 hours before breaking changes
- Use semantic versioning for API (`/api/v1/`, `/api/v2/`)
- Maintain backward compatibility during transition periods

### Documentation
- Keep API reference (06-API-REFERENCE.md) updated
- Use OpenAPI/Swagger spec for automatic documentation

---

## Action Items for Backend PM

- [ ] Review and confirm all endpoint specifications
- [ ] Answer the 14 questions in "Questions for Backend PM" section
- [ ] Provide OpenAPI/Swagger spec if available
- [ ] Set up CORS for `http://localhost:3000`
- [ ] Create sample mock data for frontend development
- [ ] Confirm authentication flow and token format
- [ ] Confirm error response format
- [ ] Set up shared testing environment
- [ ] Schedule daily sync meeting

---

## Action Items for Frontend PM (Me)

- [ ] Wait for Backend PM confirmation on API contracts
- [ ] Update frontend implementation plan based on feedback
- [ ] Create mock API responses for frontend development
- [ ] Set up API integration tests
- [ ] Document any frontend-specific requirements

---

**Status:** Awaiting Backend PM review and confirmation
**Next Update:** After Backend PM responds

---

**Contact:**
- Frontend PM: [Your contact info]
- Backend PM: [Backend PM contact info]
