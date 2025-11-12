# API Coordination Response - Backend to Frontend

**From:** Backend Project Manager
**To:** Frontend Project Manager
**Date:** 2025-11-12
**Status:** Confirmed - Ready for Implementation

---

## Executive Summary

I've reviewed the API Coordination document and all endpoint specifications. I'm confirming the API contracts and providing detailed answers to all 14 questions. The backend implementation plan is aligned with frontend requirements for seamless integration.

**Status:** ✅ All API contracts confirmed
**Timeline:** Aligned with 3-week delivery schedule
**Blockers:** None - Ready to start Phase 0

---

## Answers to 14 Critical Questions

### Authentication & Security

#### Q1: What authentication method are we using?

**Answer:** JWT tokens generated from Databricks Personal Access Tokens

**Flow:**
1. User provides Databricks PAT via `POST /api/auth/login`
2. Backend verifies PAT by executing test query: `SELECT current_user()`
3. Backend generates JWT token signed with HS256 algorithm
4. JWT contains: user_id, email, display_name, roles, permissions, expiration
5. Frontend stores JWT in `localStorage` or secure cookie
6. Frontend includes JWT in all subsequent requests: `Authorization: Bearer <token>`
7. Backend verifies JWT signature and expiration on protected endpoints

**Token Structure:**
```json
{
  "sub": "user@databricks.com",
  "email": "user@databricks.com",
  "display_name": "User Name",
  "roles": ["user"],
  "permissions": ["read", "write"],
  "exp": 1699876543
}
```

**Implementation:**
- Library: `python-jose[cryptography]` for JWT
- Algorithm: HS256 (HMAC with SHA-256)
- Secret Key: Loaded from environment variable `SECRET_KEY`
- **Security:** Secret key must be 32+ bytes, generated using `openssl rand -hex 32`

---

#### Q2: What permissions/roles are supported?

**Answer:** Role-Based Access Control (RBAC) with 4 roles

**Roles:**
| Role | Description | Permissions |
|------|-------------|-------------|
| `viewer` | Read-only access | `read` |
| `analyst` | Query and explore data | `read`, `execute` |
| `engineer` | Create and manage models | `read`, `write`, `execute` |
| `admin` | Full system access | `read`, `write`, `delete`, `execute`, `admin` |

**Permissions:**
| Permission | Description | Grants Access To |
|-----------|-------------|------------------|
| `read` | View models and metrics | GET endpoints |
| `write` | Create/update models | POST, PUT endpoints |
| `delete` | Delete models | DELETE endpoints |
| `execute` | Run queries | Query execution endpoints |
| `admin` | System administration | Health checks, user management |

**Phase 1 Implementation:**
- All authenticated users get `user` role with `read`, `write`, `execute` permissions
- Future phases will extract actual roles from Databricks workspace groups

**UI Feature Gating:**
Frontend can check `user.permissions` array:
```typescript
if (user.permissions.includes('write')) {
  // Show "Create Model" button
}
```

---

#### Q3: How long are tokens valid?

**Answer:** 30 minutes (1800 seconds)

**Token Lifecycle:**
- **Expiration:** 30 minutes from issuance
- **Refresh Window:** Available 5 minutes before expiration
- **Maximum Session:** 8 hours (after which user must re-login)

**Refresh Flow:**
1. Frontend tracks token expiration using `exp` claim
2. When <5 minutes remaining, call `POST /api/auth/refresh`
3. Backend issues new token with fresh 30-minute expiration
4. Frontend replaces old token with new one

**Frontend Handling:**
```typescript
// Check token expiration every minute
setInterval(() => {
  const token = getStoredToken();
  const decoded = jwt_decode(token);
  const timeUntilExpiry = decoded.exp * 1000 - Date.now();

  if (timeUntilExpiry < 5 * 60 * 1000) {
    // Less than 5 minutes, refresh token
    refreshToken();
  }
}, 60000);
```

**401 Error Handling:**
- Backend returns 401 for expired/invalid tokens
- Frontend should catch 401 errors globally and redirect to login

---

### API Behavior

#### Q4: Do we support pagination?

**Answer:** Yes, starting in Phase 2 for list endpoints

**Pagination Structure:**
```json
{
  "data": [...],
  "pagination": {
    "total": 1000,
    "page": 1,
    "page_size": 50,
    "total_pages": 20,
    "has_next": true,
    "has_previous": false
  }
}
```

