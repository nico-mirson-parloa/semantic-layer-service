"""
Pydantic models for semantic model creation
"""
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any


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


class SemanticModelYAML(BaseModel):
    """Complete semantic model structure for YAML generation"""
    name: str
    description: str
    model: str = Field(..., description="Base table reference")
    entities: List[Entity] = Field(default_factory=list)
    dimensions: List[Dimension] = Field(default_factory=list)
    measures: List[Measure] = Field(default_factory=list)
    metrics: List[Metric] = Field(default_factory=list)
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict)
