"""
Comprehensive unit tests for the Documentation Generation feature.
Tests include model documentation, metadata extraction, template rendering,
and various export formats.
"""

import pytest
import json
from datetime import datetime
from unittest.mock import Mock, patch, MagicMock
from pathlib import Path
import yaml

from app.services.documentation_generator import (
    DocumentationGenerator,
    DocumentationConfig,
    DocumentationFormat,
    DocumentationTemplate
)
from app.services.metadata_extractor import MetadataExtractor
from app.services.documentation_templates import TemplateManager
from app.models.documentation import (
    DocumentationMetadata,
    DocumentationSection,
    ExportOptions,
    GeneratedDocumentation
)
from app.api.documentation import router as doc_router
from fastapi.testclient import TestClient
from app.main import app


class TestMetadataExtractor:
    """Test metadata extraction from semantic models"""
    
    @pytest.fixture
    def metadata_extractor(self):
        return MetadataExtractor()
    
    @pytest.fixture
    def sample_semantic_model(self):
        return {
            'name': 'sales_fact_model',
            'description': 'Sales fact table semantic model for business analytics',
            'version': '1.0.0',
            'created_at': '2024-01-15T10:00:00Z',
            'created_by': 'data_team',
            'entities': [{
                'name': 'sales_fact',
                'description': 'Main sales fact table',
                'sql_table': 'gold.sales.sales_fact'
            }],
            'measures': [
                {
                    'name': 'total_sales',
                    'description': 'Total sales amount',
                    'sql': 'sum(amount)',
                    'type': 'sum'
                },
                {
                    'name': 'avg_order_value',
                    'description': 'Average order value',
                    'sql': 'avg(amount)',
                    'type': 'avg'
                }
            ],
            'dimensions': [
                {
                    'name': 'product_name',
                    'sql': 'product_name',
                    'type': 'string',
                    'description': 'Name of the product'
                },
                {
                    'name': 'customer_segment',
                    'sql': 'customer_segment',
                    'type': 'string',
                    'description': 'Customer segment classification'
                }
            ],
            'metrics': [
                {
                    'name': 'revenue_growth',
                    'description': 'Year-over-year revenue growth',
                    'type': 'derived',
                    'sql': '(total_sales - lag(total_sales) over (order by date)) / lag(total_sales) over (order by date)',
                    'dimensions': ['date']
                }
            ]
        }
    
    def test_extract_basic_metadata(self, metadata_extractor, sample_semantic_model):
        """Test extraction of basic model metadata"""
        metadata = metadata_extractor.extract_metadata(sample_semantic_model)
        
        assert metadata.model_name == 'sales_fact_model'
        assert metadata.description == 'Sales fact table semantic model for business analytics'
        assert metadata.version == '1.0.0'
        assert metadata.created_by == 'data_team'
        assert len(metadata.entities) == 1
        assert len(metadata.measures) == 2
        assert len(metadata.dimensions) == 2
        assert len(metadata.metrics) == 1
    
    def test_extract_relationships(self, metadata_extractor):
        """Test extraction of model relationships and dependencies"""
        model_with_relations = {
            'name': 'order_model',
            'entities': [{
                'name': 'orders',
                'sql_table': 'gold.sales.orders'
            }],
            'dimensions': [{
                'name': 'customer_id',
                'sql': 'customer_id',
                'type': 'string',
                'meta': {
                    'joins_to': 'customer_model.customer_id'
                }
            }]
        }
        
        metadata = metadata_extractor.extract_metadata(model_with_relations)
        relationships = metadata_extractor.extract_relationships(model_with_relations)
        
        assert len(relationships) == 1
        assert relationships[0]['from_model'] == 'order_model'
        assert relationships[0]['to_model'] == 'customer_model'
        assert relationships[0]['join_key'] == 'customer_id'
    
    def test_extract_business_context(self, metadata_extractor):
        """Test extraction of business context and usage patterns"""
        model = {
            'name': 'product_analytics',
            'meta': {
                'business_owner': 'Product Team',
                'refresh_schedule': 'Daily at 2 AM UTC',
                'data_quality_checks': ['null_check', 'duplicate_check'],
                'common_use_cases': [
                    'Product performance analysis',
                    'Inventory optimization',
                    'Sales forecasting'
                ]
            }
        }
        
        context = metadata_extractor.extract_business_context(model)
        
        assert context['business_owner'] == 'Product Team'
        assert context['refresh_schedule'] == 'Daily at 2 AM UTC'
        assert len(context['data_quality_checks']) == 2
        assert len(context['common_use_cases']) == 3


