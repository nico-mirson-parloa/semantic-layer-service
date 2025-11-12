"""
Extended semantic model classes for automatic generation.
Includes suggested metrics, dimensions, and generation metadata.
"""
from typing import List, Dict, Any, Optional, Literal
from datetime import datetime
from pydantic import BaseModel, Field, validator
import re


# Legacy model classes for compatibility
class SemanticModel(BaseModel):
    """Legacy semantic model class for existing API compatibility"""
    name: str
    description: Optional[str] = None
    category: Optional[str] = None
    model: str
    entities: List[Dict[str, Any]] = Field(default_factory=list)
    dimensions: List[Dict[str, Any]] = Field(default_factory=list)
    measures: List[Dict[str, Any]] = Field(default_factory=list)
    metrics: List[Dict[str, Any]] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)


class SemanticModelCreate(BaseModel):
    """Request model for creating a semantic model from a metric"""
    name: str = Field(..., description="Name of the semantic model")
    description: str = Field(..., description="Description of the semantic model")
    category: str = Field(..., description="Category/domain of the model")
    metric_name: str = Field(..., description="Name of the metric")
    metric_description: str = Field(..., description="Description of the metric")
    natural_language: str = Field(..., description="Natural language query used")
    sql: str = Field(..., description="Generated SQL")
    conversation_id: Optional[str] = None
    message_id: Optional[str] = None


class AddMetricSQLRequest(BaseModel):
    """Request to add SQL metric to a model"""
    model_name: str
    metric_name: str
    metric_description: str
    sql: str
    natural_language: str
    conversation_id: Optional[str] = None
    message_id: Optional[str] = None


class CacheConfig(BaseModel):
    """Cache configuration for metrics"""
    enabled: bool = True
    ttl_seconds: int = 3600
    refresh_schedule: Optional[str] = None


class GovernanceMetadata(BaseModel):
    """Governance metadata for models"""
    owner: str
    steward: Optional[str] = None
    classification: Optional[str] = None
    tags: List[str] = Field(default_factory=list)
    access_level: str = "public"


class EnhancedSemanticModel(SemanticModel):
    """Enhanced semantic model with additional features"""
    cache_config: Optional[CacheConfig] = None
    governance: Optional[GovernanceMetadata] = None
    lineage: Optional[Dict[str, Any]] = None
    quality_score: Optional[float] = None


# Individual component classes from semantic_model.py
class Entity(BaseModel):
    """Entity definition in a semantic model"""
    name: str
    type: str = Field(..., description="Type of entity: primary, foreign, unique")
    expr: str = Field(..., description="SQL expression for the entity")


class Dimension(BaseModel):
    """Dimension definition in a semantic model"""
    name: str
    type: str = Field(..., description="Type of dimension: time, categorical")
    expr: str = Field(..., description="SQL expression for the dimension")
    time_granularity: Optional[List[str]] = Field(None, description="Available time granularities")


class Measure(BaseModel):
    """Measure definition in a semantic model"""
    name: str
    agg: str = Field(..., description="Aggregation function: sum, avg, count, min, max")
    expr: str = Field(..., description="SQL expression for the measure")
    description: Optional[str] = None


class Metric(BaseModel):
    """Metric definition in a semantic model"""
    name: str
    type: str = Field("simple", description="Type of metric: simple, derived, ratio")
    measure: Optional[str] = Field(None, description="Base measure for simple metrics")
    expr: Optional[str] = Field(None, description="Expression for derived metrics")
    description: Optional[str] = None
    sql: Optional[str] = Field(None, description="Generated SQL for the metric")


class SuggestedMetric(BaseModel):
    """A suggested metric from automatic analysis"""
    name: str = Field(..., description="Metric identifier")
    display_name: str = Field(..., description="Human-readable metric name", alias="displayName")
    base_column: Optional[str] = Field(None, description="Base column for simple metrics", alias="baseColumn")
    aggregation: Optional[str] = Field(None, description="Aggregation function (sum, avg, count, etc.)")
    expression: str = Field(..., description="SQL expression for the metric")
    metric_type: str = Field("simple", description="Metric type: simple, derived, cumulative, ratio", alias="metricType")
    description: Optional[str] = Field(None, description="Metric description")
    category: Optional[str] = Field(None, description="Business category (sales, finance, etc.)")
    confidence_score: float = Field(0.5, ge=0.0, le=1.0, description="Suggestion confidence", alias="confidenceScore")
    requires_time_dimension: bool = Field(False, description="Whether metric needs time dimension", alias="requiresTimeDimension")
    filters: Optional[List[str]] = Field(None, description="Default filters for the metric")
    format: Optional[str] = Field(None, description="Display format (currency, percentage, number)")
    
    class Config:
        populate_by_name = True
        by_alias = True
    
    @validator('name')
    def validate_metric_name(cls, v):
        """Ensure metric name is valid identifier"""
        # Remove special characters and ensure valid SQL identifier
        cleaned = re.sub(r'[^a-zA-Z0-9_]', '_', v)
        if cleaned[0].isdigit():
            cleaned = f"metric_{cleaned}"
        return cleaned.lower()
    
    @validator('aggregation')
    def validate_aggregation(cls, v):
        """Validate aggregation function"""
        valid_aggs = ['sum', 'avg', 'count', 'count_distinct', 'min', 'max', 
                      'stddev', 'variance', 'percentile', 'median']
        if v and v.lower() not in valid_aggs:
            raise ValueError(f"Invalid aggregation: {v}")
        return v.lower() if v else v


