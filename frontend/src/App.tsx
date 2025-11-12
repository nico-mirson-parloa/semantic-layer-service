import React, { useState } from 'react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { BrowserRouter as Router, Routes, Route, Link, useLocation } from 'react-router-dom';
import HomePage from './pages/HomePage';
import MetricsExplorerPage from './pages/MetricsExplorerPage';
import MetadataPage from './pages/MetadataPage';
import QueryLabPage from './pages/QueryLabPage';
import ModelsPage from './pages/ModelsPage';
import MetricBuilderPage from './pages/MetricBuilderPage';
import { AutoModelGeneration } from './components/AutoModelGeneration';
import DocumentationPage from './pages/DocumentationPage';
import LineageVisualizationPage from './pages/LineageVisualizationPage';
import { useQuery } from '@tanstack/react-query';
import { healthCheck, databricksHealthCheck } from './services/api';
import {
  HomeIcon,
  ChartBarIcon,
  CircleStackIcon,
  BeakerIcon,
  CubeIcon,
  WrenchIcon,
  SparklesIcon,
  DocumentTextIcon,
  ShareIcon,
  ChevronLeftIcon,
  ChevronRightIcon,
  CheckCircleIcon,
  XCircleIcon,
  ExclamationCircleIcon,
  SunIcon,
  MoonIcon
} from '@heroicons/react/24/outline';
import { useTheme } from './contexts/ThemeContext';

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      refetchOnWindowFocus: false,
      retry: 1,
    },
  },
});

// Navigation items configuration
const navigationItems = [
  { 
    path: '/', 
    name: 'Home', 
    icon: HomeIcon,
    description: 'Overview and status'
  },
  { 
    path: '/metrics', 
    name: 'Metrics Explorer', 
    icon: ChartBarIcon,
    description: 'Explore and analyze metrics'
  },
  { 
    path: '/metadata', 
    name: 'Metadata Explorer', 
    icon: CircleStackIcon,
    description: 'Browse catalogs and schemas'
  },
  { 
    path: '/query', 
    name: 'Query Lab', 
    icon: BeakerIcon,
    description: 'Execute SQL queries'
  },
  { 
    path: '/models', 
    name: 'Semantic Models', 
    icon: CubeIcon,
    description: 'Manage semantic models'
  },
  { 
    path: '/metric-builder', 
    name: 'Metric Builder', 
    icon: WrenchIcon,
    description: 'Create custom metrics'
  },
  { 
    path: '/auto-generate', 
    name: 'Auto Generate', 
    icon: SparklesIcon,
    description: 'AI-powered model generation'
  },
  { 
    path: '/documentation', 
    name: 'Documentation', 
    icon: DocumentTextIcon,
    description: 'Generate documentation'
  },
  { 
    path: '/lineage', 
    name: 'Lineage', 
    icon: ShareIcon,
    description: 'Data lineage visualization'
  }
];

