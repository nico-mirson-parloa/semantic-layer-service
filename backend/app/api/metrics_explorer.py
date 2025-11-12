"""
API endpoints for the Metrics Explorer functionality
"""
from fastapi import APIRouter, HTTPException
from typing import List, Dict, Any, Optional
import os
import yaml
from pathlib import Path
import structlog

logger = structlog.get_logger()

router = APIRouter()

@router.get("/metrics")
async def get_all_metrics():
    """
    Get all metrics from all semantic models with enhanced metadata
    """
    try:
        models_path = Path("semantic-models")
        all_metrics = []
        
        if not models_path.exists():
            return []
            
        for yaml_file in models_path.glob("*.yml"):
            try:
                with open(yaml_file, 'r') as f:
                    content = yaml.safe_load(f)
                
                if content and isinstance(content, dict):
                    model_name = content.get('name', yaml_file.stem)
                    model_metrics = content.get('metrics', [])
                    model_dimensions = content.get('dimensions', [])
                    model_entities = content.get('entities', [])
                    model_measures = content.get('measures', [])
                    
                    for metric in model_metrics:
                        metric_data = {
                            "id": f"{model_name}.{metric.get('name')}",
                            "name": metric.get('name'),
                            "description": metric.get('description'),
                            "type": metric.get('type', 'simple'),
                            "model": model_name,
                            "measure": metric.get('measure'),
                            "sql": metric.get('sql'),
                            "category": content.get('metadata', {}).get('category', 'uncategorized'),
                            "created_by": content.get('metadata', {}).get('created_by', 'unknown'),
                            "last_modified": yaml_file.stat().st_mtime,
                            "dimensions": [d.get('name') for d in model_dimensions],
                            "entities": [e.get('name') for e in model_entities],
                            "measures_available": [m.get('name') for m in model_measures],
                            "file_path": str(yaml_file),
                            "natural_language_source": content.get('metadata', {}).get('natural_language_source')
                        }
                        all_metrics.append(metric_data)
                        
            except Exception as e:
                logger.error(f"Error reading {yaml_file}: {e}")
                continue
                
        return all_metrics
        
    except Exception as e:
        logger.error(f"Error getting metrics: {e}")
        raise HTTPException(status_code=500, detail=f"Error retrieving metrics: {str(e)}")

