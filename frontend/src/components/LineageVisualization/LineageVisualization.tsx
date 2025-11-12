import React, { useState, useEffect, useCallback } from 'react';
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
  Chip,
  IconButton,
  Tooltip,
  Drawer,
  TextField,
  Grid,
  Card,
  CardContent,
  Stack,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Accordion,
  AccordionSummary,
  AccordionDetails,
  Switch,
  FormControlLabel,
  Slider
} from '@mui/material';
import {
  TableCellsIcon,
  EyeIcon,
  DocumentArrowDownIcon,
  MagnifyingGlassIcon,
  AdjustmentsHorizontalIcon,
  ChartBarIcon,
  CubeIcon,
  ShareIcon,
  ArrowsPointingInIcon,
  XMarkIcon,
  InformationCircleIcon,
  ExclamationTriangleIcon,
  ChevronLeftIcon,
  ChevronRightIcon
} from '@heroicons/react/24/outline';
import ReactFlow, {
  Node,
  Edge,
  Controls,
  Background,
  useNodesState,
  useEdgesState,
  addEdge,
  Connection,
  ReactFlowProvider,
  Panel,
  MiniMap,
  ConnectionMode,
  NodeTypes,
  useReactFlow
} from 'reactflow';
import 'reactflow/dist/style.css';
import { useQuery, useMutation } from '@tanstack/react-query';
import { lineageAPI, catalogAPI } from '../../services/api';

// Custom node components
const TableNode = ({ data }: { data: any }) => (
  <Box
    sx={{
      padding: 2,
      backgroundColor: '#3B82F6',
      color: 'white',
      borderRadius: 2,
      minWidth: 120,
      textAlign: 'center',
      border: '2px solid #1E40AF',
      '&:hover': { backgroundColor: '#2563EB' }
    }}
  >
    <TableCellsIcon style={{ width: 20, height: 20, marginBottom: 4 }} />
    <Typography variant="body2" fontWeight={500}>
      {data.name}
    </Typography>
    {data.catalog && (
      <Typography variant="caption" display="block">
        {data.catalog}.{data.schema}
      </Typography>
    )}
  </Box>
);

const ViewNode = ({ data }: { data: any }) => (
  <Box
    sx={{
      padding: 2,
      backgroundColor: '#10B981',
      color: 'white',
      borderRadius: 2,
      minWidth: 120,
      textAlign: 'center',
      border: '2px solid #047857'
    }}
  >
    <EyeIcon style={{ width: 20, height: 20, marginBottom: 4 }} />
    <Typography variant="body2" fontWeight={500}>
      {data.name}
    </Typography>
  </Box>
);

const ModelNode = ({ data }: { data: any }) => (
  <Box
    sx={{
      padding: 2,
      backgroundColor: '#F59E0B',
      color: 'white',
      borderRadius: 2,
      minWidth: 120,
      textAlign: 'center',
      border: '2px solid #D97706'
    }}
  >
    <CubeIcon style={{ width: 20, height: 20, marginBottom: 4 }} />
    <Typography variant="body2" fontWeight={500}>
      {data.name}
    </Typography>
  </Box>
);

const MetricNode = ({ data }: { data: any }) => (
  <Box
    sx={{
      padding: 2,
      backgroundColor: '#EF4444',
      color: 'white',
      borderRadius: 2,
      minWidth: 120,
      textAlign: 'center',
      border: '2px solid #DC2626'
    }}
  >
    <ChartBarIcon style={{ width: 20, height: 20, marginBottom: 4 }} />
    <Typography variant="body2" fontWeight={500}>
      {data.name}
    </Typography>
  </Box>
);

// Node types configuration
const nodeTypes: NodeTypes = {
  TABLE: TableNode,
  VIEW: ViewNode,
  MODEL: ModelNode,
  METRIC: MetricNode,
  DIMENSION: ViewNode,
  COLUMN: TableNode,
  FILE: TableNode,
  EXTERNAL: ViewNode
};

// Inner component that can use React Flow hooks
const LineageFlowContent: React.FC<{
  nodes: Node[];
  edges: Edge[];
  onNodesChange: any;
  onEdgesChange: any;
  onNodeClick: any;
  onConnect: any;
  shouldFitView: boolean;
  setShouldFitView: (value: boolean) => void;
  children?: React.ReactNode;
}> = ({ 
  nodes, 
  edges, 
  onNodesChange, 
  onEdgesChange, 
  onNodeClick, 
  onConnect, 
  shouldFitView,
  setShouldFitView,
  children
}) => {
  const { fitView } = useReactFlow();

  useEffect(() => {
    if (shouldFitView && nodes.length > 0) {
      setTimeout(() => {
        fitView({ padding: 0.2, duration: 800 });
        setShouldFitView(false);
      }, 100);
    }
  }, [shouldFitView, nodes.length, fitView, setShouldFitView]);

  const handleFitView = () => {
    fitView({ padding: 0.2, duration: 800 });
  };

  return (
    <>
      <ReactFlow
        nodes={nodes}
        edges={edges}
        onNodesChange={onNodesChange}
        onEdgesChange={onEdgesChange}
        onNodeClick={onNodeClick}
        onConnect={onConnect}
        nodeTypes={nodeTypes}
        connectionMode={ConnectionMode.Loose}
        fitView
        attributionPosition="bottom-left"
        minZoom={0.1}
        maxZoom={2}
        defaultViewport={{ x: 0, y: 0, zoom: 0.8 }}
      >
        <Background />
        <Controls />
        <MiniMap 
          nodeStrokeWidth={3}
          nodeColor={(node) => {
            switch (node.type) {
              case 'TABLE': return '#3B82F6';
              case 'VIEW': return '#10B981';
              case 'MODEL': return '#8B5CF6';
              case 'METRIC': return '#F59E0B';
              default: return '#6B7280';
            }
          }}
          maskColor="rgba(0, 0, 0, 0.2)"
          style={{
            backgroundColor: '#f8fafc',
          }}
        />
        
        {/* Fit View Button */}
        <Panel position="bottom-right">
          <Button
            variant="contained"
            onClick={handleFitView}
            size="small"
            startIcon={<ArrowsPointingInIcon className="h-4 w-4" />}
            sx={{ mr: 1, mb: 1 }}
          >
            Fit View
          </Button>
        </Panel>
        
        {children}
      </ReactFlow>
    </>
  );
};

