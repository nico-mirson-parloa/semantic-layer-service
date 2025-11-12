import React, { useState, useMemo } from 'react';
import { useQuery } from '@tanstack/react-query';
import { getAllMetrics, getMetricCategories } from '../services/api';
import { 
  MagnifyingGlassIcon,
  ChartBarIcon,
  TagIcon,
  CubeIcon,
  CodeBracketIcon,
  ShareIcon,
  BookmarkIcon,
  ChartPieIcon,
  CalculatorIcon,
  TableCellsIcon,
  ArrowTrendingUpIcon,
  EyeIcon
} from '@heroicons/react/24/outline';
import {
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Paper,
  Chip,
  IconButton,
  Tooltip,
  Box,
  Typography
} from '@mui/material';

interface Metric {
  id: string;
  name: string;
  description?: string;
  type: string;
  category: string;
  model: string;
  measure?: string;
  sql?: string;
  created_by?: string;
  last_modified?: string;
  dimensions: string[];
  entities: string[];
}

function MetricsExplorerPage() {
  const [searchTerm, setSearchTerm] = useState('');
  const [selectedCategory, setSelectedCategory] = useState<string>('all');
  const [selectedMetric, setSelectedMetric] = useState<Metric | null>(null);
  const [isDetailModalOpen, setIsDetailModalOpen] = useState(false);

  const { data: allMetrics = [], isLoading } = useQuery({
    queryKey: ['metrics'],
    queryFn: getAllMetrics,
  });

  const { data: categoriesData } = useQuery({
    queryKey: ['metric-categories'],
    queryFn: getMetricCategories,
  });

  // Get categories from API
  const categories = useMemo(() => {
    if (categoriesData?.categories) {
      return ['all', ...categoriesData.categories];
    }
    return ['all'];
  }, [categoriesData]);

  // Filter metrics based on search and category
  const filteredMetrics = useMemo(() => {
    return allMetrics.filter((metric: Metric) => {
      const matchesSearch = searchTerm === '' || 
        metric.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
        metric.description?.toLowerCase().includes(searchTerm.toLowerCase()) ||
        metric.model.toLowerCase().includes(searchTerm.toLowerCase());
      
      const matchesCategory = selectedCategory === 'all' || metric.category === selectedCategory;
      
      return matchesSearch && matchesCategory;
    });
  }, [allMetrics, searchTerm, selectedCategory]);

  const openMetricDetail = (metric: Metric) => {
    setSelectedMetric(metric);
    setIsDetailModalOpen(true);
  };

  const getMetricTypeIcon = (type: string) => {
    switch (type) {
      case 'simple': return <CalculatorIcon className="h-4 w-4" />;
      case 'derived': return <ChartPieIcon className="h-4 w-4" />;
      case 'ratio': return <ArrowTrendingUpIcon className="h-4 w-4" />;
      default: return <ChartBarIcon className="h-4 w-4" />;
    }
  };

  const getMetricTypeColor = (type: string) => {
    switch (type) {
      case 'simple': return 'bg-blue-100 text-blue-800';
      case 'derived': return 'bg-purple-100 text-purple-800';
      case 'ratio': return 'bg-green-100 text-green-800';
      default: return 'bg-gray-100 text-gray-800';
    }
  };

  return (
    <div className="space-y-8">
      {/* Header */}
      <div className="text-center">
        <h1 className="text-4xl font-bold text-black tracking-tight">Metrics Explorer</h1>
        <p className="mt-4 text-lg text-gray-600 max-w-2xl mx-auto">
          Discover, explore, and understand all available metrics in your organization
        </p>
      </div>

      {/* Search and Filters */}
      <div className="bg-white border border-gray-300 rounded-xl p-6 shadow-sm">
        <div className="flex flex-col lg:flex-row gap-4">
          {/* Search Bar */}
          <div className="flex-1 relative">
            <div className="absolute inset-y-0 left-0 pl-4 flex items-center pointer-events-none">
              <MagnifyingGlassIcon className="h-5 w-5 text-gray-400" />
            </div>
            <input
              type="text"
              placeholder="Search metrics by name, description, or model..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="block w-full pl-12 pr-4 py-3 bg-gray-50 border border-gray-300 rounded-lg text-black placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-gray-500 focus:border-transparent transition-all duration-200"
            />
          </div>
          
          {/* Category Filter */}
          <div className="relative">
            <select
              value={selectedCategory}
              onChange={(e) => setSelectedCategory(e.target.value)}
              className="block w-full pl-4 pr-10 py-3 bg-gray-50 border border-gray-300 text-black focus:outline-none focus:ring-2 focus:ring-gray-500 focus:border-transparent rounded-lg transition-all duration-200"
            >
              {categories.map(category => (
                <option key={category} value={category} className="bg-white text-black">
                  {category === 'all' ? 'All Categories' : category}
                </option>
              ))}
            </select>
          </div>
        </div>

        {/* Stats */}
        <div className="mt-6 flex items-center justify-center space-x-8 text-sm">
          <div className="flex items-center text-gray-600">
            <ChartBarIcon className="h-4 w-4 mr-2" />
            <span className="font-medium">{filteredMetrics.length}</span>
            <span className="ml-1">metrics found</span>
          </div>
          <div className="flex items-center text-gray-600">
            <CubeIcon className="h-4 w-4 mr-2" />
            <span className="font-medium">{categories.length - 1}</span>
            <span className="ml-1">categories</span>
          </div>
        </div>
      </div>

      {/* Metrics Table */}
      {isLoading ? (
        <div className="text-center py-16">
          <div className="animate-spin rounded-full h-12 w-12 border-2 border-gray-300 border-t-gray-800 mx-auto"></div>
          <p className="mt-4 text-gray-600 text-lg">Loading metrics...</p>
        </div>
      ) : filteredMetrics.length > 0 ? (
        <TableContainer component={Paper} sx={{ maxHeight: 600, borderRadius: 3, border: '1px solid #e5e7eb' }}>
          <Table stickyHeader size="medium">
            <TableHead>
              <TableRow>
                <TableCell sx={{ fontWeight: 600, backgroundColor: '#f9fafb' }}>Metric Name</TableCell>
                <TableCell sx={{ fontWeight: 600, backgroundColor: '#f9fafb' }}>Type</TableCell>
                <TableCell sx={{ fontWeight: 600, backgroundColor: '#f9fafb' }}>Category</TableCell>
                <TableCell sx={{ fontWeight: 600, backgroundColor: '#f9fafb' }}>Model</TableCell>
                <TableCell sx={{ fontWeight: 600, backgroundColor: '#f9fafb', minWidth: 300 }}>Description</TableCell>
                <TableCell sx={{ fontWeight: 600, backgroundColor: '#f9fafb' }} align="center">Dimensions</TableCell>
                <TableCell sx={{ fontWeight: 600, backgroundColor: '#f9fafb' }}>Last Modified</TableCell>
                <TableCell sx={{ fontWeight: 600, backgroundColor: '#f9fafb' }} align="center">Actions</TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {filteredMetrics.map((metric: Metric) => (
                <TableRow
                  key={metric.id}
                  hover
                  sx={{
                    cursor: 'pointer',
                    '&:hover': {
                      backgroundColor: '#f9fafb',
                    }
                  }}
                >
                  <TableCell>
                    <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                      <Box className={`p-2 rounded-lg ${getMetricTypeColor(metric.type)}`}>
                        {getMetricTypeIcon(metric.type)}
                      </Box>
                      <Typography variant="body2" fontWeight={500}>
                        {metric.name}
                      </Typography>
                    </Box>
                  </TableCell>
                  <TableCell>
                    <Chip 
                      label={metric.type}
                      size="small"
                      className={getMetricTypeColor(metric.type)}
                      sx={{ fontSize: '0.75rem' }}
                    />
                  </TableCell>
                  <TableCell>
                    <Typography variant="body2">
                      {metric.category}
                    </Typography>
                  </TableCell>
                  <TableCell>
                    <Typography variant="body2">
                      {metric.model}
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
                        maxWidth: 400,
                      }}
                      title={metric.description || ''}
                    >
                      {metric.description || '-'}
                    </Typography>
                  </TableCell>
                  <TableCell align="center">
                    {metric.dimensions.length > 0 ? (
                      <Chip 
                        label={`${metric.dimensions.length}`}
                        size="small"
                        variant="outlined"
                        icon={<CubeIcon className="h-3 w-3" />}
                      />
                    ) : (
                      <Typography variant="body2" color="text.secondary">
                        0
                      </Typography>
                    )}
                  </TableCell>
                  <TableCell>
                    <Typography variant="body2" color="text.secondary">
                      {metric.last_modified ? 
                        new Date(metric.last_modified).toLocaleDateString() : 
                        '-'
                      }
                    </Typography>
                  </TableCell>
                  <TableCell align="center">
                    <Box sx={{ display: 'flex', gap: 0.5, justifyContent: 'center' }}>
                      <Tooltip title="View Details">
                        <IconButton
                          size="small"
                          onClick={(e) => {
                            e.stopPropagation();
                            openMetricDetail(metric);
                          }}
                        >
                          <EyeIcon className="h-4 w-4" />
                        </IconButton>
                      </Tooltip>
                      <Tooltip title="Query Metric">
                        <IconButton
                          size="small"
                          onClick={(e) => {
                            e.stopPropagation();
                            // Handle query action
                          }}
                        >
                          <CodeBracketIcon className="h-4 w-4" />
                        </IconButton>
                      </Tooltip>
                      <Tooltip title="Share">
                        <IconButton
                          size="small"
                          onClick={(e) => {
                            e.stopPropagation();
                            // Handle share action
                          }}
                        >
                          <ShareIcon className="h-4 w-4" />
                        </IconButton>
                      </Tooltip>
                    </Box>
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </TableContainer>
      ) : (
        <div className="text-center py-16 bg-white border border-gray-300 rounded-xl shadow-sm">
          <ChartBarIcon className="h-16 w-16 text-gray-400 mx-auto mb-6" />
          <h3 className="text-xl font-semibold text-black mb-3">No metrics found</h3>
          <p className="text-gray-600 mb-6 text-lg max-w-md mx-auto">
            {searchTerm || selectedCategory !== 'all' 
              ? "Try adjusting your search or filters"
              : "Create semantic models to see metrics here"
            }
          </p>
          {!searchTerm && selectedCategory === 'all' && (
            <button
              onClick={() => window.location.href = '/metric-builder'}
              className="inline-flex items-center px-6 py-3 bg-black hover:bg-gray-800 text-white font-medium rounded-lg transition-all duration-200"
            >
              Create Your First Metric
            </button>
          )}
        </div>
      )}

      {/* Metric Detail Modal */}
      {isDetailModalOpen && selectedMetric && (
        <div className="fixed inset-0 z-50 overflow-y-auto">
          <div className="flex items-center justify-center min-h-screen pt-4 px-4 pb-20 text-center sm:block sm:p-0">
            <div className="fixed inset-0 bg-black bg-opacity-50 transition-opacity backdrop-blur-sm" onClick={() => setIsDetailModalOpen(false)}></div>
            
            <div className="inline-block align-bottom bg-white border border-gray-300 rounded-xl px-6 pt-6 pb-6 text-left overflow-hidden shadow-2xl transform transition-all sm:my-8 sm:align-middle sm:max-w-3xl sm:w-full">
              <div className="sm:flex sm:items-start">
                <div className="mt-3 text-center sm:mt-0 sm:text-left w-full">
                  <div className="flex items-center justify-between mb-6">
                    <div className="flex items-center space-x-4">
                      <div className={`p-3 rounded-xl ${getMetricTypeColor(selectedMetric.type)}`}>
                        {getMetricTypeIcon(selectedMetric.type)}
                      </div>
                      <div>
                        <h3 className="text-2xl font-bold text-black">{selectedMetric.name}</h3>
                        <span className={`inline-flex items-center px-3 py-1 rounded-full text-sm font-medium mt-1 ${getMetricTypeColor(selectedMetric.type)}`}>
                          {selectedMetric.type} metric
                        </span>
                      </div>
                    </div>
                    <button
                      onClick={() => setIsDetailModalOpen(false)}
                      className="text-gray-500 hover:text-black transition-colors text-2xl"
                    >
                      ✕
                    </button>
                  </div>

                  {selectedMetric.description && (
                    <div className="mb-8">
                      <h4 className="text-lg font-semibold text-black mb-3">Description</h4>
                      <p className="text-gray-700 leading-relaxed">{selectedMetric.description}</p>
                    </div>
                  )}

                  <div className="grid grid-cols-1 lg:grid-cols-2 gap-8 mb-8">
                    <div className="bg-gray-50 border border-gray-200 rounded-lg p-4">
                      <h4 className="text-lg font-semibold text-black mb-4">Metadata</h4>
                      <dl className="space-y-3">
                        <div>
                          <dt className="text-gray-600 text-sm">Model</dt>
                          <dd className="text-black font-medium">{selectedMetric.model}</dd>
                        </div>
                        <div>
                          <dt className="text-gray-600 text-sm">Category</dt>
                          <dd className="text-black font-medium">{selectedMetric.category}</dd>
                        </div>
                        {selectedMetric.measure && (
                          <div>
                            <dt className="text-gray-600 text-sm">Base Measure</dt>
                            <dd className="text-black font-medium">{selectedMetric.measure}</dd>
                          </div>
                        )}
                      </dl>
                    </div>

                    <div className="bg-gray-50 border border-gray-200 rounded-lg p-4">
                      <h4 className="text-lg font-semibold text-black mb-4">Dimensions</h4>
                      {selectedMetric.dimensions.length > 0 ? (
                        <div className="flex flex-wrap gap-2">
                          {selectedMetric.dimensions.map((dim) => (
                            <span key={dim} className="inline-flex items-center px-3 py-1.5 rounded-lg text-sm bg-white text-gray-700 border border-gray-300">
                              {dim}
                            </span>
                          ))}
                        </div>
                      ) : (
                        <p className="text-gray-500">No dimensions available</p>
                      )}
                    </div>
                  </div>

                  {selectedMetric.sql && (
                    <div className="mb-8">
                      <h4 className="text-lg font-semibold text-black mb-3">SQL Definition</h4>
                      <pre className="text-sm bg-gray-50 border border-gray-200 text-gray-800 p-4 rounded-lg overflow-x-auto">
                        {selectedMetric.sql}
                      </pre>
                    </div>
                  )}

                  <div className="flex justify-end space-x-4">
                    <button
                      onClick={() => setIsDetailModalOpen(false)}
                      className="px-6 py-3 text-sm font-medium text-gray-700 bg-gray-100 border border-gray-300 rounded-lg hover:bg-gray-200 transition-all duration-200"
                    >
                      Close
                    </button>
                    <button className="px-6 py-3 text-sm font-medium text-white bg-black rounded-lg hover:bg-gray-800 transition-all duration-200">
                      Query Metric
                    </button>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

export default MetricsExplorerPage;
