# Frontend Implementation Plan - Semantic Layer Service

**Document Version:** 1.0
**Date:** 2025-11-12
**Project Manager:** Frontend PM
**Developer:** Frontend Developer (pane below)

---

## Executive Summary

This plan outlines the phased implementation of the React-based frontend for the Semantic Layer Service. The implementation is broken down into 5 phases, starting with project setup and core infrastructure, then building out key pages, and finally adding advanced features.

**Technology Stack:**
- React 18 + TypeScript
- React Router v6
- TanStack Query (React Query)
- Tailwind CSS + Material-UI
- Axios for HTTP clients
- Create React App

---

## Phase 1: Project Setup & Core Infrastructure (Priority: CRITICAL)

### Objectives
- Initialize React application
- Set up routing foundation
- Configure build tools and dependencies
- Establish API client architecture

### Tasks

#### 1.1 Initialize React Application
```bash
npx create-react-app frontend --template typescript
cd frontend
```

#### 1.2 Install Core Dependencies
```bash
npm install react-router-dom @tanstack/react-query axios
npm install @mui/material @mui/icons-material @emotion/react @emotion/styled
npm install tailwindcss postcss autoprefixer @tailwindcss/forms
npm install --save-dev @types/node
```

#### 1.3 Configure Tailwind CSS
**File:** `frontend/tailwind.config.js`
```javascript
module.exports = {
  content: ['./src/**/*.{js,jsx,ts,tsx}'],
  theme: {
    extend: {
      colors: {
        primary: {
          50: '#eff6ff',
          500: '#3b82f6',
          700: '#1d4ed8',
        },
      },
    },
  },
  plugins: [require('@tailwindcss/forms')],
};
```

**File:** `frontend/src/index.css`
```css
@tailwind base;
@tailwind components;
@tailwind utilities;
```

#### 1.4 Create Directory Structure
```
frontend/src/
├── index.tsx                    # Entry point
├── App.tsx                      # Main router + layout
├── pages/                       # Page components (create empty files)
│   ├── HomePage.tsx
│   ├── MetricsExplorerPage.tsx
│   ├── MetadataPage.tsx
│   ├── QueryLabPage.tsx
│   ├── ModelsPage.tsx
│   ├── MetricBuilderPage.tsx
│   ├── DocumentationPage.tsx
│   └── LineageVisualizationPage.tsx
├── components/                  # Reusable components
│   ├── Sidebar.tsx
│   ├── HealthStatus.tsx
│   └── SQLEditor.tsx
├── services/                    # API clients
│   ├── api.ts                   # Main axios instance
│   ├── catalogAPI.ts
│   ├── documentationAPI.ts
│   └── lineageAPI.ts
├── types/                       # TypeScript interfaces
│   └── index.ts
└── utils/                       # Utility functions
    └── index.ts
```

#### 1.5 Set Up API Client Foundation
**File:** `frontend/src/services/api.ts`

Create the base Axios instance with:
- Base URL from environment variable (`REACT_APP_API_URL`)
- Request interceptor for authentication tokens
- Response interceptor for error handling (401 redirects)
- Export basic health check functions

**Reference:** See specification lines 682-723

#### 1.6 Create TypeScript Interfaces
**File:** `frontend/src/types/index.ts`

Define core interfaces:
```typescript
export interface Catalog {
  name: string;
  comment?: string;
}

export interface Table {
  name: string;
  catalog: string;
  schema: string;
  table_type: string;
  row_count?: number;
}

export interface Column {
  name: string;
  data_type: string;
  nullable: boolean;
  comment?: string;
}

export interface SemanticModel {
  name: string;
  description?: string;
  model: string;
  entities: any[];
  dimensions: any[];
  measures: any[];
  metrics: any[];
}

export interface QueryResult {
  columns: string[];
  rows: Record<string, any>[];
  row_count: number;
  execution_time_ms: number;
}

export interface User {
  id: string;
  email: string;
  display_name: string;
  roles: string[];
  permissions: string[];
}
```

**Reference:** See specification lines 897-943

#### 1.7 Create Environment Configuration
**File:** `frontend/.env`
```
REACT_APP_API_URL=http://localhost:8000
```

### Deliverables
- [ ] Working React app that runs with `npm start`
- [ ] Tailwind CSS configured and working
- [ ] Directory structure created
- [ ] API client foundation with Axios
- [ ] TypeScript interfaces defined
- [ ] Environment variables configured

