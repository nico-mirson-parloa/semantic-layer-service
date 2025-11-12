/**
 * Tests for ModelDetailModal component
 */
import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import '@testing-library/jest-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import ModelDetailModal from '../../components/ModelDetailModal';

// Mock the API service
jest.mock('../../services/api', () => ({
  getSemanticModel: jest.fn(),
  updateSemanticModel: jest.fn(),
  deleteSemanticModel: jest.fn(),
}));

const mockApi = require('../../services/api');

describe('ModelDetailModal', () => {
  let queryClient: QueryClient;

  const mockModel = {
    id: 'test-model-id',
    name: 'sales_metrics',
    description: 'Test sales metrics model',
    model: 'main.gold.sales_fact',
    entities: [
      { name: 'order_id', type: 'primary', expr: 'order_id' },
      { name: 'customer_id', type: 'foreign', expr: 'customer_id' }
    ],
    dimensions: [
      { name: 'order_date', type: 'time', expr: 'order_date', time_granularity: ['day', 'month'] },
      { name: 'region', type: 'categorical', expr: 'customer_region' }
    ],
    measures: [
      { name: 'revenue', agg: 'sum', expr: 'order_amount', description: 'Total revenue' },
      { name: 'order_count', agg: 'count', expr: 'order_id', description: 'Number of orders' }
    ],
    metrics: [
      { name: 'total_revenue', type: 'simple', measure: 'revenue', description: 'Total revenue' },
      { name: 'avg_order_value', type: 'ratio', numerator: 'revenue', denominator: 'order_count', description: 'AOV' }
    ]
  };

  const defaultProps = {
    isOpen: true,
    onClose: jest.fn(),
    modelId: 'test-model-id'
  };

  beforeEach(() => {
    queryClient = new QueryClient({
      defaultOptions: {
        queries: { retry: false },
        mutations: { retry: false }
      }
    });
    jest.clearAllMocks();
  });

  const renderWithQueryClient = (props = {}) => {
    return render(
      <QueryClientProvider client={queryClient}>
        <ModelDetailModal {...defaultProps} {...props} />
      </QueryClientProvider>
    );
  };

  it('renders loading state initially', () => {
    mockApi.getSemanticModel.mockReturnValue(new Promise(() => {})); // Never resolves
    
    renderWithQueryClient();
    
    expect(screen.getByText(/loading/i)).toBeInTheDocument();
  });

  it('renders model details when loaded', async () => {
    mockApi.getSemanticModel.mockResolvedValue(mockModel);
    
    renderWithQueryClient();
    
    await waitFor(() => {
      expect(screen.getByText('sales_metrics')).toBeInTheDocument();
    });
    
    expect(screen.getByText('Test sales metrics model')).toBeInTheDocument();
    expect(screen.getByText('main.gold.sales_fact')).toBeInTheDocument();
  });

  it('displays entities section correctly', async () => {
    mockApi.getSemanticModel.mockResolvedValue(mockModel);
    
    renderWithQueryClient();
    
    await waitFor(() => {
      expect(screen.getByText('Entities')).toBeInTheDocument();
    });
    
    expect(screen.getByText('order_id')).toBeInTheDocument();
    expect(screen.getByText('customer_id')).toBeInTheDocument();
    expect(screen.getByText('primary')).toBeInTheDocument();
    expect(screen.getByText('foreign')).toBeInTheDocument();
  });

  it('displays dimensions section correctly', async () => {
    mockApi.getSemanticModel.mockResolvedValue(mockModel);
    
    renderWithQueryClient();
    
    await waitFor(() => {
      expect(screen.getByText('Dimensions')).toBeInTheDocument();
    });
    
    expect(screen.getByText('order_date')).toBeInTheDocument();
    expect(screen.getByText('region')).toBeInTheDocument();
    expect(screen.getByText('time')).toBeInTheDocument();
    expect(screen.getByText('categorical')).toBeInTheDocument();
  });

  it('displays measures section correctly', async () => {
    mockApi.getSemanticModel.mockResolvedValue(mockModel);
    
    renderWithQueryClient();
    
    await waitFor(() => {
      expect(screen.getByText('Measures')).toBeInTheDocument();
    });
    
    expect(screen.getByText('revenue')).toBeInTheDocument();
    expect(screen.getByText('order_count')).toBeInTheDocument();
    expect(screen.getByText('sum')).toBeInTheDocument();
    expect(screen.getByText('count')).toBeInTheDocument();
  });

  it('displays metrics section correctly', async () => {
    mockApi.getSemanticModel.mockResolvedValue(mockModel);
    
    renderWithQueryClient();
    
    await waitFor(() => {
      expect(screen.getByText('Metrics')).toBeInTheDocument();
    });
    
    expect(screen.getByText('total_revenue')).toBeInTheDocument();
    expect(screen.getByText('avg_order_value')).toBeInTheDocument();
    expect(screen.getByText('simple')).toBeInTheDocument();
    expect(screen.getByText('ratio')).toBeInTheDocument();
  });

  it('handles error state', async () => {
    mockApi.getSemanticModel.mockRejectedValue(new Error('Failed to load model'));
    
    renderWithQueryClient();
    
    await waitFor(() => {
      expect(screen.getByText(/error loading model/i)).toBeInTheDocument();
    });
  });

  it('closes modal when close button is clicked', async () => {
    mockApi.getSemanticModel.mockResolvedValue(mockModel);
    const onClose = jest.fn();
    
    renderWithQueryClient({ onClose });
    
    await waitFor(() => {
      expect(screen.getByText('sales_metrics')).toBeInTheDocument();
    });
    
    const closeButton = screen.getByRole('button', { name: /close/i });
    fireEvent.click(closeButton);
    
    expect(onClose).toHaveBeenCalledTimes(1);
  });

  it('closes modal when clicking outside', async () => {
    mockApi.getSemanticModel.mockResolvedValue(mockModel);
    const onClose = jest.fn();
    
    renderWithQueryClient({ onClose });
    
    await waitFor(() => {
      expect(screen.getByText('sales_metrics')).toBeInTheDocument();
    });
    
    // Click on backdrop
    const backdrop = screen.getByTestId('modal-backdrop');
    fireEvent.click(backdrop);
    
    expect(onClose).toHaveBeenCalledTimes(1);
  });

  it('shows edit mode when edit button is clicked', async () => {
    mockApi.getSemanticModel.mockResolvedValue(mockModel);
    
    renderWithQueryClient();
    
    await waitFor(() => {
      expect(screen.getByText('sales_metrics')).toBeInTheDocument();
    });
    
    const editButton = screen.getByRole('button', { name: /edit/i });
    fireEvent.click(editButton);
    
    expect(screen.getByDisplayValue('sales_metrics')).toBeInTheDocument();
    expect(screen.getByDisplayValue('Test sales metrics model')).toBeInTheDocument();
  });

  it('saves changes when save button is clicked', async () => {
    mockApi.getSemanticModel.mockResolvedValue(mockModel);
    mockApi.updateSemanticModel.mockResolvedValue({ ...mockModel, description: 'Updated description' });
    
    renderWithQueryClient();
    
    await waitFor(() => {
      expect(screen.getByText('sales_metrics')).toBeInTheDocument();
    });
    
    // Enter edit mode
    fireEvent.click(screen.getByRole('button', { name: /edit/i }));
    
    // Change description
    const descriptionInput = screen.getByDisplayValue('Test sales metrics model');
    fireEvent.change(descriptionInput, { target: { value: 'Updated description' } });
    
    // Save changes
    fireEvent.click(screen.getByRole('button', { name: /save/i }));
    
    await waitFor(() => {
      expect(mockApi.updateSemanticModel).toHaveBeenCalledWith('test-model-id', {
        ...mockModel,
        description: 'Updated description'
      });
    });
  });

  it('cancels edit mode when cancel button is clicked', async () => {
    mockApi.getSemanticModel.mockResolvedValue(mockModel);
    
    renderWithQueryClient();
    
    await waitFor(() => {
      expect(screen.getByText('sales_metrics')).toBeInTheDocument();
    });
    
    // Enter edit mode
    fireEvent.click(screen.getByRole('button', { name: /edit/i }));
    
    // Change description
    const descriptionInput = screen.getByDisplayValue('Test sales metrics model');
    fireEvent.change(descriptionInput, { target: { value: 'Changed description' } });
    
    // Cancel changes
    fireEvent.click(screen.getByRole('button', { name: /cancel/i }));
    
    // Should be back to read mode with original description
    expect(screen.getByText('Test sales metrics model')).toBeInTheDocument();
    expect(screen.queryByDisplayValue('Changed description')).not.toBeInTheDocument();
  });

  it('deletes model when delete button is clicked and confirmed', async () => {
    mockApi.getSemanticModel.mockResolvedValue(mockModel);
    mockApi.deleteSemanticModel.mockResolvedValue(true);
    window.confirm = jest.fn(() => true);
    
    const onClose = jest.fn();
    renderWithQueryClient({ onClose });
    
    await waitFor(() => {
      expect(screen.getByText('sales_metrics')).toBeInTheDocument();
    });
    
    fireEvent.click(screen.getByRole('button', { name: /delete/i }));
    
    await waitFor(() => {
      expect(mockApi.deleteSemanticModel).toHaveBeenCalledWith('test-model-id');
      expect(onClose).toHaveBeenCalledTimes(1);
    });
  });

  it('does not delete model when deletion is cancelled', async () => {
    mockApi.getSemanticModel.mockResolvedValue(mockModel);
    window.confirm = jest.fn(() => false);
    
    renderWithQueryClient();
    
    await waitFor(() => {
      expect(screen.getByText('sales_metrics')).toBeInTheDocument();
    });
    
    fireEvent.click(screen.getByRole('button', { name: /delete/i }));
    
    expect(mockApi.deleteSemanticModel).not.toHaveBeenCalled();
  });
});