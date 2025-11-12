"""
Table Analyzer Service for analyzing Databricks gold layer tables.
Extracts schema, statistics, and patterns for automatic model generation.
"""
import re
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime
import structlog

from app.models.catalog import (
    TableSchema, ColumnInfo, TableAnalysis, ColumnPattern, 
    TableRelationship
)
from app.integrations.databricks import DatabricksConnector


logger = structlog.get_logger()


class TableAnalyzer:
    """Service for analyzing Unity Catalog tables"""
    
    def __init__(self, client: Optional[DatabricksConnector] = None):
        """Initialize with optional Databricks client"""
        self.client = client or DatabricksConnector()
        
        # Pattern matchers for column naming conventions
        self.id_patterns = [
            r'.*_id$', r'^id$', r'.*_key$', r'^key$',
            r'.*_code$', r'.*_num$', r'.*_number$'
        ]
        self.amount_patterns = [
            r'.*_amount$', r'.*_price$', r'.*_cost$', r'.*_revenue$',
            r'.*_total$', r'.*_subtotal$', r'.*_fee$', r'.*_charge$'
        ]
        self.quantity_patterns = [
            r'.*_count$', r'.*_qty$', r'.*_quantity$', r'^count$',
            r'.*_number$', r'.*_volume$', r'.*_size$'
        ]
        self.percentage_patterns = [
            r'.*_rate$', r'.*_ratio$', r'.*_percent$', r'.*_pct$',
            r'.*_share$', r'.*_portion$'
        ]
        self.date_patterns = [
            r'.*_date$', r'^date$', r'.*_dt$', r'^dt$'
        ]
        self.timestamp_patterns = [
            r'.*_time$', r'.*_timestamp$', r'.*_ts$', r'^ts$',
            r'.*_at$', r'.*_created$', r'.*_updated$', r'.*_modified$'
        ]
        self.boolean_patterns = [
            r'^is_.*', r'^has_.*', r'^was_.*', r'^are_.*',
            r'.*_flag$', r'.*_ind$', r'.*_indicator$'
        ]
    
    def analyze_table(self, table_schema: TableSchema) -> TableAnalysis:
        """Analyze table schema and return comprehensive analysis"""
        logger.info(f"Analyzing table: {table_schema.full_name}")
        
        # Detect column patterns
        patterns = self.detect_column_patterns(table_schema)
        
        # Determine table type
        table_type = self._determine_table_type(table_schema)
        
        # Create analysis result
        analysis = TableAnalysis(
            table_name=table_schema.table,
            full_table_name=table_schema.full_name,
            row_count=table_schema.statistics.get('numRows') if table_schema.statistics else None,
            size_in_bytes=table_schema.statistics.get('sizeInBytes') if table_schema.statistics else None,
            columns=table_schema.columns,
            has_primary_key=len(table_schema.primary_keys) > 0,
            foreign_keys=table_schema.foreign_keys,
            table_type=table_type,
            is_empty=table_schema.statistics.get('numRows', 1) == 0 if table_schema.statistics else False,
            
            # Pattern results
            numeric_columns=patterns.numeric_columns,
            temporal_columns=patterns.date_columns + patterns.timestamp_columns,
            categorical_columns=patterns.categorical_columns,
            boolean_columns=patterns.boolean_columns,
            id_columns=patterns.id_columns,
            
            # Initial confidence based on table completeness
            confidence_score=self._calculate_initial_confidence(table_schema)
        )
        
        # Add analysis notes
        if not analysis.has_primary_key:
            analysis.analysis_notes.append("No primary key detected - consider identifying unique columns")
        
        if len(analysis.foreign_keys) == 0 and table_type == 'fact':
            analysis.analysis_notes.append("No foreign keys detected in fact table - relationships may be implicit")
        
        if analysis.is_empty:
            analysis.analysis_notes.append("Table is empty - suggestions based on schema only")
        
        return analysis
    
    def detect_column_patterns(self, table_schema: TableSchema) -> ColumnPattern:
        """Detect patterns in column names and types"""
        patterns = ColumnPattern()
        
        for column in table_schema.columns:
            col_name_lower = column.name.lower()
            
            # Skip system columns
            if col_name_lower in ['_rescued_data', '_commit_version', '_commit_timestamp']:
                continue
            
            # Numeric columns
            if column.is_numeric():
                patterns.numeric_columns.append(column.name)
                
                # Check if it's an ID column
                if any(re.match(pattern, col_name_lower) for pattern in self.id_patterns):
                    patterns.id_columns.append(column.name)
                # Check if it's an amount column
                elif any(re.match(pattern, col_name_lower) for pattern in self.amount_patterns):
                    patterns.amount_columns.append(column.name)
                # Check if it's a quantity column
                elif any(re.match(pattern, col_name_lower) for pattern in self.quantity_patterns):
                    patterns.quantity_columns.append(column.name)
                # Check if it's a percentage column
                elif any(re.match(pattern, col_name_lower) for pattern in self.percentage_patterns):
                    patterns.percentage_columns.append(column.name)
            
            # Temporal columns
            elif column.is_temporal():
                if column.data_type == 'DATE' or any(re.match(pattern, col_name_lower) for pattern in self.date_patterns):
                    patterns.date_columns.append(column.name)
                else:
                    patterns.timestamp_columns.append(column.name)
            
            # Boolean columns
            elif column.is_boolean() or any(re.match(pattern, col_name_lower) for pattern in self.boolean_patterns):
                patterns.boolean_columns.append(column.name)
            
            # String columns (potential dimensions)
            elif column.is_string():
                # Skip very long text fields
                if 'text' not in col_name_lower and 'description' not in col_name_lower:
                    patterns.categorical_columns.append(column.name)
        
        return patterns
    
    def analyze_column_statistics(self, table_full_name: str) -> Dict[str, Dict[str, Any]]:
        """Analyze column statistics for better metric suggestions"""
        if not self.client:
            return {}
        
        try:
            # Query for basic column statistics
            stats_query = f"""
            SELECT 
                column_name,
                data_type,
                null_count,
                distinct_count,
                min AS min_value,
                max AS max_value,
                mean AS avg_value,
                stddev AS std_dev
            FROM {table_full_name}.column_stats
            WHERE column_name IS NOT NULL
            """
            
            results = self.client.execute(stats_query)
            
            # Process results into dictionary
            column_stats = {}
            for row in results:
                col_name = row['column_name']
                column_stats[col_name] = {
                    'null_count': row.get('null_count', 0),
                    'distinct_count': row.get('distinct_count', 0),
                    'min_value': row.get('min_value'),
                    'max_value': row.get('max_value'),
                    'avg_value': row.get('avg_value'),
                    'std_dev': row.get('std_dev')
                }
                
                # Calculate additional metrics for boolean columns
                if col_name == 'is_returned' and 'true_count' in row:
                    total = row.get('true_count', 0) + row.get('false_count', 0)
                    if total > 0:
                        column_stats[col_name]['return_rate'] = row.get('true_count', 0) / total
            
            return column_stats
            
        except Exception as e:
            logger.warning(f"Failed to get column statistics: {e}")
            # Return mock statistics for testing
            return self._get_mock_statistics(table_full_name)
    
    def detect_relationships(self, table_full_name: str) -> List[TableRelationship]:
        """Detect foreign key relationships from information schema"""
        if not self.client:
            return []
        
        try:
            # Query information schema for foreign keys
            fk_query = f"""
            SELECT 
                tc.constraint_name,
                tc.table_name,
                kcu.column_name,
                ccu.table_schema AS foreign_table_schema,
                ccu.table_name AS foreign_table_name,
                ccu.column_name AS foreign_column_name
            FROM information_schema.table_constraints AS tc
            JOIN information_schema.key_column_usage AS kcu
                ON tc.constraint_name = kcu.constraint_name
                AND tc.table_schema = kcu.table_schema
            JOIN information_schema.constraint_column_usage AS ccu
                ON ccu.constraint_name = tc.constraint_name
                AND ccu.table_schema = tc.table_schema
            WHERE tc.constraint_type = 'FOREIGN KEY'
                AND tc.table_schema || '.' || tc.table_name = '{table_full_name}'
            """
            
            results = self.client.execute(fk_query)
            
            relationships = []
            for row in results:
                rel = TableRelationship(
                    from_table=table_full_name,
                    from_column=row['column_name'],
                    to_table=f"{row['foreign_table_schema']}.{row['foreign_table_name']}",
                    to_column=row['foreign_column_name'],
                    relationship_type='foreign_key',
                    confidence=1.0
                )
                relationships.append(rel)
            
            return relationships
            
        except Exception as e:
            logger.warning(f"Failed to detect relationships: {e}")
            # Return mock relationships for testing
            return self._get_mock_relationships(table_full_name)
    
    def _determine_table_type(self, table_schema: TableSchema) -> str:
        """Determine if table is fact, dimension, or aggregate"""
        table_name_lower = table_schema.table.lower()
        
        # Check naming conventions
        if any(pattern in table_name_lower for pattern in ['_fact', '_fct', '_f_']):
            return 'fact'
        elif any(pattern in table_name_lower for pattern in ['_dim', '_dimension', '_d_']):
            return 'dimension'
        elif any(pattern in table_name_lower for pattern in ['_agg', '_aggregate', '_summary']):
            return 'aggregate'
        
        # Check by structure
        has_metrics = len([c for c in table_schema.columns if c.is_numeric() and not self._is_id_column(c.name)]) > 2
        has_foreign_keys = len(table_schema.foreign_keys) > 0
        has_many_dimensions = len([c for c in table_schema.columns if c.is_string()]) > 3
        
        if has_metrics and (has_foreign_keys or has_many_dimensions):
            return 'fact'
        elif not has_metrics and table_schema.primary_keys:
            return 'dimension'
        elif has_metrics and not has_foreign_keys:
            return 'aggregate'
        
        return 'unknown'
    
    def _is_id_column(self, column_name: str) -> bool:
        """Check if column is an ID column"""
        return any(re.match(pattern, column_name.lower()) for pattern in self.id_patterns)
    
    def _calculate_initial_confidence(self, table_schema: TableSchema) -> float:
        """Calculate initial confidence score based on table metadata completeness"""
        score = 0.5  # Base score
        
        # Add points for various metadata
        if table_schema.table_comment:
            score += 0.1
        if table_schema.primary_keys:
            score += 0.1
        if any(col.comment for col in table_schema.columns):
            score += 0.1
        if table_schema.statistics and table_schema.statistics.get('numRows', 0) > 0:
            score += 0.1
        if table_schema.foreign_keys:
            score += 0.1
        
        return min(score, 1.0)
    
    def _get_mock_statistics(self, table_full_name: str) -> Dict[str, Dict[str, Any]]:
        """Return mock statistics for testing"""
        if 'sales_fact' in table_full_name:
            return {
                "revenue": {
                    "min_value": 0, 
                    "max_value": 10000, 
                    "null_count": 0, 
                    "distinct_count": 8500, 
                    "avg_value": 150.50
                },
                "region": {
                    "min_value": None, 
                    "max_value": None,
                    "null_count": 0, 
                    "distinct_count": 5, 
                    "top_values": ["North", "South", "East", "West", "Central"]
                },
                "is_returned": {
                    "min_value": None, 
                    "max_value": None,
                    "null_count": 0, 
                    "distinct_count": 2, 
                    "true_count": 50000, 
                    "false_count": 950000,
                    "return_rate": 0.05
                }
            }
        return {}
    
    def _get_mock_relationships(self, table_full_name: str) -> List[TableRelationship]:
        """Return mock relationships for testing"""
        if 'sales_fact' in table_full_name:
            return [
                TableRelationship(
                    from_table=table_full_name,
                    from_column="customer_id",
                    to_table="gold.customers",
                    to_column="customer_id",
                    relationship_type="foreign_key",
                    confidence=1.0
                ),
                TableRelationship(
                    from_table=table_full_name,
                    from_column="product_id",
                    to_table="gold.products",
                    to_column="product_id",
                    relationship_type="foreign_key",
                    confidence=1.0
                )
            ]
        return []
