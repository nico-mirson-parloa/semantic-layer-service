"""
Data models for Unity Catalog schema information.
Used for automatic model generation from gold layer tables.
"""
from typing import List, Dict, Any, Optional
from datetime import datetime
from pydantic import BaseModel, Field, validator


class ColumnInfo(BaseModel):
    """Detailed information about a table column"""
    name: str = Field(..., description="Column name")
    data_type: str = Field(..., description="Column data type (e.g., BIGINT, STRING, DECIMAL)")
    nullable: bool = Field(True, description="Whether column allows NULL values")
    comment: Optional[str] = Field(None, description="Column description/comment")
    default_value: Optional[str] = Field(None, description="Default value expression")
    is_primary_key: bool = Field(False, description="Whether column is a primary key")
    is_foreign_key: bool = Field(False, description="Whether column is a foreign key")
    foreign_key_table: Optional[str] = Field(None, description="Referenced table for foreign key")
    foreign_key_column: Optional[str] = Field(None, description="Referenced column for foreign key")
    
    @validator('name')
    def validate_column_name(cls, v):
        """Validate column name follows naming conventions"""
        if not v or not v.strip():
            raise ValueError("Column name cannot be empty")
        # Remove any backticks that might be in the name
        return v.strip('`')
    
    @validator('data_type')
    def normalize_data_type(cls, v):
        """Normalize data type to uppercase"""
        return v.upper() if v else v
    
    def is_numeric(self) -> bool:
        """Check if column is numeric type"""
        numeric_types = ['INT', 'BIGINT', 'SMALLINT', 'TINYINT', 
                        'FLOAT', 'DOUBLE', 'DECIMAL', 'NUMERIC']
        return any(self.data_type.startswith(t) for t in numeric_types)
    
    def is_temporal(self) -> bool:
        """Check if column is date/time type"""
        temporal_types = ['DATE', 'TIMESTAMP', 'DATETIME']
        return any(self.data_type.startswith(t) for t in temporal_types)
    
    def is_boolean(self) -> bool:
        """Check if column is boolean type"""
        return self.data_type == 'BOOLEAN'
    
    def is_string(self) -> bool:
        """Check if column is string type"""
        string_types = ['STRING', 'VARCHAR', 'CHAR', 'TEXT']
        return any(self.data_type.startswith(t) for t in string_types)


class TableSchema(BaseModel):
    """Complete schema information for a table"""
    catalog: str = Field(..., description="Catalog name")
    schema: str = Field(..., description="Schema/database name")
    table: str = Field(..., description="Table name")
    columns: List[ColumnInfo] = Field(default_factory=list, description="List of columns")
    table_comment: Optional[str] = Field(None, description="Table description/comment")
    table_type: Optional[str] = Field(None, description="Table type (MANAGED, EXTERNAL, etc.)")
    location: Optional[str] = Field(None, description="Physical location for external tables")
    table_properties: Dict[str, str] = Field(default_factory=dict, description="Table properties")
    partition_columns: List[str] = Field(default_factory=list, description="Partition column names")
    clustering_columns: List[str] = Field(default_factory=list, description="Clustering column names")
    statistics: Optional[Dict[str, Any]] = Field(None, description="Table statistics")
    created_at: Optional[datetime] = Field(None, description="Table creation timestamp")
    updated_at: Optional[datetime] = Field(None, description="Last update timestamp")
    
    @property
    def full_name(self) -> str:
        """Get fully qualified table name"""
        return f"{self.catalog}.{self.schema}.{self.table}"
    
    @property
    def primary_keys(self) -> List[ColumnInfo]:
        """Get primary key columns"""
        return [col for col in self.columns if col.is_primary_key]
    
    @property
    def foreign_keys(self) -> List[ColumnInfo]:
        """Get foreign key columns"""
        return [col for col in self.columns if col.is_foreign_key]
    
    def get_column(self, name: str) -> Optional[ColumnInfo]:
        """Get column by name"""
        return next((col for col in self.columns if col.name == name), None)
    
    def numeric_columns(self) -> List[ColumnInfo]:
        """Get all numeric columns"""
        return [col for col in self.columns if col.is_numeric()]
    
    def temporal_columns(self) -> List[ColumnInfo]:
        """Get all date/time columns"""
        return [col for col in self.columns if col.is_temporal()]
    
    def categorical_columns(self) -> List[ColumnInfo]:
        """Get potential categorical columns (strings with likely low cardinality)"""
        return [col for col in self.columns if col.is_string()]


class TableAnalysis(BaseModel):
    """Results of table analysis for model generation"""
    table_name: str
    full_table_name: str
    row_count: Optional[int] = None
    size_in_bytes: Optional[int] = None
    columns: List[ColumnInfo]
    has_primary_key: bool
    foreign_keys: List[ColumnInfo]
    table_type: str  # 'fact', 'dimension', 'aggregate', 'unknown'
    is_empty: bool = False
    analysis_timestamp: datetime = Field(default_factory=datetime.now)
    
    # Pattern detection results
    numeric_columns: List[str] = Field(default_factory=list)
    temporal_columns: List[str] = Field(default_factory=list)
    categorical_columns: List[str] = Field(default_factory=list)
    boolean_columns: List[str] = Field(default_factory=list)
    id_columns: List[str] = Field(default_factory=list)
    
    # Column statistics
    column_statistics: Dict[str, Dict[str, Any]] = Field(default_factory=dict)
    
    # Relationships
    relationships: List[Dict[str, str]] = Field(default_factory=list)
    
    # Quality metrics
    null_percentage: Dict[str, float] = Field(default_factory=dict)
    uniqueness_ratio: Dict[str, float] = Field(default_factory=dict)
    
    # Suggestions confidence
    confidence_score: float = Field(0.0, ge=0.0, le=1.0)
    analysis_notes: List[str] = Field(default_factory=list)


