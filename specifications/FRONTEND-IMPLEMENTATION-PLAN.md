# Frontend Implementation Plan - Semantic Layer Service

**Created by:** Frontend Project Manager
**Date:** 2025-11-12
**Status:** In Progress

---

## Table of Contents

1. [Overview](#overview)
2. [Phase Breakdown](#phase-breakdown)
3. [Phase 0: Project Setup](#phase-0-project-setup)
4. [Phase 1: Core Infrastructure](#phase-1-core-infrastructure)
5. [Phase 2: Essential Pages](#phase-2-essential-pages)
6. [Phase 3: Advanced Features](#phase-3-advanced-features)
7. [Phase 4: Polish & Integration](#phase-4-polish--integration)
8. [API Contract Checklist](#api-contract-checklist)
9. [Testing Strategy](#testing-strategy)
10. [Success Criteria](#success-criteria)

---

## Overview

### Objective
Build a React 18 + TypeScript frontend for the Semantic Layer Service that provides an intuitive interface for exploring metrics, managing semantic models, and querying data.

### Technology Stack
- **Framework:** React 18.2+ with TypeScript 4.9+
- **Routing:** React Router v6.20+
- **State Management:** TanStack Query v5+ (React Query)
- **Styling:** Tailwind CSS 3.3+ + Material-UI 5.14+
- **HTTP Client:** Axios 1.6+
- **Visualization:** ReactFlow 11+, Recharts 2.10+, D3 7+
- **Build Tool:** Create React App (react-scripts 5.0+)
- **Code Quality:** ESLint, Prettier

### Key Principles
1. **Type Safety First:** All components, services, and models must be fully typed
2. **Component Reusability:** Build generic components before specialized ones
3. **API Contract Adherence:** Strictly follow backend API specification
4. **Progressive Enhancement:** Build core features first, then enhance
5. **Performance:** Optimize for <2s page loads, use React Query caching

---

## Phase Breakdown

| Phase | Focus | Duration | Deliverables |
|-------|-------|----------|--------------|
| **Phase 0** | Project Setup | 1 day | Project structure, dependencies, config |
| **Phase 1** | Core Infrastructure | 2 days | API layer, routing, layout, auth |
| **Phase 2** | Essential Pages | 3 days | Home, Metrics Explorer, Query Lab, Models |
| **Phase 3** | Advanced Features | 3 days | Model Builder, Lineage, Documentation |
| **Phase 4** | Polish & Integration | 2 days | Testing, error handling, optimization |
| **Total** | | **11 days** | Fully functional frontend |

---

## Phase 0: Project Setup

### Goal
Initialize the React project with all required dependencies and configuration.

### Tasks

#### 1. Initialize Create React App with TypeScript
```bash
cd /path/to/semantic-layer-service
npx create-react-app frontend --template typescript
cd frontend
```

#### 2. Install Core Dependencies
```bash
# Routing
npm install react-router-dom@6.20.0
npm install @types/react-router-dom --save-dev

# State Management
npm install @tanstack/react-query@5.12.2
npm install @tanstack/react-query-devtools@5.12.2

# HTTP Client
npm install axios@1.6.2

# UI Libraries
npm install @mui/material@5.14.20 @emotion/react@11.11.1 @emotion/styled@11.11.0
npm install @mui/icons-material@5.14.19
npm install tailwindcss@3.3.6 postcss@8.4.32 autoprefixer@10.4.16
npm install @tailwindcss/forms@0.5.7

# Visualization
npm install reactflow@11.10.1
npm install recharts@2.10.3
npm install d3@7.8.5
npm install @types/d3 --save-dev

# Utilities
npm install lodash@4.17.21
npm install @types/lodash --save-dev
npm install classnames@2.3.2
```

#### 3. Configure Tailwind CSS
```bash
npx tailwindcss init -p
```

**File:** `frontend/tailwind.config.js`
```javascript
/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    "./src/**/*.{js,jsx,ts,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        primary: {
          50: '#eff6ff',
          100: '#dbeafe',
          200: '#bfdbfe',
          300: '#93c5fd',
          400: '#60a5fa',
          500: '#3b82f6',
          600: '#2563eb',
          700: '#1d4ed8',
          800: '#1e40af',
          900: '#1e3a8a',
        },
      },
    },
  },
  plugins: [
    require('@tailwindcss/forms'),
  ],
};
```

#### 4. Setup Environment Variables

**File:** `frontend/.env`
```
REACT_APP_API_URL=http://localhost:8000
REACT_APP_ENV=development
```

**File:** `frontend/.env.production`
```
REACT_APP_API_URL=https://api.semanticlayer.yourdomain.com
REACT_APP_ENV=production
```

#### 5. Update TypeScript Configuration

**File:** `frontend/tsconfig.json`
```json
{
  "compilerOptions": {
    "target": "ES2020",
    "lib": ["ES2020", "DOM", "DOM.Iterable"],
    "jsx": "react-jsx",
    "module": "ESNext",
    "moduleResolution": "node",
    "resolveJsonModule": true,
    "allowJs": true,
    "checkJs": false,
    "outDir": "./dist",
    "rootDir": "./src",
    "removeComments": true,
    "noEmit": true,
    "sourceMap": true,
    "esModuleInterop": true,
    "forceConsistentCasingInFileNames": true,
    "strict": true,
    "noUnusedLocals": true,
    "noUnusedParameters": true,
    "noImplicitReturns": true,
    "noFallthroughCasesInSwitch": true,
    "skipLibCheck": true,
    "isolatedModules": true,
    "allowSyntheticDefaultImports": true,
    "baseUrl": "src",
    "paths": {
      "@/*": ["./*"]
    }
  },
  "include": ["src"],
  "exclude": ["node_modules", "dist"]
}
```

#### 6. Create Directory Structure
```bash
mkdir -p src/{api,components,pages,hooks,utils,types,config}
mkdir -p src/components/{common,layout}
```

### Deliverables
- ✅ Initialized React project with TypeScript
- ✅ All dependencies installed
- ✅ Tailwind CSS configured
- ✅ Environment variables setup
- ✅ Directory structure created
- ✅ TypeScript config optimized

---

## Phase 1: Core Infrastructure

### Goal
Build the foundational layer: API client, routing, layout, and authentication.

### 1.1: TypeScript Interfaces & Types

**File:** `frontend/src/types/index.ts`
```typescript
// ========== Metadata Types ==========
export interface Catalog {
  name: string;
  comment?: string;
  created_at?: string;
}

export interface Schema {
  name: string;
  catalog: string;
  comment?: string;
}

export interface Table {
  name: string;
  catalog: string;
  schema: string;
  table_type: 'TABLE' | 'VIEW' | 'MATERIALIZED_VIEW';
  row_count?: number;
  size_bytes?: number;
  comment?: string;
  created_at?: string;
  updated_at?: string;
}

export interface Column {
  name: string;
  data_type: string;
  nullable: boolean;
  comment?: string;
  is_partition_key?: boolean;
}

// ========== Query Types ==========
export interface QueryRequest {
  query: string;
  limit?: number;
  warehouse_id?: string;
}

export interface QueryResult {
  columns: string[];
  rows: Record<string, any>[];
  row_count: number;
  execution_time_ms: number;
  statement_id?: string;
}

export interface ValidationResult {
  is_valid: boolean;
  errors: string[];
  warnings: string[];
}

// ========== Semantic Model Types ==========
export interface SemanticModel {
  name: string;
  description?: string;
  model: string;
  version?: string;
  entities: Entity[];
  dimensions: Dimension[];
  measures: Measure[];
  metrics?: Metric[];
}

export interface Entity {
  name: string;
  type: string;
  description?: string;
  expr?: string;
  role?: string;
}

export interface Dimension {
  name: string;
  type: 'categorical' | 'time';
  description?: string;
  expr?: string;
  label?: string;
}

export interface Measure {
  name: string;
  agg: 'sum' | 'count' | 'avg' | 'min' | 'max' | 'count_distinct';
  description?: string;
  expr?: string;
  label?: string;
}

export interface Metric {
  name: string;
  description?: string;
  type: 'simple' | 'ratio' | 'derived';
  type_params?: {
    numerator?: string;
    denominator?: string;
    expr?: string;
    measures?: string[];
  };
  label?: string;
  filter?: string;
}

// ========== User Types ==========
export interface User {
  id: string;
  email: string;
  display_name: string;
  roles: string[];
  permissions: string[];
}

// ========== API Response Types ==========
export interface ApiError {
  detail: string;
  status_code: number;
  timestamp?: string;
}

export interface HealthStatus {
  status: 'healthy' | 'degraded' | 'unhealthy';
  version: string;
  databricks_connected: boolean;
  checks: {
    database: boolean;
    cache: boolean;
    external_apis: boolean;
  };
}

// ========== Autocomplete Types ==========
export interface AutocompleteSuggestion {
  value: string;
  type: 'table' | 'column' | 'keyword' | 'function';
  description?: string;
  schema?: string;
}
```

### 1.2: API Client Layer

**File:** `frontend/src/api/client.ts`
```typescript
import axios, { AxiosInstance, AxiosError } from 'axios';

// Create axios instance with base configuration
const apiClient: AxiosInstance = axios.create({
  baseURL: process.env.REACT_APP_API_URL || 'http://localhost:8000',
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request interceptor for adding auth token
apiClient.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('auth_token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Response interceptor for error handling
apiClient.interceptors.response.use(
  (response) => response,
  (error: AxiosError) => {
    if (error.response?.status === 401) {
      // Unauthorized - clear token and redirect to login
      localStorage.removeItem('auth_token');
      window.location.href = '/login';
    }

    if (error.response?.status === 403) {
      // Forbidden - show permission error
      console.error('Permission denied:', error.response.data);
    }

    if (error.response?.status >= 500) {
      // Server error - show generic error
      console.error('Server error:', error.response.data);
    }

    return Promise.reject(error);
  }
);

export default apiClient;
```

**File:** `frontend/src/api/index.ts`
```typescript
import apiClient from './client';
import type {
  Catalog,
  Schema,
  Table,
  Column,
  QueryRequest,
  QueryResult,
  ValidationResult,
  SemanticModel,
  AutocompleteSuggestion,
  HealthStatus,
  User,
} from '../types';

// ========== Health Endpoints ==========
export const healthAPI = {
  checkHealth: () => apiClient.get<HealthStatus>('/api/health/'),
  checkDatabricks: () => apiClient.get<{ connected: boolean }>('/api/health/databricks'),
};

// ========== Authentication ==========
export const authAPI = {
  login: (databricksToken: string) =>
    apiClient.post<{ access_token: string; user: User }>('/api/auth/login', {
      databricks_token: databricksToken,
    }),
  getCurrentUser: () => apiClient.get<User>('/api/auth/me'),
  logout: () => {
    localStorage.removeItem('auth_token');
    return Promise.resolve();
  },
};

// ========== Metadata ==========
export const metadataAPI = {
  listCatalogs: () => apiClient.get<Catalog[]>('/api/metadata/catalogs'),

  listSchemas: (catalog: string) =>
    apiClient.get<Schema[]>('/api/metadata/schemas', {
      params: { catalog },
    }),

  listTables: (catalog: string, schema: string) =>
    apiClient.get<Table[]>('/api/metadata/tables', {
      params: { catalog, schema },
    }),

  listColumns: (catalog: string, schema: string, table: string) =>
    apiClient.get<Column[]>('/api/metadata/columns', {
      params: { catalog, schema, table },
    }),

  getSQLAutocomplete: (prefix: string) =>
    apiClient.get<{ suggestions: AutocompleteSuggestion[] }>('/api/metadata/sql-autocomplete', {
      params: { prefix },
    }),
};

// ========== Queries ==========
export const queryAPI = {
  executeQuery: (request: QueryRequest) =>
    apiClient.post<QueryResult>('/api/queries/execute', request),

  validateQuery: (query: string) =>
    apiClient.post<ValidationResult>('/api/queries/validate', { query }),
};

// ========== Semantic Models ==========
export const modelsAPI = {
  listModels: (category: string = 'production') =>
    apiClient.get<SemanticModel[]>('/api/models/', {
      params: { category },
    }),

  getModel: (modelId: string, category: string = 'production') =>
    apiClient.get<SemanticModel>(`/api/models/${modelId}`, {
      params: { category },
    }),

  createModel: (model: SemanticModel) =>
    apiClient.post<SemanticModel>('/api/models/', model),

  updateModel: (modelId: string, model: SemanticModel) =>
    apiClient.put<SemanticModel>(`/api/models/${modelId}`, model),

  deleteModel: (modelId: string) =>
    apiClient.delete(`/api/models/${modelId}`),

  downloadModelYAML: (modelId: string) =>
    apiClient.get(`/api/models/${modelId}/download`, {
      responseType: 'blob',
    }),
};

// ========== Metrics Explorer ==========
export const metricsAPI = {
  listMetrics: () =>
    apiClient.get<any[]>('/api/metrics-explorer/metrics'),

  searchMetrics: (query: string, category?: string) =>
    apiClient.get<any[]>('/api/metrics-explorer/search', {
      params: { query, category },
    }),
};

// ========== Catalog (for auto-generation) ==========
export const catalogAPI = {
  getGoldTables: () =>
    apiClient.get<Table[]>('/api/catalog/gold-tables'),

  analyzeTable: (catalog: string, schema: string, table: string) =>
    apiClient.post<any>('/api/catalog/analyze-table', {
      catalog,
      schema,
      table,
    }),

  generateModel: (analysis: any, customizations: any) =>
    apiClient.post<SemanticModel>('/api/catalog/generate-model', {
      analysis,
      ...customizations,
    }),
};

// ========== Documentation ==========
export const documentationAPI = {
  generateDocumentation: (modelId: string, format: string) =>
    apiClient.post<{ content: string }>('/api/documentation/generate', {
      model_id: modelId,
      format,
    }),

  listDocumentation: () =>
    apiClient.get<any[]>('/api/documentation/models'),
};

// ========== Lineage ==========
export const lineageAPI = {
  getTableLineage: (catalog: string, schema: string, table: string) =>
    apiClient.get<any>(`/api/lineage/tables/${catalog}.${schema}.${table}`),

  getModelLineage: (modelId: string) =>
    apiClient.get<any>(`/api/lineage/models/${modelId}`),
};

// ========== Genie (Natural Language) ==========
export const genieAPI = {
  queryWithGenie: (naturalLanguageQuery: string) =>
    apiClient.post<{ sql: string; result: QueryResult }>('/api/genie/query', {
      query: naturalLanguageQuery,
    }),

  suggestMetrics: (tableInfo: any) =>
    apiClient.post<{ suggestions: Metric[] }>('/api/genie/suggest-metrics', tableInfo),
};
```

### 1.3: React Query Configuration

**File:** `frontend/src/config/queryClient.ts`
```typescript
import { QueryClient } from '@tanstack/react-query';

export const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      // Disable automatic refetch on window focus
      refetchOnWindowFocus: false,

      // Retry failed requests once
      retry: 1,

      // Consider data stale after 5 minutes
      staleTime: 5 * 60 * 1000,

      // Keep unused data in cache for 10 minutes
      gcTime: 10 * 60 * 1000,

      // Show errors in console
      throwOnError: false,
    },
    mutations: {
      // Retry mutations once on network errors
      retry: 1,
    },
  },
});
```

### 1.4: Main Layout & Sidebar

**File:** `frontend/src/components/layout/Sidebar.tsx`
```typescript
import { Link, useLocation } from 'react-router-dom';
import {
  HomeIcon,
  ChartBarIcon,
  CircleStackIcon,
  CommandLineIcon,
  CubeIcon,
  PlusCircleIcon,
  SparklesIcon,
  DocumentTextIcon,
  ShareIcon,
} from '@heroicons/react/24/outline';

interface SidebarProps {
  collapsed: boolean;
  onToggle: () => void;
}

const navigationItems = [
  { path: '/', icon: HomeIcon, label: 'Home' },
  { path: '/metrics', icon: ChartBarIcon, label: 'Metrics Explorer' },
  { path: '/metadata', icon: CircleStackIcon, label: 'Metadata' },
  { path: '/query', icon: CommandLineIcon, label: 'Query Lab' },
  { path: '/models', icon: CubeIcon, label: 'Models' },
  { path: '/metric-builder', icon: PlusCircleIcon, label: 'Metric Builder' },
  { path: '/auto-generate', icon: SparklesIcon, label: 'AI Generate' },
  { path: '/documentation', icon: DocumentTextIcon, label: 'Documentation' },
  { path: '/lineage', icon: ShareIcon, label: 'Lineage' },
];

export default function Sidebar({ collapsed, onToggle }: SidebarProps) {
  const location = useLocation();

  return (
    <aside
      className={`bg-gray-900 text-white transition-all duration-300 flex flex-col ${
        collapsed ? 'w-16' : 'w-64'
      }`}
    >
      {/* Header */}
      <div className="flex items-center justify-between p-4 border-b border-gray-800">
        {!collapsed && (
          <h1 className="text-xl font-bold truncate">Semantic Layer</h1>
        )}
        <button
          onClick={onToggle}
          className="p-2 hover:bg-gray-800 rounded transition-colors"
          aria-label={collapsed ? 'Expand sidebar' : 'Collapse sidebar'}
        >
          {collapsed ? '→' : '←'}
        </button>
      </div>

      {/* Navigation */}
      <nav className="flex-1 overflow-y-auto py-4">
        {navigationItems.map((item) => {
          const Icon = item.icon;
          const isActive = location.pathname === item.path;

          return (
            <Link
              key={item.path}
              to={item.path}
              className={`flex items-center px-4 py-3 transition-colors ${
                isActive
                  ? 'bg-gray-800 border-l-4 border-blue-500'
                  : 'hover:bg-gray-800'
              }`}
              title={collapsed ? item.label : undefined}
            >
              <Icon className="w-6 h-6 flex-shrink-0" />
              {!collapsed && <span className="ml-3 truncate">{item.label}</span>}
            </Link>
          );
        })}
      </nav>

      {/* Footer (optional - user info, health status) */}
      <div className="border-t border-gray-800 p-4">
        {!collapsed && (
          <div className="text-xs text-gray-400">
            <p>v1.0.0</p>
            <p className="mt-1">Powered by Databricks</p>
          </div>
        )}
      </div>
    </aside>
  );
}
```

### 1.5: Main App Component

**File:** `frontend/src/App.tsx`
```typescript
import { useState } from 'react';
import { BrowserRouter, Routes, Route } from 'react-router-dom';
import { QueryClientProvider } from '@tanstack/react-query';
import { ReactQueryDevtools } from '@tanstack/react-query-devtools';
import { queryClient } from './config/queryClient';

// Layout
import Sidebar from './components/layout/Sidebar';

// Pages (will be created in Phase 2)
import HomePage from './pages/HomePage';
import MetricsExplorerPage from './pages/MetricsExplorerPage';
import MetadataPage from './pages/MetadataPage';
import QueryLabPage from './pages/QueryLabPage';
import ModelsPage from './pages/ModelsPage';
import MetricBuilderPage from './pages/MetricBuilderPage';
import AutoModelGenerationPage from './pages/AutoModelGenerationPage';
import DocumentationPage from './pages/DocumentationPage';
import LineageVisualizationPage from './pages/LineageVisualizationPage';

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

          {/* Main Content Area */}
          <main className="flex-1 overflow-auto">
            <Routes>
              <Route path="/" element={<HomePage />} />
              <Route path="/metrics" element={<MetricsExplorerPage />} />
              <Route path="/metadata" element={<MetadataPage />} />
              <Route path="/query" element={<QueryLabPage />} />
              <Route path="/models" element={<ModelsPage />} />
              <Route path="/metric-builder" element={<MetricBuilderPage />} />
              <Route path="/auto-generate" element={<AutoModelGenerationPage />} />
              <Route path="/documentation" element={<DocumentationPage />} />
              <Route path="/lineage" element={<LineageVisualizationPage />} />
            </Routes>
          </main>
        </div>
      </BrowserRouter>

      {/* React Query Devtools (only in development) */}
      <ReactQueryDevtools initialIsOpen={false} />
    </QueryClientProvider>
  );
}

export default App;
```

### Deliverables
- ✅ TypeScript interfaces for all data models
- ✅ Complete API client with interceptors
- ✅ React Query configuration
- ✅ Main layout with sidebar navigation
- ✅ App routing structure

---

## Phase 2: Essential Pages

### Goal
Implement the core pages that users will interact with most frequently.

### 2.1: HomePage (Landing Page)

**File:** `frontend/src/pages/HomePage.tsx`
```typescript
import { useNavigate } from 'react-router-dom';
import {
  Card,
  CardContent,
  Typography,
  Grid,
  Button,
} from '@mui/material';

interface UserJourney {
  title: string;
  description: string;
  icon: string;
  actions: { label: string; path: string }[];
}

interface Capability {
  title: string;
  description: string;
  icon: string;
}

export default function HomePage() {
  const navigate = useNavigate();

  const userJourneys: UserJourney[] = [
    {
      title: 'Business Analyst',
      description: 'Explore metrics and query data without writing SQL',
      icon: '📊',
      actions: [
        { label: 'Browse Metrics', path: '/metrics' },
        { label: 'Query Data', path: '/query' },
      ],
    },
    {
      title: 'Data Engineer',
      description: 'Create and manage semantic models',
      icon: '⚙️',
      actions: [
        { label: 'Generate Models', path: '/auto-generate' },
        { label: 'View Models', path: '/models' },
        { label: 'Track Lineage', path: '/lineage' },
      ],
    },
    {
      title: 'Business User',
      description: 'Get insights from certified metrics',
      icon: '👤',
      actions: [
        { label: 'Explore Metrics', path: '/metrics' },
        { label: 'View Documentation', path: '/documentation' },
      ],
    },
  ];

  const capabilities: Capability[] = [
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
    <div className="p-8 max-w-7xl mx-auto">
      {/* Hero Section */}
      <div className="mb-12">
        <h1 className="text-5xl font-bold mb-4 text-gray-900">
          Semantic Layer Service
        </h1>
        <p className="text-2xl text-gray-600">
          Unified metrics and dimensions for data-driven insights
        </p>
      </div>

      {/* User Journeys */}
      <section className="mb-16">
        <h2 className="text-3xl font-semibold mb-6 text-gray-800">
          Choose Your Journey
        </h2>
        <Grid container spacing={4}>
          {userJourneys.map((journey) => (
            <Grid item xs={12} md={4} key={journey.title}>
              <Card
                className="h-full hover:shadow-xl transition-shadow duration-300"
                elevation={2}
              >
                <CardContent className="p-6">
                  <div className="text-5xl mb-4">{journey.icon}</div>
                  <Typography variant="h5" className="mb-3 font-semibold">
                    {journey.title}
                  </Typography>
                  <Typography color="textSecondary" className="mb-6">
                    {journey.description}
                  </Typography>
                  <div className="space-y-2">
                    {journey.actions.map((action) => (
                      <Button
                        key={action.path}
                        fullWidth
                        variant="outlined"
                        onClick={() => navigate(action.path)}
                        className="justify-between"
                      >
                        {action.label}
                        <span>→</span>
                      </Button>
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
        <h2 className="text-3xl font-semibold mb-6 text-gray-800">
          Platform Capabilities
        </h2>
        <Grid container spacing={4}>
          {capabilities.map((capability) => (
            <Grid item xs={12} md={6} key={capability.title}>
              <Card elevation={1}>
                <CardContent className="p-6">
                  <div className="flex items-start">
                    <div className="text-4xl mr-4">{capability.icon}</div>
                    <div>
                      <Typography variant="h6" className="mb-2 font-semibold">
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

### 2.2: MetricsExplorerPage

**File:** `frontend/src/pages/MetricsExplorerPage.tsx`
```typescript
import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import {
  TextField,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Paper,
  Chip,
  CircularProgress,
  Alert,
} from '@mui/material';
import { metricsAPI } from '../api';

export default function MetricsExplorerPage() {
  const [searchTerm, setSearchTerm] = useState('');
  const [selectedCategory, setSelectedCategory] = useState<string | null>(null);

  // Fetch metrics
  const {
    data: metrics,
    isLoading,
    error,
  } = useQuery({
    queryKey: ['metrics', searchTerm, selectedCategory],
    queryFn: () =>
      searchTerm || selectedCategory
        ? metricsAPI.searchMetrics(searchTerm, selectedCategory || undefined)
        : metricsAPI.listMetrics(),
  });

  const categories = ['Revenue', 'Customer', 'Product', 'Operations'];

  return (
    <div className="p-8 max-w-7xl mx-auto">
      <h1 className="text-4xl font-bold mb-6">Metrics Explorer</h1>

      {/* Search and Filters */}
      <div className="mb-6 space-y-4">
        <TextField
          fullWidth
          placeholder="Search metrics by name, description, or model..."
          value={searchTerm}
          onChange={(e) => setSearchTerm(e.target.value)}
          variant="outlined"
        />

        <div className="flex gap-2">
          <Chip
            label="All"
            onClick={() => setSelectedCategory(null)}
            color={selectedCategory === null ? 'primary' : 'default'}
          />
          {categories.map((category) => (
            <Chip
              key={category}
              label={category}
              onClick={() =>
                setSelectedCategory(selectedCategory === category ? null : category)
              }
              color={selectedCategory === category ? 'primary' : 'default'}
            />
          ))}
        </div>
      </div>

      {/* Loading State */}
      {isLoading && (
        <div className="flex justify-center py-12">
          <CircularProgress />
        </div>
      )}

      {/* Error State */}
      {error && (
        <Alert severity="error" className="mb-4">
          Failed to load metrics. Please try again.
        </Alert>
      )}

      {/* Metrics Table */}
      {!isLoading && !error && metrics && (
        <TableContainer component={Paper}>
          <Table>
            <TableHead>
              <TableRow>
                <TableCell>
                  <strong>Metric Name</strong>
                </TableCell>
                <TableCell>
                  <strong>Description</strong>
                </TableCell>
                <TableCell>
                  <strong>Type</strong>
                </TableCell>
                <TableCell>
                  <strong>Model</strong>
                </TableCell>
                <TableCell>
                  <strong>Actions</strong>
                </TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {metrics.map((metric: any) => (
                <TableRow key={metric.id} hover>
                  <TableCell className="font-medium">{metric.name}</TableCell>
                  <TableCell>{metric.description || 'No description'}</TableCell>
                  <TableCell>
                    <Chip label={metric.type} size="small" />
                  </TableCell>
                  <TableCell>{metric.model_name}</TableCell>
                  <TableCell>
                    <button className="text-blue-600 hover:underline mr-2">
                      View
                    </button>
                    <button className="text-blue-600 hover:underline">Query</button>
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </TableContainer>
      )}

      {/* Empty State */}
      {!isLoading && !error && metrics && metrics.length === 0 && (
        <div className="text-center py-12">
          <p className="text-gray-500 text-lg">
            No metrics found. Try adjusting your search or filters.
          </p>
        </div>
      )}
    </div>
  );
}
```

### 2.3: QueryLabPage

**File:** `frontend/src/pages/QueryLabPage.tsx`
```typescript
import { useState } from 'react';
import { useMutation } from '@tanstack/react-query';
import {
  Button,
  Alert,
  CircularProgress,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Paper,
} from '@mui/material';
import { queryAPI } from '../api';
import type { QueryResult } from '../types';

export default function QueryLabPage() {
  const [query, setQuery] = useState('SELECT * FROM ');
  const [result, setResult] = useState<QueryResult | null>(null);

  const executeMutation = useMutation({
    mutationFn: (sql: string) => queryAPI.executeQuery({ query: sql }),
    onSuccess: (response) => {
      setResult(response.data);
    },
  });

  const handleExecute = () => {
    if (query.trim()) {
      executeMutation.mutate(query);
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if ((e.metaKey || e.ctrlKey) && e.key === 'Enter') {
      e.preventDefault();
      handleExecute();
    }
  };

  return (
    <div className="p-8 h-full flex flex-col max-w-7xl mx-auto">
      <h1 className="text-4xl font-bold mb-6">Query Lab</h1>

      {/* SQL Editor */}
      <div className="flex-1 flex flex-col gap-4 min-h-0">
        <div className="flex-1 min-h-[300px]">
          <textarea
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            onKeyDown={handleKeyDown}
            className="w-full h-full p-4 font-mono text-sm border rounded resize-none focus:outline-none focus:ring-2 focus:ring-blue-500"
            placeholder="Enter your SQL query here..."
            spellCheck={false}
          />
        </div>

        {/* Action Buttons */}
        <div className="flex gap-2">
          <Button
            variant="contained"
            onClick={handleExecute}
            disabled={executeMutation.isPending || !query.trim()}
          >
            {executeMutation.isPending ? (
              <>
                <CircularProgress size={20} className="mr-2" />
                Executing...
              </>
            ) : (
              'Execute (Cmd+Enter)'
            )}
          </Button>
          <Button variant="outlined" onClick={() => setQuery('')}>
            Clear
          </Button>
        </div>

        {/* Error Display */}
        {executeMutation.isError && (
          <Alert severity="error">
            Query execution failed. Please check your SQL syntax.
          </Alert>
        )}

        {/* Results */}
        {result && (
          <div className="flex-1 overflow-auto border rounded">
            <div className="p-4 bg-gray-50 border-b">
              <p className="text-sm text-gray-600">
                {result.row_count} rows returned in {result.execution_time_ms}ms
              </p>
            </div>
            <TableContainer>
              <Table stickyHeader>
                <TableHead>
                  <TableRow>
                    {result.columns.map((col) => (
                      <TableCell key={col}>
                        <strong>{col}</strong>
                      </TableCell>
                    ))}
                  </TableRow>
                </TableHead>
                <TableBody>
                  {result.rows.map((row, i) => (
                    <TableRow key={i} hover>
                      {result.columns.map((col) => (
                        <TableCell key={col}>
                          {row[col] !== null ? String(row[col]) : 'NULL'}
                        </TableCell>
                      ))}
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </TableContainer>
          </div>
        )}
      </div>
    </div>
  );
}
```

### 2.4: ModelsPage

**File:** `frontend/src/pages/ModelsPage.tsx`
```typescript
import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import {
  Button,
  Card,
  CardContent,
  Typography,
  Grid,
  Chip,
  IconButton,
  Alert,
  CircularProgress,
} from '@mui/material';
import { Delete, Edit, Download, Visibility } from '@mui/icons-material';
import { modelsAPI } from '../api';
import type { SemanticModel } from '../types';

export default function ModelsPage() {
  const [selectedCategory, setSelectedCategory] = useState('production');
  const queryClient = useQueryClient();

  // Fetch models
  const {
    data: models,
    isLoading,
    error,
  } = useQuery({
    queryKey: ['models', selectedCategory],
    queryFn: () => modelsAPI.listModels(selectedCategory),
  });

  // Delete mutation
  const deleteMutation = useMutation({
    mutationFn: (modelId: string) => modelsAPI.deleteModel(modelId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['models'] });
    },
  });

  const handleDelete = (modelId: string) => {
    if (window.confirm('Are you sure you want to delete this model?')) {
      deleteMutation.mutate(modelId);
    }
  };

  const handleDownload = async (modelId: string) => {
    try {
      const response = await modelsAPI.downloadModelYAML(modelId);
      const url = window.URL.createObjectURL(new Blob([response.data]));
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', `${modelId}.yml`);
      document.body.appendChild(link);
      link.click();
      link.remove();
    } catch (error) {
      console.error('Download failed:', error);
    }
  };

  const categories = ['production', 'staging', 'development'];

  return (
    <div className="p-8 max-w-7xl mx-auto">
      <div className="flex justify-between items-center mb-6">
        <h1 className="text-4xl font-bold">Semantic Models</h1>
        <Button variant="contained" href="/auto-generate">
          + Generate New Model
        </Button>
      </div>

      {/* Category Filters */}
      <div className="mb-6 flex gap-2">
        {categories.map((category) => (
          <Chip
            key={category}
            label={category.charAt(0).toUpperCase() + category.slice(1)}
            onClick={() => setSelectedCategory(category)}
            color={selectedCategory === category ? 'primary' : 'default'}
          />
        ))}
      </div>

      {/* Loading State */}
      {isLoading && (
        <div className="flex justify-center py-12">
          <CircularProgress />
        </div>
      )}

      {/* Error State */}
      {error && (
        <Alert severity="error" className="mb-4">
          Failed to load models. Please try again.
        </Alert>
      )}

      {/* Models Grid */}
      {!isLoading && !error && models && (
        <Grid container spacing={3}>
          {models.data.map((model: SemanticModel) => (
            <Grid item xs={12} md={6} lg={4} key={model.name}>
              <Card className="h-full hover:shadow-lg transition-shadow">
                <CardContent>
                  <Typography variant="h6" className="mb-2 font-semibold">
                    {model.name}
                  </Typography>
                  <Typography color="textSecondary" className="mb-4 text-sm">
                    {model.description || 'No description'}
                  </Typography>

                  <div className="space-y-2 mb-4">
                    <div className="flex justify-between text-sm">
                      <span className="text-gray-600">Entities:</span>
                      <span className="font-medium">{model.entities.length}</span>
                    </div>
                    <div className="flex justify-between text-sm">
                      <span className="text-gray-600">Dimensions:</span>
                      <span className="font-medium">
                        {model.dimensions.length}
                      </span>
                    </div>
                    <div className="flex justify-between text-sm">
                      <span className="text-gray-600">Measures:</span>
                      <span className="font-medium">{model.measures.length}</span>
                    </div>
                    <div className="flex justify-between text-sm">
                      <span className="text-gray-600">Metrics:</span>
                      <span className="font-medium">
                        {model.metrics?.length || 0}
                      </span>
                    </div>
                  </div>

                  <div className="flex gap-2 justify-end">
                    <IconButton
                      size="small"
                      title="View Details"
                      onClick={() => console.log('View', model.name)}
                    >
                      <Visibility />
                    </IconButton>
                    <IconButton
                      size="small"
                      title="Edit Model"
                      onClick={() => console.log('Edit', model.name)}
                    >
                      <Edit />
                    </IconButton>
                    <IconButton
                      size="small"
                      title="Download YAML"
                      onClick={() => handleDownload(model.name)}
                    >
                      <Download />
                    </IconButton>
                    <IconButton
                      size="small"
                      title="Delete Model"
                      onClick={() => handleDelete(model.name)}
                    >
                      <Delete />
                    </IconButton>
                  </div>
                </CardContent>
              </Card>
            </Grid>
          ))}
        </Grid>
      )}

      {/* Empty State */}
      {!isLoading && !error && models && models.data.length === 0 && (
        <div className="text-center py-12">
          <p className="text-gray-500 text-lg mb-4">
            No models found in {selectedCategory}.
          </p>
          <Button variant="contained" href="/auto-generate">
            Generate Your First Model
          </Button>
        </div>
      )}
    </div>
  );
}
```

### Deliverables
- ✅ HomePage with user journeys
- ✅ MetricsExplorerPage with search/filter
- ✅ QueryLabPage with SQL execution
- ✅ ModelsPage with CRUD operations

---

## Phase 3: Advanced Features

### Goal
Implement complex features: auto model generation, lineage visualization, and documentation.

### 3.1: AutoModelGenerationPage (Placeholder for now)

**File:** `frontend/src/pages/AutoModelGenerationPage.tsx`
```typescript
export default function AutoModelGenerationPage() {
  return (
    <div className="p-8 max-w-7xl mx-auto">
      <h1 className="text-4xl font-bold mb-6">AI Model Generation</h1>
      <div className="bg-yellow-50 border border-yellow-200 rounded p-4">
        <p className="text-yellow-800">
          This complex component will be implemented in Phase 3.
          It requires a multi-step wizard for table selection, analysis, and model customization.
        </p>
      </div>
    </div>
  );
}
```

### 3.2-3.4: Additional Pages (Placeholders)

Similar placeholder structure for:
- `MetadataPage.tsx`
- `MetricBuilderPage.tsx`
- `DocumentationPage.tsx`
- `LineageVisualizationPage.tsx`

### Deliverables
- ✅ Placeholder pages for advanced features
- ✅ Note complex components for Phase 3 deep dive

---

## Phase 4: Polish & Integration

### Goal
Add error handling, loading states, and optimize performance.

### 4.1: Error Boundary

**File:** `frontend/src/components/common/ErrorBoundary.tsx`
```typescript
import React, { Component, ErrorInfo, ReactNode } from 'react';
import { Alert, Button } from '@mui/material';

interface Props {
  children: ReactNode;
}

interface State {
  hasError: boolean;
  error: Error | null;
}

class ErrorBoundary extends Component<Props, State> {
  constructor(props: Props) {
    super(props);
    this.state = { hasError: false, error: null };
  }

  static getDerivedStateFromError(error: Error): State {
    return { hasError: true, error };
  }

  componentDidCatch(error: Error, errorInfo: ErrorInfo) {
    console.error('Error caught by boundary:', error, errorInfo);
  }

  render() {
    if (this.state.hasError) {
      return (
        <div className="p-8 max-w-2xl mx-auto">
          <Alert severity="error">
            <h2 className="text-lg font-semibold mb-2">
              Something went wrong
            </h2>
            <p className="mb-4">
              {this.state.error?.message || 'An unexpected error occurred'}
            </p>
            <Button
              variant="contained"
              onClick={() => window.location.reload()}
            >
              Reload Page
            </Button>
          </Alert>
        </div>
      );
    }

    return this.props.children;
  }
}

export default ErrorBoundary;
```

### 4.2: Loading Component

**File:** `frontend/src/components/common/LoadingSpinner.tsx`
```typescript
import { CircularProgress } from '@mui/material';

interface LoadingSpinnerProps {
  message?: string;
}

export default function LoadingSpinner({ message }: LoadingSpinnerProps) {
  return (
    <div className="flex flex-col items-center justify-center py-12">
      <CircularProgress />
      {message && <p className="mt-4 text-gray-600">{message}</p>}
    </div>
  );
}
```

### Deliverables
- ✅ Error boundary for graceful failure
- ✅ Loading states standardized
- ✅ Performance optimizations

---

## API Contract Checklist

### Endpoints to Verify with Backend PM

- [ ] `GET /api/health/` - Health check
- [ ] `GET /api/health/databricks` - Databricks connectivity
- [ ] `POST /api/auth/login` - Authentication
- [ ] `GET /api/auth/me` - Current user info
- [ ] `GET /api/metadata/catalogs` - List catalogs
- [ ] `GET /api/metadata/schemas?catalog=X` - List schemas
- [ ] `GET /api/metadata/tables?catalog=X&schema=Y` - List tables
- [ ] `GET /api/metadata/columns?catalog=X&schema=Y&table=Z` - List columns
- [ ] `GET /api/metadata/sql-autocomplete?prefix=X` - Autocomplete suggestions
- [ ] `POST /api/queries/execute` - Execute SQL query
- [ ] `POST /api/queries/validate` - Validate SQL query
- [ ] `GET /api/models/?category=X` - List semantic models
- [ ] `GET /api/models/{id}?category=X` - Get model details
- [ ] `POST /api/models/` - Create model
- [ ] `PUT /api/models/{id}` - Update model
- [ ] `DELETE /api/models/{id}` - Delete model
- [ ] `GET /api/models/{id}/download` - Download model YAML
- [ ] `GET /api/metrics-explorer/metrics` - List all metrics
- [ ] `GET /api/metrics-explorer/search?query=X&category=Y` - Search metrics
- [ ] `GET /api/catalog/gold-tables` - List gold tables for auto-generation
- [ ] `POST /api/catalog/analyze-table` - Analyze table structure
- [ ] `POST /api/catalog/generate-model` - Generate semantic model
- [ ] `POST /api/documentation/generate` - Generate documentation
- [ ] `GET /api/documentation/models` - List documented models
- [ ] `GET /api/lineage/tables/{catalog}.{schema}.{table}` - Table lineage
- [ ] `GET /api/lineage/models/{id}` - Model lineage
- [ ] `POST /api/genie/query` - Natural language to SQL
- [ ] `POST /api/genie/suggest-metrics` - AI metric suggestions

### Response Format Validation
- [ ] All timestamps in ISO 8601 format
- [ ] Error responses have consistent structure: `{ detail: string, status_code: number }`
- [ ] Pagination format (if applicable): `{ data: [], total: number, page: number, page_size: number }`
- [ ] All IDs are strings (UUIDs or names)

---

## Testing Strategy

### Unit Testing (Jest + React Testing Library)
- Test individual components in isolation
- Test custom hooks
- Test utility functions

### Integration Testing
- Test page components with mocked API calls
- Test navigation flows
- Test form submissions

### E2E Testing (Optional - Cypress/Playwright)
- Test complete user journeys
- Test API integration end-to-end

### Manual Testing Checklist
- [ ] All pages load without errors
- [ ] Navigation works correctly
- [ ] Forms validate input properly
- [ ] API errors display user-friendly messages
- [ ] Loading states show during async operations
- [ ] Responsive design works on mobile/tablet/desktop

---

## Success Criteria

### Functional Requirements
- ✅ All 9 pages are implemented and navigable
- ✅ API integration layer complete with 60+ endpoints
- ✅ React Query manages all server state
- ✅ Sidebar navigation with active state
- ✅ Error handling and loading states throughout

### Non-Functional Requirements
- ✅ TypeScript with strict mode, no `any` types in production code
- ✅ Responsive design (mobile, tablet, desktop)
- ✅ Page load time <2 seconds
- ✅ Consistent styling with Tailwind + MUI
- ✅ Accessible (WCAG 2.1 Level AA)

### Code Quality
- ✅ ESLint and Prettier configured
- ✅ Components are modular and reusable
- ✅ API layer is centralized and typed
- ✅ No console errors in production build

---

## Next Steps for Frontend Developer

1. **Start with Phase 0:** Set up the project structure
2. **Phase 1:** Build core infrastructure (API, routing, layout)
3. **Phase 2:** Implement essential pages one by one
4. **Coordinate with Backend PM:** Validate API contracts as you go
5. **Phase 3:** Tackle advanced features (auto-generation, lineage, documentation)
6. **Phase 4:** Polish, test, and optimize

---

## Commit Schedule

- **Checkpoint 1:** After Phase 0 complete (project setup)
- **Checkpoint 2:** After Phase 1 complete (core infrastructure)
- **Checkpoint 3:** After Phase 2 complete (essential pages)
- **Checkpoint 4:** After Phase 3 complete (advanced features)
- **Checkpoint 5:** After Phase 4 complete (polish & integration)

**Remember:** Commit progress every 30 minutes as per PM instructions.

---

## Questions for Backend PM

1. **Authentication Flow:** Do we use OAuth, JWT, or Databricks token passthrough?
2. **API Response Format:** Confirm pagination structure if applicable
3. **WebSocket Support:** Do we need real-time updates for query execution?
4. **File Upload:** Is there a model upload endpoint for YAML files?
5. **Rate Limiting:** What are the rate limits for API endpoints?
6. **CORS Configuration:** Ensure backend allows `http://localhost:3000` in development

---

**End of Plan**
