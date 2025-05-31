"""
Configuration management for VeriGreen backend.
"""
import os
from pathlib import Path
from typing import Optional

from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Base paths
BASE_DIR = Path(__file__).parent.parent
PROJECT_ROOT = BASE_DIR.parent

# Data directories
DATA_DIR = Path(os.getenv("DATA_DIR", str(PROJECT_ROOT / "data")))
RAW_DATA_DIR = Path(os.getenv("RAW_DATA_DIR", str(DATA_DIR / "raw")))
PROCESSED_DATA_DIR = Path(os.getenv("PROCESSED_DATA_DIR", str(DATA_DIR / "processed")))

# Ensure directories exist
DATA_DIR.mkdir(parents=True, exist_ok=True)
RAW_DATA_DIR.mkdir(parents=True, exist_ok=True)
PROCESSED_DATA_DIR.mkdir(parents=True, exist_ok=True)

# API Configuration
API_HOST = os.getenv("API_HOST", "0.0.0.0")
API_PORT = int(os.getenv("API_PORT", "8000"))

# Redis Configuration
REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
REDIS_PORT = int(os.getenv("REDIS_PORT", "6379"))
REDIS_DB = int(os.getenv("REDIS_DB", "0"))

# Logging
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")

# Sentinel-2 specific configuration
SENTINEL_DATA_DIR = RAW_DATA_DIR / "sentinel"
SENTINEL_DATA_DIR.mkdir(parents=True, exist_ok=True)

# Filecoin/Storacha Configuration
STORACHA_API_KEY = os.getenv("STORACHA_API_KEY")
STORACHA_API_URL = os.getenv("STORACHA_API_URL", "https://api.storacha.network")


def get_config_summary() -> dict:
    """Get a summary of the current configuration."""
    return {
        "base_dir": str(BASE_DIR),
        "project_root": str(PROJECT_ROOT),
        "data_directories": {
            "data": str(DATA_DIR),
            "raw": str(RAW_DATA_DIR),
            "processed": str(PROCESSED_DATA_DIR),
            "sentinel": str(SENTINEL_DATA_DIR),
        },
        "api": {
            "host": API_HOST,
            "port": API_PORT,
        },
        "redis": {
            "host": REDIS_HOST,
            "port": REDIS_PORT,
            "db": REDIS_DB,
        },
        "logging": {
            "level": LOG_LEVEL,
        },
        "storacha": {
            "api_key_set": bool(STORACHA_API_KEY),
            "api_url": STORACHA_API_URL,
        }
    } 