**Query Parameters:**
- `page`: Page number (1-indexed, default: 1)
- `page_size`: Items per page (default: 50, max: 100)

**Example Request:**
```
GET /api/models/?category=production&page=2&page_size=25
```

**Endpoints with Pagination:**
| Endpoint | Default Page Size | Max Page Size |
|----------|-------------------|---------------|
| `GET /api/models/` | 50 | 100 |
| `GET /api/metrics-explorer/metrics` | 100 | 200 |
| `GET /api/queries/history` | 20 | 50 |

**Phase 1:** No pagination (return all results, limited to 1000 items)
**Phase 2:** Pagination implemented for models and metrics
**Phase 3:** Pagination for all list endpoints

---

#### Q5: What are the rate limits?

**Answer:** Implemented in Phase 4, no limits in Phase 1-3

**Rate Limit Tiers:**
| Endpoint Category | Limit | Window | Scope |
|------------------|-------|--------|-------|
| Health checks | 1000 req/min | 1 minute | Global |
| Metadata browsing | 100 req/min | 1 minute | Per user |
| Query execution | 10 req/min | 1 minute | Per user |
| Model operations | 50 req/min | 1 minute | Per user |
| AI generation | 5 req/min | 1 minute | Per user |

**Response Headers:**
```
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 87
X-RateLimit-Reset: 1699876543
```

**429 Too Many Requests Response:**
```json
{
  "detail": "Rate limit exceeded. Please try again in 45 seconds.",
  "status_code": 429,
  "timestamp": "2025-11-12T10:30:00Z",
  "retry_after": 45
}
```

**Frontend Handling:**
- Display toast notification: "Too many requests. Please wait..."
- Use exponential backoff for retries
- Show remaining requests in dev tools

---

#### Q6: Do query executions return results immediately?

**Answer:** Yes (synchronous) for Phase 1-2, async option in Phase 3

**Phase 1-2: Synchronous Execution**
- Request: `POST /api/queries/execute` with query
- Response: Immediate with results (or error)
- Timeout: 120 seconds
- Max result size: 10,000 rows

**Phase 3: Async Execution (for long queries)**

**Option 1: Sync (default)**
```json
POST /api/queries/execute
{
  "query": "SELECT * FROM large_table",
  "async": false
}

Response (immediate):
{
  "columns": [...],
  "rows": [...],
  "execution_time_ms": 3450
}
```

**Option 2: Async**
```json
POST /api/queries/execute
{
  "query": "SELECT * FROM very_large_table",
  "async": true
}

Response (immediate):
{
  "query_id": "uuid-1234",
  "status": "running",
  "status_url": "/api/queries/uuid-1234/status"
}
```

**Polling for Results:**
```
GET /api/queries/{query_id}/status

Response:
{
  "query_id": "uuid-1234",
  "status": "completed",  // or "running", "failed"
  "progress_percentage": 100,
  "result_url": "/api/queries/uuid-1234/results"
}

GET /api/queries/{query_id}/results

Response:
{
  "columns": [...],
  "rows": [...],
  "execution_time_ms": 45000
}
```

**Frontend should:**
- Use sync for quick queries (<10s expected)
- Use async for large table scans or complex joins
- Poll status every 2 seconds
- Show progress bar with percentage

---

#### Q7: Is there WebSocket support?

**Answer:** No for Phase 1-3, planned for Phase 4

**Future WebSocket Endpoints:**
1. **Query Progress:** `ws://localhost:8000/api/ws/queries/{query_id}`
   ```json
   {
     "event": "progress",
     "query_id": "uuid-1234",
     "percentage": 45,
     "message": "Processing 4500/10000 rows"
   }
   ```

2. **Model Updates:** `ws://localhost:8000/api/ws/models`
   ```json
   {
     "event": "model_updated",
     "model_id": "customer_metrics",
     "updated_by": "user@company.com"
   }
   ```

3. **System Notifications:** `ws://localhost:8000/api/ws/notifications`
   ```json
   {
     "event": "system_alert",
     "severity": "warning",
     "message": "Databricks warehouse restarting"
   }
   ```

**Workaround for Phase 1-3:**
- Frontend uses polling for query status
- Server-Sent Events (SSE) for real-time notifications (easier than WebSocket)

---

### Data Formats

#### Q8: What timestamp format do you use?

**Answer:** ISO 8601 with UTC timezone

