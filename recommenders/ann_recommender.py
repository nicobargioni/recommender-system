"""
ANN-based Music Recommender System using Annoy
Content-based recommendation engine for 114k Spotify tracks
"""

import pickle
from typing import Optional, Tuple
import pandas as pd
import numpy as np
from sklearn.preprocessing import StandardScaler
from annoy import AnnoyIndex


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


class AnnRecommender:
    """
    Content-based music recommender using Approximate Nearest Neighbors (Annoy).

    Uses audio features to find similar tracks efficiently at scale.
    Designed for deployment in FastAPI microservices on Google Cloud Run.

    Attributes:
        df (pd.DataFrame): Complete dataset with track metadata and features
        scaler (StandardScaler): Fitted scaler for feature normalization
        index (AnnoyIndex): Annoy index for fast similarity search
        n_features (int): Number of audio features (dimensionality)
        scaled_features (np.ndarray): Scaled feature matrix
    """

    def __init__(self, df: pd.DataFrame):
        """
        Initialize recommender with dataset.

        Args:
            df: DataFrame containing tracks with FEATURE_COLS and metadata
        """
        self.df = df.copy()
        self.scaler: Optional[StandardScaler] = None
        self.index: Optional[AnnoyIndex] = None
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
        n_trees: int = 100
    ) -> None:
        """
        Build and save the Annoy index and StandardScaler.

        Process:
        1. Scale features using StandardScaler
        2. Build AnnoyIndex with angular metric (cosine similarity approximation)
        3. Save both artifacts to disk

        Args:
            index_path: Path to save Annoy index file (.ann)
            scaler_path: Path to save StandardScaler pickle file
            n_trees: Number of trees for Annoy index (more = better precision, slower build)
        """
        print(f"🔧 Fitting StandardScaler on {len(self.df)} tracks...")

        # Extract and scale features
        raw_features = self.df[FEATURE_COLS].values
        self.scaler = StandardScaler()
        self.scaled_features = self.scaler.fit_transform(raw_features)

        print(f"📐 Building Annoy index with {n_trees} trees...")

        # Build Annoy index (angular metric ≈ cosine similarity)
        self.index = AnnoyIndex(self.n_features, 'angular')

        for idx, feature_vector in enumerate(self.scaled_features):
            self.index.add_item(idx, feature_vector)

        # Build index with specified number of trees
        self.index.build(n_trees)

        print(f"💾 Saving artifacts...")

        # Save scaler
        with open(scaler_path, 'wb') as f:
            pickle.dump(self.scaler, f)

        # Save Annoy index
        self.index.save(index_path)

        print(f"✅ Index saved to: {index_path}")
        print(f"✅ Scaler saved to: {scaler_path}")
        print(f"📊 Index size: {len(self.df)} tracks, {self.n_features} features")

    def load_index(
        self,
        index_path: str,
        scaler_path: str = "scaler.pkl"
    ) -> None:
        """
        Load pre-built Annoy index and StandardScaler from disk.

        Args:
            index_path: Path to Annoy index file (.ann)
            scaler_path: Path to StandardScaler pickle file
        """
        print(f"📂 Loading scaler from: {scaler_path}")

        # Load scaler
        with open(scaler_path, 'rb') as f:
            self.scaler = pickle.load(f)

        print(f"📂 Loading Annoy index from: {index_path}")

        # Load Annoy index
        self.index = AnnoyIndex(self.n_features, 'angular')
        self.index.load(index_path)

        # Precompute scaled features for quick lookups
        raw_features = self.df[FEATURE_COLS].values
        self.scaled_features = self.scaler.transform(raw_features)

        print(f"✅ Index loaded successfully")
        print(f"📊 Ready to recommend from {len(self.df)} tracks")

    def get_recommendations(
        self,
        track_name: str,
        n: int = 10,
        search_by: int = -1
    ) -> pd.DataFrame:
        """
        Get top-N similar tracks for a given track name.

        Args:
            track_name: Name of the seed track
            n: Number of recommendations to return (default: 10)
            search_by: Number of candidates to search (default: -1 = all)

        Returns:
            DataFrame with columns: track_name, artists, track_genre, similarity_score
            Sorted by similarity (highest first)

        Raises:
            ValueError: If index not loaded or track not found
        """
        if self.index is None or self.scaler is None:
            raise ValueError("Index not loaded. Call fit_and_save_index() or load_index() first.")

        # Find track by name (case-insensitive)
        track_matches = self.df[
            self.df['track_name'].str.lower() == track_name.lower()
        ]

        if track_matches.empty:
            raise ValueError(f"Track '{track_name}' not found in dataset")

        # Use first match if multiple exist
        # IMPORTANT: Use iloc to get position-based index (0-based) not pandas index
        pandas_idx = track_matches.index[0]
        seed_position = self.df.index.get_loc(pandas_idx)
        seed_vector = self.scaled_features[seed_position]

        # Query Annoy index for N+1 neighbors (includes seed track)
        neighbor_indices, distances = self.index.get_nns_by_vector(
            seed_vector,
            n + 1,  # +1 to include the seed track itself
            search_k=search_by,
            include_distances=True
        )

        # Remove seed track from results
        neighbor_indices = neighbor_indices[1:]  # Skip first (seed itself)
        distances = distances[1:]

        # Convert angular distance to similarity score
        # Angular distance ∈ [0, 2], similarity ∈ [0, 1]
        # similarity = 1 - (distance / 2)
        similarity_scores = 1 - (np.array(distances) / 2)

        # Build recommendations DataFrame
        # neighbor_indices are 0-based positions, use iloc
        recommendations = self.df.iloc[neighbor_indices].copy()
        recommendations['similarity_score'] = similarity_scores

        # Select and reorder columns
        output_cols = ['track_name', 'artists', 'track_genre', 'similarity_score']

        # Handle missing columns gracefully
        available_cols = [col for col in output_cols if col in recommendations.columns]

        result = recommendations[available_cols].reset_index(drop=True)

        return result

    def get_recommendations_by_features(
        self,
        feature_vector: np.ndarray,
        n: int = 10,
        search_by: int = -1
    ) -> pd.DataFrame:
        """
        Get recommendations based on raw feature vector (for custom queries).

        Useful for API endpoints that receive feature arrays directly.

        Args:
            feature_vector: Array of FEATURE_COLS values (unscaled)
            n: Number of recommendations
            search_by: Number of candidates to search

        Returns:
            DataFrame with recommendations
        """
        if self.index is None or self.scaler is None:
            raise ValueError("Index not loaded.")

        # Scale the input vector
        scaled_vector = self.scaler.transform(feature_vector.reshape(1, -1))[0]

        # Query index
        neighbor_indices, distances = self.index.get_nns_by_vector(
            scaled_vector,
            n,
            search_k=search_by,
            include_distances=True
        )

        # Convert to similarity scores
        similarity_scores = 1 - (np.array(distances) / 2)

        # Build results
        recommendations = self.df.iloc[neighbor_indices].copy()
        recommendations['similarity_score'] = similarity_scores

        output_cols = ['track_name', 'artists', 'track_genre', 'similarity_score']
        available_cols = [col for col in output_cols if col in recommendations.columns]

        return recommendations[available_cols].reset_index(drop=True)

    def get_stats(self) -> dict:
        """
        Get recommender statistics for monitoring.

        Returns:
            Dictionary with index metrics
        """
        if self.index is None:
            return {"status": "not_loaded"}

        return {
            "status": "ready",
            "n_tracks": len(self.df),
            "n_features": self.n_features,
            "feature_names": FEATURE_COLS,
            "index_loaded": self.index is not None,
            "scaler_fitted": self.scaler is not None
        }
