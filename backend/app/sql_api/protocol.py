"""
PostgreSQL wire protocol implementation.

This module handles the low-level protocol details for PostgreSQL compatibility,
including message formats, authentication, and data type mappings.
"""

import struct
import hashlib
from enum import IntEnum
from typing import Dict, List, Tuple, Any, Optional
import logging

logger = logging.getLogger(__name__)


class MessageType(IntEnum):
    """PostgreSQL message type codes."""
    # Frontend (client to server)
    BIND = ord('B')
    CLOSE = ord('C')
    COPY_DATA = ord('d')
    COPY_DONE = ord('c')
    COPY_FAIL = ord('f')
    DESCRIBE = ord('D')
    EXECUTE = ord('E')
    FLUSH = ord('H')
    FUNCTION_CALL = ord('F')
    PARSE = ord('P')
    PASSWORD_MESSAGE = ord('p')
    QUERY = ord('Q')
    SYNC = ord('S')
    TERMINATE = ord('X')
    
    # Backend (server to client)
    AUTHENTICATION = ord('R')
    BACKEND_KEY_DATA = ord('K')
    BIND_COMPLETE = ord('2')
    CLOSE_COMPLETE = ord('3')
    COMMAND_COMPLETE = ord('C')
    COPY_IN_RESPONSE = ord('G')
    COPY_OUT_RESPONSE = ord('H')
    COPY_BOTH_RESPONSE = ord('W')
    DATA_ROW = ord('D')
    EMPTY_QUERY_RESPONSE = ord('I')
    ERROR_RESPONSE = ord('E')
    FUNCTION_CALL_RESPONSE = ord('V')
    NO_DATA = ord('n')
    NOTICE_RESPONSE = ord('N')
    NOTIFICATION_RESPONSE = ord('A')
    PARAMETER_DESCRIPTION = ord('t')
    PARAMETER_STATUS = ord('S')
    PARSE_COMPLETE = ord('1')
    PORTAL_SUSPENDED = ord('s')
    READY_FOR_QUERY = ord('Z')
    ROW_DESCRIPTION = ord('T')


class AuthenticationMethod(IntEnum):
    """PostgreSQL authentication methods."""
    OK = 0
    KERBEROS_V5 = 2
    CLEAR_TEXT_PASSWORD = 3
    MD5_PASSWORD = 5
    SCM_CREDENTIAL = 6
    GSS = 7
    GSS_CONTINUE = 8
    SSPI = 9
    SASL = 10
    SASL_CONTINUE = 11
    SASL_FINAL = 12


