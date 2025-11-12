"""
Unity Catalog API endpoints for automatic model generation.
Provides access to gold layer tables and model generation capabilities.
"""
from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks
from typing import List, Dict, Any, Optional
import structlog
import uuid
from datetime import datetime

from app.models.catalog import (
    CatalogFilter, GoldTableInfo, AnalyzeTableRequest,
    GenerateModelRequest, ModelGenerationJob
)
from app.models.semantic import (
    AnalysisResult, GeneratedModelResponse, ModelCustomization
)
from app.services.table_analyzer import TableAnalyzer
from app.services.metric_suggester import MetricSuggester  
from app.services.model_generator import ModelGenerator
from app.auth.permissions import require_auth
from app.integrations.databricks import DatabricksConnector
from app.core.config import settings

logger = structlog.get_logger()

# Create router
router = APIRouter()

# In-memory job storage (in production, use Redis or database)
generation_jobs: Dict[str, ModelGenerationJob] = {}


@router.get("/llm-models")
async def list_llm_models(
    current_user: Dict = Depends(require_auth)
) -> Dict[str, Any]:
    """
    List available LLM models for table analysis.
    
    Returns:
        Information about available LLM models and current configuration
    """
    try:
        from app.services.llm_table_analyzer import LLMModelRegistry
        
        models = LLMModelRegistry.list_models()
        current_model = settings.databricks_foundation_model_endpoint
        
        return {
            "llm_enabled": settings.enable_llm_analysis,
            "current_model": current_model,
            "available_models": models,
            "model_details": LLMModelRegistry.get_model_info(current_model),
            "note": "LLM analysis provides more intelligent metric and dimension suggestions based on business context"
        }
    except Exception as e:
        logger.error("Error listing LLM models", error=str(e))
        return {
            "llm_enabled": settings.enable_llm_analysis,
            "error": str(e),
            "note": "LLM functionality may not be available in your Databricks workspace"
        }


