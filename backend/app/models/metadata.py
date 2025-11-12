"""
Metadata models for tables and columns
"""
from pydantic import BaseModel
from typing import Optional


class Table(BaseModel):
    """Table metadata model"""
    catalog: str
    schema: str
    name: str
    type: Optional[str] = None  # TABLE, VIEW, etc.
    comment: Optional[str] = None
    
    @property
    def full_name(self) -> str:
        """Get fully qualified table name"""
        return f"{self.catalog}.{self.schema}.{self.name}"


class Column(BaseModel):
    """Column metadata model"""
    name: str
    data_type: str
    is_nullable: bool = True
    default: Optional[str] = None
    comment: Optional[str] = None
    ordinal_position: int
