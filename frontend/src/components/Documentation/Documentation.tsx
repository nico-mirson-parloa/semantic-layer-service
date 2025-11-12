import React, { useState } from 'react';
import {
  Box,
  Typography,
  Paper,
  Button,
  Select,
  MenuItem,
  FormControl,
  InputLabel,
  Alert,
  CircularProgress,
  Tabs,
  Tab,
  Chip,
  Divider,
  IconButton,
  Tooltip,
  List,
  ListItem,
  ListItemText,
  Checkbox,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Stack,
  Card,
  CardContent,
  Grid,
  Snackbar,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
} from '@mui/material';
import {
  DocumentTextIcon,
  ArrowDownTrayIcon,
  EyeIcon,
  CodeBracketIcon,
  PresentationChartBarIcon,
  UserGroupIcon,
  ArrowPathIcon,
  EyeIcon as PreviewIcon,
} from '@heroicons/react/24/outline';
import { useQuery, useMutation } from '@tanstack/react-query';
import { Prism as SyntaxHighlighter } from 'react-syntax-highlighter';
import { tomorrow } from 'react-syntax-highlighter/dist/esm/styles/prism';
import ReactMarkdown from 'react-markdown';
import { documentationAPI } from '../../services/api';

interface SemanticModel {
  id: string;
  name: string;
  description?: string;
  version: string;
  created_at: string;
  updated_at: string;
  metrics_count: number;
  dimensions_count: number;
  entities_count: number;
  measures_count?: number;
  file_path?: string;
}

interface DocumentationTemplate {
  id: string;
  name: string;
  description: string;
  icon: React.ReactNode;
  tags: string[];
}

interface GeneratedDocumentation {
  format: string;
  content: string;
  metadata: {
    generated_at: string;
    template_used: string;
    model_version: string;
  };
}

interface TabPanelProps {
  children?: React.ReactNode;
  index: number;
  value: number;
}

const TabPanel: React.FC<TabPanelProps> = ({ children, value, index, ...other }) => {
  return (
    <div
      role="tabpanel"
      hidden={value !== index}
      id={`doc-tabpanel-${index}`}
      aria-labelledby={`doc-tab-${index}`}
      {...other}
    >
      {value === index && <Box sx={{ py: 3 }}>{children}</Box>}
    </div>
  );
};

