# Project Overview - Semantic Layer Service

**Document Version:** 1.0
**Last Updated:** 2025-11-04

---

## Executive Summary

The **Semantic Layer Service** is a modern, AI-powered platform that provides a unified semantic layer on top of Databricks data lakehouse. It enables business users, analysts, and engineers to interact with data through business-friendly metrics and dimensions while maintaining a single source of truth.

### Key Value Propositions

1. **Unified Metrics Layer**: Single source of truth for business metrics across the organization
2. **Natural Language Access**: Query data using natural language via Databricks Genie integration
3. **AI-Powered Automation**: Automatic semantic model generation from existing transformations
4. **Universal BI Connectivity**: PostgreSQL-compatible SQL API for any BI tool
5. **Data Governance**: Built-in lineage tracking, documentation, and access control

---

## Business Requirements

### Primary Use Cases

#### 1. Business Analyst Workflow
**Goal:** Query data without writing SQL

- Browse available metrics and dimensions via UI
- Ask natural language questions (e.g., "Show me revenue by region for Q4")
- Execute queries and visualize results
- Save and share queries with team members

#### 2. Data Engineer Workflow
**Goal:** Define and maintain semantic models

- Analyze gold layer tables for metric opportunities
- Generate semantic models with AI assistance
- Define custom metrics with business logic
- Track data lineage from source to metric
- Generate documentation automatically

#### 3. BI Tool Integration
**Goal:** Connect existing BI tools to semantic layer

- Connect Tableau/Power BI/Preset via SQL interface
- Query semantic models as if they were database tables
- Leverage pre-defined metrics and dimensions
- Benefit from consistent business definitions

#### 4. Executive Dashboard Creation
**Goal:** Build dashboards with certified metrics

- Access only approved, governed metrics
- Ensure consistency across all reports
- Track metric usage and adoption
- Understand data lineage for compliance

### Non-Functional Requirements

| Requirement | Target | Priority |
|-------------|--------|----------|
| **Response Time** | <2s for metadata queries, <5s for data queries | High |
| **Availability** | 99.5% uptime during business hours | High |
| **Scalability** | Support 100+ concurrent users | Medium |
| **Security** | Role-based access control, Databricks SSO | High |
| **Data Freshness** | Reflect source data within 5 minutes | Medium |
| **Browser Support** | Chrome, Firefox, Safari (latest 2 versions) | High |

---

## High-Level Architecture

### System Context

