import axios from 'axios';

const API_BASE_URL = process.env.REACT_APP_API_URL || '';

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Add request interceptor for error handling
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.data?.detail) {
      error.message = error.response.data.detail;
    }
    return Promise.reject(error);
  }
);

// Health check
export const healthCheck = async () => {
  const response = await api.get('/api/health/');
  return response.data;
};

export const databricksHealthCheck = async () => {
  const response = await api.get('/api/health/databricks');
  return response.data;
};

// Metadata
export const getTables = async (catalog?: string, schema?: string) => {
  const params = new URLSearchParams();
  if (catalog) params.append('catalog', catalog);
  if (schema) params.append('schema', schema);
  
  const response = await api.get(`/api/metadata/tables?${params}`);
  return response.data;
};

export const getColumns = async (catalog: string, schema: string, table: string) => {
  const params = new URLSearchParams({ catalog, schema, table });
  const response = await api.get(`/api/metadata/columns?${params}`);
  return response.data;
};

export const getCatalogs = async () => {
  const response = await api.get('/api/metadata/catalogs');
  return response.data;
};

export const getSchemas = async (catalog: string) => {
  const params = new URLSearchParams({ catalog });
  const response = await api.get(`/api/metadata/schemas?${params}`);
  return response.data;
};

// Queries
export interface QueryRequest {
  query: string;
  parameters?: Record<string, any>;
  limit?: number;
}

export const executeQuery = async (request: QueryRequest) => {
  const response = await api.post('/api/queries/execute', request);
  return response.data;
};

export const validateQuery = async (request: QueryRequest) => {
  const response = await api.post('/api/queries/validate', request);
  return response.data;
};

// Semantic Models
export const getModels = async () => {
  // Use direct endpoint to bypass router auth issues
  const response = await api.get('/api/models-demo');
  return response.data;
};

export const getModel = async (modelId: string) => {
  // Use direct endpoint to bypass router auth issues
  const response = await api.get(`/api/models-demo/${modelId}`);
  return response.data;
};

export const downloadModel = async (modelId: string) => {
  const response = await api.get(`/api/models-demo/${modelId}/download`, {
    responseType: 'blob'
  });
  
  // Create download link
  const url = window.URL.createObjectURL(new Blob([response.data]));
  const link = document.createElement('a');
  link.href = url;
  link.setAttribute('download', `${modelId}.yml`);
  document.body.appendChild(link);
  link.click();
  link.remove();
  window.URL.revokeObjectURL(url);
};

export const updateModel = async (modelId: string, yamlContent: string) => {
  const response = await api.put(`/api/models-demo/${modelId}`, {
    raw_yaml: yamlContent
  });
  return response.data;
};

// Metrics Explorer API calls
export const getAllMetrics = async () => {
  const response = await api.get('/api/metrics-explorer/metrics');
  return response.data;
};

export const getMetricDetail = async (metricId: string) => {
  const response = await api.get(`/api/metrics-explorer/metrics/${metricId}`);
  return response.data;
};

export const searchMetrics = async (params: {
  q?: string;
  category?: string;
  model?: string;
  type?: string;
}) => {
  const searchParams = new URLSearchParams();
  Object.entries(params).forEach(([key, value]) => {
    if (value) searchParams.append(key, value);
  });
  
  const response = await api.get(`/api/metrics-explorer/metrics/search?${searchParams.toString()}`);
  return response.data;
};

export const getMetricCategories = async () => {
  const response = await api.get('/api/metrics-explorer/metrics/categories');
  return response.data;
};

export const getMetricModels = async () => {
  const response = await api.get('/api/metrics-explorer/metrics/models');
  return response.data;
};

export const createModel = async (model: any) => {
  const response = await api.post('/api/models', model);
  return response.data;
};

export const deleteModel = async (modelId: string) => {
  const response = await api.delete(`/api/models/${modelId}`);
  return response.data;
};

// SQL Autocomplete
export const getSQLAutocomplete = async (search: string, context?: string) => {
  const params = new URLSearchParams({ search });
  if (context) params.append('context', context);
  
  const response = await api.get(`/api/metadata/sql-autocomplete?${params.toString()}`);
  return response.data;
};

export default api;

// Export catalogAPI
export * from './catalogAPI';
export * from './documentationAPI';
export * from './lineageAPI';
