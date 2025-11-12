"""
Preset dashboard builder for semantic models.

This module helps create dashboard templates and charts
based on semantic model definitions.
"""

import json
from typing import Dict, List, Any, Optional
from datetime import datetime
import structlog

from app.sql_api.virtual_schema import VirtualSchemaManager, VirtualTable

logger = structlog.get_logger()


class PresetDashboardBuilder:
    """Builds Preset dashboards from semantic models."""
    
    # Chart type mappings based on data characteristics
    CHART_TYPES = {
        'time_series': 'line',
        'comparison': 'bar',
        'distribution': 'histogram',
        'composition': 'pie',
        'relationship': 'scatter',
        'geo': 'world_map',
        'table': 'table',
        'big_number': 'big_number_total',
        'pivot': 'pivot_table_v2'
    }
    
    def __init__(self, schema_manager: Optional[VirtualSchemaManager] = None):
        """Initialize dashboard builder."""
        self.schema_manager = schema_manager or VirtualSchemaManager()
    
    def generate_dashboard_template(
        self,
        schema_name: str,
        dashboard_name: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Generate a complete dashboard template for a semantic model.
        
        Args:
            schema_name: Semantic model schema name
            dashboard_name: Optional dashboard name
            
        Returns:
            Dashboard configuration for Preset
        """
        # Get the main fact table
        fact_table = self.schema_manager.get_table(f"{schema_name}.fact")
        if not fact_table:
            raise ValueError(f"No fact table found for schema {schema_name}")
        
        model_name = fact_table.semantic_model.get('name', schema_name.replace('sem_', ''))
        dashboard_name = dashboard_name or f"{model_name.replace('_', ' ').title()} Dashboard"
        
        # Generate charts based on semantic model
        charts = []
        
        # 1. KPI Big Numbers
        kpi_charts = self._generate_kpi_charts(fact_table, schema_name)
        charts.extend(kpi_charts)
        
        # 2. Time Series Charts
        time_charts = self._generate_time_series_charts(fact_table, schema_name)
        charts.extend(time_charts)
        
        # 3. Breakdown Charts
        breakdown_charts = self._generate_breakdown_charts(fact_table, schema_name)
        charts.extend(breakdown_charts)
        
        # 4. Detailed Table
        table_chart = self._generate_table_chart(fact_table, schema_name)
        charts.append(table_chart)
        
        # Create dashboard layout
        layout = self._generate_layout(charts)
        
        return {
            "dashboard_title": dashboard_name,
            "description": f"Auto-generated dashboard for {model_name} semantic model",
            "css": "",
            "json_metadata": json.dumps({
                "timed_refresh_immune_slices": [],
                "expanded_slices": {},
                "refresh_frequency": 0,
                "default_filters": "{}",
                "color_scheme": "supersetColors",
                "label_colors": {},
                "shared_label_colors": {},
                "color_scheme_domain": [],
                "cross_filters_enabled": True,
                "positions": layout
            }),
            "slices": charts,
            "created_on": datetime.utcnow().isoformat(),
            "changed_on": datetime.utcnow().isoformat()
        }
    
    def _generate_kpi_charts(self, table: VirtualTable, schema_name: str) -> List[Dict[str, Any]]:
        """Generate KPI big number charts."""
        charts = []
        
        # Create big numbers for key metrics
        for idx, metric in enumerate(table.semantic_model.get('metrics', [])[:4]):
            chart = {
                "slice_name": metric.get('description', metric['name']),
                "viz_type": "big_number_total",
                "datasource_type": "table",
                "datasource_name": f"{schema_name}.fact",
                "params": json.dumps({
                    "datasource": f"{schema_name}.fact",
                    "viz_type": "big_number_total",
                    "metric": {
                        "expressionType": "SQL",
                        "sqlExpression": self._get_metric_sql(metric, table),
                        "column": None,
                        "aggregate": None,
                        "label": metric['name']
                    },
                    "adhoc_filters": [],
                    "header_font_size": 0.4,
                    "subheader_font_size": 0.15,
                    "y_axis_format": "SMART_NUMBER",
                    "time_format": "%Y-%m-%d",
                    "time_range": "Last quarter",
                    "show_trend_line": True,
                    "start_y_axis_at_zero": True
                }),
                "cache_timeout": None,
                "description": metric.get('description', '')
            }
            charts.append(chart)
        
        return charts
    
    def _generate_time_series_charts(self, table: VirtualTable, schema_name: str) -> List[Dict[str, Any]]:
        """Generate time series charts."""
        charts = []
        
        # Find time dimension
        time_col = self._find_time_dimension(table)
        if not time_col:
            return charts
        
        # Create time series for top metrics
        for metric in table.semantic_model.get('metrics', [])[:2]:
            chart = {
                "slice_name": f"{metric['name']} Over Time",
                "viz_type": "line",
                "datasource_type": "table",
                "datasource_name": f"{schema_name}.fact",
                "params": json.dumps({
                    "datasource": f"{schema_name}.fact",
                    "viz_type": "line",
                    "x_axis": time_col.name,
                    "time_grain_sqla": "P1D",
                    "x_axis_label": time_col.name.replace('_', ' ').title(),
                    "metrics": [{
                        "expressionType": "SQL",
                        "sqlExpression": self._get_metric_sql(metric, table),
                        "column": None,
                        "aggregate": None,
                        "label": metric['name']
                    }],
                    "adhoc_filters": [],
                    "groupby": [],
                    "time_range": "Last quarter",
                    "row_limit": 10000,
                    "line_interpolation": "linear",
                    "rolling_type": "None",
                    "show_legend": True,
                    "show_markers": True,
                    "y_axis_format": "SMART_NUMBER"
                }),
                "cache_timeout": None,
                "description": f"Time series analysis of {metric['name']}"
            }
            charts.append(chart)
        
        return charts
    
    def _generate_breakdown_charts(self, table: VirtualTable, schema_name: str) -> List[Dict[str, Any]]:
        """Generate breakdown/distribution charts."""
        charts = []
        
        # Find categorical dimensions
        cat_dims = [col for col in table.columns 
                   if col.semantic_type == 'dimension' 
                   and col.data_type in ['text', 'varchar', 'character varying']][:2]
        
        if not cat_dims:
            return charts
        
        # Create bar charts for dimensional breakdowns
        for dim in cat_dims:
            for metric in table.semantic_model.get('metrics', [])[:1]:
                chart = {
                    "slice_name": f"{metric['name']} by {dim.name.replace('_', ' ').title()}",
                    "viz_type": "bar",
                    "datasource_type": "table", 
                    "datasource_name": f"{schema_name}.fact",
                    "params": json.dumps({
                        "datasource": f"{schema_name}.fact",
                        "viz_type": "bar",
                        "x_axis": dim.name,
                        "metrics": [{
                            "expressionType": "SQL",
                            "sqlExpression": self._get_metric_sql(metric, table),
                            "column": None,
                            "aggregate": None,
                            "label": metric['name']
                        }],
                        "adhoc_filters": [],
                        "groupby": [dim.name],
                        "time_range": "Last quarter",
                        "row_limit": 25,
                        "order_desc": True,
                        "color_scheme": "supersetColors",
                        "show_legend": False,
                        "show_bar_value": True,
                        "bar_stacked": False,
                        "y_axis_format": "SMART_NUMBER",
                        "bottom_margin": "auto"
                    }),
                    "cache_timeout": None,
                    "description": f"Distribution of {metric['name']} across {dim.name}"
                }
                charts.append(chart)
        
        return charts
    
    def _generate_table_chart(self, table: VirtualTable, schema_name: str) -> Dict[str, Any]:
        """Generate detailed table chart."""
        # Select key columns for the table
        columns = []
        
        # Add dimensions
        for col in table.columns[:10]:  # Limit columns
            if col.semantic_type in ['dimension', 'entity']:
                columns.append(col.name)
        
        # Add metrics
        metrics = []
        for metric in table.semantic_model.get('metrics', [])[:3]:
            metrics.append({
                "expressionType": "SQL",
                "sqlExpression": self._get_metric_sql(metric, table),
                "column": None,
                "aggregate": None,
                "label": metric['name']
            })
        
        return {
            "slice_name": "Detailed Data Table",
            "viz_type": "table",
            "datasource_type": "table",
            "datasource_name": f"{schema_name}.fact",
            "params": json.dumps({
                "datasource": f"{schema_name}.fact",
                "viz_type": "table",
                "query_mode": "aggregate",
                "groupby": columns,
                "metrics": metrics,
                "all_columns": [],
                "percent_metrics": [],
                "adhoc_filters": [],
                "order_by_cols": [],
                "row_limit": 1000,
                "server_page_length": 10,
                "order_desc": True,
                "table_timestamp_format": "%Y-%m-%d %H:%M:%S",
                "page_length": 25,
                "include_search": True,
                "table_filter": True,
                "align_pn": False,
                "color_pn": True,
                "show_cell_bars": True,
                "conditional_formatting": []
            }),
            "cache_timeout": None,
            "description": "Detailed view of data with key dimensions and metrics"
        }
    
    def _generate_layout(self, charts: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Generate dashboard layout positions."""
        positions = {}
        
        # Layout configuration
        DASHBOARD_WIDTH = 48  # Preset uses 48 column grid
        ROW_HEIGHT = 50
        
        # Row 1: KPI cards (4 cards across)
        kpi_width = DASHBOARD_WIDTH // 4
        for i in range(min(4, len(charts))):
            if charts[i]['viz_type'] == 'big_number_total':
                positions[f"CHART-{i}"] = {
                    "type": "CHART",
                    "id": f"CHART-{i}",
                    "children": [],
                    "meta": {
                        "width": kpi_width,
                        "height": ROW_HEIGHT,
                        "chartId": i,
                        "sliceName": charts[i]['slice_name']
                    }
                }
        
        # Row 2-3: Time series charts (2 rows, full width each)
        current_row = 1
        for i, chart in enumerate(charts):
            if chart['viz_type'] == 'line':
                positions[f"CHART-{i}"] = {
                    "type": "CHART",
                    "id": f"CHART-{i}",
                    "children": [],
                    "meta": {
                        "width": DASHBOARD_WIDTH,
                        "height": ROW_HEIGHT * 2,
                        "chartId": i,
                        "sliceName": chart['slice_name']
                    }
                }
                current_row += 2
        
        # Row 4-5: Bar charts (2 columns)
        bar_charts = [c for c in charts if c['viz_type'] == 'bar']
        for i, chart in enumerate(bar_charts):
            positions[f"CHART-{charts.index(chart)}"] = {
                "type": "CHART",
                "id": f"CHART-{charts.index(chart)}",
                "children": [],
                "meta": {
                    "width": DASHBOARD_WIDTH // 2,
                    "height": ROW_HEIGHT * 2,
                    "chartId": charts.index(chart),
                    "sliceName": chart['slice_name']
                }
            }
        
        # Last row: Table (full width)
        table_charts = [c for c in charts if c['viz_type'] == 'table']
        if table_charts:
            positions[f"CHART-{charts.index(table_charts[0])}"] = {
                "type": "CHART",
                "id": f"CHART-{charts.index(table_charts[0])}",
                "children": [],
                "meta": {
                    "width": DASHBOARD_WIDTH,
                    "height": ROW_HEIGHT * 3,
                    "chartId": charts.index(table_charts[0]),
                    "sliceName": table_charts[0]['slice_name']
                }
            }
        
        return positions
    
    def _find_time_dimension(self, table: VirtualTable) -> Optional[Any]:
        """Find the primary time dimension."""
        for col in table.columns:
            if col.semantic_type == 'dimension' and col.data_type in ['timestamp', 'date']:
                return col
        return None
    
    def _get_metric_sql(self, metric: Dict[str, Any], table: VirtualTable) -> str:
        """Generate SQL expression for a metric."""
        metric_type = metric.get('type', 'simple')
        
        if metric_type == 'simple':
            # Find the measure
            measure_name = metric.get('measure')
            if measure_name:
                for measure in table.semantic_model.get('measures', []):
                    if measure['name'] == measure_name:
                        agg = measure.get('agg', 'sum').upper()
                        expr = measure.get('expr', measure_name)
                        return f"{agg}({expr})"
            return f"SUM({measure_name})"
        
        elif metric_type == 'ratio':
            num = metric.get('numerator', '1')
            den = metric.get('denominator', '1')
            return f"SUM({num}) / NULLIF(SUM({den}), 0)"
        
        elif metric_type == 'derived':
            return metric.get('expr', 'NULL')
        
        else:
            # Default to count
            return "COUNT(*)"
    
    def export_dashboard_json(self, dashboard_config: Dict[str, Any]) -> str:
        """Export dashboard configuration as JSON for Preset import."""
        export_format = {
            "version": "1.0.0",
            "type": "dashboard",
            "timestamp": datetime.utcnow().isoformat(),
            "dashboard": dashboard_config
        }
        
        return json.dumps(export_format, indent=2)




