from fastapi import Header, HTTPException
from typing import Optional
from app.core.client_config import get_client_config, ClientConfig

async def get_current_client_config(x_company_id: Optional[str] = Header(None, alias="x-company-id")) -> ClientConfig:
    """
    Dependency to get the current client configuration based on the x-company-id header.
    Throws 400 if header is missing, or 404 if client is not configured.
    """
    if not x_company_id:
        raise HTTPException(status_code=400, detail="x-company-id header is required")
    
    config = get_client_config(x_company_id)
    if not config:
        raise HTTPException(status_code=403, detail=f"Client configuration not found for company ID: {x_company_id}")
    
    return config

async def get_company_id(x_company_id: Optional[str] = Header(None, alias="x-company-id")) -> str:
    """
    Dependency to just get the company ID string.
    """
    if not x_company_id:
        raise HTTPException(status_code=400, detail="x-company-id header is required")
    return x_company_id
