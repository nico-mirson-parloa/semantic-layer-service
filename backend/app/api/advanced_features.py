"""
API endpoints for advanced features: data quality, lineage, and metric suggestions
"""
from fastapi import APIRouter, HTTPException, Query, Depends
from typing import List, Dict, Any, Optional
import structlog

from app.services.data_quality_service import DataQualityService
from app.services.data_lineage_service import DataLineageService  
from app.services.metric_suggestion_service import MetricSuggestionService
from app.auth import get_current_user, User

router = APIRouter()
logger = structlog.get_logger()

# Initialize services with optional Databricks connection
try:
    quality_service = DataQualityService()
    lineage_service = DataLineageService()
    suggestion_service = MetricSuggestionService()
except ValueError as e:
    # Databricks not configured - services will have limited functionality
    quality_service = None
    lineage_service = None
    suggestion_service = None
    logger.warning(f"Advanced features disabled due to missing Databricks config: {e}")


@router.get("/quality-checks/recommend")
async def recommend_quality_checks(
    catalog: str = Query(..., description="Databricks catalog name"),
    schema: str = Query(..., description="Schema name"),
    table: str = Query(..., description="Table name"),
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Get recommended data quality checks for a table
    
    Returns quality check recommendations including:
    - Nullability checks
    - Uniqueness checks
    - Range/distribution checks
    - Pattern validation
    - Freshness checks
    - Completeness metrics
    """
    if quality_service is None:
        raise HTTPException(status_code=503, detail="Data quality service unavailable - Databricks not configured")
    
    try:
        recommendations = quality_service.recommend_quality_checks(catalog, schema, table)
        
        return {
            "success": True,
            "table": f"{catalog}.{schema}.{table}",
            "recommendations": recommendations,
            "total_checks": len(recommendations)
        }
        
    except Exception as e:
        logger.error(f"Failed to get quality check recommendations", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/quality-checks/execute")
async def execute_quality_check(
    request: Dict[str, Any],
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Execute a specific data quality check
    
    Request body should contain:
    - sql: The quality check SQL to execute
    """
    try:
        sql = request.get("sql")
        if not sql:
            raise ValueError("SQL query is required")
        
        result = quality_service.execute_quality_check(sql)
        
        return result
        
    except Exception as e:
        logger.error(f"Failed to execute quality check", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/lineage/table")
async def get_table_lineage(
    catalog: str = Query(..., description="Databricks catalog name"),
    schema: str = Query(..., description="Schema name"),
    table: str = Query(..., description="Table name"),
    depth: int = Query(3, description="How many levels to traverse"),
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Get data lineage for a table
    
    Returns:
    - Upstream dependencies (tables this table depends on)
    - Downstream dependencies (tables that depend on this table)
    - Column-level lineage if available
    """
    try:
        lineage_data = lineage_service.get_table_lineage(catalog, schema, table, depth)
        
        # Add visualization data
        if not lineage_data.get("error"):
            lineage_data["visualization"] = lineage_service.visualize_lineage(lineage_data)
        
        return {
            "success": True,
            "lineage": lineage_data
        }
        
    except Exception as e:
        logger.error(f"Failed to get table lineage", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/lineage/sql")
async def analyze_sql_lineage(
    request: Dict[str, Any],
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Analyze lineage from SQL query
    
    Request body:
    - sql: SQL query to analyze
    - target_table: Optional target table if this is a CREATE/INSERT statement
    """
    try:
        sql = request.get("sql")
        target_table = request.get("target_table")
        
        if not sql:
            raise ValueError("SQL query is required")
        
        lineage_info = lineage_service.extract_lineage_from_sql(sql, target_table)
        
        return {
            "success": True,
            "lineage": lineage_info
        }
        
    except Exception as e:
        logger.error(f"Failed to analyze SQL lineage", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/lineage/semantic-model")
async def get_semantic_model_lineage(
    model_name: str = Query(..., description="Semantic model name"),
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Get lineage for a semantic model
    
    Returns:
    - Source tables used by the model
    - Metrics and their dependencies
    - Data flow visualization
    """
    try:
        from pathlib import Path
        from app.core.config import settings
        
        model_path = Path(settings.semantic_models_path) / f"{model_name}.yml"
        
        if not model_path.exists():
            raise HTTPException(status_code=404, detail=f"Semantic model {model_name} not found")
        
        lineage_info = lineage_service.analyze_semantic_model_lineage(str(model_path))
        
        return {
            "success": True,
            "model": model_name,
            "lineage": lineage_info
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get semantic model lineage", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/suggestions/metrics")
async def suggest_metrics(
    catalog: str = Query(..., description="Databricks catalog name"),
    schema: str = Query(..., description="Schema name"), 
    table: str = Query(..., description="Table name"),
    limit: int = Query(20, description="Maximum number of suggestions"),
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Get auto-suggested metrics based on table schema
    
    Returns metric suggestions including:
    - Basic count and aggregation metrics
    - Time-based analytics
    - Business KPIs based on domain patterns
    - Data quality metrics
    - Each with ready-to-use SQL
    """
    try:
        suggestions = suggestion_service.suggest_metrics(catalog, schema, table)
        
        # Apply limit
        if limit > 0:
            suggestions = suggestions[:limit]
        
        return {
            "success": True,
            "table": f"{catalog}.{schema}.{table}",
            "suggestions": suggestions,
            "total_suggestions": len(suggestions)
        }
        
    except Exception as e:
        logger.error(f"Failed to suggest metrics", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/suggestions/apply")
async def apply_metric_suggestion(
    request: Dict[str, Any],
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Apply a suggested metric by creating it in a semantic model
    
    Request body:
    - suggestion: The metric suggestion to apply
    - model_name: Target semantic model name
    - category: Category for the semantic model
    """
    try:
        from app.services.semantic_model_generator import SemanticModelGenerator
        from app.models.semantic import SemanticModelCreate
        
        suggestion = request.get("suggestion")
        model_name = request.get("model_name")
        category = request.get("category", "auto_generated")
        
        if not suggestion or not model_name:
            raise ValueError("Suggestion and model_name are required")
        
        # Create semantic model request
        model_request = SemanticModelCreate(
            name=model_name,
            description=f"Auto-generated metrics for {model_name}",
            category=category,
            metric_name=suggestion.get("name"),
            metric_description=suggestion.get("description"),
            natural_language=suggestion.get("display_name"),
            sql=suggestion.get("sql")
        )
        
        # Generate or update semantic model
        generator = SemanticModelGenerator()
        result = generator.generate_from_sql(model_request)
        
        return result
        
    except Exception as e:
        logger.error(f"Failed to apply metric suggestion", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


# Demo endpoints (no auth required)
demo_router = APIRouter()


@demo_router.get("/quality-checks/demo")
async def demo_quality_checks() -> Dict[str, Any]:
    """
    Demo endpoint showing sample quality check recommendations
    """
    return {
        "success": True,
        "demo": True,
        "table": "analytics.conversation_metrics",
        "recommendations": [
            {
                "check_type": "nullability",
                "column": "conversation_id",
                "description": "Check for null values in conversation_id",
                "sql_template": "SELECT COUNT(*) as null_count FROM analytics.conversation_metrics WHERE conversation_id IS NULL",
                "severity": "high"
            },
            {
                "check_type": "uniqueness",
                "column": "conversation_id",
                "description": "Check uniqueness of conversation_id",
                "sql_template": "SELECT conversation_id, COUNT(*) as dup_count FROM analytics.conversation_metrics GROUP BY conversation_id HAVING COUNT(*) > 1",
                "severity": "high"
            },
            {
                "check_type": "range",
                "column": "call_duration_seconds",
                "description": "Check for negative duration values",
                "sql_template": "SELECT COUNT(*) as negative_count FROM analytics.conversation_metrics WHERE call_duration_seconds < 0",
                "severity": "medium"
            },
            {
                "check_type": "freshness",
                "column": "created_timestamp",
                "description": "Check data freshness",
                "sql_template": "SELECT MAX(created_timestamp) as latest, DATEDIFF(hour, MAX(created_timestamp), CURRENT_TIMESTAMP()) as hours_old FROM analytics.conversation_metrics",
                "severity": "medium"
            }
        ]
    }


@demo_router.get("/lineage/demo")
async def demo_lineage() -> Dict[str, Any]:
    """
    Demo endpoint showing sample lineage data
    """
    return {
        "success": True,
        "demo": True,
        "lineage": {
            "table": "analytics.conversation_metrics",
            "upstream": [
                "raw.conversations",
                "raw.call_details",
                "dim.agents"
            ],
            "downstream": [
                "analytics.daily_metrics",
                "reporting.executive_dashboard"
            ],
            "visualization": {
                "nodes": [
                    {"id": "analytics.conversation_metrics", "label": "conversation_metrics", "type": "main", "level": 0},
                    {"id": "raw.conversations", "label": "conversations", "type": "upstream", "level": -1},
                    {"id": "raw.call_details", "label": "call_details", "type": "upstream", "level": -1},
                    {"id": "dim.agents", "label": "agents", "type": "upstream", "level": -1},
                    {"id": "analytics.daily_metrics", "label": "daily_metrics", "type": "downstream", "level": 1},
                    {"id": "reporting.executive_dashboard", "label": "executive_dashboard", "type": "downstream", "level": 1}
                ],
                "edges": [
                    {"source": "raw.conversations", "target": "analytics.conversation_metrics", "type": "data_flow"},
                    {"source": "raw.call_details", "target": "analytics.conversation_metrics", "type": "data_flow"},
                    {"source": "dim.agents", "target": "analytics.conversation_metrics", "type": "data_flow"},
                    {"source": "analytics.conversation_metrics", "target": "analytics.daily_metrics", "type": "data_flow"},
                    {"source": "analytics.conversation_metrics", "target": "reporting.executive_dashboard", "type": "data_flow"}
                ]
            }
        }
    }


@demo_router.get("/suggestions/demo")
async def demo_metric_suggestions() -> Dict[str, Any]:
    """
    Demo endpoint showing sample metric suggestions
    """
    return {
        "success": True,
        "demo": True,
        "table": "analytics.conversation_metrics",
        "suggestions": [
            {
                "name": "total_conversations",
                "display_name": "Total Conversations",
                "description": "Total number of conversations",
                "category": "volume",
                "metric_type": "count",
                "sql": "SELECT COUNT(*) as total_conversations FROM analytics.conversation_metrics",
                "complexity": "simple",
                "business_value": "high",
                "score": 70
            },
            {
                "name": "avg_call_duration",
                "display_name": "Average Call Duration",
                "description": "Average duration of calls in seconds",
                "category": "performance",
                "metric_type": "average",
                "sql": "SELECT AVG(call_duration_seconds) as avg_duration FROM analytics.conversation_metrics WHERE call_duration_seconds > 0",
                "complexity": "simple",
                "business_value": "high",
                "score": 70
            },
            {
                "name": "daily_conversation_trend",
                "display_name": "Daily Conversation Trend",
                "description": "Number of conversations per day",
                "category": "time_series",
                "metric_type": "time_aggregation",
                "sql": "SELECT DATE(created_timestamp) as date, COUNT(*) as daily_count FROM analytics.conversation_metrics WHERE created_timestamp >= DATEADD(day, -30, CURRENT_DATE()) GROUP BY DATE(created_timestamp) ORDER BY date DESC",
                "complexity": "medium",
                "business_value": "high",
                "score": 65
            },
            {
                "name": "conversation_success_rate",
                "display_name": "Conversation Success Rate",
                "description": "Percentage of successful conversations",
                "category": "quality",
                "metric_type": "percentage",
                "sql": "SELECT COUNT(CASE WHEN status = 'completed' THEN 1 END) * 100.0 / COUNT(*) as success_rate FROM analytics.conversation_metrics",
                "complexity": "simple",
                "business_value": "high",
                "score": 65
            }
        ]
    }

