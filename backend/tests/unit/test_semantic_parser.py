"""Tests for semantic model parsing functionality."""

import pytest
import yaml
from app.services.semantic_parser import SemanticModelParser
from app.models.semantic_model import SemanticModel, Entity, Dimension, Measure, Metric


class TestSemanticModelParser:
    """Test cases for SemanticModelParser."""

    def test_parse_valid_yaml(self, sample_semantic_model):
        """Test parsing a valid semantic model YAML."""
        parser = SemanticModelParser()
        yaml_content = yaml.dump({'semantic_model': sample_semantic_model})
        
        result = parser.parse_yaml(yaml_content)
        
        assert isinstance(result, SemanticModel)
        assert result.name == 'test_sales_metrics'
        assert result.description == 'Test sales metrics model'
        assert result.model == 'main.gold.sales_fact'
        assert len(result.entities) == 3
        assert len(result.dimensions) == 2
        assert len(result.measures) == 2
        assert len(result.metrics) == 2

    def test_parse_invalid_yaml(self):
        """Test parsing invalid YAML content."""
        parser = SemanticModelParser()
        invalid_yaml = "invalid: yaml: content:"
        
        with pytest.raises(yaml.YAMLError):
            parser.parse_yaml(invalid_yaml)

    def test_validate_entities(self, sample_semantic_model):
        """Test entity validation."""
        parser = SemanticModelParser()
        entities_data = sample_semantic_model['entities']
        
        entities = parser._parse_entities(entities_data)
        
        assert len(entities) == 3
        assert entities[0].name == 'order_id'
        assert entities[0].type == 'primary'
        assert entities[1].type == 'foreign'

    def test_validate_dimensions(self, sample_semantic_model):
        """Test dimension validation."""
        parser = SemanticModelParser()
        dimensions_data = sample_semantic_model['dimensions']
        
        dimensions = parser._parse_dimensions(dimensions_data)
        
        assert len(dimensions) == 2
        time_dim = next(d for d in dimensions if d.name == 'order_date')
        assert time_dim.type == 'time'
        assert 'day' in time_dim.time_granularity
        assert 'month' in time_dim.time_granularity

    def test_validate_measures(self, sample_semantic_model):
        """Test measure validation."""
        parser = SemanticModelParser()
        measures_data = sample_semantic_model['measures']
        
        measures = parser._parse_measures(measures_data)
        
        assert len(measures) == 2
        revenue_measure = next(m for m in measures if m.name == 'revenue')
        assert revenue_measure.agg == 'sum'
        assert revenue_measure.expr == 'order_amount'

    def test_validate_metrics(self, sample_semantic_model):
        """Test metric validation."""
        parser = SemanticModelParser()
        metrics_data = sample_semantic_model['metrics']
        
        metrics = parser._parse_metrics(metrics_data)
        
        assert len(metrics) == 2
        ratio_metric = next(m for m in metrics if m.type == 'ratio')
        assert ratio_metric.name == 'average_order_value'
        assert ratio_metric.numerator == 'revenue'
        assert ratio_metric.denominator == 'order_count'

    def test_missing_required_fields(self):
        """Test validation with missing required fields."""
        parser = SemanticModelParser()
        invalid_model = {
            'semantic_model': {
                'name': 'test_model'
                # Missing required fields
            }
        }
        yaml_content = yaml.dump(invalid_model)
        
        with pytest.raises(ValueError, match="Missing required field"):
            parser.parse_yaml(yaml_content)

    def test_invalid_entity_type(self):
        """Test validation with invalid entity type."""
        parser = SemanticModelParser()
        invalid_entities = [
            {'name': 'test_id', 'type': 'invalid_type', 'expr': 'test_id'}
        ]
        
        with pytest.raises(ValueError, match="Invalid entity type"):
            parser._parse_entities(invalid_entities)

    def test_invalid_dimension_type(self):
        """Test validation with invalid dimension type.""" 
        parser = SemanticModelParser()
        invalid_dimensions = [
            {'name': 'test_dim', 'type': 'invalid_type', 'expr': 'test_col'}
        ]
        
        with pytest.raises(ValueError, match="Invalid dimension type"):
            parser._parse_dimensions(invalid_dimensions)

    def test_invalid_aggregation_type(self):
        """Test validation with invalid aggregation type."""
        parser = SemanticModelParser()
        invalid_measures = [
            {'name': 'test_measure', 'agg': 'invalid_agg', 'expr': 'test_col'}
        ]
        
        with pytest.raises(ValueError, match="Invalid aggregation type"):
            parser._parse_measures(invalid_measures)