class TestTemplateManager:
    """Test documentation template management"""
    
    @pytest.fixture
    def template_manager(self):
        return TemplateManager()
    
    def test_get_default_templates(self, template_manager):
        """Test retrieval of default documentation templates"""
        templates = template_manager.get_available_templates()
        
        assert 'standard' in templates
        assert 'technical' in templates
        assert 'business' in templates
        assert 'executive' in templates
    
    def test_load_template(self, template_manager):
        """Test loading a specific template"""
        template = template_manager.load_template('standard')
        
        assert template.name == 'standard'
        assert template.sections is not None
        assert 'overview' in template.sections
        assert 'entities' in template.sections
        assert 'metrics' in template.sections
    
    def test_custom_template_creation(self, template_manager):
        """Test creating custom documentation templates"""
        custom_sections = {
            'executive_summary': {
                'title': 'Executive Summary',
                'include_metrics': True,
                'include_kpis': True
            },
            'technical_details': {
                'title': 'Technical Implementation',
                'include_sql': True,
                'include_lineage': True
            }
        }
        
        custom_template = template_manager.create_custom_template(
            name='custom_exec',
            sections=custom_sections
        )
        
        assert custom_template.name == 'custom_exec'
        assert len(custom_template.sections) == 2
        assert 'executive_summary' in custom_template.sections


class TestDocumentationGenerator:
    """Test documentation generation functionality"""
    
    @pytest.fixture
    def doc_generator(self):
        return DocumentationGenerator()
    
    @pytest.fixture
    def mock_metadata_extractor(self):
        extractor = Mock(spec=MetadataExtractor)
        extractor.extract_metadata.return_value = Mock(
            model_name='test_model',
            description='Test description',
            entities=[{'name': 'test_entity', 'description': 'Test entity'}],
            measures=[{'name': 'test_measure', 'description': 'Test measure'}],
            dimensions=[{'name': 'test_dimension', 'description': 'Test dimension'}],
            metrics=[{'name': 'test_metric', 'description': 'Test metric'}]
        )
        return extractor
    
    def test_generate_markdown_documentation(self, doc_generator, sample_semantic_model):
        """Test generation of Markdown documentation"""
        config = DocumentationConfig(
            format=DocumentationFormat.MARKDOWN,
            template='standard',
            include_sql=True,
            include_lineage=False,
            include_examples=True
        )
        
        doc = doc_generator.generate_documentation(sample_semantic_model, config)
        
        assert doc.format == DocumentationFormat.MARKDOWN
        assert '# sales_fact_model' in doc.content
        assert '## Overview' in doc.content
        assert '## Entities' in doc.content
        assert '## Measures' in doc.content
        assert '## Dimensions' in doc.content
        assert '## Metrics' in doc.content
        assert 'total_sales' in doc.content
        assert 'revenue_growth' in doc.content
    
    def test_generate_html_documentation(self, doc_generator, sample_semantic_model):
        """Test generation of HTML documentation"""
        config = DocumentationConfig(
            format=DocumentationFormat.HTML,
            template='business',
            include_sql=False,
            include_visualizations=True
        )
        
        doc = doc_generator.generate_documentation(sample_semantic_model, config)
        
        assert doc.format == DocumentationFormat.HTML
        assert '<html>' in doc.content
        assert '<h1>sales_fact_model</h1>' in doc.content
        assert 'class="measure"' in doc.content
        assert 'sql' not in doc.content.lower()  # SQL should be excluded
    
    def test_generate_pdf_documentation(self, doc_generator, sample_semantic_model):
        """Test generation of PDF documentation"""
        config = DocumentationConfig(
            format=DocumentationFormat.PDF,
            template='technical'
        )
        
        doc = doc_generator.generate_documentation(sample_semantic_model, config)
        
        assert doc.format == DocumentationFormat.PDF
        assert doc.content_type == 'application/pdf'
        assert len(doc.content) > 0  # PDF content should be bytes
    
    def test_include_data_lineage(self, doc_generator):
        """Test including data lineage in documentation"""
        model_with_lineage = {
            'name': 'derived_metrics',
            'entities': [{
                'name': 'sales_summary',
                'sql_table': 'gold.analytics.sales_summary',
                'meta': {
                    'source_tables': [
                        'silver.sales.transactions',
                        'silver.sales.customers',
                        'silver.sales.products'
                    ]
                }
            }]
        }
        
        config = DocumentationConfig(
            format=DocumentationFormat.MARKDOWN,
            include_lineage=True
        )
        
        doc = doc_generator.generate_documentation(model_with_lineage, config)
        
        assert '## Data Lineage' in doc.content
        assert 'silver.sales.transactions' in doc.content
        assert 'silver.sales.customers' in doc.content
        assert 'silver.sales.products' in doc.content
    
    def test_include_usage_examples(self, doc_generator, sample_semantic_model):
        """Test including usage examples in documentation"""
        config = DocumentationConfig(
            format=DocumentationFormat.MARKDOWN,
            include_examples=True
        )
        
        doc = doc_generator.generate_documentation(sample_semantic_model, config)
        
        assert '## Usage Examples' in doc.content
        assert '```sql' in doc.content
        assert 'SELECT' in doc.content
        assert 'total_sales' in doc.content
    
    def test_multi_model_documentation(self, doc_generator):
        """Test generating documentation for multiple related models"""
        models = [
            {
                'name': 'customer_model',
                'description': 'Customer dimension model'
            },
            {
                'name': 'product_model',
                'description': 'Product dimension model'
            },
            {
                'name': 'sales_model',
                'description': 'Sales fact model'
            }
        ]
        
        config = DocumentationConfig(
            format=DocumentationFormat.MARKDOWN,
            template='standard',
            include_relationships=True
        )
        
        doc = doc_generator.generate_multi_model_documentation(models, config)
        
        assert '# Data Model Documentation' in doc.content
        assert '## customer_model' in doc.content
        assert '## product_model' in doc.content
        assert '## sales_model' in doc.content
        assert '## Model Relationships' in doc.content


