# Frontend Specification - Semantic Layer Service

**Document Version:** 1.0
**Last Updated:** 2025-11-04

---

## Table of Contents

1. [Architecture Overview](#1-architecture-overview)
2. [Directory Structure](#2-directory-structure)
3. [Routing Configuration](#3-routing-configuration)
4. [Page Components](#4-page-components)
5. [Reusable Components](#5-reusable-components)
6. [API Integration Layer](#6-api-integration-layer)
7. [State Management](#7-state-management)
8. [Styling Approach](#8-styling-approach)
9. [TypeScript Interfaces](#9-typescript-interfaces)
10. [Build Configuration](#10-build-configuration)

---

## 1. Architecture Overview

### Technology Stack

- **Framework:** React 18 with TypeScript
- **Routing:** React Router v6
- **State Management:** React Query (TanStack Query) + useState
- **Styling:** Tailwind CSS + Material-UI
- **HTTP Client:** Axios
- **Visualization:** ReactFlow, Recharts, D3
- **Build Tool:** Create React App (react-scripts)

### Component Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                      App.tsx (Router)                       │
│                     Main Layout + Navigation                │
└───────────────────┬─────────────────────────────────────────┘
                    │
        ┌───────────┴────────────┐
        │                        │
┌───────▼──────┐        ┌───────▼──────────┐
│    Pages     │        │   Components     │
│  (9 routes)  │        │   (Reusable)     │
└──────┬───────┘        └──────┬───────────┘
       │                       │
       └───────────┬───────────┘
                   │
         ┌─────────▼──────────┐
         │   API Services     │
         │  (axios clients)   │
         └─────────┬──────────┘
                   │
         ┌─────────▼──────────┐
         │  Backend REST API  │
         └────────────────────┘
```

---

## 2. Directory Structure

```
frontend/
├── public/
│   ├── index.html
│   └── favicon.ico
│
├── src/
│   ├── index.tsx                      # Application entry point
│   ├── App.tsx                        # Main router + layout
│   │
│   ├── pages/                         # Page components (9 files)
│   │   ├── HomePage.tsx               # Dashboard with user journeys
│   │   ├── MetricsExplorerPage.tsx    # Browse/search metrics
│   │   ├── MetadataPage.tsx           # Catalog tree navigator
│   │   ├── QueryLabPage.tsx           # SQL query interface
│   │   ├── ModelsPage.tsx             # Semantic model management
│   │   ├── MetricBuilderPage.tsx      # Custom metric creation
│   │   ├── DocumentationPage.tsx      # Documentation generation
│   │   └── LineageVisualizationPage.tsx  # Data lineage graph
│   │
│   ├── components/                    # Reusable components
│   │   ├── AutoModelGeneration/       # AI model generation wizard
│   │   │   └── AutoModelGeneration.tsx  (950+ lines)
│   │   ├── Documentation/
│   │   │   └── Documentation.tsx
│   │   ├── LineageVisualization/
│   │   │   └── LineageVisualization.tsx
│   │   ├── ModelDetailModal.tsx       # Model viewer/editor modal
│   │   └── SQLEditor.tsx              # SQL editor with autocomplete
│   │
│   ├── services/                      # API client layer
│   │   ├── api.ts                     # Main axios instance + 60+ endpoints
│   │   ├── catalogAPI.ts              # Catalog/table operations
│   │   ├── documentationAPI.ts        # Documentation APIs
│   │   └── lineageAPI.ts              # Data lineage queries
│   │
│   └── utils/                         # Utility functions
│
├── package.json                       # Dependencies
├── tsconfig.json                      # TypeScript configuration
├── tailwind.config.js                 # Tailwind CSS config
└── .env                               # Environment variables
```

---

## 3. Routing Configuration

### Main Router (`App.tsx`)

```typescript
import { BrowserRouter, Routes, Route } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { useState } from 'react';

// Pages
import HomePage from './pages/HomePage';
import MetricsExplorerPage from './pages/MetricsExplorerPage';
import MetadataPage from './pages/MetadataPage';
import QueryLabPage from './pages/QueryLabPage';
import ModelsPage from './pages/ModelsPage';
import MetricBuilderPage from './pages/MetricBuilderPage';
import AutoModelGeneration from './components/AutoModelGeneration/AutoModelGeneration';
import DocumentationPage from './pages/DocumentationPage';
import LineageVisualizationPage from './pages/LineageVisualizationPage';

// React Query configuration
const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      refetchOnWindowFocus: false,
      retry: 1,
    },
  },
});

function App() {
  const [sidebarCollapsed, setSidebarCollapsed] = useState(false);

  return (
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>
        <div className="flex h-screen bg-gray-50">
          {/* Sidebar Navigation */}
          <Sidebar
            collapsed={sidebarCollapsed}
            onToggle={() => setSidebarCollapsed(!sidebarCollapsed)}
          />

          {/* Main Content */}
          <main className="flex-1 overflow-auto">
            <Routes>
              <Route path="/" element={<HomePage />} />
              <Route path="/metrics" element={<MetricsExplorerPage />} />
              <Route path="/metadata" element={<MetadataPage />} />
              <Route path="/query" element={<QueryLabPage />} />
              <Route path="/models" element={<ModelsPage />} />
              <Route path="/metric-builder" element={<MetricBuilderPage />} />
              <Route path="/auto-generate" element={<AutoModelGeneration />} />
              <Route path="/documentation" element={<DocumentationPage />} />
              <Route path="/lineage" element={<LineageVisualizationPage />} />
            </Routes>
          </main>
        </div>
      </BrowserRouter>
    </QueryClientProvider>
  );
}

export default App;
```

### Sidebar Navigation Component

```typescript
interface SidebarProps {
  collapsed: boolean;
  onToggle: () => void;
}

function Sidebar({ collapsed, onToggle }: SidebarProps) {
  const location = useLocation();

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

  return (
    <aside className={`bg-gray-900 text-white transition-all duration-300 ${
      collapsed ? 'w-16' : 'w-64'
    }`}>
      {/* Header */}
      <div className="flex items-center justify-between p-4">
        {!collapsed && <h1 className="text-xl font-bold">Semantic Layer</h1>}
        <button onClick={onToggle} className="p-2 hover:bg-gray-800 rounded">
          {collapsed ? <MenuIcon /> : <XIcon />}
        </button>
      </div>

      {/* Health Status Indicators */}
      <HealthStatus collapsed={collapsed} />

      {/* Navigation Items */}
      <nav className="mt-6">
        {navItems.map((item) => (
          <Link
            key={item.path}
            to={item.path}
            className={`flex items-center px-4 py-3 hover:bg-gray-800 ${
              location.pathname === item.path ? 'bg-gray-800 border-l-4 border-blue-500' : ''
            }`}
          >
            <item.icon className="w-6 h-6" />
            {!collapsed && <span className="ml-3">{item.label}</span>}
          </Link>
        ))}
      </nav>
    </aside>
  );
}
```

---

## 4. Page Components

### 4.1 HomePage (`pages/HomePage.tsx`)

**Purpose:** Landing page with user journey guides

```typescript
import { Card, CardContent, Typography, Grid } from '@mui/material';
import { useNavigate } from 'react-router-dom';

export default function HomePage() {
  const navigate = useNavigate();

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
    {
      title: 'Data Engineer',
      description: 'Create and manage semantic models',
      actions: [
        { label: 'Generate Models', path: '/auto-generate' },
        { label: 'View Models', path: '/models' },
        { label: 'Track Lineage', path: '/lineage' },
      ],
      icon: '⚙️',
    },
    {
      title: 'Business User',
      description: 'Get insights from certified metrics',
      actions: [
        { label: 'Explore Metrics', path: '/metrics' },
        { label: 'View Documentation', path: '/documentation' },
      ],
      icon: '👤',
    },
  ];

  const capabilities = [
    {
      title: 'AI-Powered Model Generation',
      description: 'Automatically generate semantic models from gold layer tables',
      icon: '🤖',
    },
    {
      title: 'Natural Language Queries',
      description: 'Ask questions in plain English, get SQL automatically',
      icon: '💬',
    },
    {
      title: 'Data Lineage',
      description: 'Visualize data dependencies and impact analysis',
      icon: '🔄',
    },
    {
      title: 'BI Tool Integration',
      description: 'Connect Tableau, Power BI, or any SQL client',
      icon: '🔌',
    },
  ];

  return (
    <div className="p-8">
      <div className="mb-8">
        <h1 className="text-4xl font-bold mb-2">Semantic Layer Service</h1>
        <p className="text-xl text-gray-600">
          Unified metrics and dimensions for data-driven insights
        </p>
      </div>

      {/* User Journeys */}
      <section className="mb-12">
        <h2 className="text-2xl font-semibold mb-4">Choose Your Journey</h2>
        <Grid container spacing={3}>
          {userJourneys.map((journey) => (
            <Grid item xs={12} md={4} key={journey.title}>
              <Card className="h-full hover:shadow-lg transition-shadow">
                <CardContent>
                  <div className="text-4xl mb-3">{journey.icon}</div>
                  <Typography variant="h5" className="mb-2">
                    {journey.title}
                  </Typography>
                  <Typography color="textSecondary" className="mb-4">
                    {journey.description}
                  </Typography>
                  <div className="space-y-2">
                    {journey.actions.map((action) => (
                      <button
                        key={action.path}
                        onClick={() => navigate(action.path)}
                        className="w-full text-left px-4 py-2 bg-blue-50 hover:bg-blue-100 rounded"
                      >
                        {action.label} →
                      </button>
                    ))}
                  </div>
                </CardContent>
              </Card>
            </Grid>
          ))}
        </Grid>
      </section>

      {/* Platform Capabilities */}
      <section>
        <h2 className="text-2xl font-semibold mb-4">Platform Capabilities</h2>
        <Grid container spacing={3}>
          {capabilities.map((capability) => (
            <Grid item xs={12} md={6} key={capability.title}>
              <Card>
                <CardContent>
                  <div className="flex items-start">
                    <div className="text-3xl mr-4">{capability.icon}</div>
                    <div>
                      <Typography variant="h6" className="mb-1">
                        {capability.title}
                      </Typography>
                      <Typography color="textSecondary">
                        {capability.description}
                      </Typography>
                    </div>
                  </div>
                </CardContent>
              </Card>
            </Grid>
          ))}
        </Grid>
      </section>
    </div>
  );
}
```

---

### 4.2 MetricsExplorerPage (`pages/MetricsExplorerPage.tsx`)

**Purpose:** Browse, search, and filter metrics

```typescript
import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { TextField, Table, TableBody, TableCell, TableHead, TableRow, Chip } from '@mui/material';
import { searchMetrics } from '../services/api';

export default function MetricsExplorerPage() {
  const [searchTerm, setSearchTerm] = useState('');
  const [selectedCategory, setSelectedCategory] = useState<string | null>(null);

  // Fetch metrics with React Query
  const { data: metrics, isLoading } = useQuery({
    queryKey: ['metrics', searchTerm, selectedCategory],
    queryFn: () => searchMetrics(searchTerm, selectedCategory),
  });

  const categories = ['Revenue', 'Customer', 'Product', 'Operations'];

  return (
    <div className="p-8">
      <h1 className="text-3xl font-bold mb-6">Metrics Explorer</h1>

      {/* Search and Filters */}
      <div className="mb-6 space-y-4">
        <TextField
          fullWidth
          placeholder="Search metrics..."
          value={searchTerm}
          onChange={(e) => setSearchTerm(e.target.value)}
          variant="outlined"
        />

        <div className="flex gap-2">
          {categories.map((category) => (
            <Chip
              key={category}
              label={category}
              onClick={() => setSelectedCategory(
                selectedCategory === category ? null : category
              )}
              color={selectedCategory === category ? 'primary' : 'default'}
            />
          ))}
        </div>
      </div>

      {/* Metrics Table */}
      {isLoading ? (
        <div>Loading metrics...</div>
      ) : (
        <Table>
          <TableHead>
            <TableRow>
              <TableCell>Metric Name</TableCell>
              <TableCell>Description</TableCell>
              <TableCell>Type</TableCell>
              <TableCell>Model</TableCell>
              <TableCell>Actions</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {metrics?.map((metric: any) => (
              <TableRow key={metric.id} hover>
                <TableCell className="font-medium">{metric.name}</TableCell>
                <TableCell>{metric.description}</TableCell>
                <TableCell>
                  <Chip label={metric.type} size="small" />
                </TableCell>
                <TableCell>{metric.model_name}</TableCell>
                <TableCell>
                  <button className="text-blue-600 hover:underline">
                    View Details
                  </button>
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      )}
    </div>
  );
}
```

---

### 4.3 QueryLabPage (`pages/QueryLabPage.tsx`)

**Purpose:** SQL query interface with execution

```typescript
import { useState } from 'react';
import { useMutation } from '@tanstack/react-query';
import SQLEditor from '../components/SQLEditor';
import { executeQuery } from '../services/api';

export default function QueryLabPage() {
  const [query, setQuery] = useState('SELECT * FROM ');
  const [results, setResults] = useState<any>(null);

  const executeMutation = useMutation({
    mutationFn: (sql: string) => executeQuery(sql),
    onSuccess: (data) => setResults(data),
  });

  const handleExecute = () => {
    executeMutation.mutate(query);
  };

  return (
    <div className="p-8 h-full flex flex-col">
      <h1 className="text-3xl font-bold mb-6">Query Lab</h1>

      {/* SQL Editor */}
      <div className="flex-1 flex flex-col gap-4">
        <div className="flex-1 min-h-0">
          <SQLEditor
            value={query}
            onChange={setQuery}
            onExecute={handleExecute}
          />
        </div>

        {/* Execute Button */}
        <div className="flex gap-2">
          <button
            onClick={handleExecute}
            disabled={executeMutation.isPending}
            className="px-6 py-2 bg-blue-600 text-white rounded hover:bg-blue-700 disabled:opacity-50"
          >
            {executeMutation.isPending ? 'Executing...' : 'Execute (Cmd+Enter)'}
          </button>
          <button className="px-6 py-2 bg-gray-200 rounded hover:bg-gray-300">
            Validate
          </button>
        </div>

        {/* Results */}
        {results && (
          <div className="flex-1 overflow-auto border rounded p-4">
            <div className="mb-2 text-sm text-gray-600">
              {results.row_count} rows in {results.execution_time_ms}ms
            </div>
            <table className="w-full">
              <thead>
                <tr className="border-b">
                  {results.columns.map((col: string) => (
                    <th key={col} className="text-left p-2">{col}</th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {results.rows.map((row: any, i: number) => (
                  <tr key={i} className="border-b hover:bg-gray-50">
                    {results.columns.map((col: string) => (
                      <td key={col} className="p-2">{row[col]}</td>
                    ))}
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
}
```

---

## 5. Reusable Components

### 5.1 SQLEditor Component (`components/SQLEditor.tsx`)

**Purpose:** SQL editor with autocomplete

```typescript
import { useState, useEffect, useCallback } from 'react';
import { debounce } from 'lodash';
import { getSQLAutocomplete } from '../services/api';

interface SQLEditorProps {
  value: string;
  onChange: (value: string) => void;
  onExecute?: () => void;
}

export default function SQLEditor({ value, onChange, onExecute }: SQLEditorProps) {
  const [suggestions, setSuggestions] = useState<any[]>([]);
  const [showSuggestions, setShowSuggestions] = useState(false);
  const [cursorPosition, setCursorPosition] = useState(0);

  // Debounced autocomplete fetcher
  const fetchSuggestions = useCallback(
    debounce(async (text: string, position: number) => {
      // Extract word at cursor
      const beforeCursor = text.slice(0, position);
      const match = beforeCursor.match(/[\w.]+$/);
      const prefix = match ? match[0] : '';

      if (prefix.length < 2) {
        setSuggestions([]);
        return;
      }

      try {
        const result = await getSQLAutocomplete(prefix);
        setSuggestions(result.suggestions);
        setShowSuggestions(result.suggestions.length > 0);
      } catch (error) {
        console.error('Autocomplete failed:', error);
      }
    }, 300),
    []
  );

  // Handle keyboard shortcuts
  const handleKeyDown = (e: React.KeyboardEvent) => {
    // Cmd/Ctrl + Enter to execute
    if ((e.metaKey || e.ctrlKey) && e.key === 'Enter') {
      e.preventDefault();
      onExecute?.();
      return;
    }

    // Tab to accept suggestion
    if (e.key === 'Tab' && showSuggestions && suggestions.length > 0) {
      e.preventDefault();
      acceptSuggestion(suggestions[0]);
      return;
    }

    // Escape to close suggestions
    if (e.key === 'Escape') {
      setShowSuggestions(false);
    }
  };

  const handleChange = (e: React.ChangeEvent<HTMLTextAreaElement>) => {
    const newValue = e.target.value;
    const position = e.target.selectionStart;

    onChange(newValue);
    setCursorPosition(position);
    fetchSuggestions(newValue, position);
  };

  const acceptSuggestion = (suggestion: any) => {
    // Replace current word with suggestion
    const beforeCursor = value.slice(0, cursorPosition);
    const afterCursor = value.slice(cursorPosition);
    const match = beforeCursor.match(/[\w.]*$/);

    if (match) {
      const newValue = beforeCursor.slice(0, -match[0].length) + suggestion.value + afterCursor;
      onChange(newValue);
    }

    setShowSuggestions(false);
  };

  return (
    <div className="relative h-full">
      <textarea
        value={value}
        onChange={handleChange}
        onKeyDown={handleKeyDown}
        className="w-full h-full p-4 font-mono text-sm border rounded resize-none"
        placeholder="Enter your SQL query..."
        spellCheck={false}
      />

      {/* Autocomplete Dropdown */}
      {showSuggestions && (
        <div className="absolute top-full left-0 mt-1 bg-white border rounded shadow-lg max-h-48 overflow-auto z-10">
          {suggestions.map((suggestion, i) => (
            <div
              key={i}
              onClick={() => acceptSuggestion(suggestion)}
              className="px-4 py-2 hover:bg-blue-50 cursor-pointer flex items-center"
            >
              <span className="text-xs text-gray-500 mr-2">{suggestion.type}</span>
              <span className="font-mono">{suggestion.value}</span>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
```

---

## 6. API Integration Layer

### 6.1 Main API Client (`services/api.ts`)

```typescript
import axios from 'axios';

// Create axios instance
const api = axios.create({
  baseURL: process.env.REACT_APP_API_URL || 'http://localhost:8000',
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request interceptor for authentication
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('auth_token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// Response interceptor for error handling
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      // Handle unauthorized
      localStorage.removeItem('auth_token');
      window.location.href = '/login';
    }
    return Promise.reject(error);
  }
);

// ========== Health Endpoints ==========
export const checkHealth = () => api.get('/api/health/');
export const checkDatabricksHealth = () => api.get('/api/health/databricks');

// ========== Authentication ==========
export const login = (databricksToken: string) =>
  api.post('/api/auth/login', { databricks_token: databricksToken });

export const getCurrentUser = () => api.get('/api/auth/me');

// ========== Metadata ==========
export const listCatalogs = () => api.get('/api/metadata/catalogs');
export const listSchemas = (catalog: string) => api.get('/api/metadata/schemas', { params: { catalog } });
export const listTables = (catalog: string, schema: string) =>
  api.get('/api/metadata/tables', { params: { catalog, schema } });
export const listColumns = (catalog: string, schema: string, table: string) =>
  api.get('/api/metadata/columns', { params: { catalog, schema, table } });
export const getSQLAutocomplete = (prefix: string) =>
  api.get('/api/metadata/sql-autocomplete', { params: { prefix } });

// ========== Queries ==========
export const executeQuery = (query: string, limit?: number) =>
  api.post('/api/queries/execute', { query, limit });

export const validateQuery = (query: string) =>
  api.post('/api/queries/validate', { query });

// ========== Semantic Models ==========
export const listModels = (category: string = 'production') =>
  api.get('/api/models/', { params: { category } });

export const getModel = (modelId: string, category: string = 'production') =>
  api.get(`/api/models/${modelId}`, { params: { category } });

export const createModel = (model: any) => api.post('/api/models/', model);

export const updateModel = (modelId: string, model: any) =>
  api.put(`/api/models/${modelId}`, model);

export const deleteModel = (modelId: string) => api.delete(`/api/models/${modelId}`);

export const downloadModelYAML = (modelId: string) =>
  api.get(`/api/models/${modelId}/download`, { responseType: 'blob' });

// ========== Metrics ==========
export const listMetrics = () => api.get('/api/metrics-explorer/metrics');

export const searchMetrics = (query: string, category?: string) =>
  api.get('/api/metrics-explorer/search', { params: { query, category } });

// ========== Genie (Natural Language) ==========
export const queryWithGenie = (naturalLanguageQuery: string) =>
  api.post('/api/genie/query', { query: naturalLanguageQuery });

export const suggestMetrics = (tableInfo: any) =>
  api.post('/api/genie/suggest-metrics', tableInfo);

// ========== Catalog ==========
export const getGoldTables = () => api.get('/api/catalog/gold-tables');

export const analyzeTable = (catalog: string, schema: string, table: string) =>
  api.post('/api/catalog/analyze-table', { catalog, schema, table });

export const generateModel = (analysisResult: any, customizations: any) =>
  api.post('/api/catalog/generate-model', { analysis: analysisResult, ...customizations });

// ========== Documentation ==========
export const generateDocumentation = (modelId: string, format: string) =>
  api.post('/api/documentation/generate', { model_id: modelId, format });

export const listDocumentation = () => api.get('/api/documentation/models');

// ========== Lineage ==========
export const getTableLineage = (catalog: string, schema: string, table: string) =>
  api.get('/api/lineage/tables/${catalog}.${schema}.${table}`);

export const getModelLineage = (modelId: string) =>
  api.get(`/api/lineage/models/${modelId}`);

export default api;
```

---

## 7. State Management

### React Query Configuration

```typescript
import { QueryClient } from '@tanstack/react-query';

export const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      // Disable automatic refetch on window focus for better performance
      refetchOnWindowFocus: false,

      // Retry failed requests once
      retry: 1,

      // Consider data stale after 5 minutes
      staleTime: 5 * 60 * 1000,

      // Keep unused data in cache for 10 minutes
      cacheTime: 10 * 60 * 1000,
    },
  },
});
```

### Usage Example

```typescript
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';

function MyComponent() {
  const queryClient = useQueryClient();

  // Query: Fetch data
  const { data, isLoading, error } = useQuery({
    queryKey: ['metrics'],
    queryFn: listMetrics,
  });

  // Mutation: Update data
  const mutation = useMutation({
    mutationFn: createModel,
    onSuccess: () => {
      // Invalidate and refetch
      queryClient.invalidateQueries({ queryKey: ['models'] });
    },
  });

  return (
    // Component JSX
  );
}
```

---

## 8. Styling Approach

### Tailwind CSS Setup

```javascript
// tailwind.config.js
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

### Hybrid Approach

1. **Tailwind CSS** for layout and utilities:
   ```tsx
   <div className="flex items-center justify-between p-4 bg-white rounded-lg shadow">
   ```

2. **Material-UI** for complex components:
   ```tsx
   <TextField fullWidth variant="outlined" />
   <Table>...</Table>
   <Modal>...</Modal>
   ```

---

## 9. TypeScript Interfaces

```typescript
// Common interfaces
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
  entities: Entity[];
  dimensions: Dimension[];
  measures: Measure[];
  metrics: Metric[];
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

---

## 10. Build Configuration

### package.json Scripts

```json
{
  "scripts": {
    "start": "react-scripts start",
    "build": "react-scripts build",
    "test": "react-scripts test",
    "eject": "react-scripts eject",
    "dev": "react-scripts start"
  }
}
```

### Environment Variables

```.env
REACT_APP_API_URL=http://localhost:8000
```

### TypeScript Configuration

```json
{
  "compilerOptions": {
    "target": "es5",
    "lib": ["dom", "dom.iterable", "esnext"],
    "allowJs": true,
    "skipLibCheck": true,
    "esModuleInterop": true,
    "allowSyntheticDefaultImports": true,
    "strict": true,
    "forceConsistentCasingInFileNames": true,
    "noFallthroughCasesInSwitch": true,
    "module": "esnext",
    "moduleResolution": "node",
    "resolveJsonModule": true,
    "isolatedModules": true,
    "noEmit": true,
    "jsx": "react-jsx"
  },
  "include": ["src"]
}
```

---

**Implementation Summary:**
- React 18 with TypeScript for type safety
- React Query for server state management
- Tailwind + MUI hybrid styling approach
- Modular component architecture
- Axios for HTTP requests with interceptors
- React Router for navigation

**Next:** Refer to `03-BACKEND-SPECIFICATION.md` for backend API details and `06-API-REFERENCE.md` for complete API documentation.