### Acceptance Criteria
- `npm start` launches app on http://localhost:3000
- No TypeScript compilation errors
- Tailwind utility classes work in components

---

## Phase 2: Navigation & Layout (Priority: HIGH)

### Objectives
- Implement React Router with all routes
- Build Sidebar navigation component
- Create main App layout
- Add health status indicators

### Tasks

#### 2.1 Implement Main App Router
**File:** `frontend/src/App.tsx`

Create the main application component with:
- React Query provider setup
- BrowserRouter with Routes
- Sidebar + Main content flex layout
- All 9 route definitions

**Reference:** See specification lines 116-176

**Key Points:**
- QueryClient with `refetchOnWindowFocus: false` and `retry: 1`
- Sidebar state management (`sidebarCollapsed`)
- Flex layout: `flex h-screen bg-gray-50`

#### 2.2 Build Sidebar Component
**File:** `frontend/src/components/Sidebar.tsx`

Implement navigation sidebar with:
- Collapsible functionality
- 9 navigation items with icons
- Active route highlighting
- Health status section (placeholder for now)

**Reference:** See specification lines 178-234

**Navigation Items:**
```typescript
const navItems = [
  { path: '/', icon: HomeIcon, label: 'Home' },
  { path: '/metrics', icon: ChartBarIcon, label: 'Metrics Explorer' },
  { path: '/metadata', icon: DatabaseIcon, label: 'Metadata' },
  { path: '/query', icon: CommandLineIcon, label: 'Query Lab' },
  { path: '/models', icon: CubeIcon, label: 'Models' },
  { path: '/metric-builder', icon: PlusCircleIcon, label: 'Metric Builder' },
  { path: '/auto-generate', icon: SparklesIcon, label: 'AI Generate' },
  { path: '/documentation', icon: DocumentTextIcon, label: 'Documentation' },
  { path: '/lineage', icon: ArrowsPointingOutIcon, label: 'Lineage' },
];
```

**Styling:**
- Dark sidebar: `bg-gray-900 text-white`
- Collapsed width: `w-16`, expanded: `w-64`
- Active route: `bg-gray-800 border-l-4 border-blue-500`

#### 2.3 Add Health Status Component
**File:** `frontend/src/components/HealthStatus.tsx`

Create health monitoring indicators:
- Backend API status
- Databricks connection status
- Update every 30 seconds

**API Endpoints to call:**
```typescript
import { checkHealth, checkDatabricksHealth } from '../services/api';

// Use React Query with refetch interval
const { data: backendHealth } = useQuery({
  queryKey: ['health', 'backend'],
  queryFn: checkHealth,
  refetchInterval: 30000, // 30 seconds
});

const { data: databricksHealth } = useQuery({
  queryKey: ['health', 'databricks'],
  queryFn: checkDatabricksHealth,
  refetchInterval: 30000,
});
```

**Visual Indicators:**
- Green dot: healthy
- Red dot: unhealthy
- Gray dot: loading/unknown

#### 2.4 Create Placeholder Pages
For each page, create a simple placeholder component:

```typescript
export default function PageName() {
  return (
    <div className="p-8">
      <h1 className="text-3xl font-bold mb-6">Page Title</h1>
      <p>Content coming soon...</p>
    </div>
  );
}
```

**Pages to create:**
- HomePage.tsx
- MetricsExplorerPage.tsx
- MetadataPage.tsx
- QueryLabPage.tsx
- ModelsPage.tsx
- MetricBuilderPage.tsx
- DocumentationPage.tsx
- LineageVisualizationPage.tsx

### Deliverables
- [ ] Working navigation between all 9 routes
- [ ] Collapsible sidebar with active route highlighting
- [ ] Health status indicators updating every 30s
- [ ] All placeholder pages accessible

### Acceptance Criteria
- Click navigation items to navigate to each route
- Active route is visually highlighted
- Sidebar collapses/expands smoothly
- Health indicators show status (will show errors until backend is ready)

---

## Phase 3: Core Pages Implementation (Priority: HIGH)

This phase focuses on the three most critical pages for MVP functionality.

### 3.1 HomePage - Landing & User Journeys

**File:** `frontend/src/pages/HomePage.tsx`

**Objectives:**
- Create dashboard landing page
- Implement user journey cards
- Add platform capabilities section

**Implementation Details:**