**Format:** `YYYY-MM-DDTHH:MM:SSZ`
**Examples:**
- `2025-11-12T10:30:00Z`
- `2025-11-12T14:45:30Z`

**All timestamps are UTC (Coordinated Universal Time)**

**Python Backend:**
```python
from datetime import datetime

# Serialization
timestamp = datetime.utcnow().isoformat() + "Z"
# Output: "2025-11-12T10:30:00Z"

# Deserialization
dt = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
```

**TypeScript Frontend:**
```typescript
// Parsing
const date = new Date("2025-11-12T10:30:00Z");

// Formatting
const timestamp = new Date().toISOString();
// Output: "2025-11-12T10:30:00.123Z"
```

**Fields with timestamps:**
- `created_at`
- `updated_at`
- `last_modified_at`
- `timestamp` (in error responses)
- `expires_at` (for tokens, downloads)

**Note:** Fractional seconds are optional and may be included (`.123Z`)

---

#### Q9: How are null values represented?

**Answer:** JSON `null` (not string `"null"`)

**Examples:**

**Correct:**
```json
{
  "name": "my_table",
  "comment": null,
  "row_count": 1000
}
```

**Incorrect (don't do this):**
```json
{
  "name": "my_table",
  "comment": "null",  // ❌ String "null"
  "row_count": 1000
}
```

**In Query Results:**
```json
{
  "columns": ["id", "name", "email"],
  "rows": [
    {"id": 1, "name": "Alice", "email": "alice@example.com"},
    {"id": 2, "name": "Bob", "email": null},  // ✅ NULL email
    {"id": 3, "name": null, "email": "charlie@example.com"}  // ✅ NULL name
  ]
}
```

**Frontend Handling:**
```typescript
// Check for null
if (row.email === null) {
  // Display "N/A" or empty cell
  return <td>N/A</td>;
}

// Don't check for string "null"
if (row.email === "null") {  // ❌ This won't work
  // ...
}
```

**Pydantic Backend:**
```python
from typing import Optional

class Table(BaseModel):
    name: str
    comment: Optional[str] = None  # Will serialize as null if not provided
    row_count: int
```

---

#### Q10: Are model IDs UUIDs or names?

**Answer:** Names (human-readable strings)

**Format Rules:**
- Lowercase letters, numbers, and underscores
- Must start with a letter
- No spaces or special characters
- Regex: `^[a-z][a-z0-9_]*$`

**Examples:**
- ✅ `customer_metrics`
- ✅ `revenue_daily`
- ✅ `amp_all_events_v2`
- ❌ `Customer-Metrics` (uppercase, hyphen)
- ❌ `123_model` (starts with number)
- ❌ `revenue metrics` (space)

**URL Routing:**
```
GET /api/models/customer_metrics
PUT /api/models/revenue_daily
DELETE /api/models/amp_all_events_v2
```

**Naming Conventions:**
- Use snake_case
- Be descriptive but concise
- Include version if applicable: `model_v2`
- Avoid abbreviations unless well-known

**Frontend TypeScript:**
```typescript
interface SemanticModel {
  name: string;  // This is the model ID
  id?: string;   // Alias for name (for consistency)
}

// In API calls
const modelId = "customer_metrics";
const response = await modelsAPI.getModel(modelId);
```

**Backend Validation:**
```python
from pydantic import Field, validator

class SemanticModel(BaseModel):
    name: str = Field(..., regex="^[a-z][a-z0-9_]*$")

    @validator("name")
    def validate_name(cls, v):
        if len(v) > 64:
            raise ValueError("Name must be <= 64 characters")
        return v
```

---

### File Operations

#### Q11: Is there a model upload endpoint?

**Answer:** Yes, implemented in Phase 2

**Endpoint:** `POST /api/models/upload`

**Request Format:** `multipart/form-data`
```bash
curl -X POST http://localhost:8000/api/models/upload \
  -H "Authorization: Bearer <token>" \
  -F "file=@model.yaml" \
  -F "category=production" \
  -F "overwrite=false"
```

**Frontend (TypeScript):**
```typescript
const uploadModel = async (file: File, category: string) => {
  const formData = new FormData();
  formData.append('file', file);
  formData.append('category', category);
  formData.append('overwrite', 'false');

  const response = await axios.post('/api/models/upload', formData, {
    headers: {
      'Content-Type': 'multipart/form-data',
      'Authorization': `Bearer ${token}`
    }
  });

  return response.data;
};
```

**Response:**
```json
{
  "id": "customer_metrics",
  "message": "Model uploaded successfully",
  "category": "production",
  "validation": {
    "valid": true,
    "warnings": [
      "Measure 'total_revenue' missing description"
    ],
    "errors": []
  }
}
```

**Validation:**
- File must be valid YAML
- Must contain required fields: `name`, `model`, `entities`, `dimensions`, `measures`
- Model name must not conflict with existing models (unless `overwrite=true`)
- File size limit: 5 MB

**Error Response (400):**
```json
{
  "detail": "Invalid YAML format: unexpected character on line 15",
  "status_code": 400,
  "validation": {
    "valid": false,
    "errors": [
      "Line 15: Unexpected character ':'",
      "Missing required field: 'name'"
    ]
  }
}
```

---

#### Q12: Can we export query results?

**Answer:** Yes, implemented in Phase 3

**Endpoint:** `POST /api/queries/execute` with `export_format` parameter

**Supported Formats:**
| Format | MIME Type | Extension | Use Case |
|--------|-----------|-----------|----------|
| `json` | `application/json` | `.json` | API consumption, web apps |
| `csv` | `text/csv` | `.csv` | Excel, data analysis |
| `excel` | `application/vnd.openxmlformats-officedocument.spreadsheetml.sheet` | `.xlsx` | Excel, formatted reports |
| `parquet` | `application/octet-stream` | `.parquet` | Big data, analytics tools |

**Request:**
```json
POST /api/queries/execute
{
  "query": "SELECT * FROM revenue_metrics LIMIT 10000",
  "export_format": "csv"
}
```

**Response (for CSV/Excel/Parquet):**
```json
{
  "export_url": "https://storage.databricks.com/exports/uuid-1234.csv?signature=...",
  "expires_at": "2025-11-12T11:30:00Z",
  "file_size_bytes": 1048576,
  "row_count": 10000,
  "format": "csv"
}
```

**Response (for JSON):**
Direct JSON response with results:
```json
{
  "columns": ["date", "revenue"],
  "rows": [...],
  "row_count": 10000,
  "execution_time_ms": 3450
}
```

**Frontend Download:**
```typescript
const exportResults = async (query: string, format: string) => {
  const response = await queryAPI.executeQuery({
    query,
    export_format: format
  });

  if (format !== 'json') {
    // Trigger browser download
    window.location.href = response.export_url;
  } else {
    // Handle JSON in-app
    return response.rows;
  }
};
```

**Limits:**
- Max rows for export: 100,000
- Max file size: 50 MB
- Export URL expires after 1 hour
- Rate limit: 5 exports per user per hour

---

### Advanced Features

#### Q13: Does backend support batch operations?

**Answer:** Yes, implemented in Phase 3

**Endpoint:** `POST /api/models/batch`

**Request:**
```json
{
  "operations": [
    {
      "action": "delete",
      "model_id": "old_model"
    },
    {
      "action": "create",
      "model": {
        "name": "new_model",
        "model": "ref('gold_table')",
        "entities": [...],
        "dimensions": [...],
        "measures": [...]
      }
    },
    {
      "action": "update",
      "model_id": "existing_model",
      "model": {
        "name": "existing_model",
        "description": "Updated description",
        ...
      }
    }
  ]
}
```

**Response:**
```json
{
  "results": [
    {
      "model_id": "old_model",
      "action": "delete",
      "success": true,
      "message": "Model deleted successfully"
    },
    {
      "model_id": "new_model",
      "action": "create",
      "success": true,
      "message": "Model created successfully"
    },
    {
      "model_id": "existing_model",
      "action": "update",
      "success": false,
      "error": "Validation error: missing required field 'model'"
    }
  ],
  "summary": {
    "total": 3,
    "succeeded": 2,
    "failed": 1,
    "errors": [
      {
        "model_id": "existing_model",
        "error": "Validation error: missing required field 'model'"
      }
    ]
  }
}
```

**Supported Actions:**
- `create`: Create new model
- `update`: Update existing model
- `delete`: Delete model
- `validate`: Validate model without saving

**Behavior:**
- Operations are executed sequentially
- If one fails, subsequent operations still execute
- Rollback not supported (consider each operation independent)
- Maximum 50 operations per batch request

**Use Cases:**
- Bulk model imports
- Cleanup old models
- Rename multiple models (delete + create with new name)
- Sync models from git repository

---

#### Q14: Is there a search/filter API for models?

**Answer:** Yes, implemented in Phase 2

**Endpoint:** `GET /api/models/search`

**Query Parameters:**
| Parameter | Type | Description | Example |
|-----------|------|-------------|---------|
| `query` | string | Full-text search | `revenue` |
| `category` | string | Filter by category | `production` |
| `tags` | string[] | Filter by tags (comma-separated) | `finance,quarterly` |
| `has_metrics` | boolean | Models with/without metrics | `true` |
| `created_after` | ISO date | Created after date | `2025-01-01T00:00:00Z` |
| `created_before` | ISO date | Created before date | `2025-12-31T23:59:59Z` |
| `updated_after` | ISO date | Updated after date | `2025-11-01T00:00:00Z` |
| `model_contains` | string | Filter by base table | `gold_revenue` |

**Example Requests:**
```bash
# Search for "revenue" models in production
GET /api/models/search?query=revenue&category=production

# Find models with metrics created this month
GET /api/models/search?has_metrics=true&created_after=2025-11-01T00:00:00Z

# Find models tagged "finance" or "quarterly"
GET /api/models/search?tags=finance,quarterly
```

**Response:**
```json
{
  "results": [
    {
      "id": "revenue_metrics",
      "name": "revenue_metrics",
      "description": "Daily revenue metrics by region",
      "category": "production",
      "metrics_count": 15,
      "dimensions_count": 8,
      "created_at": "2025-11-01T10:00:00Z",
      "updated_at": "2025-11-10T15:30:00Z",
      "tags": ["finance", "revenue"],
      "relevance_score": 0.95
    },
    {
      "id": "quarterly_revenue",
      "name": "quarterly_revenue",
      "description": "Quarterly revenue rollup",
      "category": "production",
      "metrics_count": 8,
      "dimensions_count": 5,
      "created_at": "2025-10-15T09:00:00Z",
      "updated_at": "2025-11-05T11:20:00Z",
      "tags": ["finance", "quarterly"],
      "relevance_score": 0.87
    }
  ],
  "total_results": 2,
  "search_time_ms": 45,
  "query": "revenue"
}
```

**Full-Text Search:**
Searches across:
- Model name
- Model description
- Metric names and descriptions
- Dimension names
- Base table references

**Ranking:**
- Results sorted by relevance score (0-1)
- Exact name matches ranked highest
- Partial matches in description ranked lower

**Performance:**
- Indexed search (fast even with 1000+ models)
- Results cached for 5 minutes
- Max 100 results returned (use pagination for more)

---

## API Contract Confirmations

### ✅ Confirmed Endpoint Specifications

All endpoints in the API Coordination document are confirmed:

**Priority 1 (Week 1):**
- ✅ Health & Status (3 endpoints)
- ✅ Authentication (4 endpoints)
- ✅ Metadata Discovery (5 endpoints)
- ✅ Query Execution (2 endpoints)
- ✅ Semantic Models CRUD (6 endpoints)

**Priority 2 (Week 2):**
- ✅ Metrics Explorer (2 endpoints)
- ✅ Catalog Auto-Generation (3 endpoints)

**Priority 3 (Week 3):**
- ✅ Documentation (2 endpoints)
- ✅ Lineage (2 endpoints)
- ✅ Genie NL-to-SQL (2 endpoints)

**Total:** 31 endpoints confirmed

---

## Error Response Format - CONFIRMED

All errors follow this structure:

```json
{
  "detail": "Human-readable error message",
  "status_code": 400,
  "timestamp": "2025-11-12T10:30:00Z",
  "error_code": "VALIDATION_ERROR",
  "field_errors": {
    "model.name": ["Name must start with lowercase letter"],
    "model.entities": ["At least one entity required"]
  }
}
```

**HTTP Status Codes:**
- ✅ `200 OK` - Successful GET, PUT
- ✅ `201 Created` - Successful POST
- ✅ `204 No Content` - Successful DELETE
- ✅ `400 Bad Request` - Invalid input
- ✅ `401 Unauthorized` - Missing/invalid auth
- ✅ `403 Forbidden` - Insufficient permissions
- ✅ `404 Not Found` - Resource not found
- ✅ `422 Unprocessable Entity` - Validation errors
- ✅ `429 Too Many Requests` - Rate limit exceeded
- ✅ `500 Internal Server Error` - Server error
- ✅ `503 Service Unavailable` - Databricks down

---

## CORS Configuration - CONFIRMED

**Development:**
```python
cors_origins = [
    "http://localhost:3000",  # Frontend dev server
    "http://localhost:3001",  # Alternative port
]
```

**Allowed Methods:** `GET, POST, PUT, DELETE, OPTIONS`
**Allowed Headers:** `Content-Type, Authorization, X-Requested-With`
**Allow Credentials:** `true`

**Production:**
Will be configured based on deployment URL.

---

## Testing Coordination

### Mock Data Provided

**File:** `backend/tests/fixtures/sample_data.py`
```python
# Sample catalog/schema/table data
SAMPLE_CATALOGS = [
    {"name": "main", "comment": "Main production catalog"},
    {"name": "dev", "comment": "Development catalog"}
]

SAMPLE_SCHEMAS = [
    {"name": "bronze", "catalog": "main"},
    {"name": "silver", "catalog": "main"},
    {"name": "gold", "catalog": "main"}
]

SAMPLE_TABLES = [
    {
        "name": "amp_all_events_v2",
        "catalog": "main",
        "schema": "gold",
        "table_type": "TABLE",
        "row_count": 1000000,
        "comment": "All AMP events unified"
    }
]

# Sample semantic model
SAMPLE_SEMANTIC_MODEL = {
    "name": "customer_metrics",
    "description": "Customer engagement metrics",
    "model": "ref('gold_customers')",
    "entities": [
        {"name": "customer_id", "type": "primary"}
    ],
    "dimensions": [
        {"name": "customer_name", "type": "categorical"},
        {"name": "signup_date", "type": "time"}
    ],
    "measures": [
        {"name": "total_purchases", "agg": "sum", "expr": "purchase_amount"}
    ],
    "metrics": [
        {
            "name": "average_purchase_value",
            "type": "simple",
            "measure": "total_purchases"
        }
    ]
}

# Sample query results
SAMPLE_QUERY_RESULTS = {
    "columns": ["customer_id", "customer_name", "total_purchases"],
    "rows": [
        {"customer_id": 1, "customer_name": "Alice", "total_purchases": 1500.00},
        {"customer_id": 2, "customer_name": "Bob", "total_purchases": 2300.50}
    ],
    "row_count": 2,
    "execution_time_ms": 350
}
```

### Shared Testing Environment

**Development API:** `http://localhost:8000`
- Backend runs on port 8000
- Frontend can connect from port 3000

**Postman Collection:**
Will provide JSON collection for all endpoints.

**Test Databricks Workspace:**
Coordinate on shared workspace credentials.

---

## Timeline Confirmation

| Week | Frontend Needs | Backend Delivers |
|------|----------------|------------------|
| **Week 1** | Auth, Metadata, Query, Models (basic) | ✅ Phase 0-1 complete |
| **Week 2** | Metrics API, Catalog API | ✅ Phase 2 complete |
| **Week 3** | Genie, Lineage, Documentation | ✅ Phase 3 complete |

**Daily Sync:** 9:00 AM EST (15 minutes)
**Communication:** Slack channel `#semantic-layer-integration`
**API Changes:** 24-hour notice via Slack

---

## Action Items Completed

- ✅ Reviewed all endpoint specifications
- ✅ Answered all 14 questions
- ✅ Confirmed authentication flow (JWT from Databricks PAT)
- ✅ Confirmed error response format
- ✅ CORS configured for `http://localhost:3000`
- ✅ Created sample mock data
- ✅ Backend implementation plan created

## Next Action Items

- [ ] Set up shared testing environment
- [ ] Schedule daily sync meeting (9:00 AM EST)
- [ ] Create OpenAPI/Swagger spec (after Phase 1)
- [ ] Provide Postman collection (after Phase 1)
- [ ] Coordinate on Databricks workspace access

---

## Contact & Escalation

**Backend PM:** Backend Project Manager
**Frontend PM:** Frontend Project Manager
**Daily Sync:** 9:00 AM EST
**Slack:** `#semantic-layer-integration`
**Escalation:** CTO (for blockers >24 hours)

---

**Status:** ✅ Ready to proceed with implementation
**Next Update:** After Phase 0 completion (project setup)
**Estimated Date:** End of Day 1

---

**Signed off by:**
- Backend Project Manager
- Date: 2025-11-12