class SuggestedDimension(BaseModel):
    """A suggested dimension from automatic analysis"""
    name: str = Field(..., description="Dimension identifier")
    display_name: str = Field(..., description="Human-readable dimension name", alias="displayName")
    type: Literal["time", "categorical", "geographic", "hierarchical"] = Field(..., description="Dimension type")
    expression: str = Field(..., description="SQL expression for the dimension")
    description: Optional[str] = Field(None, description="Dimension description")
    granularities: Optional[List[str]] = Field(None, description="Available granularities for time dimensions")
    hierarchy: Optional[List[str]] = Field(None, description="Hierarchy levels for hierarchical dimensions")
    cardinality: Optional[int] = Field(None, description="Estimated number of distinct values")
    sample_values: Optional[List[str]] = Field(None, description="Sample dimension values", alias="sampleValues")
    
    class Config:
        populate_by_name = True
        by_alias = True
    
    @validator('name')
    def validate_dimension_name(cls, v):
        """Ensure dimension name is valid identifier"""
        cleaned = re.sub(r'[^a-zA-Z0-9_]', '_', v)
        if cleaned[0].isdigit():
            cleaned = f"dim_{cleaned}"
        return cleaned.lower()
    
    @validator('granularities')
    def validate_granularities(cls, v, values):
        """Validate time granularities"""
        if values.get('type') == 'time' and v:
            valid_granularities = ['second', 'minute', 'hour', 'day', 'week', 
                                  'month', 'quarter', 'year']
            invalid = [g for g in v if g not in valid_granularities]
            if invalid:
                raise ValueError(f"Invalid granularities: {invalid}")
        return v


class GeneratedModel(BaseModel):
    """A complete generated semantic model"""
    name: str = Field(..., description="Model name")
    display_name: Optional[str] = Field(None, description="Human-readable model name")
    description: Optional[str] = Field(None, description="Model description")
    model_ref: str = Field(..., description="Reference to source table")
    
    # Model components
    entities: List[Dict[str, Any]] = Field(default_factory=list, description="Entity definitions")
    dimensions: List[SuggestedDimension] = Field(default_factory=list, description="Dimension definitions")
    measures: List[Dict[str, Any]] = Field(default_factory=list, description="Measure definitions")
    metrics: List[SuggestedMetric] = Field(default_factory=list, description="Metric definitions")
    
    # Metadata
    source_table: str = Field(..., description="Source table full name")
    generated_at: datetime = Field(default_factory=datetime.now)
    generation_version: str = Field("1.0", description="Generation algorithm version")
    confidence_score: float = Field(0.0, ge=0.0, le=1.0, description="Overall model confidence")
    
    # Additional configurations
    defaults: Optional[Dict[str, Any]] = Field(None, description="Default configurations")
    validations: Optional[List[Dict[str, Any]]] = Field(None, description="Validation rules")
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat() if v else None
        }
    
    def to_yaml_dict(self) -> Dict[str, Any]:
        """Convert to dictionary suitable for YAML serialization"""
        yaml_dict = {
            'semantic_model': {
                'name': self.name,
                'description': self.description,
                'model': self.model_ref,
                'defaults': self.defaults or {
                    'agg_time_dimension': 'order_date'
                }
            }
        }
        
        # Add entities
        if self.entities:
            yaml_dict['semantic_model']['entities'] = self.entities
        
        # Add dimensions
        if self.dimensions:
            yaml_dict['semantic_model']['dimensions'] = [
                {
                    'name': d.name,
                    'type': d.type,
                    'expr': d.expression,
                    'description': d.description
                } for d in self.dimensions
            ]
            
            # Add time granularities
            for dim in self.dimensions:
                if dim.type == 'time' and dim.granularities:
                    dim_entry = next(d for d in yaml_dict['semantic_model']['dimensions'] 
                                   if d['name'] == dim.name)
                    dim_entry['type_params'] = {
                        'time_granularity': dim.granularities
                    }
        
        # Add measures
        if self.measures:
            yaml_dict['semantic_model']['measures'] = self.measures
        
        # Add metrics
        if self.metrics:
            yaml_dict['metrics'] = [
                {
                    'name': m.name,
                    'description': m.description,
                    'type': m.metric_type,
                    'type_params': {
                        'measure': {
                            'name': m.base_column,
                            'agg': m.aggregation
                        } if m.metric_type == 'simple' else None,
                        'expr': m.expression if m.metric_type == 'derived' else None
                    },
                    'filter': m.filters[0] if m.filters else None
                } for m in self.metrics
            ]
            
            # Clean up None values in type_params
            for metric in yaml_dict['metrics']:
                if 'type_params' in metric:
                    metric['type_params'] = {k: v for k, v in metric['type_params'].items() if v is not None}
        
        return yaml_dict


