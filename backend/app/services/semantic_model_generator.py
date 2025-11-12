"""
Service to generate semantic models from SQL queries
"""
from typing import Dict, List, Any, Optional, Tuple
from pathlib import Path
import re
import yaml
import structlog

from app.models.semantic_model import (
    SemanticModelCreate,
    SemanticModelYAML,
    Entity,
    Dimension,
    Measure,
    Metric
)
from app.core.config import settings

logger = structlog.get_logger()


class SemanticModelGenerator:
    """Generate semantic model YAML from SQL queries"""
    
    def __init__(self):
        self.models_path = Path(settings.semantic_models_path)
        self.models_path.mkdir(parents=True, exist_ok=True)
    
    def generate_from_sql(self, request: SemanticModelCreate) -> Dict[str, Any]:
        """
        Generate a semantic model from SQL query
        
        Args:
            request: Semantic model creation request with SQL
            
        Returns:
            Dict with the generated model info and file path
        """
        try:
            # Parse SQL to extract components
            sql_info = self._parse_sql(request.sql)
            
            # Extract base table
            base_table = sql_info.get("main_table", "unknown_table")
            catalog, schema, table = self._parse_table_name(base_table)
            
            # Generate model reference
            if catalog and schema:
                model_ref = f"ref('{catalog}.{schema}.{table}')"
            elif schema:
                model_ref = f"ref('{schema}.{table}')"
            else:
                model_ref = f"ref('{table}')"
            
            # Extract components from SQL
            entities = self._extract_entities(sql_info)
            dimensions = self._extract_dimensions(sql_info)
            measures = self._extract_measures(sql_info)
            
            # Create the metric
            metric = Metric(
                name=self._sanitize_name(request.metric_name),
                type="simple",
                description=request.metric_description,
                sql=request.sql
            )
            
            # If we have measures, link the metric to the first one
            if measures:
                metric.measure = measures[0].name
            
            # Create the semantic model
            model = SemanticModelYAML(
                name=self._sanitize_name(request.name),
                description=request.description,
                model=model_ref,
                entities=entities,
                dimensions=dimensions,
                measures=measures,
                metrics=[metric],
                metadata={
                    "category": request.category,
                    "natural_language_source": request.natural_language,
                    "genie_conversation_id": request.conversation_id,
                    "genie_message_id": request.message_id,
                    "created_by": "genie_natural_language"
                }
            )
            
            # Check if model already exists
            filename = f"{model.name}.yml"
            file_path = self.models_path / filename
            
            if file_path.exists():
                # Load existing model and merge
                with open(file_path, 'r') as f:
                    existing_data = yaml.safe_load(f)
                
                # Merge entities (avoiding duplicates)
                existing_entities = {e['name']: e for e in existing_data.get('entities', [])}
                for entity in entities:
                    if entity.name not in existing_entities:
                        existing_entities[entity.name] = entity.dict()
                model.entities = [Entity(**e) for e in existing_entities.values()]
                
                # Merge dimensions (avoiding duplicates)
                existing_dims = {d['name']: d for d in existing_data.get('dimensions', [])}
                for dim in dimensions:
                    if dim.name not in existing_dims:
                        existing_dims[dim.name] = dim.dict()
                model.dimensions = [Dimension(**d) for d in existing_dims.values()]
                
                # Merge measures (avoiding duplicates)
                existing_measures = {m['name']: m for m in existing_data.get('measures', [])}
                for measure in measures:
                    if measure.name not in existing_measures:
                        existing_measures[measure.name] = measure.dict()
                model.measures = [Measure(**m) for m in existing_measures.values()]
                
                # Merge metrics (avoiding duplicates)
                existing_metrics = {m['name']: m for m in existing_data.get('metrics', [])}
                for metric in model.metrics:
                    existing_metrics[metric.name] = metric.dict()
                model.metrics = [Metric(**m) for m in existing_metrics.values()]
            
            self._save_to_yaml(model, file_path)
            
            logger.info(f"Created semantic model {model.name}", file_path=str(file_path))
            
            return {
                "success": True,
                "message": "Semantic model created successfully",
                "model_name": model.name,
                "file_path": str(file_path),
                "model_structure": model.dict()
            }
            
        except Exception as e:
            logger.error("Failed to generate semantic model", error=str(e))
            raise
    
    def _parse_sql(self, sql: str) -> Dict[str, Any]:
        """Parse SQL to extract structure information"""
        info = {
            "tables": [],
            "main_table": None,
            "select_columns": [],
            "group_by_columns": [],
            "aggregations": [],
            "where_conditions": [],
            "order_by_columns": []
        }
        
        # Normalize SQL
        sql = ' '.join(sql.split())
        
        # Extract main table from FROM clause
        from_pattern = r'FROM\s+(?:`([^`]+)`|"([^"]+)"|(\S+))'
        from_match = re.search(from_pattern, sql, re.IGNORECASE)
        if from_match:
            info['main_table'] = from_match.group(1) or from_match.group(2) or from_match.group(3)
            info['tables'].append(info['main_table'])
        
        # Extract SELECT columns
        select_pattern = r'SELECT\s+(.*?)\s+FROM'
        select_match = re.search(select_pattern, sql, re.IGNORECASE | re.DOTALL)
        if select_match:
            select_clause = select_match.group(1)
            # Split by comma but respect parentheses
            columns = self._split_columns(select_clause)
            info['select_columns'] = columns
            
            # Extract aggregations
            agg_pattern = r'\b(COUNT|SUM|AVG|MAX|MIN)\s*\('
            for col in columns:
                if re.search(agg_pattern, col, re.IGNORECASE):
                    info['aggregations'].append(col)
        
        # Extract GROUP BY columns
        group_pattern = r'GROUP\s+BY\s+(.*?)(?:ORDER|LIMIT|$)'
        group_match = re.search(group_pattern, sql, re.IGNORECASE)
        if group_match:
            group_clause = group_match.group(1)
            info['group_by_columns'] = [col.strip() for col in group_clause.split(',')]
        
        return info
    
    def _parse_table_name(self, table_name: str) -> Tuple[Optional[str], Optional[str], str]:
        """Parse table name into catalog, schema, and table parts"""
        parts = table_name.split('.')
        if len(parts) == 3:
            return parts[0], parts[1], parts[2]
        elif len(parts) == 2:
            return None, parts[0], parts[1]
        else:
            return None, None, parts[0]
    
    def _extract_entities(self, sql_info: Dict[str, Any]) -> List[Entity]:
        """Extract entities from SQL info"""
        entities = []
        seen_entities = set()
        
        # Look for common ID columns in select/group by
        id_patterns = ['id', '_id', 'key', '_key']
        
        # Combine columns and remove duplicates
        all_columns = sql_info.get('select_columns', []) + sql_info.get('group_by_columns', [])
        
        for col in all_columns:
            col_lower = col.lower()
            for pattern in id_patterns:
                if pattern in col_lower:
                    # Extract the actual column name
                    col_name = self._extract_column_name(col)
                    if col_name and col_name not in seen_entities:
                        seen_entities.add(col_name)
                        
                        # Determine entity type based on column name
                        if 'tenant' in col_lower:
                            entity_type = "primary"
                        elif 'conversation' in col_lower or 'session' in col_lower:
                            entity_type = "primary"
                        elif 'user' in col_lower or 'customer' in col_lower:
                            entity_type = "primary"
                        else:
                            entity_type = "foreign"
                        
                        entities.append(Entity(
                            name=col_name,
                            type=entity_type,
                            expr=col_name
                        ))
                        break
        
        return entities
    
    def _extract_dimensions(self, sql_info: Dict[str, Any]) -> List[Dimension]:
        """Extract dimensions from SQL info"""
        dimensions = []
        seen = set()
        
        # Time dimensions
        time_patterns = ['date', 'time', 'timestamp', 'day', 'month', 'year', 'hour']
        time_functions = ['HOUR', 'DAY', 'DAYOFWEEK', 'MONTH', 'YEAR', 'DATE_TRUNC']
        
        for col in sql_info.get('group_by_columns', []):
            col_name = self._extract_column_name(col)
            if col_name and col_name not in seen:
                seen.add(col_name)
                
                # Check if it's a time dimension
                is_time = False
                for pattern in time_patterns:
                    if pattern in col.lower():
                        is_time = True
                        break
                
                # Check for time functions
                for func in time_functions:
                    if func in col.upper():
                        is_time = True
                        break
                
                if is_time:
                    dimensions.append(Dimension(
                        name=col_name,
                        type="time",
                        expr=col,
                        time_granularity=["day", "week", "month", "quarter", "year"]
                    ))
                else:
                    dimensions.append(Dimension(
                        name=col_name,
                        type="categorical",
                        expr=col
                    ))
        
        return dimensions
    
    def _extract_measures(self, sql_info: Dict[str, Any]) -> List[Measure]:
        """Extract measures from SQL info"""
        measures = []
        
        # Parse aggregations
        agg_pattern = r'(COUNT|SUM|AVG|MAX|MIN)\s*\(\s*(?:DISTINCT\s+)?([^)]+)\)'
        
        for agg_col in sql_info.get('aggregations', []):
            match = re.search(agg_pattern, agg_col, re.IGNORECASE)
            if match:
                agg_func = match.group(1).lower()
                expr = match.group(2).strip()
                
                # Generate a name for the measure
                measure_name = self._generate_measure_name(agg_func, expr)
                
                measures.append(Measure(
                    name=measure_name,
                    agg=agg_func,
                    expr=expr,
                    description=f"{agg_func.title()} of {expr}"
                ))
        
        return measures
    
    def _extract_column_name(self, col_expr: str) -> Optional[str]:
        """Extract clean column name from expression"""
        # Remove backticks and quotes
        col_expr = col_expr.strip().strip('`"\'')
        
        # Handle AS alias
        as_match = re.search(r'AS\s+[`"]?(\w+)[`"]?', col_expr, re.IGNORECASE)
        if as_match:
            return as_match.group(1)
        
        # Handle function expressions
        func_match = re.search(r'\w+\s*\(\s*[`"]?(\w+)[`"]?\s*\)', col_expr)
        if func_match:
            return f"{func_match.group(0).split('(')[0].strip().lower()}_{func_match.group(1)}"
        
        # Simple column
        if re.match(r'^\w+$', col_expr):
            return col_expr
        
        return None
    
    def _generate_measure_name(self, agg_func: str, expr: str) -> str:
        """Generate a name for a measure"""
        # Clean the expression
        expr_clean = re.sub(r'[`"\']', '', expr)
        expr_clean = re.sub(r'\W+', '_', expr_clean)
        
        # Common patterns
        if 'duration' in expr_clean.lower():
            return f"{agg_func}_duration"
        elif 'amount' in expr_clean.lower() or 'revenue' in expr_clean.lower():
            return f"{agg_func}_amount"
        elif 'count' in agg_func.lower():
            return f"count_{expr_clean}"
        else:
            return f"{agg_func}_{expr_clean}".lower()
    
    def _sanitize_name(self, name: str) -> str:
        """Sanitize name for YAML"""
        # Replace spaces and special characters with underscores
        name = re.sub(r'[^\w]+', '_', name)
        # Remove leading/trailing underscores
        name = name.strip('_')
        # Convert to lowercase
        return name.lower()
    
    def _split_columns(self, select_clause: str) -> List[str]:
        """Split SELECT clause into columns, respecting parentheses"""
        columns = []
        current = ""
        paren_count = 0
        
        for char in select_clause:
            if char == ',' and paren_count == 0:
                columns.append(current.strip())
                current = ""
            else:
                if char == '(':
                    paren_count += 1
                elif char == ')':
                    paren_count -= 1
                current += char
        
        if current.strip():
            columns.append(current.strip())
        
        return columns
    
    def _save_to_yaml(self, model: SemanticModelYAML, file_path: Path):
        """Save semantic model to YAML file"""
        # Convert to dict and clean up
        data = model.dict(exclude_none=True)
        
        # Convert lists of models to lists of dicts
        for key in ['entities', 'dimensions', 'measures', 'metrics']:
            if key in data:
                data[key] = [item for item in data[key]]
        
        # Write to file
        with open(file_path, 'w') as f:
            yaml.dump(data, f, default_flow_style=False, sort_keys=False)


# Singleton instance
_generator: Optional[SemanticModelGenerator] = None


def get_semantic_model_generator() -> SemanticModelGenerator:
    """Get or create semantic model generator"""
    global _generator
    if _generator is None:
        _generator = SemanticModelGenerator()
    return _generator
