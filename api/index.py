"""Vercel Serverless Function entry point for FastAPI backend."""
import sys
from pathlib import Path

# Add backend directory to Python sys.path so 'app' imports resolve seamlessly
current_dir = Path(__file__).resolve().parent
backend_dir = current_dir.parent / "backend"

if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

from app.main import app

# Vercel ASGI handler expects 'app'
__all__ = ["app"]

