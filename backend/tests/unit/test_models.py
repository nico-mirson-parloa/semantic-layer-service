"""Tests for Pydantic models and data structures."""

import pytest
from pydantic import ValidationError
from app.models.semantic_model import (
    SemanticModel, Entity, Dimension, Measure, Metric,
    EntityType, DimensionType, AggregationType, MetricType
)
from app.models.queries import QueryRequest, QueryResult
from app.models.metadata import TableMetadata, ColumnMetadata


class TestSemanticModelModels:
    """Test cases for semantic model Pydantic models."""

    def test_entity_creation_valid(self):
        """Test creating a valid Entity."""
        entity = Entity(
            name="customer_id",
            type=EntityType.FOREIGN,
            expr="customer_id",
            description="Customer identifier"
        )
        
        assert entity.name == "customer_id"
        assert entity.type == EntityType.FOREIGN
        assert entity.expr == "customer_id"

    def test_entity_invalid_type(self):
        """Test Entity creation with invalid type."""
        with pytest.raises(ValidationError):
            Entity(
                name="test_id",
                type="invalid_type",
                expr="test_id"
            )

    def test_dimension_time_type_valid(self):
        """Test creating a time dimension with granularities."""
        dimension = Dimension(
            name="order_date",
            type=DimensionType.TIME,
            expr="order_date",
            time_granularity=["day", "week", "month", "quarter", "year"]
        )
        
        assert dimension.type == DimensionType.TIME
        assert "month" in dimension.time_granularity
        assert len(dimension.time_granularity) == 5

    def test_dimension_categorical_type(self):
        """Test creating a categorical dimension."""
        dimension = Dimension(
            name="product_category",
            type=DimensionType.CATEGORICAL,
            expr="product_category"
        )
        
        assert dimension.type == DimensionType.CATEGORICAL
        assert dimension.time_granularity is None

    def test_measure_aggregation_types(self):
        """Test measure creation with different aggregation types."""
        sum_measure = Measure(
            name="total_revenue",
            agg=AggregationType.SUM,
            expr="order_amount"
        )
        
        count_measure = Measure(
            name="order_count",
            agg=AggregationType.COUNT,
            expr="order_id"
        )
        
        avg_measure = Measure(
            name="avg_amount",
            agg=AggregationType.AVG,
            expr="order_amount"
        )
        
        assert sum_measure.agg == AggregationType.SUM
        assert count_measure.agg == AggregationType.COUNT
        assert avg_measure.agg == AggregationType.AVG

    def test_metric_simple_type(self):
        """Test creating a simple metric."""
        metric = Metric(
            name="total_sales",
            type=MetricType.SIMPLE,
            measure="revenue",
            description="Total sales revenue"
        )
        
        assert metric.type == MetricType.SIMPLE
        assert metric.measure == "revenue"
        assert metric.numerator is None
        assert metric.denominator is None

    def test_metric_ratio_type(self):
        """Test creating a ratio metric."""
        metric = Metric(
            name="avg_order_value",
            type=MetricType.RATIO,
            numerator="revenue",
            denominator="order_count",
            description="Average order value"
        )
        
        assert metric.type == MetricType.RATIO
        assert metric.numerator == "revenue"
        assert metric.denominator == "order_count"
        assert metric.measure is None

    def test_semantic_model_complete(self, sample_semantic_model):
        """Test creating a complete semantic model."""
        model = SemanticModel(**sample_semantic_model)
        
        assert model.name == "test_sales_metrics"
        assert len(model.entities) == 3
        assert len(model.dimensions) == 2
        assert len(model.measures) == 2
        assert len(model.metrics) == 2
        
        # Test entity access
        primary_entity = next(e for e in model.entities if e.type == EntityType.PRIMARY)
        assert primary_entity.name == "order_id"
        
        # Test dimension access
        time_dimension = next(d for d in model.dimensions if d.type == DimensionType.TIME)
        assert time_dimension.name == "order_date"

    def test_semantic_model_validation_missing_name(self):
        """Test semantic model validation with missing name."""
        invalid_model = {
            "description": "Test model",
            "model": "test.table"
        }
        
        with pytest.raises(ValidationError, match="name"):
            SemanticModel(**invalid_model)


class TestQueryModels:
    """Test cases for query-related models."""

    def test_query_request_basic(self):
        """Test creating a basic query request."""
        request = QueryRequest(
            metrics=["total_revenue", "order_count"],
            dimensions=["order_date", "customer_region"],
            filters={"order_date": {">=": "2024-01-01"}},
            limit=1000
        )
        
        assert len(request.metrics) == 2
        assert len(request.dimensions) == 2
        assert "order_date" in request.filters
        assert request.limit == 1000

    def test_query_request_no_metrics(self):
        """Test query request validation with no metrics."""
        with pytest.raises(ValidationError, match="at least one metric"):
            QueryRequest(
                metrics=[],
                dimensions=["order_date"]
            )

    def test_query_result_structure(self):
        """Test query result structure."""
        result = QueryResult(
            columns=["order_date", "total_revenue", "order_count"],
            data=[
                ["2024-01-01", 1500.50, 12],
                ["2024-01-02", 2300.75, 18]
            ],
            row_count=2,
            execution_time=0.45
        )
        
        assert len(result.columns) == 3
        assert len(result.data) == 2
        assert result.row_count == 2
        assert result.execution_time == 0.45


class TestMetadataModels:
    """Test cases for metadata models."""

    def test_column_metadata(self):
        """Test column metadata model."""
        column = ColumnMetadata(
            column_name="order_amount",
            data_type="decimal(10,2)",
            is_nullable=False,
            comment="Order total amount"
        )
        
        assert column.column_name == "order_amount"
        assert column.data_type == "decimal(10,2)"
        assert not column.is_nullable

    def test_table_metadata_with_columns(self):
        """Test table metadata with column information."""
        columns = [
            ColumnMetadata(column_name="id", data_type="bigint", is_nullable=False),
            ColumnMetadata(column_name="name", data_type="string", is_nullable=True)
        ]
        
        table = TableMetadata(
            catalog_name="main",
            schema_name="gold",
            table_name="customers",
            table_type="TABLE",
            data_source_format="DELTA",
            columns=columns
        )
        
        assert table.full_name == "main.gold.customers"
        assert len(table.columns) == 2
        assert table.columns[0].column_name == "id"

    def test_table_metadata_full_name_property(self):
        """Test table metadata full name property."""
        table = TableMetadata(
            catalog_name="main",
            schema_name="bronze",
            table_name="raw_data",
            table_type="TABLE"
        )
        
        assert table.full_name == "main.bronze.raw_data"