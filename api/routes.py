"""
API routes for music recommendations
"""

from fastapi import APIRouter, HTTPException, Query, Depends
from typing import List
import numpy as np
import pandas as pd
from api.models import (
    RecommendationRequest,
    RecommendationResponse,
    CustomFeaturesRequest,
    TrackInfo,
    SearchResponse
)

router = APIRouter()

# Import get_recommender inside functions to avoid circular import
def get_recommender():
    """Dependency to get recommender instance"""
    from main import recommender
    if recommender is None:
        raise HTTPException(status_code=503, detail="Recommender not loaded")
    return recommender


@router.post("/recommend", response_model=RecommendationResponse)
async def get_recommendations(request: RecommendationRequest):
    """
    Get track recommendations based on a seed track name.

    Returns the top N most similar tracks using audio features.
    """
    recommender = get_recommender()

    try:
        # Get recommendations
        results = recommender.get_recommendations(
            track_name=request.track_name,
            n=request.n
        )

        # Get seed track features
        seed_track_row = recommender.df[
            recommender.df['track_name'].str.lower() == request.track_name.lower()
        ]

        seed_features = None
        if not seed_track_row.empty:
            seed_features = {
                'danceability': float(seed_track_row.iloc[0]['danceability']),
                'energy': float(seed_track_row.iloc[0]['energy']),
                'loudness': float(seed_track_row.iloc[0]['loudness']),
                'speechiness': float(seed_track_row.iloc[0]['speechiness']),
                'acousticness': float(seed_track_row.iloc[0]['acousticness']),
                'instrumentalness': float(seed_track_row.iloc[0]['instrumentalness']),
                'liveness': float(seed_track_row.iloc[0]['liveness']),
                'valence': float(seed_track_row.iloc[0]['valence']),
                'tempo': float(seed_track_row.iloc[0]['tempo']),
                'duration_ms': float(seed_track_row.iloc[0]['duration_ms'])
            }

        # Convert to response model
        recommendations = [
            TrackInfo(
                track_name=row['track_name'],
                artists=row['artists'],
                track_genre=row.get('track_genre'),
                similarity_score=round(row['similarity_score'], 4),
                danceability=row.get('danceability'),
                energy=row.get('energy'),
                loudness=row.get('loudness'),
                speechiness=row.get('speechiness'),
                acousticness=row.get('acousticness'),
                instrumentalness=row.get('instrumentalness'),
                liveness=row.get('liveness'),
                valence=row.get('valence'),
                tempo=row.get('tempo'),
                duration_ms=row.get('duration_ms')
            )
            for _, row in results.iterrows()
        ]

        return RecommendationResponse(
            seed_track=request.track_name,
            seed_track_features=seed_features,
            recommendations=recommendations,
            count=len(recommendations)
        )

    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal error: {str(e)}")


@router.post("/recommend-by-features", response_model=RecommendationResponse)
async def recommend_by_features(request: CustomFeaturesRequest):
    """
    Get recommendations based on custom audio features.

    Useful for creating custom queries with specific audio characteristics.
    """
    recommender = get_recommender()

    try:
        # Build feature vector
        feature_vector = np.array([
            request.danceability,
            request.energy,
            request.loudness,
            request.speechiness,
            request.acousticness,
            request.instrumentalness,
            request.liveness,
            request.valence,
            request.tempo,
            request.duration_ms
        ])

        # Get recommendations
        results = recommender.get_recommendations_by_features(
            feature_vector=feature_vector,
            n=request.n
        )

        # Convert to response model
        recommendations = [
            TrackInfo(
                track_name=row['track_name'],
                artists=row['artists'],
                track_genre=row.get('track_genre'),
                similarity_score=round(row['similarity_score'], 4),
                danceability=row.get('danceability'),
                energy=row.get('energy'),
                loudness=row.get('loudness'),
                speechiness=row.get('speechiness'),
                acousticness=row.get('acousticness'),
                instrumentalness=row.get('instrumentalness'),
                liveness=row.get('liveness'),
                valence=row.get('valence'),
                tempo=row.get('tempo'),
                duration_ms=row.get('duration_ms')
            )
            for _, row in results.iterrows()
        ]

        return RecommendationResponse(
            seed_track="Custom Features",
            recommendations=recommendations,
            count=len(recommendations)
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal error: {str(e)}")


@router.get("/search", response_model=SearchResponse)
async def search_tracks(
    q: str = Query(..., min_length=1, description="Search query"),
    limit: int = Query(10, ge=1, le=50)
):
    """
    Search for tracks by name (autocomplete).

    Returns matching track names for autocomplete functionality.
    """
    recommender = get_recommender()

    try:
        # Search tracks (case-insensitive)
        df = recommender.df
        matches = df[
            df['track_name'].str.contains(q, case=False, na=False)
        ]['track_name'].unique()[:limit].tolist()

        return SearchResponse(
            query=q,
            matches=matches,
            count=len(matches)
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Search error: {str(e)}")


@router.get("/random", response_model=List[str])
async def get_random_tracks(n: int = Query(5, ge=1, le=20)):
    """
    Get random track names for exploration.
    """
    recommender = get_recommender()

    try:
        random_tracks = recommender.df['track_name'].sample(n=n).tolist()
        return random_tracks
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")


@router.post("/recommend/vectors")
async def get_recommendation_vectors(request: RecommendationRequest):
    """
    Get 2D vector coordinates for visualization using PCA.

    Returns the seed track and its neighbors projected onto a 2D plane
    for vector space visualization.
    """
    recommender = get_recommender()

    try:
        from sklearn.decomposition import PCA

        # Get recommendations
        results = recommender.get_recommendations(
            track_name=request.track_name,
            n=request.n
        )

        # Get the seed track index
        seed_idx = recommender.df[
            recommender.df['track_name'] == request.track_name
        ].index[0]

        # Get indices of recommendations
        rec_indices = []
        for _, row in results.iterrows():
            idx = recommender.df[
                (recommender.df['track_name'] == row['track_name']) &
                (recommender.df['artists'] == row['artists'])
            ].index[0]
            rec_indices.append(idx)

        # Get normalized features for seed + recommendations
        all_indices = [seed_idx] + rec_indices[:10]  # Top 10 + seed
        features = recommender.scaled_features[all_indices]

        # Apply PCA to reduce to 2D
        pca = PCA(n_components=2)
        coords_2d = pca.fit_transform(features)

        # Prepare response
        vectors = []
        for i, idx in enumerate(all_indices):
            track_info = recommender.df.iloc[idx]
            vectors.append({
                "track_name": track_info['track_name'],
                "artists": track_info['artists'],
                "track_genre": track_info.get('track_genre'),
                "is_seed": i == 0,
                "x": float(coords_2d[i, 0]),
                "y": float(coords_2d[i, 1]),
                "similarity_score": 1.0 if i == 0 else float(results.iloc[i-1]['similarity_score'])
            })

        return {
            "seed_track": request.track_name,
            "vectors": vectors,
            "explained_variance": [float(v) for v in pca.explained_variance_ratio_],
            "count": len(vectors)
        }

    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal error: {str(e)}")


@router.get("/stats")
async def get_stats():
    """Get system statistics"""
    recommender = get_recommender()
    return recommender.get_stats()
