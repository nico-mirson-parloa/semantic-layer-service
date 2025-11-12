#!/bin/bash

# Test script for SQL API

echo "🧪 Testing SQL API Setup"
echo "========================"

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "❌ Virtual environment not found. Please run:"
    echo "   python3 -m venv venv"
    echo "   source venv/bin/activate"
    echo "   pip install -r backend/requirements.txt"
    exit 1
fi

# Activate virtual environment
source venv/bin/activate

# Check dependencies
echo "Checking dependencies..."
python -c "import sqlparse" 2>/dev/null || { echo "❌ sqlparse not installed"; exit 1; }
python -c "import psycopg2" 2>/dev/null || { echo "⚠️  psycopg2 not installed (needed for demo script)"; }

echo "✅ Dependencies OK"

# Check if semantic models exist
if [ ! -d "semantic-models" ] || [ -z "$(ls -A semantic-models/*.yml 2>/dev/null)" ]; then
    echo "⚠️  No semantic models found in semantic-models/"
    echo "   Creating sample model..."
    
    mkdir -p semantic-models
    cat > semantic-models/sample_metrics.yml << 'EOF'
semantic_model:
  name: sample_metrics
  description: Sample semantic model for testing
  model: main.gold.sample_fact
  entities:
    - name: id
      type: primary
      expr: id
  dimensions:
    - name: created_date
      type: time
      expr: created_date
      time_granularity: [day, week, month, year]
    - name: category
      type: categorical
      expr: category
  measures:
    - name: amount
      agg: sum
      expr: amount
      description: Total amount
    - name: count
      agg: count
      expr: id
      description: Number of records
  metrics:
    - name: total_amount
      type: simple
      measure: amount
      description: Total amount across all records
    - name: record_count
      type: simple
      measure: count
      description: Total number of records
EOF
    echo "✅ Created sample_metrics.yml"
fi

echo ""
echo "📋 Available semantic models:"
ls -la semantic-models/*.yml | awk '{print "   • " $9}'

echo ""
echo "🚀 Starting SQL API server..."
echo "   Connect with: psql -h localhost -p 5433 -U user -d semantic_layer"
echo ""
echo "Press Ctrl+C to stop the server"
echo ""

# Start the SQL server
cd backend
python start_sql_server.py




