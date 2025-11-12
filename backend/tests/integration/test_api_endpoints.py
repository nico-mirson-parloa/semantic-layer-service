"""Integration tests for API endpoints."""

import pytest
import json
from fastapi.testclient import TestClient
from unittest.mock import patch, Mock


class TestHealthEndpoint:
    """Test cases for health check endpoint."""

    def test_health_check(self, client):
        """Test basic health check endpoint."""
        response = client.get("/api/v1/health")
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "timestamp" in data


class TestMetadataEndpoints:
    """Test cases for metadata API endpoints."""

    def test_get_catalogs(self, client, mock_databricks_connection):
        """Test getting available catalogs."""
        mock_conn, mock_cursor = mock_databricks_connection
        mock_cursor.fetchall.return_value = [("main",), ("hive_metastore",)]
        
        response = client.get("/api/v1/metadata/catalogs")
        
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2
        assert "main" in data
        assert "hive_metastore" in data

    def test_get_schemas(self, client, mock_databricks_connection):
        """Test getting schemas for a catalog."""
        mock_conn, mock_cursor = mock_databricks_connection
        mock_cursor.fetchall.return_value = [("bronze",), ("silver",), ("gold",)]
        
        response = client.get("/api/v1/metadata/catalogs/main/schemas")
        
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 3
        assert "gold" in data

    def test_get_tables(self, client, mock_databricks_connection):
        """Test getting tables for a schema."""
        mock_conn, mock_cursor = mock_databricks_connection
        mock_cursor.fetchall.return_value = [
            ("main", "gold", "sales_fact", "TABLE", "DELTA"),
            ("main", "gold", "customers_dim", "TABLE", "DELTA")
        ]
        
        response = client.get("/api/v1/metadata/catalogs/main/schemas/gold/tables")
        
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2
        assert any(table["table_name"] == "sales_fact" for table in data)

    def test_get_table_columns(self, client, mock_databricks_connection):
        """Test getting columns for a table."""
        mock_conn, mock_cursor = mock_databricks_connection
        mock_cursor.fetchall.return_value = [
            ("order_id", "bigint", False, "Order identifier"),
            ("order_date", "date", False, "Order date"),
            ("amount", "decimal(10,2)", False, "Order amount")
        ]
        
        response = client.get("/api/v1/metadata/tables/main.gold.sales_fact/columns")
        
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 3
        assert data[0]["column_name"] == "order_id"
        assert data[0]["data_type"] == "bigint"


class TestSemanticModelEndpoints:
    """Test cases for semantic model API endpoints."""

    def test_create_semantic_model(self, client, sample_semantic_model):
        """Test creating a new semantic model."""
        with patch('app.services.semantic_parser.SemanticModelParser.parse_yaml') as mock_parse:
            mock_parse.return_value = Mock(name="test_model")
            
            response = client.post(
                "/api/v1/models",
                json=sample_semantic_model
            )
            
            assert response.status_code == 201
            data = response.json()
            assert "id" in data
            assert data["name"] == sample_semantic_model["name"]

    def test_list_semantic_models(self, client):
        """Test listing all semantic models."""
        with patch('app.api.models.get_all_models') as mock_get_all:
            mock_models = [
                {"id": "1", "name": "sales_metrics", "description": "Sales metrics"},
                {"id": "2", "name": "customer_metrics", "description": "Customer metrics"}
            ]
            mock_get_all.return_value = mock_models
            
            response = client.get("/api/v1/models")
            
            assert response.status_code == 200
            data = response.json()
            assert len(data) == 2
            assert data[0]["name"] == "sales_metrics"

    def test_get_semantic_model_by_id(self, client, sample_semantic_model):
        """Test getting a specific semantic model."""
        with patch('app.api.models.get_model_by_id') as mock_get:
            mock_get.return_value = sample_semantic_model
            
            response = client.get("/api/v1/models/test-model-id")
            
            assert response.status_code == 200
            data = response.json()
            assert data["name"] == sample_semantic_model["name"]

    def test_get_nonexistent_model(self, client):
        """Test getting a non-existent semantic model."""
        with patch('app.api.models.get_model_by_id') as mock_get:
            mock_get.return_value = None
            
            response = client.get("/api/v1/models/nonexistent-id")
            
            assert response.status_code == 404

    def test_update_semantic_model(self, client, sample_semantic_model):
        """Test updating a semantic model."""
        updated_model = sample_semantic_model.copy()
        updated_model["description"] = "Updated description"
        
        with patch('app.api.models.update_model') as mock_update:
            mock_update.return_value = updated_model
            
            response = client.put(
                "/api/v1/models/test-model-id",
                json=updated_model
            )
            
            assert response.status_code == 200
            data = response.json()
            assert data["description"] == "Updated description"

    def test_delete_semantic_model(self, client):
        """Test deleting a semantic model."""
        with patch('app.api.models.delete_model') as mock_delete:
            mock_delete.return_value = True
            
            response = client.delete("/api/v1/models/test-model-id")
            
            assert response.status_code == 204


