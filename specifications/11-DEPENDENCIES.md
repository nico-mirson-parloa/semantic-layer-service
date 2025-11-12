# Dependencies Specification

**Document Version:** 1.0
**Last Updated:** 2025-11-04

---

## Backend Dependencies

### Core Framework & Server

| Package | Version | Purpose | Critical |
|---------|---------|---------|----------|
| `fastapi` | 0.104.1 | Modern async web framework | ✅ Yes |
| `uvicorn[standard]` | 0.24.0 | ASGI server with WebSocket support | ✅ Yes |
| `pydantic` | 2.5.2 | Data validation using Python type hints | ✅ Yes |
| `pydantic-settings` | 2.1.0 | Settings management from environment | ✅ Yes |

**Justification:**
- FastAPI provides automatic API documentation, async support, and excellent performance
- Uvicorn is the recommended ASGI server with production-ready features
- Pydantic V2 offers significant performance improvements over V1

### Databricks Integration

| Package | Version | Purpose | Critical |
|---------|---------|---------|----------|
| `databricks-sql-connector` | 3.0.2 | SQL Warehouse connectivity | ✅ Yes |
| `databricks-sdk` | 0.18.0 | Workspace API client | ✅ Yes |

**Justification:**
- Official Databricks libraries ensure compatibility and support
- SQL connector provides connection pooling and async capabilities
- SDK enables Unity Catalog and Genie API access

### Data Processing & Parsing

| Package | Version | Purpose | Critical |
|---------|---------|---------|----------|
| `pyyaml` | 6.0.1 | YAML semantic model parsing | ✅ Yes |
| `jinja2` | 3.1.2 | Template engine for documentation | Yes |
| `sqlparse` | 0.4.4 | SQL query parsing and formatting | Yes |
| `pyparsing` | 3.1.1 | Parser library for SQL translation | Yes |

### HTTP & Communication

| Package | Version | Purpose | Critical |
|---------|---------|---------|----------|
| `httpx` | 0.25.2 | Modern async HTTP client | Yes |
| `requests` | 2.31.0 | Traditional HTTP library (for compatibility) | Yes |
| `python-multipart` | 0.0.6 | Form data and file upload handling | Yes |

### Authentication & Security

| Package | Version | Purpose | Critical |
|---------|---------|---------|----------|
| `python-jose[cryptography]` | 3.3.0 | JWT token creation and verification | ✅ Yes |
| `passlib[bcrypt]` | 1.7.4 | Password hashing (future use) | No |

**Security Note:**
- JWT tokens expire after 30 minutes
- Tokens are verified against Databricks API on each login
- All passwords should use bcrypt hashing when implemented

### Logging & Monitoring

| Package | Version | Purpose | Critical |
|---------|---------|---------|----------|
| `structlog` | 23.2.0 | Structured logging with JSON output | Yes |
| `rich` | 13.7.0 | Rich terminal formatting and pretty printing | No |

### SQL API (PostgreSQL Protocol)

| Package | Version | Purpose | Critical |
|---------|---------|---------|----------|
| `asyncpg` | 0.29.0 | Async PostgreSQL driver for wire protocol | Yes |

### Configuration & Environment

| Package | Version | Purpose | Critical |
|---------|---------|---------|----------|
| `python-dotenv` | 1.0.0 | Load environment variables from .env files | Yes |

### Development & Testing

| Package | Version | Purpose | Critical |
|---------|---------|---------|----------|
| `pytest` | 7.4.3 | Testing framework | ✅ Yes |
| `pytest-asyncio` | 0.21.1 | Async test support | ✅ Yes |
| `black` | 23.11.0 | Code formatter | Yes |
| `isort` | 5.12.0 | Import sorting | Yes |
| `mypy` | 1.7.1 | Static type checker | Yes |

---

## Frontend Dependencies

### Core Framework

| Package | Version | Purpose | Critical |
|---------|---------|---------|----------|
| `react` | ^18.2.0 | UI framework | ✅ Yes |
| `react-dom` | ^18.2.0 | React DOM renderer | ✅ Yes |
| `typescript` | ^4.9.5 | Type safety | ✅ Yes |
| `react-scripts` | 5.0.1 | Build tooling (CRA) | ✅ Yes |

