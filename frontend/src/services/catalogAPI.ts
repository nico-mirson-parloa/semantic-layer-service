import axios from 'axios';

const API_BASE_URL = process.env.REACT_APP_API_URL || '';

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Add auth token to requests
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('authToken');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

export interface GoldTableInfo {
  catalog: string;
  schema: string;
  table: string;
  fullName: string;
  tableType: string;
  description?: string;
  columnCount: number;
  hasSemanticModel: boolean;
  lastUpdated?: string;
}

export interface AnalyzeTableRequest {
  catalog: string;
  schema: string;
  table: string;
  includeLineage?: boolean;
}

export interface TableAnalysis {
  tableAnalysis: any;
  suggestedMetrics: any[];
  suggestedDimensions: any[];
  suggestedEntities: any[];
  suggestedMeasures?: any[];
  confidenceScores: {
    overall: number;
    metrics: number;
    dimensions: number;
  };
  statistics?: {
    totalSuggestions: number;
    metricsCount: number;
    dimensionsCount: number;
    entitiesCount: number;
  };
}

export interface GenerateModelRequest {
  catalog: string;
  schema: string;
  table?: string;
  tables?: string[];
  acceptSuggestions: boolean;
  customization?: {
    modelName?: string;
    description?: string;
    excludedMetrics?: string[];
    excludedDimensions?: string[];
    minimumConfidenceScore?: number;
  };
  includeLineage?: boolean;
  asyncGeneration?: boolean;
}

export interface GeneratedModelResponse {
  success: boolean;
  modelId?: string;
  modelName?: string;
  yamlContent?: string;
  validationResult?: {
    isValid: boolean;
    errors?: string[];
    warnings?: string[];
    suggestions?: string[];
  };
  metadata?: any;
  filePath?: string;
  errors?: string[];
}

export interface ModelGenerationJob {
  jobId: string;
  status: 'pending' | 'processing' | 'completed' | 'failed';
  progress?: number;
  totalTables?: number;
  tablesProcessed?: number;
  currentTable?: string;
  results?: any[];
  errors?: string[];
  startTime: string;
  endTime?: string;
}

export const catalogAPI = {
  // Get list of tables
  getGoldTables: (catalog?: string, schemaPattern?: string, search?: string, limit?: number) => {
    const params = new URLSearchParams();
    if (catalog) params.append('catalog', catalog);
    if (schemaPattern) params.append('schema_pattern', schemaPattern);
    if (search) params.append('search', search);
    if (limit) params.append('limit', limit.toString());
    
    return api.get<GoldTableInfo[]>(`/api/catalog/gold-tables?${params.toString()}`);
  },

  // Analyze a table and get suggestions
  analyzeTable: (request: AnalyzeTableRequest) => {
    return api.post<TableAnalysis>('/api/catalog/analyze-table', request);
  },

  // Generate semantic model
  generateModel: (request: GenerateModelRequest) => {
    return api.post<GeneratedModelResponse>('/api/catalog/generate', request);
  },

  // Get generation job status
  getGenerationStatus: (jobId: string) => {
    return api.get<ModelGenerationJob>(`/api/catalog/generation-status/${jobId}`);
  },

  // Batch operations
  batchAnalyzeTables: (tables: AnalyzeTableRequest[]) => {
    return api.post<TableAnalysis[]>('/api/catalog/batch-analyze', { tables });
  },

  // Get catalog metadata
  getCatalogMetadata: () => {
    return api.get('/api/catalog/metadata');
  },

  // Get supported data types
  getSupportedDataTypes: () => {
    return api.get<string[]>('/api/catalog/supported-types');
  },

  // Get available catalogs
  getCatalogs: () => {
    return api.get<{catalogs: Array<{catalog_name: string, comment: string, catalog_owner: string}>, total_catalogs: number}>('/api/catalog/catalogs');
  },

  // Get schemas for a catalog
  getSchemas: (catalog: string) => {
    return api.get<{schemas: Array<{schema_name: string, catalog_name: string, comment: string, table_count: number}>, total_schemas: number}>(`/api/catalog/schemas?catalog=${catalog}`);
  },
};

export default catalogAPI;