class TestQueryEndpoints:
    """Test cases for query execution endpoints."""

    def test_execute_query(self, client, mock_databricks_connection):
        """Test query execution."""
        mock_conn, mock_cursor = mock_databricks_connection
        mock_cursor.fetchall.return_value = [
            ("2024-01-01", 1500.50, 12),
            ("2024-01-02", 2300.75, 18)
        ]
        mock_cursor.description = [
            ("order_date", "date"),
            ("total_revenue", "decimal"),
            ("order_count", "bigint")
        ]
        
        query_request = {
            "metrics": ["total_revenue", "order_count"],
            "dimensions": ["order_date"],
            "filters": {"order_date": {">=": "2024-01-01"}},
            "limit": 100
        }
        
        response = client.post("/api/v1/queries/execute", json=query_request)
        
        assert response.status_code == 200
        data = response.json()
        assert len(data["columns"]) == 3
        assert len(data["data"]) == 2
        assert data["row_count"] == 2

    def test_execute_invalid_query(self, client):
        """Test query execution with invalid request."""
        invalid_request = {
            "metrics": [],  # Invalid: empty metrics
            "dimensions": ["order_date"]
        }
        
        response = client.post("/api/v1/queries/execute", json=invalid_request)
        
        assert response.status_code == 422

    def test_get_query_history(self, client):
        """Test getting query execution history."""
        with patch('app.api.queries.get_user_query_history') as mock_history:
            mock_history.return_value = [
                {
                    "id": "query-1",
                    "sql": "SELECT COUNT(*) FROM sales",
                    "executed_at": "2024-01-01T10:00:00Z",
                    "execution_time": 0.5
                }
            ]
            
            response = client.get("/api/v1/queries/history")
            
            assert response.status_code == 200
            data = response.json()
            assert len(data) == 1
            assert data[0]["id"] == "query-1"


class TestGenieEndpoints:
    """Test cases for Databricks Genie integration endpoints."""

    @patch('app.integrations.databricks_genie.DatabricksGenieClient.create_conversation')
    @patch('app.integrations.databricks_genie.DatabricksGenieClient.send_message')
    def test_natural_language_query(self, mock_send, mock_create, client, mock_genie_response):
        """Test natural language query processing."""
        mock_create.return_value = {"id": "conv-123"}
        mock_send.return_value = mock_genie_response
        
        request = {
            "message": "Show me total revenue by product category",
            "context": "sales analytics"
        }
        
        response = client.post("/api/v1/genie/query", json=request)
        
        assert response.status_code == 200
        data = response.json()
        assert "sql" in data
        assert "conversation_id" in data

    @patch('app.integrations.databricks_genie.DatabricksGenieClient.get_statement_result')
    def test_get_sql_logic(self, mock_get_result, client, mock_genie_response):
        """Test SQL logic extraction endpoint."""
        mock_get_result.return_value = mock_genie_response
        
        request = {
            "question": "What was the total revenue last month?",
            "return_sql_only": True
        }
        
        response = client.post("/api/v1/genie/get-sql-logic", json=request)
        
        assert response.status_code == 200
        data = response.json()
        assert "sql" in data
        assert "reasoning" in data