**Version Notes:**
- React 18 introduces concurrent rendering and automatic batching
- TypeScript 4.9 provides satisfies operator and improved type inference

### Routing

| Package | Version | Purpose | Critical |
|---------|---------|---------|----------|
| `react-router-dom` | ^6.18.0 | Client-side routing | ✅ Yes |

**Migration Note:**
- React Router v6 uses new API (useNavigate vs useHistory)
- Simplified route configuration

### State Management & Data Fetching

| Package | Version | Purpose | Critical |
|---------|---------|---------|----------|
| `@tanstack/react-query` | ^5.8.4 | Server state management | ✅ Yes |
| `axios` | ^1.6.2 | HTTP client | ✅ Yes |

**Why React Query v5?**
- Automatic caching and background refetching
- Optimistic updates support
- Significantly reduces boilerplate vs Redux
- Better developer experience with DevTools

### UI Component Libraries

| Package | Version | Purpose | Critical |
|---------|---------|---------|----------|
| `@mui/material` | ^5.16.7 | Material Design components | Yes |
| `@mui/icons-material` | ^5.16.7 | Material Design icons | Yes |
| `@emotion/react` | ^11.14.0 | CSS-in-JS (MUI dependency) | Yes |
| `@emotion/styled` | ^11.14.1 | Styled components (MUI dependency) | Yes |
| `@headlessui/react` | ^2.2.7 | Unstyled accessible components | No |
| `@heroicons/react` | ^2.0.18 | Icon library | No |

**Justification:**
- Material-UI provides production-ready complex components
- Emotion is required by MUI v5
- HeadlessUI offers flexibility for custom-styled components

### Styling

| Package | Version | Purpose | Critical |
|---------|---------|---------|----------|
| `tailwindcss` | ^3.3.6 | Utility-first CSS framework | ✅ Yes |
| `autoprefixer` | ^10.4.16 | PostCSS plugin for browser prefixes | Yes |
| `postcss` | ^8.4.31 | CSS transformation tool | Yes |
| `@tailwindcss/forms` | ^0.5.7 | Better form styling | No |

### Data Visualization

| Package | Version | Purpose | Critical |
|---------|---------|---------|----------|
| `reactflow` | ^11.11.4 | Interactive node-based graphs (lineage) | ✅ Yes |
| `recharts` | ^2.8.0 | Chart library | Yes |
| `d3` | ^7.9.0 | Data visualization primitives | Yes |

**Use Cases:**
- ReactFlow: Data lineage visualization with draggable nodes
- Recharts: Metric trend charts and dashboards
- D3: Custom visualizations and transformations

### Form Handling

| Package | Version | Purpose | Critical |
|---------|---------|---------|----------|
| `react-hook-form` | ^7.47.0 | Performant form validation | Yes |

**Why react-hook-form?**
- Minimal re-renders
- Built-in validation
- Excellent TypeScript support

### Code Display & Markdown

| Package | Version | Purpose | Critical |
|---------|---------|---------|----------|
| `react-syntax-highlighter` | ^15.5.0 | SQL syntax highlighting | Yes |
| `react-markdown` | ^10.1.0 | Markdown rendering (documentation) | Yes |

### Utilities

| Package | Version | Purpose | Critical |
|---------|---------|---------|----------|
| `lodash` | ^4.17.21 | Utility functions (debounce, etc.) | Yes |
| `lucide-react` | ^0.294.0 | Modern icon library | No |

### Type Definitions

| Package | Version | Purpose | Critical |
|---------|---------|---------|----------|
| `@types/react` | ^18.2.37 | React type definitions | ✅ Yes |
| `@types/react-dom` | ^18.2.15 | React DOM type definitions | ✅ Yes |
| `@types/node` | ^20.9.0 | Node.js type definitions | Yes |
| `@types/lodash` | ^4.17.20 | Lodash type definitions | Yes |
| `@types/d3` | ^7.4.3 | D3 type definitions | Yes |
| `@types/react-syntax-highlighter` | ^15.5.10 | Syntax highlighter types | Yes |

### Development Tools

| Package | Version | Purpose | Critical |
|---------|---------|---------|----------|
| `ajv` | ^8.17.1 | JSON schema validation | No |
| `web-vitals` | ^3.5.0 | Performance metrics | No |

