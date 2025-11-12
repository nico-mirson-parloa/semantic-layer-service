"""
DEPRECATED: This module is deprecated and will be removed in a future version.

Use app.services.lineage_extractor.LineageExtractor instead.

Deprecation reasons:
1. Duplicates functionality in lineage_extractor.py
2. Uses unsafe regex-based SQL parsing instead of Unity Catalog system tables
3. Does not support recursive CTEs for efficient lineage traversal
4. Contains custom LineageNode class that duplicates Pydantic models in app.models.lineage
5. SQL injection vulnerabilities in _fetch_databricks_lineage method (line 314)

Migration guide:
- Replace DataLineageService with LineageExtractor
- Use LineageExtractor.extract_table_lineage() instead of get_table_lineage()
- Use LineageExtractor.extract_lineage_from_sql() for SQL parsing (if needed)
- Use app.models.lineage.LineageNode instead of the custom LineageNode class

For more details, see LINEAGE_IMPLEMENTATION_SPEC.md
"""

from typing import List, Dict, Any, Optional, Set
import structlog
import re
import warnings

from app.integrations.databricks import DatabricksConnector

warnings.warn(
    "data_lineage_service is deprecated. Use lineage_extractor instead. "
    "This module will be removed in a future version.",
    DeprecationWarning,
    stacklevel=2
)

logger = structlog.get_logger()


