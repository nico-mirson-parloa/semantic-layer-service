"""
Service for managing documentation templates.
"""

from typing import Dict, List, Optional, Any
import json
import logging
from pathlib import Path

from app.models.documentation import DocumentationTemplate


logger = logging.getLogger(__name__)


class TemplateManager:
    """Manage documentation templates"""
    
    def __init__(self, template_dir: Optional[Path] = None):
        """
        Initialize template manager.
        
        Args:
            template_dir: Directory containing custom templates
        """
        self.template_dir = template_dir or Path(__file__).parent / "templates"
        self._templates: Dict[str, DocumentationTemplate] = {}
        self._load_default_templates()
    
    def _load_default_templates(self):
        """Load default documentation templates"""
        # Standard template - balanced for all audiences
        self._templates['standard'] = DocumentationTemplate(
            name='standard',
            description='Standard documentation template suitable for most use cases',
            sections={
                'overview': {
                    'title': 'Overview',
                    'include': ['description', 'version', 'owner', 'last_updated'],
                    'order': 1
                },
                'entities': {
                    'title': 'Data Sources',
                    'include': ['name', 'description', 'sql_table', 'update_frequency'],
                    'order': 2
                },
                'measures': {
                    'title': 'Measures',
                    'include': ['name', 'description', 'type', 'sql'],
                    'order': 3
                },
                'dimensions': {
                    'title': 'Dimensions',
                    'include': ['name', 'description', 'type'],
                    'order': 4
                },
                'metrics': {
                    'title': 'Business Metrics',
                    'include': ['name', 'description', 'calculation'],
                    'order': 5
                },
                'examples': {
                    'title': 'Usage Examples',
                    'include': ['common_queries', 'typical_filters'],
                    'order': 6
                }
            }
        )
        
        # Technical template - for data engineers and developers
        self._templates['technical'] = DocumentationTemplate(
            name='technical',
            description='Technical documentation with implementation details',
            sections={
                'overview': {
                    'title': 'Technical Overview',
                    'include': ['description', 'version', 'schema_version', 'dependencies'],
                    'order': 1
                },
                'architecture': {
                    'title': 'Architecture',
                    'include': ['data_flow', 'processing_steps', 'optimization'],
                    'order': 2
                },
                'entities': {
                    'title': 'Entity Definitions',
                    'include': ['name', 'sql_table', 'primary_key', 'indexes', 'partitions'],
                    'show_sql': True,
                    'order': 3
                },
                'measures': {
                    'title': 'Measure Specifications',
                    'include': ['name', 'sql', 'type', 'aggregation', 'filters'],
                    'show_sql': True,
                    'order': 4
                },
                'dimensions': {
                    'title': 'Dimension Specifications',
                    'include': ['name', 'sql', 'type', 'cardinality', 'joins'],
                    'show_sql': True,
                    'order': 5
                },
                'metrics': {
                    'title': 'Calculated Metrics',
                    'include': ['name', 'sql', 'dependencies', 'performance_notes'],
                    'show_sql': True,
                    'order': 6
                },
                'lineage': {
                    'title': 'Data Lineage',
                    'include': ['source_tables', 'transformations', 'dependencies'],
                    'order': 7
                },
                'performance': {
                    'title': 'Performance Considerations',
                    'include': ['query_patterns', 'optimization_hints', 'cache_config'],
                    'order': 8
                }
            }
        )
        
        # Business template - for business users and analysts
        self._templates['business'] = DocumentationTemplate(
            name='business',
            description='Business-focused documentation without technical details',
            sections={
                'summary': {
                    'title': 'Business Summary',
                    'include': ['description', 'business_purpose', 'key_insights'],
                    'order': 1
                },
                'metrics': {
                    'title': 'Key Performance Indicators',
                    'include': ['name', 'description', 'business_meaning', 'typical_values'],
                    'order': 2
                },
                'dimensions': {
                    'title': 'Analysis Dimensions',
                    'include': ['name', 'description', 'business_examples'],
                    'order': 3
                },
                'use_cases': {
                    'title': 'Common Use Cases',
                    'include': ['scenario', 'questions_answered', 'example_insights'],
                    'order': 4
                },
                'glossary': {
                    'title': 'Business Glossary',
                    'include': ['term_definitions', 'acronyms'],
                    'order': 5
                },
                'contacts': {
                    'title': 'Contacts',
                    'include': ['business_owner', 'data_steward', 'support_team'],
                    'order': 6
                }
            }
        )
        
        # Executive template - high-level summary
        self._templates['executive'] = DocumentationTemplate(
            name='executive',
            description='Executive summary with key metrics and insights',
            sections={
                'executive_summary': {
                    'title': 'Executive Summary',
                    'include': ['purpose', 'key_metrics', 'business_value'],
                    'order': 1
                },
                'kpis': {
                    'title': 'Key Performance Indicators',
                    'include': ['metric_name', 'current_value', 'trend', 'target'],
                    'format': 'dashboard',
                    'order': 2
                },
                'insights': {
                    'title': 'Key Insights',
                    'include': ['insight', 'impact', 'recommendation'],
                    'order': 3
                },
                'roi': {
                    'title': 'Business Value',
                    'include': ['cost_savings', 'efficiency_gains', 'decision_impact'],
                    'order': 4
                }
            }
        )
    
    def get_available_templates(self) -> Dict[str, DocumentationTemplate]:
        """
        Get all available documentation templates.
        
        Returns:
            Dictionary of template name to DocumentationTemplate
        """
        return self._templates.copy()
    
    def load_template(self, template_name: str) -> DocumentationTemplate:
        """
        Load a specific documentation template.
        
        Args:
            template_name: Name of the template to load
            
        Returns:
            DocumentationTemplate object
            
        Raises:
            ValueError: If template not found
        """
        if template_name not in self._templates:
            # Try to load from file if not in memory
            template_file = self.template_dir / f"{template_name}.json"
            if template_file.exists():
                try:
                    with open(template_file, 'r') as f:
                        template_data = json.load(f)
                    template = DocumentationTemplate(**template_data)
                    self._templates[template_name] = template
                    return template
                except Exception as e:
                    logger.error(f"Error loading template {template_name}: {str(e)}")
                    raise ValueError(f"Failed to load template: {template_name}")
            else:
                raise ValueError(f"Template not found: {template_name}")
        
        return self._templates[template_name]
    
    def create_custom_template(
        self,
        name: str,
        sections: Dict[str, Dict[str, Any]],
        description: Optional[str] = None,
        styles: Optional[Dict[str, Any]] = None
    ) -> DocumentationTemplate:
        """
        Create a custom documentation template.
        
        Args:
            name: Template name
            sections: Section configuration
            description: Template description
            styles: Styling configuration
            
        Returns:
            Created DocumentationTemplate
        """
        template = DocumentationTemplate(
            name=name,
            description=description or f"Custom template: {name}",
            sections=sections,
            styles=styles
        )
        
        # Validate sections
        for section_name, section_config in sections.items():
            if 'title' not in section_config:
                section_config['title'] = section_name.replace('_', ' ').title()
            if 'order' not in section_config:
                section_config['order'] = len(sections)
        
        # Save to templates
        self._templates[name] = template
        
        # Optionally persist to file
        try:
            template_file = self.template_dir / f"{name}.json"
            template_file.parent.mkdir(parents=True, exist_ok=True)
            with open(template_file, 'w') as f:
                json.dump(template.model_dump(), f, indent=2)
        except Exception as e:
            logger.warning(f"Could not save custom template to file: {str(e)}")
        
        return template
    
    def get_template_sections(self, template_name: str) -> List[str]:
        """
        Get list of sections in a template.
        
        Args:
            template_name: Name of the template
            
        Returns:
            List of section names in order
        """
        template = self.load_template(template_name)
        sections = sorted(
            template.sections.items(),
            key=lambda x: x[1].get('order', 999)
        )
        return [name for name, _ in sections]
    
    def merge_templates(
        self,
        base_template: str,
        override_sections: Dict[str, Dict[str, Any]]
    ) -> DocumentationTemplate:
        """
        Merge custom sections with a base template.
        
        Args:
            base_template: Name of base template
            override_sections: Sections to override or add
            
        Returns:
            Merged DocumentationTemplate
        """
        base = self.load_template(base_template)
        
        # Create merged sections
        merged_sections = base.sections.copy()
        merged_sections.update(override_sections)
        
        # Re-order sections if needed
        max_order = max(
            section.get('order', 0) 
            for section in merged_sections.values()
        )
        
        for section_name, section_config in override_sections.items():
            if 'order' not in section_config:
                max_order += 1
                section_config['order'] = max_order
        
        return DocumentationTemplate(
            name=f"{base_template}_custom",
            description=f"Customized {base_template} template",
            sections=merged_sections,
            styles=base.styles
        )

