from fastapi import Header, HTTPException
import logging

logger = logging.getLogger(__name__)

def get_active_account(x_active_account: str = Header(..., alias="X-Active-Account")) -> str:
    """
    Dependency that extracts the active account ID from the 'X-Active-Account' header.
    Validates against allowed accounts and raises exceptions if missing or invalid.
    """
    valid_accounts = {"car-j-works", "car-j-home"}
    
    if not x_active_account:
        logger.warning("Missing X-Active-Account header")
        raise HTTPException(status_code=401, detail="X-Active-Account header is missing")
        
    if x_active_account not in valid_accounts:
        logger.warning(f"Invalid X-Active-Account header: {x_active_account}")
        raise HTTPException(status_code=403, detail="Invalid active account")
        
    return x_active_account
