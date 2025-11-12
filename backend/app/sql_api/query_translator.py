"""
SQL to semantic query translator.

This module translates SQL queries into semantic layer queries,
handling the mapping between SQL syntax and semantic model concepts.
"""

import re
import sqlparse
from sqlparse.sql import IdentifierList, Identifier, Where, Comparison, Function
from sqlparse.tokens import Keyword, DML, Punctuation, Whitespace, Literal, Name
from typing import Dict, List, Any, Optional, Tuple, Set
from dataclasses import dataclass, field

import structlog

from .virtual_schema import VirtualSchemaManager, VirtualTable

logger = structlog.get_logger()


@dataclass
class SemanticQuery:
    """Represents a translated semantic query."""
    model: str
    metrics: List[str] = field(default_factory=list)
    dimensions: List[str] = field(default_factory=list)
    measures: List[Dict[str, Any]] = field(default_factory=list)
    filters: Dict[str, Any] = field(default_factory=dict)
    order_by: List[Dict[str, str]] = field(default_factory=list)
    limit: Optional[int] = None
    time_granularity: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for API calls."""
        result = {
            'model': self.model,
            'metrics': self.metrics,
            'dimensions': self.dimensions,
            'filters': self.filters
        }
        
        if self.measures:
            result['measures'] = self.measures
        if self.order_by:
            result['order_by'] = self.order_by
        if self.limit is not None:
            result['limit'] = self.limit
        if self.time_granularity:
            result['time_granularity'] = self.time_granularity
            
        return result


class SQLToSemanticTranslator:
    """Translates SQL queries to semantic queries."""
    
    # Common aggregate functions
    AGGREGATE_FUNCTIONS = {
        'sum', 'avg', 'count', 'min', 'max',
        'stddev', 'stddev_pop', 'stddev_samp',
        'var_pop', 'var_samp', 'variance'
    }
    
    # Time granularity mappings
    TIME_GRANULARITIES = {
        'year': 'year',
        'quarter': 'quarter', 
        'month': 'month',
        'week': 'week',
        'day': 'day',
        'hour': 'hour',
        'minute': 'minute'
    }
    
    def __init__(self, schema_manager: Optional[VirtualSchemaManager] = None):
        """Initialize translator."""
        self.schema_manager = schema_manager or VirtualSchemaManager()
    
    async def translate(self, sql: str) -> Dict[str, Any]:
        """Translate SQL query to semantic query."""
        try:
            # Parse SQL
            parsed = sqlparse.parse(sql)[0]
            
            # Determine query type
            if parsed.get_type() == 'SELECT':
                return await self._translate_select(parsed)
            else:
                raise ValueError(f"Unsupported SQL statement type: {parsed.get_type()}")
                
        except Exception as e:
            logger.error(f"SQL translation failed: {e}", sql=sql)
            raise
    
    async def _translate_select(self, statement) -> Dict[str, Any]:
        """Translate SELECT statement."""
        query = SemanticQuery(model='')
        
        # Extract components
        tables = self._extract_tables(statement)
        if not tables:
            raise ValueError("No table found in FROM clause")
        
        # Get main table and semantic model
        main_table_ref = tables[0]
        table = self.schema_manager.get_table(main_table_ref)
        if not table:
            raise ValueError(f"Table not found: {main_table_ref}")
        
        # Set model name
        model_name = table.semantic_model.get('name', '')
        query.model = model_name
        
        # Extract SELECT columns
        select_list = self._extract_select_list(statement)
        self._process_select_list(select_list, table, query)
        
        # Extract WHERE clause
        where_clause = self._extract_where(statement)
        if where_clause:
            self._process_where_clause(where_clause, table, query)
        
        # Extract GROUP BY
        group_by = self._extract_group_by(statement)
        if group_by:
            self._process_group_by(group_by, table, query)
        
        # Extract ORDER BY
        order_by = self._extract_order_by(statement)
        if order_by:
            self._process_order_by(order_by, query)
        
        # Extract LIMIT
        limit = self._extract_limit(statement)
        if limit:
            query.limit = limit
        
        # Detect time granularity
        query.time_granularity = self._detect_time_granularity(query, table)
        
        return query.to_dict()
    
    def _extract_tables(self, statement) -> List[str]:
        """Extract table references from FROM clause."""
        tables = []
        from_seen = False
        
        for token in statement.tokens:
            if from_seen:
                if isinstance(token, IdentifierList):
                    for identifier in token.get_identifiers():
                        tables.append(str(identifier).strip())
                elif isinstance(token, Identifier):
                    tables.append(str(token).strip())
                elif token.ttype is None and not token.is_whitespace:
                    # Simple table name
                    table_name = str(token).strip()
                    if table_name and not self._is_keyword(table_name):
                        tables.append(table_name)
            elif token.ttype is Keyword and token.value.upper() == 'FROM':
                from_seen = True
            elif from_seen and token.ttype is Keyword:
                # Stop at next keyword (WHERE, GROUP BY, etc.)
                break
        
        return tables
    
    def _extract_select_list(self, statement) -> List[Any]:
        """Extract SELECT list items."""
        select_list = []
        select_seen = False
        
        for token in statement.tokens:
            if select_seen and token.ttype is Keyword:
                break
            elif token.ttype is DML and token.value.upper() == 'SELECT':
                select_seen = True
            elif select_seen:
                if isinstance(token, IdentifierList):
                    select_list.extend(token.get_identifiers())
                elif isinstance(token, (Identifier, Function)) or \
                     (token.ttype is None and not token.is_whitespace):
                    select_list.append(token)
        
        return select_list
    
    def _process_select_list(self, select_list: List[Any], table: VirtualTable, query: SemanticQuery):
        """Process SELECT list items into metrics/dimensions."""
        for item in select_list:
            if isinstance(item, Function):
                # Aggregate function - likely a measure
                func_name = self._get_function_name(item).lower()
                args = self._get_function_args(item)
                
                if func_name in self.AGGREGATE_FUNCTIONS:
                    # Check if this matches a predefined measure
                    measure_name = self._find_matching_measure(func_name, args, table)
                    if measure_name:
                        # It's a predefined measure - check if there's a metric
                        metric_name = self._find_metric_for_measure(measure_name, table)
                        if metric_name:
                            query.metrics.append(metric_name)
                        else:
                            query.measures.append({
                                'name': measure_name,
                                'agg': func_name,
                                'expr': args[0] if args else '*'
                            })
                    else:
                        # Ad-hoc measure
                        query.measures.append({
                            'name': f"{func_name}_{args[0] if args else 'all'}",
                            'agg': func_name,
                            'expr': args[0] if args else '*'
                        })
                        
            elif str(item).strip() == '*':
                # SELECT * - add all dimensions
                for col in table.columns:
                    if col.semantic_type == 'dimension':
                        query.dimensions.append(col.name)
                    elif col.semantic_type == 'metric':
                        query.metrics.append(col.name)
                        
            else:
                # Regular column - check type
                col_name = self._extract_column_name(item)
                col = table.get_column(col_name)
                
                if col:
                    if col.semantic_type == 'dimension':
                        query.dimensions.append(col_name)
                    elif col.semantic_type == 'metric':
                        query.metrics.append(col_name)
                    elif col.semantic_type == 'measure':
                        # Raw measure without aggregation
                        query.measures.append({
                            'name': col_name,
                            'agg': 'sum',  # Default aggregation
                            'expr': col_name
                        })
    
    def _extract_where(self, statement) -> Optional[Where]:
        """Extract WHERE clause."""
        for token in statement.tokens:
            if isinstance(token, Where):
                return token
        return None
    
    def _process_where_clause(self, where: Where, table: VirtualTable, query: SemanticQuery):
        """Process WHERE clause into filters."""
        # Simple filter extraction - can be enhanced
        conditions = self._extract_conditions(where)
        
        for column, operator, value in conditions:
            col = table.get_column(column)
            if col and col.semantic_type in ['dimension', 'entity']:
                if operator == '=':
                    query.filters[column] = value
                elif operator == 'IN':
                    query.filters[column] = {'in': value}
                elif operator in ['>', '>=', '<', '<=', '!=', '<>']:
                    query.filters[column] = {operator: value}
                elif operator == 'BETWEEN':
                    query.filters[column] = {'between': value}
                elif operator == 'LIKE':
                    query.filters[column] = {'like': value}
    
    def _extract_conditions(self, where: Where) -> List[Tuple[str, str, Any]]:
        """Extract conditions from WHERE clause."""
        conditions = []
        
        # Simple extraction - handles basic comparisons
        # This can be enhanced to handle complex boolean logic
        tokens = list(where.flatten())
        i = 0
        
        while i < len(tokens):
            if tokens[i].ttype in (Name, None) and not tokens[i].is_whitespace:
                column = str(tokens[i]).strip()
                
                # Look for operator
                i += 1
                while i < len(tokens) and tokens[i].is_whitespace:
                    i += 1
                
                if i < len(tokens):
                    operator = str(tokens[i]).strip().upper()
                    
                    # Look for value
                    i += 1
                    while i < len(tokens) and tokens[i].is_whitespace:
                        i += 1
                    
                    if i < len(tokens):
                        value = self._extract_value(tokens[i])
                        conditions.append((column, operator, value))
            
            i += 1
        
        return conditions
    
    def _extract_value(self, token) -> Any:
        """Extract value from token."""
        if token.ttype in Literal.Number:
            return float(str(token)) if '.' in str(token) else int(str(token))
        elif token.ttype in Literal.String:
            # Remove quotes
            value = str(token).strip()
            if value.startswith("'") and value.endswith("'"):
                return value[1:-1]
            return value
        else:
            return str(token).strip()
    
    def _extract_group_by(self, statement) -> List[str]:
        """Extract GROUP BY columns."""
        group_by = []
        group_by_seen = False
        
        for token in statement.tokens:
            if group_by_seen and token.ttype is Keyword:
                break
            elif token.ttype is Keyword and 'GROUP' in token.value.upper():
                group_by_seen = True
            elif group_by_seen and not token.is_whitespace:
                if isinstance(token, IdentifierList):
                    for identifier in token.get_identifiers():
                        group_by.append(self._extract_column_name(identifier))
                elif token.ttype is None:
                    col_name = str(token).strip()
                    if col_name and col_name != 'BY':
                        group_by.append(col_name)
        
        return group_by
    
    def _process_group_by(self, group_by: List[str], table: VirtualTable, query: SemanticQuery):
        """Process GROUP BY columns."""
        for col_name in group_by:
            col = table.get_column(col_name)
            if col and col.semantic_type == 'dimension':
                if col_name not in query.dimensions:
                    query.dimensions.append(col_name)
    
    def _extract_order_by(self, statement) -> List[Tuple[str, str]]:
        """Extract ORDER BY columns and directions."""
        order_by = []
        order_by_seen = False
        
        for token in statement.tokens:
            if order_by_seen and token.ttype is Keyword and token.value.upper() not in ['ASC', 'DESC']:
                break
            elif token.ttype is Keyword and 'ORDER' in token.value.upper():
                order_by_seen = True
            elif order_by_seen and not token.is_whitespace:
                if isinstance(token, IdentifierList):
                    for identifier in token.get_identifiers():
                        col_name = self._extract_column_name(identifier)
                        # Check for ASC/DESC after column
                        direction = 'asc'  # default
                        order_by.append((col_name, direction))
                elif token.ttype is None and str(token).strip() != 'BY':
                    col_name = str(token).strip()
                    if col_name:
                        direction = 'asc'
                        order_by.append((col_name, direction))
        
        return order_by
    
    def _process_order_by(self, order_by: List[Tuple[str, str]], query: SemanticQuery):
        """Process ORDER BY into query."""
        for col_name, direction in order_by:
            query.order_by.append({
                'column': col_name,
                'direction': direction
            })
    
    def _extract_limit(self, statement) -> Optional[int]:
        """Extract LIMIT value."""
        limit_seen = False
        
        for token in statement.tokens:
            if limit_seen and token.ttype in Literal.Number:
                return int(str(token))
            elif token.ttype is Keyword and token.value.upper() == 'LIMIT':
                limit_seen = True
        
        return None
    
    def _detect_time_granularity(self, query: SemanticQuery, table: VirtualTable) -> Optional[str]:
        """Detect time granularity from query."""
        # Check if any time dimension is being used
        time_dims = []
        for dim in query.dimensions:
            col = table.get_column(dim)
            if col and col.semantic_type == 'dimension':
                # Check if it's a time dimension in the model
                for model_dim in table.semantic_model.get('dimensions', []):
                    if model_dim['name'] == dim and model_dim.get('type') == 'time':
                        time_dims.append(dim)
        
        # For now, default to 'day' if time dimension is present
        if time_dims:
            return 'day'
        
        return None
    
    # Helper methods
    def _is_keyword(self, value: str) -> bool:
        """Check if value is a SQL keyword."""
        keywords = {
            'SELECT', 'FROM', 'WHERE', 'GROUP', 'BY', 'ORDER',
            'HAVING', 'LIMIT', 'OFFSET', 'JOIN', 'LEFT', 'RIGHT',
            'INNER', 'OUTER', 'ON', 'AND', 'OR', 'NOT', 'IN',
            'EXISTS', 'BETWEEN', 'LIKE', 'AS', 'ASC', 'DESC'
        }
        return value.upper() in keywords
    
    def _get_function_name(self, func: Function) -> str:
        """Extract function name."""
        for token in func.tokens:
            if token.ttype is Name or (token.ttype is None and not token.is_whitespace):
                name = str(token).strip()
                if name != '(' and not name.startswith('('):
                    return name
        return ''
    
    def _get_function_args(self, func: Function) -> List[str]:
        """Extract function arguments."""
        args = []
        in_parens = False
        
        for token in func.tokens:
            if str(token) == '(':
                in_parens = True
            elif str(token) == ')':
                break
            elif in_parens and not token.is_whitespace:
                if token.ttype is Punctuation and str(token) == ',':
                    continue
                args.append(str(token).strip())
        
        return args
    
    def _extract_column_name(self, identifier) -> str:
        """Extract column name from identifier."""
        if isinstance(identifier, Identifier):
            # Handle aliased columns
            return identifier.get_real_name() or str(identifier).strip()
        else:
            return str(identifier).strip()
    
    def _find_matching_measure(self, func_name: str, args: List[str], table: VirtualTable) -> Optional[str]:
        """Find a matching predefined measure."""
        if not args:
            return None
            
        arg = args[0].lower()
        
        # Check semantic model measures
        for measure in table.semantic_model.get('measures', []):
            if (measure.get('agg', '').lower() == func_name and
                measure.get('expr', '').lower() == arg):
                return measure['name']
        
        return None
    
    def _find_metric_for_measure(self, measure_name: str, table: VirtualTable) -> Optional[str]:
        """Find a metric that uses this measure."""
        for metric in table.semantic_model.get('metrics', []):
            if metric.get('type') == 'simple' and metric.get('measure') == measure_name:
                return metric['name']
        
        return None