class ColumnPattern(BaseModel):
    """Detected patterns in columns for suggestion generation"""
    numeric_columns: List[str] = Field(default_factory=list)
    id_columns: List[str] = Field(default_factory=list)
    date_columns: List[str] = Field(default_factory=list)
    timestamp_columns: List[str] = Field(default_factory=list)
    categorical_columns: List[str] = Field(default_factory=list)
    boolean_columns: List[str] = Field(default_factory=list)
    amount_columns: List[str] = Field(default_factory=list)  # Monetary amounts
    quantity_columns: List[str] = Field(default_factory=list)  # Counts/quantities
    percentage_columns: List[str] = Field(default_factory=list)  # Percentages
    
    def get_pattern_for_column(self, column_name: str) -> Optional[str]:
        """Get the detected pattern type for a column"""
        patterns = {
            'numeric': self.numeric_columns,
            'id': self.id_columns,
            'date': self.date_columns,
            'timestamp': self.timestamp_columns,
            'categorical': self.categorical_columns,
            'boolean': self.boolean_columns,
            'amount': self.amount_columns,
            'quantity': self.quantity_columns,
            'percentage': self.percentage_columns
        }
        
        for pattern_type, columns in patterns.items():
            if column_name in columns:
                return pattern_type
        return None


class TableRelationship(BaseModel):
    """Represents a relationship between tables"""
    from_table: str
    from_column: str
    to_table: str
    to_column: str
    relationship_type: str = "foreign_key"  # foreign_key, join, derived
    confidence: float = Field(1.0, ge=0.0, le=1.0)


class CatalogFilter(BaseModel):
    """Filter criteria for listing catalog objects"""
    catalog_name: Optional[str] = None
    schema_pattern: Optional[str] = None
    table_pattern: Optional[str] = None
    table_types: Optional[List[str]] = None  # MANAGED, EXTERNAL, VIEW
    include_views: bool = False
    include_temp_tables: bool = False
    tags: Optional[Dict[str, str]] = None
    min_row_count: Optional[int] = None
    max_tables: int = Field(100, ge=1, le=1000)


class GoldTableInfo(BaseModel):
    """Summary information for a gold layer table"""
    catalog: str
    schema: str
    table: str
    full_name: str = Field(alias="fullName")
    table_type: str = Field(alias="tableType")
    description: Optional[str] = None
    row_count: Optional[int] = Field(None, alias="rowCount")
    size_mb: Optional[float] = Field(None, alias="sizeMb")
    column_count: int = Field(alias="columnCount")
    has_semantic_model: bool = Field(False, alias="hasSemanticModel")
    last_updated: Optional[datetime] = Field(None, alias="lastUpdated")
    tags: Dict[str, str] = Field(default_factory=dict)
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat() if v else None
        }
        populate_by_name = True
        by_alias = True


class AnalyzeTableRequest(BaseModel):
    """Request to analyze a table for model generation"""
    catalog: str
    schema: str
    table: str
    include_statistics: bool = True
    include_lineage: bool = False
    sample_rows: Optional[int] = Field(None, ge=0, le=10000)
    
    @validator('catalog', 'schema', 'table')
    def validate_names(cls, v):
        """Validate catalog object names"""
        if not v or not v.strip():
            raise ValueError("Name cannot be empty")
        return v.strip()


class GenerateModelRequest(BaseModel):
    """Request to generate a semantic model"""
    catalog: str
    schema: str
    table: Optional[str] = None  # Single table
    tables: Optional[List[str]] = None  # Multiple tables
    accept_suggestions: bool = True
    customization: Optional[Dict[str, Any]] = None
    model_name: Optional[str] = None
    description: Optional[str] = None
    include_lineage: bool = True
    async_generation: bool = False
    output_format: str = Field("yaml", pattern="^(yaml|json)$")
    
    @validator('tables')
    def validate_table_input(cls, v, values):
        """Ensure either table or tables is provided"""
        if not v and not values.get('table'):
            raise ValueError("Either 'table' or 'tables' must be provided")
        return v


class ModelGenerationJob(BaseModel):
    """Status of an async model generation job"""
    job_id: str
    status: str  # pending, processing, completed, failed
    progress: float = Field(0.0, ge=0.0, le=1.0)
    tables_processed: int = 0
    total_tables: int = 0
    current_table: Optional[str] = None
    start_time: datetime
    end_time: Optional[datetime] = None
    results: Optional[List[Dict[str, Any]]] = None
    errors: List[str] = Field(default_factory=list)
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat() if v else None
        }
