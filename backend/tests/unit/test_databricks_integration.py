"""Tests for Databricks integration functionality."""

import pytest
from unittest.mock import Mock, patch, MagicMock
from app.integrations.databricks import DatabricksClient
from app.integrations.databricks_genie import DatabricksGenieClient
from databricks import sql
import requests


class TestDatabricksClient:
    """Test cases for DatabricksClient."""

    def test_get_connection_success(self, mock_databricks_connection):
        """Test successful database connection."""
        mock_conn, _ = mock_databricks_connection
        client = DatabricksClient()
        
        connection = client.get_connection()
        
        assert connection is not None
        assert connection == mock_conn

    @patch('databricks.sql.connect')
    def test_get_connection_failure(self, mock_connect):
        """Test database connection failure."""
        mock_connect.side_effect = Exception("Connection failed")
        client = DatabricksClient()
        
        with pytest.raises(Exception, match="Connection failed"):
            client.get_connection()

    def test_get_tables_metadata(self, mock_databricks_connection, sample_table_metadata):
        """Test fetching table metadata."""
        mock_conn, mock_cursor = mock_databricks_connection
        mock_cursor.fetchall.return_value = [
            ('main', 'gold', 'sales_fact', 'TABLE', 'DELTA')
        ]
        
        client = DatabricksClient()
        tables = client.get_tables_metadata('main', 'gold')
        
        assert len(tables) > 0
        mock_cursor.execute.assert_called_once()

    def test_get_table_columns(self, mock_databricks_connection):
        """Test fetching table column information."""
        mock_conn, mock_cursor = mock_databricks_connection
        mock_cursor.fetchall.return_value = [
            ('order_id', 'bigint', False),
            ('customer_id', 'bigint', False),
            ('order_amount', 'decimal(10,2)', False)
        ]
        
        client = DatabricksClient()
        columns = client.get_table_columns('main.gold.sales_fact')
        
        assert len(columns) == 3
        assert columns[0]['column_name'] == 'order_id'
        assert columns[0]['data_type'] == 'bigint'

    def test_execute_query(self, mock_databricks_connection):
        """Test query execution."""
        mock_conn, mock_cursor = mock_databricks_connection
        mock_cursor.fetchall.return_value = [
            (1000.50, 'Electronics'),
            (750.25, 'Books')
        ]
        mock_cursor.description = [
            ('revenue', 'decimal'),
            ('category', 'string')
        ]
        
        client = DatabricksClient()
        result = client.execute_query("SELECT SUM(amount) as revenue, category FROM sales GROUP BY category")
        
        assert len(result['data']) == 2
        assert result['columns'] == ['revenue', 'category']
        assert result['data'][0] == [1000.50, 'Electronics']

    def test_execute_query_failure(self, mock_databricks_connection):
        """Test query execution failure."""
        mock_conn, mock_cursor = mock_databricks_connection
        mock_cursor.execute.side_effect = Exception("Query failed")
        
        client = DatabricksClient()
        
        with pytest.raises(Exception, match="Query failed"):
            client.execute_query("SELECT * FROM invalid_table")


class TestDatabricksGenieClient:
    """Test cases for DatabricksGenieClient."""

    @patch('requests.post')
    def test_create_conversation_success(self, mock_post):
        """Test successful conversation creation."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'id': 'conv-123',
            'title': 'Test Conversation'
        }
        mock_post.return_value = mock_response
        
        client = DatabricksGenieClient()
        conversation = client.create_conversation("Test message")
        
        assert conversation['id'] == 'conv-123'
        assert conversation['title'] == 'Test Conversation'

    @patch('requests.post')
    def test_create_conversation_failure(self, mock_post):
        """Test conversation creation failure."""
        mock_response = Mock()
        mock_response.status_code = 400
        mock_response.text = "Bad Request"
        mock_post.return_value = mock_response
        
        client = DatabricksGenieClient()
        
        with pytest.raises(requests.HTTPError):
            client.create_conversation("Test message")

    @patch('requests.post')
    def test_send_message_success(self, mock_post, mock_genie_response):
        """Test successful message sending."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = mock_genie_response
        mock_post.return_value = mock_response
        
        client = DatabricksGenieClient()
        response = client.send_message("conv-123", "Show me total revenue")
        
        assert response['statement_id'] == 'test-statement-123'
        assert response['status']['state'] == 'SUCCEEDED'

    @patch('requests.get')
    def test_get_statement_result_success(self, mock_get, mock_genie_response):
        """Test successful statement result retrieval."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = mock_genie_response
        mock_get.return_value = mock_response
        
        client = DatabricksGenieClient()
        result = client.get_statement_result('test-statement-123')
        
        assert result['status']['state'] == 'SUCCEEDED'
        assert 'result' in result

    def test_extract_sql_from_response(self, mock_genie_response):
        """Test SQL extraction from Genie response."""
        client = DatabricksGenieClient()
        sql_query = client.extract_sql_from_response(mock_genie_response)
        
        assert 'SELECT' in sql_query
        assert 'SUM(order_amount)' in sql_query
        assert 'FROM main.gold.sales_fact' in sql_query

    def test_extract_sql_from_empty_response(self):
        """Test SQL extraction from empty response."""
        client = DatabricksGenieClient()
        empty_response = {'result': {'data_array': []}}
        
        sql_query = client.extract_sql_from_response(empty_response)
        
        assert sql_query == ""

    @patch('time.sleep')
    @patch('requests.get')
    def test_wait_for_completion_success(self, mock_get, mock_sleep):
        """Test waiting for statement completion."""
        # First call returns RUNNING, second returns SUCCEEDED
        mock_responses = [
            Mock(status_code=200, json=lambda: {'status': {'state': 'RUNNING'}}),
            Mock(status_code=200, json=lambda: {'status': {'state': 'SUCCEEDED'}})
        ]
        mock_get.side_effect = mock_responses
        
        client = DatabricksGenieClient()
        result = client.wait_for_completion('test-statement-123')
        
        assert result['status']['state'] == 'SUCCEEDED'
        assert mock_get.call_count == 2

    @patch('time.sleep')
    @patch('requests.get')
    def test_wait_for_completion_timeout(self, mock_get, mock_sleep):
        """Test waiting for statement completion with timeout."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {'status': {'state': 'RUNNING'}}
        mock_get.return_value = mock_response
        
        client = DatabricksGenieClient()
        
        with pytest.raises(TimeoutError, match="Statement execution timed out"):
            client.wait_for_completion('test-statement-123', max_wait=1)