"""
SQL API module for PostgreSQL-compatible interface.

This module provides a PostgreSQL wire protocol server that allows
BI tools and SQL clients to connect to the semantic layer as if it
were a regular PostgreSQL database.
"""

from .server import SQLServer
from .protocol import PostgreSQLProtocol
from .virtual_schema import VirtualSchemaManager
from .query_translator import SQLToSemanticTranslator

__all__ = [
    "SQLServer",
    "PostgreSQLProtocol", 
    "VirtualSchemaManager",
    "SQLToSemanticTranslator"
]