interface LineageVisualizationProps {
  initialCatalog?: string;
  initialSchema?: string;
  initialTable?: string;
  initialModelId?: string;
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
      id={`lineage-tabpanel-${index}`}
      aria-labelledby={`lineage-tab-${index}`}
      {...other}
    >
      {value === index && <Box sx={{ py: 3 }}>{children}</Box>}
    </div>
  );
};

const LineageVisualization: React.FC<LineageVisualizationProps> = ({
  initialCatalog = '',
  initialSchema = '',
  initialTable = '',
  initialModelId = ''
}) => {
  // State management
  const [activeTab, setActiveTab] = useState(0);
  const [nodes, setNodes, onNodesChange] = useNodesState([]);
  const [edges, setEdges, onEdgesChange] = useEdgesState([]);
  const [selectedEntity, setSelectedEntity] = useState<any>(null);
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [settingsOpen, setSettingsOpen] = useState(false);
  
  // Form state
  const [catalog, setCatalog] = useState(initialCatalog);
  const [schema, setSchema] = useState(initialSchema);
  const [table, setTable] = useState(initialTable);
  const [modelId, setModelId] = useState(initialModelId);
  const [direction, setDirection] = useState<'upstream' | 'downstream' | 'both'>('both');
  const [depth, setDepth] = useState(3);
  const [includeColumns, setIncludeColumns] = useState(false);
  const [layoutAlgorithm, setLayoutAlgorithm] = useState('hierarchical');
  
  // Available options for dropdowns
  const [availableCatalogs, setAvailableCatalogs] = useState<Array<{catalog_name: string, comment: string}>>([]);
  const [availableSchemas, setAvailableSchemas] = useState<Array<{schema_name: string, comment: string, table_count: number}>>([]);
  const [availableTables, setAvailableTables] = useState<Array<{table: string, description?: string}>>([]);
  
  // Error and loading states
  const [error, setError] = useState<string>('');
  const [exportDialogOpen, setExportDialogOpen] = useState(false);
  const [configPanelCollapsed, setConfigPanelCollapsed] = useState(false);

  // Query for catalogs
  const { data: catalogsData } = useQuery({
    queryKey: ['catalogs'],
    queryFn: () => catalogAPI.getCatalogs()
  });

  // Query for schemas when catalog changes
  const { data: schemasData } = useQuery({
    queryKey: ['schemas', catalog],
    queryFn: () => catalogAPI.getSchemas(catalog),
    enabled: !!catalog
  });

  // Query for tables when catalog and schema change
  const { data: tablesData } = useQuery({
    queryKey: ['tables', catalog, schema],
    queryFn: () => catalogAPI.getGoldTables(catalog, schema),
    enabled: !!catalog && !!schema
  });

  // Update available options when data changes
  useEffect(() => {
    if (catalogsData?.data?.catalogs) {
      setAvailableCatalogs(catalogsData.data.catalogs);
    }
  }, [catalogsData]);

  useEffect(() => {
    if (schemasData?.data?.schemas) {
      setAvailableSchemas(schemasData.data.schemas);
      // Reset schema and table when catalog changes
      if (schema) {
        const schemaExists = schemasData.data.schemas.some((s: any) => s.schema_name === schema);
        if (!schemaExists) {
          setSchema('');
          setTable('');
        }
      }
    }
  }, [schemasData, schema]);

  useEffect(() => {
    if (tablesData?.data) {
      setAvailableTables(tablesData.data);
      // Reset table when schema changes
      if (table) {
        const tableExists = tablesData.data.some((t: any) => t.table === table);
        if (!tableExists) {
          setTable('');
        }
      }
    }
  }, [tablesData, table]);

  // Query for table lineage
  const {
    data: lineageData,
    isLoading: lineageLoading,
    refetch: refetchLineage,
    error: lineageError
  } = useQuery({
    queryKey: ['table-lineage', catalog, schema, table, direction, depth, includeColumns, layoutAlgorithm],
    queryFn: () => lineageAPI.getTableLineage({
      catalog,
      schema,
      table,
      direction,
      depth,
      include_columns: includeColumns,
      layout_algorithm: layoutAlgorithm
    }),
    enabled: false // Manual trigger
  });

  // Query for model lineage
  const {
    data: modelLineageData,
    isLoading: modelLineageLoading,
    refetch: refetchModelLineage,
    error: modelLineageError
  } = useQuery({
    queryKey: ['model-lineage', modelId, depth, layoutAlgorithm],
    queryFn: () => lineageAPI.getModelLineage(modelId, {
      depth,
      layout_algorithm: layoutAlgorithm
    }),
    enabled: false // Manual trigger
  });

  // Export mutation
  const exportMutation = useMutation({
    mutationFn: lineageAPI.exportLineage,
    onSuccess: (blob, variables) => {
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `lineage.${variables.format}`;
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);
      document.body.removeChild(a);
      setExportDialogOpen(false);
    },
    onError: (error: any) => {
      setError(error.message || 'Failed to export lineage');
    }
  });

  // Impact analysis mutation
  const impactMutation = useMutation({
    mutationFn: lineageAPI.analyzeImpact,
    onSuccess: (data) => {
      // Handle impact analysis results
      console.log('Impact analysis:', data);
    }
  });

  // Auto-layout function for better node positioning
  const autoLayoutNodes = useCallback((nodes: Node[], edges: Edge[], algorithm: string = 'hierarchical') => {
    if (nodes.length === 0) return nodes;

    switch (algorithm) {
      case 'hierarchical':
        return hierarchicalLayout(nodes, edges);
      case 'force':
        return forceLayout(nodes, edges);
      case 'circular':
        return circularLayout(nodes);
      case 'tree':
        return treeLayout(nodes, edges);
      default:
        return hierarchicalLayout(nodes, edges);
    }
  }, []);

  // Hierarchical layout implementation
  const hierarchicalLayout = (nodes: Node[], edges: Edge[]) => {
    const nodeMap = new Map(nodes.map(node => [node.id, node]));
    const incomingEdges = new Map<string, string[]>();
    const outgoingEdges = new Map<string, string[]>();
    
    // Build adjacency lists
    edges.forEach(edge => {
      if (!incomingEdges.has(edge.target)) incomingEdges.set(edge.target, []);
      if (!outgoingEdges.has(edge.source)) outgoingEdges.set(edge.source, []);
      incomingEdges.get(edge.target)!.push(edge.source);
      outgoingEdges.get(edge.source)!.push(edge.target);
    });

    // Find root nodes (no incoming edges)
    const rootNodes = nodes.filter(node => !incomingEdges.has(node.id) || incomingEdges.get(node.id)!.length === 0);
    
    // Level assignment
    const levels = new Map<string, number>();
    const visited = new Set<string>();
    
    const assignLevels = (nodeId: string, level: number) => {
      if (visited.has(nodeId)) return;
      visited.add(nodeId);
      levels.set(nodeId, Math.max(levels.get(nodeId) || 0, level));
      
      const children = outgoingEdges.get(nodeId) || [];
      children.forEach(childId => assignLevels(childId, level + 1));
    };

    rootNodes.forEach(node => assignLevels(node.id, 0));
    
    // Handle disconnected nodes
    nodes.forEach(node => {
      if (!levels.has(node.id)) {
        levels.set(node.id, 0);
      }
    });

    // Group nodes by level
    const nodesByLevel = new Map<number, Node[]>();
    nodes.forEach(node => {
      const level = levels.get(node.id) || 0;
      if (!nodesByLevel.has(level)) nodesByLevel.set(level, []);
      nodesByLevel.get(level)!.push(node);
    });

    // Position nodes
    const levelHeight = 200;
    const nodeWidth = 180;
    const positioned: Node[] = [];

    Array.from(nodesByLevel.keys()).sort((a, b) => a - b).forEach(level => {
      const levelNodes = nodesByLevel.get(level)!;
      const totalWidth = levelNodes.length * nodeWidth;
      const startX = -totalWidth / 2;

      levelNodes.forEach((node, index) => {
        positioned.push({
          ...node,
          position: {
            x: startX + (index * nodeWidth) + (nodeWidth / 2),
            y: level * levelHeight
          }
        });
      });
    });

    return positioned;
  };

  // Force-directed layout (simplified)
  const forceLayout = (nodes: Node[], edges: Edge[]) => {
    const positioned = nodes.map((node, index) => ({
      ...node,
      position: {
        x: (index % 4) * 200 + Math.random() * 100,
        y: Math.floor(index / 4) * 150 + Math.random() * 50
      }
    }));
    return positioned;
  };

  // Circular layout
  const circularLayout = (nodes: Node[]) => {
    const radius = Math.max(150, nodes.length * 30);
    const angleStep = (2 * Math.PI) / nodes.length;
    
    return nodes.map((node, index) => ({
      ...node,
      position: {
        x: Math.cos(index * angleStep) * radius,
        y: Math.sin(index * angleStep) * radius
      }
    }));
  };

  // Tree layout (simple top-down)
  const treeLayout = (nodes: Node[], edges: Edge[]) => {
    // Similar to hierarchical but with more spacing
    return hierarchicalLayout(nodes, edges).map(node => ({
      ...node,
      position: {
        x: node.position.x * 1.5,
        y: node.position.y * 1.2
      }
    }));
  };

  // Convert API data to React Flow format
  const convertToReactFlowData = useCallback((data: any) => {
    if (!data?.graph) return { nodes: [], edges: [] };

    const flowNodes: Node[] = data.graph.nodes.map((node: any) => ({
      id: node.id,
      type: node.type,
      position: { x: 0, y: 0 }, // Will be positioned by layout algorithm
      data: {
        name: node.name,
        type: node.type,
        catalog: node.catalog,
        schema: node.schema,
        description: node.description,
        metadata: node.metadata,
        ...node
      }
    }));

    const flowEdges: Edge[] = data.graph.edges.map((edge: any) => ({
      id: edge.id,
      source: edge.source,
      target: edge.target,
      type: 'smoothstep',
      animated: edge.animated || false,
      style: {
        stroke: edge.color || '#6B7280',
        strokeWidth: 2.5
      },
      markerEnd: {
        type: 'arrowclosed',
        width: 20,
        height: 20,
        color: edge.color || '#6B7280'
      },
      label: edge.label,
      data: edge.metadata
    }));

    // Apply auto-layout
    const layoutedNodes = autoLayoutNodes(flowNodes, flowEdges, layoutAlgorithm);

    return { nodes: layoutedNodes, edges: flowEdges };
  }, [autoLayoutNodes, layoutAlgorithm]);

  // Update React Flow when data changes
  useEffect(() => {
    const data = activeTab === 0 ? lineageData : modelLineageData;
    if (data) {
      const { nodes: flowNodes, edges: flowEdges } = convertToReactFlowData(data);
      setNodes(flowNodes);
      setEdges(flowEdges);
      // Trigger fit view after nodes are set
      setShouldFitView(true);
    }
  }, [lineageData, modelLineageData, activeTab, convertToReactFlowData, setNodes, setEdges]);

  // Handle table lineage request
  const handleTableLineage = useCallback(() => {
    if (!catalog || !schema || !table) {
      setError('Please provide catalog, schema, and table name');
      return;
    }
    setError('');
    refetchLineage();
  }, [catalog, schema, table, refetchLineage]);

  // Handle model lineage request
  const handleModelLineage = useCallback(() => {
    if (!modelId) {
      setError('Please provide model ID');
      return;
    }
    setError('');
    refetchModelLineage();
  }, [modelId, refetchModelLineage]);

  // Re-layout existing nodes when layout algorithm changes
  const handleLayoutChange = useCallback((newLayout: string) => {
    if (nodes.length > 0) {
      const layoutedNodes = autoLayoutNodes(nodes, edges, newLayout);
      setNodes(layoutedNodes);
    }
    setLayoutAlgorithm(newLayout);
  }, [nodes, edges, autoLayoutNodes, setNodes]);

  // Fit view function will be passed down to inner component
  const [shouldFitView, setShouldFitView] = useState(false);

  // Handle node click
  const onNodeClick = useCallback((_: any, node: Node) => {
    setSelectedEntity(node.data);
    setSidebarOpen(true);
  }, []);

  // Handle edge connection (for interactive editing)
  const onConnect = useCallback((params: Connection) => {
    setEdges((eds) => addEdge(params, eds));
  }, [setEdges]);

  // Handle export
  const handleExport = useCallback((format: string) => {
    const currentGraph = activeTab === 0 ? lineageData?.graph : modelLineageData?.graph;
    if (!currentGraph) {
      setError('No lineage data to export');
      return;
    }

    exportMutation.mutate({
      graph: currentGraph,
      format,
      layout_algorithm: layoutAlgorithm,
      include_metadata: true
    });
  }, [activeTab, lineageData, modelLineageData, layoutAlgorithm, exportMutation]);

  // Handle impact analysis
  const handleImpactAnalysis = useCallback(() => {
    if (!selectedEntity) return;

    const entityType = selectedEntity.type === 'TABLE' ? 'TABLE' : 'MODEL';
    const entityId = entityType === 'TABLE' 
      ? `${selectedEntity.catalog}.${selectedEntity.schema}.${selectedEntity.name}`
      : selectedEntity.name;

    impactMutation.mutate({
      entity_id: entityId,
      entity_type: entityType,
      change_type: 'schema_change',
      depth: 5
    });
  }, [selectedEntity, impactMutation]);

  const isLoading = lineageLoading || modelLineageLoading;
  const currentError = lineageError || modelLineageError || error;

  return (
    <Box sx={{ height: '100vh', display: 'flex', flexDirection: 'column' }}>
      {/* Clean Header */}
      <Paper 
        elevation={0} 
        sx={{ 
          borderBottom: '1px solid #e0e0e0',
          backgroundColor: 'white'
        }}
      >
        <Box sx={{ p: 3 }}>
          <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
            <Box>
              <Typography variant="h4" component="h1" fontWeight={600} sx={{ mb: 1, color: '#1f2937' }}>
                Data Lineage Explorer
              </Typography>
              <Typography variant="body1" sx={{ color: '#6b7280' }}>
                Discover and visualize data relationships across your organization
              </Typography>
            </Box>
            <Stack direction="row" spacing={1}>
              <Tooltip title="Visualization Settings">
                <IconButton 
                  onClick={() => setSettingsOpen(true)}
                  sx={{ 
                    color: '#6b7280', 
                    backgroundColor: '#f9fafb',
                    border: '1px solid #e5e7eb',
                    '&:hover': { 
                      backgroundColor: '#f3f4f6',
                      color: '#374151'
                    }
                  }}
                >
                  <AdjustmentsHorizontalIcon className="h-5 w-5" />
                </IconButton>
              </Tooltip>
              <Tooltip title="Export Lineage">
                <IconButton 
                  onClick={() => setExportDialogOpen(true)}
                  sx={{ 
                    color: '#6b7280', 
                    backgroundColor: '#f9fafb',
                    border: '1px solid #e5e7eb',
                    '&:hover': { 
                      backgroundColor: '#f3f4f6',
                      color: '#374151'
                    }
                  }}
                >
                  <DocumentArrowDownIcon className="h-5 w-5" />
                </IconButton>
              </Tooltip>
              <Tooltip title="Share View">
                <IconButton 
                  sx={{ 
                    color: '#6b7280', 
                    backgroundColor: '#f9fafb',
                    border: '1px solid #e5e7eb',
                    '&:hover': { 
                      backgroundColor: '#f3f4f6',
                      color: '#374151'
                    }
                  }}
                >
                  <ShareIcon className="h-5 w-5" />
                </IconButton>
              </Tooltip>
            </Stack>
          </Box>

          {/* Clean Tab Design */}
          <Box sx={{ 
            backgroundColor: '#f9fafb', 
            borderRadius: 2, 
            p: 1,
            display: 'flex',
            gap: 1,
            border: '1px solid #e5e7eb'
          }}>
            {['Table Lineage', 'Model Lineage', 'Impact Analysis'].map((label, index) => (
              <Button
                key={index}
                variant={activeTab === index ? "contained" : "text"}
                onClick={() => setActiveTab(index)}
                sx={{
                  flex: 1,
                  color: activeTab === index ? '#1f2937' : '#6b7280',
                  backgroundColor: activeTab === index ? 'white' : 'transparent',
                  fontWeight: 600,
                  borderRadius: 1.5,
                  textTransform: 'none',
                  boxShadow: activeTab === index ? '0 1px 3px rgba(0, 0, 0, 0.1)' : 'none',
                  '&:hover': {
                    backgroundColor: activeTab === index ? 'white' : '#f3f4f6',
                    color: '#374151'
                  },
                  '& .MuiButton-startIcon': {
                    mr: 1,
                    '& svg': { width: 18, height: 18 }
                  }
                }}
                startIcon={
                  index === 0 ? <TableCellsIcon /> :
                  index === 1 ? <CubeIcon /> :
                  <ExclamationTriangleIcon />
                }
              >
                {label}
              </Button>
            ))}
          </Box>
        </Box>
      </Paper>

      {/* Content */}
      <Box sx={{ flex: 1, display: 'flex' }}>
        {/* Main visualization area */}
        <Box sx={{ flex: 1, position: 'relative' }}>
          <ReactFlowProvider>
            <LineageFlowContent
              nodes={nodes}
              edges={edges}
              onNodesChange={onNodesChange}
              onEdgesChange={onEdgesChange}
              onNodeClick={onNodeClick}
              onConnect={onConnect}
              shouldFitView={shouldFitView}
              setShouldFitView={setShouldFitView}
            >
              {/* Modern Control Panel */}
              <Panel position="top-left">
                <Card sx={{ 
                  minWidth: configPanelCollapsed ? 60 : 400, 
                  maxWidth: configPanelCollapsed ? 60 : 450,
                  borderRadius: 2,
                  boxShadow: '0 4px 6px -1px rgba(0, 0, 0, 0.1)',
                  border: '1px solid #e5e7eb',
                  backgroundColor: 'white',
                  transition: 'all 0.3s ease-in-out'
                }}>
                  {/* Collapse/Expand Button */}
                  <Box sx={{ 
                    display: 'flex', 
                    justifyContent: configPanelCollapsed ? 'center' : 'space-between',
                    alignItems: 'center',
                    p: 1,
                    borderBottom: configPanelCollapsed ? 'none' : '1px solid #e5e7eb'
                  }}>
                    {configPanelCollapsed && (
                      <Box sx={{ display: 'flex', flexDirection: 'column', alignItems: 'center', py: 2 }}>
                        {activeTab === 0 && <TableCellsIcon className="h-6 w-6" style={{ color: '#6b7280' }} />}
                        {activeTab === 1 && <CubeIcon className="h-6 w-6" style={{ color: '#6b7280' }} />}
                        {activeTab === 2 && <ExclamationTriangleIcon className="h-6 w-6" style={{ color: '#6b7280' }} />}
                      </Box>
                    )}
                    {!configPanelCollapsed && (
                      <Typography variant="subtitle2" sx={{ color: '#6b7280', fontWeight: 600, ml: 1 }}>
                        Configuration
                      </Typography>
                    )}
                    <Tooltip title={configPanelCollapsed ? "Expand Configuration" : "Minimize Configuration"}>
                      <IconButton
                        size="small"
                        onClick={() => setConfigPanelCollapsed(!configPanelCollapsed)}
                        sx={{ 
                          color: '#6b7280',
                          '&:hover': { 
                            backgroundColor: '#f3f4f6',
                            color: '#374151'
                          }
                        }}
                      >
                        {configPanelCollapsed ? (
                          <ChevronRightIcon className="h-5 w-5" />
                        ) : (
                          <ChevronLeftIcon className="h-5 w-5" />
                        )}
                      </IconButton>
                    </Tooltip>
                  </Box>

                  {!configPanelCollapsed && (
                    <CardContent sx={{ p: 3, pt: 2 }}>
                      <TabPanel value={activeTab} index={0}>
                      <Box sx={{ display: 'flex', alignItems: 'center', mb: 3 }}>
                        <TableCellsIcon className="h-6 w-6" style={{ marginRight: 12, color: '#6b7280' }} />
                        <Typography variant="h6" fontWeight={600} sx={{ color: '#1f2937' }}>
                          Table Lineage Configuration
                        </Typography>
                      </Box>
                      
                      <Grid container spacing={3}>
                        {/* Catalog Selection */}
                        <Grid item xs={12}>
                          <FormControl fullWidth size="small">
                            <InputLabel>Catalog</InputLabel>
                            <Select
                              value={catalog}
                              onChange={(e) => setCatalog(e.target.value)}
                              label="Catalog"
                              disabled={!availableCatalogs.length}
                            >
                              {availableCatalogs.map((cat) => (
                                <MenuItem key={cat.catalog_name} value={cat.catalog_name}>
                                  <Box>
                                    <Typography variant="body2" fontWeight={500}>
                                      {cat.catalog_name}
                                    </Typography>
                                    {cat.comment && (
                                      <Typography variant="caption" color="text.secondary">
                                        {cat.comment}
                                      </Typography>
                                    )}
                                  </Box>
                                </MenuItem>
                              ))}
                            </Select>
                          </FormControl>
                        </Grid>

                        {/* Schema Selection */}
                        <Grid item xs={12}>
                          <FormControl fullWidth size="small">
                            <InputLabel>Schema</InputLabel>
                            <Select
                              value={schema}
                              onChange={(e) => setSchema(e.target.value)}
                              label="Schema"
                              disabled={!catalog || !availableSchemas.length}
                            >
                              {availableSchemas.map((sch) => (
                                <MenuItem key={sch.schema_name} value={sch.schema_name}>
                                  <Box sx={{ display: 'flex', justifyContent: 'space-between', width: '100%' }}>
                                    <Box>
                                      <Typography variant="body2" fontWeight={500}>
                                        {sch.schema_name}
                                      </Typography>
                                      {sch.comment && (
                                        <Typography variant="caption" color="text.secondary">
                                          {sch.comment}
                                        </Typography>
                                      )}
                                    </Box>
                                    <Chip
                                      label={`${sch.table_count} tables`}
                                      size="small"
                                      variant="outlined"
                                      color="primary"
                                    />
                                  </Box>
                                </MenuItem>
                              ))}
                            </Select>
                          </FormControl>
                        </Grid>

                        {/* Table Selection */}
                        <Grid item xs={12}>
                          <FormControl fullWidth size="small">
                            <InputLabel>Table</InputLabel>
                            <Select
                              value={table}
                              onChange={(e) => setTable(e.target.value)}
                              label="Table"
                              disabled={!schema || !availableTables.length}
                            >
                              {availableTables.map((tbl) => (
                                <MenuItem key={tbl.table} value={tbl.table}>
                                  <Box>
                                    <Typography variant="body2" fontWeight={500}>
                                      {tbl.table}
                                    </Typography>
                                    {tbl.description && (
                                      <Typography variant="caption" color="text.secondary">
                                        {tbl.description}
                                      </Typography>
                                    )}
                                  </Box>
                                </MenuItem>
                              ))}
                            </Select>
                          </FormControl>
                        </Grid>

                        {/* Direction and Depth */}
                        <Grid item xs={6}>
                          <FormControl fullWidth size="small">
                            <InputLabel>Direction</InputLabel>
                            <Select
                              value={direction}
                              onChange={(e) => setDirection(e.target.value as any)}
                              label="Direction"
                            >
                              <MenuItem value="upstream">↑ Upstream</MenuItem>
                              <MenuItem value="downstream">↓ Downstream</MenuItem>
                              <MenuItem value="both">↕ Both</MenuItem>
                            </Select>
                          </FormControl>
                        </Grid>
                        <Grid item xs={6}>
                          <FormControl fullWidth size="small">
                            <InputLabel>Depth</InputLabel>
                            <Select
                              value={depth}
                              onChange={(e) => setDepth(e.target.value as number)}
                              label="Depth"
                            >
                              {[1, 2, 3, 4, 5, 6, 7, 8, 9, 10].map((d) => (
                                <MenuItem key={d} value={d}>{d} level{d > 1 ? 's' : ''}</MenuItem>
                              ))}
                            </Select>
                          </FormControl>
                        </Grid>

                        {/* Analyze Button */}
                        <Grid item xs={12}>
                          <Button
                            variant="contained"
                            onClick={handleTableLineage}
                            disabled={isLoading || !catalog || !schema || !table}
                            fullWidth
                            size="large"
                            startIcon={isLoading ? <CircularProgress size={20} /> : <MagnifyingGlassIcon className="h-5 w-5" />}
                            sx={{
                              backgroundColor: '#1f2937',
                              color: 'white',
                              fontWeight: 600,
                              py: 1.5,
                              textTransform: 'none',
                              '&:hover': {
                                backgroundColor: '#374151',
                              },
                              '&:disabled': {
                                backgroundColor: '#9ca3af',
                                color: '#f3f4f6'
                              }
                            }}
                          >
                            {isLoading ? 'Analyzing...' : 'Generate Lineage'}
                          </Button>
                        </Grid>
                      </Grid>
                    </TabPanel>

                    <TabPanel value={activeTab} index={1}>
                      <Box sx={{ display: 'flex', alignItems: 'center', mb: 3 }}>
                        <CubeIcon className="h-6 w-6" style={{ marginRight: 12, color: '#6b7280' }} />
                        <Typography variant="h6" fontWeight={600} sx={{ color: '#1f2937' }}>
                          Model Lineage Configuration
                        </Typography>
                      </Box>
                      
                      <Grid container spacing={3}>
                        <Grid item xs={12}>
                          <TextField
                            label="Model ID"
                            value={modelId}
                            onChange={(e) => setModelId(e.target.value)}
                            size="small"
                            fullWidth
                            placeholder="Enter semantic model identifier"
                          />
                        </Grid>
                        <Grid item xs={12}>
                          <Button
                            variant="contained"
                            onClick={handleModelLineage}
                            disabled={isLoading || !modelId}
                            fullWidth
                            size="large"
                            startIcon={isLoading ? <CircularProgress size={20} /> : <CubeIcon className="h-5 w-5" />}
                            sx={{
                              backgroundColor: '#1f2937',
                              color: 'white',
                              fontWeight: 600,
                              py: 1.5,
                              textTransform: 'none',
                              '&:hover': {
                                backgroundColor: '#374151',
                              },
                              '&:disabled': {
                                backgroundColor: '#9ca3af',
                                color: '#f3f4f6'
                              }
                            }}
                          >
                            {isLoading ? 'Analyzing...' : 'Generate Model Lineage'}
                          </Button>
                        </Grid>
                      </Grid>
                    </TabPanel>

                    <TabPanel value={activeTab} index={2}>
                      <Box sx={{ display: 'flex', alignItems: 'center', mb: 3 }}>
                        <ExclamationTriangleIcon className="h-6 w-6" style={{ marginRight: 12, color: '#6b7280' }} />
                        <Typography variant="h6" fontWeight={600} sx={{ color: '#1f2937' }}>
                          Impact Analysis
                        </Typography>
                      </Box>
                      
                      <Typography variant="body2" color="text.secondary" gutterBottom sx={{ mb: 3 }}>
                        Select a node in the visualization to analyze its downstream impact and dependencies.
                      </Typography>
                      
                      {selectedEntity ? (
                        <Box sx={{ mb: 3 }}>
                          <Alert severity="info" sx={{ mb: 2 }}>
                            <Typography variant="body2" fontWeight={500}>
                              Selected: {selectedEntity.name}
                            </Typography>
                            <Typography variant="caption">
                              {selectedEntity.type === 'TABLE' ? 
                                `${selectedEntity.catalog}.${selectedEntity.schema}` : 
                                'Semantic Model'
                              }
                            </Typography>
                          </Alert>
                          <Button
                            variant="contained"
                            onClick={handleImpactAnalysis}
                            disabled={impactMutation.isPending}
                            fullWidth
                            size="large"
                            startIcon={<ExclamationTriangleIcon className="h-5 w-5" />}
                            sx={{
                              backgroundColor: '#1f2937',
                              color: 'white',
                              fontWeight: 600,
                              py: 1.5,
                              textTransform: 'none',
                              '&:hover': {
                                backgroundColor: '#374151',
                              },
                              '&:disabled': {
                                backgroundColor: '#9ca3af',
                                color: '#f3f4f6'
                              }
                            }}
                          >
                            Analyze Impact
                          </Button>
                        </Box>
                      ) : (
                        <Box sx={{ 
                          textAlign: 'center', 
                          py: 4,
                          border: '2px dashed #e0e0e0',
                          borderRadius: 2,
                          backgroundColor: '#f9f9f9'
                        }}>
                          <InformationCircleIcon className="h-12 w-12" style={{ color: '#9ca3af', marginBottom: 8 }} />
                          <Typography variant="body2" color="text.secondary">
                            Click on any node in the visualization to begin impact analysis
                          </Typography>
                        </Box>
                      )}
                    </TabPanel>
                    </CardContent>
                  )}
                </Card>
              </Panel>

              {/* Modern Statistics Panel */}
              {(lineageData || modelLineageData) && (
                <Panel position="top-right">
                  <Card sx={{ 
                    minWidth: 240,
                    borderRadius: 2,
                    boxShadow: '0 4px 6px -1px rgba(0, 0, 0, 0.1)',
                    border: '1px solid #e5e7eb',
                    backgroundColor: 'white'
                  }}>
                    <CardContent sx={{ p: 3 }}>
                      <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
                        <ChartBarIcon className="h-5 w-5" style={{ marginRight: 8, color: '#6b7280' }} />
                        <Typography variant="h6" fontWeight={600} sx={{ color: '#1f2937' }}>
                          Lineage Statistics
                        </Typography>
                      </Box>
                      <Stack spacing={2}>
                        <Box sx={{ 
                          display: 'flex', 
                          justifyContent: 'space-between',
                          p: 2,
                          backgroundColor: '#f8fafc',
                          borderRadius: 2,
                          border: '1px solid #e2e8f0'
                        }}>
                          <Typography variant="body2" color="text.secondary">
                            Nodes
                          </Typography>
                          <Chip 
                            label={nodes.length} 
                            size="small" 
                            sx={{
                              backgroundColor: '#374151',
                              color: 'white'
                            }}
                          />
                        </Box>
                        <Box sx={{ 
                          display: 'flex', 
                          justifyContent: 'space-between',
                          p: 2,
                          backgroundColor: '#f8fafc',
                          borderRadius: 2,
                          border: '1px solid #e2e8f0'
                        }}>
                          <Typography variant="body2" color="text.secondary">
                            Relationships
                          </Typography>
                          <Chip 
                            label={edges.length} 
                            size="small" 
                            sx={{
                              backgroundColor: '#6b7280',
                              color: 'white'
                            }}
                          />
                        </Box>
                        <Box sx={{ 
                          display: 'flex', 
                          justifyContent: 'space-between',
                          p: 2,
                          backgroundColor: '#f8fafc',
                          borderRadius: 2,
                          border: '1px solid #e2e8f0'
                        }}>
                          <Typography variant="body2" color="text.secondary">
                            Query Time
                          </Typography>
                          <Chip 
                            label={`${(activeTab === 0 ? lineageData : modelLineageData)?.query_time_ms || 0}ms`} 
                            size="small" 
                            sx={{
                              backgroundColor: '#9ca3af',
                              color: 'white'
                            }}
                          />
                        </Box>
                      </Stack>
                    </CardContent>
                  </Card>
                </Panel>
              )}
            </LineageFlowContent>
          </ReactFlowProvider>

          {/* Error Display */}
          {currentError && (
            <Box sx={{ position: 'absolute', top: 16, left: '50%', transform: 'translateX(-50%)', zIndex: 1000 }}>
              <Alert severity="error" onClose={() => setError('')}>
                {currentError.toString()}
              </Alert>
            </Box>
          )}
        </Box>

        {/* Entity Details Sidebar */}
        <Drawer
          anchor="right"
          open={sidebarOpen}
          onClose={() => setSidebarOpen(false)}
          sx={{ '& .MuiDrawer-paper': { width: 400 } }}
        >
          <Box sx={{ p: 2 }}>
            <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
              <Typography variant="h6">Entity Details</Typography>
              <IconButton onClick={() => setSidebarOpen(false)}>
                <XMarkIcon className="h-5 w-5" />
              </IconButton>
            </Box>

            {selectedEntity && (
              <Stack spacing={2}>
                <Chip label={selectedEntity.type} color="primary" />
                
                <Accordion defaultExpanded>
                  <AccordionSummary>
                    <Typography variant="subtitle1">Basic Information</Typography>
                  </AccordionSummary>
                  <AccordionDetails>
                    <Stack spacing={1}>
                      <Box>
                        <Typography variant="body2" color="text.secondary">Name</Typography>
                        <Typography variant="body1">{selectedEntity.name}</Typography>
                      </Box>
                      {selectedEntity.catalog && (
                        <Box>
                          <Typography variant="body2" color="text.secondary">Location</Typography>
                          <Typography variant="body1">
                            {selectedEntity.catalog}.{selectedEntity.schema}
                          </Typography>
                        </Box>
                      )}
                      {selectedEntity.description && (
                        <Box>
                          <Typography variant="body2" color="text.secondary">Description</Typography>
                          <Typography variant="body1">{selectedEntity.description}</Typography>
                        </Box>
                      )}
                    </Stack>
                  </AccordionDetails>
                </Accordion>

                {selectedEntity.metadata && Object.keys(selectedEntity.metadata).length > 0 && (
                  <Accordion>
                    <AccordionSummary>
                      <Typography variant="subtitle1">Metadata</Typography>
                    </AccordionSummary>
                    <AccordionDetails>
                      <Stack spacing={1}>
                        {Object.entries(selectedEntity.metadata).map(([key, value]) => (
                          <Box key={key}>
                            <Typography variant="body2" color="text.secondary">{key}</Typography>
                            <Typography variant="body1">{String(value)}</Typography>
                          </Box>
                        ))}
                      </Stack>
                    </AccordionDetails>
                  </Accordion>
                )}

                <Button
                  variant="outlined"
                  onClick={handleImpactAnalysis}
                  disabled={impactMutation.isPending}
                  startIcon={<ExclamationTriangleIcon className="h-4 w-4" />}
                >
                  Analyze Impact
                </Button>
              </Stack>
            )}
          </Box>
        </Drawer>
      </Box>

      {/* Settings Dialog */}
      <Dialog open={settingsOpen} onClose={() => setSettingsOpen(false)} maxWidth="md" fullWidth>
        <DialogTitle>Visualization Settings</DialogTitle>
        <DialogContent>
          <Grid container spacing={3} sx={{ mt: 1 }}>
            <Grid item xs={12} md={6}>
              <FormControl fullWidth>
                <InputLabel>Layout Algorithm</InputLabel>
                <Select
                  value={layoutAlgorithm}
                  onChange={(e) => handleLayoutChange(e.target.value)}
                  label="Layout Algorithm"
                >
                  <MenuItem value="hierarchical">Hierarchical</MenuItem>
                  <MenuItem value="force">Force Directed</MenuItem>
                  <MenuItem value="circular">Circular</MenuItem>
                  <MenuItem value="tree">Tree</MenuItem>
                </Select>
              </FormControl>
            </Grid>
            <Grid item xs={12} md={6}>
              <FormControlLabel
                control={
                  <Switch
                    checked={includeColumns}
                    onChange={(e) => setIncludeColumns(e.target.checked)}
                  />
                }
                label="Include Column Lineage"
              />
            </Grid>
            <Grid item xs={12}>
              <Typography gutterBottom>Analysis Depth</Typography>
              <Slider
                value={depth}
                onChange={(_, value) => setDepth(value as number)}
                min={1}
                max={10}
                marks
                valueLabelDisplay="auto"
              />
            </Grid>
          </Grid>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setSettingsOpen(false)}>Close</Button>
        </DialogActions>
      </Dialog>

      {/* Export Dialog */}
      <Dialog open={exportDialogOpen} onClose={() => setExportDialogOpen(false)}>
        <DialogTitle>Export Lineage</DialogTitle>
        <DialogContent>
          <Stack spacing={2} sx={{ minWidth: 300, pt: 1 }}>
            <Button
              variant="outlined"
              onClick={() => handleExport('svg')}
              disabled={exportMutation.isPending}
            >
              Export as SVG
            </Button>
            <Button
              variant="outlined"
              onClick={() => handleExport('json')}
              disabled={exportMutation.isPending}
            >
              Export as JSON
            </Button>
            <Button
              variant="outlined"
              onClick={() => handleExport('dot')}
              disabled={exportMutation.isPending}
            >
              Export as DOT (Graphviz)
            </Button>
          </Stack>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setExportDialogOpen(false)}>Close</Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
};

export default LineageVisualization;