// AppLayout component with side panel
function AppLayout() {
  const [sidebarOpen, setSidebarOpen] = useState(true);
  const location = useLocation();
  const { theme, toggleTheme } = useTheme();

  // Health check queries
  const { data: health } = useQuery({
    queryKey: ['health'],
    queryFn: healthCheck,
    refetchInterval: 30000 // Refresh every 30 seconds
  });

  const { data: databricksHealth } = useQuery({
    queryKey: ['databricks-health'],
    queryFn: databricksHealthCheck,
    refetchInterval: 30000
  });

  const currentPath = location.pathname;

  return (
    <div className="flex h-screen bg-gray-50 dark:bg-gray-900">
      {/* Sidebar */}
      <div className={`${sidebarOpen ? 'w-64' : 'w-16'} transition-all duration-300 bg-white dark:bg-gray-800 border-r border-gray-200 dark:border-gray-700 flex flex-col`}>
        {/* Logo and Title */}
        <div className="p-4 border-b border-gray-200 dark:border-gray-700">
          <div className="flex items-center justify-between">
            <div className={`flex items-center space-x-3 ${!sidebarOpen && 'justify-center'}`}>
              <div className="w-8 h-8 bg-black dark:bg-white rounded-lg flex items-center justify-center flex-shrink-0">
                <span className="text-white dark:text-black text-sm font-bold">S</span>
              </div>
              {sidebarOpen && (
                <h1 className="text-xl font-bold text-black dark:text-white tracking-tight">
                  Semantic Layer
                </h1>
              )}
            </div>
            <div className="flex items-center space-x-1">
              <button
                onClick={toggleTheme}
                className="p-1 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-700 transition-colors"
                title={theme === 'light' ? 'Switch to dark mode' : 'Switch to light mode'}
              >
                {theme === 'light' ? (
                  <MoonIcon className="h-5 w-5 text-gray-600 dark:text-gray-300" />
                ) : (
                  <SunIcon className="h-5 w-5 text-gray-600 dark:text-gray-300" />
                )}
              </button>
              <button
                onClick={() => setSidebarOpen(!sidebarOpen)}
                className="p-1 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-700 transition-colors"
              >
                {sidebarOpen ? (
                  <ChevronLeftIcon className="h-5 w-5 text-gray-600 dark:text-gray-300" />
                ) : (
                  <ChevronRightIcon className="h-5 w-5 text-gray-600 dark:text-gray-300" />
                )}
              </button>
            </div>
          </div>
        </div>

        {/* Navigation */}
        <nav className="flex-1 overflow-y-auto p-3">
          <ul className="space-y-1">
            {navigationItems.map((item) => {
              const Icon = item.icon;
              const isActive = currentPath === item.path;
              
              return (
                <li key={item.path}>
                  <Link
                    to={item.path}
                    className={`flex items-center px-3 py-2 rounded-lg transition-all duration-200 group ${
                      isActive
                        ? 'bg-gray-900 dark:bg-gray-700 text-white'
                        : 'text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-700'
                    }`}
                  >
                    <Icon className={`h-5 w-5 flex-shrink-0 ${
                      isActive ? 'text-white' : 'text-gray-500 dark:text-gray-400 group-hover:text-gray-700 dark:group-hover:text-gray-200'
                    }`} />
                    {sidebarOpen && (
                      <div className="ml-3">
                        <div className={`text-sm font-medium ${
                          isActive ? 'text-white' : 'text-gray-900 dark:text-gray-100'
                        }`}>
                          {item.name}
                        </div>
                        <div className={`text-xs ${
                          isActive ? 'text-gray-300' : 'text-gray-500 dark:text-gray-400'
                        }`}>
                          {item.description}
                        </div>
                      </div>
                    )}
                  </Link>
                </li>
              );
            })}
          </ul>
        </nav>

        {/* Connection Status */}
        <div className="p-4 border-t border-gray-200 dark:border-gray-700">
          {sidebarOpen ? (
            <div className="space-y-3">
              {/* API Status */}
              <div className="flex items-center justify-between">
                <span className="text-xs font-medium text-gray-600 dark:text-gray-400">API</span>
                {health?.status === 'healthy' ? (
                  <div className="flex items-center">
                    <CheckCircleIcon className="h-4 w-4 text-green-500 mr-1" />
                    <span className="text-xs text-green-600 font-medium">Connected</span>
                  </div>
                ) : (
                  <div className="flex items-center">
                    <XCircleIcon className="h-4 w-4 text-red-500 mr-1" />
                    <span className="text-xs text-red-600 font-medium">Disconnected</span>
                  </div>
                )}
              </div>

              {/* Databricks Status */}
              <div className="flex items-center justify-between">
                <span className="text-xs font-medium text-gray-600 dark:text-gray-400">Databricks</span>
                {databricksHealth?.status === 'healthy' ? (
                  <div className="flex items-center">
                    <CheckCircleIcon className="h-4 w-4 text-green-500 mr-1" />
                    <span className="text-xs text-green-600 font-medium">Connected</span>
                  </div>
                ) : databricksHealth?.status === 'not_configured' ? (
                  <div className="flex items-center">
                    <ExclamationCircleIcon className="h-4 w-4 text-yellow-500 mr-1" />
                    <span className="text-xs text-yellow-600 font-medium">Not Configured</span>
                  </div>
                ) : (
                  <div className="flex items-center">
                    <XCircleIcon className="h-4 w-4 text-red-500 mr-1" />
                    <span className="text-xs text-red-600 font-medium">Error</span>
                  </div>
                )}
              </div>
            </div>
          ) : (
            <div className="flex flex-col items-center space-y-2">
              <div className={`w-2 h-2 rounded-full ${
                health?.status === 'healthy' ? 'bg-green-500' : 'bg-red-500'
              }`} />
              <div className={`w-2 h-2 rounded-full ${
                databricksHealth?.status === 'healthy' ? 'bg-green-500' : 
                databricksHealth?.status === 'not_configured' ? 'bg-yellow-500' : 'bg-red-500'
              }`} />
            </div>
          )}
        </div>
      </div>

      {/* Main Content */}
      <div className="flex-1 overflow-auto bg-gray-50 dark:bg-gray-900">
        <main className="p-8">
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
    </div>
  );
}

function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <Router>
        <AppLayout />
      </Router>
    </QueryClientProvider>
  );
}

export default App;
