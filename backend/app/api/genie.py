"""
Databricks Genie API endpoints for natural language metric creation
"""
from fastapi import APIRouter, HTTPException
from typing import Dict, Any, List, Optional
import structlog
import yaml
from pathlib import Path

from app.integrations.databricks_genie import get_genie_client
from app.integrations.databricks_genie_simple import get_simple_genie_client
from app.integrations.databricks_sql_statements import get_statements_client
from app.services.sql_intent import generate_sql_from_intent
from app.integrations.databricks import get_databricks_connector
from app.models.genie import (
    NaturalLanguageQuery,
    GenieResponse,
    MetricSuggestion,
    SemanticModelNL
)
from app.models.semantic_model import SemanticModelCreate
from app.core.config import settings
from app.utils.sql_formatter import format_sql, extract_table_info
from app.services.semantic_model_generator import get_semantic_model_generator

router = APIRouter()
logger = structlog.get_logger()


@router.post("/query", response_model=GenieResponse)
async def natural_language_to_sql(request: NaturalLanguageQuery) -> GenieResponse:
    """
    Convert natural language to SQL using Databricks Genie
    
    Example:
        "Show me total revenue by month for the last year"
        → SELECT DATE_TRUNC('month', order_date) as month,
                 SUM(amount) as total_revenue
          FROM gold.sales.orders
          WHERE order_date >= DATEADD(year, -1, CURRENT_DATE())
          GROUP BY 1
          ORDER BY 1
    """
    try:
        # Phase 1: Try rule-based generator to avoid demo SQL for common intents
        generated_sql = generate_sql_from_intent(request.query) or ""
        nl2sql: Dict[str, Any] = {"explanation": "Rule-based SQL", "confidence": 0.85}

        # Fallback: use simplified Genie generator if no rule matched
        if not generated_sql:
            genie = get_simple_genie_client()
            nl2sql = await genie.query_to_sql(request.query)
            sql_value = nl2sql.get("sql", "")
            # Ensure sql_value is a string before calling strip()
            if isinstance(sql_value, str):
                generated_sql = sql_value.strip()
            elif isinstance(sql_value, dict):
                # If it's a dict, try to extract the actual SQL
                generated_sql = str(sql_value.get("query", "") or sql_value.get("sql", "")).strip()
            else:
                generated_sql = str(sql_value).strip() if sql_value else ""
        if not generated_sql:
            return GenieResponse(
                sql="",
                explanation=nl2sql.get("explanation", "Failed to generate SQL"),
                confidence=nl2sql.get("confidence", 0.0),
                success=False,
                error=nl2sql.get("error")
            )

        # Optional safety: enforce LIMIT 100 if not present
        if " limit " not in generated_sql.lower():
            generated_sql = f"{generated_sql.rstrip(';')}\nLIMIT 100"

        # Optional validation only when requested: run an EXPLAIN to catch obvious errors
        if request.validate:
            try:
                statements = get_statements_client()
                explain_sql = f"EXPLAIN {generated_sql}"
                await statements.run_sql_and_get_results(explain_sql, timeout_s=60)
                explanation = nl2sql.get("explanation", "SQL generated and validated (EXPLAIN)")
                return GenieResponse(
                    sql=generated_sql,
                    explanation=explanation,
                    confidence=nl2sql.get("confidence", 0.8),
                    conversation_id=nl2sql.get("conversation_id"),
                    space_id=nl2sql.get("space_id"),
                    message_id=nl2sql.get("message_id"),
                    success=True
                )
            except Exception as e:
                return GenieResponse(
                    sql=generated_sql,
                    explanation=f"SQL generated; EXPLAIN error: {str(e)}",
                    confidence=nl2sql.get("confidence", 0.7),
                    conversation_id=nl2sql.get("conversation_id"),
                    space_id=nl2sql.get("space_id"),
                    message_id=nl2sql.get("message_id"),
                    success=True,
                    error=str(e)
                )

        # Default: return SQL without execution
        return GenieResponse(
            sql=generated_sql,
            explanation=nl2sql.get("explanation", "SQL generated"),
            confidence=nl2sql.get("confidence", 0.8),
            conversation_id=nl2sql.get("conversation_id"),
            space_id=nl2sql.get("space_id"),
            message_id=nl2sql.get("message_id"),
            success=True
        )
        
    except Exception as e:
        logger.error("Failed to generate SQL", error=str(e))
        return GenieResponse(
            sql="",
            explanation=f"Error: {str(e)}",
            confidence=0.0,
            success=False,
            error=str(e)
        )


