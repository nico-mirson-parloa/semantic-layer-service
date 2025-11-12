"""
Data models for lineage visualization feature.
Represents lineage graphs, nodes, edges, and metadata.
"""

from enum import Enum
from typing import List, Dict, Any, Optional
from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict


class NodeType(str, Enum):
    """Types of nodes in lineage graph"""
    TABLE = "TABLE"
    VIEW = "VIEW"
    MODEL = "MODEL"
    METRIC = "METRIC"
    DIMENSION = "DIMENSION"
    COLUMN = "COLUMN"
    FILE = "FILE"
    EXTERNAL = "EXTERNAL"
    UNKNOWN = "UNKNOWN"


class EdgeType(str, Enum):
    """Types of relationships between nodes"""
    DERIVES_FROM = "DERIVES_FROM"
    JOINS_WITH = "JOINS_WITH"
    FILTERS_FROM = "FILTERS_FROM"
    AGGREGATES_FROM = "AGGREGATES_FROM"
    REFERENCES = "REFERENCES"
    CONTAINS = "CONTAINS"
    TRANSFORMS_TO = "TRANSFORMS_TO"
    BELONGS_TO = "BELONGS_TO"


class LineageDirection(str, Enum):
    """Direction of lineage traversal"""
    UPSTREAM = "upstream"
    DOWNSTREAM = "downstream"
    BOTH = "both"


class LineageNode(BaseModel):
    """Represents a node in the lineage graph"""
    id: str = Field(..., description="Unique identifier for the node")
    name: str = Field(..., description="Display name of the node")
    type: NodeType = Field(..., description="Type of the node")
    catalog: Optional[str] = Field(None, description="Databricks catalog name")
    schema: Optional[str] = Field(None, description="Schema/database name")
    description: Optional[str] = Field(None, description="Node description")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")
    
    # Visualization properties
    x: Optional[float] = Field(None, description="X coordinate for visualization")
    y: Optional[float] = Field(None, description="Y coordinate for visualization")
    color: Optional[str] = Field(None, description="Color for visualization")
    icon: Optional[str] = Field(None, description="Icon identifier")
    
    model_config = ConfigDict(
        populate_by_name=True,
        use_enum_values=True
    )


class LineageEdge(BaseModel):
    """Represents an edge/relationship in the lineage graph"""
    id: str = Field(..., description="Unique identifier for the edge")
    source: str = Field(..., description="Source node ID")
    target: str = Field(..., description="Target node ID")
    type: EdgeType = Field(..., description="Type of relationship")
    label: Optional[str] = Field(None, description="Display label for the edge")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")
    
    # Visualization properties
    style: Optional[str] = Field(None, description="Line style (solid, dashed, dotted)")
    color: Optional[str] = Field(None, description="Edge color")
    weight: Optional[float] = Field(1.0, description="Edge weight for layout algorithms")
    
    model_config = ConfigDict(
        populate_by_name=True,
        use_enum_values=True
    )


class LineageGraph(BaseModel):
    """Complete lineage graph with nodes and edges"""
    nodes: List[LineageNode] = Field(default_factory=list, description="List of nodes")
    edges: List[LineageEdge] = Field(default_factory=list, description="List of edges")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Graph metadata")
    
    # Graph properties
    layout_algorithm: Optional[str] = Field("hierarchical", description="Layout algorithm used")
    direction: Optional[str] = Field("LR", description="Graph direction (LR, TB, etc.)")
    
    def get_node_by_id(self, node_id: str) -> Optional[LineageNode]:
        """Get a node by its ID"""
        for node in self.nodes:
            if node.id == node_id:
                return node
        return None
    
    def get_edges_from_node(self, node_id: str) -> List[LineageEdge]:
        """Get all edges originating from a node"""
        return [edge for edge in self.edges if edge.source == node_id]
    
    def get_edges_to_node(self, node_id: str) -> List[LineageEdge]:
        """Get all edges pointing to a node"""
        return [edge for edge in self.edges if edge.target == node_id]
    
    model_config = ConfigDict(
        populate_by_name=True
    )