class ModelValidationResult(BaseModel):
    """Result of semantic model validation"""
    is_valid: bool = Field(alias="isValid")
    errors: List[str] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)
    suggestions: List[str] = Field(default_factory=list)
    validated_at: datetime = Field(default_factory=datetime.now, alias="validatedAt")
    
    class Config:
        populate_by_name = True
        by_alias = True
    
    def add_error(self, error: str):
        """Add validation error"""
        self.errors.append(error)
        self.is_valid = False
    
    def add_warning(self, warning: str):
        """Add validation warning"""
        self.warnings.append(warning)
    
    def add_suggestion(self, suggestion: str):
        """Add improvement suggestion"""
        self.suggestions.append(suggestion)


class ModelGenerationMetadata(BaseModel):
    """Metadata about the model generation process"""
    created_by: str = Field("automatic_generator", description="Generation method")
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: Optional[datetime] = None
    source_table: str = Field(..., description="Source table full name")
    source_catalog: str = Field(..., description="Source catalog")
    source_schema: str = Field(..., description="Source schema")
    generation_version: str = Field("1.0", description="Generator version")
    confidence_score: float = Field(0.0, ge=0.0, le=1.0)
    
    # Statistics
    table_row_count: Optional[int] = None
    table_size_mb: Optional[float] = None
    columns_analyzed: int = 0
    metrics_suggested: int = 0
    dimensions_suggested: int = 0
    
    # Additional info
    additional_info: Dict[str, Any] = Field(default_factory=dict)
    generation_notes: List[str] = Field(default_factory=list)
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat() if v else None
        }


class ModelCustomization(BaseModel):
    """Customization options for model generation"""
    model_name: Optional[str] = None
    description: Optional[str] = None
    excluded_metrics: List[str] = Field(default_factory=list)
    excluded_dimensions: List[str] = Field(default_factory=list)
    excluded_columns: List[str] = Field(default_factory=list)
    
    metric_overrides: Dict[str, Dict[str, Any]] = Field(default_factory=dict)
    dimension_overrides: Dict[str, Dict[str, Any]] = Field(default_factory=dict)
    
    additional_metrics: List[Dict[str, Any]] = Field(default_factory=list)
    additional_dimensions: List[Dict[str, Any]] = Field(default_factory=list)
    
    # Generation preferences
    prefer_simple_metrics: bool = True
    include_derived_metrics: bool = True
    include_time_intelligence: bool = True
    minimum_confidence_score: float = Field(0.7, ge=0.0, le=1.0)
    
    # Naming conventions
    metric_prefix: Optional[str] = None
    metric_suffix: Optional[str] = None
    dimension_prefix: Optional[str] = None
    dimension_suffix: Optional[str] = None


class AnalysisResult(BaseModel):
    """Complete result of table analysis"""
    table_analysis: Dict[str, Any] = Field(alias="tableAnalysis")
    suggested_metrics: List[SuggestedMetric] = Field(alias="suggestedMetrics")
    suggested_dimensions: List[SuggestedDimension] = Field(alias="suggestedDimensions")
    suggested_entities: List[Dict[str, Any]] = Field(alias="suggestedEntities")
    suggested_measures: List[Dict[str, Any]] = Field(alias="suggestedMeasures")
    
    confidence_scores: Dict[str, float] = Field(default_factory=dict, alias="confidenceScores")
    analysis_notes: List[str] = Field(default_factory=list, alias="analysisNotes")
    warnings: List[str] = Field(default_factory=list)
    
    # Lineage information (optional)
    lineage: Optional[Dict[str, Any]] = None
    
    # Statistics
    total_suggestions: int = Field(0, alias="totalSuggestions")
    high_confidence_suggestions: int = Field(0, alias="highConfidenceSuggestions")
    
    class Config:
        populate_by_name = True
        by_alias = True
    
    def calculate_statistics(self):
        """Calculate suggestion statistics"""
        all_suggestions = self.suggested_metrics + self.suggested_dimensions
        self.total_suggestions = len(all_suggestions)
        self.high_confidence_suggestions = sum(
            1 for s in all_suggestions 
            if hasattr(s, 'confidence_score') and s.confidence_score >= 0.8
        )


class GeneratedModelResponse(BaseModel):
    """Response from model generation endpoint"""
    success: bool
    model_id: Optional[str] = Field(None, alias="modelId")
    model_name: Optional[str] = Field(None, alias="modelName")
    yaml_content: Optional[str] = Field(None, alias="yamlContent")
    json_content: Optional[Dict[str, Any]] = Field(None, alias="jsonContent")
    validation_result: Optional[ModelValidationResult] = Field(None, alias="validationResult")
    metadata: Optional[ModelGenerationMetadata] = None
    file_path: Optional[str] = Field(None, alias="filePath")
    errors: List[str] = Field(default_factory=list)
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat() if v else None
        }
        populate_by_name = True
        by_alias = True