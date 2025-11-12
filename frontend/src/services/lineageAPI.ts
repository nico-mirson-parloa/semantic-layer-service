import axios from 'axios';

const api = axios.create({
  baseURL: process.env.REACT_APP_API_URL || 'http://localhost:8000',
});

// Add token to requests
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('auth_token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

export interface LineageDirection {
  UPSTREAM: 'upstream';
  DOWNSTREAM: 'downstream';
  BOTH: 'both';
}

export interface TableLineageRequest {
  catalog: string;
  schema: string;
  table: string;
  direction?: 'upstream' | 'downstream' | 'both';
  depth?: number;
  include_columns?: boolean;
  layout_algorithm?: string;
}

export interface ModelLineageRequest {
  include_upstream?: boolean;
  include_downstream?: boolean;
  depth?: number;
  layout_algorithm?: string;
}

export interface ColumnLineageRequest {
  catalog: string;
  schema: string;
  table: string;
  column: string;
  layout_algorithm?: string;
}

export interface ImpactAnalysisRequest {
  entity_id: string;
  entity_type: string;
  change_type?: string;
  depth?: number;
}

export interface LineageExportRequest {
  graph: any;
  format: string;
  layout_algorithm?: string;
  include_metadata?: boolean;
}

export interface LineageSearchRequest {
  query: string;
  entity_types?: string;
  limit?: number;
}

export const lineageAPI = {
  // Get table lineage
  getTableLineage: async (params: TableLineageRequest) => {
    const response = await api.get('/api/v1/lineage/table', { params });
    return response.data;
  },

  // Get model lineage
  getModelLineage: async (modelId: string, params: ModelLineageRequest = {}) => {
    const response = await api.get(`/api/v1/lineage/model/${modelId}`, { params });
    return response.data;
  },

  // Get column lineage
  getColumnLineage: async (params: ColumnLineageRequest) => {
    const response = await api.get('/api/v1/lineage/column', { params });
    return response.data;
  },

  // Analyze impact
  analyzeImpact: async (data: ImpactAnalysisRequest) => {
    const response = await api.post('/api/v1/lineage/impact', data);
    return response.data;
  },

  // Export lineage
  exportLineage: async (data: LineageExportRequest): Promise<Blob> => {
    const response = await api.post('/api/v1/lineage/export', data, {
      responseType: 'blob'
    });
    return response.data;
  },

  // Get lineage statistics
  getLineageStats: async (catalog?: string, schema?: string) => {
    const params: any = {};
    if (catalog) params.catalog = catalog;
    if (schema) params.schema = schema;
    
    const response = await api.get('/api/v1/lineage/stats', { params });
    return response.data;
  },

  // Search lineage entities
  searchLineage: async (params: LineageSearchRequest) => {
    const response = await api.get('/api/v1/lineage/search', { params });
    return response.data;
  }
};