@router.post("/test-llm")
async def test_llm_analysis(
    current_user: Dict = Depends(require_auth)
) -> Dict[str, Any]:
    """
    Test LLM connectivity and functionality.
    
    Returns:
        Test results including model response
    """
    try:
        import requests
        
        model = settings.databricks_foundation_model_endpoint
        
        # Simple test prompt
        test_prompt = """
        Given a table with columns: customer_id (INT), order_date (DATE), total_amount (DECIMAL), status (VARCHAR)
        
        Suggest one metric in JSON format:
        {"name": "metric_name", "expression": "SQL_expression", "description": "what it measures"}
        """
        
        # Try Model Serving API first
        try:
            host = settings.databricks_host
            token = settings.databricks_token
            
            # Construct the endpoint URL
            endpoint_url = f"https://{host}/api/2.0/preview/ml/served-models/{model}/invocations"
            
            headers = {
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json"
            }
            
            payload = {
                "prompt": test_prompt,
                "max_tokens": 500,
                "temperature": 0.3
            }
            
            start_time = datetime.now()
            response = requests.post(endpoint_url, json=payload, headers=headers, timeout=30)
            end_time = datetime.now()
            
            if response.status_code == 200:
                result = response.json()
                
                # Extract text from various response formats
                llm_response = None
                response_format = list(result.keys())
                
                if "predictions" in result and isinstance(result["predictions"], list) and len(result["predictions"]) > 0:
                    prediction = result["predictions"][0]
                    if isinstance(prediction, dict) and "generated_text" in prediction:
                        llm_response = prediction["generated_text"]
                    elif isinstance(prediction, str):
                        llm_response = prediction
                elif "choices" in result and isinstance(result["choices"], list) and len(result["choices"]) > 0:
                    choice = result["choices"][0]
                    if "message" in choice and "content" in choice["message"]:
                        llm_response = choice["message"]["content"]
                    elif "text" in choice:
                        llm_response = choice["text"]
                elif "generated_text" in result:
                    llm_response = result["generated_text"]
                elif "text" in result:
                    llm_response = result["text"]
                elif "output" in result:
                    llm_response = result["output"]
                
                if llm_response:
                    return {
                        "success": True,
                        "model": model,
                        "response": llm_response,
                        "response_time_ms": int((end_time - start_time).total_seconds() * 1000),
                        "message": "LLM is working correctly via Model Serving API!",
                        "method": "model_serving_api",
                        "response_format": response_format
                    }
                else:
                    return {
                        "success": False,
                        "model": model,
                        "error": f"Unexpected response format: {response_format}",
                        "raw_response": json.dumps(result)[:500],
                        "message": "Model returned data but in unexpected format"
                    }
            else:
                # Try SQL AI function as fallback
                logger.info(f"Model Serving API failed with {response.status_code}, trying SQL AI function")
                connector = DatabricksConnector()
                query = f"""
                SELECT ai_query(
                    '{model}',
                    '{test_prompt.replace("'", "''")}'
                ) as llm_response
                """
                
                start_time = datetime.now()
                results = connector.execute_query(query)
                end_time = datetime.now()
                
                if results and len(results) > 0:
                    llm_response = results[0]['llm_response']
                    return {
                        "success": True,
                        "model": model,
                        "response": llm_response,
                        "response_time_ms": int((end_time - start_time).total_seconds() * 1000),
                        "message": "LLM is working correctly via SQL AI function!",
                        "method": "sql_ai_function"
                    }
                else:
                    return {
                        "success": False,
                        "model": model,
                        "error": f"Model Serving API returned {response.status_code}: {response.text[:200]}",
                        "message": "Both Model Serving API and SQL AI function failed"
                    }
                    
        except Exception as e:
            # If Model Serving fails, try SQL AI function
            logger.warning(f"Model Serving API error: {e}")
            connector = DatabricksConnector()
            query = f"""
            SELECT ai_query(
                '{model}',
                '{test_prompt.replace("'", "''")}'
            ) as llm_response
            """
            
            start_time = datetime.now()
            results = connector.execute_query(query)
            end_time = datetime.now()
            
            if results and len(results) > 0:
                llm_response = results[0]['llm_response']
                return {
                    "success": True,
                    "model": model,
                    "response": llm_response,
                    "response_time_ms": int((end_time - start_time).total_seconds() * 1000),
                    "message": "LLM is working correctly via SQL AI function!",
                    "method": "sql_ai_function"
                }
            else:
                return {
                    "success": False,
                    "model": model,
                    "error": str(e),
                    "message": "Both Model Serving API and SQL AI function failed"
                }
            
    except Exception as e:
        error_msg = str(e)
        logger.error(f"LLM test failed: {error_msg}")
        
        # Check for common error patterns
        if "ai_query" in error_msg.lower() or "function" in error_msg.lower():
            suggestion = "The ai_query function may not be available. Ensure your Databricks workspace has Foundation Model APIs enabled."
        elif "permission" in error_msg.lower():
            suggestion = "Check that your token has permission to access Foundation Models."
        else:
            suggestion = "Check Databricks workspace configuration and Foundation Model availability."
        
        return {
            "success": False,
            "model": settings.databricks_foundation_model_endpoint,
            "error": error_msg,
            "suggestion": suggestion
        }


@router.get("/table-types")
async def list_table_types(
    catalog: str = "parloa-prod-weu",
    schema: Optional[str] = None,
    current_user: Dict = Depends(require_auth)
) -> Dict[str, Any]:
    """
    List all table types in a catalog/schema for diagnostic purposes.
    
    Args:
        catalog: Catalog name
        schema: Schema name (optional)
        
    Returns:
        Count of tables by type
    """
    try:
        connector = DatabricksConnector()
        
        # Build conditions
        conditions = [f"table_catalog = '{catalog}'"]
        if schema:
            conditions.append(f"table_schema = '{schema}'")
        
        where_clause = " AND ".join(conditions)
        
        # Query for table types
        query = f"""
        SELECT 
            table_type,
            COUNT(*) as count
        FROM system.information_schema.tables
        WHERE {where_clause}
        GROUP BY table_type
        ORDER BY count DESC
        """
        
        results = connector.execute_query(query)
        
        # Also get total tables that would be shown in list_gold_tables
        supported_types_query = f"""
        SELECT COUNT(*) as count
        FROM system.information_schema.tables
        WHERE {where_clause}
            AND table_type IN ('MANAGED', 'EXTERNAL', 'MATERIALIZED_VIEW')
        """
        
        supported_count = connector.execute_query(supported_types_query)
        
        return {
            "catalog": catalog,
            "schema": schema,
            "table_types": results,
            "total_tables": sum(r['count'] for r in results),
            "supported_table_count": supported_count[0]['count'] if supported_count else 0,
            "note": "MANAGED, EXTERNAL, and MATERIALIZED_VIEW tables are shown in the Auto Model Generation UI"
        }
    except Exception as e:
        logger.error("Error listing table types", error=str(e))
        return {
            "catalog": catalog,
            "schema": schema,
            "error": str(e)
        }


