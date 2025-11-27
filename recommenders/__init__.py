"""
Spotify Tracks Recommender System
Content-based recommendation engine
"""

# Use sklearn recommender (more reliable than Annoy with Python 3.13)
from .sklearn_recommender import SklearnRecommender, FEATURE_COLS

# Keep AnnRecommender for reference (has bugs with Python 3.13)
try:
    from .ann_recommender import AnnRecommender
except:
    AnnRecommender = None

__all__ = ['SklearnRecommender', 'FEATURE_COLS']
__version__ = '1.1.0'
