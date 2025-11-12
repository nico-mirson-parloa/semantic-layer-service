#!/usr/bin/env python3
"""
SQL API Demo - Connecting to Semantic Layer via PostgreSQL Protocol

This script demonstrates how to connect to the Semantic Layer Service
using standard PostgreSQL libraries and execute SQL queries against
semantic models.
"""

import psycopg2
import pandas as pd
from tabulate import tabulate
import sys

def connect_to_semantic_layer():
    """Establish connection to the Semantic Layer SQL API."""
    try:
        conn = psycopg2.connect(
            host="localhost",
            port=5433,
            database="semantic_layer",
            user="demo_user"  # Any username works with trust auth
        )
        print("✅ Connected to Semantic Layer SQL API")
        return conn
    except Exception as e:
        print(f"❌ Connection failed: {e}")
        sys.exit(1)


def list_available_models(conn):
    """List all available semantic models (schemas)."""
    cursor = conn.cursor()
    
    # Query information schema
    cursor.execute("""
        SELECT schema_name 
        FROM information_schema.schemata 
        WHERE schema_name LIKE 'sem_%'
        ORDER BY schema_name
    """)
    
    schemas = cursor.fetchall()
    
    print("\n📊 Available Semantic Models:")
    print("-" * 40)
    for schema in schemas:
        model_name = schema[0].replace('sem_', '')
        print(f"  • {model_name} (schema: {schema[0]})")
    
    cursor.close()
    return [s[0] for s in schemas]


def explore_model_structure(conn, schema_name):
    """Explore the structure of a semantic model."""
    cursor = conn.cursor()
    
    print(f"\n🔍 Exploring Model: {schema_name}")
    print("=" * 60)
    
    # List tables in schema
    cursor.execute("""
        SELECT table_name, table_type
        FROM information_schema.tables
        WHERE table_schema = %s
        ORDER BY table_name
    """, (schema_name,))
    
    tables = cursor.fetchall()
    
    print("\n📋 Tables:")
    for table_name, table_type in tables:
        print(f"  • {table_name} ({table_type})")
        
        # Get column details
        cursor.execute("""
            SELECT column_name, data_type, is_nullable
            FROM information_schema.columns
            WHERE table_schema = %s AND table_name = %s
            ORDER BY ordinal_position
        """, (schema_name, table_name))
        
        columns = cursor.fetchall()
        
        if columns:
            print(f"\n    Columns in {table_name}:")
            for col_name, data_type, nullable in columns:
                null_indicator = "NULL" if nullable == 'YES' else "NOT NULL"
                print(f"      - {col_name}: {data_type} {null_indicator}")
    
    cursor.close()


def execute_sample_queries(conn, schema_name):
    """Execute sample SQL queries against semantic models."""
    cursor = conn.cursor()
    
    print(f"\n🚀 Sample Queries for {schema_name}")
    print("=" * 60)
    
    # Query 1: Basic SELECT with LIMIT
    print("\n1️⃣ Basic SELECT (first 5 rows):")
    query1 = f"SELECT * FROM {schema_name}.fact LIMIT 5"
    print(f"   Query: {query1}")
    
    try:
        cursor.execute(query1)
        results = cursor.fetchall()
        columns = [desc[0] for desc in cursor.description]
        
        df = pd.DataFrame(results, columns=columns)
        print("\n" + tabulate(df, headers='keys', tablefmt='grid', showindex=False))
    except Exception as e:
        print(f"   Error: {e}")
    
    # Query 2: Aggregation example
    print("\n2️⃣ Aggregation Query:")
    
    # First, check what columns are available
    cursor.execute(f"""
        SELECT column_name 
        FROM information_schema.columns 
        WHERE table_schema = '{schema_name}' 
        AND table_name = 'fact'
        AND data_type IN ('integer', 'bigint', 'numeric', 'real', 'double precision')
        LIMIT 1
    """)
    
    numeric_col = cursor.fetchone()
    
    if numeric_col:
        metric_col = numeric_col[0]
        
        # Find a dimension column
        cursor.execute(f"""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_schema = '{schema_name}' 
            AND table_name = 'fact'
            AND data_type IN ('text', 'varchar', 'character varying')
            LIMIT 1
        """)
        
        dim_col = cursor.fetchone()
        
        if dim_col:
            dimension_col = dim_col[0]
            
            query2 = f"""
                SELECT 
                    {dimension_col},
                    COUNT(*) as count,
                    SUM({metric_col}) as total
                FROM {schema_name}.fact
                GROUP BY {dimension_col}
                ORDER BY total DESC
                LIMIT 5
            """
            print(f"   Query: {query2}")
            
            try:
                cursor.execute(query2)
                results = cursor.fetchall()
                columns = [desc[0] for desc in cursor.description]
                
                df = pd.DataFrame(results, columns=columns)
                print("\n" + tabulate(df, headers='keys', tablefmt='grid', showindex=False))
            except Exception as e:
                print(f"   Error: {e}")
    
    cursor.close()


def demonstrate_bi_tool_query(conn, schema_name):
    """Demonstrate a typical BI tool query pattern."""
    cursor = conn.cursor()
    
    print(f"\n📈 BI Tool Query Pattern")
    print("=" * 60)
    
    # Simulate a query that a BI tool might generate
    bi_query = f"""
        SELECT 
            column_name,
            data_type,
            is_nullable,
            column_default
        FROM information_schema.columns
        WHERE table_schema = '{schema_name}'
        AND table_name = 'fact'
        ORDER BY ordinal_position
    """
    
    print(f"Query (metadata discovery):\n{bi_query}")
    
    try:
        cursor.execute(bi_query)
        results = cursor.fetchall()
        
        print("\n📊 Column Metadata:")
        print("-" * 80)
        print(f"{'Column Name':<30} {'Data Type':<20} {'Nullable':<10} {'Default':<20}")
        print("-" * 80)
        
        for row in results:
            col_name, data_type, nullable, default = row
            default_str = str(default) if default else 'None'
            print(f"{col_name:<30} {data_type:<20} {nullable:<10} {default_str:<20}")
            
    except Exception as e:
        print(f"Error: {e}")
    
    cursor.close()


def main():
    """Main demo function."""
    print("🚀 Semantic Layer SQL API Demo")
    print("=" * 60)
    
    # Connect to semantic layer
    conn = connect_to_semantic_layer()
    
    try:
        # List available models
        schemas = list_available_models(conn)
        
        if not schemas:
            print("\n⚠️  No semantic models found. Please create some models first.")
            return
        
        # Use the first available schema for demo
        demo_schema = schemas[0]
        
        # Explore model structure
        explore_model_structure(conn, demo_schema)
        
        # Execute sample queries
        execute_sample_queries(conn, demo_schema)
        
        # Demonstrate BI tool pattern
        demonstrate_bi_tool_query(conn, demo_schema)
        
        print("\n✅ Demo completed successfully!")
        
    except Exception as e:
        print(f"\n❌ Error during demo: {e}")
        
    finally:
        conn.close()
        print("\n👋 Connection closed")


if __name__ == "__main__":
    # Check if SQL server is running
    print("ℹ️  Make sure the SQL server is running:")
    print("   cd backend && python start_sql_server.py")
    print()
    
    try:
        import psycopg2
        import pandas
        import tabulate
    except ImportError as e:
        print("❌ Missing dependencies. Please install:")
        print("   pip install psycopg2-binary pandas tabulate")
        sys.exit(1)
    
    main()