class LineageRequest(BaseModel):
    """Request model for lineage extraction"""
    entity_type: str = Field(..., description="Type of entity (table, model, etc.)")
    entity_id: Optional[str] = Field(None, description="Entity identifier")
    catalog: Optional[str] = Field(None, description="Catalog name for tables")
    schema: Optional[str] = Field(None, description="Schema name for tables")
    table: Optional[str] = Field(None, description="Table name")
    direction: LineageDirection = Field(LineageDirection.BOTH, description="Direction to traverse")
    depth: int = Field(3, ge=1, le=10, description="Maximum depth to traverse")
    include_columns: bool = Field(False, description="Include column-level lineage")
    filters: Optional[Dict[str, Any]] = Field(None, description="Additional filters")
    
    model_config = ConfigDict(
        populate_by_name=True,
        use_enum_values=True
    )


class LineageResponse(BaseModel):
    """Response model for lineage requests"""
    graph: LineageGraph = Field(..., description="The lineage graph")
    query_time_ms: int = Field(..., description="Query execution time in milliseconds")
    truncated: bool = Field(False, description="Whether results were truncated")
    error: Optional[str] = Field(None, description="Error message if any")
    
    model_config = ConfigDict(
        populate_by_name=True
    )


class LineageMetadata(BaseModel):
    """Metadata about lineage information"""
    source_system: str = Field(..., description="Source system (e.g., Unity Catalog)")
    extraction_time: datetime = Field(..., description="When lineage was extracted")
    total_nodes: int = Field(..., description="Total number of nodes")
    total_edges: int = Field(..., description="Total number of edges")
    depth_reached: int = Field(..., description="Maximum depth reached")
    filters_applied: Dict[str, Any] = Field(default_factory=dict, description="Filters that were applied")
    
    model_config = ConfigDict(
        populate_by_name=True
    )


class ImpactAnalysisRequest(BaseModel):
    """Request for impact analysis"""
    entity_id: str = Field(..., description="Entity to analyze impact for")
    entity_type: str = Field(..., description="Type of entity")
    change_type: str = Field(..., description="Type of change (schema_change, deletion, etc.)")
    depth: int = Field(5, ge=1, le=10, description="Maximum depth for impact analysis")
    
    model_config = ConfigDict(
        populate_by_name=True
    )


class ImpactAnalysisResponse(BaseModel):
    """Response for impact analysis"""
    directly_impacted: List[str] = Field(..., description="Directly impacted entities")
    indirectly_impacted: List[str] = Field(..., description="Indirectly impacted entities")
    total_impact_count: int = Field(..., description="Total number of impacted entities")
    impact_graph: Optional[LineageGraph] = Field(None, description="Graph of impacted entities")
    warnings: List[str] = Field(default_factory=list, description="Any warnings")
    
    model_config = ConfigDict(
        populate_by_name=True
    )


class LineageExportRequest(BaseModel):
    """Request for exporting lineage visualization"""
    graph: LineageGraph = Field(..., description="Graph to export")
    format: str = Field(..., description="Export format (svg, png, dot, json)")
    layout_algorithm: Optional[str] = Field("hierarchical", description="Layout algorithm")
    include_metadata: bool = Field(True, description="Include metadata in export")
    
    model_config = ConfigDict(
        populate_by_name=True
    )


class ColumnLineage(BaseModel):
    """Column-level lineage information"""
    source_column: str = Field(..., description="Source column identifier")
    target_column: str = Field(..., description="Target column identifier")
    transformation: Optional[str] = Field(None, description="Transformation applied")
    confidence: float = Field(1.0, ge=0.0, le=1.0, description="Confidence score")
    lineage_type: str = Field("direct", description="Type of lineage (direct, derived, etc.)")
    
    model_config = ConfigDict(
        populate_by_name=True
    )

