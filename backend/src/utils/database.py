import json
import logging
from typing import Optional, List
from datetime import datetime
from pathlib import Path

logger = logging.getLogger(__name__)

# Temporary storage location for development
CLAIMS_FILE = Path(__file__).parent.parent.parent.parent / "data" / "claims.json"


def store_claim(claim_data: dict) -> bool:
    """
    Store a land claim in the database.
    
    Args:
        claim_data: The complete claim data dictionary
        
    Returns:
        True if successful, False otherwise
    """
    try:
        # Ensure data directory exists
        CLAIMS_FILE.parent.mkdir(parents=True, exist_ok=True)
        
        # Load existing claims
        claims = {}
        if CLAIMS_FILE.exists():
            with open(CLAIMS_FILE, 'r') as f:
                claims = json.load(f)
        
        # Store claim
        claims[claim_data["claim_id"]] = claim_data
        
        # Save to file
        with open(CLAIMS_FILE, 'w') as f:
            json.dump(claims, f, indent=2)
        
        logger.info(f"Successfully stored claim {claim_data['claim_id']}")
        return True
        
    except Exception as e:
        logger.error(f"Failed to store claim {claim_data.get('claim_id', 'unknown')}: {str(e)}")
        return False


def get_claim(claim_id: str) -> Optional[dict]:
    """
    Retrieve a land claim by its ID.
    
    Args:
        claim_id: The unique identifier for the claim
        
    Returns:
        Claim data if found, None otherwise
    """
    try:
        if not CLAIMS_FILE.exists():
            return None
        
        with open(CLAIMS_FILE, 'r') as f:
            claims = json.load(f)
        
        return claims.get(claim_id)
        
    except Exception as e:
        logger.error(f"Failed to retrieve claim {claim_id}: {str(e)}")
        return None


def get_all_claims() -> List[dict]:
    """
    Retrieve all land claims.
    
    Returns:
        List of all claim data
    """
    try:
        if not CLAIMS_FILE.exists():
            return []
        
        with open(CLAIMS_FILE, 'r') as f:
            claims = json.load(f)
        
        return list(claims.values())
        
    except Exception as e:
        logger.error(f"Failed to retrieve all claims: {str(e)}")
        return []


def update_claim_status(claim_id: str, status: str, **kwargs) -> bool:
    """
    Update the status of a land claim.
    
    Args:
        claim_id: The unique identifier for the claim
        status: New status value
        **kwargs: Additional fields to update (e.g., filecoin_hash)
        
    Returns:
        True if successful, False otherwise
    """
    try:
        if not CLAIMS_FILE.exists():
            return False
        
        with open(CLAIMS_FILE, 'r') as f:
            claims = json.load(f)
        
        if claim_id not in claims:
            return False
        
        # Update claim
        claims[claim_id]["status"] = status
        claims[claim_id]["updated_at"] = datetime.utcnow().isoformat()
        
        # Update additional fields
        for key, value in kwargs.items():
            claims[claim_id][key] = value
        
        # Save changes
        with open(CLAIMS_FILE, 'w') as f:
            json.dump(claims, f, indent=2)
        
        logger.info(f"Updated claim {claim_id} status to {status}")
        return True
        
    except Exception as e:
        logger.error(f"Failed to update claim {claim_id}: {str(e)}")
        return False


async def check_existing_claims(area_bounds) -> list:
    """
    Check for existing claims that might overlap with the given boundaries.
    
    TODO: Implement spatial queries for overlap detection.
    For now, returns empty list (no overlaps).
    
    Args:
        area_bounds: The geographical boundaries to check
        
    Returns:
        List of overlapping claim IDs
    """
    # Placeholder implementation
    # In a real system with PostGIS or similar:
    # 1. Create a polygon from area_bounds
    # 2. Query database for intersecting polygons
    # 3. Return list of overlapping claim IDs
    
    return [] 