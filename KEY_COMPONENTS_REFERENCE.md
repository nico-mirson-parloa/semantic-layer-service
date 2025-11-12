# Key Components Reference - Frontend

**Quick reference guide for critical frontend components**

---

## Component Hierarchy

```
App.tsx (Root)
├── Sidebar
│   ├── HealthStatus
│   └── Navigation Items
└── Pages
    ├── HomePage
    ├── MetricsExplorerPage
    ├── QueryLabPage
    │   └── SQLEditor
    ├── ModelsPage
    │   └── ModelDetailModal
    ├── MetadataPage
    ├── MetricBuilderPage
    ├── DocumentationPage
    ├── LineageVisualizationPage
    └── AutoModelGeneration (Component used as page)
```

---

## Critical Components Breakdown

### 1. App.tsx - Main Application Router

**Responsibilities:**
- React Query provider setup
- React Router configuration
- Main layout (sidebar + content area)
- Global state management (sidebar collapsed state)

**Key Code:**
```typescript
const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      refetchOnWindowFocus: false,
      retry: 1,
      staleTime: 5 * 60 * 1000,
      cacheTime: 10 * 60 * 1000,
    },
  },
});

function App() {
  const [sidebarCollapsed, setSidebarCollapsed] = useState(false);

  return (
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>
        <div className="flex h-screen bg-gray-50">
          <Sidebar collapsed={sidebarCollapsed} onToggle={...} />
          <main className="flex-1 overflow-auto">
            <Routes>
              {/* 9 route definitions */}
            </Routes>
          </main>
        </div>
      </BrowserRouter>
    </QueryClientProvider>
  );
}
```

**Dependencies:**
- react-router-dom: BrowserRouter, Routes, Route
- @tanstack/react-query: QueryClient, QueryClientProvider
- All page components

---

### 2. Sidebar - Navigation Component

**Responsibilities:**
- Navigation menu with 9 items
- Active route highlighting
- Collapse/expand functionality
- Health status display

**Props:**
```typescript
interface SidebarProps {
  collapsed: boolean;
  onToggle: () => void;
}
```

**Key Features:**
- Icons from Heroicons or Material-UI Icons
- Active route detected with `useLocation()`
- Smooth transitions with Tailwind: `transition-all duration-300`
- Responsive width: `w-16` (collapsed) or `w-64` (expanded)

**Styling:**
- Dark theme: `bg-gray-900 text-white`
- Active route: `bg-gray-800 border-l-4 border-blue-500`
- Hover effect: `hover:bg-gray-800`

---

### 3. HealthStatus - System Health Indicators

**Responsibilities:**
- Display backend API status
- Display Databricks connection status
- Auto-refresh every 30 seconds

**Key Code:**
```typescript
const { data: backendHealth } = useQuery({
  queryKey: ['health', 'backend'],
  queryFn: checkHealth,
  refetchInterval: 30000,
});

const { data: databricksHealth } = useQuery({
  queryKey: ['health', 'databricks'],
  queryFn: checkDatabricksHealth,
  refetchInterval: 30000,
});
```

**Visual States:**
- 🟢 Green: Healthy/Connected
- 🔴 Red: Unhealthy/Disconnected
- ⚪ Gray: Loading/Unknown

**Display (Collapsed):**
- Just colored dots

**Display (Expanded):**
- Label + colored dot + status text

---

### 4. HomePage - Landing Dashboard

**Responsibilities:**
- Welcome message and overview
- User journey cards (3 personas)
- Platform capabilities showcase (4 features)

**Data Structure:**
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
  // Data Engineer
  // Business User
];

const capabilities = [
  {
    title: 'AI-Powered Model Generation',
    description: '...',
    icon: '🤖',
  },
  // 3 more...
];
```

**Layout:**
- Material-UI Grid: 3 columns for journeys, 2 columns for capabilities
- Cards with hover effects
- Action buttons with navigation
- Responsive design

**Dependencies:**
- @mui/material: Grid, Card, CardContent, Typography
- react-router-dom: useNavigate

---

### 5. MetricsExplorerPage - Metrics Browser

**Responsibilities:**
- Search metrics by name/description
- Filter by category
- Display metrics in table
- Navigate to metric details

**State Management:**
```typescript
const [searchTerm, setSearchTerm] = useState('');
const [selectedCategory, setSelectedCategory] = useState<string | null>(null);

const { data: metrics, isLoading } = useQuery({
  queryKey: ['metrics', searchTerm, selectedCategory],
  queryFn: () => searchMetrics(searchTerm, selectedCategory),
});
```

**UI Sections:**
1. **Search Bar:** Full-width TextField
2. **Category Chips:** Revenue, Customer, Product, Operations
3. **Metrics Table:** Name, Description, Type, Model, Actions

**Key Features:**
- Real-time search (query key updates trigger refetch)
- Category toggle (click same category to clear)
- Loading state during fetch
- Empty state when no results

**Dependencies:**
- @mui/material: TextField, Table, Chip
- @tanstack/react-query: useQuery
- API: searchMetrics()

---

### 6. QueryLabPage - SQL Query Interface

**Responsibilities:**
- SQL query editor
- Execute queries
- Display results
- Validate queries

**State Management:**
```typescript
const [query, setQuery] = useState('SELECT * FROM ');
const [results, setResults] = useState<QueryResult | null>(null);

