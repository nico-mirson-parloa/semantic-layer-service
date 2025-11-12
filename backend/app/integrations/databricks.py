"""
Databricks SQL integration using databricks-sql-connector
"""
from typing import List, Dict, Any, Optional, Union
from contextlib import contextmanager
import structlog
import numpy as np
from datetime import date, datetime
from decimal import Decimal
from databricks import sql
from app.core.config import settings

logger = structlog.get_logger()


class DatabricksConnector:
    """Manages connections to Databricks SQL Warehouse"""
    
    def __init__(self):
        self.host = settings.databricks_host
        self.http_path = settings.databricks_http_path
        self.token = settings.databricks_token
        self._validate_config()
    
    def _convert_to_serializable(self, value: Any) -> Any:
        """Convert numpy/special types to JSON-serializable format"""
        if isinstance(value, np.ndarray):
            return value.tolist()
        elif isinstance(value, np.generic):
            return value.item()
        elif isinstance(value, Decimal):
            return float(value)
        elif isinstance(value, (date, datetime)):
            return value.isoformat()
        elif isinstance(value, bytes):
            return value.decode('utf-8', errors='replace')
        return value
    
    def _validate_config(self):
        """Validate Databricks configuration"""
        if not all([self.host, self.http_path, self.token]):
            raise ValueError(
                "Databricks configuration incomplete. Please set "
                "DATABRICKS_HOST, DATABRICKS_HTTP_PATH, and DATABRICKS_TOKEN"
            )
    
    @contextmanager
    def get_connection(self):
        """Get a Databricks SQL connection"""
        connection = None
        try:
            logger.info("Connecting to Databricks SQL Warehouse", host=self.host)
            connection = sql.connect(
                server_hostname=self.host,
                http_path=self.http_path,
                access_token=self.token
            )
            yield connection
        except Exception as e:
            logger.error("Failed to connect to Databricks", error=str(e))
            raise
        finally:
            if connection:
                connection.close()
                logger.debug("Closed Databricks connection")
    
    def execute_query(self, query: str, parameters: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """
        Execute SQL query with optional parameters.

        Args:
            query: SQL query string. Use :param_name for parameters.
                   Example: "SELECT * FROM table WHERE id = :id"
            parameters: Dictionary of parameter values.
                       Example: {"id": 123}

        Returns:
            List of dictionaries with column names as keys

        Example:
            >>> connector.execute_query(
            ...     "SELECT * FROM system.access.table_lineage WHERE source_table_full_name = :table_name",
            ...     {"table_name": "catalog.schema.table"}
            ... )

        Note:
            Always use parameterized queries for user input to prevent SQL injection.
        """
        with self.get_connection() as connection:
            with connection.cursor() as cursor:
                logger.info("Executing query", query_preview=query[:100] + "..." if len(query) > 100 else query)

                # Validate parameters if provided
                if parameters:
                    logger.debug(f"Executing query with parameters: {list(parameters.keys())}")
                    # Ensure all placeholders in query have corresponding parameters
                    import re
                    placeholders = set(re.findall(r':(\w+)', query))
                    missing = placeholders - set(parameters.keys())
                    if missing:
                        raise ValueError(f"Missing parameters: {missing}")

                # Security check: warn if query contains string formatting characters
                if '{' in query or '%s' in query or '%d' in query:
                    logger.warning(
                        "Query contains string formatting characters. "
                        "Use parameterized queries with :param_name instead. "
                        f"Query preview: {query[:100]}"
                    )

                if parameters:
                    cursor.execute(query, parameters)
                else:
                    cursor.execute(query)
                
                # Get column names
                columns = [desc[0] for desc in cursor.description] if cursor.description else []
                
                # Fetch all results
                rows = cursor.fetchall()
                
                # Convert to list of dicts with serializable values
                results = []
                for row in rows:
                    # Convert each value to serializable format
                    converted_row = [self._convert_to_serializable(value) for value in row]
                    results.append(dict(zip(columns, converted_row)))
                
                logger.info("Query executed successfully", row_count=len(results))
                return results
    
    def get_tables(self, catalog: Optional[str] = None, schema: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get list of tables from Unity Catalog"""
        where_clauses = ["true"]
        parameters = {}

        if catalog:
            where_clauses.append("table_catalog = :catalog")
            parameters["catalog"] = catalog
        if schema:
            where_clauses.append("table_schema = :schema")
            parameters["schema"] = schema

        where_clause = " and ".join(where_clauses)
        query = f"SELECT * FROM system.information_schema.tables WHERE {where_clause}"

        return self.execute_query(query, parameters if parameters else None)
    
    def get_columns(self, catalog: str, schema: str, table: str) -> List[Dict[str, Any]]:
        """Get columns for a specific table"""
        query = """
        SELECT
            column_name,
            data_type,
            is_nullable,
            column_default,
            comment
        FROM system.information_schema.columns
        WHERE
            true
            and table_catalog = :catalog
            and table_schema = :schema
            and table_name = :table
        ORDER BY ordinal_position
        """

        parameters = {
            "catalog": catalog,
            "schema": schema,
            "table": table
        }

        return self.execute_query(query, parameters)
    
    def test_connection(self) -> bool:
        """Test the Databricks connection"""
        try:
            result = self.execute_query("SELECT 1 as test")
            return len(result) > 0 and result[0]["test"] == 1
        except Exception as e:
            logger.error("Connection test failed", error=str(e))
            return False


# Singleton instance
_connector: Optional[DatabricksConnector] = None


def get_databricks_connector() -> DatabricksConnector:
    """Get or create the Databricks connector instance"""
    global _connector
    if _connector is None:
        _connector = DatabricksConnector()
    return _connector