1. **User Journey Cards** (3 cards in grid):
   - Business Analyst journey
   - Data Engineer journey
   - Business User journey
   - Each card has icon, title, description, and action buttons
   - Use Material-UI Grid and Card components

2. **Platform Capabilities** (4 cards):
   - AI-Powered Model Generation
   - Natural Language Queries
   - Data Lineage
   - BI Tool Integration

**Reference:** See specification lines 240-375

**Key Components:**
```typescript
const userJourneys = [
  {
    title: 'Business Analyst',
    description: 'Explore metrics and query data without writing SQL',
    actions: [
      { label: 'Browse Metrics', path: '/metrics' },
      { label: 'Query Data', path: '/query' },
    ],
    icon: '📊',
  },
  // ... 2 more
];
```

**Styling:**
- Use Material-UI Grid: `<Grid container spacing={3}>`
- Cards with hover effect: `hover:shadow-lg transition-shadow`
- Action buttons: `bg-blue-50 hover:bg-blue-100`

### 3.2 MetricsExplorerPage - Browse & Search Metrics

**File:** `frontend/src/pages/MetricsExplorerPage.tsx`

**Objectives:**
- Implement metric search and filtering
- Display metrics in table format
- Integrate with React Query for data fetching

**Implementation Details:**

1. **Search Functionality:**
   ```typescript
   const [searchTerm, setSearchTerm] = useState('');
   const [selectedCategory, setSelectedCategory] = useState<string | null>(null);
   ```

2. **React Query Integration:**
   ```typescript
   const { data: metrics, isLoading } = useQuery({
     queryKey: ['metrics', searchTerm, selectedCategory],
     queryFn: () => searchMetrics(searchTerm, selectedCategory),
   });
   ```

3. **UI Components:**
   - Search TextField (full width)
   - Category filter chips (Revenue, Customer, Product, Operations)
   - Metrics table with columns:
     - Metric Name
     - Description
     - Type
     - Model
     - Actions

**Reference:** See specification lines 379-465

**API Function to implement in `services/api.ts`:**
```typescript
export const searchMetrics = (query: string, category?: string) =>
  api.get('/api/metrics-explorer/search', { params: { query, category } });
```

### 3.3 QueryLabPage - SQL Query Interface

**File:** `frontend/src/pages/QueryLabPage.tsx`

**Objectives:**
- Implement SQL query editor
- Add query execution functionality
- Display query results in table format

**Implementation Details:**

1. **State Management:**
   ```typescript
   const [query, setQuery] = useState('SELECT * FROM ');
   const [results, setResults] = useState<any>(null);
   ```

2. **Query Execution with React Query Mutation:**
   ```typescript
   const executeMutation = useMutation({
     mutationFn: (sql: string) => executeQuery(sql),
     onSuccess: (data) => setResults(data),
   });
   ```

3. **Layout Structure:**
   - Full height flex layout
   - SQL Editor component (top half)
   - Execute/Validate buttons
   - Results table (bottom half)

4. **Results Display:**
   - Show row count and execution time
   - Dynamic table with columns from results
   - Scrollable for large result sets

**Reference:** See specification lines 469-549

**API Function:**
```typescript
export const executeQuery = (query: string, limit?: number) =>
  api.post('/api/queries/execute', { query, limit });
```

### 3.4 SQLEditor Component

**File:** `frontend/src/components/SQLEditor.tsx`

**Objectives:**
- Create SQL editor with syntax support
- Implement autocomplete functionality
- Add keyboard shortcuts

**Implementation Details:**

1. **Core Features:**
   - Textarea with monospace font
   - Autocomplete dropdown
   - Debounced suggestion fetching (300ms)

2. **Keyboard Shortcuts:**
   - `Cmd/Ctrl + Enter`: Execute query
   - `Tab`: Accept suggestion
   - `Escape`: Close suggestions

3. **Autocomplete Logic:**
   ```typescript
   const fetchSuggestions = useCallback(
     debounce(async (text: string, position: number) => {
       // Extract word at cursor
       const beforeCursor = text.slice(0, position);
       const match = beforeCursor.match(/[\w.]+$/);
       const prefix = match ? match[0] : '';

       if (prefix.length < 2) return;

       const result = await getSQLAutocomplete(prefix);
       setSuggestions(result.suggestions);
     }, 300),
     []
   );
   ```

**Reference:** See specification lines 556-674

**Additional Dependencies Needed:**
```bash
npm install lodash
npm install --save-dev @types/lodash
```