const executeMutation = useMutation({
  mutationFn: (sql: string) => executeQuery(sql),
  onSuccess: (data) => setResults(data),
});
```

**Layout:**
- Flex column layout (full height)
- SQLEditor component (expandable)
- Action buttons (Execute, Validate)
- Results table (scrollable)

**Key Features:**
- Cmd/Ctrl+Enter to execute
- Loading state during execution
- Error display for failed queries
- Results metadata (row count, execution time)

**Dependencies:**
- SQLEditor component (custom)
- @tanstack/react-query: useMutation
- API: executeQuery(), validateQuery()

---

### 7. SQLEditor - SQL Editor Component

**Responsibilities:**
- Code editor for SQL
- Autocomplete suggestions
- Keyboard shortcuts
- Syntax support (basic)

**Props:**
```typescript
interface SQLEditorProps {
  value: string;
  onChange: (value: string) => void;
  onExecute?: () => void;
}
```

**Key Features:**

1. **Autocomplete:**
   - Trigger on typing (min 2 chars)
   - Debounced API calls (300ms)
   - Dropdown with suggestions
   - Tab to accept, Escape to close

2. **Keyboard Shortcuts:**
   - Cmd/Ctrl+Enter: Execute query
   - Tab: Accept suggestion
   - Escape: Close suggestions

3. **Implementation:**
```typescript
const fetchSuggestions = useCallback(
  debounce(async (text: string, position: number) => {
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

**Dependencies:**
- lodash: debounce
- API: getSQLAutocomplete()

**Styling:**
- Monospace font: `font-mono`
- No spell check: `spellCheck={false}`
- Border and padding: `border rounded p-4`

---

### 8. ModelsPage - Semantic Model Management

**Responsibilities:**
- List all semantic models
- Filter by category (production/staging/development)
- CRUD operations (Create, Read, Update, Delete)
- Download model YAML

**State Management:**
```typescript
const [category, setCategory] = useState('production');
const [selectedModel, setSelectedModel] = useState<string | null>(null);
const [showModal, setShowModal] = useState(false);

const { data: models, isLoading } = useQuery({
  queryKey: ['models', category],
  queryFn: () => listModels(category),
});
```

**UI Sections:**
1. **Category Tabs:** Production | Staging | Development
2. **Create Button:** Opens modal for new model
3. **Models Grid/Table:** Display model cards or table rows
4. **Actions:** View, Edit, Delete, Download

**Key Features:**
- Modal for model details (ModelDetailModal)
- Confirmation dialog for delete
- Download YAML file
- Invalidate query cache after mutations

**Dependencies:**
- ModelDetailModal component (custom)
- @mui/material: Tabs, Dialog
- @tanstack/react-query: useQuery, useMutation
- API: listModels(), getModel(), createModel(), updateModel(), deleteModel(), downloadModelYAML()

---

### 9. ModelDetailModal - Model Viewer/Editor

**Responsibilities:**
- Display full model details
- Edit model configuration
- Tabbed interface for different sections
- Save changes

**Props:**
```typescript
interface ModelDetailModalProps {
  modelId: string | null;
  open: boolean;
  onClose: () => void;
  mode: 'view' | 'edit' | 'create';
}
```

**Tabs:**
1. **Overview:** Name, description, base table
2. **Entities:** Entity definitions
3. **Dimensions:** Dimension definitions
4. **Measures:** Measure definitions
5. **Metrics:** Metric definitions

**Form Structure:**
```typescript
interface SemanticModel {
  name: string;
  description: string;
  model: string; // table reference
  entities: Entity[];
  dimensions: Dimension[];
  measures: Measure[];
  metrics: Metric[];
}
```

**Dependencies:**
- @mui/material: Dialog, Tabs, TextField, Button
- React Hook Form (optional, for form management)
- API: getModel(), updateModel(), createModel()

---

### 10. MetadataPage - Catalog Tree Navigator

**Responsibilities:**
- Display catalog → schema → table hierarchy
- Expandable tree structure
- Show table details on selection
- Display column information

**State Management:**
```typescript
const [expandedNodes, setExpandedNodes] = useState<Set<string>>(new Set());
const [selectedTable, setSelectedTable] = useState<{
  catalog: string;
  schema: string;
  table: string;
} | null>(null);

// Query for catalogs
const { data: catalogs } = useQuery({
  queryKey: ['catalogs'],
  queryFn: listCatalogs,
});

// Query for columns (when table selected)
const { data: columns } = useQuery({
  queryKey: ['columns', selectedTable],
  queryFn: () => selectedTable
    ? listColumns(selectedTable.catalog, selectedTable.schema, selectedTable.table)
    : null,
  enabled: !!selectedTable,
});
```

**UI Structure:**
- Left panel: Tree view
- Right panel: Table details and columns

**Tree Levels:**
1. Catalogs (loaded on mount)
2. Schemas (loaded on catalog expand)
3. Tables (loaded on schema expand)

**Dependencies:**
- @mui/material: TreeView (or custom tree component)
- @tanstack/react-query: useQuery
- API: listCatalogs(), listSchemas(), listTables(), listColumns()

---

## Component Development Priorities

### Phase 1: Foundation (CRITICAL)
1. App.tsx - Main structure
2. Sidebar - Navigation

### Phase 2: Core Pages (HIGH)
3. HomePage - Landing
4. MetricsExplorerPage - Metrics browser
5. QueryLabPage - SQL interface
6. SQLEditor - Query editor

### Phase 3: Models (MEDIUM)
7. ModelsPage - Model list
8. ModelDetailModal - Model viewer/editor
9. MetadataPage - Catalog tree

### Phase 4: Advanced (LOW)
10. MetricBuilderPage
11. DocumentationPage
12. LineageVisualizationPage
13. AutoModelGeneration

---

## Common Patterns

### React Query Pattern
```typescript
// Fetch data
const { data, isLoading, error } = useQuery({
  queryKey: ['resource', param1, param2],
  queryFn: () => fetchResource(param1, param2),
});

// Mutate data
const mutation = useMutation({
  mutationFn: updateResource,
  onSuccess: () => {
    queryClient.invalidateQueries({ queryKey: ['resource'] });
  },
});
```

### Navigation Pattern
```typescript
import { useNavigate } from 'react-router-dom';

function Component() {
  const navigate = useNavigate();

  const handleClick = () => {
    navigate('/target-path');
  };
}
```

### Error Handling Pattern
```typescript
const { data, error } = useQuery({
  queryKey: ['data'],
  queryFn: fetchData,
});

if (error) {
  return (
    <div className="p-4 bg-red-50 border border-red-200 rounded">
      <p className="text-red-800">Error: {error.message}</p>
    </div>
  );
}
```

### Loading State Pattern
```typescript
if (isLoading) {
  return (
    <div className="flex items-center justify-center p-8">
      <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600" />
      <span className="ml-2 text-gray-600">Loading...</span>
    </div>
  );
}
```

---

## Styling Conventions

### Layout Classes
- Page container: `p-8`
- Full height: `h-full` or `h-screen`
- Flex layouts: `flex flex-col` or `flex items-center justify-between`
- Grid layouts: Use Material-UI Grid or `grid grid-cols-3 gap-4`

### Color Scheme
- Primary: `bg-blue-600`, `text-blue-600`
- Secondary: `bg-gray-200`, `text-gray-600`
- Success: `bg-green-600`
- Error: `bg-red-600`
- Dark sidebar: `bg-gray-900 text-white`

### Component Classes
- Cards: `bg-white rounded-lg shadow p-4`
- Buttons: `px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700`
- Inputs: Material-UI TextField with `fullWidth` prop

### Transitions
- Smooth transitions: `transition-all duration-300`
- Hover effects: `hover:shadow-lg`

---

## Testing Checklist

### Component Testing
- [ ] Component renders without errors
- [ ] Props are correctly typed
- [ ] Loading states display properly
- [ ] Error states display properly
- [ ] User interactions work (clicks, inputs)
- [ ] Navigation works
- [ ] API integration works (or shows expected errors)

### Page Testing
- [ ] Page accessible via route
- [ ] Page title displays
- [ ] Data fetching works
- [ ] Empty states display
- [ ] Pagination works (if applicable)
- [ ] Search/filter works
- [ ] Forms validate input
- [ ] Success/error messages display

---

## Quick Start for Frontend Developer

1. **Set up project:**
   ```bash
   npx create-react-app frontend --template typescript
   cd frontend
   npm install [all dependencies]
   ```

2. **Create directory structure:**
   ```bash
   mkdir -p src/{pages,components,services,types,utils}
   ```

3. **Start with App.tsx:**
   - Set up React Query
   - Set up React Router
   - Create basic layout

4. **Build Sidebar:**
   - Add navigation items
   - Implement collapse/expand
   - Add health status

5. **Create placeholder pages:**
   - Create all 9 page components
   - Add basic structure to each

6. **Implement API client:**
   - Create axios instance in services/api.ts
   - Add all endpoint functions
   - Test with mock data or real backend

7. **Build pages incrementally:**
   - Start with HomePage (static content)
   - Then MetricsExplorerPage (simple list)
   - Then QueryLabPage (more complex)
   - Continue through remaining pages

---

**Remember:** Commit after each major component completion!
