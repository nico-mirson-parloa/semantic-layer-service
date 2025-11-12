"""
Service for generating documentation from semantic models.
"""

import logging
from typing import Dict, List, Any, Optional, Union
from datetime import datetime
import json
import re
from pathlib import Path
import yaml

from app.models.documentation import (
    DocumentationConfig,
    DocumentationFormat,
    GeneratedDocumentation,
    DocumentationMetadata,
    DocumentationSection
)
from app.services.metadata_extractor import MetadataExtractor
from app.services.documentation_templates import TemplateManager
from app.services.llm_table_analyzer import LLMTableAnalyzer
from app.core.config import settings


logger = logging.getLogger(__name__)


class DocumentationGenerator:
    """Generate documentation from semantic models"""
    
    def __init__(
        self,
        metadata_extractor: Optional[MetadataExtractor] = None,
        template_manager: Optional[TemplateManager] = None,
        use_llm: bool = None
    ):
        """
        Initialize documentation generator.
        
        Args:
            metadata_extractor: Metadata extraction service
            template_manager: Template management service
            use_llm: Whether to use LLM for enhanced documentation generation
        """
        self.metadata_extractor = metadata_extractor or MetadataExtractor()
        self.template_manager = template_manager or TemplateManager()
        self.use_llm = use_llm if use_llm is not None else getattr(settings, 'enable_llm_analysis', False)
        self.llm_analyzer = None
        
        if self.use_llm:
            try:
                self.llm_analyzer = LLMTableAnalyzer()
                logger.info("LLM-enhanced documentation generation enabled")
            except Exception as e:
                logger.warning(f"Failed to initialize LLM analyzer: {e}. Falling back to template-based generation.")
                self.use_llm = False
    
    def generate_documentation(
        self,
        model: Dict[str, Any],
        config: DocumentationConfig
    ) -> GeneratedDocumentation:
        """
        Generate documentation for a semantic model.
        
        Args:
            model: Semantic model dictionary
            config: Documentation configuration
            
        Returns:
            GeneratedDocumentation object
        """
        try:
            # Extract metadata
            metadata = self.metadata_extractor.extract_metadata(model)
            
            # Load template
            template = self.template_manager.load_template(config.template)
            
            # Generate documentation based on format
            if config.format == DocumentationFormat.MARKDOWN:
                if self.use_llm and self.llm_analyzer:
                    content = self._generate_llm_enhanced_markdown(model, metadata, template, config)
                else:
                    content = self._generate_markdown(model, metadata, template, config)
                content_type = "text/markdown"
            elif config.format == DocumentationFormat.HTML:
                content = self._generate_html(model, metadata, template, config)
                content_type = "text/html"
            elif config.format == DocumentationFormat.PDF:
                content = self._generate_pdf(model, metadata, template, config)
                content_type = "application/pdf"
            elif config.format == DocumentationFormat.JSON:
                content = self._generate_json(model, metadata, template, config)
                content_type = "application/json"
            else:
                raise ValueError(f"Unsupported format: {config.format}")
            
            # Calculate size
            size_bytes = len(content) if isinstance(content, (str, bytes)) else None
            if isinstance(content, str):
                size_bytes = len(content.encode('utf-8'))
            
            # Generate filename
            filename = self._generate_filename(metadata.model_name, config.format)
            
            return GeneratedDocumentation(
                format=config.format,
                content=content,
                content_type=content_type,
                metadata={
                    'generated_at': datetime.utcnow().isoformat(),
                    'model_name': metadata.model_name,
                    'model_version': metadata.version,
                    'template': config.template,
                    'config': config.model_dump()
                },
                filename=filename,
                size_bytes=size_bytes
            )
            
        except Exception as e:
            logger.error(f"Error generating documentation: {str(e)}")
            # Return error documentation
            return GeneratedDocumentation(
                format=config.format,
                content=f"Error generating documentation: {str(e)}",
                content_type="text/plain",
                metadata={
                    'error': str(e),
                    'generated_at': datetime.utcnow().isoformat()
                }
            )
    
    def _generate_llm_enhanced_markdown(
        self,
        model: Dict[str, Any],
        metadata: DocumentationMetadata,
        template: Any,
        config: DocumentationConfig
    ) -> str:
        """Generate LLM-enhanced engineering documentation"""
        try:
            # Handle nested semantic_model structure
            if 'semantic_model' in model:
                semantic_model = model['semantic_model']
            else:
                semantic_model = model
            
            # Build context for LLM
            model_context = self._build_semantic_model_context(semantic_model, metadata)
            
            # Create engineering documentation prompt
            prompt = self._create_engineering_documentation_prompt(model_context, metadata, config)
            
            # Call LLM for documentation generation
            llm_response = self.llm_analyzer._call_databricks_llm(prompt)
            
            # Parse and enhance the LLM response
            enhanced_content = self._process_llm_documentation_response(llm_response, model, metadata)
            
            return enhanced_content
            
        except Exception as e:
            logger.error(f"LLM documentation generation failed: {e}. Falling back to template-based generation.")
            return self._generate_markdown(model, metadata, template, config)
    
    def _build_semantic_model_context(self, model: Dict[str, Any], metadata: DocumentationMetadata) -> str:
        """Build comprehensive context about the semantic model for LLM"""
        context_parts = []
        
        # Basic model information
        context_parts.append(f"SEMANTIC MODEL: {metadata.model_name}")
        if metadata.description:
            context_parts.append(f"Description: {metadata.description}")
        if metadata.version:
            context_parts.append(f"Version: {metadata.version}")
        
        # Model structure overview
        context_parts.append(f"\nMODEL STRUCTURE:")
        context_parts.append(f"- Entities: {len(metadata.entities)}")
        context_parts.append(f"- Measures: {len(metadata.measures)}")
        context_parts.append(f"- Dimensions: {len(metadata.dimensions)}")
        context_parts.append(f"- Business Metrics: {len(metadata.metrics)}")
        
        # Detailed component information
        if metadata.entities:
            context_parts.append(f"\nENTITIES:")
            for entity in metadata.entities:
                context_parts.append(f"- {entity['name']}: {entity.get('description', 'No description')}")
                if entity.get('source_tables'):
                    context_parts.append(f"  Source: {', '.join(entity['source_tables'])}")
        
        if metadata.measures:
            context_parts.append(f"\nMEASURES:")
            for measure in metadata.measures:
                context_parts.append(f"- {measure['name']}: {measure.get('description', 'No description')}")
                context_parts.append(f"  Type: {measure.get('type', 'Unknown')}")
                if measure.get('sql'):
                    context_parts.append(f"  SQL: {measure['sql']}")
        
        if metadata.dimensions:
            context_parts.append(f"\nDIMENSIONS:")
            for dimension in metadata.dimensions:
                context_parts.append(f"- {dimension['name']}: {dimension.get('description', 'No description')}")
                context_parts.append(f"  Type: {dimension.get('type', 'categorical')}")
                if dimension.get('sql'):
                    context_parts.append(f"  SQL: {dimension['sql']}")
        
        if metadata.metrics:
            context_parts.append(f"\nBUSINESS METRICS:")
            for metric in metadata.metrics:
                context_parts.append(f"- {metric['name']}: {metric.get('description', 'No description')}")
                if metric.get('type'):
                    context_parts.append(f"  Type: {metric['type']}")
                if metric.get('sql'):
                    context_parts.append(f"  Calculation: {metric['sql']}")
        
        # Business context if available
        if metadata.business_context:
            context_parts.append(f"\nBUSINESS CONTEXT:")
            for key, value in metadata.business_context.items():
                if value:
                    context_parts.append(f"- {key}: {value}")
        
        return "\n".join(context_parts)
    
    def _create_engineering_documentation_prompt(
        self, 
        model_context: str, 
        metadata: DocumentationMetadata, 
        config: DocumentationConfig
    ) -> str:
        """Create a detailed prompt for LLM to generate engineering documentation"""
        
        template_type = config.template if config.template else "standard"
        
        prompt = f"""You are creating technical documentation for a semantic data model. 

SEMANTIC MODEL DETAILS:
{model_context}

INSTRUCTIONS:
1. Document ONLY what is defined in the model above
2. DO NOT make up fields, metrics, tables, or features not shown
3. If information is missing, state "Not specified" rather than guessing
4. Focus on practical usage of the actual model components

Generate documentation with these sections:

## Model Overview
- Name: [Use the exact model name from above]
- Description: [Use the exact description from above]
- Purpose: [Infer from the metrics and dimensions provided]

## Components

### Dimensions
Create a table with columns: Name | Type | Expression | Description
[List ONLY the dimensions shown in the model]

### Measures  
Create a table with columns: Name | Aggregation | Expression | Description
[List ONLY the measures shown in the model]

### Metrics (if any)
Create a table with columns: Name | Type | Expression | Description
[List ONLY if metrics are defined in the model]

## Usage Guide

### Key Use Cases
Based on the available measures and dimensions, this model supports:
[List 2-3 use cases that can be directly fulfilled by the defined components]

### Example Queries

```sql
-- Example 1: [Describe what this query does]
SELECT 
    [Use actual dimension names],
    [Use actual measure names]
FROM [model name]
GROUP BY [dimension]
ORDER BY [measure] DESC
LIMIT 10;
```

```sql
-- Example 2: [Describe what this query does]
[Create another example using different dimensions/measures]
```

### Combining Dimensions and Measures
[Explain which dimensions work well with which measures based on the model]

## Technical Considerations

### Performance Notes
- Aggregation columns: [List the columns used in measures]
- Suggested indexes: [Based on common group by fields]

### Data Types and Constraints
[Only include if explicitly mentioned in the model definition]

## Model Metadata
- Version: {metadata.version if metadata.version else 'Not specified'}
- Created by: {metadata.created_by if metadata.created_by else 'Not specified'}
- Last modified: {metadata.last_modified if metadata.last_modified else 'Not specified'}

IMPORTANT REMINDERS:
- Use ONLY information from the provided model
- Be specific about field names and calculations
- Keep explanations concise and factual
- Do not add governance, security, or operational sections unless defined in the model

Generate the documentation now:"""

        return prompt
    
    def _process_llm_documentation_response(
        self, 
        llm_response: str, 
        model: Dict[str, Any], 
        metadata: DocumentationMetadata
    ) -> str:
        """Process and enhance the LLM response"""
        
        # Clean up the response
        content = llm_response.strip()
        
        # Add metadata header
        header_parts = []
        header_parts.append(f"# {metadata.model_name}")
        
        if metadata.description:
            header_parts.append(f"\n> {metadata.description}")
        
        # Add generation metadata
        header_parts.append(f"\n**Generated:** {datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')}")
        if metadata.version:
            header_parts.append(f"**Version:** {metadata.version}")
        header_parts.append(f"**Documentation Type:** Engineering Guide (LLM-Enhanced)")
        
        # Combine header with LLM content
        final_content = "\n".join(header_parts) + "\n\n---\n\n" + content
        
        # Add footer with additional technical details
        footer_parts = []
        footer_parts.append("\n\n---\n\n## Technical Metadata")
        
        if metadata.relationships:
            footer_parts.append("\n### Model Relationships")
            for rel in metadata.relationships:
                footer_parts.append(f"- **{rel.get('type', 'Unknown')}**: {rel}")
        
        # Add model configuration details
        footer_parts.append(f"\n### Configuration")
        footer_parts.append(f"- **Total Components**: {len(metadata.entities) + len(metadata.measures) + len(metadata.dimensions) + len(metadata.metrics)}")
        footer_parts.append(f"- **Last Updated**: {metadata.last_modified.strftime('%Y-%m-%d') if metadata.last_modified else 'Unknown'}")
        
        return final_content + "\n".join(footer_parts)
    
    def _generate_markdown(
        self,
        model: Dict[str, Any],
        metadata: DocumentationMetadata,
        template: Any,
        config: DocumentationConfig
    ) -> str:
        """Generate Markdown documentation"""
        sections = []
        
        # Title and overview
        sections.append(f"# {metadata.model_name}")
        
        if metadata.description:
            sections.append(f"\n{metadata.description}")
        
        # Metadata section
        if metadata.version or metadata.created_by:
            sections.append("\n## Metadata")
            if metadata.version:
                sections.append(f"- **Version**: {metadata.version}")
            if metadata.created_by:
                sections.append(f"- **Created By**: {metadata.created_by}")
            if metadata.created_at:
                sections.append(f"- **Created At**: {metadata.created_at.strftime('%Y-%m-%d')}")
            if metadata.last_modified:
                sections.append(f"- **Last Modified**: {metadata.last_modified.strftime('%Y-%m-%d')}")
        
        # Generate sections based on template
        for section_name, section_config in sorted(
            template.sections.items(),
            key=lambda x: x[1].get('order', 999)
        ):
            section_content = self._generate_section_markdown(
                section_name,
                section_config,
                model,
                metadata,
                config
            )
            if section_content:
                sections.append(section_content)
        
        # Add custom sections if configured
        if config.custom_sections:
            for section_name, section_data in config.custom_sections.items():
                sections.append(f"\n## {section_name}")
                sections.append(section_data)
        
        return "\n".join(sections)
    
    def _generate_section_markdown(
        self,
        section_name: str,
        section_config: Dict[str, Any],
        model: Dict[str, Any],
        metadata: DocumentationMetadata,
        config: DocumentationConfig
    ) -> Optional[str]:
        """Generate a specific section in Markdown"""
        title = section_config.get('title', section_name.title())
        content = [f"\n## {title}"]
        
        if section_name == 'overview':
            return self._generate_overview_section(metadata, config)
        
        elif section_name == 'entities':
            if not metadata.entities:
                return None
            for entity in metadata.entities:
                content.append(f"\n### {entity['name']}")
                if entity.get('description'):
                    content.append(f"{entity['description']}")
                if config.include_sql and entity.get('sql_table'):
                    content.append(f"- **Table**: `{entity['sql_table']}`")
                if entity.get('primary_key'):
                    content.append(f"- **Primary Key**: `{entity['primary_key']}`")
        
        elif section_name == 'measures':
            if not metadata.measures:
                return None
            for measure in metadata.measures:
                content.append(f"\n### {measure['name']}")
                if measure.get('description'):
                    content.append(f"{measure['description']}")
                content.append(f"- **Type**: {measure.get('type', 'Unknown')}")
                if config.include_sql and measure.get('sql'):
                    content.append(f"- **SQL**: `{measure['sql']}`")
        
        elif section_name == 'dimensions':
            if not metadata.dimensions:
                return None
            for dimension in metadata.dimensions:
                content.append(f"\n### {dimension['name']}")
                if dimension.get('description'):
                    content.append(f"{dimension['description']}")
                content.append(f"- **Type**: {dimension.get('type', 'string')}")
                if config.include_sql and dimension.get('sql'):
                    content.append(f"- **SQL**: `{dimension['sql']}`")
        
        elif section_name == 'metrics':
            if not metadata.metrics:
                return None
            for metric in metadata.metrics:
                content.append(f"\n### {metric['name']}")
                if metric.get('description'):
                    content.append(f"{metric['description']}")
                if metric.get('type'):
                    content.append(f"- **Type**: {metric['type']}")
                if config.include_sql and metric.get('sql'):
                    content.append(f"- **Calculation**: `{metric['sql']}`")
        
        elif section_name == 'lineage' and config.include_lineage:
            return self._generate_lineage_section(model, metadata)
        
        elif section_name == 'examples' and config.include_examples:
            return self._generate_examples_section(model, metadata)
        
        return "\n".join(content) if len(content) > 1 else None
    
    def _generate_overview_section(
        self,
        metadata: DocumentationMetadata,
        config: DocumentationConfig
    ) -> str:
        """Generate overview section"""
        content = ["\n## Overview"]
        
        # Summary statistics
        content.append("\n### Model Statistics")
        content.append(f"- **Entities**: {len(metadata.entities)}")
        content.append(f"- **Measures**: {len(metadata.measures)}")
        content.append(f"- **Dimensions**: {len(metadata.dimensions)}")
        content.append(f"- **Business Metrics**: {len(metadata.metrics)}")
        
        # Business context if available
        if metadata.business_context:
            context = metadata.business_context
            if context.get('business_owner') or context.get('data_steward'):
                content.append("\n### Ownership")
                if context.get('business_owner'):
                    content.append(f"- **Business Owner**: {context['business_owner']}")
                if context.get('data_steward'):
                    content.append(f"- **Data Steward**: {context['data_steward']}")
            
            if context.get('refresh_schedule'):
                content.append(f"\n### Data Refresh")
                content.append(f"- **Schedule**: {context['refresh_schedule']}")
            
            if context.get('common_use_cases'):
                content.append("\n### Common Use Cases")
                for use_case in context['common_use_cases']:
                    content.append(f"- {use_case}")
        
        return "\n".join(content)
    
    def _generate_lineage_section(
        self,
        model: Dict[str, Any],
        metadata: DocumentationMetadata
    ) -> str:
        """Generate data lineage section"""
        content = ["\n## Data Lineage"]
        
        # Source tables
        source_tables = set()
        for entity in metadata.entities:
            if entity.get('source_tables'):
                source_tables.update(entity['source_tables'])
        
        if source_tables:
            content.append("\n### Source Tables")
            for table in sorted(source_tables):
                content.append(f"- `{table}`")
        
        # Dependencies
        if metadata.relationships:
            content.append("\n### Dependencies")
            for rel in metadata.relationships:
                if rel.get('type') == 'metric_dependency':
                    content.append(
                        f"- **{rel['from_metric']}** depends on → "
                        f"`{rel['to_model']}.{rel['to_metric']}`"
                    )
                elif rel.get('type') == 'dimension_join':
                    content.append(
                        f"- **{rel['join_key']}** joins to → "
                        f"`{rel['to_model']}.{rel.get('to_field', rel['join_key'])}`"
                    )
        
        return "\n".join(content)
    
    def _generate_examples_section(
        self,
        model: Dict[str, Any],
        metadata: DocumentationMetadata
    ) -> str:
        """Generate usage examples section"""
        content = ["\n## Usage Examples"]
        
        # Basic query example
        if metadata.measures and metadata.dimensions:
            measure = metadata.measures[0]
            dimension = metadata.dimensions[0]
            
            content.append("\n### Basic Query")
            content.append("```sql")
            content.append("SELECT")
            content.append(f"  {dimension['name']},")
            content.append(f"  {measure['name']}")
            content.append(f"FROM {metadata.model_name}")
            content.append(f"GROUP BY {dimension['name']}")
            content.append("ORDER BY {measure['name']} DESC")
            content.append("LIMIT 10;")
            content.append("```")
        
        # Metric calculation example
        if metadata.metrics:
            metric = metadata.metrics[0]
            content.append("\n### Metric Calculation")
            content.append("```sql")
            content.append("SELECT")
            content.append(f"  {metric['name']}")
            content.append(f"FROM {metadata.model_name}")
            if metric.get('dimensions'):
                content.append(f"GROUP BY {', '.join(metric['dimensions'])}")
            content.append("```")
        
        # Business context examples
        if metadata.business_context and metadata.business_context.get('example_queries'):
            content.append("\n### Business Queries")
            for i, query in enumerate(metadata.business_context['example_queries'], 1):
                content.append(f"\n**Example {i}**: {query.get('description', 'Query')}")
                content.append("```sql")
                content.append(query.get('sql', '-- Query here'))
                content.append("```")
        
        return "\n".join(content)
    
    def _generate_html(
        self,
        model: Dict[str, Any],
        metadata: DocumentationMetadata,
        template: Any,
        config: DocumentationConfig
    ) -> str:
        """Generate HTML documentation"""
        # First generate markdown
        markdown_content = self._generate_markdown(model, metadata, template, config)
        
        # Convert to HTML (simplified - in production use a proper markdown parser)
        html_content = f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{metadata.model_name} Documentation</title>
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            line-height: 1.6;
            max-width: 900px;
            margin: 0 auto;
            padding: 20px;
            color: #333;
        }}
        h1 {{ color: #2c3e50; border-bottom: 2px solid #3498db; padding-bottom: 10px; }}
        h2 {{ color: #34495e; margin-top: 30px; }}
        h3 {{ color: #7f8c8d; }}
        code {{
            background-color: #f4f4f4;
            padding: 2px 4px;
            border-radius: 3px;
            font-family: 'Courier New', Courier, monospace;
        }}
        pre {{
            background-color: #f4f4f4;
            padding: 15px;
            border-radius: 5px;
            overflow-x: auto;
        }}
        .measure, .dimension, .metric {{
            background-color: #ecf0f1;
            padding: 10px;
            margin: 10px 0;
            border-left: 4px solid #3498db;
            border-radius: 4px;
        }}
        .metadata {{
            background-color: #e8f4f8;
            padding: 10px;
            border-radius: 5px;
            margin: 10px 0;
        }}
    </style>
</head>
<body>
    <h1>{metadata.model_name}</h1>
"""
        
        # Convert markdown to HTML (basic conversion)
        lines = markdown_content.split('\n')
        in_code_block = False
        
        for line in lines:
            if line.startswith('```'):
                if in_code_block:
                    html_content += "</pre>\n"
                    in_code_block = False
                else:
                    html_content += "<pre><code>"
                    in_code_block = True
            elif in_code_block:
                html_content += line + "\n"
            elif line.startswith('# '):
                # Skip h1 as we already have it
                continue
            elif line.startswith('## '):
                html_content += f"<h2>{line[3:]}</h2>\n"
            elif line.startswith('### '):
                html_content += f"<h3>{line[4:]}</h3>\n"
            elif line.startswith('- '):
                html_content += f"<li>{line[2:]}</li>\n"
            elif line.strip():
                html_content += f"<p>{line}</p>\n"
        
        html_content += """
</body>
</html>
"""
        return html_content
    
    def _generate_pdf(
        self,
        model: Dict[str, Any],
        metadata: DocumentationMetadata,
        template: Any,
        config: DocumentationConfig
    ) -> bytes:
        """Generate PDF documentation"""
        # For now, return a placeholder
        # In production, use a library like reportlab or weasyprint
        pdf_content = b"PDF documentation generation not yet implemented"
        return pdf_content
    
    def _generate_json(
        self,
        model: Dict[str, Any],
        metadata: DocumentationMetadata,
        template: Any,
        config: DocumentationConfig
    ) -> str:
        """Generate JSON documentation"""
        doc_data = {
            'metadata': {
                'model_name': metadata.model_name,
                'description': metadata.description,
                'version': metadata.version,
                'created_by': metadata.created_by,
                'created_at': metadata.created_at.isoformat() if metadata.created_at else None,
                'generated_at': datetime.utcnow().isoformat(),
                'template': config.template
            },
            'model': model,
            'statistics': {
                'entities': len(metadata.entities),
                'measures': len(metadata.measures),
                'dimensions': len(metadata.dimensions),
                'metrics': len(metadata.metrics)
            },
            'components': {
                'entities': metadata.entities,
                'measures': metadata.measures,
                'dimensions': metadata.dimensions,
                'metrics': metadata.metrics
            }
        }
        
        if config.include_lineage and metadata.relationships:
            doc_data['lineage'] = {
                'relationships': metadata.relationships
            }
        
        if metadata.business_context:
            doc_data['business_context'] = metadata.business_context
        
        return json.dumps(doc_data, indent=2, default=str)
    
    def _generate_filename(self, model_name: str, format: DocumentationFormat) -> str:
        """Generate appropriate filename for documentation"""
        timestamp = datetime.utcnow().strftime('%Y%m%d_%H%M%S')
        extension = {
            DocumentationFormat.MARKDOWN: 'md',
            DocumentationFormat.HTML: 'html',
            DocumentationFormat.PDF: 'pdf',
            DocumentationFormat.DOCX: 'docx',
            DocumentationFormat.RST: 'rst',
            DocumentationFormat.JSON: 'json'
        }.get(format, 'txt')
        
        return f"{model_name}_documentation_{timestamp}.{extension}"
    
    def generate_multi_model_documentation(
        self,
        models: List[Dict[str, Any]],
        config: DocumentationConfig
    ) -> GeneratedDocumentation:
        """
        Generate documentation for multiple related models.
        
        Args:
            models: List of semantic model dictionaries
            config: Documentation configuration
            
        Returns:
            GeneratedDocumentation object
        """
        if config.format == DocumentationFormat.MARKDOWN:
            content = self._generate_multi_model_markdown(models, config)
            content_type = "text/markdown"
        else:
            # For other formats, convert from markdown first
            markdown_content = self._generate_multi_model_markdown(models, config)
            # Convert based on format...
            content = markdown_content
            content_type = "text/plain"
        
        return GeneratedDocumentation(
            format=config.format,
            content=content,
            content_type=content_type,
            metadata={
                'generated_at': datetime.utcnow().isoformat(),
                'model_count': len(models),
                'template': config.template
            },
            filename=f"data_model_documentation_{datetime.utcnow().strftime('%Y%m%d')}.{config.format.value}"
        )
    
    def _generate_multi_model_markdown(
        self,
        models: List[Dict[str, Any]],
        config: DocumentationConfig
    ) -> str:
        """Generate markdown for multiple models"""
        sections = ["# Data Model Documentation"]
        sections.append(f"\nGenerated on: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')}")
        sections.append(f"\nTotal Models: {len(models)}")
        
        # Table of contents
        sections.append("\n## Table of Contents")
        for i, model in enumerate(models, 1):
            model_name = model.get('name', f'Model {i}')
            sections.append(f"{i}. [{model_name}](#{model_name.lower().replace(' ', '-')})")
        
        # Generate documentation for each model
        for model in models:
            metadata = self.metadata_extractor.extract_metadata(model)
            template = self.template_manager.load_template(config.template)
            
            model_doc = self._generate_markdown(model, metadata, template, config)
            sections.append(f"\n---\n{model_doc}")
        
        # Add relationships section if configured
        if config.include_relationships:
            sections.append("\n## Model Relationships")
            all_relationships = []
            for model in models:
                metadata = self.metadata_extractor.extract_metadata(model)
                if metadata.relationships:
                    all_relationships.extend(metadata.relationships)
            
            if all_relationships:
                for rel in all_relationships:
                    sections.append(
                        f"- **{rel['from_model']}** → **{rel['to_model']}** "
                        f"({rel.get('type', 'unknown')})"
                    )
        
        return "\n".join(sections)