const Documentation: React.FC = () => {
  const [activeTab, setActiveTab] = useState(0);
  const [selectedModels, setSelectedModels] = useState<string[]>([]);
  const [selectedTemplate, setSelectedTemplate] = useState<string>('standard');
  const [selectedFormat, setSelectedFormat] = useState<string>('markdown');
  const [previewContent, setPreviewContent] = useState<GeneratedDocumentation | null>(null);
  const [previewDialogOpen, setPreviewDialogOpen] = useState(false);
  const [batchDialogOpen, setBatchDialogOpen] = useState(false);
  const [successMessage, setSuccessMessage] = useState<string>('');
  const [errorMessage, setErrorMessage] = useState<string>('');

  // Available templates
  const templates: DocumentationTemplate[] = [
    {
      id: 'standard',
      name: 'Standard Documentation',
      description: 'Comprehensive documentation with all details',
      icon: <DocumentTextIcon className="h-5 w-5" />,
      tags: ['Complete', 'Default'],
    },
    {
      id: 'technical',
      name: 'Technical Reference',
      description: 'Detailed technical documentation for developers',
      icon: <CodeBracketIcon className="h-5 w-5" />,
      tags: ['Technical', 'Developers'],
    },
    {
      id: 'business',
      name: 'Business Overview',
      description: 'Business-focused documentation for stakeholders',
      icon: <PresentationChartBarIcon className="h-5 w-5" />,
      tags: ['Business', 'Non-technical'],
    },
    {
      id: 'executive',
      name: 'Executive Summary',
      description: 'High-level summary for executives',
      icon: <UserGroupIcon className="h-5 w-5" />,
      tags: ['Summary', 'Executive'],
    },
  ];

  // Fetch available models from semantic model storage
  const { data: models = [], isLoading: modelsLoading, error: modelsError } = useQuery({
    queryKey: ['semantic-models'],
    queryFn: documentationAPI.getModels,
  });

  // Fetch recent documentations
  const { data: recentDocs = [], refetch: refetchRecent } = useQuery({
    queryKey: ['recent-documentations'],
    queryFn: documentationAPI.getRecentDocumentations,
    refetchInterval: 5000, // Refresh every 5 seconds
  });

  // Generate documentation mutation
  const generateDocMutation = useMutation({
    mutationFn: documentationAPI.generateDocumentation,
    onSuccess: (data) => {
      setPreviewContent(data.documentation);
      setSuccessMessage('Documentation generated successfully!');
      setPreviewDialogOpen(true);
      // Refetch recent documentations
      refetchRecent();
    },
    onError: (error: any) => {
      setErrorMessage(error.message || 'Failed to generate documentation');
    },
  });

  // Batch generate documentation mutation
  const batchGenerateMutation = useMutation({
    mutationFn: documentationAPI.batchGenerateDocumentation,
    onSuccess: (data) => {
      setSuccessMessage(`Batch documentation job started. Job ID: ${data.job_id}`);
      setBatchDialogOpen(false);
      setSelectedModels([]);
    },
    onError: (error: any) => {
      setErrorMessage(error.message || 'Failed to start batch generation');
    },
  });

  const handleGenerateDoc = (modelId: string) => {
    generateDocMutation.mutate({
      model_id: modelId,
      template_id: selectedTemplate,
      format: selectedFormat,
    });
  };

  const handleBatchGenerate = () => {
    if (selectedModels.length === 0) {
      setErrorMessage('Please select at least one model');
      return;
    }

    batchGenerateMutation.mutate({
      model_ids: selectedModels,
      template_id: selectedTemplate,
      format: selectedFormat,
    });
  };

  const handlePreview = async (modelId: string) => {
    try {
      const preview = await documentationAPI.previewDocumentation(modelId, selectedTemplate);
      setPreviewContent(preview);
      setPreviewDialogOpen(true);
    } catch (error: any) {
      setErrorMessage(error.message || 'Failed to preview documentation');
    }
  };

  const handleExport = async () => {
    if (!previewContent) return;

    try {
      const blob = await documentationAPI.exportDocumentation(
        previewContent.content,
        previewContent.format,
        'semantic_model_documentation'
      );
      
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `documentation.${previewContent.format}`;
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);
      document.body.removeChild(a);
      
      setSuccessMessage('Documentation exported successfully!');
    } catch (error: any) {
      setErrorMessage(error.message || 'Failed to export documentation');
    }
  };

  const handleDownloadFromRecent = async (modelId: string, format: string) => {
    try {
      // First get the preview to get the content
      const preview = await documentationAPI.previewDocumentation(modelId, selectedTemplate);
      
      // Then export it
      const blob = await documentationAPI.exportDocumentation(
        preview.content,
        format || 'markdown',
        `${modelId}_documentation`
      );

      // Create download link
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `${modelId}_documentation.${format || 'md'}`;
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);
      document.body.removeChild(a);
      
      setSuccessMessage('Documentation downloaded successfully!');
    } catch (error: any) {
      setErrorMessage(error.message || 'Failed to download documentation');
    }
  };

  const handleSelectAll = () => {
    if (selectedModels.length === models.length) {
      setSelectedModels([]);
    } else {
      setSelectedModels(models.map((m: SemanticModel) => m.id));
    }
  };

  return (
    <Box sx={{ maxWidth: 1200, mx: 'auto', p: 3 }}>
      {/* Header */}
      <Paper 
        elevation={0} 
        sx={{ 
          borderBottom: '1px solid #e5e7eb',
          backgroundColor: 'white',
          mb: 3
        }}
      >
        <Box sx={{ p: 3 }}>
          <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
            <Box>
              <Typography variant="h4" component="h1" fontWeight={600} sx={{ mb: 1, color: '#1f2937' }}>
                Documentation Generator
              </Typography>
              <Typography variant="body1" sx={{ color: '#6b7280' }}>
                Generate and export comprehensive documentation for your semantic models
              </Typography>
            </Box>
            <Stack direction="row" spacing={1}>
              <Tooltip title="Refresh Models">
                <IconButton
                  sx={{
                    backgroundColor: '#f9fafb',
                    border: '1px solid #e5e7eb',
                    '&:hover': {
                      backgroundColor: '#f3f4f6',
                    },
                  }}
                  onClick={() => window.location.reload()}
                >
                  <ArrowPathIcon className="h-5 w-5" style={{ color: '#6b7280' }} />
                </IconButton>
              </Tooltip>
            </Stack>
          </Box>
        </Box>
      </Paper>

      {/* Connection Status */}
      {modelsError && (
        <Alert severity="error" sx={{ mb: 3 }}>
          <Typography variant="subtitle2" gutterBottom>
            Failed to connect to semantic model storage
          </Typography>
          <Typography variant="body2">
            Error: {modelsError?.message || 'Unable to fetch models from the backend'}
          </Typography>
        </Alert>
      )}

      {/* Settings Panel */}
      <Paper sx={{ p: 3, mb: 3, border: '1px solid #e5e7eb', backgroundColor: 'white' }}>
        <Typography variant="h6" gutterBottom sx={{ color: '#1f2937' }}>
          Documentation Settings
        </Typography>
        <Grid container spacing={3}>
          <Grid item xs={12} md={4}>
            <FormControl fullWidth>
              <InputLabel>Template</InputLabel>
              <Select
                value={selectedTemplate}
                onChange={(e) => setSelectedTemplate(e.target.value)}
                label="Template"
              >
                {templates.map((template) => (
                  <MenuItem key={template.id} value={template.id}>
                    <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                      {template.icon}
                      <span>{template.name}</span>
                    </Box>
                  </MenuItem>
                ))}
              </Select>
            </FormControl>
          </Grid>
          <Grid item xs={12} md={4}>
            <FormControl fullWidth>
              <InputLabel>Format</InputLabel>
              <Select
                value={selectedFormat}
                onChange={(e) => setSelectedFormat(e.target.value)}
                label="Format"
              >
                <MenuItem value="markdown">Markdown</MenuItem>
                <MenuItem value="html">HTML</MenuItem>
                <MenuItem value="pdf">PDF</MenuItem>
                <MenuItem value="json">JSON</MenuItem>
              </Select>
            </FormControl>
          </Grid>
          <Grid item xs={12} md={4}>
            <Button
              variant="outlined"
              fullWidth
              sx={{ 
                height: '56px',
                backgroundColor: '#f9fafb',
                border: '1px solid #e5e7eb',
                color: '#1f2937',
                '&:hover': {
                  backgroundColor: '#f3f4f6',
                  border: '1px solid #d1d5db',
                },
              }}
              onClick={() => setBatchDialogOpen(true)}
              disabled={models.length === 0}
            >
              Batch Generate
            </Button>
          </Grid>
        </Grid>

        {/* Template Info */}
        <Box sx={{ mt: 2 }}>
          {templates.find(t => t.id === selectedTemplate) && (
            <Alert severity="info" sx={{ mt: 2 }}>
              <Typography variant="subtitle2" gutterBottom>
                {templates.find(t => t.id === selectedTemplate)?.name}
              </Typography>
              <Typography variant="body2">
                {templates.find(t => t.id === selectedTemplate)?.description}
              </Typography>
              <Box sx={{ mt: 1 }}>
                {templates.find(t => t.id === selectedTemplate)?.tags.map((tag) => (
                  <Chip key={tag} label={tag} size="small" sx={{ mr: 1 }} />
                ))}
              </Box>
            </Alert>
          )}
        </Box>
      </Paper>

      {/* Content Tabs */}
      <Paper sx={{ width: '100%', border: '1px solid #e5e7eb', backgroundColor: 'white' }}>
        <Tabs value={activeTab} onChange={(_, val) => setActiveTab(val)}>
          <Tab label="Semantic Models" />
          <Tab label="Recent Jobs" />
          <Tab label="Templates" />
        </Tabs>

        <Divider />

        {/* Semantic Models Tab */}
        <TabPanel value={activeTab} index={0}>
          {modelsLoading ? (
            <Box sx={{ display: 'flex', justifyContent: 'center', p: 4 }}>
              <CircularProgress />
              <Typography variant="body2" sx={{ ml: 2, color: '#6b7280' }}>
                Loading semantic models...
              </Typography>
            </Box>
          ) : models.length === 0 ? (
            <Alert severity="info">
              <Typography variant="subtitle2" gutterBottom>
                No semantic models found
              </Typography>
              <Typography variant="body2">
                The semantic model storage appears to be empty. Create some semantic models first to generate documentation.
              </Typography>
            </Alert>
          ) : (
            <>
              <Box sx={{ mb: 2, p: 2, backgroundColor: '#f9fafb', borderRadius: 1 }}>
                <Typography variant="body2" sx={{ color: '#6b7280' }}>
                  Found {models.length} semantic model{models.length !== 1 ? 's' : ''} in storage
                </Typography>
              </Box>
              <TableContainer>
                <Table>
                  <TableHead>
                    <TableRow>
                      <TableCell sx={{ fontWeight: 600 }}>Model Name</TableCell>
                      <TableCell sx={{ fontWeight: 600 }}>Description</TableCell>
                      <TableCell align="center" sx={{ fontWeight: 600 }}>Metrics</TableCell>
                      <TableCell align="center" sx={{ fontWeight: 600 }}>Dimensions</TableCell>
                      <TableCell align="center" sx={{ fontWeight: 600 }}>Entities</TableCell>
                      <TableCell sx={{ fontWeight: 600 }}>Last Updated</TableCell>
                      <TableCell align="center" sx={{ fontWeight: 600 }}>Actions</TableCell>
                    </TableRow>
                  </TableHead>
                  <TableBody>
                    {models.map((model: SemanticModel) => (
                      <TableRow key={model.id} hover>
                        <TableCell>
                          <Typography variant="body2" fontWeight={500}>
                            {model.name}
                          </Typography>
                          <Typography variant="caption" color="text.secondary">
                            {model.id}
                          </Typography>
                        </TableCell>
                        <TableCell>
                          <Typography variant="body2" color="text.secondary">
                            {model.description || '-'}
                          </Typography>
                        </TableCell>
                        <TableCell align="center">
                          <Chip 
                            label={model.metrics_count} 
                            size="small" 
                            sx={{ backgroundColor: '#374151', color: 'white' }}
                          />
                        </TableCell>
                        <TableCell align="center">
                          <Chip 
                            label={model.dimensions_count} 
                            size="small" 
                            sx={{ backgroundColor: '#6b7280', color: 'white' }}
                          />
                        </TableCell>
                        <TableCell align="center">
                          <Chip 
                            label={model.entities_count} 
                            size="small" 
                            sx={{ backgroundColor: '#9ca3af', color: 'white' }}
                          />
                        </TableCell>
                        <TableCell>
                          <Typography variant="caption">
                            {new Date(model.updated_at).toLocaleDateString()}
                          </Typography>
                        </TableCell>
                        <TableCell align="center">
                          <Stack direction="row" spacing={1} justifyContent="center">
                            <Tooltip title="Preview">
                              <IconButton
                                size="small"
                                onClick={() => handlePreview(model.id)}
                                sx={{ color: '#6b7280' }}
                              >
                                <EyeIcon className="h-4 w-4" />
                              </IconButton>
                            </Tooltip>
                            <Tooltip title="Generate">
                              <IconButton
                                size="small"
                                onClick={() => handleGenerateDoc(model.id)}
                                disabled={generateDocMutation.isPending}
                                sx={{ 
                                  color: '#1f2937',
                                  '&:hover': { backgroundColor: '#f3f4f6' }
                                }}
                              >
                                {generateDocMutation.isPending ? (
                                  <CircularProgress size={16} />
                                ) : (
                                  <DocumentTextIcon className="h-4 w-4" />
                                )}
                              </IconButton>
                            </Tooltip>
                          </Stack>
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              </TableContainer>
            </>
          )}
        </TabPanel>

        {/* Recent Jobs Tab */}
        <TabPanel value={activeTab} index={1}>
          {recentDocs.length === 0 ? (
            <Alert severity="info">
              <Typography variant="subtitle2" gutterBottom>
                No Recent Documentation
              </Typography>
              <Typography variant="body2">
                Generated documentation will appear here. Generate documentation for any model to see it listed.
              </Typography>
            </Alert>
          ) : (
            <>
              <Box sx={{ mb: 2, p: 2, backgroundColor: '#f9fafb', borderRadius: 1 }}>
                <Typography variant="body2" sx={{ color: '#6b7280' }}>
                  Showing {recentDocs.length} recent documentation{recentDocs.length !== 1 ? 's' : ''}
                </Typography>
              </Box>
              <TableContainer>
                <Table>
                  <TableHead>
                    <TableRow>
                      <TableCell sx={{ fontWeight: 600 }}>Model Name</TableCell>
                      <TableCell sx={{ fontWeight: 600 }}>Format</TableCell>
                      <TableCell sx={{ fontWeight: 600 }}>Template</TableCell>
                      <TableCell sx={{ fontWeight: 600 }}>Generated At</TableCell>
                      <TableCell align="center" sx={{ fontWeight: 600 }}>Actions</TableCell>
                    </TableRow>
                  </TableHead>
                  <TableBody>
                    {recentDocs.map((doc: any) => (
                      <TableRow key={`${doc.model_id}-${doc.generated_at}`}>
                        <TableCell>
                          <Typography variant="body2" sx={{ fontWeight: 500 }}>
                            {doc.model_name}
                          </Typography>
                        </TableCell>
                        <TableCell>
                          <Chip 
                            label={doc.format.toUpperCase()} 
                            size="small" 
                            color="primary" 
                            variant="outlined"
                          />
                        </TableCell>
                        <TableCell>
                          <Typography variant="body2">{doc.template}</Typography>
                        </TableCell>
                        <TableCell>
                          <Typography variant="body2" sx={{ color: '#6b7280' }}>
                            {new Date(doc.generated_at).toLocaleString()}
                          </Typography>
                        </TableCell>
                        <TableCell align="center">
                          <Stack direction="row" spacing={1} justifyContent="center">
                            <Tooltip title="Preview">
                              <IconButton
                                size="small"
                                onClick={() => handlePreview(doc.model_id)}
                                sx={{ color: '#1f2937' }}
                              >
                                <PreviewIcon />
                              </IconButton>
                            </Tooltip>
                            <Tooltip title="Download">
                              <IconButton
                                size="small"
                                onClick={() => handleDownloadFromRecent(doc.model_id, doc.format)}
                                sx={{ color: '#1f2937' }}
                              >
                                <ArrowDownTrayIcon />
                              </IconButton>
                            </Tooltip>
                          </Stack>
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              </TableContainer>
            </>
          )}
        </TabPanel>

        {/* Templates Tab */}
        <TabPanel value={activeTab} index={2}>
          <Grid container spacing={3}>
            {templates.map((template) => (
              <Grid item xs={12} md={6} key={template.id}>
                <Card 
                  variant="outlined" 
                  sx={{ 
                    border: selectedTemplate === template.id ? '2px solid #1f2937' : '1px solid #e5e7eb',
                    cursor: 'pointer',
                    '&:hover': {
                      boxShadow: '0 4px 6px -1px rgba(0, 0, 0, 0.1)',
                    }
                  }}
                  onClick={() => setSelectedTemplate(template.id)}
                >
                  <CardContent>
                    <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, mb: 2 }}>
                      <Box
                        sx={{
                          p: 2,
                          borderRadius: 2,
                          backgroundColor: '#f3f4f6',
                          color: '#6b7280',
                        }}
                      >
                        {template.icon}
                      </Box>
                      <Box>
                        <Typography variant="h6" sx={{ color: '#1f2937' }}>
                          {template.name}
                        </Typography>
                        <Box sx={{ mt: 0.5 }}>
                          {template.tags.map((tag) => (
                            <Chip
                              key={tag}
                              label={tag}
                              size="small"
                              sx={{ mr: 1 }}
                              variant="outlined"
                            />
                          ))}
                        </Box>
                      </Box>
                    </Box>
                    <Typography variant="body2" color="text.secondary">
                      {template.description}
                    </Typography>
                  </CardContent>
                </Card>
              </Grid>
            ))}
          </Grid>
        </TabPanel>
      </Paper>

      {/* Preview Dialog */}
      <Dialog
        open={previewDialogOpen}
        onClose={() => setPreviewDialogOpen(false)}
        maxWidth="md"
        fullWidth
      >
        <DialogTitle>
          Documentation Preview
          <Typography variant="caption" display="block" color="text.secondary">
            Format: {previewContent?.format} | Template: {previewContent?.metadata.template_used}
          </Typography>
        </DialogTitle>
        <DialogContent dividers>
          {previewContent?.format === 'markdown' ? (
            <Box sx={{ maxHeight: '60vh', overflow: 'auto' }}>
              <ReactMarkdown>{previewContent.content}</ReactMarkdown>
            </Box>
          ) : previewContent?.format === 'html' ? (
            <Box 
              sx={{ maxHeight: '60vh', overflow: 'auto' }}
              dangerouslySetInnerHTML={{ __html: previewContent.content }}
            />
          ) : (
            <SyntaxHighlighter
              language={previewContent?.format || 'text'}
              style={tomorrow}
              customStyle={{ maxHeight: '60vh', overflow: 'auto' }}
            >
              {previewContent?.content || ''}
            </SyntaxHighlighter>
          )}
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setPreviewDialogOpen(false)}>Close</Button>
          <Button onClick={handleExport} variant="contained" startIcon={<ArrowDownTrayIcon className="h-4 w-4" />}>
            Export
          </Button>
        </DialogActions>
      </Dialog>

      {/* Batch Generate Dialog */}
      <Dialog
        open={batchDialogOpen}
        onClose={() => setBatchDialogOpen(false)}
        maxWidth="sm"
        fullWidth
      >
        <DialogTitle>Batch Generate Documentation</DialogTitle>
        <DialogContent>
          <Box sx={{ mb: 2 }}>
            <Button
              size="small"
              onClick={handleSelectAll}
              sx={{ mb: 2 }}
            >
              {selectedModels.length === models.length ? 'Deselect All' : 'Select All'}
            </Button>
          </Box>
          <List>
            {models.map((model: SemanticModel) => (
              <ListItem key={model.id} dense>
                <Checkbox
                  edge="start"
                  checked={selectedModels.includes(model.id)}
                  onChange={(e) => {
                    if (e.target.checked) {
                      setSelectedModels([...selectedModels, model.id]);
                    } else {
                      setSelectedModels(selectedModels.filter(id => id !== model.id));
                    }
                  }}
                />
                <ListItemText
                  primary={model.name}
                  secondary={model.description}
                />
              </ListItem>
            ))}
          </List>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setBatchDialogOpen(false)}>Cancel</Button>
          <Button
            onClick={handleBatchGenerate}
            variant="contained"
            disabled={selectedModels.length === 0 || batchGenerateMutation.isPending}
          >
            Generate ({selectedModels.length} models)
          </Button>
        </DialogActions>
      </Dialog>

      {/* Success/Error Messages */}
      <Snackbar
        open={!!successMessage}
        autoHideDuration={6000}
        onClose={() => setSuccessMessage('')}
      >
        <Alert severity="success" onClose={() => setSuccessMessage('')}>
          {successMessage}
        </Alert>
      </Snackbar>
      <Snackbar
        open={!!errorMessage}
        autoHideDuration={6000}
        onClose={() => setErrorMessage('')}
      >
        <Alert severity="error" onClose={() => setErrorMessage('')}>
          {errorMessage}
        </Alert>
      </Snackbar>
    </Box>
  );
};

export default Documentation;
