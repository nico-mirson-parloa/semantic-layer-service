"""
Query execution models
"""
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
from datetime import datetime


class QueryRequest(BaseModel):
    """Query execution request"""
    query: str
    parameters: Optional[Dict[str, Any]] = None
    limit: Optional[int] = 1000


class QueryResponse(BaseModel):
    """Query execution response"""
    success: bool
    data: List[Dict[str, Any]]
    columns: List[str]
    row_count: int
    execution_time: float  # seconds
    query: str
    error: Optional[str] = None


class QueryResult(BaseModel):
    """Saved query result for history"""
    id: str
    query: str
    execution_time: float
    row_count: int
    created_at: datetime
    error: Optional[str] = None
