"""
API endpoints for lineage visualization feature.
Provides REST endpoints for extracting, processing, and visualizing lineage data.
"""

import logging
from typing import Dict, Any, Optional
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import Response

from app.auth.permissions import require_auth
from app.models.lineage import (
    LineageResponse,
    LineageDirection,
    ImpactAnalysisRequest,
    ImpactAnalysisResponse,
    LineageExportRequest
)
from app.services.lineage_extractor import LineageExtractor
from app.services.lineage_processor import LineageProcessor
from app.services.lineage_visualizer import LineageVisualizer
from app.integrations.databricks import DatabricksConnector

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1/lineage", tags=["lineage"])


@router.get("/table")
async def get_table_lineage(
    catalog: str = Query(..., description="Catalog name"),
    schema: str = Query(..., description="Schema name"),
    table: str = Query(..., description="Table name"),
    direction: LineageDirection = Query(LineageDirection.BOTH, description="Lineage direction"),
    depth: int = Query(3, ge=1, le=10, description="Maximum depth to traverse"),
    days_back: int = Query(90, ge=1, le=365, description="Number of days to look back for lineage events"),
    include_columns: bool = Query(False, description="Include column-level lineage"),
    layout_algorithm: str = Query("hierarchical", description="Layout algorithm for visualization"),
    page: int = Query(1, ge=1, description="Page number (1-indexed)"),
    page_size: int = Query(50, ge=10, le=500, description="Items per page"),
    current_user: Dict = Depends(require_auth)
) -> LineageResponse:
    """
    Get lineage for a specific table with pagination support.

    Returns lineage graph showing upstream and/or downstream dependencies
    for the specified table using Unity Catalog metadata with recursive CTEs.
    Results are paginated to handle large lineage graphs efficiently.

    Pagination parameters:
        - page: Page number (1-indexed)
        - page_size: Number of nodes per page (10-500)
        - days_back: Number of days to look back for lineage events (1-365)

    The full lineage is extracted from system.access.table_lineage (with caching),
    then paginated on the server side. Edges are filtered to include only those
    connecting nodes in the current page.
    """
    start_time = datetime.now()

    try:
        logger.info(f"Getting table lineage for {catalog}.{schema}.{table} (page={page}, page_size={page_size}, days_back={days_back})")

        # Initialize services
        connector = DatabricksConnector()
        extractor = LineageExtractor(connector)
        processor = LineageProcessor()
        visualizer = LineageVisualizer()

        # Convert direction string to enum
        direction_enum = LineageDirection(direction.lower())

        # Extract full lineage using Unity Catalog metadata (with caching)
        full_graph = extractor.extract_table_lineage_from_metadata(
            catalog=catalog,
            schema=schema,
            table=table,
            direction=direction_enum,
            depth=depth,
            days_back=days_back
        )

        # Calculate pagination boundaries
        total_nodes = len(full_graph.nodes)
        total_edges = len(full_graph.edges)
        total_pages = (total_nodes + page_size - 1) // page_size if total_nodes > 0 else 1

        start_idx = (page - 1) * page_size
        end_idx = min(start_idx + page_size, total_nodes)

        # Paginate nodes
        paginated_nodes = full_graph.nodes[start_idx:end_idx]
        paginated_node_ids = {node.id for node in paginated_nodes}

        # Filter edges to only include those connecting paginated nodes
        paginated_edges = [
            edge for edge in full_graph.edges
            if edge.source in paginated_node_ids or edge.target in paginated_node_ids
        ]

        # Create paginated graph
        from app.models.lineage import LineageGraph
        paginated_graph = LineageGraph(
            nodes=paginated_nodes,
            edges=paginated_edges,
            metadata={
                **full_graph.metadata,
                "pagination": {
                    "page": page,
                    "page_size": page_size,
                    "total_nodes": total_nodes,
                    "total_edges": total_edges,
                    "total_pages": total_pages,
                    "has_next": page < total_pages,
                    "has_previous": page > 1,
                    "start_idx": start_idx,
                    "end_idx": end_idx
                }
            }
        )

        # Process graph
        processed_graph = processor.process_graph(paginated_graph)

        # Generate visualization data
        visualizer.generate_visualization_data(
            processed_graph,
            layout_algorithm=layout_algorithm
        )

        # Calculate query time
        query_time = int((datetime.now() - start_time).total_seconds() * 1000)

        return LineageResponse(
            graph=processed_graph,
            query_time_ms=query_time,
            truncated=total_nodes > end_idx
        )
        
    except Exception as e:
        logger.error(f"Error getting table lineage: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/model/{model_id}")
