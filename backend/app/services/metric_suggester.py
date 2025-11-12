"""
Metric Suggester Service for suggesting metrics based on table analysis.
Uses pattern recognition and business logic to suggest relevant metrics.
"""
from typing import List, Dict, Any, Optional, Tuple
import re
import structlog

from app.models.semantic import SuggestedMetric, SuggestedDimension
from app.models.catalog import TableAnalysis, ColumnInfo


logger = structlog.get_logger()


class MetricSuggester:
    """Service for suggesting metrics from analyzed tables"""
    
    def __init__(self):
        """Initialize metric suggester with pattern rules"""
        # Industry patterns for context-aware suggestions
        self.industry_patterns = {
            'retail': {
                'keywords': ['sales', 'order', 'product', 'customer', 'store'],
                'metrics': [
                    ('basket_size', 'Average number of items per order', 'AVG(quantity)'),
                    ('conversion_rate', 'Percentage of visitors who make a purchase', 'COUNT(DISTINCT order_id) / COUNT(DISTINCT visitor_id)'),
                    ('customer_lifetime_value', 'Total revenue per customer', 'SUM(revenue) / COUNT(DISTINCT customer_id)')
                ]
            },
            'finance': {
                'keywords': ['transaction', 'account', 'balance', 'payment'],
                'metrics': [
                    ('transaction_volume', 'Total transaction amount', 'SUM(amount)'),
                    ('average_balance', 'Average account balance', 'AVG(balance)'),
                    ('payment_success_rate', 'Percentage of successful payments', 'SUM(CASE WHEN status = "success" THEN 1 ELSE 0 END) / COUNT(*)')
                ]
            },
            'logistics': {
                'keywords': ['shipment', 'delivery', 'warehouse', 'inventory'],
                'metrics': [
                    ('on_time_delivery_rate', 'Percentage of on-time deliveries', 'SUM(CASE WHEN delivered_date <= promised_date THEN 1 ELSE 0 END) / COUNT(*)'),
                    ('inventory_turnover', 'Rate of inventory movement', 'SUM(quantity_sold) / AVG(inventory_level)'),
                    ('fulfillment_time', 'Average time from order to delivery', 'AVG(DATEDIFF(delivered_date, order_date))')
                ]
            }
        }
        
        # Common metric patterns by column type
        self.metric_patterns = {
            'amount': [
                ('total_{column}', 'Total {column}', 'SUM({column})', 0.95),
                ('avg_{column}', 'Average {column}', 'AVG({column})', 0.85),
                ('max_{column}', 'Maximum {column}', 'MAX({column})', 0.70),
                ('min_{column}', 'Minimum {column}', 'MIN({column})', 0.70)
            ],
            'quantity': [
                ('total_{column}', 'Total {column}', 'SUM({column})', 0.90),
                ('avg_{column}', 'Average {column}', 'AVG({column})', 0.85),
                ('distinct_{column}', 'Unique {column} count', 'COUNT(DISTINCT {column})', 0.80)
            ],
            'percentage': [
                ('avg_{column}', 'Average {column}', 'AVG({column})', 0.90),
                ('weighted_avg_{column}', 'Weighted average {column}', 'SUM({column} * weight) / SUM(weight)', 0.75)
            ],
            'duration': [
                ('avg_{column}', 'Average {column}', 'AVG({column})', 0.95),
                ('max_{column}', 'Maximum {column}', 'MAX({column})', 0.85),
                ('min_{column}', 'Minimum {column}', 'MIN({column})', 0.85),
                ('p95_{column}', '95th percentile {column}', 'PERCENTILE_CONT(0.95) WITHIN GROUP (ORDER BY {column})', 0.80),
                ('p99_{column}', '99th percentile {column}', 'PERCENTILE_CONT(0.99) WITHIN GROUP (ORDER BY {column})', 0.80)
            ],
            'boolean': [
                ('{column}_rate', '{column} rate', 'SUM(CASE WHEN {column} THEN 1 ELSE 0 END) / COUNT(*)', 0.85),
                ('{column}_count', 'Count of {column}', 'SUM(CASE WHEN {column} THEN 1 ELSE 0 END)', 0.80)
            ],
            'id': [
                ('distinct_{column}_count', 'Unique {column} count', 'COUNT(DISTINCT {column})', 0.85),
                ('total_records', 'Total record count', 'COUNT(*)', 0.80)
            ]
        }
    
    def suggest_metrics(self, analyzed_table: Dict[str, Any]) -> List[SuggestedMetric]:
        """Generate metric suggestions based on table analysis"""
        suggestions = []
        
        # Detect industry context
        industry_context = analyzed_table.get('industry_context') or self._detect_industry(analyzed_table)
        
        # Generate basic metrics from numeric columns
        basic_metrics = self._suggest_basic_metrics(analyzed_table)
        suggestions.extend(basic_metrics)
        
        # Generate calculated metrics
        calculated_metrics = self._suggest_calculated_metrics(analyzed_table)
        suggestions.extend(calculated_metrics)
        
        # Generate time-based metrics if date columns exist
        if self._has_time_dimension(analyzed_table):
            time_metrics = self._suggest_time_based_metrics(analyzed_table)
            suggestions.extend(time_metrics)
        
        # Add industry-specific metrics
        if industry_context:
            industry_metrics = self._suggest_industry_metrics(analyzed_table, industry_context)
            suggestions.extend(industry_metrics)
        
        # Score and rank suggestions
        suggestions = self._score_and_rank_metrics(suggestions, analyzed_table)
        
        # Remove duplicates and sort by confidence
        seen = set()
        unique_suggestions = []
        for metric in sorted(suggestions, key=lambda m: m.confidence_score, reverse=True):
            if metric.name not in seen:
                seen.add(metric.name)
                unique_suggestions.append(metric)
        
        return unique_suggestions
    
    def _suggest_basic_metrics(self, analyzed_table: Dict[str, Any]) -> List[SuggestedMetric]:
        """Suggest basic aggregation metrics from numeric columns"""
        suggestions = []
        columns = analyzed_table.get('columns', {})
        
        for col_name, col_info in columns.items():
            pattern = col_info.get('pattern')
            data_type = col_info.get('data_type', '')
            
            # Skip ID columns and system columns
            if pattern == 'identifier' or col_name.startswith('_'):
                continue
            
            # Get patterns for this column type
            patterns = []
            if pattern == 'metric' and any(t in data_type.upper() for t in ['DECIMAL', 'DOUBLE', 'FLOAT', 'NUMERIC']):
                if any(p in col_name.lower() for p in ['amount', 'price', 'cost', 'revenue', 'total']):
                    patterns = self.metric_patterns.get('amount', [])
                elif any(p in col_name.lower() for p in ['latency', 'duration', 'time', 'seconds', 'ms']):
                    patterns = self.metric_patterns.get('duration', [])
                else:
                    patterns = self.metric_patterns.get('quantity', [])
            elif pattern == 'metric' and 'INT' in data_type.upper():
                patterns = self.metric_patterns.get('quantity', [])
            elif pattern == 'filter' or data_type == 'BOOLEAN':
                patterns = self.metric_patterns.get('boolean', [])
            
            # Generate metrics from patterns
            for pattern_template, desc_template, expr_template, confidence in patterns:
                metric_name = pattern_template.format(column=col_name)
                description = desc_template.format(column=col_name.replace('_', ' '))
                expression = expr_template.format(column=col_name)
                
                # Determine aggregation type
                agg = None
                if 'SUM(' in expression:
                    agg = 'sum'
                elif 'AVG(' in expression:
                    agg = 'avg'
                elif 'COUNT(' in expression:
                    agg = 'count_distinct' if 'DISTINCT' in expression else 'count'
                elif 'MAX(' in expression:
                    agg = 'max'
                elif 'MIN(' in expression:
                    agg = 'min'
                
                # Create more user-friendly display names
                display_name = description
                if 'latency' in col_name.lower() or 'duration' in col_name.lower():
                    # Clean up latency/duration metric names
                    display_name = display_name.replace('avg agent speech latency ms', 'Agent Speech Latency (ms)')
                    display_name = display_name.replace('percentile', 'Percentile')
                
                metric = SuggestedMetric(
                    name=metric_name,
                    display_name=display_name,
                    base_column=col_name if agg else None,
                    aggregation=agg,
                    expression=expression,
                    metric_type='simple' if agg else 'derived',
                    description=description,
                    confidence_score=confidence * col_info.get('confidence_modifier', 1.0),
                    format='number' if 'latency' in col_name.lower() or 'duration' in col_name.lower() else None
                )
                suggestions.append(metric)
        
        return suggestions
    
    def _suggest_calculated_metrics(self, analyzed_table: Dict[str, Any]) -> List[SuggestedMetric]:
        """Suggest calculated metrics based on multiple columns"""
        suggestions = []
        columns = analyzed_table.get('columns', {})
        
        # Average order value (if revenue and order count exist)
        if 'revenue' in columns and any('order' in c for c in columns):
            suggestions.append(SuggestedMetric(
                name='avg_order_value',
                display_name='Average Order Value',
                expression='SUM(revenue) / COUNT(DISTINCT order_id)',
                metric_type='derived',
                description='Average revenue per order',
                confidence_score=0.90
            ))
        
        # Discount rate (if discount and revenue exist)
        if 'discount_amount' in columns and 'revenue' in columns:
            suggestions.append(SuggestedMetric(
                name='discount_rate',
                display_name='Discount Rate',
                expression='SUM(discount_amount) / (SUM(revenue) + SUM(discount_amount))',
                metric_type='derived',
                description='Percentage of revenue given as discount',
                confidence_score=0.85,
                format='percentage'
            ))
        
        # Return rate (if return flag exists)
        return_cols = [c for c in columns if 'return' in c.lower() and columns[c].get('data_type') == 'BOOLEAN']
        if return_cols:
            return_col = return_cols[0]
            suggestions.append(SuggestedMetric(
                name='return_rate',
                display_name='Return Rate',
                expression=f'SUM(CASE WHEN {return_col} THEN 1 ELSE 0 END) / COUNT(*)',
                metric_type='derived',
                description='Percentage of orders that were returned',
                confidence_score=0.85,
                format='percentage'
            ))
        
        # Profit margin (if cost and revenue exist)
        cost_cols = [c for c in columns if 'cost' in c.lower() and columns[c].get('pattern') == 'metric']
        revenue_cols = [c for c in columns if 'revenue' in c.lower() and columns[c].get('pattern') == 'metric']
        if cost_cols and revenue_cols:
            cost_col = cost_cols[0]
            revenue_col = revenue_cols[0]
            suggestions.append(SuggestedMetric(
                name='profit_margin',
                display_name='Profit Margin',
                expression=f'(SUM({revenue_col}) - SUM({cost_col})) / SUM({revenue_col})',
                metric_type='derived',
                description='Profit as percentage of revenue',
                confidence_score=0.88,
                format='percentage'
            ))
        
        return suggestions
    
    def _suggest_time_based_metrics(self, analyzed_table: Dict[str, Any]) -> List[SuggestedMetric]:
        """Suggest time-based metrics when date columns exist"""
        suggestions = []
        columns = analyzed_table.get('columns', {})
        
        # Find primary date column
        date_cols = [c for c in columns if columns[c].get('pattern') == 'time_dimension' 
                     and columns[c].get('data_type') == 'DATE']
        
        if not date_cols:
            return suggestions
        
        primary_date = date_cols[0]  # Use first date column
        
        # Find primary metric column
        metric_cols = [c for c in columns if columns[c].get('pattern') == 'metric' 
                       and 'revenue' in c.lower()]
        if not metric_cols:
            metric_cols = [c for c in columns if columns[c].get('pattern') == 'metric']
        
        if metric_cols:
            metric_col = metric_cols[0]
            
            # Growth rate
            suggestions.append(SuggestedMetric(
                name=f'{metric_col}_growth_rate',
                display_name=f'{metric_col.replace("_", " ").title()} Growth Rate',
                expression=f'(SUM({metric_col}) - LAG(SUM({metric_col}), 1) OVER (ORDER BY {primary_date})) / LAG(SUM({metric_col}), 1) OVER (ORDER BY {primary_date})',
                metric_type='derived',
                description=f'Period-over-period growth rate for {metric_col}',
                confidence_score=0.82,
                requires_time_dimension=True,
                format='percentage'
            ))
            
            # Rolling average
            suggestions.append(SuggestedMetric(
                name=f'rolling_7_day_{metric_col}',
                display_name=f'7-Day Rolling {metric_col.replace("_", " ").title()}',
                expression=f'AVG(SUM({metric_col})) OVER (ORDER BY {primary_date} ROWS BETWEEN 6 PRECEDING AND CURRENT ROW)',
                metric_type='derived',
                description=f'7-day rolling average of {metric_col}',
                confidence_score=0.80,
                requires_time_dimension=True
            ))
        
        # Orders per day (if order ID exists)
        order_cols = [c for c in columns if 'order' in c.lower() and columns[c].get('pattern') == 'identifier']
        if order_cols:
            suggestions.append(SuggestedMetric(
                name='orders_per_day',
                display_name='Orders Per Day',
                expression=f'COUNT(DISTINCT {order_cols[0]}) / COUNT(DISTINCT {primary_date})',
                metric_type='derived',
                description='Average number of orders per day',
                confidence_score=0.85,
                requires_time_dimension=True
            ))
        
        return suggestions
    
    def _suggest_industry_metrics(self, analyzed_table: Dict[str, Any], industry: str) -> List[SuggestedMetric]:
        """Suggest industry-specific metrics"""
        suggestions = []
        
        if industry not in self.industry_patterns:
            return suggestions
        
        industry_config = self.industry_patterns[industry]
        columns = analyzed_table.get('columns', {})
        
        # Check if we have required columns for each industry metric
        for metric_name, description, expression_template in industry_config['metrics']:
            # Simple check if referenced columns might exist
            required_cols = re.findall(r'\b(\w+)\b', expression_template)
            available_cols = [col for col in required_cols if any(col in c for c in columns)]
            
            if len(available_cols) >= len(required_cols) * 0.5:  # 50% match threshold
                suggestions.append(SuggestedMetric(
                    name=metric_name,
                    display_name=description,
                    expression=expression_template,
                    metric_type='derived',
                    description=description,
                    category=industry,
                    confidence_score=0.75
                ))
        
        return suggestions
    
    def _detect_industry(self, analyzed_table: Dict[str, Any]) -> Optional[str]:
        """Detect industry based on table and column names"""
        table_name = analyzed_table.get('table_name', '').lower()
        columns = analyzed_table.get('columns', {})
        all_text = table_name + ' ' + ' '.join(columns.keys()).lower()
        
        best_match = None
        best_score = 0
        
        for industry, config in self.industry_patterns.items():
            score = sum(1 for keyword in config['keywords'] if keyword in all_text)
            if score > best_score:
                best_score = score
                best_match = industry
        
        return best_match if best_score >= 2 else None  # Need at least 2 keyword matches
    
    def _has_time_dimension(self, analyzed_table: Dict[str, Any]) -> bool:
        """Check if table has time dimension columns"""
        columns = analyzed_table.get('columns', {})
        return any(col.get('pattern') == 'time_dimension' for col in columns.values())
    
    def _score_and_rank_metrics(self, metrics: List[SuggestedMetric], analyzed_table: Dict[str, Any]) -> List[SuggestedMetric]:
        """Score and rank metrics by relevance and confidence"""
        columns = analyzed_table.get('columns', {})
        
        for metric in metrics:
            # Adjust confidence based on various factors
            
            # Boost metrics on high-value columns (like revenue)
            if metric.base_column and metric.base_column in columns:
                col_info = columns[metric.base_column]
                avg_val = col_info.get('avg_value')
                if avg_val and avg_val > 100:  # High value column
                    metric.confidence_score *= 1.1
            
            # Boost commonly used metric types
            if any(common in metric.name for common in ['total', 'count', 'average']):
                metric.confidence_score *= 1.05
            
            # Reduce confidence for complex expressions
            if metric.expression.count('(') > 3:
                metric.confidence_score *= 0.9
            
            # Ensure score stays in valid range
            metric.confidence_score = max(0.0, min(1.0, metric.confidence_score))
        
        return metrics