---

## Version Constraints & Compatibility

### Python Version
**Required:** Python 3.11+

**Reasoning:**
- Improved performance (up to 25% faster than 3.10)
- Better error messages
- Native support for async improvements
- Pydantic V2 requires 3.11+

**Compatibility:**
```python
# pyproject.toml or setup.py
python_requires = ">=3.11"
```

### Node.js Version
**Required:** Node.js 18+

**Reasoning:**
- LTS version with long-term support
- Native fetch API
- Improved performance
- Required by React 18

**Compatibility:**
```json
{
  "engines": {
    "node": ">=18.0.0",
    "npm": ">=9.0.0"
  }
}
```

---

## Dependency Installation

### Backend Setup

```bash
# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Development installation
pip install -e .
```

### Frontend Setup

```bash
# Install dependencies
cd frontend
npm install

# Or with specific registry
npm install --registry=https://registry.npmjs.org/
```

---

## Security Considerations

### Backend

1. **Pin Major Versions:** Critical packages are pinned to specific versions
2. **Regular Updates:** Review security advisories monthly
3. **Vulnerability Scanning:**
   ```bash
   pip install safety
   safety check
   ```

### Frontend

1. **npm audit:** Run regularly
   ```bash
   npm audit
   npm audit fix
   ```

2. **Dependabot:** Enable GitHub Dependabot for automated PRs

---

## Breaking Changes to Watch

### FastAPI 0.x → 1.0 (Future)
- May require middleware updates
- Dependency injection changes possible

### React 18 → 19 (Future)
- Already using new APIs
- Should be smooth upgrade

### Pydantic V2 → V3 (Future)
- Currently on V2 (major rewrite from V1)
- Migration guide will be provided by Pydantic team

### Material-UI v5 → v6 (Future)
- Emotion remains CSS-in-JS solution
- Theme API may evolve

---

## Optional Dependencies

### Backend

```bash
# For enhanced debugging
pip install ipdb pdbpp

# For profiling
pip install py-spy

# For documentation generation
pip install mkdocs mkdocs-material
```

### Frontend

```bash
# For bundle analysis
npm install --save-dev webpack-bundle-analyzer

# For testing
npm install --save-dev @testing-library/react @testing-library/jest-dom

# For storybook (component development)
npx sb init
```

---

## Dependency Justification Matrix

### Backend

| Category | Primary Choice | Alternatives Considered | Decision Rationale |
|----------|----------------|------------------------|-------------------|
| Web Framework | FastAPI | Flask, Django, Express (Node) | Async-first, automatic docs, type safety |
| Data Validation | Pydantic V2 | Marshmallow, Cerberus | Performance, type hints, FastAPI integration |
| YAML Parser | PyYAML | ruamel.yaml | Simpler API, sufficient for our use case |
| HTTP Client | httpx | aiohttp, requests | Async support, requests-like API |
| JWT Library | python-jose | PyJWT | More features, better documented |
| Testing | pytest | unittest | Better fixtures, plugins, async support |

### Frontend

| Category | Primary Choice | Alternatives Considered | Decision Rationale |
|----------|----------------|------------------------|-------------------|
| Framework | React | Vue, Angular, Svelte | Largest ecosystem, team familiarity |
| State Management | React Query | Redux, Zustand, Recoil | Purpose-built for server state |
| Styling | Tailwind + MUI | Styled Components, Chakra UI | Speed + completeness |
| Data Viz | ReactFlow | cytoscape.js, vis.js | Best for interactive graphs |
| HTTP Client | Axios | fetch, ky | Interceptors, better error handling |

---

## Maintenance Schedule

- **Monthly:** Review security advisories, apply patches
- **Quarterly:** Evaluate minor version upgrades
- **Bi-Annually:** Consider major version upgrades
- **Annually:** Review all dependencies for replacements/improvements

---

**Next Steps:**
1. Review `09-DEPLOYMENT.md` for infrastructure requirements
2. See `10-TESTING-STRATEGY.md` for test dependencies
3. Refer to `03-BACKEND-SPECIFICATION.md` and `04-FRONTEND-SPECIFICATION.md` for usage patterns