class TestDocumentationAPI:
    """Test documentation API endpoints"""
    
    @pytest.fixture
    def client(self):
        return TestClient(app)
    
    @pytest.fixture
    def auth_headers(self):
        return {"Authorization": "Bearer test-token"}
    
    @pytest.fixture
    def mock_doc_generator(self):
        with patch('app.api.documentation.DocumentationGenerator') as mock:
            generator = mock.return_value
            generator.generate_documentation.return_value = Mock(
                format=DocumentationFormat.MARKDOWN,
                content='# Test Documentation',
                metadata={'generated_at': datetime.utcnow().isoformat()}
            )
            yield generator
    
    def test_generate_documentation_endpoint(self, client, auth_headers, mock_doc_generator):
        """Test POST /documentation/generate endpoint"""
        request_data = {
            'model_id': 'sales_model',
            'format': 'markdown',
            'template': 'standard',
            'options': {
                'include_sql': True,
                'include_examples': True
            }
        }
        
        response = client.post(
            '/api/v1/documentation/generate',
            json=request_data,
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data['success'] is True
        assert data['documentation']['format'] == 'markdown'
        assert data['documentation']['content'] is not None
    
    def test_generate_batch_documentation(self, client, auth_headers):
        """Test POST /documentation/batch endpoint for multiple models"""
        request_data = {
            'model_ids': ['model1', 'model2', 'model3'],
            'format': 'html',
            'template': 'business'
        }
        
        response = client.post(
            '/api/v1/documentation/batch',
            json=request_data,
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data['success'] is True
        assert data['job_id'] is not None
    
    def test_get_documentation_status(self, client, auth_headers):
        """Test GET /documentation/status/{job_id} endpoint"""
        job_id = 'test-job-123'
        
        response = client.get(
            f'/api/v1/documentation/status/{job_id}',
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert 'status' in data
        assert 'progress' in data
    
    def test_list_templates(self, client, auth_headers):
        """Test GET /documentation/templates endpoint"""
        response = client.get(
            '/api/v1/documentation/templates',
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert 'templates' in data
        assert len(data['templates']) > 0
        assert 'standard' in [t['name'] for t in data['templates']]
    
    def test_export_documentation(self, client, auth_headers):
        """Test GET /documentation/export endpoint"""
        params = {
            'model_id': 'sales_model',
            'format': 'pdf'
        }
        
        response = client.get(
            '/api/v1/documentation/export',
            params=params,
            headers=auth_headers
        )
        
        assert response.status_code == 200
        assert response.headers['content-type'] == 'application/pdf'
        assert len(response.content) > 0


class TestDocumentationIntegration:
    """Integration tests for documentation generation"""
    
    @pytest.fixture
    def integrated_generator(self):
        """Create generator with all dependencies"""
        return DocumentationGenerator(
            metadata_extractor=MetadataExtractor(),
            template_manager=TemplateManager()
        )
    
    def test_end_to_end_documentation_generation(self, integrated_generator):
        """Test complete documentation generation workflow"""
        # Load a semantic model
        model_yaml = """
        name: customer_analytics
        description: Customer analytics semantic model
        
        entities:
          - name: customers
            sql_table: gold.analytics.dim_customers
            description: Customer dimension table
        
        measures:
          - name: customer_count
            sql: count(distinct customer_id)
            type: count_distinct
            description: Total number of unique customers
          
          - name: total_revenue
            sql: sum(lifetime_value)
            type: sum
            description: Total customer lifetime value
        
        dimensions:
          - name: customer_segment
            sql: customer_segment
            type: string
            description: Customer segmentation category
          
          - name: acquisition_channel
            sql: acquisition_channel
            type: string
            description: Channel through which customer was acquired
        
        metrics:
          - name: avg_customer_value
            type: derived
            sql: "{{total_revenue}} / {{customer_count}}"
            description: Average lifetime value per customer
        """
        
        model = yaml.safe_load(model_yaml)
        
        # Generate documentation
        config = DocumentationConfig(
            format=DocumentationFormat.MARKDOWN,
            template='business',
            include_sql=False,
            include_examples=True,
            include_visualizations=True
        )
        
        doc = integrated_generator.generate_documentation(model, config)
        
        # Verify documentation content
        assert doc.format == DocumentationFormat.MARKDOWN
        assert 'Customer analytics semantic model' in doc.content
        assert 'customer_count' in doc.content
        assert 'avg_customer_value' in doc.content
        assert 'Usage Examples' in doc.content
        
        # Verify no SQL is included (business template)
        assert 'count(distinct customer_id)' not in doc.content
    
    def test_documentation_versioning(self, integrated_generator):
        """Test documentation versioning and history"""
        model = {'name': 'test_model', 'version': '1.0.0'}
        
        # Generate v1 documentation
        doc_v1 = integrated_generator.generate_documentation(
            model,
            DocumentationConfig(format=DocumentationFormat.MARKDOWN)
        )
        
        # Update model
        model['version'] = '1.1.0'
        model['changelog'] = ['Added new metrics', 'Updated dimensions']
        
        # Generate v2 documentation
        doc_v2 = integrated_generator.generate_documentation(
            model,
            DocumentationConfig(
                format=DocumentationFormat.MARKDOWN,
                include_changelog=True
            )
        )
        
        assert doc_v1.metadata['version'] == '1.0.0'
        assert doc_v2.metadata['version'] == '1.1.0'
        assert 'Changelog' in doc_v2.content
        assert 'Added new metrics' in doc_v2.content


# Performance and edge case tests
class TestDocumentationPerformance:
    """Test documentation generation performance and edge cases"""
    
    def test_large_model_documentation(self):
        """Test documentation generation for large models"""
        large_model = {
            'name': 'large_model',
            'measures': [{'name': f'measure_{i}', 'sql': f'sum(col_{i})'} 
                        for i in range(100)],
            'dimensions': [{'name': f'dim_{i}', 'sql': f'dim_{i}'} 
                          for i in range(50)],
            'metrics': [{'name': f'metric_{i}', 'sql': f'complex_sql_{i}'} 
                       for i in range(30)]
        }
        
        generator = DocumentationGenerator()
        start_time = datetime.utcnow()
        
        doc = generator.generate_documentation(
            large_model,
            DocumentationConfig(format=DocumentationFormat.MARKDOWN)
        )
        
        generation_time = (datetime.utcnow() - start_time).total_seconds()
        
        assert generation_time < 5.0  # Should complete within 5 seconds
        assert len(doc.content) > 10000  # Should generate substantial content
    
    def test_invalid_model_handling(self):
        """Test handling of invalid or incomplete models"""
        generator = DocumentationGenerator()
        
        # Test with empty model
        empty_doc = generator.generate_documentation(
            {},
            DocumentationConfig(format=DocumentationFormat.MARKDOWN)
        )
        assert 'No model information available' in empty_doc.content
        
        # Test with missing required fields
        incomplete_model = {'name': 'test'}
        doc = generator.generate_documentation(
            incomplete_model,
            DocumentationConfig(format=DocumentationFormat.MARKDOWN)
        )
        assert doc is not None
        assert 'test' in doc.content

