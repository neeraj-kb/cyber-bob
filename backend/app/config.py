"""Configuration and scoring constants for Cybersecurity Flight Simulator."""
from pathlib import Path
import os

# Base paths
BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
DB_PATH = os.getenv("DB_PATH", str(BASE_DIR / "twin_state.db"))

# Graph Traversal Limits
DEFAULT_PATH_CUTOFF = 8
CRITICALITY_THRESHOLD = 4

# Evidence Pipeline Constants
FRESHNESS_WINDOW_DAYS = 7.0  # Events within this window are fresh
CONFIDENCE_HALF_LIFE_DAYS = 14.0  # Half-life decay for confidence scoring
MAX_CONFIDENCE_UNKNOWN = 0.05
BASE_CONFIDENCE_MULTIPLIER = 0.4

# Defense Archetypes Fixed Effort Scores (1-5)
EFFORT_SCORES = {
    "isolate_host": 2,
    "revoke_identity": 1,
    "block_link": 3,
}

# AI Explanation Configuration
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")

