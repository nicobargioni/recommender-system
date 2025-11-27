"""
Content-Based Music Recommender using scikit-learn NearestNeighbors
Alternative to Annoy that works reliably with Python 3.13
"""

import pickle
from typing import Optional
import pandas as pd
import numpy as np
from sklearn.preprocessing import StandardScaler
from sklearn.neighbors import NearestNeighbors


# Audio features for similarity computation
FEATURE_COLS = [
    'danceability',
    'energy',
    'loudness',
    'speechiness',
    'acousticness',
    'instrumentalness',
    'liveness',
    'valence',
    'tempo',
    'duration_ms'
]


class SklearnRecommender:
    """
    Content-based music recommender using scikit-learn NearestNeighbors.

    Uses cosine similarity on audio features to find similar tracks.
    More reliable than Annoy for Python 3.13, with exact (not approximate) results.

    Attributes:
        df (pd.DataFrame): Complete dataset with track metadata and features
        scaler (StandardScaler): Fitted scaler for feature normalization
        nn_model (NearestNeighbors): sklearn model for similarity search
        n_features (int): Number of audio features (dimensionality)
        scaled_features (np.ndarray): Scaled feature matrix
    """

    def __init__(self, df: pd.DataFrame):
        """
        Initialize recommender with dataset.

        Args:
            df: DataFrame containing tracks with FEATURE_COLS and metadata
        """
        self.df = df.copy().reset_index(drop=True)  # Reset index to ensure 0-based
        self.scaler: Optional[StandardScaler] = None
        self.nn_model: Optional[NearestNeighbors] = None
        self.n_features = len(FEATURE_COLS)
        self.scaled_features: Optional[np.ndarray] = None

        # Validate required columns
        missing_cols = set(FEATURE_COLS) - set(df.columns)
        if missing_cols:
            raise ValueError(f"Missing required columns: {missing_cols}")

    def fit_and_save_index(
        self,
        index_path: str,
        scaler_path: str = "scaler.pkl",
        n_neighbors: int = 20
    ) -> None:
        """
        Build and save the NearestNeighbors model and StandardScaler.

        Args:
            index_path: Path to save model file (.pkl)
            scaler_path: Path to save StandardScaler pickle file
            n_neighbors: Number of neighbors for the model (default: 20)
        """
        print(f"🔧 Fitting StandardScaler on {len(self.df)} tracks...")

        # Extract and scale features
        raw_features = self.df[FEATURE_COLS].values
        self.scaler = StandardScaler()
        self.scaled_features = self.scaler.fit_transform(raw_features)

        print(f"📐 Building NearestNeighbors model...")

        # Build sklearn NearestNeighbors model with cosine metric
        self.nn_model = NearestNeighbors(
            n_neighbors=min(n_neighbors, len(self.df)),
            metric='cosine',
            algorithm='brute',  # Exact search, works best for cosine
            n_jobs=-1  # Use all CPU cores
        )
        self.nn_model.fit(self.scaled_features)

        print(f"💾 Saving artifacts...")

        # Save scaler
        with open(scaler_path, 'wb') as f:
            pickle.dump(self.scaler, f)

        # Save model
        with open(index_path, 'wb') as f:
            pickle.dump(self.nn_model, f)

        print(f"✅ Model saved to: {index_path}")
        print(f"✅ Scaler saved to: {scaler_path}")
        print(f"📊 Model ready: {len(self.df)} tracks, {self.n_features} features")

    def load_index(
        self,
        index_path: str,
        scaler_path: str = "scaler.pkl"
    ) -> None:
        """
        Load pre-built NearestNeighbors model and StandardScaler from disk.

        Args:
            index_path: Path to model file (.pkl)
            scaler_path: Path to StandardScaler pickle file
        """
        print(f"📂 Loading scaler from: {scaler_path}")

        # Load scaler
        with open(scaler_path, 'rb') as f:
            self.scaler = pickle.load(f)

        print(f"📂 Loading NearestNeighbors model from: {index_path}")

        # Load model
        with open(index_path, 'rb') as f:
            self.nn_model = pickle.load(f)

        # Precompute scaled features
        raw_features = self.df[FEATURE_COLS].values
        self.scaled_features = self.scaler.transform(raw_features)

        print(f"✅ Model loaded successfully")
        print(f"📊 Ready to recommend from {len(self.df)} tracks")

    def get_recommendations(
        self,
        track_name: str,
        n: int = 10
    ) -> pd.DataFrame:
        """
        Get top-N similar tracks for a given track name.

        Args:
            track_name: Name of the seed track
            n: Number of recommendations to return (default: 10)

        Returns:
            DataFrame with columns: track_name, artists, track_genre, similarity_score
            Sorted by similarity (highest first)

        Raises:
            ValueError: If model not loaded or track not found
        """
        if self.nn_model is None or self.scaler is None:
            raise ValueError("Model not loaded. Call fit_and_save_index() or load_index() first.")

        # Find track by name (case-insensitive)
        track_matches = self.df[
            self.df['track_name'].str.lower() == track_name.lower()
        ]

        if track_matches.empty:
            raise ValueError(f"Track '{track_name}' not found in dataset")

        # Use first match if multiple exist
        seed_idx = track_matches.index[0]
        seed_vector = self.scaled_features[seed_idx].reshape(1, -1)

        # Query NearestNeighbors for N+1 neighbors (includes seed track)
        distances, indices = self.nn_model.kneighbors(
            seed_vector,
            n_neighbors=min(n + 1, len(self.df))
        )

        # Remove seed track from results (first result is always the seed itself)
        indices = indices[0][1:]  # Skip first (seed itself)
        distances = distances[0][1:]

        # Convert cosine distance to similarity score
        # Cosine distance = 1 - cosine_similarity
        # So similarity = 1 - distance
        similarity_scores = 1 - distances

        # Build recommendations DataFrame
        recommendations = self.df.iloc[indices].copy()
        recommendations['similarity_score'] = similarity_scores

        # Select and reorder columns (include audio features)
        output_cols = ['track_name', 'artists', 'track_genre', 'similarity_score'] + FEATURE_COLS

        # Handle missing columns gracefully
        available_cols = [col for col in output_cols if col in recommendations.columns]

        result = recommendations[available_cols].reset_index(drop=True)

        return result

    def get_recommendations_by_features(
        self,
        feature_vector: np.ndarray,
        n: int = 10
    ) -> pd.DataFrame:
        """
        Get recommendations based on raw feature vector (for custom queries).

        Args:
            feature_vector: Array of FEATURE_COLS values (unscaled)
            n: Number of recommendations

        Returns:
            DataFrame with recommendations
        """
        if self.nn_model is None or self.scaler is None:
            raise ValueError("Model not loaded.")

        # Scale the input vector
        scaled_vector = self.scaler.transform(feature_vector.reshape(1, -1))

        # Query model
        distances, indices = self.nn_model.kneighbors(
            scaled_vector,
            n_neighbors=min(n, len(self.df))
        )

        # Convert to similarity scores
        similarity_scores = 1 - distances[0]

        # Build results
        recommendations = self.df.iloc[indices[0]].copy()
        recommendations['similarity_score'] = similarity_scores

        output_cols = ['track_name', 'artists', 'track_genre', 'similarity_score'] + FEATURE_COLS
        available_cols = [col for col in output_cols if col in recommendations.columns]

        return recommendations[available_cols].reset_index(drop=True)

    def get_stats(self) -> dict:
        """
        Get recommender statistics for monitoring.

        Returns:
            Dictionary with model metrics
        """
        if self.nn_model is None:
            return {"status": "not_loaded"}

        return {
            "status": "ready",
            "n_tracks": len(self.df),
            "n_features": self.n_features,
            "feature_names": FEATURE_COLS,
            "model_loaded": self.nn_model is not None,
            "scaler_fitted": self.scaler is not None,
            "algorithm": "sklearn NearestNeighbors (cosine)"
        }
