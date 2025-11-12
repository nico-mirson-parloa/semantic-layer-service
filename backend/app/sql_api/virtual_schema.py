"""
Virtual schema management for SQL API.

This module manages the mapping between semantic models and virtual SQL schemas/tables,
allowing SQL clients to query semantic models as if they were regular database tables.
"""

import os
import yaml
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
from datetime import datetime

import structlog

logger = structlog.get_logger()


@dataclass
class VirtualColumn:
    """Represents a virtual column in a SQL table."""
    name: str
    data_type: str
    is_nullable: bool = True
    is_primary_key: bool = False
    comment: Optional[str] = None
    semantic_type: Optional[str] = None  # entity, dimension, measure, metric
    
    def to_sql_column_def(self) -> str:
        """Convert to SQL column definition."""
        sql = f"{self.name} {self.data_type}"
        if not self.is_nullable:
            sql += " NOT NULL"
        if self.is_primary_key:
            sql += " PRIMARY KEY"
        if self.comment:
            sql += f" -- {self.comment}"
        return sql


@dataclass
class VirtualTable:
    """Represents a virtual table backed by a semantic model."""
    schema_name: str
    table_name: str
    columns: List[VirtualColumn]
    semantic_model: Dict[str, Any]
    description: Optional[str] = None
    
    def get_column(self, name: str) -> Optional[VirtualColumn]:
        """Get column by name."""
        for col in self.columns:
            if col.name.lower() == name.lower():
                return col
        return None
    
    def to_create_table_sql(self) -> str:
        """Generate CREATE TABLE statement."""
        columns_sql = ",\n  ".join(col.to_sql_column_def() for col in self.columns)
        sql = f"CREATE TABLE {self.schema_name}.{self.table_name} (\n  {columns_sql}\n)"
        if self.description:
            sql += f";\nCOMMENT ON TABLE {self.schema_name}.{self.table_name} IS '{self.description}';"
        return sql


