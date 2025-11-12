"""
Pydantic models for Databricks Genie integration
"""
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any


class NaturalLanguageQuery(BaseModel):
    """Request model for natural language to SQL conversion"""
    query: str = Field(..., description="Natural language query")
    catalog: Optional[str] = Field(None, description="Target catalog")
    schema: Optional[str] = Field(None, description="Target schema")
    table: Optional[str] = Field(None, description="Target table")
    time_grain: Optional[str] = Field(None, description="Time granularity (day, week, month, etc.)")
    space_id: Optional[str] = Field(None, description="Existing Genie space ID")
    validate: Optional[bool] = Field(False, description="If true, run EXPLAIN to validate SQL (no data)")


class GenieResponse(BaseModel):
    """Response from Genie API"""
    sql: str = Field(..., description="Generated SQL query")
    explanation: str = Field("", description="Explanation of the generated SQL")
    confidence: float = Field(0.8, description="Confidence score (0-1)")
    conversation_id: Optional[str] = Field(None, description="Conversation ID for refinement")
    space_id: Optional[str] = Field(None, description="Genie space ID")
    message_id: Optional[str] = Field(None, description="Message ID for retrieving full query details")
    success: bool = Field(True, description="Whether the generation was successful")
    error: Optional[str] = Field(None, description="Error message if failed")


class MetricSuggestion(BaseModel):
    """Suggested metric from Genie"""
    name: str = Field(..., description="Metric name")
    description: str = Field(..., description="Metric description")
    natural_language_query: str = Field(..., description="Natural language to calculate metric")


class NaturalLanguageMetric(BaseModel):
    """Metric defined using natural language"""
    name: str = Field(..., description="Metric name")
    description: str = Field(..., description="Business description")
    natural_language: str = Field(..., description="Natural language definition")
    category: Optional[str] = Field("General", description="Metric category")


class NaturalLanguageDimension(BaseModel):
    """Dimension defined using natural language"""
    name: str = Field(..., description="Dimension name")
    description: str = Field(..., description="Business description")
    natural_language: str = Field(..., description="Natural language definition")
    time_grains: Optional[List[str]] = Field(None, description="Available time grains if time dimension")


class SemanticModelNL(BaseModel):
    """Complete semantic model using natural language definitions"""
    name: str = Field(..., description="Model name")
    description: str = Field(..., description="Model description")
    catalog: str = Field(..., description="Databricks catalog")
    schema: str = Field(..., description="Databricks schema")
    base_table: str = Field(..., description="Base table name")
    dimensions: Optional[List[NaturalLanguageDimension]] = Field(default_factory=list)
    metrics: List[NaturalLanguageMetric] = Field(..., description="List of metrics")


class MetricQueryRequest(BaseModel):
    """Request to query metrics using natural language"""
    query: str = Field(..., description="Natural language metric query")
    model_name: str = Field(..., description="Semantic model to use")
    filters: Optional[Dict[str, Any]] = Field(None, description="Additional filters")
    limit: int = Field(100, description="Result limit")


class MetricQueryResponse(BaseModel):
    """Response from metric query"""
    query: str = Field(..., description="Original query")
    generated_sql: str = Field(..., description="Generated SQL")
    results: List[Dict[str, Any]] = Field(..., description="Query results")
    row_count: int = Field(..., description="Number of rows returned")
    execution_time_ms: float = Field(..., description="Execution time in milliseconds")
