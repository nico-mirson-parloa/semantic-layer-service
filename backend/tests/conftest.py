"""Test configuration and fixtures for semantic layer service tests."""

import pytest
import os
from unittest.mock import Mock, patch
from fastapi.testclient import TestClient
from app.main import app
from app.core.config import settings


@pytest.fixture
def client():
    """Create a test client for the FastAPI application."""
    with TestClient(app) as c:
        yield c


@pytest.fixture
def mock_databricks_connection():
    """Mock Databricks connection for testing."""
    with patch('app.integrations.databricks.get_databricks_connection') as mock:
        mock_conn = Mock()
        mock_cursor = Mock()
        mock_conn.cursor.return_value = mock_cursor
        mock.return_value = mock_conn
        yield mock_conn, mock_cursor


@pytest.fixture
def sample_table_metadata():
    """Sample table metadata for testing."""
    return [
        {
            'catalog_name': 'main',
            'schema_name': 'gold',
            'table_name': 'sales_fact',
            'table_type': 'TABLE',
            'data_source_format': 'DELTA',
            'columns': [
                {'column_name': 'order_id', 'data_type': 'bigint', 'is_nullable': False},
                {'column_name': 'customer_id', 'data_type': 'bigint', 'is_nullable': False},
                {'column_name': 'product_id', 'data_type': 'bigint', 'is_nullable': False},
                {'column_name': 'order_date', 'data_type': 'date', 'is_nullable': False},
                {'column_name': 'order_amount', 'data_type': 'decimal(10,2)', 'is_nullable': False},
                {'column_name': 'quantity', 'data_type': 'int', 'is_nullable': False},
                {'column_name': 'customer_region', 'data_type': 'string', 'is_nullable': True},
                {'column_name': 'product_category', 'data_type': 'string', 'is_nullable': True}
            ]
        }
    ]


@pytest.fixture
def sample_semantic_model():
    """Sample semantic model definition for testing."""
    return {
        'name': 'test_sales_metrics',
        'description': 'Test sales metrics model',
        'model': 'main.gold.sales_fact',
        'entities': [
            {'name': 'order_id', 'type': 'primary', 'expr': 'order_id'},
            {'name': 'customer_id', 'type': 'foreign', 'expr': 'customer_id'},
            {'name': 'product_id', 'type': 'foreign', 'expr': 'product_id'}
        ],
        'dimensions': [
            {
                'name': 'order_date',
                'type': 'time',
                'expr': 'order_date',
                'time_granularity': ['day', 'week', 'month']
            },
            {
                'name': 'customer_region',
                'type': 'categorical',
                'expr': 'customer_region'
            }
        ],
        'measures': [
            {
                'name': 'revenue',
                'agg': 'sum',
                'expr': 'order_amount',
                'description': 'Total revenue'
            },
            {
                'name': 'order_count',
                'agg': 'count',
                'expr': 'order_id',
                'description': 'Number of orders'
            }
        ],
        'metrics': [
            {
                'name': 'total_revenue',
                'type': 'simple',
                'measure': 'revenue',
                'description': 'Total revenue across all orders'
            },
            {
                'name': 'average_order_value',
                'type': 'ratio',
                'numerator': 'revenue',
                'denominator': 'order_count',
                'description': 'Average revenue per order'
            }
        ]
    }


@pytest.fixture
def mock_genie_response():
    """Mock Databricks Genie API response."""
    return {
        'statement_id': 'test-statement-123',
        'status': {
            'state': 'SUCCEEDED'
        },
        'result': {
            'data_array': [
                ['SELECT', 'SUM(order_amount) as total_revenue', 'FROM main.gold.sales_fact'],
                ['WHERE', 'order_date >= "2024-01-01"', '']
            ]
        },
        'manifest': {
            'schema': {
                'columns': [
                    {'name': 'query_type', 'type_name': 'STRING'},
                    {'name': 'sql_fragment', 'type_name': 'STRING'},
                    {'name': 'condition', 'type_name': 'STRING'}
                ]
            }
        }
    }


@pytest.fixture(autouse=True)
def setup_test_environment():
    """Setup test environment variables."""
    test_env = {
        'DATABRICKS_HOST': 'test-workspace.databricks.com',
        'DATABRICKS_TOKEN': 'test-token',
        'DATABRICKS_HTTP_PATH': '/sql/1.0/warehouses/test',
        'DATABRICKS_GENIE_SPACE_ID': 'test-space-id'
    }
    
    with patch.dict(os.environ, test_env):
        yield