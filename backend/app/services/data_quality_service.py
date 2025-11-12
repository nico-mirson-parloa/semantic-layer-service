"""
Data Quality Service for automated quality check recommendations
"""
from typing import List, Dict, Any, Optional
from datetime import datetime
import structlog
from enum import Enum

from app.integrations.databricks import DatabricksConnector
from app.core.config import settings

logger = structlog.get_logger()


class QualityCheckType(str, Enum):
    """Types of data quality checks"""
    NULLABILITY = "nullability"
    UNIQUENESS = "uniqueness"
    RANGE = "range"
    PATTERN = "pattern"
    FRESHNESS = "freshness"
    CONSISTENCY = "consistency"
    COMPLETENESS = "completeness"
    ACCURACY = "accuracy"


class QualityCheckRecommendation:
    """Data quality check recommendation"""
    def __init__(
        self,
        check_type: QualityCheckType,
        column: str,
        description: str,
        sql_template: str,
        severity: str = "medium",
        metadata: Optional[Dict[str, Any]] = None
    ):
        self.check_type = check_type
        self.column = column
        self.description = description
        self.sql_template = sql_template
        self.severity = severity
        self.metadata = metadata or {}
        self.created_at = datetime.utcnow()


class DataQualityService:
    """Service for generating data quality check recommendations"""
    
    def __init__(self):
        self.databricks = DatabricksConnector()
    
    def recommend_quality_checks(
        self, 
        catalog: str, 
        schema: str, 
        table: str
    ) -> List[Dict[str, Any]]:
        """
        Recommend data quality checks based on table schema and data patterns
        
        Args:
            catalog: Databricks catalog name
            schema: Schema name
            table: Table name
            
        Returns:
            List of quality check recommendations
        """
        try:
            # Get table schema
            columns = self.databricks.get_columns(catalog, schema, table)
            if not columns:
                return []
            
            recommendations = []
            
            # Analyze each column
            for column in columns:
                col_name = column.get('name', '')
                col_type = column.get('data_type', '').upper()
                col_comment = column.get('comment', '').lower()
                is_nullable = column.get('is_nullable', True)
                
                # Add column-specific recommendations
                col_recommendations = self._recommend_for_column(
                    catalog, schema, table, col_name, col_type, col_comment, is_nullable
                )
                recommendations.extend(col_recommendations)
            
            # Add table-level recommendations
            table_recommendations = self._recommend_table_level_checks(
                catalog, schema, table, columns
            )
            recommendations.extend(table_recommendations)
            
            # Convert to dict format
            return [self._recommendation_to_dict(r) for r in recommendations]
            
        except Exception as e:
            logger.error(f"Failed to recommend quality checks: {e}")
            return []
    
    def _recommend_for_column(
        self,
        catalog: str,
        schema: str,
        table: str,
        col_name: str,
        col_type: str,
        col_comment: str,
        is_nullable: bool
    ) -> List[QualityCheckRecommendation]:
        """Generate recommendations for a specific column"""
        recommendations = []
        table_ref = f"`{catalog}`.`{schema}`.`{table}`"
        
        # Nullability check for important fields
        if not is_nullable or any(key in col_name.lower() for key in ['id', 'key', 'code']):
            recommendations.append(QualityCheckRecommendation(
                check_type=QualityCheckType.NULLABILITY,
                column=col_name,
                description=f"Check for null values in {col_name}",
                sql_template=f"""
                    SELECT COUNT(*) as null_count,
                           COUNT(*) * 100.0 / NULLIF(COUNT(1), 0) as null_percentage
                    FROM {table_ref}
                    WHERE `{col_name}` IS NULL
                """,
                severity="high" if not is_nullable else "medium"
            ))
        
        # Uniqueness check for ID fields
        if any(identifier in col_name.lower() for identifier in ['id', 'key', 'code', 'number']):
            recommendations.append(QualityCheckRecommendation(
                check_type=QualityCheckType.UNIQUENESS,
                column=col_name,
                description=f"Check uniqueness of {col_name}",
                sql_template=f"""
                    SELECT `{col_name}`, COUNT(*) as duplicate_count
                    FROM {table_ref}
                    GROUP BY `{col_name}`
                    HAVING COUNT(*) > 1
                    ORDER BY duplicate_count DESC
                    LIMIT 100
                """,
                severity="high"
            ))
        
        # Range checks for numeric fields
        if any(t in col_type for t in ['INT', 'FLOAT', 'DOUBLE', 'DECIMAL', 'NUMERIC']):
            recommendations.append(QualityCheckRecommendation(
                check_type=QualityCheckType.RANGE,
                column=col_name,
                description=f"Check value range for {col_name}",
                sql_template=f"""
                    SELECT 
                        MIN(`{col_name}`) as min_value,
                        MAX(`{col_name}`) as max_value,
                        AVG(`{col_name}`) as avg_value,
                        STDDEV(`{col_name}`) as stddev_value,
                        PERCENTILE_CONT(0.25) WITHIN GROUP (ORDER BY `{col_name}`) as q1,
                        PERCENTILE_CONT(0.50) WITHIN GROUP (ORDER BY `{col_name}`) as median,
                        PERCENTILE_CONT(0.75) WITHIN GROUP (ORDER BY `{col_name}`) as q3
                    FROM {table_ref}
                    WHERE `{col_name}` IS NOT NULL
                """,
                severity="medium",
                metadata={"check_subtype": "statistical_distribution"}
            ))
            
            # Special checks for duration/amount fields
            if any(term in col_name.lower() for term in ['duration', 'amount', 'count', 'seconds']):
                recommendations.append(QualityCheckRecommendation(
                    check_type=QualityCheckType.RANGE,
                    column=col_name,
                    description=f"Check for negative values in {col_name}",
                    sql_template=f"""
                        SELECT COUNT(*) as negative_count,
                               COUNT(*) * 100.0 / NULLIF(COUNT(1), 0) as negative_percentage
                        FROM {table_ref}
                        WHERE `{col_name}` < 0
                    """,
                    severity="high",
                    metadata={"check_subtype": "negative_values"}
                ))
        
        # Pattern checks for string fields
        if 'STRING' in col_type or 'VARCHAR' in col_type or 'CHAR' in col_type:
            # Email pattern check
            if 'email' in col_name.lower():
                recommendations.append(QualityCheckRecommendation(
                    check_type=QualityCheckType.PATTERN,
                    column=col_name,
                    description=f"Validate email format in {col_name}",
                    sql_template=f"""
                        SELECT COUNT(*) as invalid_email_count
                        FROM {table_ref}
                        WHERE `{col_name}` IS NOT NULL 
                        AND `{col_name}` NOT RLIKE '^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{{2,}}$'
                    """,
                    severity="medium",
                    metadata={"pattern_type": "email"}
                ))
            
            # Phone pattern check
            elif 'phone' in col_name.lower() or 'mobile' in col_name.lower():
                recommendations.append(QualityCheckRecommendation(
                    check_type=QualityCheckType.PATTERN,
                    column=col_name,
                    description=f"Validate phone number format in {col_name}",
                    sql_template=f"""
                        SELECT COUNT(*) as invalid_phone_count
                        FROM {table_ref}
                        WHERE `{col_name}` IS NOT NULL 
                        AND LENGTH(REGEXP_REPLACE(`{col_name}`, '[^0-9]', '')) NOT BETWEEN 10 AND 15
                    """,
                    severity="medium",
                    metadata={"pattern_type": "phone"}
                ))
        
        # Freshness checks for timestamp fields
        if 'TIMESTAMP' in col_type or 'DATE' in col_type:
            recommendations.append(QualityCheckRecommendation(
                check_type=QualityCheckType.FRESHNESS,
                column=col_name,
                description=f"Check data freshness for {col_name}",
                sql_template=f"""
                    SELECT 
                        MAX(`{col_name}`) as latest_timestamp,
                        DATEDIFF(hour, MAX(`{col_name}`), CURRENT_TIMESTAMP()) as hours_since_latest,
                        COUNT(CASE WHEN `{col_name}` > DATEADD(day, -7, CURRENT_DATE()) THEN 1 END) as records_last_7_days,
                        COUNT(CASE WHEN `{col_name}` > DATEADD(day, -30, CURRENT_DATE()) THEN 1 END) as records_last_30_days
                    FROM {table_ref}
                """,
                severity="medium",
                metadata={"temporal_column": True}
            ))
        
        return recommendations
    
    def _recommend_table_level_checks(
        self,
        catalog: str,
        schema: str,
        table: str,
        columns: List[Dict[str, Any]]
    ) -> List[QualityCheckRecommendation]:
        """Generate table-level quality check recommendations"""
        recommendations = []
        table_ref = f"`{catalog}`.`{schema}`.`{table}`"
        
        # Table completeness check
        recommendations.append(QualityCheckRecommendation(
            check_type=QualityCheckType.COMPLETENESS,
            column="*",
            description="Check overall table completeness",
            sql_template=f"""
                SELECT 
                    COUNT(*) as total_rows,
                    {', '.join([f"SUM(CASE WHEN `{col['name']}` IS NULL THEN 1 ELSE 0 END) as null_{col['name']}" 
                               for col in columns[:5]]) if columns else 'NULL as no_columns'}
                FROM {table_ref}
            """,
            severity="high",
            metadata={"check_level": "table"}
        ))
        
        # Row count consistency check
        recommendations.append(QualityCheckRecommendation(
            check_type=QualityCheckType.CONSISTENCY,
            column="*",
            description="Monitor row count trends",
            sql_template=f"""
                WITH daily_counts AS (
                    SELECT 
                        DATE(created_timestamp) as date,
                        COUNT(*) as row_count
                    FROM {table_ref}
                    WHERE created_timestamp > DATEADD(day, -30, CURRENT_DATE())
                    GROUP BY DATE(created_timestamp)
                )
                SELECT 
                    date,
                    row_count,
                    LAG(row_count) OVER (ORDER BY date) as prev_day_count,
                    (row_count - LAG(row_count) OVER (ORDER BY date)) * 100.0 / 
                        NULLIF(LAG(row_count) OVER (ORDER BY date), 0) as pct_change
                FROM daily_counts
                ORDER BY date DESC
            """,
            severity="medium",
            metadata={"check_level": "table", "requires_timestamp": True}
        ))
        
        # If we have ID fields, check for relationships
        id_columns = [col for col in columns if 'id' in col['name'].lower()]
        if len(id_columns) >= 2:
            recommendations.append(QualityCheckRecommendation(
                check_type=QualityCheckType.CONSISTENCY,
                column=",".join([col['name'] for col in id_columns[:2]]),
                description="Check referential integrity between ID fields",
                sql_template=f"""
                    SELECT 
                        COUNT(DISTINCT `{id_columns[0]['name']}`) as distinct_{id_columns[0]['name']},
                        COUNT(DISTINCT `{id_columns[1]['name']}`) as distinct_{id_columns[1]['name']},
                        COUNT(*) as total_rows,
                        COUNT(*) * 1.0 / NULLIF(COUNT(DISTINCT `{id_columns[0]['name']}`), 0) as avg_per_{id_columns[0]['name']}
                    FROM {table_ref}
                """,
                severity="medium",
                metadata={"check_level": "relationship"}
            ))
        
        return recommendations
    
    def _recommendation_to_dict(self, rec: QualityCheckRecommendation) -> Dict[str, Any]:
        """Convert recommendation object to dictionary"""
        return {
            "check_type": rec.check_type.value,
            "column": rec.column,
            "description": rec.description,
            "sql_template": rec.sql_template.strip(),
            "severity": rec.severity,
            "metadata": rec.metadata,
            "created_at": rec.created_at.isoformat()
        }
    
    def execute_quality_check(self, sql: str) -> Dict[str, Any]:
        """Execute a quality check SQL and return results"""
        try:
            # Execute the quality check query
            results = self.databricks.execute_query(sql)
            
            return {
                "success": True,
                "results": results,
                "executed_at": datetime.utcnow().isoformat()
            }
        except Exception as e:
            logger.error(f"Failed to execute quality check: {e}")
            return {
                "success": False,
                "error": str(e)
            }

