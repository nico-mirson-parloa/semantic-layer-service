"""
SQL formatting utilities for better readability
"""
import re
from typing import Optional


def format_sql(sql: str) -> str:
    """
    Format SQL for better readability by adding line breaks
    
    Args:
        sql: Raw SQL string
        
    Returns:
        Formatted SQL string with proper line breaks
    """
    if not sql:
        return sql
    
    # Keywords that should start on a new line
    keywords = [
        'SELECT', 'FROM', 'WHERE', 'GROUP BY', 'HAVING', 
        'ORDER BY', 'LIMIT', 'OFFSET', 'UNION', 'UNION ALL',
        'JOIN', 'LEFT JOIN', 'RIGHT JOIN', 'INNER JOIN', 'OUTER JOIN',
        'ON', 'AND', 'OR', 'WITH', 'AS'
    ]
    
    # First, normalize spaces
    sql = ' '.join(sql.split())
    
    # Add line breaks before major keywords
    for keyword in keywords:
        # Use regex to match whole words only
        pattern = rf'\b{keyword}\b'
        
        # Special handling for SELECT (don't add newline before first SELECT)
        if keyword == 'SELECT' and sql.strip().upper().startswith('SELECT'):
            continue
            
        # Add newline before keyword if it's not at the start
        sql = re.sub(pattern, f'\n{keyword}', sql, flags=re.IGNORECASE)
    
    # Clean up multiple newlines
    sql = re.sub(r'\n\s*\n', '\n', sql)
    
    # Ensure proper indentation for readability
    lines = sql.strip().split('\n')
    formatted_lines = []
    indent_level = 0
    
    for line in lines:
        line = line.strip()
        if not line:
            continue
            
        # Decrease indent for closing parentheses
        if line.startswith(')'):
            indent_level = max(0, indent_level - 1)
        
        # Add indentation
        formatted_lines.append('  ' * indent_level + line)
        
        # Increase indent for subqueries
        if '(' in line and not ')' in line:
            indent_level += 1
        elif ')' in line and not '(' in line:
            indent_level = max(0, indent_level - 1)
    
    return '\n'.join(formatted_lines)


def extract_table_info(sql: str) -> dict:
    """
    Extract table information from SQL query
    
    Args:
        sql: SQL query string
        
    Returns:
        Dictionary with extracted table information
    """
    info = {
        'tables': [],
        'main_table': None,
        'has_joins': False,
        'has_aggregation': False
    }
    
    # Extract main table from FROM clause
    # Match backtick-quoted or unquoted table names
    from_pattern = r'FROM\s+(?:`([^`]+)`|"([^"]+)"|(\S+))'
    from_match = re.search(from_pattern, sql, re.IGNORECASE)
    if from_match:
        # Get the first non-None group
        info['main_table'] = from_match.group(1) or from_match.group(2) or from_match.group(3)
        info['tables'].append(info['main_table'])
    
    # Check for JOINs
    join_pattern = r'(?:LEFT|RIGHT|INNER|OUTER|CROSS|FULL)?\s*JOIN\s+(?:`([^`]+)`|"([^"]+)"|(\S+))'
    join_matches = re.finditer(join_pattern, sql, re.IGNORECASE)
    for match in join_matches:
        info['has_joins'] = True
        table_name = match.group(1) or match.group(2) or match.group(3)
        if table_name:
            info['tables'].append(table_name)
    
    # Check for aggregation functions
    agg_functions = ['COUNT', 'SUM', 'AVG', 'MAX', 'MIN', 'GROUP_CONCAT']
    for func in agg_functions:
        if re.search(rf'\b{func}\s*\(', sql, re.IGNORECASE):
            info['has_aggregation'] = True
            break
    
    # Remove duplicates from tables
    info['tables'] = list(set(info['tables']))
    
    return info


def add_sql_comment(sql: str, comment: str) -> str:
    """
    Add a comment header to SQL query
    
    Args:
        sql: SQL query string
        comment: Comment to add
        
    Returns:
        SQL with comment header
    """
    comment_lines = comment.strip().split('\n')
    formatted_comment = '\n'.join(f'-- {line}' for line in comment_lines)
    
    return f"{formatted_comment}\n\n{sql}"
