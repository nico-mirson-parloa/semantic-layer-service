"""
Comprehensive unit tests for automatic model generation from gold layer tables.
Tests follow TDD approach - written before implementation.
"""
import pytest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime
from typing import List, Dict, Any

from app.services.table_analyzer import TableAnalyzer
from app.services.metric_suggester import MetricSuggester
from app.services.model_generator import ModelGenerator
from app.models.catalog import TableSchema, ColumnInfo
from app.models.semantic import GeneratedModel, SuggestedMetric, SuggestedDimension


class TestTableAnalyzer:
    """Test cases for TableAnalyzer service"""
    
    @pytest.fixture
    def mock_databricks_client(self):
        """Mock Databricks client for testing"""
        client = Mock()
        return client
    
    @pytest.fixture
    def table_analyzer(self, mock_databricks_client):
        """Create TableAnalyzer instance with mocked client"""
        return TableAnalyzer(client=mock_databricks_client)
    
    @pytest.fixture
    def sample_sales_schema(self):
        """Sample gold layer sales fact table schema"""
        return TableSchema(
            catalog="main",
            schema="gold",
            table="sales_fact",
            columns=[
                ColumnInfo(
                    name="order_id",
                    data_type="BIGINT",
                    nullable=False,
                    comment="Unique order identifier",
                    is_primary_key=True
                ),
                ColumnInfo(
                    name="customer_id",
                    data_type="BIGINT",
                    nullable=False,
                    comment="Customer identifier",
                    is_foreign_key=True,
                    foreign_key_table="gold.customers"
                ),
                ColumnInfo(
                    name="product_id",
                    data_type="BIGINT",
                    nullable=False,
                    comment="Product identifier",
                    is_foreign_key=True,
                    foreign_key_table="gold.products"
                ),
                ColumnInfo(
                    name="order_date",
                    data_type="DATE",
                    nullable=False,
                    comment="Date when order was placed"
                ),
                ColumnInfo(
                    name="ship_date",
                    data_type="DATE",
                    nullable=True,
                    comment="Date when order was shipped"
                ),
                ColumnInfo(
                    name="quantity",
                    data_type="INT",
                    nullable=False,
                    comment="Number of items ordered"
                ),
                ColumnInfo(
                    name="unit_price",
                    data_type="DECIMAL(10,2)",
                    nullable=False,
                    comment="Price per unit"
                ),
                ColumnInfo(
                    name="discount_amount",
                    data_type="DECIMAL(10,2)",
                    nullable=True,
                    comment="Discount applied to order",
                    default_value="0.00"
                ),
                ColumnInfo(
                    name="revenue",
                    data_type="DECIMAL(10,2)",
                    nullable=False,
                    comment="Total revenue (quantity * unit_price - discount)"
                ),
                ColumnInfo(
                    name="region",
                    data_type="STRING",
                    nullable=False,
                    comment="Sales region"
                ),
                ColumnInfo(
                    name="sales_channel",
                    data_type="STRING",
                    nullable=False,
                    comment="Channel through which sale was made (Online, Store, Phone)"
                ),
                ColumnInfo(
                    name="is_returned",
                    data_type="BOOLEAN",
                    nullable=False,
                    comment="Whether the order was returned",
                    default_value="false"
                ),
                ColumnInfo(
                    name="created_at",
                    data_type="TIMESTAMP",
                    nullable=False,
                    comment="Timestamp when record was created"
                ),
                ColumnInfo(
                    name="updated_at",
                    data_type="TIMESTAMP",
                    nullable=False,
                    comment="Timestamp when record was last updated"
                )
            ],
            table_comment="Gold layer fact table containing all sales transactions",
            table_properties={
                "delta.autoOptimize.optimizeWrite": "true",
                "delta.autoOptimize.autoCompact": "true"
            },
            statistics={
                "numRows": 1000000,
                "sizeInBytes": 524288000,
                "lastModified": datetime.now()
            }
        )
    
    def test_analyze_table_schema(self, table_analyzer, sample_sales_schema):
        """Test basic table schema analysis"""
        analysis = table_analyzer.analyze_table(sample_sales_schema)
        
        assert analysis.table_name == "sales_fact"
        assert analysis.row_count == 1000000
        assert len(analysis.columns) == 14
        assert analysis.has_primary_key is True
        assert len(analysis.foreign_keys) == 2
        assert analysis.table_type == "fact"  # Detected from name pattern
    
    def test_detect_column_patterns(self, table_analyzer, sample_sales_schema):
        """Test column pattern detection for metric/dimension suggestions"""
        patterns = table_analyzer.detect_column_patterns(sample_sales_schema)
        
        # Numeric columns that could be metrics
        assert "revenue" in patterns.numeric_columns
        assert "quantity" in patterns.numeric_columns
        assert "unit_price" in patterns.numeric_columns
        assert "discount_amount" in patterns.numeric_columns
        
        # ID columns (should not be suggested as metrics)
        assert "order_id" in patterns.id_columns
        assert "customer_id" in patterns.id_columns
        assert "product_id" in patterns.id_columns
        
        # Date/time columns for time dimensions
        assert "order_date" in patterns.date_columns
        assert "ship_date" in patterns.date_columns
        assert "created_at" in patterns.timestamp_columns
        
        # Categorical columns for dimensions
        assert "region" in patterns.categorical_columns
        assert "sales_channel" in patterns.categorical_columns
        
        # Boolean columns for filters
        assert "is_returned" in patterns.boolean_columns
    
    def test_analyze_column_statistics(self, table_analyzer, mock_databricks_client):
        """Test column statistics analysis for better suggestions"""
        # Mock column statistics query
        mock_databricks_client.execute_query.return_value = [
            {"column_name": "revenue", "min_value": 0, "max_value": 10000, 
             "null_count": 0, "distinct_count": 8500, "avg_value": 150.50},
            {"column_name": "region", "min_value": None, "max_value": None,
             "null_count": 0, "distinct_count": 5, "top_values": ["North", "South", "East", "West", "Central"]},
            {"column_name": "is_returned", "min_value": None, "max_value": None,
             "null_count": 0, "distinct_count": 2, "true_count": 50000, "false_count": 950000}
        ]
        
        stats = table_analyzer.analyze_column_statistics("main.gold.sales_fact")
        
        assert stats["revenue"]["avg_value"] == 150.50
        assert stats["revenue"]["distinct_count"] == 8500
        assert stats["region"]["distinct_count"] == 5
        assert stats["is_returned"]["return_rate"] == 0.05  # 5% return rate
    
    def test_detect_relationships(self, table_analyzer, mock_databricks_client):
        """Test foreign key relationship detection"""
        # Mock information schema query for relationships
        mock_databricks_client.execute_query.return_value = [
            {"constraint_name": "fk_customer", "column_name": "customer_id", 
             "referenced_table": "gold.customers", "referenced_column": "customer_id"},
            {"constraint_name": "fk_product", "column_name": "product_id",
             "referenced_table": "gold.products", "referenced_column": "product_id"}
        ]
        
        relationships = table_analyzer.detect_relationships("main.gold.sales_fact")
        
        assert len(relationships) == 2
        assert relationships[0].from_column == "customer_id"
        assert relationships[0].to_table == "gold.customers"
        assert relationships[1].from_column == "product_id"
        assert relationships[1].to_table == "gold.products"