async def get_model_lineage(
    model_id: str,
    include_upstream: bool = Query(True, description="Include upstream tables"),
    include_downstream: bool = Query(True, description="Include downstream usage"),
    depth: int = Query(3, ge=1, le=10, description="Maximum depth to traverse"),
    layout_algorithm: str = Query("hierarchical", description="Layout algorithm"),
    current_user: Dict = Depends(require_auth)
) -> LineageResponse:
    """
    Get lineage for a semantic model.
    
    Returns lineage graph showing the model's dependencies on tables
    and any downstream usage in metrics or dashboards.
    """
    start_time = datetime.now()
    
    try:
        logger.info(f"Getting model lineage for {model_id}")
        
        # Initialize services
        connector = DatabricksConnector()
        extractor = LineageExtractor(connector)
        processor = LineageProcessor()
        visualizer = LineageVisualizer()
        
        # Extract lineage
        graph = extractor.extract_model_lineage(
            model_id=model_id,
            include_upstream=include_upstream,
            include_downstream=include_downstream,
            depth=depth
        )
        
        # Process graph
        processed_graph = processor.process_graph(graph)
        
        # Generate visualization data
        visualizer.generate_visualization_data(
            processed_graph,
            layout_algorithm=layout_algorithm
        )
        
        # Calculate query time
        query_time = int((datetime.now() - start_time).total_seconds() * 1000)
        
        return LineageResponse(
            graph=processed_graph,
            query_time_ms=query_time,
            truncated=False
        )
        
    except Exception as e:
        logger.error(f"Error getting model lineage: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/column")
async def get_column_lineage(
    catalog: str = Query(..., description="Catalog name"),
    schema: str = Query(..., description="Schema name"),
    table: str = Query(..., description="Table name"),
    column: str = Query(..., description="Column name"),
    layout_algorithm: str = Query("hierarchical", description="Layout algorithm"),
    current_user: Dict = Depends(require_auth)
) -> LineageResponse:
    """
    Get column-level lineage.
    
    Returns lineage graph showing how a specific column is derived
    from source columns in upstream tables.
    """
    start_time = datetime.now()
    
    try:
        logger.info(f"Getting column lineage for {catalog}.{schema}.{table}.{column}")
        
        # Initialize services
        connector = DatabricksConnector()
        extractor = LineageExtractor(connector)
        processor = LineageProcessor()
        visualizer = LineageVisualizer()
        
        # Extract lineage
        graph = extractor.extract_column_lineage(
            catalog=catalog,
            schema=schema,
            table=table,
            column=column
        )
        
        # Process graph
        processed_graph = processor.process_graph(graph)
        
        # Generate visualization data
        visualizer.generate_visualization_data(
            processed_graph,
            layout_algorithm=layout_algorithm
        )
        
        # Calculate query time
        query_time = int((datetime.now() - start_time).total_seconds() * 1000)
        
        return LineageResponse(
            graph=processed_graph,
            query_time_ms=query_time,
            truncated=False
        )
        
    except Exception as e:
        logger.error(f"Error getting column lineage: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/impact")