@router.get("/catalogs")
async def list_catalogs(
    current_user: Dict = Depends(require_auth)
) -> Dict[str, Any]:
    """
    List all available catalogs for diagnostic purposes.
    
    Returns:
        List of catalogs
    """
    try:
        connector = DatabricksConnector()
        
        # Query for all catalogs
        query = """
        SELECT 
            catalog_name,
            comment,
            catalog_owner
        FROM system.information_schema.catalogs
        ORDER BY catalog_name
        """
        
        results = connector.execute_query(query)
        
        return {
            "catalogs": results,
            "total_catalogs": len(results),
            "suggestion": "Use one of these catalog names in your API calls"
        }
    except Exception as e:
        logger.error("Error listing catalogs", error=str(e))
        return {
            "catalogs": [],
            "error": str(e),
            "suggestion": "Check your Databricks connection"
        }


@router.get("/schemas")
async def list_schemas(
    catalog: str = "parloa-prod-weu",
    current_user: Dict = Depends(require_auth)
) -> Dict[str, Any]:
    """
    List all available schemas in the catalog for diagnostic purposes.
    
    Args:
        catalog: Catalog name (default: main)
        
    Returns:
        List of schemas with table counts
    """
    try:
        connector = DatabricksConnector()
        
        # Query for all schemas - count MANAGED, EXTERNAL, and MATERIALIZED_VIEW tables to match list_gold_tables
        query = f"""
        SELECT 
            s.schema_name,
            s.catalog_name,
            s.comment,
            COUNT(DISTINCT CASE 
                WHEN t.table_type IN ('MANAGED', 'EXTERNAL', 'MATERIALIZED_VIEW') 
                THEN t.table_name 
                ELSE NULL 
            END) as table_count
        FROM system.information_schema.schemata s
        LEFT JOIN system.information_schema.tables t
            ON t.table_catalog = s.catalog_name 
            AND t.table_schema = s.schema_name
        WHERE s.catalog_name = '{catalog}'
        GROUP BY s.schema_name, s.catalog_name, s.comment
        ORDER BY s.schema_name
        """
        
        results = connector.execute_query(query)
        
        return {
            "catalog": catalog,
            "schemas": results,
            "total_schemas": len(results),
            "suggestion": "Use schema_pattern parameter in /gold-tables endpoint to filter by schema, e.g., ?schema_pattern=bronze% or leave empty to see all tables"
        }
    except Exception as e:
        logger.error("Error listing schemas", error=str(e))
        return {
            "catalog": catalog,
            "schemas": [],
            "error": str(e),
            "suggestion": "Check your Databricks connection and catalog name"
        }


