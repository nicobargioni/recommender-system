#!/bin/bash

# Local development server startup script
# Runs the FastAPI application with auto-reload

echo "🚀 Starting Sonic Finder API (Development Mode)"
echo "================================================"

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "⚠️  No virtual environment found. Creating one..."
    python3 -m venv venv
fi

# Activate virtual environment
source venv/bin/activate

# Install dependencies if needed
if ! pip show fastapi &> /dev/null; then
    echo "📦 Installing dependencies..."
    pip install -r requirements.txt
fi

# Check if dataset exists, download if needed
if [ ! -f "data/spotify_tracks.csv" ]; then
    echo "⚠️  Dataset not found at data/spotify_tracks.csv"
    echo "📥 Downloading dataset from Hugging Face..."
    echo ""
    python download_dataset.py

    if [ $? -ne 0 ]; then
        echo ""
        echo "❌ Failed to download dataset automatically"
        echo "   Please run: python download_dataset.py"
        exit 1
    fi
    echo ""
fi

# Export environment variables
export PORT=8080
export DATASET_PATH=data/spotify_tracks.csv
export INDEX_PATH=artifacts/sklearn_model.pkl
export SCALER_PATH=artifacts/scaler.pkl

echo ""
echo "✅ Environment ready"
echo "🌐 Server will start at: http://localhost:8080"
echo "📚 API docs at: http://localhost:8080/docs"
echo ""
echo "Press Ctrl+C to stop the server"
echo ""

# Run with auto-reload for development
uvicorn main:app --host 0.0.0.0 --port 8080 --reload
