import React, { useState, useEffect } from 'react';
import {
  Box,
  Stepper,
  Step,
  StepLabel,
  StepContent,
  Button,
  Typography,
  TextField,
  Alert,
  CircularProgress,
  Chip,
  Card,
  CardContent,
  List,
  ListItem,
  ListItemText,
  Accordion,
  AccordionSummary,
  AccordionDetails,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Checkbox,
  Grid,
  Select,
  MenuItem,
  FormControl,
  InputLabel,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Paper,
  Radio,
} from '@mui/material';
import {
  ExpandMore as ExpandMoreIcon,
  Info as InfoIcon,
  CheckCircle as CheckCircleIcon,
  Warning as WarningIcon,
  Error as ErrorIcon,
  AutoAwesome as AutoAwesomeIcon,
  TableChart as TableChartIcon,
  Analytics as AnalyticsIcon,
  Save as SaveIcon,
  Preview as PreviewIcon,
  Code as CodeIcon,
  Download as DownloadIcon,
} from '@mui/icons-material';
import { Prism as SyntaxHighlighter } from 'react-syntax-highlighter';
import { tomorrow } from 'react-syntax-highlighter/dist/esm/styles/prism';
import { catalogAPI } from '../../services/api';

interface GoldTable {
  catalog: string;
  schema: string;
  table: string;
  fullName: string;
  tableType: string;
  description?: string;
  columnCount: number;
  rowCount?: number;
  sizeMb?: number;
  hasSemanticModel: boolean;
  lastUpdated?: string;
}

interface TableAnalysis {
  tableAnalysis: any;
  suggestedMetrics: SuggestedMetric[];
  suggestedDimensions: SuggestedDimension[];
  suggestedEntities: any[];
  confidenceScores: {
    overall: number;
    metrics: number;
    dimensions: number;
  };
}

interface SuggestedMetric {
  name: string;
  displayName: string;
  expression: string;
  metricType: string;
  description?: string;
  confidenceScore: number;
  category?: string;
  selected?: boolean;
}

interface SuggestedDimension {
  name: string;
  displayName: string;
  type: string;
  expression: string;
  description?: string;
  granularities?: string[];
  selected?: boolean;
}

interface ModelCustomization {
  modelName?: string;
  description?: string;
  excludedMetrics: string[];
  excludedDimensions: string[];
  minimumConfidenceScore: number;
}

