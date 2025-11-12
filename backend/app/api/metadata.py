"""
Metadata API endpoints for discovering Databricks tables and columns
"""
from fastapi import APIRouter, HTTPException, Query
from typing import List, Dict, Any, Optional
import structlog

from app.integrations.databricks import get_databricks_connector
from app.models.metadata import Table, Column

router = APIRouter()
logger = structlog.get_logger()


@router.get("/tables", response_model=List[Table])
async def get_tables(
    catalog: Optional[str] = Query(None, description="Filter by catalog"),
    schema: Optional[str] = Query(None, description="Filter by schema")
) -> List[Table]:
    """Get available tables from Databricks Unity Catalog"""
    try:
        connector = get_databricks_connector()
        tables_data = connector.get_tables(catalog=catalog, schema=schema)
        
        # Convert to Table models
        tables = []
        for table in tables_data:
            tables.append(Table(
                catalog=table.get("table_catalog"),
                schema=table.get("table_schema"),
                name=table.get("table_name"),
                type=table.get("table_type"),
                comment=table.get("comment")
            ))
        
        logger.info("Retrieved tables", count=len(tables), catalog=catalog, schema=schema)
        return tables
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error("Failed to retrieve tables", error=str(e))
        raise HTTPException(status_code=500, detail=f"Failed to retrieve tables: {str(e)}")


@router.get("/columns", response_model=List[Column])
async def get_columns(
    catalog: str = Query(..., description="Catalog name"),
    schema: str = Query(..., description="Schema name"),
    table: str = Query(..., description="Table name")
) -> List[Column]:
    """Get columns for a specific table"""
    try:
        connector = get_databricks_connector()
        columns_data = connector.get_columns(catalog=catalog, schema=schema, table=table)
        
        # Convert to Column models
        columns = []
        for idx, col in enumerate(columns_data):
            columns.append(Column(
                name=col.get("column_name"),
                data_type=col.get("data_type"),
                is_nullable=col.get("is_nullable") == "YES",
                default=col.get("column_default"),
                comment=col.get("comment"),
                ordinal_position=idx + 1
            ))
        
        logger.info("Retrieved columns", count=len(columns), table=f"{catalog}.{schema}.{table}")
        return columns
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error("Failed to retrieve columns", error=str(e))
        raise HTTPException(status_code=500, detail=f"Failed to retrieve columns: {str(e)}")


@router.get("/catalogs")
async def get_catalogs() -> List[str]:
    """Get list of available catalogs"""
    try:
        connector = get_databricks_connector()
        query = "SELECT DISTINCT table_catalog FROM system.information_schema.tables ORDER BY table_catalog"
        results = connector.execute_query(query)
        catalogs = [row["table_catalog"] for row in results]
        logger.info("Retrieved catalogs", count=len(catalogs))
        return catalogs
        
    except Exception as e:
        logger.error("Failed to retrieve catalogs", error=str(e))
        raise HTTPException(status_code=500, detail=f"Failed to retrieve catalogs: {str(e)}")


@router.get("/schemas")
async def get_schemas(
    catalog: str = Query(..., description="Catalog name")
) -> List[str]:
    """Get list of schemas in a catalog"""
    try:
        connector = get_databricks_connector()
        query = f"""
        SELECT DISTINCT table_schema 
        FROM system.information_schema.tables 
        WHERE table_catalog = '{catalog}'
        ORDER BY table_schema
        """
        results = connector.execute_query(query)
        schemas = [row["table_schema"] for row in results]
        logger.info("Retrieved schemas", count=len(schemas), catalog=catalog)
        return schemas
        
    except Exception as e:
        logger.error("Failed to retrieve schemas", error=str(e))
        raise HTTPException(status_code=500, detail=f"Failed to retrieve schemas: {str(e)}")


