import axios from 'axios';

const API_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';

// Add request interceptor to include auth token
axios.interceptors.request.use(
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

export interface DocumentationGenerationRequest {
  model_id: string;
  template_id: string;
  format: string;
  include_lineage?: boolean;
  include_usage_examples?: boolean;
}

export interface BatchDocumentationRequest {
  model_ids: string[];
  template_id: string;
  format: string;
}

export interface DocumentationStatus {
  job_id: string;
  status: 'pending' | 'processing' | 'completed' | 'failed';
  progress: number;
  result?: any;
  error?: string;
}

export interface TemplateInfo {
  id: string;
  name: string;
  description: string;
  sections: string[];
  is_custom: boolean;
}

export const documentationAPI = {
  // Get available models (using existing demo endpoint)
  async getModels() {
    const response = await axios.get(`${API_URL}/api/models-demo`);
    return response.data;
  },

  // Generate documentation for a single model
  async generateDocumentation(request: DocumentationGenerationRequest) {
    const response = await axios.post(`${API_URL}/api/documentation/demo/generate`, request);
    return response.data;
  },

  // Batch generate documentation
  async batchGenerateDocumentation(request: BatchDocumentationRequest) {
    const response = await axios.post(`${API_URL}/api/v1/documentation/batch`, request);
    return response.data;
  },

  // Get job status
  async getJobStatus(jobId: string): Promise<DocumentationStatus> {
    const response = await axios.get(`${API_URL}/api/v1/documentation/status/${jobId}`);
    return response.data;
  },

  // Get available templates
  async getTemplates(): Promise<TemplateInfo[]> {
    const response = await axios.get(`${API_URL}/api/v1/documentation/templates`);
    return response.data.templates;
  },

  // Preview documentation
  async previewDocumentation(modelId: string, templateId: string = 'standard') {
    const response = await axios.get(`${API_URL}/api/documentation/demo/preview/${modelId}`, {
      params: { template: templateId }
    });
    return response.data;
  },

  // Export documentation
  async exportDocumentation(content: string, format: string, filename: string): Promise<Blob> {
    const response = await axios.post(
      `${API_URL}/api/documentation/demo/export`,
      { content, format, filename },
      { responseType: 'blob' }
    );
    return response.data;
  },

  // Get recent documentations
  async getRecentDocumentations() {
    const response = await axios.get(`${API_URL}/api/documentation/demo/recent`);
    return response.data.documentations || [];
  }
};
