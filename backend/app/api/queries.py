"""
Query execution API endpoints
"""
from fastapi import APIRouter, HTTPException
from typing import List, Dict, Any, Optional
import structlog
from datetime import datetime

from app.integrations.databricks import get_databricks_connector
from app.models.queries import QueryRequest, QueryResponse, QueryResult

router = APIRouter()
logger = structlog.get_logger()


@router.post("/execute", response_model=QueryResponse)
async def execute_query(request: QueryRequest) -> QueryResponse:
    """Execute a SQL query against Databricks"""
    start_time = datetime.utcnow()
    
    try:
        # Validate query (basic checks)
        if not request.query.strip():
            raise ValueError("Query cannot be empty")
        
        # Log query execution
        logger.info("Executing query", query_preview=request.query[:200])
        
        # Execute query
        connector = get_databricks_connector()
        results = connector.execute_query(request.query, request.parameters)
        
        # Calculate execution time
        execution_time = (datetime.utcnow() - start_time).total_seconds()
        
        # Get column info from first row if available
        columns = []
        if results:
            columns = list(results[0].keys())
        
        # Create response
        response = QueryResponse(
            success=True,
            data=results,
            columns=columns,
            row_count=len(results),
            execution_time=execution_time,
            query=request.query
        )
        
        logger.info(
            "Query executed successfully",
            row_count=len(results),
            execution_time=execution_time
        )
        
        return response
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error("Query execution failed", error=str(e), query=request.query)
        
        # Return error response
        execution_time = (datetime.utcnow() - start_time).total_seconds()
        return QueryResponse(
            success=False,
            data=[],
            columns=[],
            row_count=0,
            execution_time=execution_time,
            query=request.query,
            error=str(e)
        )


@router.post("/validate")
async def validate_query(request: QueryRequest) -> Dict[str, Any]:
    """Validate a SQL query without executing it"""
    try:
        # For now, we'll do a simple EXPLAIN to validate
        explain_query = f"EXPLAIN {request.query}"
        
        connector = get_databricks_connector()
        connector.execute_query(explain_query)
        
        return {
            "valid": True,
            "message": "Query is valid"
        }
        
    except Exception as e:
        logger.warning("Query validation failed", error=str(e))
        return {
            "valid": False,
            "message": str(e)
        }


@router.get("/history")
async def get_query_history(
    limit: int = 10,
    offset: int = 0
) -> List[QueryResult]:
    """Get query execution history (placeholder for now)"""
    # TODO: Implement query history storage in PostgreSQL
    return []


@router.post("/save")
async def save_query(
    name: str,
    query: str,
    description: Optional[str] = None
) -> Dict[str, Any]:
    """Save a query for future use (placeholder for now)"""
    # TODO: Implement query saving in PostgreSQL
    return {
        "id": "placeholder",
        "name": name,
        "query": query,
        "description": description,
        "created_at": datetime.utcnow().isoformat()
    }