@router.get("/sql-autocomplete")
async def get_sql_autocomplete(
    search: str = Query("", description="Search term for autocomplete"),
    context: Optional[str] = Query(None, description="Context (catalog, schema, or full)")
) -> Dict[str, Any]:
    """
    Get SQL autocomplete suggestions for catalog, schema, and table names
    
    Returns suggestions based on the search term and context:
    - If search contains dots, it provides contextual suggestions
    - catalog.schema. -> suggests tables
    - catalog. -> suggests schemas
    - Otherwise suggests catalogs, popular tables, etc.
    """
    logger.info("SQL autocomplete request", search=search, context=context)
    
    try:
        connector = get_databricks_connector()
        suggestions = {
            "catalogs": [],
            "schemas": [],
            "tables": [],
            "columns": [],
            "keywords": []
        }
        
        # Parse the search term to understand context
        parts = search.split('.')
        search_lower = search.lower()
        
        # Add SQL keywords if search is short
        if len(search) < 3 or search_lower in ['sel', 'sele', 'selec']:
            suggestions["keywords"] = ["SELECT", "FROM", "WHERE", "GROUP BY", "ORDER BY", "LIMIT"]
        elif search_lower.startswith('fr'):
            suggestions["keywords"] = ["FROM"]
        elif search_lower.startswith('wh'):
            suggestions["keywords"] = ["WHERE"]
        elif search_lower.startswith('gr'):
            suggestions["keywords"] = ["GROUP BY"]
        elif search_lower.startswith('or'):
            suggestions["keywords"] = ["ORDER BY"]
        
        # Determine what to suggest based on the input
        if len(parts) == 1 and not search.endswith('.'):
            # Suggest catalogs and top-level items
            if search:
                # Filter catalogs
                catalog_query = f"""
                    SELECT DISTINCT table_catalog 
                    FROM system.information_schema.tables 
                    WHERE LOWER(table_catalog) LIKE LOWER('{search}%')
                    ORDER BY table_catalog
                    LIMIT 10
                """
            else:
                # All catalogs
                catalog_query = """
                    SELECT DISTINCT table_catalog 
                    FROM system.information_schema.tables 
                    ORDER BY table_catalog
                    LIMIT 10
                """
            logger.debug("Executing catalog query", query=catalog_query, search=search)
            catalog_results = connector.execute_query(catalog_query)
            logger.debug("Catalog results", count=len(catalog_results), results=catalog_results)
            suggestions["catalogs"] = [row["table_catalog"] for row in catalog_results]
            
        elif len(parts) == 2 or (len(parts) == 1 and search.endswith('.')):
            # Suggest schemas for the given catalog
            catalog = parts[0].strip('`')
            schema_pattern = parts[1] if len(parts) == 2 else ''
            
            schema_query = f"""
                SELECT DISTINCT table_schema 
                FROM system.information_schema.tables 
                WHERE table_catalog = '{catalog}'
                {f"AND LOWER(table_schema) LIKE LOWER('{schema_pattern}%')" if schema_pattern else ""}
                ORDER BY table_schema
                LIMIT 10
            """
            schema_results = connector.execute_query(schema_query)
            suggestions["schemas"] = [f"{catalog}.{row['table_schema']}" for row in schema_results]
            
        elif len(parts) == 3 or (len(parts) == 2 and search.endswith('.')):
            # Suggest tables for the given catalog.schema
            catalog = parts[0].strip('`')
            schema = parts[1].strip('`') if len(parts) > 1 else ''
            table_pattern = parts[2] if len(parts) == 3 else ''
            
            table_query = f"""
                SELECT table_name, table_type
                FROM system.information_schema.tables 
                WHERE table_catalog = '{catalog}'
                AND table_schema = '{schema}'
                {f"AND LOWER(table_name) LIKE LOWER('{table_pattern}%')" if table_pattern else ""}
                ORDER BY 
                    CASE WHEN table_type = 'TABLE' THEN 0 ELSE 1 END,
                    table_name
                LIMIT 20
            """
            table_results = connector.execute_query(table_query)
            suggestions["tables"] = [
                {
                    "name": f"`{catalog}`.`{schema}`.`{row['table_name']}`",
                    "type": row["table_type"],
                    "display": row["table_name"]
                }
                for row in table_results
            ]
            
        # If we're in the middle of a query, also suggest recently used tables
        if context == "full" and not search:
            # Get some commonly used tables
            recent_tables_query = """
                SELECT table_catalog, table_schema, table_name, table_type
                FROM system.information_schema.tables 
                WHERE table_schema NOT IN ('information_schema', 'system')
                ORDER BY table_catalog, table_schema, table_name
                LIMIT 10
            """
            recent_results = connector.execute_query(recent_tables_query)
            suggestions["tables"] = [
                {
                    "name": f"`{row['table_catalog']}`.`{row['table_schema']}`.`{row['table_name']}`",
                    "type": row["table_type"],
                    "display": f"{row['table_schema']}.{row['table_name']}"
                }
                for row in recent_results
            ]
        
        return {
            "search_term": search,
            "suggestions": suggestions,
            "total_suggestions": (
                len(suggestions["catalogs"]) + 
                len(suggestions["schemas"]) + 
                len(suggestions["tables"]) +
                len(suggestions["keywords"])
            )
        }
        
    except Exception as e:
        logger.error("Failed to get SQL autocomplete suggestions", error=str(e), search=search, context=context)
        import traceback
        traceback.print_exc()
        # Return empty suggestions on error to not break the UI
        return {
            "search_term": search,
            "suggestions": {
                "catalogs": [],
                "schemas": [],
                "tables": [],
                "columns": [],
                "keywords": []
            },
            "total_suggestions": 0
        }
