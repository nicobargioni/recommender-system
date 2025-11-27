"""
Spotify Tracks Recommender API
FastAPI microservice for music recommendations using Annoy
"""

import os
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi import Request
import pandas as pd
from recommenders import SklearnRecommender
from api.models import RecommendationRequest, RecommendationResponse, HealthResponse
from api.routes import router


# Global recommender instance
recommender: SklearnRecommender = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Load model on startup, cleanup on shutdown"""
    global recommender

    print("🚀 Starting Spotify Recommender API...")

    # Load dataset
    data_path = os.getenv('DATASET_PATH', 'data/spotify_tracks.csv')
    index_path = os.getenv('INDEX_PATH', 'artifacts/sklearn_model.pkl')
    scaler_path = os.getenv('SCALER_PATH', 'artifacts/scaler.pkl')

    print(f"📂 Loading dataset from: {data_path}")
    df = pd.read_csv(data_path)

    # Initialize recommender
    recommender = SklearnRecommender(df)

    # Check if model exists, otherwise build it
    if os.path.exists(index_path) and os.path.exists(scaler_path):
        print("📦 Loading pre-built model...")
        recommender.load_index(index_path, scaler_path)
    else:
        print("⚠️  No pre-built model found, building new model...")
        os.makedirs('artifacts', exist_ok=True)
        recommender.fit_and_save_index(index_path, scaler_path)

    print("✅ API ready to serve recommendations!")

    yield

    print("🛑 Shutting down API...")


# Initialize FastAPI app
app = FastAPI(
    title="Spotify Tracks Recommender",
    description="Content-based music recommendation system using Annoy (ANN)",
    version="1.0.0",
    lifespan=lifespan
)

# CORS middleware for frontend access
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files and templates
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

# Include API routes
app.include_router(router, prefix="/api", tags=["Recommendations"])


@app.get("/", response_class=HTMLResponse)
async def root(request: Request):
    """Serve landing page"""
    return templates.TemplateResponse("index.html", {"request": request})


@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint for Cloud Run"""
    stats = recommender.get_stats() if recommender else {"status": "not_loaded"}
    return {
        "status": "healthy" if stats.get("status") == "ready" else "loading",
        "version": "1.0.0",
        "model_stats": stats
    }
