#!/bin/bash
# Start the frontend service

echo "🎨 Starting Semantic Layer Frontend..."

# Go to frontend directory
cd frontend

# Set the API URL if not already set
export REACT_APP_API_URL=http://localhost:8000

# Start the React development server
npm start

