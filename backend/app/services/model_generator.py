"""
Model Generator Service for creating semantic models from analyzed tables.
Converts suggestions into valid YAML semantic models.
"""
import re
import yaml
from typing import List, Dict, Any, Optional
from datetime import datetime
from pathlib import Path
import structlog

from app.models.semantic import (
    GeneratedModel, SuggestedMetric, SuggestedDimension,
    ModelValidationResult, ModelGenerationMetadata,
    ModelCustomization
)


logger = structlog.get_logger()


class ModelGenerator:
    """Service for generating semantic models"""
    
    def __init__(self, models_path: str = "semantic-models"):
        """Initialize with models directory path"""
        self.models_path = Path(models_path)
        self.models_path.mkdir(exist_ok=True)
        
        # Ensure backups directory exists
        self.backups_path = self.models_path / "backups"
        self.backups_path.mkdir(exist_ok=True)
    
    def generate_model(
        self,
        table_name: str,
        schema: str,
        catalog: str,
        suggestions: Dict[str, Any],
        customization: Optional[Dict[str, Any]] = None
    ) -> GeneratedModel:
        """Generate a semantic model from suggestions"""
        logger.info(f"Generating model for {catalog}.{schema}.{table_name}")
        
        # Apply customization if provided
        if customization:
            suggestions = self._apply_customization(suggestions, customization)
        
        # Generate model name
        model_name = self._generate_model_name(table_name, customization)
        
        # Build model reference
        model_ref = f"ref('{catalog}.{schema}.{table_name}')"
        
        # Calculate overall confidence
        all_suggestions = suggestions.get('metrics', []) + suggestions.get('dimensions', [])
        avg_confidence = sum(s.confidence_score for s in all_suggestions if hasattr(s, 'confidence_score')) / len(all_suggestions) if all_suggestions else 0.5
        
        # Create the model
        model = GeneratedModel(
            name=model_name,
            display_name=self._generate_display_name(table_name),
            description=customization.get('description') if customization else f"Semantic model for {table_name}",
            model_ref=model_ref,
            entities=suggestions.get('entities', []),
            dimensions=suggestions.get('dimensions', []),
            measures=self._generate_measures(suggestions.get('metrics', [])),
            metrics=suggestions.get('metrics', []),
            source_table=f"{catalog}.{schema}.{table_name}",
            generation_version="1.0",
            confidence_score=avg_confidence,
            defaults={
                'agg_time_dimension': self._get_primary_time_dimension(suggestions.get('dimensions', []))
            }
        )
        
        return model
    
    def to_yaml(self, model: GeneratedModel) -> str:
        """Convert model to YAML string"""
        yaml_dict = model.to_yaml_dict()
        
        # Custom YAML formatting for better readability
        yaml_str = yaml.dump(yaml_dict, 
                            default_flow_style=False,
                            sort_keys=False,
                            allow_unicode=True,
                            width=120)
        
        # Add header comment
        header = f"""# Semantic Model: {model.name}
# Generated on: {model.generated_at.isoformat()}
# Source table: {model.source_table}
# Generation confidence: {model.confidence_score:.2%}

"""
        
        return header + yaml_str
    
    def validate_model(self, model: GeneratedModel) -> ModelValidationResult:
        """Validate a generated model"""
        result = ModelValidationResult(is_valid=True)
        
        # Check required fields
        if not model.name:
            result.add_error("Model name is required")
        
        if not model.model_ref:
            result.add_error("Model reference is required")
        
        # Check metrics
        if not model.metrics:
            result.add_error("Model must have at least one metric")
        
        # Check dimensions
        if not model.dimensions:
            result.add_warning("Model has no dimensions - consider adding time or categorical dimensions")
        
        # Check entities
        if not model.entities:
            result.add_warning("Model has no entities defined - consider adding primary/foreign keys")
        
        # Validate metric expressions
        for metric in model.metrics:
            if not metric.expression:
                result.add_error(f"Metric '{metric.name}' has no expression")
            
            # Check for SQL injection patterns
            if self._has_dangerous_sql(metric.expression):
                result.add_error(f"Metric '{metric.name}' contains potentially dangerous SQL")
        
        # Validate dimension expressions
        for dim in model.dimensions:
            if not dim.expression:
                result.add_error(f"Dimension '{dim.name}' has no expression")
        
        # Check for duplicate names
        all_names = [m.name for m in model.metrics] + [d.name for d in model.dimensions]
        duplicates = [name for name in all_names if all_names.count(name) > 1]
        if duplicates:
            result.add_error(f"Duplicate names found: {', '.join(set(duplicates))}")
        
        # Add suggestions
        if model.confidence_score < 0.7:
            result.add_suggestion("Low confidence score - consider reviewing and customizing the generated model")
        
        if len(model.metrics) > 20:
            result.add_suggestion("Large number of metrics - consider organizing into multiple models")
        
        time_dims = [d for d in model.dimensions if d.type == 'time']
        if not time_dims:
            result.add_suggestion("No time dimension found - consider adding date fields for time-series analysis")
        
        return result
    
    def save_model(self, model: GeneratedModel, validate: bool = True) -> str:
        """Save model to file"""
        if validate:
            validation = self.validate_model(model)
            if not validation.is_valid:
                raise ValueError(f"Model validation failed: {validation.errors}")
        
        # Generate filename
        filename = f"{model.name}.yml"
        filepath = self.models_path / filename
        
        # Create backup if file exists
        if filepath.exists():
            backup_name = f"{model.name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.yml"
            backup_path = self.backups_path / backup_name
            filepath.rename(backup_path)
            logger.info(f"Created backup: {backup_path}")
        
        # Convert to YAML and save
        yaml_content = self.to_yaml(model)
        filepath.write_text(yaml_content)
        
        logger.info(f"Saved model to: {filepath}")
        return str(filepath)
    
    def generate_metadata(self, model: GeneratedModel) -> ModelGenerationMetadata:
        """Generate metadata for the model"""
        metadata = ModelGenerationMetadata(
            source_table=model.source_table,
            source_catalog=model.source_table.split('.')[0],
            source_schema=model.source_table.split('.')[1],
            confidence_score=model.confidence_score,
            columns_analyzed=len(model.dimensions) + len(model.measures),
            metrics_suggested=len(model.metrics),
            dimensions_suggested=len(model.dimensions),
            additional_info={
                'generation_timestamp': datetime.now().isoformat(),
                'model_version': model.generation_version,
                'has_time_dimension': any(d.type == 'time' for d in model.dimensions),
                'has_derived_metrics': any(m.metric_type == 'derived' for m in model.metrics),
                'primary_entities': [e['name'] for e in model.entities if e.get('type') == 'primary'],
                'statistics': {
                    'total_metrics': len(model.metrics),
                    'total_dimensions': len(model.dimensions),
                    'total_entities': len(model.entities)
                }
            }
        )
        
        # Add generation notes
        if model.confidence_score < 0.7:
            metadata.generation_notes.append("Low confidence - manual review recommended")
        
        if len(model.metrics) > 15:
            metadata.generation_notes.append("Large number of metrics generated - consider splitting")
        
        return metadata
    
    def _apply_customization(self, suggestions: Dict[str, Any], customization: Dict[str, Any]) -> Dict[str, Any]:
        """Apply user customization to suggestions"""
        # Handle both ModelCustomization object and plain dict
        if isinstance(customization, ModelCustomization):
            custom_dict = customization.dict()
        else:
            custom_dict = customization
        
        # Filter out excluded metrics
        excluded_metrics = custom_dict.get('excluded_metrics', [])
        if excluded_metrics and 'metrics' in suggestions:
            suggestions['metrics'] = [
                m for m in suggestions['metrics'] 
                if m.name not in excluded_metrics
            ]
        
        # Apply metric overrides
        metric_overrides = custom_dict.get('metric_overrides', {})
        if metric_overrides and 'metrics' in suggestions:
            for metric in suggestions['metrics']:
                if metric.name in metric_overrides:
                    overrides = metric_overrides[metric.name]
                    for key, value in overrides.items():
                        if hasattr(metric, key):
                            setattr(metric, key, value)
        
        # Add additional metrics
        additional_metrics = custom_dict.get('additional_metrics', [])
        if additional_metrics:
            for metric_dict in additional_metrics:
                metric = SuggestedMetric(**metric_dict)
                suggestions.setdefault('metrics', []).append(metric)
        
        # Filter by minimum confidence score
        min_confidence = custom_dict.get('minimum_confidence_score', 0.0)
        if min_confidence > 0:
            for key in ['metrics', 'dimensions']:
                if key in suggestions:
                    suggestions[key] = [
                        item for item in suggestions[key]
                        if not hasattr(item, 'confidence_score') or item.confidence_score >= min_confidence
                    ]
        
        return suggestions
    
    def _generate_model_name(self, table_name: str, customization: Optional[Dict[str, Any]] = None) -> str:
        """Generate a valid model name"""
        if customization and customization.get('model_name'):
            name = customization['model_name']
        else:
            # Remove common suffixes and clean up
            name = table_name.lower()
            # Keep the full table name for clarity
            name = f"{name}_model"
        
        # Ensure valid identifier
        name = re.sub(r'[^a-z0-9_]', '_', name.lower())
        name = re.sub(r'_+', '_', name).strip('_')
        
        return name
    
    def _generate_display_name(self, table_name: str) -> str:
        """Generate human-readable display name"""
        # Remove underscores and capitalize words
        words = table_name.split('_')
        return ' '.join(word.capitalize() for word in words if word)
    
    def _generate_measures(self, metrics: List[SuggestedMetric]) -> List[Dict[str, Any]]:
        """Generate measure definitions from metrics"""
        measures = []
        seen = set()
        
        for metric in metrics:
            if metric.metric_type == 'simple' and metric.base_column and metric.aggregation:
                measure_name = f"{metric.base_column}_{metric.aggregation}"
                if measure_name not in seen:
                    seen.add(measure_name)
                    measures.append({
                        'name': measure_name,
                        'agg': metric.aggregation,
                        'expr': metric.base_column,
                        'description': f"{metric.aggregation.upper()} of {metric.base_column}"
                    })
        
        return measures
    
    def _get_primary_time_dimension(self, dimensions: List[SuggestedDimension]) -> Optional[str]:
        """Get the primary time dimension for defaults"""
        time_dims = [d for d in dimensions if d.type == 'time']
        if not time_dims:
            return None
        
        # Prefer dimensions with 'date' in the name
        for dim in time_dims:
            if 'date' in dim.name.lower():
                return dim.name
        
        # Otherwise return first time dimension
        return time_dims[0].name
    
    def _has_dangerous_sql(self, expression: str) -> bool:
        """Check for potentially dangerous SQL patterns"""
        dangerous_patterns = [
            r';\s*DROP',
            r';\s*DELETE',
            r';\s*INSERT',
            r';\s*UPDATE',
            r';\s*CREATE',
            r';\s*ALTER',
            r'--',
            r'/\*.*\*/',
            r'EXEC\s*\(',
            r'EXECUTE\s*\('
        ]
        
        expression_upper = expression.upper()
        return any(re.search(pattern, expression_upper) for pattern in dangerous_patterns)