@router.post("/refine")
async def refine_query(
    space_id: str,
    conversation_id: str,
    feedback: str
) -> GenieResponse:
    """Refine a previously generated query based on feedback"""
    try:
        genie = get_genie_client()
        result = await genie.refine_query(space_id, conversation_id, feedback)
        
        return GenieResponse(
            sql=result["sql"],
            explanation=result.get("explanation", ""),
            confidence=result.get("confidence", 0.8),
            conversation_id=conversation_id,
            space_id=space_id,
            success=True
        )
        
    except Exception as e:
        logger.error("Failed to refine query", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/suggest-metrics", response_model=List[MetricSuggestion])
async def suggest_metrics(
    catalog: str,
    schema: str,
    table: str
) -> List[MetricSuggestion]:
    """Get AI-suggested metrics for a table"""
    try:
        genie = get_genie_client()
        suggestions = await genie.suggest_metrics(table, catalog, schema)
        
        return [
            MetricSuggestion(
                name=s["name"],
                description=s["description"],
                natural_language_query=s["query"]
            )
            for s in suggestions
        ]
        
    except Exception as e:
        logger.error("Failed to get metric suggestions", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/create-semantic-model")
async def create_semantic_model_from_nl(model: SemanticModelNL) -> Dict[str, Any]:
    """
    Create a complete semantic model using natural language definitions
    """
    try:
        genie = get_genie_client()
        
        # Generate SQL for each metric
        generated_metrics = []
        for metric in model.metrics:
            context = {
                "catalog": model.catalog,
                "schema": model.schema,
                "table": model.base_table
            }
            
            result = await genie.natural_language_to_sql(
                query=metric.natural_language,
                context=context
            )
            
            generated_metrics.append({
                "name": metric.name,
                "description": metric.description,
                "natural_language": metric.natural_language,
                "generated_sql": result["sql"],
                "confidence": result["confidence"]
            })
        
        # Create the semantic model YAML
        semantic_model = {
            "semantic_model": {
                "name": model.name,
                "description": model.description,
                "catalog": model.catalog,
                "schema": model.schema,
                "base_table": model.base_table,
                "metrics": generated_metrics,
                "created_with": "databricks_genie",
                "genie_version": "1.0"
            }
        }
        
        # Save to file
        models_path = Path(settings.semantic_models_path)
        models_path.mkdir(parents=True, exist_ok=True)
        
        filename = f"{model.name.lower().replace(' ', '_')}_nl.yml"
        file_path = models_path / filename
        
        with open(file_path, 'w') as f:
            yaml.dump(semantic_model, f, default_flow_style=False, sort_keys=False)
        
        logger.info(f"Created semantic model {model.name} with Genie", file_path=str(file_path))
        
        return {
            "message": "Semantic model created successfully",
            "model_name": model.name,
            "file_path": str(file_path),
            "metrics_generated": len(generated_metrics)
        }
        
    except Exception as e:
        logger.error("Failed to create semantic model", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/validate-genie")
async def validate_genie_connection() -> Dict[str, Any]:
    """Check if Databricks Genie is available and configured"""
    try:
        # Check if we have the required settings
        has_host = bool(settings.databricks_host)
        has_token = bool(settings.databricks_token)
        has_warehouse = bool(settings.databricks_http_path)
        has_space_id = bool(settings.databricks_genie_space_id)
        
        is_configured = all([has_host, has_token, has_warehouse, has_space_id])
        
        return {
            "available": is_configured,
            "message": "Genie is ready" if is_configured else "Missing Databricks configuration",
            "configuration": {
                "host": has_host,
                "token": has_token,
                "warehouse": has_warehouse,
                "space_id": has_space_id
            }
        }
        
    except Exception as e:
        return {
            "available": False,
            "message": f"Error checking Genie: {str(e)}",
            "configuration": {}
        }


@router.post("/get-sql-logic")
async def get_sql_logic_from_nl(request: NaturalLanguageQuery) -> Dict[str, Any]:
    """
    Get the SQL logic for a natural language query without executing it.
    This endpoint returns the SQL statement that Genie would run.
    """
    try:
        # Use the same logic as the /query endpoint but focus on SQL extraction
        response = await natural_language_to_sql(request)
        
        # Format the SQL for better readability
        formatted_sql = format_sql(response.sql) if response.sql else ""
        
        # Extract table information
        table_info = extract_table_info(response.sql) if response.sql else {}
        
        return {
            "success": response.success,
            "natural_language_query": request.query,
            "generated_sql": response.sql,
            "formatted_sql": formatted_sql,
            "sql_explanation": response.explanation,
            "confidence_score": response.confidence,
            "conversation_id": response.conversation_id,
            "message_id": response.message_id,
            "space_id": response.space_id,
            "context": {
                "catalog": request.catalog,
                "schema": request.schema,
                "table": request.table
            },
            "sql_metadata": {
                "tables_used": table_info.get("tables", []),
                "main_table": table_info.get("main_table"),
                "has_joins": table_info.get("has_joins", False),
                "has_aggregation": table_info.get("has_aggregation", False)
            },
            "error": response.error
        }
    except Exception as e:
        logger.error("Failed to get SQL logic", error=str(e))
        return {
            "success": False,
            "natural_language_query": request.query,
            "generated_sql": "",
            "sql_explanation": f"Error: {str(e)}",
            "confidence_score": 0.0,
            "error": str(e)
        }


@router.get("/available-data")
async def get_genie_available_data(catalog: Optional[str] = None, schema: Optional[str] = None) -> Dict[str, Any]:
    """Get the data context based on actual Unity Catalog visibility for the configured warehouse/token.

    Note: This reflects what the current SQL warehouse can access. In most setups, Genie uses the same
    warehouse configured for the space, so this is a practical proxy for "Genie-accessible" data.
    """
    try:
        connector = get_databricks_connector()
        tables = connector.get_tables(catalog=catalog, schema=schema)

        # Group tables into {catalog -> {schema -> [tables]}}
        catalogs_map: Dict[str, Dict[str, Any]] = {}
        for t in tables:
            cat = t.get("table_catalog") or t.get("catalog")
            sch = t.get("table_schema") or t.get("schema")
            name = t.get("table_name") or t.get("name")
            comment = t.get("comment")

            if not cat or not sch or not name:
                continue

            if cat not in catalogs_map:
                catalogs_map[cat] = {"name": cat, "schemas": {}}
            if sch not in catalogs_map[cat]["schemas"]:
                catalogs_map[cat]["schemas"][sch] = {"name": sch, "tables": []}

            catalogs_map[cat]["schemas"][sch]["tables"].append({
                "name": name,
                "description": comment or ""
            })

        # Convert map to list structure expected by the frontend
        catalogs_list: List[Dict[str, Any]] = []
        for cat_val in catalogs_map.values():
            schemas_list: List[Dict[str, Any]] = []
            for sch_val in cat_val["schemas"].values():
                # Sort tables alphabetically
                sch_val["tables"].sort(key=lambda x: x["name"]) 
                schemas_list.append(sch_val)
            # Sort schemas alphabetically
            schemas_list.sort(key=lambda x: x["name"]) 
            catalogs_list.append({
                "name": cat_val["name"],
                "schemas": schemas_list
            })

        # Sort catalogs alphabetically
        catalogs_list.sort(key=lambda x: x["name"]) 

        return {
            "success": True,
            "catalogs": catalogs_list,
            "note": "Tables come from Unity Catalog for the configured SQL warehouse/token"
        }

    except Exception as e:
        logger.error("Failed to get data context from Unity Catalog", error=str(e))
        return {
            "success": False,
            "error": str(e),
            "catalogs": [],
            "note": "Error connecting to Unity Catalog"
        }


@router.post("/save-semantic-model")
async def save_semantic_model(request: SemanticModelCreate) -> Dict[str, Any]:
    """
    Save a metric as a semantic model in YAML format
    
    This endpoint takes the generated SQL and creates a properly structured
    semantic model with entities, dimensions, measures, and metrics.
    """
    try:
        generator = get_semantic_model_generator()
        result = generator.generate_from_sql(request)
        
        logger.info(
            "Saved semantic model",
            model_name=result.get("model_name"),
            file_path=result.get("file_path")
        )
        
        return result
        
    except Exception as e:
        logger.error("Failed to save semantic model", error=str(e))
        return {
            "success": False,
            "error": str(e),
            "message": f"Failed to save semantic model: {str(e)}"
        }