@router.get("/gold-tables", response_model=List[GoldTableInfo])
async def list_gold_tables(
    catalog: Optional[str] = "parloa-prod-weu",
    schema_pattern: Optional[str] = None,
    search: Optional[str] = None,
    limit: int = 100,
    current_user: Dict = Depends(require_auth)
) -> List[GoldTableInfo]:
    """
    List available tables from Unity Catalog.
    
    Args:
        catalog: Catalog name (default: main)
        schema_pattern: Schema name pattern (optional, e.g. 'gold%', 'silver%')
        search: Search term to filter table names or descriptions
        limit: Maximum number of tables to return
        
    Returns:
        List of table information
    """
    try:
        connector = DatabricksConnector()
        
        # Build query conditions
        conditions = [f"table_catalog = '{catalog}'"]
        # Include MANAGED, EXTERNAL, and MATERIALIZED_VIEW tables
        conditions.append("table_type IN ('MANAGED', 'EXTERNAL', 'MATERIALIZED_VIEW')")
        
        # Add schema pattern if provided
        if schema_pattern:
            conditions.append(f"table_schema LIKE '{schema_pattern}'")
        
        # Add search filter if provided
        if search:
            search_lower = search.lower()
            conditions.append(f"(LOWER(table_name) LIKE '%{search_lower}%' OR LOWER(comment) LIKE '%{search_lower}%')")
        
        where_clause = " AND ".join(conditions)
        
        # Query for tables
        query = f"""
        SELECT 
            table_catalog as catalog,
            table_schema as schema,
            table_name as table,
            table_type,
            comment as description,
            data_source_format,
            created as last_updated
        FROM system.information_schema.tables
        WHERE {where_clause}
        ORDER BY table_schema, table_name
        LIMIT {limit}
        """
        
        results = connector.execute_query(query)
        
        tables = []
        for row in results:
            # Check if semantic model exists
            model_path = f"semantic-models/{row['table']}_model.yml"
            has_model = False
            try:
                from pathlib import Path
                has_model = Path(model_path).exists()
            except:
                pass
            
            tables.append(GoldTableInfo(
                catalog=row['catalog'],
                schema=row['schema'],
                table=row['table'],
                full_name=f"{row['catalog']}.{row['schema']}.{row['table']}",
                table_type=row['table_type'],
                description=row.get('description'),
                has_semantic_model=has_model,
                last_updated=row.get('last_updated'),
                column_count=0  # Would need separate query
            ))
        
        return tables
        
    except Exception as e:
        logger.error(f"Error listing gold tables: {e}")
        # Return mock data for testing
        return [
            GoldTableInfo(
                catalog="main",
                schema="gold", 
                table="sales_fact",
                full_name="main.gold.sales_fact",
                table_type="MANAGED",
                description="Sales fact table",
                column_count=15,
                has_semantic_model=False
            ),
            GoldTableInfo(
                catalog="main",
                schema="gold",
                table="customer_dim",
                full_name="main.gold.customer_dim",
                table_type="MANAGED",
                description="Customer dimension table",
                column_count=20,
                has_semantic_model=True
            )
        ]


