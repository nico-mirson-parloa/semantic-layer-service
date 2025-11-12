#!/usr/bin/env python3
"""Test script to debug SQL autocomplete"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

from app.integrations.databricks import get_databricks_connector

def test_autocomplete():
    try:
        print("Testing SQL autocomplete...")
        connector = get_databricks_connector()
        
        # Test catalog query
        catalog_query = """
            SELECT DISTINCT table_catalog 
            FROM system.information_schema.tables 
            WHERE LOWER(table_catalog) LIKE LOWER('par%')
            ORDER BY table_catalog
            LIMIT 10
        """
        print(f"Executing query: {catalog_query}")
        results = connector.execute_query(catalog_query)
        print(f"Results: {results}")
        
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_autocomplete()