### Deliverables
- [ ] HomePage with user journeys and capabilities
- [ ] MetricsExplorerPage with search and filtering
- [ ] QueryLabPage with SQL editor and results
- [ ] SQLEditor component with autocomplete

### Acceptance Criteria
- HomePage displays all journey cards and capabilities
- MetricsExplorerPage fetches and displays metrics (may show errors until backend ready)
- QueryLabPage can execute SQL queries (will fail until backend ready)
- SQLEditor shows autocomplete suggestions (will fail until backend ready)

---

## Phase 4: ModelsPage & Advanced Components (Priority: MEDIUM)

### 4.1 ModelsPage - Semantic Model Management

**File:** `frontend/src/pages/ModelsPage.tsx`

**Objectives:**
- Display list of semantic models
- Implement model filtering by category
- Add create/edit/delete actions
- Integrate Model Detail Modal

**Implementation Requirements:**

1. **Model List Display:**
   - Grid or table layout
   - Show model name, description, status
   - Category filter (production, staging, development)

2. **React Query Integration:**
   ```typescript
   const [category, setCategory] = useState('production');

   const { data: models, isLoading } = useQuery({
     queryKey: ['models', category],
     queryFn: () => listModels(category),
   });
   ```

3. **Actions:**
   - Create New Model button
   - Edit model (opens modal)
   - Delete model (with confirmation)
   - Download YAML

4. **API Functions to implement:**
   ```typescript
   export const listModels = (category: string = 'production') =>
     api.get('/api/models/', { params: { category } });

   export const getModel = (modelId: string, category: string = 'production') =>
     api.get(`/api/models/${modelId}`, { params: { category } });

   export const createModel = (model: any) => api.post('/api/models/', model);

   export const updateModel = (modelId: string, model: any) =>
     api.put(`/api/models/${modelId}`, model);

   export const deleteModel = (modelId: string) =>
     api.delete(`/api/models/${modelId}`);

   export const downloadModelYAML = (modelId: string) =>
     api.get(`/api/models/${modelId}/download`, { responseType: 'blob' });
   ```

**Reference:** See specification lines 743-758

### 4.2 Model Detail Modal Component

**File:** `frontend/src/components/ModelDetailModal.tsx`

**Objectives:**
- Create modal for viewing/editing semantic models
- Display model structure (entities, dimensions, measures, metrics)
- Form validation

**Modal Sections:**
1. **Header:** Model name, description
2. **Entities Tab:** List of entities with SQL definitions
3. **Dimensions Tab:** Dimension definitions
4. **Measures Tab:** Measure definitions
5. **Metrics Tab:** Metric definitions

**Use Material-UI Modal/Dialog:**
```typescript
import { Dialog, DialogTitle, DialogContent, DialogActions, Tabs, Tab } from '@mui/material';
```

### 4.3 MetadataPage - Catalog Navigator

**File:** `frontend/src/pages/MetadataPage.tsx`

**Objectives:**
- Tree view of catalogs → schemas → tables
- Display column information
- Table statistics

**Implementation:**
1. **Tree Structure:**
   - Expandable catalogs
   - Expandable schemas under catalogs
   - Tables under schemas
   - Click table to show columns

2. **API Functions:**
   ```typescript
   export const listCatalogs = () => api.get('/api/metadata/catalogs');

   export const listSchemas = (catalog: string) =>
     api.get('/api/metadata/schemas', { params: { catalog } });

   export const listTables = (catalog: string, schema: string) =>
     api.get('/api/metadata/tables', { params: { catalog, schema } });

   export const listColumns = (catalog: string, schema: string, table: string) =>
     api.get('/api/metadata/columns', { params: { catalog, schema, table } });
   ```

**Reference:** See specification lines 726-734

### 4.4 MetricBuilderPage - Custom Metric Creation

**File:** `frontend/src/pages/MetricBuilderPage.tsx`

**Objectives:**
- Form-based metric creation
- Metric type selection (simple, ratio, derived, cumulative)
- SQL expression builder

**Form Fields:**
- Metric name (required)
- Description
- Type (dropdown)
- Base measure selection
- Aggregation function
- Filter conditions
- Time grain

### Deliverables
- [ ] ModelsPage with model list and actions
- [ ] ModelDetailModal for viewing/editing models
- [ ] MetadataPage with catalog tree navigator
- [ ] MetricBuilderPage with metric creation form