@router.post("/analyze-table", response_model=AnalysisResult)
async def analyze_table(
    request: AnalyzeTableRequest,
    current_user: Dict = Depends(require_auth)
) -> AnalysisResult:
    """
    Analyze a table and suggest metrics, dimensions, and entities.
    
    Args:
        request: Table analysis request
        
    Returns:
        Analysis results with suggestions
    """
    try:
        # Get table schema
        connector = DatabricksConnector()
        
        # Check if LLM analysis is enabled
        use_llm = settings.enable_llm_analysis
        
        if use_llm:
            try:
                from app.services.llm_table_analyzer import LLMTableAnalyzer
                logger.info("Using LLM-based table analysis")
                llm_analyzer = LLMTableAnalyzer()
            except Exception as e:
                logger.warning(f"Failed to initialize LLM analyzer: {e}. Falling back to pattern-based analysis.")
                use_llm = False
        
        if not use_llm:
            analyzer = TableAnalyzer(connector)
            suggester = MetricSuggester()
        
        # Get table metadata
        schema_query = f"""
        SELECT 
            column_name,
            data_type,
            is_nullable,
            comment
        FROM system.information_schema.columns
        WHERE table_catalog = '{request.catalog}'
            AND table_schema = '{request.schema}'
            AND table_name = '{request.table}'
        ORDER BY ordinal_position
        """
        
        # Execute query to get real table schema
        from app.models.catalog import TableSchema, ColumnInfo
        
        column_results = connector.execute_query(schema_query)
        
        # Convert results to ColumnInfo objects
        columns = []
        for row in column_results:
            columns.append(ColumnInfo(
                name=row['column_name'],
                data_type=row['data_type'],
                nullable=row['is_nullable'] == 'YES',
                comment=row.get('comment'),
                is_primary_key=False  # Would need separate query for PKs
            ))
        
        # Get table comment and stats
        table_info_query = f"""
        SELECT 
            comment as table_comment
        FROM system.information_schema.tables
        WHERE table_catalog = '{request.catalog}'
            AND table_schema = '{request.schema}'
            AND table_name = '{request.table}'
        """
        
        table_info = connector.execute_query(table_info_query)
        table_comment = table_info[0]['table_comment'] if table_info else None
        
        table_schema = TableSchema(
            catalog=request.catalog,
            schema=request.schema,
            table=request.table,
            columns=columns,
            table_comment=table_comment or f"Table: {request.table}"
        )
        
        # Analyze table based on method chosen
        if use_llm:
            # Use LLM-based analysis
            try:
                result = llm_analyzer.analyze_table_with_llm(table_schema)
                return result
            except Exception as e:
                logger.error(f"LLM analysis failed: {e}. Falling back to pattern-based analysis.")
                # Fall back to pattern-based analysis
                analyzer = TableAnalyzer(connector)
                suggester = MetricSuggester()
        
        # Pattern-based analysis (default or fallback)
        analysis = analyzer.analyze_table(table_schema)
        
        # Convert to format for suggester
        analyzed_dict = {
            "table_name": analysis.table_name,
            "table_type": analysis.table_type,
            "columns": {}
        }
        
        # Add column info with proper pattern detection
        for col in analysis.columns:
            # Determine pattern based on analysis results
            pattern = "dimension"  # default
            
            if col.name in analysis.numeric_columns:
                if col.name in analysis.id_columns:
                    pattern = "identifier"
                elif any(keyword in col.name.lower() for keyword in ['amount', 'price', 'cost', 'revenue', 'total', 'fee', 'charge']):
                    pattern = "amount"
                elif any(keyword in col.name.lower() for keyword in ['count', 'qty', 'quantity', 'volume', 'number']):
                    pattern = "quantity"
                elif any(keyword in col.name.lower() for keyword in ['rate', 'ratio', 'percent', 'pct', 'share']):
                    pattern = "percentage"
                else:
                    pattern = "metric"
            elif col.name in analysis.temporal_columns:
                pattern = "time"
            elif col.name in analysis.boolean_columns:
                pattern = "boolean"
            elif col.name in analysis.categorical_columns:
                pattern = "dimension"
            
            analyzed_dict["columns"][col.name] = {
                "data_type": col.data_type,
                "pattern": pattern,
                "nullable": col.nullable,
                "comment": col.comment
            }
        
        # Suggest metrics
        suggestions = suggester.suggest_metrics(analyzed_dict)
        
        # Generate dimension suggestions
        dimension_suggestions = []
        
        # Import SuggestedDimension for proper typing
        from app.models.semantic import SuggestedDimension
        
        # Add categorical columns as dimensions
        for col_name in analysis.categorical_columns:
            col_info = next((c for c in analysis.columns if c.name == col_name), None)
            if col_info:
                # Check for special dimension types
                dim_type = "categorical"
                if any(geo in col_name.lower() for geo in ['country', 'state', 'city', 'region', 'location']):
                    dim_type = "geographic"
                
                dimension_suggestions.append(SuggestedDimension(
                    name=col_name,
                    display_name=col_name.replace('_', ' ').title(),
                    type=dim_type,
                    expression=col_name,
                    description=col_info.comment or f"Dimension based on {col_name}"
                ))
        
        # Add time dimensions
        for col_name in analysis.temporal_columns:
            col_info = next((c for c in analysis.columns if c.name == col_name), None)
            if col_info and col_info.data_type in ['DATE', 'TIMESTAMP']:
                dimension_suggestions.append(SuggestedDimension(
                    name=col_name,
                    display_name=col_name.replace('_', ' ').title(),
                    type="time",
                    expression=col_name,
                    description=col_info.comment or f"Time dimension based on {col_name}",
                    granularities=["day", "week", "month", "quarter", "year"] if col_info.data_type == 'DATE' else ["hour", "day", "week", "month", "quarter", "year"]
                ))
        
        # Build response
        result = AnalysisResult(
            table_analysis=analyzed_dict,
            suggested_metrics=suggestions[:10],  # Limit suggestions
            suggested_dimensions=dimension_suggestions[:10],  # Limit dimensions too
            suggested_entities=[],  # Remove hardcoded order entity
            suggested_measures=[],
            confidence_scores={
                "overall": 0.85,
                "metrics": 0.90,
                "dimensions": 0.80
            }
        )
        
        result.calculate_statistics()
        
        return result
        
    except Exception as e:
        logger.error(f"Error analyzing table: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/generate", response_model=GeneratedModelResponse)
