"""
Preset/Superset connector implementation.

This module handles the connection setup and configuration for Preset
to connect to the Semantic Layer SQL API.
"""

import json
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
import structlog

from app.core.config import settings
from app.sql_api.virtual_schema import VirtualSchemaManager

logger = structlog.get_logger()


@dataclass
class PresetDataSource:
    """Represents a Preset/Superset data source configuration."""
    database_name: str
    sqlalchemy_uri: str
    schema_access: List[str]
    extra: Dict[str, Any]
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to Preset API format."""
        return {
            "database_name": self.database_name,
            "sqlalchemy_uri": self.sqlalchemy_uri,
            "expose_in_sqllab": True,
            "allow_run_async": True,
            "allow_ctas": False,
            "allow_cvas": False,
            "allow_dml": False,
            "force_ctas_schema": None,
            "schemas_allowed_for_csv_upload": [],
            "extra": json.dumps(self.extra),
            "schemas": self.schema_access
        }


class PresetConnector:
    """Handles Preset/Superset connectivity to Semantic Layer."""
    
    def __init__(self, schema_manager: Optional[VirtualSchemaManager] = None):
        """Initialize Preset connector."""
        self.schema_manager = schema_manager or VirtualSchemaManager()
        self.sql_host = settings.get("SQL_SERVER_HOST", "localhost")
        self.sql_port = settings.get("SQL_SERVER_PORT", 5433)
        
    def generate_connection_config(
        self,
        database_name: str = "Semantic Layer",
        include_schemas: Optional[List[str]] = None
    ) -> PresetDataSource:
        """
        Generate Preset database connection configuration.
        
        Args:
            database_name: Display name in Preset
            include_schemas: List of semantic model schemas to include (None = all)
            
        Returns:
            PresetDataSource configuration
        """
        # Build SQLAlchemy URI for PostgreSQL
        sqlalchemy_uri = f"postgresql://preset_user@{self.sql_host}:{self.sql_port}/semantic_layer"
        
        # Get available schemas
        all_schemas = self.schema_manager.get_all_schemas()
        schema_access = include_schemas or all_schemas
        
        # Extra configuration for optimal Preset performance
        extra = {
            "metadata_params": {},
            "engine_params": {
                "pool_size": 50,
                "max_overflow": 100,
                "pool_pre_ping": True,
                "pool_recycle": 3600,
                "connect_args": {
                    "sslmode": "prefer",
                    "application_name": "preset_semantic_layer",
                    "options": "-c statement_timeout=300000"  # 5 min timeout
                }
            },
            "schemas_allowed_for_csv_upload": [],
            "version": "1.0",
            "allows_virtual_table_explore": True,
            "disable_data_preview": False,
            # Preset-specific optimizations
            "cost_estimate_enabled": True,
            "allows_subquery": True,
            "allows_joins": True,
            "has_implicit_cancel": True
        }
        
        return PresetDataSource(
            database_name=database_name,
            sqlalchemy_uri=sqlalchemy_uri,
            schema_access=schema_access,
            extra=extra
        )
    
    def generate_yaml_config(self) -> str:
        """Generate YAML configuration for Preset CLI."""
        config = {
            "databases": [{
                "database_name": "Semantic Layer",
                "sqlalchemy_uri": f"postgresql://preset_user@{self.sql_host}:{self.sql_port}/semantic_layer",
                "expose_in_sqllab": True,
                "extra": {
                    "allows_virtual_table_explore": True,
                    "schemas_allowed_for_csv_upload": []
                }
            }]
        }
        
        import yaml
        return yaml.dump(config, default_flow_style=False)
    
    def validate_connection(self) -> Dict[str, Any]:
        """Validate that Preset can connect to SQL API."""
        try:
            # Check if SQL server is accessible
            import socket
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            result = sock.connect_ex((self.sql_host, self.sql_port))
            sock.close()
            
            if result != 0:
                return {
                    "valid": False,
                    "error": f"SQL API not accessible on {self.sql_host}:{self.sql_port}"
                }
            
            # Check available schemas
            schemas = self.schema_manager.get_all_schemas()
            
            return {
                "valid": True,
                "host": self.sql_host,
                "port": self.sql_port,
                "available_schemas": schemas,
                "connection_string": f"postgresql://preset_user@{self.sql_host}:{self.sql_port}/semantic_layer"
            }
            
        except Exception as e:
            logger.error(f"Connection validation failed: {e}")
            return {
                "valid": False,
                "error": str(e)
            }
    
    def get_recommended_settings(self) -> Dict[str, Any]:
        """Get recommended Preset configuration settings."""
        return {
            "database_settings": {
                "async_queries": True,
                "cache_timeout": 300,  # 5 minutes
                "schema_cache_timeout": 86400,  # 24 hours
            },
            "query_settings": {
                "row_limit": 50000,
                "sql_lab_timeout": 300,  # 5 minutes
                "async_query_timeout": 600,  # 10 minutes
            },
            "performance_tips": [
                "Enable query result caching in Preset",
                "Use async query execution for large datasets",
                "Create aggregate tables for commonly used metrics",
                "Set up scheduled cache warming for dashboards"
            ]
        }
    
    def generate_explore_config(self, schema_name: str, table_name: str) -> Dict[str, Any]:
        """
        Generate Preset dataset (explore) configuration.
        
        Args:
            schema_name: Semantic model schema
            table_name: Table name (usually 'fact' or metric view)
            
        Returns:
            Dataset configuration for Preset
        """
        table = self.schema_manager.get_table(f"{schema_name}.{table_name}")
        if not table:
            raise ValueError(f"Table {schema_name}.{table_name} not found")
        
        # Generate column metadata for Preset
        columns = []
        metrics = []
        
        for col in table.columns:
            column_config = {
                "column_name": col.name,
                "verbose_name": col.name.replace('_', ' ').title(),
                "description": col.comment or "",
                "type": self._map_sql_type_to_preset(col.data_type),
                "groupby": col.semantic_type in ['dimension', 'entity'],
                "filterable": True,
                "is_dttm": col.data_type in ['timestamp', 'date', 'datetime']
            }
            columns.append(column_config)
            
            # Auto-generate metrics for measures
            if col.semantic_type == 'measure':
                metrics.append({
                    "metric_name": f"sum_{col.name}",
                    "verbose_name": f"Sum of {col.name.replace('_', ' ').title()}",
                    "metric_type": "sum",
                    "expression": f"SUM({col.name})"
                })
                metrics.append({
                    "metric_name": f"avg_{col.name}",
                    "verbose_name": f"Average {col.name.replace('_', ' ').title()}",
                    "metric_type": "avg",
                    "expression": f"AVG({col.name})"
                })
        
        # Always add count metric
        metrics.append({
            "metric_name": "count",
            "verbose_name": "Row Count",
            "metric_type": "count",
            "expression": "COUNT(*)"
        })
        
        return {
            "table_name": table_name,
            "schema": schema_name,
            "description": table.description or f"Semantic model: {schema_name}",
            "columns": columns,
            "metrics": metrics,
            "main_dttm_col": self._find_time_column(table),
            "default_endpoint": None,
            "filter_select_enabled": True,
            "fetch_values_predicate": None,
            "params": json.dumps({
                "semantic_model": table.semantic_model.get('name'),
                "model_version": "1.0"
            })
        }
    
    def _map_sql_type_to_preset(self, sql_type: str) -> str:
        """Map SQL types to Preset generic types."""
        type_mapping = {
            'integer': 'BIGINT',
            'bigint': 'BIGINT',
            'smallint': 'BIGINT',
            'numeric': 'DOUBLE',
            'decimal': 'DOUBLE',
            'real': 'FLOAT',
            'double precision': 'DOUBLE',
            'text': 'VARCHAR',
            'varchar': 'VARCHAR',
            'character varying': 'VARCHAR',
            'boolean': 'BOOLEAN',
            'date': 'DATE',
            'timestamp': 'TIMESTAMP',
            'timestamptz': 'TIMESTAMP',
            'time': 'TIME',
            'json': 'JSON',
            'jsonb': 'JSON'
        }
        
        return type_mapping.get(sql_type.lower(), 'VARCHAR')
    
    def _find_time_column(self, table) -> Optional[str]:
        """Find the main time column for a table."""
        # Look for time dimensions
        for col in table.columns:
            if col.semantic_type == 'dimension' and col.data_type in ['timestamp', 'date']:
                # Prefer columns with 'date' in the name
                if 'date' in col.name.lower():
                    return col.name
        
        # Return first time column found
        for col in table.columns:
            if col.data_type in ['timestamp', 'date']:
                return col.name
        
        return None