class TestMetricSuggester:
    """Test cases for MetricSuggester service"""
    
    @pytest.fixture
    def metric_suggester(self):
        """Create MetricSuggester instance"""
        return MetricSuggester()
    
    @pytest.fixture
    def analyzed_table(self):
        """Sample analyzed table data"""
        return {
            "table_name": "sales_fact",
            "columns": {
                "revenue": {"data_type": "DECIMAL", "pattern": "metric", "avg_value": 150.50},
                "quantity": {"data_type": "INT", "pattern": "metric", "avg_value": 3.2},
                "discount_amount": {"data_type": "DECIMAL", "pattern": "metric", "avg_value": 5.75},
                "order_date": {"data_type": "DATE", "pattern": "time_dimension"},
                "region": {"data_type": "STRING", "pattern": "dimension", "distinct_values": 5},
                "is_returned": {"data_type": "BOOLEAN", "pattern": "filter"},
                "order_id": {"data_type": "BIGINT", "pattern": "identifier"}
            },
            "table_type": "fact"
        }
    
    def test_suggest_basic_metrics(self, metric_suggester, analyzed_table):
        """Test basic metric suggestions from numeric columns"""
        suggestions = metric_suggester.suggest_metrics(analyzed_table)
        
        # Should suggest sum metrics for revenue and quantity
        revenue_metrics = [m for m in suggestions if m.base_column == "revenue"]
        assert len(revenue_metrics) >= 1
        assert any(m.aggregation == "sum" and m.name == "total_revenue" for m in revenue_metrics)
        
        quantity_metrics = [m for m in suggestions if m.base_column == "quantity"]
        assert any(m.aggregation == "sum" and m.name == "total_quantity" for m in quantity_metrics)
        assert any(m.aggregation == "avg" and m.name == "avg_quantity" for m in quantity_metrics)
    
    def test_suggest_calculated_metrics(self, metric_suggester, analyzed_table):
        """Test suggestions for calculated/derived metrics"""
        suggestions = metric_suggester.suggest_metrics(analyzed_table)
        
        # Should suggest calculated metrics based on multiple columns
        calculated_metrics = [m for m in suggestions if m.metric_type == "derived"]
        
        # Average order value (revenue / count)
        assert any(m.name == "avg_order_value" and m.expression for m in calculated_metrics)
        
        # Discount rate (discount_amount / revenue)
        assert any(m.name == "discount_rate" and "discount_amount" in m.expression for m in calculated_metrics)
        
        # Return rate (using is_returned boolean)
        assert any(m.name == "return_rate" for m in calculated_metrics)
    
    def test_suggest_time_based_metrics(self, metric_suggester, analyzed_table):
        """Test time-based metric suggestions"""
        suggestions = metric_suggester.suggest_metrics(analyzed_table)
        
        # Should suggest time-based metrics when date columns exist
        time_metrics = [m for m in suggestions if m.requires_time_dimension]
        
        assert any(m.name == "revenue_growth_rate" for m in time_metrics)
        assert any(m.name == "orders_per_day" for m in time_metrics)
        assert any(m.name == "rolling_7_day_revenue" for m in time_metrics)
    
    def test_metric_scoring_and_ranking(self, metric_suggester, analyzed_table):
        """Test metric suggestion scoring and ranking"""
        suggestions = metric_suggester.suggest_metrics(analyzed_table)
        
        # Metrics should be scored and ranked by relevance
        assert all(hasattr(m, 'confidence_score') for m in suggestions)
        assert all(0 <= m.confidence_score <= 1 for m in suggestions)
        
        # Higher value columns should have higher scores
        revenue_metric = next(m for m in suggestions if m.name == "total_revenue")
        quantity_metric = next(m for m in suggestions if m.name == "total_quantity")
        assert revenue_metric.confidence_score >= quantity_metric.confidence_score
    
    def test_industry_specific_suggestions(self, metric_suggester, analyzed_table):
        """Test industry-specific metric suggestions based on table context"""
        # Add industry context
        analyzed_table["industry_context"] = "retail"
        
        # Add some columns that retail metrics need
        analyzed_table["columns"]["customer_id"] = {"data_type": "BIGINT", "pattern": "identifier"}
        analyzed_table["columns"]["visitor_id"] = {"data_type": "BIGINT", "pattern": "identifier"}
        
        suggestions = metric_suggester.suggest_metrics(analyzed_table)
        
        # Should include retail-specific metrics
        retail_metrics = [m for m in suggestions if m.category == "retail"]
        assert len(retail_metrics) > 0  # Should have at least some retail metrics
        
        # Check for specific metrics (some may be included based on column availability)
        metric_names = [m.name for m in retail_metrics]
        assert "basket_size" in metric_names or "customer_lifetime_value" in metric_names