class PostgreSQLProtocol:
    """PostgreSQL wire protocol handler."""
    
    # PostgreSQL type OIDs
    TYPE_OIDS = {
        'bool': 16,
        'bytea': 17,
        'char': 18,
        'int8': 20,
        'int2': 21,
        'int4': 23,
        'text': 25,
        'oid': 26,
        'float4': 700,
        'float8': 701,
        'varchar': 1043,
        'date': 1082,
        'time': 1083,
        'timestamp': 1114,
        'timestamptz': 1184,
        'interval': 1186,
        'numeric': 1700,
        'json': 114,
        'jsonb': 3802,
        'uuid': 2950,
        'array': 2003,
        'unknown': 705,
        
        # Common aliases
        'boolean': 16,
        'integer': 23,
        'bigint': 20,
        'smallint': 21,
        'real': 700,
        'double': 701,
        'decimal': 1700,
        'string': 25,
        'datetime': 1114,
    }
    
    # Error severity levels
    ERROR_SEVERITY = {
        'ERROR': 'ERROR',
        'FATAL': 'FATAL',
        'PANIC': 'PANIC',
        'WARNING': 'WARNING',
        'NOTICE': 'NOTICE',
        'DEBUG': 'DEBUG',
        'INFO': 'INFO',
        'LOG': 'LOG'
    }
    
    # SQLSTATE error codes
    SQLSTATE_CODES = {
        'successful_completion': '00000',
        'feature_not_supported': '0A000',
        'invalid_schema_name': '3F000',
        'undefined_table': '42P01',
        'undefined_column': '42703',
        'syntax_error': '42601',
        'insufficient_privilege': '42501',
        'invalid_text_representation': '22P02',
        'numeric_value_out_of_range': '22003',
        'data_exception': '22000',
        'connection_exception': '08000',
        'connection_does_not_exist': '08003',
        'connection_failure': '08006',
        'protocol_violation': '08P01',
    }
    
    def __init__(self):
        """Initialize protocol handler."""
        self.buffer = bytearray()
    
    def parse_startup_message(self, data: bytes) -> Dict[str, str]:
        """Parse startup message from client."""
        params = {}
        
        # First 4 bytes are protocol version
        protocol_version = struct.unpack('!I', data[:4])[0]
        
        # Rest are null-terminated key-value pairs
        pos = 4
        while pos < len(data) - 1:  # -1 for final null terminator
            # Find key
            key_end = data.find(b'\x00', pos)
            if key_end == -1:
                break
            key = data[pos:key_end].decode('utf-8')
            
            # Find value
            pos = key_end + 1
            value_end = data.find(b'\x00', pos)
            if value_end == -1:
                break
            value = data[pos:value_end].decode('utf-8')
            
            params[key] = value
            pos = value_end + 1
        
        logger.debug(f"Startup parameters: {params}")
        return params
    
    def build_authentication_request(
        self,
        method: AuthenticationMethod,
        salt: Optional[bytes] = None
    ) -> bytes:
        """Build authentication request message."""
        if method == AuthenticationMethod.OK:
            return struct.pack('!cII', b'R', 8, 0)
        elif method == AuthenticationMethod.CLEAR_TEXT_PASSWORD:
            return struct.pack('!cII', b'R', 8, 3)
        elif method == AuthenticationMethod.MD5_PASSWORD:
            if not salt or len(salt) != 4:
                raise ValueError("MD5 authentication requires 4-byte salt")
            return struct.pack('!cII4s', b'R', 12, 5, salt)
        else:
            raise ValueError(f"Unsupported authentication method: {method}")
    
    def build_parameter_status(self, name: str, value: str) -> bytes:
        """Build parameter status message."""
        body = name.encode('utf-8') + b'\x00' + value.encode('utf-8') + b'\x00'
        return struct.pack('!cI', b'S', 4 + len(body)) + body
    
    def build_backend_key_data(self, process_id: int, secret_key: int) -> bytes:
        """Build backend key data message."""
        return struct.pack('!cIII', b'K', 12, process_id, secret_key)
    
    def build_ready_for_query(self, transaction_status: str = 'I') -> bytes:
        """Build ready for query message."""
        return struct.pack('!cIc', b'Z', 5, transaction_status.encode('ascii'))
    
    def build_row_description(self, columns: List[Tuple[str, str]]) -> bytes:
        """Build row description message."""
        body = struct.pack('!H', len(columns))
        
        for col_name, col_type in columns:
            # Column name
            body += col_name.encode('utf-8') + b'\x00'
            # Table OID (0 for no specific table)
            body += struct.pack('!I', 0)
            # Column attribute number (0)
            body += struct.pack('!H', 0)
            # Data type OID
            type_oid = self.get_type_oid(col_type)
            body += struct.pack('!I', type_oid)
            # Data type size (-1 for variable length)
            body += struct.pack('!h', -1)
            # Type modifier (-1)
            body += struct.pack('!i', -1)
            # Format code (0 for text)
            body += struct.pack('!H', 0)
        
        return struct.pack('!cI', b'T', 4 + len(body)) + body
    
    def build_data_row(self, values: List[Any]) -> bytes:
        """Build data row message."""
        body = struct.pack('!H', len(values))
        
        for value in values:
            if value is None:
                # NULL value
                body += struct.pack('!i', -1)
            else:
                # Convert to string and encode
                value_bytes = str(value).encode('utf-8')
                body += struct.pack('!I', len(value_bytes))
                body += value_bytes
        
        return struct.pack('!cI', b'D', 4 + len(body)) + body
    
    def build_command_complete(self, tag: str) -> bytes:
        """Build command complete message."""
        tag_bytes = tag.encode('utf-8') + b'\x00'
        return struct.pack('!cI', b'C', 4 + len(tag_bytes)) + tag_bytes
    
    def build_error_response(
        self,
        severity: str,
        code: str,
        message: str,
        detail: Optional[str] = None,
        hint: Optional[str] = None,
        position: Optional[int] = None,
        internal_position: Optional[int] = None,
        internal_query: Optional[str] = None,
        where: Optional[str] = None,
        schema: Optional[str] = None,
        table: Optional[str] = None,
        column: Optional[str] = None,
        datatype: Optional[str] = None,
        constraint: Optional[str] = None,
        file: Optional[str] = None,
        line: Optional[int] = None,
        routine: Optional[str] = None
    ) -> bytes:
        """Build error response message."""
        body = b''
        
        # Severity
        body += b'S' + severity.encode('utf-8') + b'\x00'
        
        # SQLSTATE code
        body += b'C' + code.encode('utf-8') + b'\x00'
        
        # Message
        body += b'M' + message.encode('utf-8') + b'\x00'
        
        # Optional fields
        if detail:
            body += b'D' + detail.encode('utf-8') + b'\x00'
        if hint:
            body += b'H' + hint.encode('utf-8') + b'\x00'
        if position is not None:
            body += b'P' + str(position).encode('utf-8') + b'\x00'
        if where:
            body += b'W' + where.encode('utf-8') + b'\x00'
        if schema:
            body += b's' + schema.encode('utf-8') + b'\x00'
        if table:
            body += b't' + table.encode('utf-8') + b'\x00'
        if column:
            body += b'c' + column.encode('utf-8') + b'\x00'
        
        # Terminator
        body += b'\x00'
        
        return struct.pack('!cI', b'E', 4 + len(body)) + body
    
    def build_empty_query_response(self) -> bytes:
        """Build empty query response message."""
        return struct.pack('!cI', b'I', 4)
    
    def build_parse_complete(self) -> bytes:
        """Build parse complete message."""
        return struct.pack('!cI', b'1', 4)
    
    def build_bind_complete(self) -> bytes:
        """Build bind complete message."""
        return struct.pack('!cI', b'2', 4)
    
    def build_no_data(self) -> bytes:
        """Build no data message."""
        return struct.pack('!cI', b'n', 4)
    
    def get_type_oid(self, type_name: str) -> int:
        """Get PostgreSQL type OID for a given type name."""
        # Normalize type name
        type_name = type_name.lower().strip()
        
        # Check direct mapping
        if type_name in self.TYPE_OIDS:
            return self.TYPE_OIDS[type_name]
        
        # Check for array types
        if type_name.endswith('[]'):
            base_type = type_name[:-2]
            if base_type in self.TYPE_OIDS:
                # Return generic array OID
                return self.TYPE_OIDS['array']
        
        # Default to text type
        return self.TYPE_OIDS['text']
    
    def parse_query(self, data: bytes) -> str:
        """Parse simple query message."""
        # Query is null-terminated
        if data.endswith(b'\x00'):
            return data[:-1].decode('utf-8')
        return data.decode('utf-8')
    
    def parse_parse_message(self, data: bytes) -> Tuple[str, str, List[int]]:
        """Parse Parse message (prepared statement)."""
        pos = 0
        
        # Statement name (null-terminated)
        name_end = data.find(b'\x00', pos)
        stmt_name = data[pos:name_end].decode('utf-8')
        pos = name_end + 1
        
        # Query string (null-terminated)
        query_end = data.find(b'\x00', pos)
        query = data[pos:query_end].decode('utf-8')
        pos = query_end + 1
        
        # Number of parameter types
        param_count = struct.unpack('!H', data[pos:pos+2])[0]
        pos += 2
        
        # Parameter type OIDs
        param_types = []
        for _ in range(param_count):
            type_oid = struct.unpack('!I', data[pos:pos+4])[0]
            param_types.append(type_oid)
            pos += 4
        
        return stmt_name, query, param_types
    
    def md5_password(self, password: str, user: str, salt: bytes) -> str:
        """Generate MD5 password hash for PostgreSQL authentication."""
        # First MD5: md5(password + username)
        stage1 = hashlib.md5((password + user).encode('utf-8')).hexdigest()
        
        # Second MD5: md5(stage1 + salt)
        stage2 = hashlib.md5((stage1 + salt.decode('latin-1')).encode('utf-8')).hexdigest()
        
        # Prepend 'md5'
        return 'md5' + stage2