```
┌─────────────────────────────────────────────────────────────┐
│                     External Systems                        │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐  │
│  │ Tableau  │  │Power BI  │  │  Preset  │  │  Excel   │  │
│  └────┬─────┘  └────┬─────┘  └────┬─────┘  └────┬─────┘  │
│       │             │              │              │         │
│       └─────────────┴──────────────┴──────────────┘         │
│                           │ SQL Protocol (PostgreSQL)       │
└───────────────────────────┼─────────────────────────────────┘
                            │
┌───────────────────────────┼─────────────────────────────────┐
│               Semantic Layer Service                        │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌─────────────────┐           ┌─────────────────┐         │
│  │  React Frontend │◄─────────►│  FastAPI Backend│         │
│  │  (Port 3000)    │   REST    │  (Port 8000)    │         │
│  └─────────────────┘   API     └────────┬────────┘         │
│                                          │                  │
│                                ┌─────────┴────────┐         │
│                                │   SQL API Server │         │
│                                │   (Port 5433)    │         │
│                                └──────────────────┘         │
└───────────────────────────────┼─────────────────────────────┘
                                │
┌───────────────────────────────┼─────────────────────────────┐
│                    Databricks Platform                      │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌────────────────┐  ┌────────────────┐  ┌──────────────┐ │
│  │ SQL Warehouses │  │ Unity Catalog  │  │    Genie     │ │
│  │  (Compute)     │  │  (Metadata +   │  │  (NL to SQL) │ │
│  │                │  │   Storage)     │  │              │ │
│  └────────────────┘  └────────────────┘  └──────────────┘ │
│                                                             │
│  ┌────────────────────────────────────────────────────────┐ │
│  │         Gold Layer Tables (Delta Format)              │ │
│  └────────────────────────────────────────────────────────┘ │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### Component Responsibilities

#### React Frontend
- **Purpose:** User interface for all personas
- **Key Features:**
  - Metrics explorer and search
  - SQL query lab with autocomplete
  - AI-powered model generation wizard
  - Data lineage visualization
  - Documentation viewer
- **Technology:** React 18, TypeScript, Tailwind CSS, Material-UI

#### FastAPI Backend
- **Purpose:** Business logic, API orchestration, AI integration
- **Key Features:**
  - REST API for all operations
  - Databricks integration layer
  - Authentication & authorization
  - Semantic model parsing and storage
  - LLM-powered analysis
- **Technology:** Python 3.11+, FastAPI, Pydantic

#### SQL API Server
- **Purpose:** PostgreSQL-compatible interface for BI tools
- **Key Features:**
  - Wire protocol implementation
  - Virtual schema management
  - Query translation to semantic models
  - Standard JDBC/ODBC connectivity
- **Technology:** Python asyncpg, custom protocol handler

#### Databricks Platform
- **Purpose:** Data storage, compute, and AI services
- **Components:**
  - **SQL Warehouses:** Query execution engine
  - **Unity Catalog:** Metadata management and Volumes storage
  - **Genie:** Natural language to SQL conversion
  - **Foundation Models:** LLM-based table analysis

---

## Technology Decisions

### Backend Technology: FastAPI (Python)

**Why FastAPI?**
- Native async support for high concurrency
- Automatic OpenAPI documentation generation
- Strong type safety with Pydantic
- Excellent performance (comparable to Node.js, Go)
- Rich ecosystem for data/ML workflows
- Native integration with Databricks Python SDK

**Alternatives Considered:**
- Node.js + Express: Lacks strong typing, weaker ML ecosystem
- Django: Too heavyweight, not async-first
- Go: Steeper learning curve, less ML/data tooling

### Frontend Technology: React + TypeScript

**Why React?**
- Large talent pool and community
- Rich ecosystem of libraries (ReactFlow, Recharts)
- Excellent performance with virtual DOM
- Strong TypeScript support
- Component reusability

**Why TypeScript?**
- Type safety for large codebase
- Better IDE support and refactoring
- Catches errors at compile time
- Self-documenting code

**Alternatives Considered:**
- Vue.js: Smaller ecosystem
- Angular: Too opinionated, steeper learning curve
- Svelte: Smaller community, fewer libraries

### State Management: React Query + Local State

**Why React Query?**
- Purpose-built for server state
- Built-in caching and invalidation
- Reduces boilerplate dramatically
- Excellent developer experience

**Why Not Redux?**
- Overkill for this application
- React Query handles 90% of state needs
- Local useState sufficient for UI state

### Styling: Tailwind CSS + Material-UI

**Why This Combination?**
- Tailwind: Utility-first for rapid development
- Material-UI: Complex components (modals, tables, autocomplete)
- Best of both worlds: speed + completeness

### Data Storage: Unity Catalog Volumes

**Why Volumes?**
- Native Databricks integration
- Built-in governance and access control
- File-based (YAML) for git-friendly version control
- No separate database to manage
- Cost-effective for this use case

**Why Not Traditional Database?**
- Semantic models are small files (KBs)
- Infrequent writes, frequent reads (cache-friendly)
- Already have Databricks infrastructure
- Simplified deployment and operations

---

## Data Flow Architecture

### Read Path (Query Execution)

```
User Action
    ↓
Frontend (React)
    ↓
API Request (axios)
    ↓
FastAPI Backend
    ↓
Parse Semantic Model (from cache or Volume)
    ↓
Generate SQL from Model Definition
    ↓
Databricks SQL Warehouse
    ↓
Execute Against Gold Layer
    ↓
Return Results
    ↓
Frontend Visualization
```

### Write Path (Model Creation)

```
User Selects Table
    ↓
Frontend AI Model Wizard
    ↓
API Request to Analyze Table
    ↓
Backend: Fetch Table Metadata
    ↓
LLM Analysis (Databricks Foundation Model)
    ↓
Generate Metric Suggestions
    ↓
Return to Frontend
    ↓
User Customizes Model
    ↓
API Request to Save Model
    ↓
Backend: Generate YAML
    ↓
Write to Unity Catalog Volume
    ↓
Update Cache
    ↓
Confirm to User
```

### BI Tool Query Path

```
BI Tool (e.g., Tableau)
    ↓
PostgreSQL JDBC Connection
    ↓
SQL API Server (Port 5433)
    ↓
Parse SQL Query
    ↓
Identify Semantic Model from Virtual Schema
    ↓
Translate SQL to Semantic Query
    ↓
FastAPI Backend (Internal Call)
    ↓
Execute Against Databricks
    ↓
Return Results via PostgreSQL Protocol
    ↓