class TestModelGenerator:
    """Test cases for ModelGenerator service"""
    
    @pytest.fixture
    def model_generator(self):
        """Create ModelGenerator instance"""
        return ModelGenerator()
    
    @pytest.fixture
    def suggested_components(self):
        """Sample suggested metrics and dimensions"""
        return {
            "metrics": [
                SuggestedMetric(
                    name="total_revenue",
                    display_name="Total Revenue",
                    base_column="revenue",
                    aggregation="sum",
                    expression="SUM(revenue)",
                    description="Total revenue from all orders",
                    confidence_score=0.95
                ),
                SuggestedMetric(
                    name="avg_order_value",
                    display_name="Average Order Value",
                    expression="SUM(revenue) / COUNT(DISTINCT order_id)",
                    metric_type="derived",
                    description="Average revenue per order",
                    confidence_score=0.90
                ),
                SuggestedMetric(
                    name="return_rate",
                    display_name="Return Rate",
                    expression="SUM(CASE WHEN is_returned THEN 1 ELSE 0 END) / COUNT(*)",
                    metric_type="derived",
                    description="Percentage of orders that were returned",
                    confidence_score=0.85
                )
            ],
            "dimensions": [
                SuggestedDimension(
                    name="order_date",
                    display_name="Order Date",
                    type="time",
                    granularities=["day", "week", "month", "quarter", "year"],
                    expression="order_date"
                ),
                SuggestedDimension(
                    name="region",
                    display_name="Region",
                    type="categorical",
                    expression="region"
                ),
                SuggestedDimension(
                    name="sales_channel",
                    display_name="Sales Channel",
                    type="categorical",
                    expression="sales_channel"
                )
            ],
            "entities": [
                {"name": "order", "type": "primary", "expr": "order_id"},
                {"name": "customer", "type": "foreign", "expr": "customer_id"},
                {"name": "product", "type": "foreign", "expr": "product_id"}
            ]
        }
    
    def test_generate_semantic_model(self, model_generator, suggested_components):
        """Test basic semantic model generation"""
        model = model_generator.generate_model(
            table_name="sales_fact",
            schema="gold",
            catalog="main",
            suggestions=suggested_components
        )
        
        assert model.name == "sales_fact_model"
        assert model.model_ref == "ref('main.gold.sales_fact')"
        assert len(model.metrics) == 3
        assert len(model.dimensions) == 3
        assert len(model.entities) == 3
    
    def test_generate_yaml_output(self, model_generator, suggested_components):
        """Test YAML generation for semantic model"""
        model = model_generator.generate_model(
            table_name="sales_fact",
            schema="gold",
            catalog="main",
            suggestions=suggested_components
        )
        
        yaml_content = model_generator.to_yaml(model)
        
        # Verify YAML structure
        assert "semantic_model:" in yaml_content
        assert "name: sales_fact_model" in yaml_content
        assert "metrics:" in yaml_content
        assert "- name: total_revenue" in yaml_content
        assert "dimensions:" in yaml_content
        assert "- name: order_date" in yaml_content
        assert "entities:" in yaml_content
    
    def test_model_validation(self, model_generator, suggested_components):
        """Test model validation rules"""
        model = model_generator.generate_model(
            table_name="sales_fact",
            schema="gold", 
            catalog="main",
            suggestions=suggested_components
        )
        
        # Validate model
        validation_result = model_generator.validate_model(model)
        
        assert validation_result.is_valid is True
        assert len(validation_result.errors) == 0
        assert len(validation_result.warnings) == 0
        
        # Test invalid model
        model.metrics = []  # Remove all metrics
        validation_result = model_generator.validate_model(model)
        
        assert validation_result.is_valid is False
        assert any("at least one metric" in str(e) for e in validation_result.errors)
    
    def test_model_customization(self, model_generator, suggested_components):
        """Test customization of generated model"""
        # Allow customization of suggestions before generation
        customization = {
            "excluded_metrics": ["return_rate"],
            "metric_overrides": {
                "total_revenue": {
                    "display_name": "Gross Revenue",
                    "description": "Total gross revenue including returns"
                }
            },
            "additional_metrics": [
                {
                    "name": "net_revenue",
                    "display_name": "Net Revenue",
                    "expression": "SUM(CASE WHEN NOT is_returned THEN revenue ELSE 0 END)",
                    "description": "Revenue excluding returned orders"
                }
            ]
        }
        
        model = model_generator.generate_model(
            table_name="sales_fact",
            schema="gold",
            catalog="main",
            suggestions=suggested_components,
            customization=customization
        )
        
        # Verify customizations applied
        assert not any(m.name == "return_rate" for m in model.metrics)
        revenue_metric = next(m for m in model.metrics if m.name == "total_revenue")
        assert revenue_metric.display_name == "Gross Revenue"
        assert any(m.name == "net_revenue" for m in model.metrics)
    
    def test_model_metadata_generation(self, model_generator, suggested_components):
        """Test metadata generation for model"""
        model = model_generator.generate_model(
            table_name="sales_fact",
            schema="gold",
            catalog="main", 
            suggestions=suggested_components
        )
        
        metadata = model_generator.generate_metadata(model)
        
        assert metadata.created_by == "automatic_generator"
        assert metadata.created_at is not None
        assert metadata.source_table == "main.gold.sales_fact"
        assert metadata.generation_version == "1.0"
        assert metadata.confidence_score > 0
        assert "statistics" in metadata.additional_info


