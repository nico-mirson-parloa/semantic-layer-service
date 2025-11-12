# Preset Connector for Semantic Layer

This module provides native integration between the Semantic Layer Service and Preset (Apache Superset cloud platform).

## Components

### 1. **PresetConnector** (`connector.py`)
- Handles database connection configuration
- Generates Preset-compatible connection strings
- Validates SQL API connectivity
- Provides dataset configuration generation

### 2. **PresetDashboardBuilder** (`dashboard_builder.py`)
- Automatically generates dashboard templates from semantic models
- Creates appropriate chart types based on data characteristics
- Builds dashboard layouts with KPIs, time series, and breakdowns
- Exports dashboard configurations for import

### 3. **PresetMetricSync** (`metric_sync.py`)
- Synchronizes semantic layer metrics with Preset
- Generates metric definitions in Preset format
- Creates calculated fields and custom aggregations
- Handles metric metadata and formatting

## Quick Start

### 1. Run Setup Script

```bash
cd backend/app/connectors/preset
python setup_preset.py
```

This will:
- Validate your SQL API connection
- Generate all necessary configuration files
- Create dashboard templates
- Export metrics definitions

### 2. Connect Preset

In your Preset workspace:

1. Add Database:
   - Type: PostgreSQL
   - Host: Your server IP
   - Port: 5433
   - Database: semantic_layer
   - Username: preset_user

2. Import Generated Configurations:
   - Datasets from `preset_configs/datasets.json`
   - Metrics from `preset_configs/*_metrics.yaml`
   - Dashboards from `preset_configs/*_dashboard.json`

## Configuration Files

### Database Connection
```python
datasource = PresetConnector().generate_connection_config(
    database_name="Semantic Layer",
    include_schemas=["sem_sales_metrics"]
)
```

### Dashboard Generation
```python
dashboard = PresetDashboardBuilder().generate_dashboard_template(
    schema_name="sem_sales_metrics",
    dashboard_name="Sales Analytics"
)
```

### Metric Sync
```python
metrics = PresetMetricSync().generate_dataset_metrics(
    schema_name="sem_sales_metrics"
)
```

## Features

- **Automatic Configuration**: Generates all Preset configurations from semantic models
- **Dashboard Templates**: Creates complete dashboards with appropriate visualizations
- **Metric Management**: Syncs semantic layer metrics as Preset calculated fields
- **Performance Optimized**: Includes caching and query optimization settings
- **Security Ready**: Supports row-level security and access controls

## Directory Structure

```
preset/
├── __init__.py              # Module exports
├── connector.py             # Connection management
├── dashboard_builder.py     # Dashboard generation
├── metric_sync.py          # Metric synchronization
├── setup_preset.py         # Automated setup script
├── preset_config_example.yaml  # Configuration template
└── README.md               # This file
```

## Advanced Usage

### Custom Dashboard Creation

```python
from app.connectors.preset import PresetDashboardBuilder

builder = PresetDashboardBuilder()

# Create custom dashboard with specific charts
dashboard = builder.generate_dashboard_template(
    schema_name="sem_custom_model",
    dashboard_name="Custom Analytics"
)

# Export for Preset import
json_export = builder.export_dashboard_json(dashboard)
```

### Programmatic Metric Creation

```python
from app.connectors.preset import PresetMetricSync

sync = PresetMetricSync()

# Generate metrics for a specific model
metrics_yaml = sync.generate_metrics_yaml("sem_sales_metrics")

# Create dataset-specific metrics
dataset_metrics = sync.generate_dataset_metrics(
    schema_name="sem_sales_metrics",
    table_name="fact"
)
```

## Troubleshooting

### Connection Issues
- Ensure SQL API is running: `cd backend && python start_sql_server.py`
- Check firewall allows port 5433
- Verify Preset can reach your server

### Schema Not Found
- Check semantic models exist in `semantic-models/` directory
- Restart SQL server to reload models
- Verify schema naming (should be `sem_<model_name>`)

### Performance Issues
- Enable caching in Preset dataset settings
- Use async query execution for large datasets
- Consider pre-aggregations for common queries

## Best Practices

1. **Naming Conventions**
   - Datasets: `SL - <Model Name>`
   - Metrics: Use semantic model names
   - Dashboards: Business-friendly titles

2. **Performance**
   - Set appropriate cache timeouts
   - Use dataset filters over dashboard filters
   - Enable query result caching

3. **Security**
   - Configure row-level security if needed
   - Use Preset roles for access control
   - Regular audit of permissions

## Support

For issues or questions:
1. Check the [Preset Integration Guide](../../../../docs/PRESET_INTEGRATION_GUIDE.md)
2. Review SQL API logs for connection issues
3. Consult Preset documentation for platform-specific features




