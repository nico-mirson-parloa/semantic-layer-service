#!/usr/bin/env python3
"""
Preset Integration Demo

This script demonstrates how to use the Preset connector
to set up Preset/Superset integration with the Semantic Layer.
"""

import sys
from pathlib import Path

# Add parent to path
sys.path.insert(0, str(Path(__file__).parent.parent / 'backend'))

from app.connectors.preset import PresetConnector, PresetDashboardBuilder
from app.sql_api.virtual_schema import VirtualSchemaManager


def main():
    """Run Preset integration demo."""
    print("🎯 Preset Integration Demo")
    print("=" * 60)
    
    # Initialize components
    schema_manager = VirtualSchemaManager()
    connector = PresetConnector(schema_manager)
    
    # 1. Validate connection
    print("\n1️⃣ Checking SQL API Connection...")
    validation = connector.validate_connection()
    
    if validation['valid']:
        print(f"✅ SQL API is running on {validation['host']}:{validation['port']}")
        print(f"📊 Available models: {', '.join([s.replace('sem_', '') for s in validation['available_schemas']])}")
    else:
        print(f"❌ SQL API not available: {validation['error']}")
        print("\nPlease start the SQL server:")
        print("  cd backend && python start_sql_server.py")
        return
    
    # 2. Show connection configuration
    print("\n2️⃣ Preset Connection Configuration:")
    print("-" * 60)
    
    config = connector.generate_connection_config()
    print(f"Database Name: {config.database_name}")
    print(f"Connection URL: {config.sqlalchemy_uri}")
    print(f"\nTo connect from Preset:")
    print("1. Go to Data → Databases → + Database")
    print("2. Select PostgreSQL")
    print("3. Enter connection details:")
    print(f"   - Host: {validation['host']}")
    print(f"   - Port: {validation['port']}")
    print("   - Database: semantic_layer")
    print("   - Username: preset_user")
    
    # 3. Show available datasets
    print("\n3️⃣ Available Datasets:")
    print("-" * 60)
    
    for schema in validation['available_schemas']:
        model_name = schema.replace('sem_', '')
        print(f"\n📊 Model: {model_name}")
        
        # Show fact table
        tables = schema_manager.get_schema_tables(schema)
        for table in tables:
            print(f"   - {table['name']} ({table['type']}) - {table['columns']} columns")
    
    # 4. Generate sample dashboard
    if validation['available_schemas']:
        print("\n4️⃣ Sample Dashboard Generation:")
        print("-" * 60)
        
        # Use first available schema
        sample_schema = validation['available_schemas'][0]
        model_name = sample_schema.replace('sem_', '')
        
        builder = PresetDashboardBuilder(schema_manager)
        
        try:
            dashboard = builder.generate_dashboard_template(
                schema_name=sample_schema,
                dashboard_name=f"{model_name.replace('_', ' ').title()} Dashboard"
            )
            
            print(f"\n✅ Generated dashboard: {dashboard['dashboard_title']}")
            print(f"   - Charts: {len(dashboard['slices'])}")
            print(f"   - Description: {dashboard['description']}")
            
            # Show chart types
            chart_types = {}
            for chart in dashboard['slices']:
                viz_type = chart['viz_type']
                chart_types[viz_type] = chart_types.get(viz_type, 0) + 1
            
            print("\n   Chart Types:")
            for viz_type, count in chart_types.items():
                print(f"     • {viz_type}: {count}")
                
        except Exception as e:
            print(f"⚠️  Could not generate dashboard: {e}")
    
    # 5. Show SQL examples
    print("\n5️⃣ Sample SQL Queries for Preset:")
    print("-" * 60)
    
    if validation['available_schemas']:
        schema = validation['available_schemas'][0]
        
        print(f"\n-- Test connection")
        print(f"SELECT 'Connected to {schema}' as status;")
        
        print(f"\n-- Explore data")
        print(f"SELECT * FROM {schema}.fact LIMIT 10;")
        
        print(f"\n-- Aggregate metrics")
        print(f"SELECT ")
        print(f"    DATE_TRUNC('month', order_date) as month,")
        print(f"    COUNT(*) as orders,")
        print(f"    SUM(revenue) as total_revenue")
        print(f"FROM {schema}.fact")
        print(f"GROUP BY 1")
        print(f"ORDER BY 1;")
    
    print("\n" + "=" * 60)
    print("✅ Demo Complete!")
    print("\n📚 Next Steps:")
    print("1. Connect Preset using the configuration above")
    print("2. Create datasets from semantic models")
    print("3. Build dashboards using the generated templates")
    print("\nSee docs/PRESET_INTEGRATION_GUIDE.md for detailed instructions")


if __name__ == "__main__":
    main()




