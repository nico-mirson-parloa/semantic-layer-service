#!/bin/bash

# Semantic Layer Backend Startup Script
# This script starts the FastAPI backend on port 8000

set -e

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${GREEN}=== Semantic Layer Backend Startup ===${NC}"

# Check if we're in the backend directory
if [ ! -f "app/main.py" ]; then
    echo -e "${RED}Error: Must run from backend directory${NC}"
    exit 1
fi

# Check if .env file exists (in parent or current directory)
if [ ! -f ".env" ] && [ ! -f "../.env" ]; then
    echo -e "${YELLOW}Warning: No .env file found${NC}"
    echo "Please create .env file with Databricks credentials"
    echo "See ../env.example for template"
    exit 1
fi

# Activate virtual environment
if [ -f "../venv/bin/activate" ]; then
    echo -e "${GREEN}Activating virtual environment...${NC}"
    source ../venv/bin/activate
else
    echo -e "${RED}Error: Virtual environment not found at ../venv${NC}"
    echo "Please run: python3 -m venv ../venv"
    exit 1
fi

# Check if port 8000 is already in use
if lsof -i :8000 > /dev/null 2>&1; then
    echo -e "${YELLOW}Warning: Port 8000 is already in use${NC}"
    echo "Stopping existing process..."
    pkill -f "uvicorn app.main:app" || true
    sleep 2
fi

# Start the backend
echo -e "${GREEN}Starting FastAPI backend on port 8000...${NC}"
echo ""
echo "Access points:"
echo "  - API: http://localhost:8000"
echo "  - Docs: http://localhost:8000/docs"
echo "  - Health: http://localhost:8000/api/health/"
echo ""

# Run in foreground for development (use nohup for background)
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