class LineageNode:
    """Represents a node in the data lineage graph"""
    def __init__(
        self,
        node_id: str,
        node_type: str,  # table, view, metric, dimension
        catalog: Optional[str] = None,
        schema: Optional[str] = None,
        name: str = None,
        metadata: Optional[Dict[str, Any]] = None
    ):
        self.node_id = node_id
        self.node_type = node_type
        self.catalog = catalog
        self.schema = schema
        self.name = name
        self.metadata = metadata or {}
        self.upstream_nodes: Set[str] = set()
        self.downstream_nodes: Set[str] = set()
    
    def add_upstream(self, node_id: str):
        """Add an upstream dependency"""
        self.upstream_nodes.add(node_id)
    
    def add_downstream(self, node_id: str):
        """Add a downstream dependency"""
        self.downstream_nodes.add(node_id)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation"""
        return {
            "node_id": self.node_id,
            "node_type": self.node_type,
            "catalog": self.catalog,
            "schema": self.schema,
            "name": self.name,
            "metadata": self.metadata,
            "upstream_nodes": list(self.upstream_nodes),
            "downstream_nodes": list(self.downstream_nodes)
        }


class DataLineageService:
    """Service for tracking and analyzing data lineage"""
    
    def __init__(self):
        self.databricks = DatabricksConnector()
        self.lineage_graph: Dict[str, LineageNode] = {}
    
    def extract_lineage_from_sql(self, sql: str, target_table: Optional[str] = None) -> Dict[str, Any]:
        """
        Extract data lineage from SQL query
        
        Args:
            sql: SQL query to analyze
            target_table: Target table being created/updated (if applicable)
            
        Returns:
            Lineage information including source tables and relationships
        """
        try:
            # Parse SQL to identify tables
            source_tables = self._extract_source_tables(sql)
            target_tables = self._extract_target_tables(sql) if not target_table else [target_table]
            
            # Build lineage graph
            lineage_info = {
                "source_tables": source_tables,
                "target_tables": target_tables,
                "relationships": [],
                "query_type": self._identify_query_type(sql)
            }
            
            # Create relationships
            for target in target_tables:
                target_node = self._get_or_create_node(target, "table")
                
                for source in source_tables:
                    source_node = self._get_or_create_node(source, "table")
                    
                    # Create relationship
                    target_node.add_upstream(source_node.node_id)
                    source_node.add_downstream(target_node.node_id)
                    
                    lineage_info["relationships"].append({
                        "source": source,
                        "target": target,
                        "relationship_type": "data_flow"
                    })
            
            return lineage_info
            
        except Exception as e:
            logger.error(f"Failed to extract lineage from SQL: {e}")
            return {
                "source_tables": [],
                "target_tables": [],
                "relationships": [],
                "error": str(e)
            }
    
    def get_table_lineage(self, catalog: str, schema: str, table: str, depth: int = 3) -> Dict[str, Any]:
        """
        Get upstream and downstream lineage for a table
        
        Args:
            catalog: Catalog name
            schema: Schema name
            table: Table name
            depth: How many levels to traverse
            
        Returns:
            Complete lineage information
        """
        try:
            table_ref = f"{catalog}.{schema}.{table}"
            
            # Try to get lineage from Databricks (if available)
            lineage_data = self._fetch_databricks_lineage(catalog, schema, table)
            
            # Build lineage graph
            if lineage_data:
                return self._build_lineage_graph(lineage_data, table_ref, depth)
            
            # Fallback: analyze table definition
            return self._analyze_table_definition(catalog, schema, table)
            
        except Exception as e:
            logger.error(f"Failed to get table lineage: {e}")
            return {
                "error": str(e),
                "upstream": [],
                "downstream": []
            }
    
    def analyze_semantic_model_lineage(self, model_path: str) -> Dict[str, Any]:
        """
        Analyze lineage for a semantic model
        
        Args:
            model_path: Path to semantic model YAML file
            
        Returns:
            Lineage information for the semantic model
        """
        try:
            import yaml
            
            with open(model_path, 'r') as f:
                model_data = yaml.safe_load(f)
            
            lineage_info = {
                "model_name": model_data.get('name'),
                "source_tables": [],
                "metrics": [],
                "dependencies": []
            }
            
            # Extract base model reference
            model_ref = model_data.get('model', '')
            if 'ref(' in model_ref:
                table_ref = model_ref.replace('ref(', '').replace(')', '').strip("'\"")
                lineage_info["source_tables"].append(table_ref)
            
            # Analyze metrics
            for metric in model_data.get('metrics', []):
                metric_info = {
                    "name": metric.get('name'),
                    "type": metric.get('type'),
                    "measure": metric.get('measure'),
                    "sql_tables": []
                }
                
                # Extract tables from metric SQL
                if metric.get('sql'):
                    metric_info["sql_tables"] = self._extract_source_tables(metric['sql'])
                
                lineage_info["metrics"].append(metric_info)
            
            # Analyze measures
            for measure in model_data.get('measures', []):
                expr = measure.get('expr', '')
                # Track which columns/expressions are used
                if '.' in expr:
                    table_alias = expr.split('.')[0].strip('`')
                    lineage_info["dependencies"].append({
                        "type": "measure",
                        "name": measure.get('name'),
                        "source": table_alias
                    })
            
            return lineage_info
            
        except Exception as e:
            logger.error(f"Failed to analyze semantic model lineage: {e}")
            return {"error": str(e)}
    
    def _extract_source_tables(self, sql: str) -> List[str]:
        """Extract source tables from SQL query"""
        tables = []
        
        # Remove comments
        sql = re.sub(r'--.*$', '', sql, flags=re.MULTILINE)
        sql = re.sub(r'/\*.*?\*/', '', sql, flags=re.DOTALL)
        
        # Common patterns for finding tables
        patterns = [
            r'FROM\s+`?([a-zA-Z0-9_]+(?:\.[a-zA-Z0-9_]+)*)`?',
            r'JOIN\s+`?([a-zA-Z0-9_]+(?:\.[a-zA-Z0-9_]+)*)`?',
            r'INTO\s+`?([a-zA-Z0-9_]+(?:\.[a-zA-Z0-9_]+)*)`?',
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, sql, re.IGNORECASE)
            tables.extend(matches)
        
        # Clean and deduplicate
        cleaned_tables = []
        for table in tables:
            # Skip aliases and keywords
            if table.upper() not in ['SELECT', 'WHERE', 'GROUP', 'ORDER', 'HAVING']:
                cleaned_tables.append(table)
        
        return list(set(cleaned_tables))
    
    def _extract_target_tables(self, sql: str) -> List[str]:
        """Extract target tables from SQL query"""
        tables = []
        
        # Patterns for target tables
        patterns = [
            r'CREATE\s+(?:OR\s+REPLACE\s+)?(?:TABLE|VIEW)\s+(?:IF\s+NOT\s+EXISTS\s+)?`?([a-zA-Z0-9_]+(?:\.[a-zA-Z0-9_]+)*)`?',
            r'INSERT\s+(?:INTO|OVERWRITE)\s+`?([a-zA-Z0-9_]+(?:\.[a-zA-Z0-9_]+)*)`?',
            r'UPDATE\s+`?([a-zA-Z0-9_]+(?:\.[a-zA-Z0-9_]+)*)`?',
            r'MERGE\s+INTO\s+`?([a-zA-Z0-9_]+(?:\.[a-zA-Z0-9_]+)*)`?',
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, sql, re.IGNORECASE)
            tables.extend(matches)
        
        return list(set(tables))
    
    def _identify_query_type(self, sql: str) -> str:
        """Identify the type of SQL query"""
        sql_upper = sql.upper().strip()
        
        if sql_upper.startswith('SELECT'):
            return 'SELECT'
        elif sql_upper.startswith('CREATE'):
            return 'CREATE'
        elif sql_upper.startswith('INSERT'):
            return 'INSERT'
        elif sql_upper.startswith('UPDATE'):
            return 'UPDATE'
        elif sql_upper.startswith('MERGE'):
            return 'MERGE'
        elif sql_upper.startswith('DELETE'):
            return 'DELETE'
        else:
            return 'OTHER'
    
    def _get_or_create_node(self, table_ref: str, node_type: str) -> LineageNode:
        """Get or create a lineage node"""
        if table_ref not in self.lineage_graph:
            parts = table_ref.split('.')
            if len(parts) == 3:
                catalog, schema, name = parts
            elif len(parts) == 2:
                catalog = None
                schema, name = parts
            else:
                catalog = None
                schema = None
                name = table_ref
            
            node = LineageNode(
                node_id=table_ref,
                node_type=node_type,
                catalog=catalog,
                schema=schema,
                name=name
            )
            self.lineage_graph[table_ref] = node
        
        return self.lineage_graph[table_ref]
    
    def _fetch_databricks_lineage(self, catalog: str, schema: str, table: str) -> Optional[Dict[str, Any]]:
        """Fetch lineage information from Databricks Unity Catalog"""
        try:
            # Query to get table dependencies
            query = f"""
                SELECT 
                    source_table_full_name,
                    target_table_full_name,
                    source_column_name,
                    target_column_name
                FROM system.access.column_lineage
                WHERE target_table_full_name = '{catalog}.{schema}.{table}'
                   OR source_table_full_name = '{catalog}.{schema}.{table}'
                LIMIT 1000
            """
            
            results = self.databricks.execute_query(query)
            
            if results:
                return {
                    "lineage_data": results,
                    "table": f"{catalog}.{schema}.{table}"
                }
            
        except Exception as e:
            logger.debug(f"Could not fetch Unity Catalog lineage: {e}")
        
        return None
    
    def _build_lineage_graph(self, lineage_data: Dict[str, Any], table_ref: str, depth: int) -> Dict[str, Any]:
        """Build lineage graph from Databricks data"""
        upstream_tables = set()
        downstream_tables = set()
        column_lineage = []
        
        for row in lineage_data.get("lineage_data", []):
            source_table = row.get("source_table_full_name")
            target_table = row.get("target_table_full_name")
            source_column = row.get("source_column_name")
            target_column = row.get("target_column_name")
            
            if target_table == table_ref:
                upstream_tables.add(source_table)
            else:
                downstream_tables.add(target_table)
            
            column_lineage.append({
                "source_table": source_table,
                "source_column": source_column,
                "target_table": target_table,
                "target_column": target_column
            })
        
        return {
            "table": table_ref,
            "upstream": list(upstream_tables),
            "downstream": list(downstream_tables),
            "column_lineage": column_lineage,
            "depth": depth
        }
    
    def _analyze_table_definition(self, catalog: str, schema: str, table: str) -> Dict[str, Any]:
        """Analyze table definition to extract lineage"""
        try:
            # Get table DDL
            query = f"SHOW CREATE TABLE `{catalog}`.`{schema}`.`{table}`"
            results = self.databricks.execute_query(query)
            
            if results and len(results) > 0:
                create_statement = results[0].get("createtab_stmt", "")
                
                # Extract source tables from CREATE statement
                source_tables = self._extract_source_tables(create_statement)
                
                return {
                    "table": f"{catalog}.{schema}.{table}",
                    "upstream": source_tables,
                    "downstream": [],  # Would need to scan other tables to find downstream
                    "definition_based": True
                }
            
        except Exception as e:
            logger.error(f"Failed to analyze table definition: {e}")
        
        return {
            "table": f"{catalog}.{schema}.{table}",
            "upstream": [],
            "downstream": [],
            "error": "Could not analyze table definition"
        }
    
    def visualize_lineage(self, lineage_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Convert lineage data to a format suitable for visualization
        
        Args:
            lineage_data: Raw lineage data
            
        Returns:
            Visualization-ready format with nodes and edges
        """
        nodes = []
        edges = []
        node_ids = set()
        
        # Add main table as central node
        main_table = lineage_data.get("table", "")
        if main_table:
            nodes.append({
                "id": main_table,
                "label": main_table.split('.')[-1],  # Use table name as label
                "type": "main",
                "level": 0
            })
            node_ids.add(main_table)
        
        # Add upstream nodes
        for i, upstream in enumerate(lineage_data.get("upstream", [])):
            if upstream not in node_ids:
                nodes.append({
                    "id": upstream,
                    "label": upstream.split('.')[-1],
                    "type": "upstream",
                    "level": -1
                })
                node_ids.add(upstream)
            
            edges.append({
                "source": upstream,
                "target": main_table,
                "type": "data_flow"
            })
        
        # Add downstream nodes
        for i, downstream in enumerate(lineage_data.get("downstream", [])):
            if downstream not in node_ids:
                nodes.append({
                    "id": downstream,
                    "label": downstream.split('.')[-1],
                    "type": "downstream",
                    "level": 1
                })
                node_ids.add(downstream)
            
            edges.append({
                "source": main_table,
                "target": downstream,
                "type": "data_flow"
            })
        
        return {
            "nodes": nodes,
            "edges": edges,
            "layout": "hierarchical"
        }

