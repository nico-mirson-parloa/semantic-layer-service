"""
PostgreSQL-compatible SQL server for semantic layer access.

This server implements the PostgreSQL wire protocol, allowing standard SQL clients
and BI tools to connect and query semantic models as if they were database tables.
"""

import asyncio
import struct
import hashlib
import logging
from typing import Dict, Optional, Any, List, Tuple
from datetime import datetime

import structlog
from fastapi import HTTPException

from app.core.config import settings
from .protocol import PostgreSQLProtocol, MessageType, AuthenticationMethod
from .virtual_schema import VirtualSchemaManager
from .query_translator import SQLToSemanticTranslator
from app.services.semantic_parser import SemanticParser
from app.integrations.databricks import get_databricks_connector

logger = structlog.get_logger()


class SQLServer:
    """PostgreSQL-compatible SQL server for semantic layer."""
    
    def __init__(
        self,
        host: str = "0.0.0.0",
        port: int = 5433,  # Default to 5433 to avoid conflicts with local PostgreSQL
        database: str = "semantic_layer",
        max_connections: int = 100
    ):
        self.host = host
        self.port = port
        self.database = database
        self.max_connections = max_connections
        
        # Initialize components
        self.protocol = PostgreSQLProtocol()
        self.schema_manager = VirtualSchemaManager()
        self.query_translator = SQLToSemanticTranslator()
        self.semantic_parser = SemanticParser()
        
        # Connection tracking
        self.connections: Dict[str, 'ClientConnection'] = {}
        self.server: Optional[asyncio.Server] = None
        
        logger.info(
            "SQL Server initialized",
            host=host,
            port=port,
            database=database,
            max_connections=max_connections
        )
    
    async def start(self):
        """Start the SQL server."""
        try:
            self.server = await asyncio.start_server(
                self.handle_client,
                self.host,
                self.port
            )
            
            logger.info(
                f"SQL Server listening on {self.host}:{self.port}",
                semantic_models=len(self.schema_manager.get_all_models())
            )
            
            async with self.server:
                await self.server.serve_forever()
                
        except Exception as e:
            logger.error(f"Failed to start SQL server: {e}")
            raise
    
    async def stop(self):
        """Stop the SQL server gracefully."""
        if self.server:
            self.server.close()
            await self.server.wait_closed()
            
            # Close all client connections
            for conn_id, connection in self.connections.items():
                await connection.close()
            
            logger.info("SQL Server stopped")
    
    async def handle_client(self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter):
        """Handle a new client connection."""
        client_addr = writer.get_extra_info('peername')
        conn_id = f"{client_addr[0]}:{client_addr[1]}_{datetime.utcnow().timestamp()}"
        
        logger.info(f"New SQL connection from {client_addr}")
        
        # Check connection limit
        if len(self.connections) >= self.max_connections:
            logger.warning(f"Connection limit reached, rejecting {client_addr}")
            writer.close()
            await writer.wait_closed()
            return
        
        # Create client connection handler
        connection = ClientConnection(
            conn_id=conn_id,
            reader=reader,
            writer=writer,
            server=self
        )
        
        self.connections[conn_id] = connection
        
        try:
            await connection.handle()
        except Exception as e:
            logger.error(f"Error handling client {conn_id}: {e}")
        finally:
            # Clean up connection
            if conn_id in self.connections:
                del self.connections[conn_id]
            writer.close()
            await writer.wait_closed()


