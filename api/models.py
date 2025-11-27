"""
Pydantic models for API requests and responses
"""

from typing import List, Optional
from pydantic import BaseModel, Field


class TrackInfo(BaseModel):
    """Track information in recommendation response"""
    track_name: str
    artists: str
    track_genre: Optional[str] = None
    similarity_score: float = Field(..., ge=0.0, le=1.0)

    # Audio features
    danceability: Optional[float] = None
    energy: Optional[float] = None
    loudness: Optional[float] = None
    speechiness: Optional[float] = None
    acousticness: Optional[float] = None
    instrumentalness: Optional[float] = None
    liveness: Optional[float] = None
    valence: Optional[float] = None
    tempo: Optional[float] = None
    duration_ms: Optional[float] = None


class RecommendationRequest(BaseModel):
    """Request model for track recommendations"""
    track_name: str = Field(..., min_length=1, description="Name of the seed track")
    n: int = Field(12, ge=1, le=50, description="Number of recommendations (1-50)")

    class Config:
        json_schema_extra = {
            "example": {
                "track_name": "Bohemian Rhapsody",
                "n": 10
            }
        }


class RecommendationResponse(BaseModel):
    """Response model for recommendations"""
    seed_track: str
    seed_track_features: Optional[dict] = None
    recommendations: List[TrackInfo]
    count: int

    class Config:
        json_schema_extra = {
            "example": {
                "seed_track": "Bohemian Rhapsody",
                "count": 10,
                "recommendations": [
                    {
                        "track_name": "Don't Stop Me Now",
                        "artists": "Queen",
                        "track_genre": "rock",
                        "similarity_score": 0.95
                    }
                ]
            }
        }


class CustomFeaturesRequest(BaseModel):
    """Request with custom audio features"""
    danceability: float = Field(..., ge=0.0, le=1.0)
    energy: float = Field(..., ge=0.0, le=1.0)
    loudness: float = Field(..., ge=-60.0, le=0.0)
    speechiness: float = Field(..., ge=0.0, le=1.0)
    acousticness: float = Field(..., ge=0.0, le=1.0)
    instrumentalness: float = Field(..., ge=0.0, le=1.0)
    liveness: float = Field(..., ge=0.0, le=1.0)
    valence: float = Field(..., ge=0.0, le=1.0)
    tempo: float = Field(..., ge=0.0, le=250.0)
    duration_ms: float = Field(..., ge=0.0, le=600000.0)
    n: int = Field(10, ge=1, le=50)


class HealthResponse(BaseModel):
    """Health check response"""
    status: str
    version: str
    model_stats: dict


class SearchResponse(BaseModel):
    """Search results for track names"""
    query: str
    matches: List[str]
    count: int