@router.get("/metrics/{metric_id}")
async def get_metric_detail(metric_id: str):
    """
    Get detailed information about a specific metric including lineage
    """
    try:
        # Parse metric_id (format: model_name.metric_name)
        if '.' not in metric_id:
            raise HTTPException(status_code=400, detail="Invalid metric ID format")
            
        model_name, metric_name = metric_id.split('.', 1)
        model_path = Path(f"semantic-models/{model_name}.yml")
        
        if not model_path.exists():
            raise HTTPException(status_code=404, detail=f"Model {model_name} not found")
            
        with open(model_path, 'r') as f:
            content = yaml.safe_load(f)
            
        if not content:
            raise HTTPException(status_code=404, detail="Invalid model file")
            
        # Find the specific metric
        metrics = content.get('metrics', [])
        target_metric = None
        
        for metric in metrics:
            if metric.get('name') == metric_name:
                target_metric = metric
                break
                
        if not target_metric:
            raise HTTPException(status_code=404, detail=f"Metric {metric_name} not found in model {model_name}")
            
        # Build detailed response with lineage information
        metric_detail = {
            "id": metric_id,
            "name": target_metric.get('name'),
            "description": target_metric.get('description'),
            "type": target_metric.get('type', 'simple'),
            "model": model_name,
            "measure": target_metric.get('measure'),
            "sql": target_metric.get('sql'),
            "category": content.get('metadata', {}).get('category', 'uncategorized'),
            "created_by": content.get('metadata', {}).get('created_by', 'unknown'),
            "last_modified": model_path.stat().st_mtime,
            "natural_language_source": content.get('metadata', {}).get('natural_language_source'),
            
            # Lineage information
            "lineage": {
                "upstream_tables": _extract_tables_from_sql(target_metric.get('sql', '')),
                "base_measures": [target_metric.get('measure')] if target_metric.get('measure') else [],
                "dimensions": [d.get('name') for d in content.get('dimensions', [])],
                "entities": [e.get('name') for e in content.get('entities', [])],
            },
            
            # Available slicing options
            "slicing_options": {
                "dimensions": [
                    {
                        "name": d.get('name'),
                        "type": d.get('type'),
                        "expr": d.get('expr'),
                        "description": d.get('description')
                    }
                    for d in content.get('dimensions', [])
                ],
                "entities": [
                    {
                        "name": e.get('name'),
                        "type": e.get('type'),
                        "expr": e.get('expr')
                    }
                    for e in content.get('entities', [])
                ]
            },
            
            # Model metadata
            "model_metadata": {
                "description": content.get('description'),
                "model_ref": content.get('model'),
                "total_metrics": len(content.get('metrics', [])),
                "total_dimensions": len(content.get('dimensions', [])),
                "total_entities": len(content.get('entities', [])),
                "total_measures": len(content.get('measures', []))
            }
        }
        
        return metric_detail
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting metric detail for {metric_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Error retrieving metric detail: {str(e)}")

@router.get("/metrics/search")
async def search_metrics(
    q: Optional[str] = None,
    category: Optional[str] = None,
    model: Optional[str] = None,
    type: Optional[str] = None
):
    """
    Advanced search for metrics with multiple filter options
    """
    try:
        # Get all metrics first
        all_metrics = await get_all_metrics()
        
        filtered_metrics = all_metrics
        
        # Apply filters
        if q:
            q_lower = q.lower()
            filtered_metrics = [
                m for m in filtered_metrics
                if (q_lower in m.get('name', '').lower() or
                    q_lower in m.get('description', '').lower() or
                    q_lower in m.get('model', '').lower())
            ]
            
        if category and category != 'all':
            filtered_metrics = [m for m in filtered_metrics if m.get('category') == category]
            
        if model:
            filtered_metrics = [m for m in filtered_metrics if m.get('model') == model]
            
        if type:
            filtered_metrics = [m for m in filtered_metrics if m.get('type') == type]
            
        return {
            "metrics": filtered_metrics,
            "total": len(filtered_metrics),
            "filters_applied": {
                "search": q,
                "category": category,
                "model": model,
                "type": type
            }
        }
        
    except Exception as e:
        logger.error(f"Error searching metrics: {e}")
        raise HTTPException(status_code=500, detail=f"Error searching metrics: {str(e)}")

@router.get("/metrics/categories")
async def get_metric_categories():
    """
    Get all available metric categories
    """
    try:
        metrics = await get_all_metrics()
        categories = list(set(metric.get('category', 'uncategorized') for metric in metrics))
        categories.sort()
        
        return {
            "categories": categories,
            "total": len(categories)
        }
        
    except Exception as e:
        logger.error(f"Error getting categories: {e}")
        raise HTTPException(status_code=500, detail=f"Error retrieving categories: {str(e)}")

@router.get("/metrics/models")
async def get_metric_models():
    """
    Get all models that contain metrics
    """
    try:
        metrics = await get_all_metrics()
        models = list(set(metric.get('model') for metric in metrics))
        models.sort()
        
        return {
            "models": models,
            "total": len(models)
        }
        
    except Exception as e:
        logger.error(f"Error getting models: {e}")
        raise HTTPException(status_code=500, detail=f"Error retrieving models: {str(e)}")

def _extract_tables_from_sql(sql: str) -> List[str]:
    """
    Extract table references from SQL query
    Simple regex-based extraction for demo purposes
    """
    import re
    
    if not sql:
        return []
        
    # Pattern to match table references like `catalog`.`schema`.`table`
    pattern = r'`([^`]+)`\.`([^`]+)`\.`([^`]+)`'
    matches = re.findall(pattern, sql)
    
    tables = []
    for match in matches:
        catalog, schema, table = match
        tables.append(f"{catalog}.{schema}.{table}")
        
    # Also look for simple table references
    simple_pattern = r'FROM\s+([^\s]+)'
    simple_matches = re.findall(simple_pattern, sql, re.IGNORECASE)
    
    for match in simple_matches:
        if match not in tables:
            tables.append(match)
            
    return list(set(tables))  # Remove duplicates