### Acceptance Criteria
- ModelsPage displays list of models from API
- ModelDetailModal opens with model details
- MetadataPage shows expandable tree of catalogs/schemas/tables
- MetricBuilderPage has working form for metric creation

---

## Phase 5: Advanced Features (Priority: LOW)

### 5.1 DocumentationPage

**File:** `frontend/src/pages/DocumentationPage.tsx`

**Objectives:**
- List all semantic models with documentation
- Generate documentation in multiple formats
- Preview documentation

**API Functions:**
```typescript
export const generateDocumentation = (modelId: string, format: string) =>
  api.post('/api/documentation/generate', { model_id: modelId, format });

export const listDocumentation = () => api.get('/api/documentation/models');
```

### 5.2 LineageVisualizationPage

**File:** `frontend/src/pages/LineageVisualizationPage.tsx`

**Objectives:**
- Visualize data lineage using ReactFlow
- Show table-to-table dependencies
- Interactive graph with zoom/pan

**Additional Dependencies:**
```bash
npm install reactflow
```

**API Functions:**
```typescript
export const getTableLineage = (catalog: string, schema: string, table: string) =>
  api.get(`/api/lineage/tables/${catalog}.${schema}.${table}`);

export const getModelLineage = (modelId: string) =>
  api.get(`/api/lineage/models/${modelId}`);
```

### 5.3 AutoModelGeneration Component

**File:** `frontend/src/components/AutoModelGeneration/AutoModelGeneration.tsx`

**Objectives:**
- Multi-step wizard for AI model generation
- Table selection from gold layer
- Customization options
- Model preview and save

**Steps:**
1. Select gold layer table
2. Analyze table structure
3. AI suggests metrics/dimensions
4. Customize suggestions
5. Preview model YAML
6. Save to models

**API Functions:**
```typescript
export const getGoldTables = () => api.get('/api/catalog/gold-tables');

export const analyzeTable = (catalog: string, schema: string, table: string) =>
  api.post('/api/catalog/analyze-table', { catalog, schema, table });

export const generateModel = (analysisResult: any, customizations: any) =>
  api.post('/api/catalog/generate-model', { analysis: analysisResult, ...customizations });
```

### Deliverables
- [ ] DocumentationPage with generation capabilities
- [ ] LineageVisualizationPage with ReactFlow graph
- [ ] AutoModelGeneration wizard component

### Acceptance Criteria
- DocumentationPage can generate docs in multiple formats
- LineageVisualizationPage renders interactive lineage graph
- AutoModelGeneration wizard guides through all steps

---

## API Contract Coordination with Backend PM

### Critical Endpoints (Must be ready for Phase 3)

#### Health Endpoints
- `GET /api/health/` - Backend health check
- `GET /api/health/databricks` - Databricks connection health

#### Metadata Endpoints
- `GET /api/metadata/catalogs` - List catalogs
- `GET /api/metadata/schemas?catalog={catalog}` - List schemas
- `GET /api/metadata/tables?catalog={catalog}&schema={schema}` - List tables
- `GET /api/metadata/columns?catalog={catalog}&schema={schema}&table={table}` - List columns
- `GET /api/metadata/sql-autocomplete?prefix={prefix}` - SQL autocomplete

#### Query Endpoints
- `POST /api/queries/execute` - Execute SQL query
  ```json
  {
    "query": "SELECT * FROM table",
    "limit": 1000
  }
  ```
  Response:
  ```json
  {
    "columns": ["col1", "col2"],
    "rows": [{"col1": "value1", "col2": "value2"}],
    "row_count": 1,
    "execution_time_ms": 123
  }
  ```

- `POST /api/queries/validate` - Validate SQL query

#### Semantic Models Endpoints
- `GET /api/models/?category={category}` - List models
- `GET /api/models/{modelId}?category={category}` - Get model details
- `POST /api/models/` - Create model
- `PUT /api/models/{modelId}` - Update model
- `DELETE /api/models/{modelId}` - Delete model
- `GET /api/models/{modelId}/download` - Download model YAML

#### Metrics Explorer Endpoints
- `GET /api/metrics-explorer/metrics` - List all metrics
- `GET /api/metrics-explorer/search?query={query}&category={category}` - Search metrics

### Expected Response Formats

All successful responses should follow:
```json
{
  "data": { ... },
  "status": "success"
}
```

