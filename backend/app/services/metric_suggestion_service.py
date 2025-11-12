"""
Metric Suggestion Service for auto-suggesting metrics based on table schema
"""
from typing import List, Dict, Any, Optional
from datetime import datetime
import structlog
import re

from app.integrations.databricks import DatabricksConnector
from app.core.config import settings

logger = structlog.get_logger()


class MetricTemplate:
    """Template for suggested metrics"""
    def __init__(
        self,
        name: str,
        display_name: str,
        description: str,
        metric_type: str,
        sql_template: str,
        required_columns: List[Dict[str, str]],
        category: str,
        complexity: str = "simple",
        business_value: str = "medium"
    ):
        self.name = name
        self.display_name = display_name
        self.description = description
        self.metric_type = metric_type
        self.sql_template = sql_template
        self.required_columns = required_columns
        self.category = category
        self.complexity = complexity
        self.business_value = business_value


class MetricSuggestionService:
    """Service for auto-suggesting metrics based on table schema"""
    
    def __init__(self):
        self.databricks = DatabricksConnector()
        self.metric_templates = self._initialize_metric_templates()
    
    def suggest_metrics(self, catalog: str, schema: str, table: str) -> List[Dict[str, Any]]:
        """
        Suggest metrics based on table schema
        
        Args:
            catalog: Databricks catalog
            schema: Schema name
            table: Table name
            
        Returns:
            List of suggested metrics with SQL
        """
        try:
            # Get table schema
            columns = self.databricks.get_columns(catalog, schema, table)
            if not columns:
                return []
            
            # Analyze schema
            schema_analysis = self._analyze_schema(columns)
            
            # Generate suggestions
            suggestions = []
            
            # 1. Basic count metrics
            suggestions.extend(self._suggest_count_metrics(catalog, schema, table, columns, schema_analysis))
            
            # 2. Aggregation metrics
            suggestions.extend(self._suggest_aggregation_metrics(catalog, schema, table, columns, schema_analysis))
            
            # 3. Time-based metrics
            suggestions.extend(self._suggest_time_based_metrics(catalog, schema, table, columns, schema_analysis))
            
            # 4. Ratio and percentage metrics
            suggestions.extend(self._suggest_ratio_metrics(catalog, schema, table, columns, schema_analysis))
            
            # 5. Business-specific metrics
            suggestions.extend(self._suggest_business_metrics(catalog, schema, table, columns, schema_analysis))
            
            # Score and rank suggestions
            scored_suggestions = self._score_suggestions(suggestions, schema_analysis)
            
            # Return top suggestions
            return sorted(scored_suggestions, key=lambda x: x['score'], reverse=True)
            
        except Exception as e:
            logger.error(f"Failed to suggest metrics: {e}")
            return []
    
    def _analyze_schema(self, columns: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze schema to understand data patterns"""
        analysis = {
            "total_columns": len(columns),
            "id_columns": [],
            "numeric_columns": [],
            "timestamp_columns": [],
            "categorical_columns": [],
            "boolean_columns": [],
            "text_columns": [],
            "potential_measures": [],
            "potential_dimensions": [],
            "table_type": None  # fact, dimension, transaction, etc.
        }
        
        for column in columns:
            col_name = column.get('name', '').lower()
            col_type = column.get('data_type', '').upper()
            
            # Categorize columns
            if any(id_term in col_name for id_term in ['_id', '_key', '_code']):
                analysis["id_columns"].append(column)
                analysis["potential_dimensions"].append(column)
            
            if any(t in col_type for t in ['INT', 'FLOAT', 'DOUBLE', 'DECIMAL', 'NUMERIC']):
                analysis["numeric_columns"].append(column)
                # Check if it's a measure
                if any(term in col_name for term in ['amount', 'count', 'total', 'sum', 'duration', 'price', 'cost', 'revenue']):
                    analysis["potential_measures"].append(column)
            
            if 'TIMESTAMP' in col_type or 'DATE' in col_type:
                analysis["timestamp_columns"].append(column)
                analysis["potential_dimensions"].append(column)
            
            if 'BOOLEAN' in col_type or 'BOOL' in col_type:
                analysis["boolean_columns"].append(column)
                analysis["potential_dimensions"].append(column)
            
            if 'STRING' in col_type or 'VARCHAR' in col_type:
                if len(col_name) < 20 and not any(term in col_name for term in ['description', 'comment', 'text', 'note']):
                    analysis["categorical_columns"].append(column)
                    analysis["potential_dimensions"].append(column)
                else:
                    analysis["text_columns"].append(column)
        
        # Determine table type
        if len(analysis["id_columns"]) >= 2 and len(analysis["numeric_columns"]) > 2:
            analysis["table_type"] = "fact"
        elif len(analysis["id_columns"]) == 1 and len(analysis["text_columns"]) > len(analysis["numeric_columns"]):
            analysis["table_type"] = "dimension"
        elif any('transaction' in col.get('name', '').lower() for col in columns):
            analysis["table_type"] = "transaction"
        else:
            analysis["table_type"] = "general"
        
        return analysis
    
    def _suggest_count_metrics(
        self, 
        catalog: str, 
        schema: str, 
        table: str, 
        columns: List[Dict[str, Any]], 
        analysis: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Suggest count-based metrics"""
        suggestions = []
        table_ref = f"`{catalog}`.`{schema}`.`{table}`"
        
        # Basic row count
        suggestions.append({
            "name": f"total_{table}_count",
            "display_name": f"Total {table.replace('_', ' ').title()} Count",
            "description": f"Total number of records in {table}",
            "category": "volume",
            "metric_type": "count",
            "sql": f"SELECT COUNT(*) as total_count FROM {table_ref}",
            "complexity": "simple",
            "business_value": "high"
        })
        
        # Distinct counts for ID columns
        for id_col in analysis["id_columns"][:3]:  # Limit to 3
            col_name = id_col['name']
            suggestions.append({
                "name": f"unique_{col_name}_count",
                "display_name": f"Unique {col_name.replace('_', ' ').title()} Count",
                "description": f"Number of unique {col_name} values",
                "category": "uniqueness",
                "metric_type": "distinct_count",
                "sql": f"SELECT COUNT(DISTINCT `{col_name}`) as unique_count FROM {table_ref}",
                "complexity": "simple",
                "business_value": "high" if 'customer' in col_name or 'user' in col_name else "medium"
            })
        
        # Active record counts (if status/active columns exist)
        status_columns = [col for col in columns if any(term in col['name'].lower() for term in ['status', 'active', 'enabled'])]
        for status_col in status_columns[:1]:
            col_name = status_col['name']
            if 'BOOL' in status_col.get('data_type', '').upper():
                suggestions.append({
                    "name": f"active_{table}_count",
                    "display_name": f"Active {table.replace('_', ' ').title()} Count",
                    "description": f"Number of active records",
                    "category": "status",
                    "metric_type": "filtered_count",
                    "sql": f"SELECT COUNT(*) as active_count FROM {table_ref} WHERE `{col_name}` = true",
                    "complexity": "simple",
                    "business_value": "high"
                })
        
        return suggestions
    
    def _suggest_aggregation_metrics(
        self,
        catalog: str,
        schema: str,
        table: str,
        columns: List[Dict[str, Any]],
        analysis: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Suggest aggregation metrics for numeric columns"""
        suggestions = []
        table_ref = f"`{catalog}`.`{schema}`.`{table}`"
        
        for measure_col in analysis["potential_measures"]:
            col_name = measure_col['name']
            col_type = measure_col.get('data_type', '').upper()
            
            # Average metric
            suggestions.append({
                "name": f"avg_{col_name}",
                "display_name": f"Average {col_name.replace('_', ' ').title()}",
                "description": f"Average value of {col_name}",
                "category": "aggregation",
                "metric_type": "average",
                "sql": f"SELECT AVG(`{col_name}`) as avg_value FROM {table_ref} WHERE `{col_name}` IS NOT NULL",
                "complexity": "simple",
                "business_value": "high" if any(term in col_name for term in ['revenue', 'amount', 'price']) else "medium"
            })
            
            # Sum metric (for appropriate columns)
            if any(term in col_name for term in ['amount', 'total', 'sum', 'revenue', 'cost', 'price']):
                suggestions.append({
                    "name": f"total_{col_name}",
                    "display_name": f"Total {col_name.replace('_', ' ').title()}",
                    "description": f"Sum of all {col_name} values",
                    "category": "aggregation",
                    "metric_type": "sum",
                    "sql": f"SELECT SUM(`{col_name}`) as total_value FROM {table_ref}",
                    "complexity": "simple",
                    "business_value": "high"
                })
            
            # Min/Max for relevant columns
            if any(term in col_name for term in ['duration', 'time', 'age', 'score']):
                suggestions.append({
                    "name": f"max_{col_name}",
                    "display_name": f"Maximum {col_name.replace('_', ' ').title()}",
                    "description": f"Maximum value of {col_name}",
                    "category": "aggregation",
                    "metric_type": "max",
                    "sql": f"SELECT MAX(`{col_name}`) as max_value FROM {table_ref}",
                    "complexity": "simple",
                    "business_value": "medium"
                })
                
                suggestions.append({
                    "name": f"min_{col_name}",
                    "display_name": f"Minimum {col_name.replace('_', ' ').title()}",
                    "description": f"Minimum value of {col_name}",
                    "category": "aggregation",
                    "metric_type": "min",
                    "sql": f"SELECT MIN(`{col_name}`) as min_value FROM {table_ref}",
                    "complexity": "simple",
                    "business_value": "medium"
                })
        
        return suggestions
    
    def _suggest_time_based_metrics(
        self,
        catalog: str,
        schema: str,
        table: str,
        columns: List[Dict[str, Any]],
        analysis: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Suggest time-based metrics"""
        suggestions = []
        table_ref = f"`{catalog}`.`{schema}`.`{table}`"
        
        if not analysis["timestamp_columns"]:
            return suggestions
        
        # Use the most relevant timestamp
        timestamp_col = None
        for ts_col in analysis["timestamp_columns"]:
            col_name = ts_col['name'].lower()
            if any(term in col_name for term in ['created', 'start', 'begin']):
                timestamp_col = ts_col
                break
        
        if not timestamp_col:
            timestamp_col = analysis["timestamp_columns"][0]
        
        ts_name = timestamp_col['name']
        
        # Daily count metric
        suggestions.append({
            "name": f"daily_{table}_count",
            "display_name": f"Daily {table.replace('_', ' ').title()} Count",
            "description": f"Number of records per day",
            "category": "time_series",
            "metric_type": "time_aggregation",
            "sql": f"""
                SELECT 
                    DATE(`{ts_name}`) as date,
                    COUNT(*) as daily_count
                FROM {table_ref}
                WHERE `{ts_name}` >= DATEADD(day, -30, CURRENT_DATE())
                GROUP BY DATE(`{ts_name}`)
                ORDER BY date DESC
            """.strip(),
            "complexity": "medium",
            "business_value": "high"
        })
        
        # Growth metrics
        suggestions.append({
            "name": f"{table}_growth_rate",
            "display_name": f"{table.replace('_', ' ').title()} Growth Rate",
            "description": "Week-over-week growth rate",
            "category": "growth",
            "metric_type": "growth_rate",
            "sql": f"""
                WITH weekly_counts AS (
                    SELECT 
                        DATE_TRUNC('week', `{ts_name}`) as week,
                        COUNT(*) as weekly_count
                    FROM {table_ref}
                    WHERE `{ts_name}` >= DATEADD(week, -8, CURRENT_DATE())
                    GROUP BY DATE_TRUNC('week', `{ts_name}`)
                )
                SELECT 
                    week,
                    weekly_count,
                    LAG(weekly_count) OVER (ORDER BY week) as prev_week_count,
                    (weekly_count - LAG(weekly_count) OVER (ORDER BY week)) * 100.0 / 
                        NULLIF(LAG(weekly_count) OVER (ORDER BY week), 0) as growth_rate
                FROM weekly_counts
                ORDER BY week DESC
            """.strip(),
            "complexity": "complex",
            "business_value": "high"
        })
        
        # Recency metrics
        suggestions.append({
            "name": f"latest_{table}_timestamp",
            "display_name": f"Latest {table.replace('_', ' ').title()} Timestamp",
            "description": "Most recent record timestamp",
            "category": "freshness",
            "metric_type": "timestamp",
            "sql": f"SELECT MAX(`{ts_name}`) as latest_timestamp FROM {table_ref}",
            "complexity": "simple",
            "business_value": "medium"
        })
        
        return suggestions
    
    def _suggest_ratio_metrics(
        self,
        catalog: str,
        schema: str,
        table: str,
        columns: List[Dict[str, Any]],
        analysis: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Suggest ratio and percentage metrics"""
        suggestions = []
        table_ref = f"`{catalog}`.`{schema}`.`{table}`"
        
        # Completion/Success rates based on boolean columns
        for bool_col in analysis["boolean_columns"]:
            col_name = bool_col['name']
            if any(term in col_name.lower() for term in ['success', 'complete', 'valid', 'approved']):
                suggestions.append({
                    "name": f"{col_name}_rate",
                    "display_name": f"{col_name.replace('_', ' ').title()} Rate",
                    "description": f"Percentage of records where {col_name} is true",
                    "category": "rate",
                    "metric_type": "percentage",
                    "sql": f"""
                        SELECT 
                            COUNT(CASE WHEN `{col_name}` = true THEN 1 END) * 100.0 / COUNT(*) as success_rate
                        FROM {table_ref}
                    """.strip(),
                    "complexity": "simple",
                    "business_value": "high"
                })
        
        # Null percentage for important columns
        important_cols = analysis["id_columns"][:2] + analysis["potential_measures"][:2]
        for col in important_cols:
            col_name = col['name']
            suggestions.append({
                "name": f"{col_name}_completeness",
                "display_name": f"{col_name.replace('_', ' ').title()} Completeness",
                "description": f"Percentage of non-null values for {col_name}",
                "category": "data_quality",
                "metric_type": "percentage",
                "sql": f"""
                    SELECT 
                        COUNT(`{col_name}`) * 100.0 / COUNT(*) as completeness_rate
                    FROM {table_ref}
                """.strip(),
                "complexity": "simple",
                "business_value": "medium"
            })
        
        return suggestions
    
    def _suggest_business_metrics(
        self,
        catalog: str,
        schema: str,
        table: str,
        columns: List[Dict[str, Any]],
        analysis: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Suggest business-specific metrics based on domain patterns"""
        suggestions = []
        table_ref = f"`{catalog}`.`{schema}`.`{table}`"
        
        # Detect domain from table/column names
        table_lower = table.lower()
        column_names = [col['name'].lower() for col in columns]
        
        # E-commerce metrics
        if any(term in table_lower for term in ['order', 'purchase', 'transaction']):
            # Average order value
            amount_cols = [col for col in analysis["potential_measures"] 
                          if any(term in col['name'].lower() for term in ['amount', 'total', 'price'])]
            if amount_cols:
                col_name = amount_cols[0]['name']
                suggestions.append({
                    "name": "average_order_value",
                    "display_name": "Average Order Value (AOV)",
                    "description": "Average value per order",
                    "category": "revenue",
                    "metric_type": "business_kpi",
                    "sql": f"SELECT AVG(`{col_name}`) as aov FROM {table_ref}",
                    "complexity": "simple",
                    "business_value": "high"
                })
        
        # Customer/User metrics
        if any(term in table_lower for term in ['customer', 'user', 'account']):
            # Active users
            if analysis["timestamp_columns"]:
                ts_col = analysis["timestamp_columns"][0]['name']
                suggestions.append({
                    "name": "monthly_active_users",
                    "display_name": "Monthly Active Users (MAU)",
                    "description": "Unique users active in the last 30 days",
                    "category": "engagement",
                    "metric_type": "business_kpi",
                    "sql": f"""
                        SELECT COUNT(DISTINCT user_id) as mau
                        FROM {table_ref}
                        WHERE `{ts_col}` >= DATEADD(day, -30, CURRENT_DATE())
                    """.strip(),
                    "complexity": "medium",
                    "business_value": "high"
                })
        
        # Conversation/Communication metrics
        if any(term in table_lower for term in ['conversation', 'message', 'call']):
            # Average conversation duration
            duration_cols = [col for col in analysis["potential_measures"]
                           if any(term in col['name'].lower() for term in ['duration', 'length', 'time'])]
            if duration_cols:
                col_name = duration_cols[0]['name']
                suggestions.append({
                    "name": "avg_conversation_duration",
                    "display_name": "Average Conversation Duration",
                    "description": "Average duration of conversations",
                    "category": "performance",
                    "metric_type": "business_kpi",
                    "sql": f"""
                        SELECT 
                            AVG(`{col_name}`) as avg_duration,
                            AVG(`{col_name}`) / 60 as avg_duration_minutes
                        FROM {table_ref}
                        WHERE `{col_name}` > 0
                    """.strip(),
                    "complexity": "simple",
                    "business_value": "high"
                })
        
        return suggestions
    
    def _score_suggestions(
        self, 
        suggestions: List[Dict[str, Any]], 
        analysis: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Score and prioritize metric suggestions"""
        scored_suggestions = []
        
        for suggestion in suggestions:
            score = 0
            
            # Business value scoring
            if suggestion.get("business_value") == "high":
                score += 30
            elif suggestion.get("business_value") == "medium":
                score += 20
            else:
                score += 10
            
            # Complexity scoring (simpler is better for auto-suggestions)
            if suggestion.get("complexity") == "simple":
                score += 20
            elif suggestion.get("complexity") == "medium":
                score += 10
            else:
                score += 5
            
            # Category scoring based on table type
            if analysis["table_type"] == "fact" and suggestion.get("category") in ["aggregation", "time_series"]:
                score += 15
            elif analysis["table_type"] == "dimension" and suggestion.get("category") in ["uniqueness", "completeness"]:
                score += 15
            elif analysis["table_type"] == "transaction" and suggestion.get("category") in ["volume", "growth"]:
                score += 15
            
            # Boost KPIs
            if suggestion.get("metric_type") == "business_kpi":
                score += 20
            
            suggestion["score"] = score
            scored_suggestions.append(suggestion)
        
        return scored_suggestions
    
    def _initialize_metric_templates(self) -> List[MetricTemplate]:
        """Initialize reusable metric templates"""
        return [
            MetricTemplate(
                name="conversion_rate",
                display_name="Conversion Rate",
                description="Percentage of successful conversions",
                metric_type="percentage",
                sql_template="""
                    SELECT 
                        COUNT(CASE WHEN {success_column} = true THEN 1 END) * 100.0 / COUNT(*) as conversion_rate
                    FROM {table}
                """,
                required_columns=[
                    {"type": "boolean", "purpose": "success_indicator"}
                ],
                category="conversion",
                business_value="high"
            ),
            MetricTemplate(
                name="retention_rate",
                display_name="User Retention Rate",
                description="Percentage of users retained over time",
                metric_type="cohort",
                sql_template="""
                    WITH cohorts AS (
                        SELECT 
                            {user_id_column},
                            DATE_TRUNC('month', MIN({timestamp_column})) as cohort_month
                        FROM {table}
                        GROUP BY {user_id_column}
                    )
                    SELECT 
                        cohort_month,
                        COUNT(DISTINCT c.{user_id_column}) as cohort_size,
                        COUNT(DISTINCT CASE WHEN t.{timestamp_column} >= DATEADD(month, 1, c.cohort_month) THEN c.{user_id_column} END) as retained_users
                    FROM cohorts c
                    JOIN {table} t ON c.{user_id_column} = t.{user_id_column}
                    GROUP BY cohort_month
                """,
                required_columns=[
                    {"type": "id", "purpose": "user_identifier"},
                    {"type": "timestamp", "purpose": "activity_timestamp"}
                ],
                category="retention",
                complexity="complex",
                business_value="high"
            )
        ]