export const AutoModelGeneration: React.FC = () => {
  const [activeStep, setActiveStep] = useState(0);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  
  // Step 1: Table Selection
  const [goldTables, setGoldTables] = useState<GoldTable[]>([]);
  const [selectedTable, setSelectedTable] = useState<GoldTable | null>(null);
  const [tableFilter, setTableFilter] = useState('');

  
  // Catalog and Schema selection
  const [catalogs, setCatalogs] = useState<Array<{catalog_name: string, comment: string}>>([]);
  const [selectedCatalog, setSelectedCatalog] = useState<string>('parloa-prod-weu');
  const [schemas, setSchemas] = useState<Array<{schema_name: string, table_count: number}>>([]);
  const [selectedSchema, setSelectedSchema] = useState<string>('');
  
  // Step 2: Analysis Results
  const [analysis, setAnalysis] = useState<TableAnalysis | null>(null);
  const [selectedMetrics, setSelectedMetrics] = useState<Set<string>>(new Set());
  const [selectedDimensions, setSelectedDimensions] = useState<Set<string>>(new Set());
  
  // Step 3: Customization
  const [customization, setCustomization] = useState<ModelCustomization>({
    excludedMetrics: [],
    excludedDimensions: [],
    minimumConfidenceScore: 0.75,
  });
  
  // Step 4: Preview & Generate
  const [generatedModel, setGeneratedModel] = useState<any>(null);
  const [yamlPreview, setYamlPreview] = useState<string>('');
  const [showYamlDialog, setShowYamlDialog] = useState(false);



  // Load catalogs on mount
  useEffect(() => {
    loadCatalogs();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  // Load schemas when catalog changes
  useEffect(() => {
    if (selectedCatalog) {
      loadSchemas();
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [selectedCatalog]);

  // Load tables when catalog, schema or table filter changes
  useEffect(() => {
    if (selectedCatalog) {
      loadGoldTables();
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [selectedCatalog, selectedSchema, tableFilter]);

  const loadCatalogs = async () => {
    try {
      const response = await catalogAPI.getCatalogs();
      setCatalogs(response.data.catalogs || []);
    } catch (err) {
      console.error('Failed to load catalogs:', err);
    }
  };

  const loadSchemas = async () => {
    try {
      const response = await catalogAPI.getSchemas(selectedCatalog);
      setSchemas(response.data.schemas || []);
    } catch (err) {
      console.error('Failed to load schemas:', err);
      setSchemas([]);
    }
  };

  const loadGoldTables = async () => {
    try {
      setLoading(true);
      setError(null);
      
      // Build schema pattern from selected schema
      const schemaFilter = selectedSchema || undefined;
      
      const response = await catalogAPI.getGoldTables(
        selectedCatalog, 
        schemaFilter,
        tableFilter || undefined,
        200
      );
      
      // Ensure we have an array and filter out any invalid entries
      const tables = Array.isArray(response.data) ? response.data.filter(table => table && table.fullName) : [];
      setGoldTables(tables);
      
      if (tables.length === 0 && !selectedSchema && !tableFilter) {
        setError('No tables found. Try selecting a different catalog or schema.');
      } else if (tables.length === 0) {
        setError('No tables found matching your filters. Try adjusting your search criteria.');
      }
    } catch (err) {
      setError('Failed to load tables');
      console.error(err);
      setGoldTables([]); // Ensure goldTables is always an array
    } finally {
      setLoading(false);
    }
  };

  const analyzeTable = async () => {
    if (!selectedTable) return;
    
    try {
      setLoading(true);
      setError(null);
      
      const response = await catalogAPI.analyzeTable({
        catalog: selectedTable.catalog,
        schema: selectedTable.schema,
        table: selectedTable.table,
      });
      
      setAnalysis(response.data);
      
      // Auto-select high confidence suggestions
      const metrics = new Set<string>();
      const dimensions = new Set<string>();
      
      response.data.suggestedMetrics.forEach((metric: SuggestedMetric) => {
        if (metric.confidenceScore >= customization.minimumConfidenceScore) {
          metrics.add(metric.name);
        }
      });
      
      response.data.suggestedDimensions.forEach((dim: SuggestedDimension) => {
        dimensions.add(dim.name);
      });
      
      setSelectedMetrics(metrics);
      setSelectedDimensions(dimensions);
      
      setActiveStep(1);
    } catch (err) {
      setError('Failed to analyze table');
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const generateModel = async () => {
    if (!selectedTable || !analysis) return;
    
    try {
      setLoading(true);
      setError(null);
      
      // Build excluded lists
      const excludedMetrics = analysis.suggestedMetrics
        .filter(m => !selectedMetrics.has(m.name))
        .map(m => m.name);
      
      const excludedDimensions = analysis.suggestedDimensions
        .filter(d => !selectedDimensions.has(d.name))
        .map(d => d.name);
      
      const response = await catalogAPI.generateModel({
        catalog: selectedTable.catalog,
        schema: selectedTable.schema,
        table: selectedTable.table,
        acceptSuggestions: true,
        customization: {
          ...customization,
          excludedMetrics,
          excludedDimensions,
        },
      });
      
      if (response.data.success) {
        setGeneratedModel(response.data);
        setYamlPreview(response.data.yamlContent || '');
        setActiveStep(3);
      } else {
        setError('Model generation failed: ' + (response.data.errors?.join(', ') || 'Unknown error'));
      }
    } catch (err) {
      setError('Failed to generate model');
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const handleMetricToggle = (metricName: string) => {
    const newSelected = new Set(selectedMetrics);
    if (newSelected.has(metricName)) {
      newSelected.delete(metricName);
    } else {
      newSelected.add(metricName);
    }
    setSelectedMetrics(newSelected);
  };

  const handleDimensionToggle = (dimensionName: string) => {
    const newSelected = new Set(selectedDimensions);
    if (newSelected.has(dimensionName)) {
      newSelected.delete(dimensionName);
    } else {
      newSelected.add(dimensionName);
    }
    setSelectedDimensions(newSelected);
  };

  const getConfidenceColor = (score: number) => {
    if (score >= 0.8) return 'success';
    if (score >= 0.6) return 'warning';
    return 'error';
  };

  const getConfidenceIcon = (score: number) => {
    if (score >= 0.8) return <CheckCircleIcon />;
    if (score >= 0.6) return <WarningIcon />;
    return <ErrorIcon />;
  };

  const downloadYaml = () => {
    if (!yamlPreview || !generatedModel) return;
    
    const blob = new Blob([yamlPreview], { type: 'text/yaml' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `${generatedModel.modelName || 'model'}.yml`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  };

  // Tables are already filtered by the backend based on catalog, schema, and table filter
  // This is just for client-side display consistency
  const filteredTables = goldTables;

  return (
    <Box sx={{ p: 3 }}>
      <Typography variant="h4" gutterBottom>
        <AutoAwesomeIcon sx={{ mr: 1, verticalAlign: 'bottom' }} />
        Automatic Model Generation
      </Typography>
      
      <Typography variant="body1" color="text.secondary" paragraph>
        Generate semantic models automatically from your Databricks tables and materialized views with AI-powered suggestions.
      </Typography>

      {error && (
        <Alert severity="error" onClose={() => setError(null)} sx={{ mb: 3 }}>
          {error}
        </Alert>
      )}

      <Stepper activeStep={activeStep} orientation="vertical">
        {/* Step 1: Select Table */}
        <Step>
          <StepLabel>
            <Typography variant="h6">Select Table</Typography>
          </StepLabel>
          <StepContent>
            <Box sx={{ mb: 2 }}>
              <Grid container spacing={2} sx={{ mb: 2 }}>
                <Grid item xs={12} md={4}>
                  <FormControl fullWidth variant="outlined">
                    <InputLabel>Catalog</InputLabel>
                    <Select
                      value={selectedCatalog}
                      onChange={(e) => {
                        setSelectedCatalog(e.target.value);
                        setSelectedSchema(''); // Reset schema when catalog changes
                      }}
                      label="Catalog"
                    >
                      {catalogs.map((catalog) => (
                        <MenuItem key={catalog.catalog_name} value={catalog.catalog_name}>
                          {catalog.catalog_name}
                          {catalog.comment && (
                            <Typography variant="caption" color="text.secondary" sx={{ ml: 1 }}>
                              {catalog.comment}
                            </Typography>
                          )}
                        </MenuItem>
                      ))}
                    </Select>
                  </FormControl>
                </Grid>
                
                <Grid item xs={12} md={4}>
                  <FormControl fullWidth variant="outlined">
                    <InputLabel>Schema</InputLabel>
                    <Select
                      value={selectedSchema}
                      onChange={(e) => setSelectedSchema(e.target.value)}
                      label="Schema"
                      disabled={!selectedCatalog || schemas.length === 0}
                    >
                      <MenuItem value="">
                        <em>All schemas</em>
                      </MenuItem>
                      {schemas.map((schema) => (
                        <MenuItem key={schema.schema_name} value={schema.schema_name}>
                          {schema.schema_name}
                          <Typography variant="caption" color="text.secondary" sx={{ ml: 1 }}>
                            ({schema.table_count} tables)
                          </Typography>
                        </MenuItem>
                      ))}
                    </Select>
                    <Typography variant="caption" color="text.secondary" sx={{ mt: 0.5 }}>
                      {selectedCatalog && schemas.length > 0 && `${schemas.length} schemas available`}
                    </Typography>
                  </FormControl>
                </Grid>
                
                <Grid item xs={12} md={4}>
                  <TextField
                    fullWidth
                    label="Table name filter"
                    variant="outlined"
                    value={tableFilter}
                    onChange={(e: React.ChangeEvent<HTMLInputElement>) => setTableFilter(e.target.value)}
                    placeholder="Filter by name..."
                    helperText="Search in table names and descriptions"
                  />
                </Grid>
              </Grid>
              
              {/* Filter summary */}
              {!loading && (
                <Box sx={{ mb: 2, p: 2, bgcolor: 'background.paper', borderRadius: 1 }}>
                  <Typography variant="body2" color="text.secondary">
                    Showing {filteredTables.length} tables
                    {selectedCatalog && ` in catalog "${selectedCatalog}"`}
                    {selectedSchema && ` / schema "${selectedSchema}"`}
                    {tableFilter && ` matching "${tableFilter}"`}
                  </Typography>
                </Box>
              )}
              
              {loading ? (
                <Box sx={{ display: 'flex', justifyContent: 'center', p: 3 }}>
                  <CircularProgress />
                </Box>
              ) : filteredTables.length === 0 ? (
                <Alert severity="info" sx={{ mb: 2 }}>
                  No tables found. Try adjusting your filters or check your Databricks connection.
                </Alert>
              ) : (
                <TableContainer component={Paper} sx={{ maxHeight: 440, mb: 2 }}>
                  <Table stickyHeader aria-label="table selection" size="small">
                    <TableHead>
                      <TableRow>
                        <TableCell padding="checkbox" sx={{ width: 50 }}></TableCell>
                        <TableCell>Table Name</TableCell>
                        <TableCell>Catalog</TableCell>
                        <TableCell>Schema</TableCell>
                        <TableCell sx={{ minWidth: 200 }}>Description</TableCell>
                        <TableCell align="right">Rows</TableCell>
                        <TableCell align="right">Columns</TableCell>
                        <TableCell align="right">Size (MB)</TableCell>
                        <TableCell align="center">Type</TableCell>
                        <TableCell align="center">Has Model</TableCell>
                        <TableCell>Last Updated</TableCell>
                      </TableRow>
                    </TableHead>
                    <TableBody>
                      {filteredTables.map((table) => (
                        <TableRow
                          key={table.fullName}
                          hover
                          selected={selectedTable?.fullName === table.fullName}
                          onClick={() => setSelectedTable(table)}
                          sx={{ 
                            cursor: 'pointer',
                            '&.Mui-selected': {
                              backgroundColor: 'action.selected',
                            },
                            '&:hover': {
                              backgroundColor: 'action.hover',
                            }
                          }}
                        >
                          <TableCell padding="checkbox">
                            <Radio
                              checked={selectedTable?.fullName === table.fullName}
                              value={table.fullName}
                              size="small"
                              color="primary"
                            />
                          </TableCell>
                          <TableCell>
                            <Typography variant="body2" fontWeight={500}>
                              {table.table}
                            </Typography>
                          </TableCell>
                          <TableCell>
                            <Typography variant="body2">
                              {table.catalog}
                            </Typography>
                          </TableCell>
                          <TableCell>
                            <Typography variant="body2">
                              {table.schema}
                            </Typography>
                          </TableCell>
                          <TableCell>
                            <Typography 
                              variant="body2" 
                              sx={{ 
                                overflow: 'hidden',
                                textOverflow: 'ellipsis',
                                display: '-webkit-box',
                                WebkitLineClamp: 2,
                                WebkitBoxOrient: 'vertical',
                                maxWidth: 300,
                              }}
                              title={table.description || ''}
                            >
                              {table.description || '-'}
                            </Typography>
                          </TableCell>
                          <TableCell align="right">
                            <Typography variant="body2">
                              {table.rowCount?.toLocaleString() || '-'}
                            </Typography>
                          </TableCell>
                          <TableCell align="right">
                            <Typography variant="body2">
                              {table.columnCount || '-'}
                            </Typography>
                          </TableCell>
                          <TableCell align="right">
                            <Typography variant="body2">
                              {table.sizeMb ? table.sizeMb.toFixed(1) : '-'}
                            </Typography>
                          </TableCell>
                          <TableCell align="center">
                            <Chip 
                              label={table.tableType || 'TABLE'} 
                              size="small"
                              variant="outlined"
                              sx={{ fontSize: '0.75rem' }}
                            />
                          </TableCell>
                          <TableCell align="center">
                            {table.hasSemanticModel ? (
                              <Chip 
                                label="Yes" 
                                size="small" 
                                color="success"
                                sx={{ fontSize: '0.75rem' }}
                              />
                            ) : (
                              <Typography variant="body2" color="text.secondary">
                                -
                              </Typography>
                            )}
                          </TableCell>
                          <TableCell>
                            <Typography variant="body2" color="text.secondary">
                              {table.lastUpdated ? 
                                new Date(table.lastUpdated).toLocaleDateString() : 
                                '-'
                              }
                            </Typography>
                          </TableCell>
                        </TableRow>
                      ))}
                    </TableBody>
                  </Table>
                </TableContainer>
              )}
            </Box>
            
            <Box sx={{ mt: 2 }}>
              <Button
                variant="contained"
                onClick={analyzeTable}
                disabled={!selectedTable || loading}
                startIcon={<AnalyticsIcon />}
              >
                Analyze Table
              </Button>
            </Box>
          </StepContent>
        </Step>

        {/* Step 2: Review Analysis */}
        <Step>
          <StepLabel>
            <Typography variant="h6">Review Analysis</Typography>
          </StepLabel>
          <StepContent>
            {analysis && (
              <Box>
                <Alert severity="info" sx={{ mb: 2 }}>
                  <Typography variant="body2">
                    Analysis complete! Found {analysis.suggestedMetrics.length} potential metrics
                    and {analysis.suggestedDimensions.length} dimensions.
                    Overall confidence: {(analysis.confidenceScores.overall * 100).toFixed(0)}%
                  </Typography>
                </Alert>

                {/* Suggested Metrics */}
                <Accordion defaultExpanded>
                  <AccordionSummary expandIcon={<ExpandMoreIcon />}>
                    <Typography variant="h6">
                      Suggested Metrics ({selectedMetrics.size}/{analysis.suggestedMetrics.length})
                    </Typography>
                  </AccordionSummary>
                  <AccordionDetails>
                    <List>
                      {analysis.suggestedMetrics.map((metric) => (
                        <ListItem key={metric.name} divider>
                          <Checkbox
                            checked={selectedMetrics.has(metric.name)}
                            onChange={() => handleMetricToggle(metric.name)}
                          />
                          <ListItemText
                            primary={
                              <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                                <Typography>{metric.displayName}</Typography>
                                <Chip 
                                  label={metric.metricType}
                                  size="small"
                                  variant="outlined"
                                />
                                <Chip
                                  icon={getConfidenceIcon(metric.confidenceScore)}
                                  label={`${(metric.confidenceScore * 100).toFixed(0)}%`}
                                  size="small"
                                  color={getConfidenceColor(metric.confidenceScore)}
                                />
                              </Box>
                            }
                            secondary={
                              <Box>
                                <Typography variant="body2" color="text.secondary">
                                  {metric.description}
                                </Typography>
                                <Typography variant="caption" sx={{ fontFamily: 'monospace' }}>
                                  {metric.expression}
                                </Typography>
                              </Box>
                            }
                          />
                        </ListItem>
                      ))}
                    </List>
                  </AccordionDetails>
                </Accordion>

                {/* Suggested Dimensions */}
                <Accordion defaultExpanded sx={{ mt: 2 }}>
                  <AccordionSummary expandIcon={<ExpandMoreIcon />}>
                    <Typography variant="h6">
                      Suggested Dimensions ({selectedDimensions.size}/{analysis.suggestedDimensions.length})
                    </Typography>
                  </AccordionSummary>
                  <AccordionDetails>
                    <List>
                      {analysis.suggestedDimensions.map((dimension) => (
                        <ListItem key={dimension.name} divider>
                          <Checkbox
                            checked={selectedDimensions.has(dimension.name)}
                            onChange={() => handleDimensionToggle(dimension.name)}
                          />
                          <ListItemText
                            primary={
                              <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                                <Typography>{dimension.displayName}</Typography>
                                <Chip 
                                  label={dimension.type}
                                  size="small"
                                  variant="outlined"
                                  color={dimension.type === 'time' ? 'primary' : 'default'}
                                />
                              </Box>
                            }
                            secondary={
                              <Box>
                                {dimension.description && (
                                  <Typography variant="body2" color="text.secondary">
                                    {dimension.description}
                                  </Typography>
                                )}
                                {dimension.granularities && (
                                  <Box sx={{ mt: 0.5 }}>
                                    {dimension.granularities.map((gran) => (
                                      <Chip
                                        key={gran}
                                        label={gran}
                                        size="small"
                                        sx={{ mr: 0.5, mb: 0.5 }}
                                      />
                                    ))}
                                  </Box>
                                )}
                              </Box>
                            }
                          />
                        </ListItem>
                      ))}
                    </List>
                  </AccordionDetails>
                </Accordion>

                <Box sx={{ mt: 3, display: 'flex', gap: 2 }}>
                  <Button
                    variant="outlined"
                    onClick={() => setActiveStep(0)}
                  >
                    Back
                  </Button>
                  <Button
                    variant="contained"
                    onClick={() => setActiveStep(2)}
                    disabled={selectedMetrics.size === 0}
                  >
                    Continue to Customization
                  </Button>
                </Box>
              </Box>
            )}
          </StepContent>
        </Step>

        {/* Step 3: Customize Model */}
        <Step>
          <StepLabel>
            <Typography variant="h6">Customize Model</Typography>
          </StepLabel>
          <StepContent>
            <Box sx={{ mb: 3 }}>
              <TextField
                fullWidth
                label="Model Name"
                variant="outlined"
                value={customization.modelName || ''}
                onChange={(e: React.ChangeEvent<HTMLInputElement>) => setCustomization({ ...customization, modelName: e.target.value })}
                placeholder={`${selectedTable?.table}_model`}
                sx={{ mb: 2 }}
              />
              
              <TextField
                fullWidth
                multiline
                rows={3}
                label="Model Description"
                variant="outlined"
                value={customization.description || ''}
                onChange={(e: React.ChangeEvent<HTMLInputElement>) => setCustomization({ ...customization, description: e.target.value })}
                placeholder="Describe the purpose and contents of this semantic model..."
                sx={{ mb: 2 }}
              />
              
              <Box sx={{ mb: 2 }}>
                <Typography gutterBottom>
                  Minimum Confidence Score: {(customization.minimumConfidenceScore * 100).toFixed(0)}%
                </Typography>
                <Box sx={{ px: 2 }}>
                  <input
                    type="range"
                    min="0"
                    max="100"
                    value={customization.minimumConfidenceScore * 100}
                    onChange={(e) => setCustomization({ 
                      ...customization, 
                      minimumConfidenceScore: Number(e.target.value) / 100 
                    })}
                    style={{ width: '100%' }}
                  />
                </Box>
                <Typography variant="caption" color="text.secondary">
                  Only include suggestions with confidence above this threshold
                </Typography>
              </Box>
              
              <Alert severity="info">
                <Typography variant="body2">
                  Selected {selectedMetrics.size} metrics and {selectedDimensions.size} dimensions
                  for the model. You can go back to adjust selections if needed.
                </Typography>
              </Alert>
            </Box>
            
            <Box sx={{ display: 'flex', gap: 2 }}>
              <Button
                variant="outlined"
                onClick={() => setActiveStep(1)}
              >
                Back
              </Button>
              <Button
                variant="contained"
                onClick={generateModel}
                disabled={loading}
                startIcon={loading ? <CircularProgress size={20} /> : <AutoAwesomeIcon />}
              >
                Generate Model
              </Button>
            </Box>
          </StepContent>
        </Step>

        {/* Step 4: Generate & Save */}
        <Step>
          <StepLabel>
            <Typography variant="h6">Generate & Save</Typography>
          </StepLabel>
          <StepContent>
            {generatedModel && (
              <Box>
                <Alert severity="success" sx={{ mb: 2 }}>
                  <Typography variant="body2">
                    Model generated successfully! The semantic model has been saved to:
                    <br />
                    <strong>{generatedModel.filePath}</strong>
                  </Typography>
                </Alert>

                {generatedModel.validationResult && (
                  <Box sx={{ mb: 2 }}>
                    {generatedModel.validationResult.warnings?.length > 0 && (
                      <Alert severity="warning" sx={{ mb: 1 }}>
                        <Typography variant="body2" gutterBottom>
                          <strong>Warnings:</strong>
                        </Typography>
                        <ul style={{ margin: 0, paddingLeft: 20 }}>
                          {generatedModel.validationResult.warnings.map((warning: string, idx: number) => (
                            <li key={idx}><Typography variant="body2">{warning}</Typography></li>
                          ))}
                        </ul>
                      </Alert>
                    )}
                    
                    {generatedModel.validationResult.suggestions?.length > 0 && (
                      <Alert severity="info">
                        <Typography variant="body2" gutterBottom>
                          <strong>Suggestions:</strong>
                        </Typography>
                        <ul style={{ margin: 0, paddingLeft: 20 }}>
                          {generatedModel.validationResult.suggestions.map((suggestion: string, idx: number) => (
                            <li key={idx}><Typography variant="body2">{suggestion}</Typography></li>
                          ))}
                        </ul>
                      </Alert>
                    )}
                  </Box>
                )}

                <Box sx={{ mb: 2 }}>
                  <Button
                    variant="contained"
                    onClick={() => setShowYamlDialog(true)}
                    startIcon={<PreviewIcon />}
                    sx={{ mr: 1 }}
                  >
                    Preview YAML
                  </Button>
                  <Button
                    variant="outlined"
                    onClick={downloadYaml}
                    startIcon={<DownloadIcon />}
                  >
                    Download YAML
                  </Button>
                </Box>

                <Box sx={{ mt: 3 }}>
                  <Button
                    variant="outlined"
                    onClick={() => {
                      setActiveStep(0);
                      setSelectedTable(null);
                      setAnalysis(null);
                      setGeneratedModel(null);
                      setYamlPreview('');
                    }}
                  >
                    Generate Another Model
                  </Button>
                </Box>
              </Box>
            )}
          </StepContent>
        </Step>
      </Stepper>

      {/* YAML Preview Dialog */}
      <Dialog
        open={showYamlDialog}
        onClose={() => setShowYamlDialog(false)}
        maxWidth="lg"
        fullWidth
      >
        <DialogTitle>
          <Box sx={{ display: 'flex', alignItems: 'center' }}>
            <CodeIcon sx={{ mr: 1 }} />
            Generated Semantic Model YAML
          </Box>
        </DialogTitle>
        <DialogContent>
          <Box sx={{ maxHeight: '70vh', overflow: 'auto' }}>
            <SyntaxHighlighter
              language="yaml"
              style={tomorrow}
              showLineNumbers
              customStyle={{
                margin: 0,
                fontSize: '0.875rem',
              }}
            >
              {yamlPreview}
            </SyntaxHighlighter>
          </Box>
        </DialogContent>
        <DialogActions>
          <Button onClick={downloadYaml} startIcon={<DownloadIcon />}>
            Download
          </Button>
          <Button onClick={() => setShowYamlDialog(false)}>
            Close
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
};