async def analyze_impact(
    request: ImpactAnalysisRequest,
    current_user: Dict = Depends(require_auth)
) -> ImpactAnalysisResponse:
    """
    Analyze impact of changes to an entity.
    
    Calculates which downstream entities would be affected
    by changes to the specified entity.
    """
    try:
        logger.info(f"Analyzing impact for {request.entity_type} {request.entity_id}")
        
        # Initialize services
        connector = DatabricksConnector()
        extractor = LineageExtractor(connector)
        processor = LineageProcessor()
        
        # Extract lineage based on entity type
        if request.entity_type.upper() == "TABLE":
            # Parse entity_id as catalog.schema.table
            parts = request.entity_id.split(".")
            if len(parts) != 3:
                raise HTTPException(status_code=400, detail="Table entity_id must be in format catalog.schema.table")
            
            graph = extractor.extract_table_lineage(
                catalog=parts[0],
                schema=parts[1],
                table=parts[2],
                direction=LineageDirection.DOWNSTREAM,
                depth=request.depth
            )
        elif request.entity_type.upper() == "MODEL":
            graph = extractor.extract_model_lineage(
                model_id=request.entity_id,
                include_upstream=False,
                include_downstream=True,
                depth=request.depth
            )
        else:
            raise HTTPException(status_code=400, detail=f"Unsupported entity type: {request.entity_type}")
        
        # Calculate impact
        impact_analysis = processor.calculate_impact_analysis(graph, request.entity_id)
        
        # Generate impact graph (subset of nodes that are impacted)
        impacted_node_ids = set(impact_analysis["directly_impacted"] + impact_analysis["indirectly_impacted"])
        impact_nodes = [node for node in graph.nodes if node.id in impacted_node_ids]
        impact_edges = [
            edge for edge in graph.edges 
            if edge.source in impacted_node_ids and edge.target in impacted_node_ids
        ]
        
        from app.models.lineage import LineageGraph
        impact_graph = LineageGraph(
            nodes=impact_nodes,
            edges=impact_edges,
            metadata={"impact_analysis": True}
        )
        
        # Generate warnings
        warnings = []
        if impact_analysis["total_impact_count"] > 50:
            warnings.append("Large number of impacted entities. Consider phased rollout.")
        
        if "MODEL" in impact_analysis.get("impact_by_type", {}):
            warnings.append("Changes will affect semantic models. Update model documentation.")
        
        return ImpactAnalysisResponse(
            directly_impacted=impact_analysis["directly_impacted"],
            indirectly_impacted=impact_analysis["indirectly_impacted"],
            total_impact_count=impact_analysis["total_impact_count"],
            impact_graph=impact_graph,
            warnings=warnings
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error analyzing impact: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/export")
async def export_lineage(
    request: LineageExportRequest,
    current_user: Dict = Depends(require_auth)
) -> Response:
    """
    Export lineage visualization in various formats.
    
    Supports SVG, DOT (Graphviz), and JSON export formats.
    """
    try:
        logger.info(f"Exporting lineage as {request.format}")
        
        # Initialize visualizer
        visualizer = LineageVisualizer()
        
        # Generate export based on format
        if request.format.lower() == "svg":
            content = visualizer.export_as_svg(request.graph)
            media_type = "image/svg+xml"
            filename = "lineage.svg"
            
        elif request.format.lower() == "dot":
            content = visualizer.export_as_dot(request.graph)
            media_type = "text/plain"
            filename = "lineage.dot"
            
        elif request.format.lower() == "json":
            content = visualizer.export_as_json(request.graph)
            media_type = "application/json"
            filename = "lineage.json"
            
        else:
            raise HTTPException(status_code=400, detail=f"Unsupported export format: {request.format}")
        
        # Return file response
        return Response(
            content=content,
            media_type=media_type,
            headers={
                "Content-Disposition": f"attachment; filename={filename}"
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error exporting lineage: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/stats")
async def get_lineage_stats(
    catalog: Optional[str] = Query(None, description="Filter by catalog"),
    schema: Optional[str] = Query(None, description="Filter by schema"),
    current_user: Dict = Depends(require_auth)
) -> Dict[str, Any]:
    """
    Get lineage statistics for the workspace.
    
    Returns aggregated statistics about lineage coverage,
    node types, and common patterns.
    """
    try:
        logger.info("Getting lineage statistics")
        
        # Initialize services
        connector = DatabricksConnector()
        
        # Build query with optional filters
        where_clauses = ["true"]
        parameters = {}

        if catalog:
            where_clauses.append("table_catalog = :catalog")
            parameters["catalog"] = catalog
        if schema:
            where_clauses.append("table_schema = :schema")
            parameters["schema"] = schema

        where_clause = " and ".join(where_clauses)

        # Get table counts by type
        table_stats_query = f"""
        SELECT
            table_type,
            COUNT(*) as count
        FROM information_schema.tables
        WHERE {where_clause}
        GROUP BY table_type
        """

        table_stats = connector.execute_query(table_stats_query, parameters if parameters else None)
        
        # Get lineage coverage (tables with lineage)
        lineage_where_clauses = ["true"]
        lineage_parameters = {}

        if catalog:
            lineage_where_clauses.append('SPLIT(source_name, ".")[0] = :catalog')
            lineage_parameters["catalog"] = catalog

        lineage_where_clause = " and ".join(lineage_where_clauses)

        lineage_coverage_query = f"""
        SELECT
            COUNT(DISTINCT source_name) + COUNT(DISTINCT target_name) as tables_with_lineage,
            COUNT(*) as total_lineage_edges
        FROM system.lineage.table_lineage
        WHERE {lineage_where_clause}
        """

        try:
            lineage_coverage = connector.execute_query(lineage_coverage_query, lineage_parameters if lineage_parameters else None)
        except Exception:
            # Fallback if lineage tables don't exist
            lineage_coverage = [{"tables_with_lineage": 0, "total_lineage_edges": 0}]
        
        # Compile statistics
        stats = {
            "table_statistics": {
                "by_type": {row["table_type"]: row["count"] for row in table_stats},
                "total_tables": sum(row["count"] for row in table_stats)
            },
            "lineage_statistics": {
                "tables_with_lineage": lineage_coverage[0]["tables_with_lineage"],
                "total_lineage_edges": lineage_coverage[0]["total_lineage_edges"],
                "coverage_percentage": (
                    lineage_coverage[0]["tables_with_lineage"] / 
                    max(1, sum(row["count"] for row in table_stats))
                ) * 100 if table_stats else 0
            },
            "filters_applied": {
                "catalog": catalog,
                "schema": schema
            },
            "generated_at": datetime.now().isoformat()
        }
        
        return stats
        
    except Exception as e:
        logger.error(f"Error getting lineage statistics: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/debug/test")
async def debug_lineage_test(
    catalog: str = Query(..., description="Catalog name"),
    schema: str = Query(..., description="Schema name"),
    table: str = Query(..., description="Table name"),
    days_back: int = Query(90, ge=1, le=365, description="Number of days to look back"),
    current_user: Dict = Depends(require_auth)
) -> Dict[str, Any]:
    """
    Debug endpoint to test lineage queries and see raw results.

    Returns the raw results from the simple lineage test query to help diagnose
    why lineage extraction might not be working.
    """
    try:
        from app.services.lineage_queries import SIMPLE_LINEAGE_TEST
        from app.integrations.databricks import DatabricksConnector

        connector = DatabricksConnector()
        full_table_name = f"{catalog}.{schema}.{table}"

        parameters = {
            "table_name": full_table_name,
            "days_back": days_back
        }

        logger.info(f"Running lineage debug test for {full_table_name}")

        # Test simple query
        test_results = connector.execute_query(SIMPLE_LINEAGE_TEST, parameters)

        return {
            "table_name": full_table_name,
            "parameters": parameters,
            "record_count": len(test_results),
            "sample_records": test_results[:5] if test_results else [],
            "all_records": test_results
        }
    except Exception as e:
        logger.error(f"Debug test failed: {e}")
        logger.exception("Full traceback:")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/cache/stats")
async def get_cache_stats(
    current_user: Dict = Depends(require_auth)
) -> Dict[str, Any]:
    """
    Get lineage cache statistics.

    Returns cache performance metrics including:
    - Cache configuration (enabled, TTL, max size)
    - Hit/miss statistics and hit rate
    - Current cache size and eviction count

    This endpoint is useful for monitoring cache performance
    and identifying if cache tuning is needed.
    """
    try:
        from app.services.lineage_cache import get_lineage_cache
        from app.core.config import settings

        cache = get_lineage_cache()
        stats = cache.get_stats()

        return {
            "cache_configuration": {
                "enabled": settings.LINEAGE_CACHE_ENABLED,
                "ttl_minutes": settings.LINEAGE_CACHE_TTL_MINUTES,
                "ttl_seconds": stats["default_ttl_seconds"],
                "max_size": stats["max_size"]
            },
            "statistics": {
                "hits": stats["hits"],
                "misses": stats["misses"],
                "evictions": stats["evictions"],
                "total_queries": stats["total_queries"],
                "hit_rate_percent": round(stats["hit_rate"], 2),
                "current_size": stats["current_size"],
                "utilization_percent": round(
                    (stats["current_size"] / stats["max_size"] * 100) if stats["max_size"] > 0 else 0,
                    2
                )
            }
        }
    except Exception as e:
        logger.error(f"Error getting cache statistics: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/cache/clear")
async def clear_cache(
    current_user: Dict = Depends(require_auth)
) -> Dict[str, str]:
    """
    Clear lineage cache.

    Removes all cached lineage query results. This endpoint is useful for:
    - Forcing fresh lineage data after schema changes
    - Troubleshooting cache-related issues
    - Testing cache behavior

    Note: Future requests will require fresh queries to Unity Catalog,
    which may result in slower response times until cache is repopulated.
    """
    try:
        from app.services.lineage_cache import get_lineage_cache

        # TODO: Add admin check when role-based access control is implemented
        # if not current_user.get("is_admin"):
        #     raise HTTPException(status_code=403, detail="Admin access required")

        cache = get_lineage_cache()
        cache.clear()

        logger.info(f"Cache cleared by user {current_user.get('user_id', 'unknown')}")

        return {
            "status": "success",
            "message": "Lineage cache cleared successfully"
        }
    except Exception as e:
        logger.error(f"Error clearing cache: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/search")
async def search_lineage(
    query: str = Query(..., description="Search term"),
    entity_types: Optional[str] = Query(None, description="Comma-separated entity types to search"),
    limit: int = Query(20, ge=1, le=100, description="Maximum results to return"),
    current_user: Dict = Depends(require_auth)
) -> Dict[str, Any]:
    """
    Search for entities in lineage data.
    
    Searches table names, column names, and descriptions
    for entities matching the query term.
    """
    try:
        logger.info(f"Searching lineage for: {query}")
        
        # Initialize services
        connector = DatabricksConnector()
        
        # Parse entity types filter
        allowed_types = []
        if entity_types:
            allowed_types = [t.strip().upper() for t in entity_types.split(",")]
        
        # Search tables
        results = {"tables": [], "columns": [], "models": []}
        
        # Search in tables
        if not allowed_types or "TABLE" in allowed_types:
            table_search_query = """
            SELECT
                table_catalog,
                table_schema,
                table_name,
                table_type,
                table_comment as description
            FROM information_schema.tables
            WHERE (
                lower(table_name) like :search_pattern
                or lower(table_comment) like :search_pattern
            )
            LIMIT :limit
            """

            search_parameters = {
                "search_pattern": f"%{query.lower()}%",
                "limit": limit
            }

            table_results = connector.execute_query(table_search_query, search_parameters)
            results["tables"] = [
                {
                    "id": f"{row['table_catalog']}.{row['table_schema']}.{row['table_name']}",
                    "name": row["table_name"],
                    "type": "TABLE",
                    "catalog": row["table_catalog"],
                    "schema": row["table_schema"],
                    "description": row.get("description"),
                    "table_type": row.get("table_type")
                }
                for row in table_results
            ]
        
        # Search in columns
        if not allowed_types or "COLUMN" in allowed_types:
            column_search_query = """
            SELECT
                table_catalog,
                table_schema,
                table_name,
                column_name,
                data_type,
                comment as description
            FROM information_schema.columns
            WHERE (
                lower(column_name) like :search_pattern
                or lower(comment) like :search_pattern
            )
            LIMIT :limit
            """

            search_parameters = {
                "search_pattern": f"%{query.lower()}%",
                "limit": limit
            }

            column_results = connector.execute_query(column_search_query, search_parameters)
            results["columns"] = [
                {
                    "id": f"{row['table_catalog']}.{row['table_schema']}.{row['table_name']}.{row['column_name']}",
                    "name": row["column_name"],
                    "type": "COLUMN",
                    "catalog": row["table_catalog"],
                    "schema": row["table_schema"],
                    "table": row["table_name"],
                    "data_type": row["data_type"],
                    "description": row.get("description")
                }
                for row in column_results
            ]
        
        # Count total results
        total_results = sum(len(results[key]) for key in results)
        
        return {
            "query": query,
            "total_results": total_results,
            "results": results,
            "limit": limit,
            "entity_types_filter": allowed_types
        }
        
    except Exception as e:
        logger.error(f"Error searching lineage: {e}")
        raise HTTPException(status_code=500, detail=str(e))