class TestModelGenerationAPI:
    """Integration tests for model generation API endpoints"""
    
    @pytest.fixture
    def client(self):
        """Test client for API"""
        from app.main import app
        from fastapi.testclient import TestClient
        return TestClient(app)
    
    @pytest.fixture
    def auth_headers(self):
        """Authentication headers for protected endpoints"""
        return {"Authorization": "Bearer test-token"}
    
    def test_list_gold_tables(self, client, auth_headers):
        """Test endpoint to list available gold tables"""
        response = client.get("/api/catalog/gold-tables", headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) > 0
        assert "catalog" in data[0]
        assert "schema" in data[0]
        assert "table" in data[0]
    
    def test_analyze_table_endpoint(self, client, auth_headers):
        """Test table analysis endpoint"""
        request_data = {
            "catalog": "main",
            "schema": "gold", 
            "table": "sales_fact"
        }
        
        response = client.post(
            "/api/models/analyze-table",
            json=request_data,
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "analysis" in data
        assert "suggested_metrics" in data
        assert "suggested_dimensions" in data
        assert "confidence_scores" in data
    
    def test_generate_model_endpoint(self, client, auth_headers):
        """Test model generation endpoint"""
        request_data = {
            "catalog": "main",
            "schema": "gold",
            "table": "sales_fact",
            "accept_suggestions": True,
            "customization": {
                "model_name": "sales_metrics",
                "excluded_metrics": ["low_confidence_metric"]
            }
        }
        
        response = client.post(
            "/api/models/generate",
            json=request_data,
            headers=auth_headers
        )
        
        assert response.status_code == 201
        data = response.json()
        assert "model_id" in data
        assert "yaml_content" in data
        assert "validation_result" in data
        assert data["validation_result"]["is_valid"] is True
    
    def test_async_generation_status(self, client, auth_headers):
        """Test async generation status endpoint"""
        # Start generation
        request_data = {
            "catalog": "main",
            "schema": "gold",
            "tables": ["sales_fact", "customer_dim", "product_dim"],  # Multiple tables
            "async": True
        }
        
        response = client.post(
            "/api/models/generate",
            json=request_data,
            headers=auth_headers
        )
        
        assert response.status_code == 202  # Accepted
        data = response.json()
        job_id = data["job_id"]
        
        # Check status
        status_response = client.get(
            f"/api/models/generation-status/{job_id}",
            headers=auth_headers
        )
        
        assert status_response.status_code == 200
        status_data = status_response.json()
        assert "status" in status_data
        assert "progress" in status_data
        assert status_data["status"] in ["pending", "processing", "completed", "failed"]
    
    def test_generation_with_lineage(self, client, auth_headers):
        """Test model generation includes lineage information"""
        request_data = {
            "catalog": "main",
            "schema": "gold",
            "table": "sales_fact",
            "include_lineage": True
        }
        
        response = client.post(
            "/api/models/analyze-table",
            json=request_data,
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "lineage" in data
        assert "upstream_tables" in data["lineage"]
        assert "downstream_tables" in data["lineage"]
        
    def test_error_handling(self, client, auth_headers):
        """Test error handling for various scenarios"""
        # Non-existent table
        response = client.post(
            "/api/models/analyze-table",
            json={"catalog": "main", "schema": "gold", "table": "non_existent"},
            headers=auth_headers
        )
        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()
        
        # Invalid schema
        response = client.post(
            "/api/models/generate",
            json={"invalid": "data"},
            headers=auth_headers
        )
        assert response.status_code == 422  # Validation error
        
        # Unauthorized
        response = client.get("/api/catalog/gold-tables")
        assert response.status_code == 401


# Performance and edge case tests
class TestPerformanceAndEdgeCases:
    """Test performance and edge cases for model generation"""
    
    @pytest.fixture
    def table_analyzer(self, mock_databricks_client):
        """Create TableAnalyzer instance with mocked client"""
        return TableAnalyzer(client=mock_databricks_client)
    
    @pytest.fixture
    def model_generator(self):
        """Create ModelGenerator instance"""
        return ModelGenerator()
    
    @pytest.fixture
    def mock_databricks_client(self):
        """Mock Databricks client for testing"""
        client = Mock()
        return client
    
    @pytest.fixture
    def auth_headers(self):
        """Authentication headers for protected endpoints"""
        return {"Authorization": "Bearer test-token"}
    
    @pytest.fixture
    def large_table_schema(self):
        """Schema with many columns to test performance"""
        columns = []
        # Add 1000 columns of various types
        for i in range(1000):
            col_type = ["BIGINT", "DECIMAL(10,2)", "STRING", "DATE", "BOOLEAN"][i % 5]
            columns.append(
                ColumnInfo(
                    name=f"column_{i}",
                    data_type=col_type,
                    nullable=True,
                    comment=f"Column {i} description"
                )
            )
        
        return TableSchema(
            catalog="main",
            schema="gold",
            table="large_table",
            columns=columns,
            table_comment="Large table for performance testing"
        )
    
    def test_large_table_performance(self, table_analyzer, large_table_schema):
        """Test performance with large tables"""
        import time
        
        start_time = time.time()
        analysis = table_analyzer.analyze_table(large_table_schema)
        end_time = time.time()
        
        # Should complete within reasonable time (< 5 seconds)
        assert (end_time - start_time) < 5.0
        assert len(analysis.columns) == 1000
    
    def test_special_characters_handling(self, model_generator):
        """Test handling of special characters in names"""
        suggestions = {
            "metrics": [
                SuggestedMetric(
                    name="revenue_$_usd",
                    display_name="Revenue (USD)",
                    base_column="revenue_usd",
                    aggregation="sum"
                )
            ],
            "dimensions": [
                SuggestedDimension(
                    name="region/territory",
                    display_name="Region/Territory",
                    type="categorical"
                )
            ]
        }
        
        model = model_generator.generate_model(
            table_name="sales-fact",  # Hyphen in name
            schema="gold",
            catalog="main",
            suggestions=suggestions
        )
        
        # Should sanitize names
        assert model.name == "sales_fact_model"
        assert model.metrics[0].name == "revenue_usd"  # $ removed
        assert model.dimensions[0].name == "region_territory"  # / replaced
    
    def test_empty_table_handling(self, table_analyzer):
        """Test handling of empty tables"""
        empty_schema = TableSchema(
            catalog="main",
            schema="gold", 
            table="empty_table",
            columns=[],
            statistics={"numRows": 0}
        )
        
        analysis = table_analyzer.analyze_table(empty_schema)
        assert analysis.row_count == 0
        assert len(analysis.columns) == 0
        assert analysis.is_empty is True
    
    def test_concurrent_generation(self, client, auth_headers):
        """Test concurrent model generation requests"""
        import asyncio
        import aiohttp
        
        async def generate_model(session, table_name):
            url = "http://localhost:8000/api/models/generate"
            data = {
                "catalog": "main",
                "schema": "gold",
                "table": table_name
            }
            async with session.post(url, json=data, headers=auth_headers) as response:
                return await response.json()
        
        async def test_concurrent():
            async with aiohttp.ClientSession() as session:
                tables = [f"table_{i}" for i in range(10)]
                tasks = [generate_model(session, table) for table in tables]
                results = await asyncio.gather(*tasks, return_exceptions=True)
                
                # All should succeed or fail gracefully
                assert all(
                    isinstance(r, dict) or isinstance(r, Exception)
                    for r in results
                )
        
        # Run concurrent test
        asyncio.run(test_concurrent())
