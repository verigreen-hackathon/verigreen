"""
Processing package for VeriGreen.

Handles on-demand processing of satellite imagery for land claims.
"""

from .claim_processor import ClaimProcessor, ProcessingResult

__all__ = [
    'ClaimProcessor',
    'ProcessingResult'
] 