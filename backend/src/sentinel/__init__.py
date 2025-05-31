"""Sentinel-2 data acquisition module."""
from .download import download_sentinel_imagery, validate_downloaded_data

__all__ = ['download_sentinel_imagery', 'validate_downloaded_data'] 