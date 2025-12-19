"""Configuration for FastAPI service"""
import sys
import os

# Add parent directory to path to import shared modules
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from shared.config import Config

# FastAPI specific settings
API_PREFIX = "/api/simplefx"
HOST = "0.0.0.0"
PORT = int(os.getenv("FASTAPI_PORT", "8000"))