Error responses:
```json
{
  "error": "Error message",
  "status": "error",
  "details": { ... }
}
```

### CORS Configuration

Backend must enable CORS for:
- Origin: `http://localhost:3000` (development)
- Methods: GET, POST, PUT, DELETE, OPTIONS
- Headers: Content-Type, Authorization

---

## Testing Strategy

### Unit Testing
```bash
npm install --save-dev @testing-library/react @testing-library/jest-dom @testing-library/user-event
```

**Test Coverage:**
- Component rendering
- API function calls (mock axios)
- User interactions (button clicks, form submissions)
- React Query hooks

### Integration Testing
- Test complete user flows
- API integration with mock server
- Route navigation

### Manual Testing Checklist
- [ ] All routes accessible via sidebar
- [ ] Health indicators updating
- [ ] Query execution and results display
- [ ] Model CRUD operations
- [ ] Search and filtering work correctly
- [ ] Forms validate input
- [ ] Error messages display properly

---

## Performance Optimization

### Code Splitting
```typescript
// Lazy load pages
const MetricsExplorerPage = lazy(() => import('./pages/MetricsExplorerPage'));
const QueryLabPage = lazy(() => import('./pages/QueryLabPage'));

// Wrap routes in Suspense
<Suspense fallback={<LoadingSpinner />}>
  <Routes>...</Routes>
</Suspense>
```

### React Query Optimization
- Set appropriate `staleTime` for different data types
- Use `keepPreviousData` for paginated lists
- Implement query prefetching for anticipated navigation

### Bundle Optimization
- Analyze bundle size: `npm run build` and check build output
- Consider replacing Material-UI with lighter alternatives if bundle is too large
- Use tree-shaking compatible imports: `import { Button } from '@mui/material/Button'`

---

## Development Workflow

### Starting Development Server
```bash
cd frontend
npm start
```

### Build for Production
```bash
npm run build
```

### Project Structure Validation
Before starting each phase, ensure:
1. All necessary files exist
2. Imports are correct
3. TypeScript has no errors: `npm run build` (without serving)

### Git Commit Strategy
- Commit after completing each phase
- Use conventional commits format
- Example: `feat(frontend): implement HomePage with user journeys`

---

## Phase Priorities Summary

1. **Phase 1 (CRITICAL):** Foundation - Must complete first
2. **Phase 2 (HIGH):** Navigation & Layout - Needed for app navigation
3. **Phase 3 (HIGH):** Core Pages - MVP functionality
4. **Phase 4 (MEDIUM):** ModelsPage & Advanced - Full CRUD capabilities
5. **Phase 5 (LOW):** Advanced Features - Nice-to-have enhancements

---

## Questions for Backend PM

1. **Authentication:** Is authentication required? If yes, what's the auth flow?
2. **Databricks Token:** How should we handle Databricks token in frontend? Environment variable or user input?
3. **API Rate Limiting:** Any rate limits we need to handle?
4. **WebSocket Support:** Any real-time features needed (query execution status)?
5. **Pagination:** Should we implement pagination for large result sets?

---

## Success Criteria

### Phase 3 Completion (MVP)
- [ ] User can navigate between all pages
- [ ] Health indicators show status
- [ ] User can search and view metrics
- [ ] User can execute SQL queries and see results
- [ ] SQL editor has basic autocomplete

### Phase 4 Completion (Full CRUD)
- [ ] User can view list of semantic models
- [ ] User can create/edit/delete models
- [ ] User can browse metadata catalog
- [ ] User can create custom metrics

### Phase 5 Completion (Advanced)
- [ ] User can generate documentation
- [ ] User can visualize data lineage
- [ ] User can use AI to generate models

---

## Next Steps for Frontend Developer

1. **Start with Phase 1:** Set up project infrastructure
2. **Verify each phase:** Run `npm start` after each task to verify functionality
3. **Coordinate with Backend PM:** Confirm API endpoints are ready before testing integration
4. **Report blockers:** If any dependencies or clarifications are needed, coordinate immediately
5. **Commit regularly:** Commit after each major task completion

---

## Communication Protocol

- **Daily check-ins:** 10:00 AM and 3:00 PM
- **Blockers:** Report immediately in shared channel
- **Progress updates:** Every 30 minutes via commit + brief summary
- **API contract questions:** Tag Backend PM for quick resolution
- **Code reviews:** PR after each phase completion

---

**Let's build this! Start with Phase 1 and report back when complete.**
