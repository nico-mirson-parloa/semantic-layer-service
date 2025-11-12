#!/bin/bash
# Start the backend service with proper Python path

echo "🚀 Starting Semantic Layer Backend..."

# Get the absolute path of the semantic-layer-service directory
SERVICE_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

echo "📁 Service directory: $SERVICE_DIR"

# Check if we're in the semantic-layer-service directory
if [[ ! -f "$SERVICE_DIR/start_backend.sh" ]]; then
    echo "❌ Error: Not in the semantic-layer-service directory"
    echo "Please run this script from: /Users/nicolas.mirson/Repos/nico-playground/semantic-layer-service"
    exit 1
fi

# Check if virtual environment exists
if [[ ! -d "$SERVICE_DIR/venv" ]]; then
    echo "❌ Error: Virtual environment not found"
    echo "Please create it with: python -m venv venv"
    exit 1
fi

# Load environment variables from .env file
ENV_FILE="$SERVICE_DIR/.env"
if [[ -f "$ENV_FILE" ]]; then
    echo "📝 Loading environment variables from .env file..."
    # Read .env file and export variables (ignoring comments and empty lines)
    set -a
    source "$ENV_FILE"
    set +a
    echo "✅ Environment variables loaded"
else
    echo "⚠️  Warning: .env file not found at $ENV_FILE"
    echo "   The backend may not have proper Databricks configuration"
fi

echo "🚀 Starting Semantic Layer Backend..."

# Activate virtual environment
source "$SERVICE_DIR/venv/bin/activate"

# Set Python path to include backend directory
export PYTHONPATH="$SERVICE_DIR/backend:$PYTHONPATH"

echo "🐍 Python path: $PYTHONPATH"

# Change to backend directory and start uvicorn
cd "$SERVICE_DIR/backend"

echo "📂 Working directory: $(pwd)"
echo "🌐 Starting server on http://localhost:8000"
echo "📝 API docs available at http://localhost:8000/docs"
echo ""
echo "Press Ctrl+C to stop the server"
echo ""

# Start uvicorn
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