class VirtualSchemaManager:
    """Manages virtual schemas and tables for semantic models."""
    
    # SQL type mappings from semantic types
    TYPE_MAPPINGS = {
        # Time types
        'time': 'timestamp',
        'date': 'date',
        'datetime': 'timestamp',
        'timestamp': 'timestamp',
        
        # Numeric types
        'number': 'numeric',
        'integer': 'integer',
        'int': 'integer',
        'bigint': 'bigint',
        'decimal': 'decimal',
        'float': 'double precision',
        'double': 'double precision',
        'money': 'decimal(19,4)',
        'percent': 'decimal(5,2)',
        
        # String types
        'string': 'text',
        'text': 'text',
        'varchar': 'varchar',
        'categorical': 'varchar(255)',
        
        # Boolean
        'boolean': 'boolean',
        'bool': 'boolean',
        
        # Other
        'json': 'jsonb',
        'array': 'text[]',
        'uuid': 'uuid'
    }
    
    def __init__(self, models_path: str = "semantic-models"):
        """Initialize schema manager."""
        self.models_path = Path(models_path)
        self.schemas: Dict[str, Dict[str, VirtualTable]] = {}
        self.tables: Dict[str, VirtualTable] = {}
        
        # Load all semantic models
        self.reload_models()
    
    def reload_models(self) -> None:
        """Reload all semantic models from disk."""
        self.schemas.clear()
        self.tables.clear()
        
        if not self.models_path.exists():
            logger.warning(f"Semantic models path does not exist: {self.models_path}")
            return
        
        # Load each YAML file
        for yaml_file in self.models_path.glob("*.yml"):
            try:
                self.load_model_file(yaml_file)
            except Exception as e:
                logger.error(f"Failed to load model {yaml_file}: {e}")
    
    def load_model_file(self, file_path: Path) -> None:
        """Load a single semantic model file."""
        with open(file_path, 'r') as f:
            content = yaml.safe_load(f)
        
        if not content:
            return
        
        # Handle both wrapped and unwrapped formats
        model_data = content.get('semantic_model', content)
        if not isinstance(model_data, dict):
            logger.warning(f"Invalid model format in {file_path}")
            return
        
        # Create virtual schema and tables
        model_name = model_data.get('name', file_path.stem)
        
        # Main fact table
        fact_table = self.create_fact_table(model_name, model_data)
        
        # Dimension tables (if needed)
        dimension_tables = self.create_dimension_tables(model_name, model_data)
        
        # Metric views
        metric_views = self.create_metric_views(model_name, model_data)
        
        # Store in schema
        schema_name = f"sem_{model_name}"
        self.schemas[schema_name] = {}
        
        # Add fact table
        self.schemas[schema_name][fact_table.table_name] = fact_table
        self.tables[f"{schema_name}.{fact_table.table_name}"] = fact_table
        
        # Add dimension tables
        for dim_table in dimension_tables:
            self.schemas[schema_name][dim_table.table_name] = dim_table
            self.tables[f"{schema_name}.{dim_table.table_name}"] = dim_table
        
        # Add metric views
        for metric_view in metric_views:
            self.schemas[schema_name][metric_view.table_name] = metric_view
            self.tables[f"{schema_name}.{metric_view.table_name}"] = metric_view
        
        logger.info(
            f"Loaded semantic model {model_name}",
            schema=schema_name,
            tables=len(self.schemas[schema_name])
        )
    
    def create_fact_table(self, model_name: str, model_data: Dict[str, Any]) -> VirtualTable:
        """Create the main fact table for a semantic model."""
        columns = []
        
        # Add entity columns
        for entity in model_data.get('entities', []):
            col_type = 'bigint' if entity.get('type') == 'primary' else 'integer'
            columns.append(VirtualColumn(
                name=entity['name'],
                data_type=col_type,
                is_nullable=False,
                is_primary_key=(entity.get('type') == 'primary'),
                comment=f"Entity: {entity.get('type', 'foreign')}",
                semantic_type='entity'
            ))
        
        # Add dimension columns
        for dimension in model_data.get('dimensions', []):
            sql_type = self.map_semantic_type_to_sql(dimension.get('type', 'string'))
            columns.append(VirtualColumn(
                name=dimension['name'],
                data_type=sql_type,
                is_nullable=True,
                comment=f"Dimension: {dimension.get('type', 'categorical')}",
                semantic_type='dimension'
            ))
        
        # Add measure columns
        for measure in model_data.get('measures', []):
            # Infer SQL type from aggregation
            if measure.get('agg') in ['count', 'count_distinct']:
                sql_type = 'bigint'
            elif measure.get('agg') in ['sum', 'avg', 'min', 'max']:
                sql_type = 'numeric'
            else:
                sql_type = 'numeric'
            
            columns.append(VirtualColumn(
                name=measure['name'],
                data_type=sql_type,
                is_nullable=True,
                comment=f"Measure: {measure.get('agg', 'sum')} of {measure.get('expr', measure['name'])}",
                semantic_type='measure'
            ))
        
        return VirtualTable(
            schema_name=f"sem_{model_name}",
            table_name="fact",
            columns=columns,
            semantic_model=model_data,
            description=model_data.get('description', f"Fact table for {model_name}")
        )
    
    def create_dimension_tables(self, model_name: str, model_data: Dict[str, Any]) -> List[VirtualTable]:
        """Create dimension tables if needed."""
        # For now, we'll keep dimensions in the fact table
        # In future, we could create separate dimension tables for categorical dimensions
        return []
    
    def create_metric_views(self, model_name: str, model_data: Dict[str, Any]) -> List[VirtualTable]:
        """Create views for each metric."""
        views = []
        
        for metric in model_data.get('metrics', []):
            # Create a simple view with the metric and common dimensions
            columns = []
            
            # Add time dimension if exists
            time_dims = [d for d in model_data.get('dimensions', []) 
                        if d.get('type') == 'time']
            if time_dims:
                columns.append(VirtualColumn(
                    name=time_dims[0]['name'],
                    data_type='timestamp',
                    is_nullable=False,
                    semantic_type='dimension'
                ))
            
            # Add categorical dimensions (limit to most common ones)
            cat_dims = [d for d in model_data.get('dimensions', []) 
                       if d.get('type') == 'categorical'][:3]
            for dim in cat_dims:
                columns.append(VirtualColumn(
                    name=dim['name'],
                    data_type='varchar(255)',
                    is_nullable=True,
                    semantic_type='dimension'
                ))
            
            # Add the metric column
            columns.append(VirtualColumn(
                name=metric['name'],
                data_type='numeric',
                is_nullable=True,
                comment=metric.get('description', ''),
                semantic_type='metric'
            ))
            
            views.append(VirtualTable(
                schema_name=f"sem_{model_name}",
                table_name=f"v_{metric['name']}",
                columns=columns,
                semantic_model=model_data,
                description=f"View for metric: {metric['name']}"
            ))
        
        return views
    
    def map_semantic_type_to_sql(self, semantic_type: str) -> str:
        """Map semantic type to SQL type."""
        return self.TYPE_MAPPINGS.get(semantic_type.lower(), 'text')
    
    def get_all_schemas(self) -> List[str]:
        """Get all virtual schema names."""
        return list(self.schemas.keys())
    
    def get_all_models(self) -> List[str]:
        """Get all semantic model names."""
        models = []
        for schema_name in self.schemas:
            if schema_name.startswith('sem_'):
                models.append(schema_name[4:])  # Remove 'sem_' prefix
        return models
    
    def get_schema_tables(self, schema_name: str) -> List[Dict[str, Any]]:
        """Get all tables in a schema."""
        tables = []
        
        if schema_name in self.schemas:
            for table_name, table in self.schemas[schema_name].items():
                tables.append({
                    'name': table_name,
                    'type': 'VIEW' if table_name.startswith('v_') else 'TABLE',
                    'columns': len(table.columns),
                    'description': table.description
                })
        
        return tables
    
    def get_tables(self, database: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get all tables, optionally filtered by database/schema."""
        tables = []
        
        if database and database in self.schemas:
            # Single schema
            return self.get_schema_tables(database)
        else:
            # All schemas
            for schema_name in self.schemas:
                for table_name, table in self.schemas[schema_name].items():
                    tables.append({
                        'schema': schema_name,
                        'name': table_name,
                        'type': 'VIEW' if table_name.startswith('v_') else 'TABLE',
                        'columns': len(table.columns)
                    })
        
        return tables
    
    def get_table(self, table_ref: str) -> Optional[VirtualTable]:
        """Get a table by reference (schema.table or just table)."""
        # Check full reference
        if table_ref in self.tables:
            return self.tables[table_ref]
        
        # Check without schema (search all schemas)
        for full_ref, table in self.tables.items():
            if full_ref.endswith(f".{table_ref}"):
                return table
        
        return None
    
    def get_table_columns(self, table_ref: str) -> List[Dict[str, Any]]:
        """Get columns for a table."""
        table = self.get_table(table_ref)
        if not table:
            return []
        
        columns = []
        for idx, col in enumerate(table.columns):
            columns.append({
                'ordinal_position': idx + 1,
                'column_name': col.name,
                'data_type': col.data_type,
                'is_nullable': 'YES' if col.is_nullable else 'NO',
                'column_default': None,
                'character_maximum_length': None,
                'numeric_precision': None,
                'numeric_scale': None,
                'is_primary_key': col.is_primary_key,
                'comment': col.comment,
                'semantic_type': col.semantic_type
            })
        
        return columns
    
    def get_information_schema_tables(self) -> List[Dict[str, Any]]:
        """Get tables for information_schema.tables view."""
        rows = []
        
        for schema_name in self.schemas:
            for table_name, table in self.schemas[schema_name].items():
                rows.append({
                    'table_catalog': 'semantic_layer',
                    'table_schema': schema_name,
                    'table_name': table_name,
                    'table_type': 'VIEW' if table_name.startswith('v_') else 'BASE TABLE',
                    'self_referencing_column_name': None,
                    'reference_generation': None,
                    'user_defined_type_catalog': None,
                    'user_defined_type_schema': None,
                    'user_defined_type_name': None,
                    'is_insertable_into': 'NO',
                    'is_typed': 'NO',
                    'commit_action': None
                })
        
        return rows
    
    def get_information_schema_columns(self) -> List[Dict[str, Any]]:
        """Get columns for information_schema.columns view."""
        rows = []
        
        for schema_name in self.schemas:
            for table_name, table in self.schemas[schema_name].items():
                for idx, col in enumerate(table.columns):
                    rows.append({
                        'table_catalog': 'semantic_layer',
                        'table_schema': schema_name,
                        'table_name': table_name,
                        'column_name': col.name,
                        'ordinal_position': idx + 1,
                        'column_default': None,
                        'is_nullable': 'YES' if col.is_nullable else 'NO',
                        'data_type': col.data_type,
                        'character_maximum_length': None,
                        'character_octet_length': None,
                        'numeric_precision': None,
                        'numeric_precision_radix': None,
                        'numeric_scale': None,
                        'datetime_precision': None,
                        'interval_type': None,
                        'interval_precision': None,
                        'character_set_catalog': None,
                        'character_set_schema': None,
                        'character_set_name': None,
                        'collation_catalog': None,
                        'collation_schema': None,
                        'collation_name': None,
                        'domain_catalog': None,
                        'domain_schema': None,
                        'domain_name': None,
                        'udt_catalog': None,
                        'udt_schema': None,
                        'udt_name': None,
                        'scope_catalog': None,
                        'scope_schema': None,
                        'scope_name': None,
                        'maximum_cardinality': None,
                        'dtd_identifier': None,
                        'is_self_referencing': 'NO',
                        'is_identity': 'NO',
                        'identity_generation': None,
                        'identity_start': None,
                        'identity_increment': None,
                        'identity_maximum': None,
                        'identity_minimum': None,
                        'identity_cycle': 'NO',
                        'is_generated': 'NEVER',
                        'generation_expression': None,
                        'is_updatable': 'NO'
                    })
        
        return rows




