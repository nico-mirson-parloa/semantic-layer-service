"""
Service for extracting metadata from semantic models for documentation.
"""

from typing import Dict, List, Any, Optional
from datetime import datetime
import logging

from app.models.documentation import DocumentationMetadata


logger = logging.getLogger(__name__)


class MetadataExtractor:
    """Extract metadata from semantic models for documentation generation"""
    
    def extract_metadata(self, model: Dict[str, Any]) -> DocumentationMetadata:
        """
        Extract comprehensive metadata from a semantic model.
        
        Args:
            model: Semantic model dictionary
            
        Returns:
            DocumentationMetadata object
        """
        try:
            # Handle nested semantic_model structure
            if 'semantic_model' in model:
                semantic_model = model['semantic_model']
            else:
                semantic_model = model
            
            # Extract basic information
            metadata = DocumentationMetadata(
                model_name=semantic_model.get('name', 'Unnamed Model'),
                description=semantic_model.get('description'),
                version=semantic_model.get('version', '1.0.0'),
                created_by=semantic_model.get('created_by') or semantic_model.get('meta', {}).get('created_by'),
                entities=self._extract_entities(semantic_model),
                measures=self._extract_measures(semantic_model),
                dimensions=self._extract_dimensions(semantic_model),
                metrics=self._extract_metrics(semantic_model)
            )
            
            # Extract timestamps
            if 'created_at' in model:
                metadata.created_at = self._parse_timestamp(model['created_at'])
            elif 'created_at' in semantic_model:
                metadata.created_at = self._parse_timestamp(semantic_model['created_at'])
                
            if 'last_modified' in model or 'updated_at' in model:
                metadata.last_modified = self._parse_timestamp(
                    model.get('last_modified') or model.get('updated_at')
                )
            elif 'last_modified' in semantic_model or 'updated_at' in semantic_model:
                metadata.last_modified = self._parse_timestamp(
                    semantic_model.get('last_modified') or semantic_model.get('updated_at')
                )
            
            # Extract business context
            metadata.business_context = self.extract_business_context(semantic_model)
            
            # Extract relationships
            metadata.relationships = self.extract_relationships(semantic_model)
            
            return metadata
            
        except Exception as e:
            logger.error(f"Error extracting metadata: {str(e)}")
            # Return minimal metadata on error
            # Try to get name from nested structure
            if 'semantic_model' in model and 'name' in model['semantic_model']:
                fallback_name = model['semantic_model']['name']
            else:
                fallback_name = model.get('name', 'Unknown')
                
            return DocumentationMetadata(
                model_name=fallback_name,
                entities=[],
                measures=[],
                dimensions=[],
                metrics=[]
            )
    
    def _extract_entities(self, model: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Extract entity information from model"""
        entities = model.get('entities', [])
        extracted = []
        
        for entity in entities:
            entity_info = {
                'name': entity.get('name'),
                'description': entity.get('description'),
                'sql_table': entity.get('sql_table'),
                'primary_key': entity.get('primary_key')
            }
            
            # Add additional metadata if present
            if 'meta' in entity:
                entity_info['source_tables'] = entity['meta'].get('source_tables', [])
                entity_info['update_frequency'] = entity['meta'].get('update_frequency')
                entity_info['row_count'] = entity['meta'].get('row_count')
            
            extracted.append(entity_info)
        
        return extracted
    
    def _extract_measures(self, model: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Extract measure information from model"""
        measures = model.get('measures', [])
        extracted = []
        
        for measure in measures:
            measure_info = {
                'name': measure.get('name'),
                'description': measure.get('description'),
                'sql': measure.get('sql'),
                'type': measure.get('type'),
                'format': measure.get('format')
            }
            
            # Add aggregation details
            if 'aggregation' in measure:
                measure_info['aggregation'] = measure['aggregation']
            
            # Add filters if present
            if 'filters' in measure:
                measure_info['filters'] = measure['filters']
            
            extracted.append(measure_info)
        
        return extracted
    
    def _extract_dimensions(self, model: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Extract dimension information from model"""
        dimensions = model.get('dimensions', [])
        extracted = []
        
        for dimension in dimensions:
            dim_info = {
                'name': dimension.get('name'),
                'description': dimension.get('description'),
                'sql': dimension.get('sql'),
                'type': dimension.get('type')
            }
            
            # Add time dimension specific info
            if dimension.get('type') == 'time':
                dim_info['time_granularities'] = dimension.get('time_granularities', [])
            
            # Add relationship information
            if 'meta' in dimension and 'joins_to' in dimension['meta']:
                dim_info['joins_to'] = dimension['meta']['joins_to']
            
            extracted.append(dim_info)
        
        return extracted
    
    def _extract_metrics(self, model: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Extract metric information from model"""
        metrics = model.get('metrics', [])
        extracted = []
        
        for metric in metrics:
            metric_info = {
                'name': metric.get('name'),
                'description': metric.get('description'),
                'type': metric.get('type'),
                'sql': metric.get('sql')
            }
            
            # Add metric-specific details
            if 'dimensions' in metric:
                metric_info['dimensions'] = metric['dimensions']
            if 'filters' in metric:
                metric_info['filters'] = metric['filters']
            if 'time_grains' in metric:
                metric_info['time_grains'] = metric['time_grains']
            
            # Add calculation details for derived metrics
            if metric.get('type') == 'derived':
                metric_info['calculation'] = metric.get('calculation')
                metric_info['depends_on'] = metric.get('depends_on', [])
            
            extracted.append(metric_info)
        
        return extracted
    
    def extract_relationships(self, model: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Extract model relationships and dependencies.
        
        Args:
            model: Semantic model dictionary
            
        Returns:
            List of relationship dictionaries
        """
        relationships = []
        
        # Extract dimension-based relationships
        for dimension in model.get('dimensions', []):
            if 'meta' in dimension and 'joins_to' in dimension['meta']:
                join_info = dimension['meta']['joins_to']
                if '.' in join_info:
                    to_model, to_field = join_info.split('.', 1)
                    relationships.append({
                        'from_model': model.get('name'),
                        'to_model': to_model,
                        'join_key': dimension['name'],
                        'to_field': to_field,
                        'type': 'dimension_join'
                    })
        
        # Extract entity-based relationships
        for entity in model.get('entities', []):
            if 'meta' in entity and 'foreign_keys' in entity['meta']:
                for fk in entity['meta']['foreign_keys']:
                    relationships.append({
                        'from_model': model.get('name'),
                        'to_model': fk.get('references_model'),
                        'from_field': fk.get('column'),
                        'to_field': fk.get('references_column'),
                        'type': 'foreign_key'
                    })
        
        # Extract metric dependencies
        for metric in model.get('metrics', []):
            if 'depends_on' in metric:
                for dependency in metric['depends_on']:
                    if '.' in dependency:
                        dep_model, dep_metric = dependency.split('.', 1)
                        relationships.append({
                            'from_model': model.get('name'),
                            'to_model': dep_model,
                            'from_metric': metric['name'],
                            'to_metric': dep_metric,
                            'type': 'metric_dependency'
                        })
        
        return relationships
    
    def extract_business_context(self, model: Dict[str, Any]) -> Dict[str, Any]:
        """
        Extract business context and usage information.
        
        Args:
            model: Semantic model dictionary
            
        Returns:
            Dictionary containing business context
        """
        context = {}
        
        # Extract from model metadata
        meta = model.get('meta', {})
        
        # Business ownership
        context['business_owner'] = meta.get('business_owner')
        context['data_steward'] = meta.get('data_steward')
        context['contact_email'] = meta.get('contact_email')
        
        # Data quality and governance
        context['data_quality_checks'] = meta.get('data_quality_checks', [])
        context['sla'] = meta.get('sla')
        context['refresh_schedule'] = meta.get('refresh_schedule')
        
        # Usage patterns
        context['common_use_cases'] = meta.get('common_use_cases', [])
        context['example_queries'] = meta.get('example_queries', [])
        context['typical_filters'] = meta.get('typical_filters', [])
        
        # Access and security
        context['access_level'] = meta.get('access_level', 'general')
        context['required_permissions'] = meta.get('required_permissions', [])
        context['pii_fields'] = meta.get('pii_fields', [])
        
        # Performance considerations
        context['estimated_query_time'] = meta.get('estimated_query_time')
        context['optimization_hints'] = meta.get('optimization_hints', [])
        
        # Tags and categories
        context['tags'] = meta.get('tags', [])
        context['categories'] = meta.get('categories', [])
        
        # Remove None values
        context = {k: v for k, v in context.items() if v is not None}
        
        return context
    
    def _parse_timestamp(self, timestamp: Any) -> Optional[datetime]:
        """Parse various timestamp formats"""
        if isinstance(timestamp, datetime):
            return timestamp
        
        if isinstance(timestamp, str):
            try:
                # Try ISO format first
                return datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
            except:
                try:
                    # Try common format
                    return datetime.strptime(timestamp, '%Y-%m-%d %H:%M:%S')
                except:
                    logger.warning(f"Could not parse timestamp: {timestamp}")
                    return None
        
        return None