class ClientConnection:
    """Handles a single client connection."""
    
    def __init__(
        self,
        conn_id: str,
        reader: asyncio.StreamReader,
        writer: asyncio.StreamWriter,
        server: SQLServer
    ):
        self.conn_id = conn_id
        self.reader = reader
        self.writer = writer
        self.server = server
        self.protocol = server.protocol
        
        # Connection state
        self.authenticated = False
        self.username: Optional[str] = None
        self.database: Optional[str] = None
        self.transaction_status = 'I'  # Idle
        
        # Query state
        self.current_query: Optional[str] = None
        self.prepared_statements: Dict[str, Any] = {}
    
    async def handle(self):
        """Main connection handling loop."""
        try:
            # Wait for startup message
            await self.handle_startup()
            
            # Main command loop
            while True:
                # Read message type
                msg_type = await self.reader.read(1)
                if not msg_type:
                    break
                
                # Read message length
                length_bytes = await self.reader.read(4)
                if len(length_bytes) < 4:
                    break
                
                length = struct.unpack('!I', length_bytes)[0] - 4
                
                # Read message body
                if length > 0:
                    body = await self.reader.read(length)
                    if len(body) < length:
                        break
                else:
                    body = b''
                
                # Handle message
                await self.handle_message(msg_type[0], body)
                
        except asyncio.CancelledError:
            raise
        except Exception as e:
            logger.error(f"Connection error for {self.conn_id}: {e}")
            await self.send_error_response(str(e))
    
    async def handle_startup(self):
        """Handle connection startup and authentication."""
        # Read startup message length
        length_bytes = await self.reader.read(4)
        length = struct.unpack('!I', length_bytes)[0] - 4
        
        # Read startup message
        startup_data = await self.reader.read(length)
        
        # Parse startup parameters
        params = self.protocol.parse_startup_message(startup_data)
        self.username = params.get('user', 'anonymous')
        self.database = params.get('database', self.server.database)
        
        logger.info(
            f"Client {self.conn_id} startup",
            username=self.username,
            database=self.database,
            application=params.get('application_name', 'unknown')
        )
        
        # Send authentication request (we'll use trust auth for now)
        await self.send_authentication_ok()
        
        # Send backend key data
        await self.send_backend_key_data()
        
        # Send parameter status messages
        await self.send_parameter_status('server_version', '14.0 (Semantic Layer)')
        await self.send_parameter_status('server_encoding', 'UTF8')
        await self.send_parameter_status('client_encoding', 'UTF8')
        await self.send_parameter_status('DateStyle', 'ISO, MDY')
        await self.send_parameter_status('TimeZone', 'UTC')
        
        # Send ready for query
        await self.send_ready_for_query()
        
        self.authenticated = True
    
    async def handle_message(self, msg_type: int, body: bytes):
        """Route message to appropriate handler."""
        if msg_type == ord('Q'):  # Simple query
            await self.handle_simple_query(body)
        elif msg_type == ord('P'):  # Parse (prepared statement)
            await self.handle_parse(body)
        elif msg_type == ord('B'):  # Bind
            await self.handle_bind(body)
        elif msg_type == ord('E'):  # Execute
            await self.handle_execute(body)
        elif msg_type == ord('D'):  # Describe
            await self.handle_describe(body)
        elif msg_type == ord('S'):  # Sync
            await self.handle_sync()
        elif msg_type == ord('X'):  # Terminate
            logger.info(f"Client {self.conn_id} terminated connection")
            raise asyncio.CancelledError()
        else:
            logger.warning(f"Unknown message type: {chr(msg_type)}")
    
    async def handle_simple_query(self, body: bytes):
        """Handle simple query protocol."""
        # Extract query string (null-terminated)
        query = body.rstrip(b'\x00').decode('utf-8')
        
        logger.info(f"SQL query from {self.conn_id}: {query[:100]}...")
        
        try:
            # Check for special queries
            if query.upper().startswith('SELECT VERSION()'):
                await self.send_query_response(
                    columns=[('version', 'text')],
                    rows=[['PostgreSQL 14.0 (Semantic Layer)']]
                )
            elif query.upper().startswith('SHOW'):
                await self.handle_show_command(query)
            elif query.upper() == 'SELECT 1':
                # Common connection test query
                await self.send_query_response(
                    columns=[('?column?', 'integer')],
                    rows=[[1]]
                )
            else:
                # Translate SQL to semantic query
                semantic_query = await self.server.query_translator.translate(query)
                
                # Execute semantic query
                results = await self.execute_semantic_query(semantic_query)
                
                # Send results
                await self.send_query_response(
                    columns=results['columns'],
                    rows=results['rows']
                )
            
            # Send command complete
            await self.send_command_complete(f"SELECT {len(results.get('rows', []))}")
            
        except Exception as e:
            logger.error(f"Query execution error: {e}")
            await self.send_error_response(str(e))
        
        finally:
            await self.send_ready_for_query()
    
    async def handle_show_command(self, query: str):
        """Handle SHOW commands for PostgreSQL compatibility."""
        query_upper = query.upper()
        
        if 'DATABASES' in query_upper or 'SCHEMAS' in query_upper:
            # Show available schemas (semantic models)
            models = self.server.schema_manager.get_all_models()
            rows = [[model] for model in models]
            await self.send_query_response(
                columns=[('schema_name', 'text')],
                rows=rows
            )
        elif 'TABLES' in query_upper:
            # Show tables in current schema
            if self.database:
                tables = self.server.schema_manager.get_tables(self.database)
                rows = [[table['name'], table['type']] for table in tables]
                await self.send_query_response(
                    columns=[('table_name', 'text'), ('table_type', 'text')],
                    rows=rows
                )
            else:
                await self.send_query_response(columns=[('table_name', 'text')], rows=[])
        else:
            # Generic SHOW command response
            await self.send_query_response(columns=[('result', 'text')], rows=[['OK']])
    
    async def execute_semantic_query(self, semantic_query: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a semantic query and return results."""
        try:
            # Get the semantic model
            model_name = semantic_query.get('model')
            if not model_name:
                raise ValueError("No semantic model specified in query")
            
            # Execute through semantic parser
            results = await self.server.semantic_parser.execute_query(semantic_query)
            
            return {
                'columns': results.get('columns', []),
                'rows': results.get('data', [])
            }
            
        except Exception as e:
            logger.error(f"Semantic query execution failed: {e}")
            raise
    
    # Protocol helper methods
    async def send_authentication_ok(self):
        """Send authentication OK response."""
        msg = struct.pack('!cI', b'R', 8)  # Type R, length 8
        msg += struct.pack('!I', 0)  # Auth OK
        self.writer.write(msg)
        await self.writer.drain()
    
    async def send_backend_key_data(self):
        """Send backend key data for cancellation."""
        msg = struct.pack('!cI', b'K', 12)  # Type K, length 12
        msg += struct.pack('!II', 12345, 67890)  # Process ID and secret key
        self.writer.write(msg)
        await self.writer.drain()
    
    async def send_parameter_status(self, name: str, value: str):
        """Send parameter status message."""
        body = name.encode('utf-8') + b'\x00' + value.encode('utf-8') + b'\x00'
        msg = struct.pack('!cI', b'S', 4 + len(body)) + body
        self.writer.write(msg)
        await self.writer.drain()
    
    async def send_ready_for_query(self):
        """Send ready for query message."""
        msg = struct.pack('!cI', b'Z', 5)  # Type Z, length 5
        msg += self.transaction_status.encode('ascii')  # Transaction status
        self.writer.write(msg)
        await self.writer.drain()
    
    async def send_query_response(self, columns: List[Tuple[str, str]], rows: List[List[Any]]):
        """Send query results."""
        # Send RowDescription
        body = struct.pack('!H', len(columns))  # Number of fields
        
        for col_name, col_type in columns:
            # Field name
            body += col_name.encode('utf-8') + b'\x00'
            # Table OID (0 for no table)
            body += struct.pack('!I', 0)
            # Column number (0)
            body += struct.pack('!H', 0)
            # Type OID (25 for text, 23 for integer, etc.)
            type_oid = self.protocol.get_type_oid(col_type)
            body += struct.pack('!I', type_oid)
            # Type size (-1 for variable)
            body += struct.pack('!h', -1)
            # Type modifier (-1)
            body += struct.pack('!I', 4294967295)  # -1 as unsigned
            # Format code (0 for text)
            body += struct.pack('!H', 0)
        
        msg = struct.pack('!cI', b'T', 4 + len(body)) + body
        self.writer.write(msg)
        
        # Send DataRow messages
        for row in rows:
            row_body = struct.pack('!H', len(row))  # Number of values
            
            for value in row:
                if value is None:
                    row_body += struct.pack('!i', -1)  # NULL
                else:
                    value_bytes = str(value).encode('utf-8')
                    row_body += struct.pack('!I', len(value_bytes))
                    row_body += value_bytes
            
            msg = struct.pack('!cI', b'D', 4 + len(row_body)) + row_body
            self.writer.write(msg)
        
        await self.writer.drain()
    
    async def send_command_complete(self, tag: str):
        """Send command complete message."""
        body = tag.encode('utf-8') + b'\x00'
        msg = struct.pack('!cI', b'C', 4 + len(body)) + body
        self.writer.write(msg)
        await self.writer.drain()
    
    async def send_error_response(self, message: str):
        """Send error response."""
        body = b'S' + b'ERROR\x00'  # Severity
        body += b'C' + b'42P01\x00'  # Error code
        body += b'M' + message.encode('utf-8') + b'\x00'  # Message
        body += b'\x00'  # Terminator
        
        msg = struct.pack('!cI', b'E', 4 + len(body)) + body
        self.writer.write(msg)
        await self.writer.drain()
    
    async def close(self):
        """Close the client connection."""
        try:
            self.writer.close()
            await self.writer.wait_closed()
        except Exception as e:
            logger.error(f"Error closing connection {self.conn_id}: {e}")


# Convenience function to start the server
async def start_sql_server(host: str = "0.0.0.0", port: int = 5433):
    """Start the SQL server."""
    server = SQLServer(host=host, port=port)
    await server.start()


if __name__ == "__main__":
    # Run the server directly for testing
    asyncio.run(start_sql_server())


