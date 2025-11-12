"""
Preset metric synchronization.

This module handles syncing semantic layer metrics with Preset,
including creating calculated fields and custom metrics.
"""

import json
from typing import Dict, List, Any, Optional
from datetime import datetime
import structlog

from app.sql_api.virtual_schema import VirtualSchemaManager

logger = structlog.get_logger()


class PresetMetricSync:
    """Synchronizes semantic layer metrics with Preset."""
    
    def __init__(self, schema_manager: Optional[VirtualSchemaManager] = None):
        """Initialize metric sync."""
        self.schema_manager = schema_manager or VirtualSchemaManager()
    
    def generate_metrics_yaml(self, schema_name: str) -> str:
        """
        Generate Preset metrics YAML for a semantic model.
        
        Args:
            schema_name: Semantic model schema name
            
        Returns:
            YAML configuration for Preset metrics
        """
        table = self.schema_manager.get_table(f"{schema_name}.fact")
        if not table:
            raise ValueError(f"No fact table found for schema {schema_name}")
        
        metrics_config = {
            "version": 1,
            "metrics": []
        }
        
        # Generate metrics from semantic model
        for metric in table.semantic_model.get('metrics', []):
            preset_metric = self._convert_to_preset_metric(metric, table)
            metrics_config["metrics"].append(preset_metric)
        
        # Generate metrics from measures
        for measure in table.semantic_model.get('measures', []):
            preset_metrics = self._generate_measure_metrics(measure, table)
            metrics_config["metrics"].extend(preset_metrics)
        
        # Add common calculated metrics
        calculated_metrics = self._generate_calculated_metrics(table)
        metrics_config["metrics"].extend(calculated_metrics)
        
        import yaml
        return yaml.dump(metrics_config, default_flow_style=False, sort_keys=False)
    
    def generate_dataset_metrics(self, schema_name: str, table_name: str = "fact") -> List[Dict[str, Any]]:
        """
        Generate dataset-level metrics for Preset.
        
        Args:
            schema_name: Semantic model schema name
            table_name: Table name within schema
            
        Returns:
            List of metric configurations
        """
        table = self.schema_manager.get_table(f"{schema_name}.{table_name}")
        if not table:
            raise ValueError(f"Table {schema_name}.{table_name} not found")
        
        dataset_metrics = []
        
        # Process semantic model metrics
        for metric in table.semantic_model.get('metrics', []):
            metric_config = {
                "metric_name": f"sm_{metric['name']}",  # Prefix with sm_ for semantic metric
                "verbose_name": metric.get('description', metric['name'].replace('_', ' ').title()),
                "metric_type": "expression",
                "expression": self._get_metric_expression(metric, table),
                "description": metric.get('description', ''),
                "d3format": self._get_format_string(metric),
                "warning_text": None,
                "extra": json.dumps({
                    "semantic_layer_metric": True,
                    "source_metric": metric['name'],
                    "metric_type": metric.get('type', 'simple')
                })
            }
            dataset_metrics.append(metric_config)
        
        # Add standard aggregation metrics for measures
        for measure in table.semantic_model.get('measures', []):
            measure_metrics = self._create_measure_aggregations(measure)
            dataset_metrics.extend(measure_metrics)
        
        return dataset_metrics
    
    def _convert_to_preset_metric(self, metric: Dict[str, Any], table) -> Dict[str, Any]:
        """Convert semantic metric to Preset metric format."""
        metric_type = metric.get('type', 'simple')
        
        preset_metric = {
            "metric_name": metric['name'],
            "verbose_name": metric.get('description', metric['name'].replace('_', ' ').title()),
            "metric_type": self._map_metric_type(metric_type),
            "owners": [],
            "is_restricted": False,
            "d3format": ".3s",  # Default format
        }
        
        # Set expression based on type
        if metric_type == 'simple':
            measure_name = metric.get('measure')
            if measure_name:
                measure = self._find_measure(measure_name, table)
                if measure:
                    agg = measure.get('agg', 'sum').upper()
                    expr = measure.get('expr', measure_name)
                    preset_metric["expression"] = f"{agg}({expr})"
                else:
                    preset_metric["expression"] = f"SUM({measure_name})"
        
        elif metric_type == 'ratio':
            num = metric.get('numerator')
            den = metric.get('denominator')
            preset_metric["expression"] = f"SUM({num}) / NULLIF(SUM({den}), 0)"
            preset_metric["d3format"] = ".2%"  # Percentage format for ratios
        
        elif metric_type == 'derived':
            preset_metric["expression"] = metric.get('expr', 'NULL')
        
        # Add metadata
        preset_metric["extra"] = {
            "certification": {
                "certified_by": "Semantic Layer",
                "certification_details": f"Auto-synced from {table.semantic_model.get('name')} model"
            },
            "warning_markdown": None
        }
        
        return preset_metric
    
    def _generate_measure_metrics(self, measure: Dict[str, Any], table) -> List[Dict[str, Any]]:
        """Generate multiple metrics from a measure."""
        metrics = []
        measure_name = measure['name']
        expr = measure.get('expr', measure_name)
        
        # Standard aggregations
        aggregations = {
            'sum': {
                'name': f"sum_{measure_name}",
                'verbose': f"Total {measure_name.replace('_', ' ').title()}",
                'expression': f"SUM({expr})",
                'format': ".3s"
            },
            'avg': {
                'name': f"avg_{measure_name}",
                'verbose': f"Average {measure_name.replace('_', ' ').title()}",
                'expression': f"AVG({expr})",
                'format': ".2f"
            },
            'min': {
                'name': f"min_{measure_name}",
                'verbose': f"Minimum {measure_name.replace('_', ' ').title()}",
                'expression': f"MIN({expr})",
                'format': ".3s"
            },
            'max': {
                'name': f"max_{measure_name}",
                'verbose': f"Maximum {measure_name.replace('_', ' ').title()}",
                'expression': f"MAX({expr})",
                'format': ".3s"
            }
        }
        
        # Create metrics based on measure type
        default_agg = measure.get('agg', 'sum')
        
        # Always create the default aggregation
        if default_agg in aggregations:
            agg_config = aggregations[default_agg]
            metrics.append({
                "metric_name": agg_config['name'],
                "verbose_name": agg_config['verbose'],
                "metric_type": "expression",
                "expression": agg_config['expression'],
                "d3format": agg_config['format'],
                "description": f"{default_agg.upper()} aggregation of {measure_name}"
            })
        
        # For numeric measures, optionally add other aggregations
        if default_agg == 'sum':
            # Also add average
            agg_config = aggregations['avg']
            metrics.append({
                "metric_name": agg_config['name'],
                "verbose_name": agg_config['verbose'],
                "metric_type": "expression",
                "expression": agg_config['expression'],
                "d3format": agg_config['format'],
                "description": f"Average of {measure_name}"
            })
        
        return metrics
    
    def _generate_calculated_metrics(self, table) -> List[Dict[str, Any]]:
        """Generate common calculated metrics."""
        calculated_metrics = []
        
        # Row count
        calculated_metrics.append({
            "metric_name": "row_count",
            "verbose_name": "Row Count",
            "metric_type": "count",
            "expression": "COUNT(*)",
            "d3format": ".3s",
            "description": "Total number of records"
        })
        
        # Distinct counts for key dimensions
        for col in table.columns:
            if col.semantic_type == 'entity' and col.is_primary_key:
                calculated_metrics.append({
                    "metric_name": f"unique_{col.name}",
                    "verbose_name": f"Unique {col.name.replace('_', ' ').title()}",
                    "metric_type": "count_distinct", 
                    "expression": f"COUNT(DISTINCT {col.name})",
                    "d3format": ".3s",
                    "description": f"Count of unique {col.name} values"
                })
                break  # Only one primary entity count
        
        # Period-over-period calculations (if time dimension exists)
        time_dim = self._find_time_dimension(table)
        if time_dim:
            # YoY growth for first revenue/amount measure
            revenue_measure = self._find_revenue_measure(table)
            if revenue_measure:
                expr = revenue_measure.get('expr', revenue_measure['name'])
                calculated_metrics.append({
                    "metric_name": f"{revenue_measure['name']}_yoy_growth",
                    "verbose_name": f"{revenue_measure['name'].replace('_', ' ').title()} YoY Growth",
                    "metric_type": "expression",
                    "expression": f"""
                        (SUM(CASE WHEN {time_dim.name} >= DATE_TRUNC('year', CURRENT_DATE) 
                                  AND {time_dim.name} < CURRENT_DATE 
                             THEN {expr} END) 
                         - 
                         SUM(CASE WHEN {time_dim.name} >= DATE_TRUNC('year', CURRENT_DATE - INTERVAL '1 year')
                                  AND {time_dim.name} < CURRENT_DATE - INTERVAL '1 year'
                             THEN {expr} END))
                        / 
                        NULLIF(SUM(CASE WHEN {time_dim.name} >= DATE_TRUNC('year', CURRENT_DATE - INTERVAL '1 year')
                                        AND {time_dim.name} < CURRENT_DATE - INTERVAL '1 year'
                                   THEN {expr} END), 0)
                    """,
                    "d3format": ".1%",
                    "description": "Year-over-year growth rate"
                })
        
        return calculated_metrics
    
    def _create_measure_aggregations(self, measure: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Create standard aggregation metrics for a measure."""
        metrics = []
        measure_name = measure['name']
        expr = measure.get('expr', measure_name)
        agg = measure.get('agg', 'sum')
        
        # Primary aggregation
        metrics.append({
            "metric_name": f"{agg}_{measure_name}",
            "verbose_name": f"{agg.title()} of {measure_name.replace('_', ' ').title()}",
            "metric_type": agg if agg in ['sum', 'avg', 'min', 'max', 'count'] else 'expression',
            "expression": f"{agg.upper()}({expr})" if agg not in ['sum', 'avg', 'min', 'max', 'count'] else None,
            "column": expr if agg in ['sum', 'avg', 'min', 'max'] else None,
            "aggregate": agg.upper() if agg in ['sum', 'avg', 'min', 'max'] else None,
            "description": measure.get('description', f"{agg.title()} of {measure_name}"),
            "d3format": self._get_measure_format(measure)
        })
        
        return metrics
    
    def _map_metric_type(self, semantic_type: str) -> str:
        """Map semantic metric type to Preset metric type."""
        mapping = {
            'simple': 'expression',
            'ratio': 'expression',
            'derived': 'expression',
            'cumulative': 'expression'
        }
        return mapping.get(semantic_type, 'expression')
    
    def _find_measure(self, measure_name: str, table) -> Optional[Dict[str, Any]]:
        """Find measure by name in semantic model."""
        for measure in table.semantic_model.get('measures', []):
            if measure['name'] == measure_name:
                return measure
        return None
    
    def _find_time_dimension(self, table) -> Optional[Any]:
        """Find time dimension column."""
        for col in table.columns:
            if col.semantic_type == 'dimension' and col.data_type in ['timestamp', 'date']:
                return col
        return None
    
    def _find_revenue_measure(self, table) -> Optional[Dict[str, Any]]:
        """Find a revenue-related measure."""
        # Look for common revenue field names
        revenue_keywords = ['revenue', 'sales', 'amount', 'total', 'value']
        
        for measure in table.semantic_model.get('measures', []):
            measure_name_lower = measure['name'].lower()
            if any(keyword in measure_name_lower for keyword in revenue_keywords):
                return measure
        
        # Return first numeric measure if no revenue field found
        return table.semantic_model.get('measures', [{}])[0] if table.semantic_model.get('measures') else None
    
    def _get_metric_expression(self, metric: Dict[str, Any], table) -> str:
        """Get SQL expression for a metric."""
        metric_type = metric.get('type', 'simple')
        
        if metric_type == 'simple':
            measure_name = metric.get('measure')
            if measure_name:
                measure = self._find_measure(measure_name, table)
                if measure:
                    agg = measure.get('agg', 'sum').upper()
                    expr = measure.get('expr', measure_name)
                    return f"{agg}({expr})"
            return f"SUM({measure_name})"
        
        elif metric_type == 'ratio':
            num = metric.get('numerator')
            den = metric.get('denominator')
            return f"CAST(SUM({num}) AS FLOAT) / NULLIF(SUM({den}), 0)"
        
        elif metric_type == 'derived':
            return metric.get('expr', 'NULL')
        
        return "NULL"
    
    def _get_format_string(self, metric: Dict[str, Any]) -> str:
        """Get D3 format string for metric."""
        metric_type = metric.get('type', 'simple')
        
        if metric_type == 'ratio' or 'rate' in metric.get('name', '').lower():
            return ".1%"  # Percentage with 1 decimal
        elif 'count' in metric.get('name', '').lower():
            return ",.0f"  # Integer with thousands separator
        elif 'currency' in metric.get('name', '').lower() or 'revenue' in metric.get('name', '').lower():
            return "$,.0f"  # Currency format
        else:
            return ".3s"  # Default: SI prefix notation
    
    def _get_measure_format(self, measure: Dict[str, Any]) -> str:
        """Get D3 format string for measure."""
        measure_name = measure.get('name', '').lower()
        
        if any(term in measure_name for term in ['price', 'cost', 'revenue', 'amount', 'value']):
            return "$,.2f"  # Currency with 2 decimals
        elif 'count' in measure_name:
            return ",.0f"  # Integer with thousands separator  
        elif 'rate' in measure_name or 'percent' in measure_name:
            return ".1%"  # Percentage
        else:
            return ",.2f"  # Default: 2 decimals with separator