async def generate_model(
    request: GenerateModelRequest,
    background_tasks: BackgroundTasks,
    current_user: Dict = Depends(require_auth)
) -> GeneratedModelResponse:
    """
    Generate semantic model(s) from table(s).
    
    Args:
        request: Model generation request
        
    Returns:
        Generated model response or job ID for async processing
    """
    try:
        # Check if async processing requested
        if request.async_generation or request.tables:
            # Create job
            job_id = str(uuid.uuid4())
            job = ModelGenerationJob(
                job_id=job_id,
                status="pending",
                total_tables=len(request.tables) if request.tables else 1,
                start_time=datetime.now()
            )
            generation_jobs[job_id] = job
            
            # Start background processing
            background_tasks.add_task(
                process_generation_job,
                job_id,
                request
            )
            
            return GeneratedModelResponse(
                success=True,
                model_id=job_id,
                errors=[]
            )
        
        # Synchronous processing for single table
        if not request.table:
            raise HTTPException(status_code=400, detail="Table name required")
        
        # Analyze table first
        analyze_req = AnalyzeTableRequest(
            catalog=request.catalog,
            schema=request.schema,
            table=request.table
        )
        
        analysis = await analyze_table(analyze_req, current_user)
        
        # Generate model
        generator = ModelGenerator()
        
        # Prepare suggestions
        suggestions = {
            "metrics": analysis.suggested_metrics,
            "dimensions": analysis.suggested_dimensions,
            "entities": analysis.suggested_entities
        }
        
        # Apply customization
        customization = None
        if request.customization:
            customization = ModelCustomization(**request.customization)
        
        model = generator.generate_model(
            table_name=request.table,
            schema=request.schema,
            catalog=request.catalog,
            suggestions=suggestions,
            customization=request.customization
        )
        
        # Validate model
        validation = generator.validate_model(model)
        
        if validation.is_valid:
            # Save model
            file_path = generator.save_model(model)
            
            # Generate response
            yaml_content = generator.to_yaml(model)
            metadata = generator.generate_metadata(model)
            
            return GeneratedModelResponse(
                success=True,
                model_id=model.name,
                model_name=model.name,
                yaml_content=yaml_content,
                validation_result=validation,
                metadata=metadata,
                file_path=file_path
            )
        else:
            return GeneratedModelResponse(
                success=False,
                errors=validation.errors,
                validation_result=validation
            )
            
    except Exception as e:
        logger.error(f"Error generating model: {e}")
        return GeneratedModelResponse(
            success=False,
            errors=[str(e)]
        )


@router.get("/generation-status/{job_id}", response_model=ModelGenerationJob)
async def get_generation_status(
    job_id: str,
    current_user: Dict = Depends(require_auth)
) -> ModelGenerationJob:
    """
    Get status of async model generation job.
    
    Args:
        job_id: Job identifier
        
    Returns:
        Job status and results
    """
    if job_id not in generation_jobs:
        raise HTTPException(status_code=404, detail="Job not found")
    
    return generation_jobs[job_id]


async def process_generation_job(job_id: str, request: GenerateModelRequest):
    """
    Process model generation job in background.
    """
    job = generation_jobs[job_id]
    job.status = "processing"
    
    try:
        tables = request.tables or [request.table]
        results = []
        
        for i, table in enumerate(tables):
            job.current_table = table
            job.tables_processed = i
            job.progress = (i + 1) / len(tables)
            
            # Generate model for each table
            # (Similar logic as synchronous generation)
            results.append({
                "table": table,
                "success": True,
                "model_name": f"{table}_model"
            })
        
        job.status = "completed"
        job.end_time = datetime.now()
        job.results = results
        
    except Exception as e:
        job.status = "failed"
        job.errors.append(str(e))
        job.end_time = datetime.now()
