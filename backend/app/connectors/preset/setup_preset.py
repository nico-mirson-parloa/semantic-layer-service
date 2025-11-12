#!/usr/bin/env python3
"""
Preset setup script for Semantic Layer integration.

This script helps configure Preset to connect to the Semantic Layer SQL API
and creates initial datasets and dashboards.
"""

import json
import sys
from pathlib import Path
from typing import Optional

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from app.connectors.preset import PresetConnector, PresetDashboardBuilder, PresetMetricSync
from app.sql_api.virtual_schema import VirtualSchemaManager
from app.core.logging import setup_logging
import structlog

# Setup logging
setup_logging()
logger = structlog.get_logger()


def main():
    """Main setup function."""
    print("🎯 Preset Integration Setup for Semantic Layer")
    print("=" * 60)
    
    # Initialize components
    schema_manager = VirtualSchemaManager()
    connector = PresetConnector(schema_manager)
    dashboard_builder = PresetDashboardBuilder(schema_manager)
    metric_sync = PresetMetricSync(schema_manager)
    
    # Step 1: Validate SQL API connection
    print("\n1️⃣ Validating SQL API Connection...")
    validation = connector.validate_connection()
    
    if not validation['valid']:
        print(f"❌ Connection validation failed: {validation.get('error')}")
        print("\nPlease ensure the SQL API server is running:")
        print("  cd backend && python start_sql_server.py")
        return
    
    print(f"✅ SQL API accessible at {validation['host']}:{validation['port']}")
    print(f"📊 Available schemas: {', '.join(validation['available_schemas'])}")
    
    # Step 2: Generate connection configuration
    print("\n2️⃣ Generating Preset Connection Configuration...")
    
    datasource = connector.generate_connection_config(
        database_name="Semantic Layer",
        include_schemas=None  # Include all schemas
    )
    
    print("\n📋 Database Configuration for Preset:")
    print("-" * 60)
    print(f"Database Name: {datasource.database_name}")
    print(f"Connection String: {datasource.sqlalchemy_uri}")
    print(f"Schemas: {', '.join(datasource.schema_access)}")
    print("\n💡 To add this database in Preset:")
    print("   1. Go to Data → Databases → + Database")
    print("   2. Select PostgreSQL")
    print("   3. Use the connection details above")
    print("   4. Add this to 'Extra' field:")
    print(json.dumps(datasource.extra, indent=2))
    
    # Step 3: Generate dataset configurations
    print("\n3️⃣ Generating Dataset Configurations...")
    
    datasets_config = []
    for schema in validation['available_schemas']:
        try:
            # Generate explore config for fact table
            explore_config = connector.generate_explore_config(schema, "fact")
            datasets_config.append({
                "schema": schema,
                "config": explore_config
            })
            print(f"✅ Generated config for {schema}.fact")
        except Exception as e:
            print(f"⚠️  Skipped {schema}: {e}")
    
    # Save dataset configurations
    output_dir = Path("preset_configs")
    output_dir.mkdir(exist_ok=True)
    
    with open(output_dir / "datasets.json", "w") as f:
        json.dump(datasets_config, f, indent=2)
    print(f"\n💾 Saved dataset configurations to {output_dir / 'datasets.json'}")
    
    # Step 4: Generate metrics
    print("\n4️⃣ Generating Metrics Configurations...")
    
    for schema in validation['available_schemas']:
        try:
            # Generate metrics YAML
            metrics_yaml = metric_sync.generate_metrics_yaml(schema)
            
            # Save metrics configuration
            metrics_file = output_dir / f"{schema}_metrics.yaml"
            with open(metrics_file, "w") as f:
                f.write(metrics_yaml)
            
            print(f"✅ Generated metrics for {schema}")
            
            # Also generate dataset metrics JSON
            dataset_metrics = metric_sync.generate_dataset_metrics(schema)
            metrics_json_file = output_dir / f"{schema}_dataset_metrics.json"
            with open(metrics_json_file, "w") as f:
                json.dump(dataset_metrics, f, indent=2)
                
        except Exception as e:
            print(f"⚠️  Skipped metrics for {schema}: {e}")
    
    # Step 5: Generate dashboard templates
    print("\n5️⃣ Generating Dashboard Templates...")
    
    for schema in validation['available_schemas']:
        try:
            # Generate dashboard
            dashboard_config = dashboard_builder.generate_dashboard_template(
                schema_name=schema,
                dashboard_name=f"{schema.replace('sem_', '').replace('_', ' ').title()} Analytics"
            )
            
            # Export dashboard
            dashboard_json = dashboard_builder.export_dashboard_json(dashboard_config)
            dashboard_file = output_dir / f"{schema}_dashboard.json"
            
            with open(dashboard_file, "w") as f:
                f.write(dashboard_json)
            
            print(f"✅ Generated dashboard for {schema}")
            
        except Exception as e:
            print(f"⚠️  Skipped dashboard for {schema}: {e}")
    
    # Step 6: Generate setup instructions
    print("\n6️⃣ Generating Setup Instructions...")
    
    instructions = f"""
# Preset Setup Instructions

## 1. Database Connection

1. In Preset, go to **Data → Databases**
2. Click **+ Database**
3. Configure with these settings:

```
Host: {validation['host']}
Port: {validation['port']}
Database: semantic_layer
Username: preset_user
```

## 2. Import Datasets

For each semantic model, create a dataset:

1. Go to **Data → Datasets**
2. Click **+ Dataset**
3. Select the Semantic Layer database
4. Choose schema and table
5. Configure metrics from the generated files

## 3. Import Dashboards

1. Go to **Dashboards**
2. Use the import feature
3. Select the generated dashboard JSON files

## 4. Configure Caching

Recommended cache settings:
- Dataset cache: 300 seconds
- Chart cache: 300 seconds
- Dashboard filters cache: 86400 seconds

## Generated Files

- `datasets.json` - Dataset configurations
- `*_metrics.yaml` - Metrics for each model
- `*_dashboard.json` - Dashboard templates

## Connection Test Query

```sql
SELECT 'Connected to Semantic Layer' as status;
```
"""
    
    instructions_file = output_dir / "SETUP_INSTRUCTIONS.md"
    with open(instructions_file, "w") as f:
        f.write(instructions)
    
    print(f"\n📄 Setup instructions saved to {instructions_file}")
    
    # Step 7: Generate recommended settings
    print("\n7️⃣ Recommended Preset Settings:")
    settings = connector.get_recommended_settings()
    
    print("\n⚙️  Database Settings:")
    for key, value in settings['database_settings'].items():
        print(f"   • {key}: {value}")
    
    print("\n⚡ Performance Tips:")
    for tip in settings['performance_tips']:
        print(f"   • {tip}")
    
    # Summary
    print("\n" + "=" * 60)
    print("✅ Preset Setup Complete!")
    print(f"\n📁 Configuration files saved to: {output_dir.absolute()}")
    print("\n🚀 Next Steps:")
    print("   1. Add the database connection in Preset")
    print("   2. Import the generated datasets")
    print("   3. Import the dashboard templates")
    print("   4. Customize as needed")
    print("\n📚 See PRESET_INTEGRATION_GUIDE.md for detailed instructions")


if __name__ == "__main__":
    main()