BI Tool Renders Visualization
```

---

## Security Architecture

### Authentication Flow

```
1. User navigates to application
2. Frontend redirects to Databricks OAuth
3. User authenticates with Databricks credentials
4. Databricks returns OAuth token
5. Frontend sends token to backend
6. Backend verifies token with Databricks API
7. Backend extracts user info and group membership
8. Backend maps groups to roles (Admin, Analyst, Viewer)
9. Backend generates JWT with user + roles + permissions
10. Frontend stores JWT in localStorage
11. All subsequent requests include JWT in Authorization header
```

### Authorization Model

**Roles:**
- **System Admin:** Full access to all features
- **Data Engineer:** Create/edit models, run queries
- **Analyst:** Run queries, view models
- **Viewer:** View models only (read-only)

**Permissions:**
- VOLUME_READ, VOLUME_WRITE, VOLUME_ADMIN
- METRIC_READ, METRIC_CREATE, METRIC_UPDATE, METRIC_APPROVE
- QUERY_EXECUTE, QUERY_SAVE
- SYSTEM_ADMIN

**Enforcement:**
- Backend: Decorator-based permission checks on endpoints
- Frontend: Conditional UI rendering based on user permissions
- Databricks: Native Unity Catalog ACLs for Volume access

---

## Scalability Considerations

### Horizontal Scaling
- **Frontend:** Static files served via CDN (future)
- **Backend:** Stateless, can run multiple instances behind load balancer
- **SQL API:** Can scale independently via multiple instances

### Caching Strategy
- **Semantic Models:** In-memory cache with 30-minute TTL
- **Metadata:** Short cache (5 minutes) for catalog/schema/table lists
- **Query Results:** Optional user-configurable caching

### Performance Optimization
- **Lazy Loading:** Metadata tree loads on-demand
- **Pagination:** All list endpoints support pagination
- **Debouncing:** Search and autocomplete requests debounced
- **Query Optimization:** LIMIT clauses on preview queries

---

## Success Metrics

### Adoption Metrics
- Number of active users (daily/weekly/monthly)
- Number of semantic models created
- Number of queries executed
- Number of BI tool connections

### Performance Metrics
- Average query response time
- API endpoint response times (p50, p95, p99)
- Cache hit rate
- Error rate

### Business Metrics
- Reduction in ad-hoc SQL queries
- Increase in self-service analytics
- Time to create new dashboards
- Metric reuse rate

---

## Risks and Mitigations

| Risk | Impact | Probability | Mitigation |
|------|--------|-------------|------------|
| Databricks API changes | High | Low | Version pinning, integration tests |
| Genie API rate limits | Medium | Medium | Fallback to rule-based SQL generation |
| Performance degradation with scale | High | Medium | Caching, query optimization, monitoring |
| Security vulnerabilities | High | Low | Regular security audits, penetration testing |
| User adoption challenges | High | Medium | Training, documentation, champion program |

---

## Future Roadmap

### Phase 1 (Completed): Foundation
- ✅ Basic semantic layer functionality
- ✅ Databricks integration
- ✅ React UI for metrics and queries

### Phase 2 (Completed): AI Features
- ✅ Automatic model generation
- ✅ Natural language to SQL (Genie)
- ✅ Data lineage visualization
- ✅ Documentation generation

### Phase 3 (Current): Enterprise Features
- ✅ SQL API for BI tools
- ✅ Preset integration
- 🚧 Advanced caching strategies
- 🚧 Multi-tenant support

### Phase 4 (Planned): Advanced Analytics
- 📋 Pre-aggregation tables
- 📋 Incremental refresh
- 📋 Real-time metrics
- 📋 Advanced monitoring and alerting

### Phase 5 (Planned): Platform Expansion
- 📋 API rate limiting and quotas
- 📋 Metric approval workflows
- 📋 A/B testing for metric definitions
- 📋 Cross-organization metric marketplace

---

## Glossary

- **Semantic Layer:** Abstraction layer that provides business-friendly view of data
- **Metric:** Quantitative measurement (e.g., revenue, user count)
- **Dimension:** Attribute for grouping/filtering (e.g., region, product category)
- **Measure:** Aggregatable field (e.g., amount, quantity)
- **Entity:** Primary or foreign key for joins
- **Unity Catalog:** Databricks unified governance solution
- **Gold Layer:** Curated, business-ready tables in medallion architecture
- **Semantic Model:** YAML definition of metrics, dimensions, and relationships

---

## References

- [Databricks Unity Catalog Documentation](https://docs.databricks.com/en/data-governance/unity-catalog/index.html)
- [dbt Semantic Layer](https://docs.getdbt.com/docs/use-dbt-semantic-layer/dbt-semantic-layer) (Design inspiration)
- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [React Query Documentation](https://tanstack.com/query/latest)

---

**Next:** Proceed to `02-SYSTEM-ARCHITECTURE.md` for detailed architectural diagrams and component interactions.
