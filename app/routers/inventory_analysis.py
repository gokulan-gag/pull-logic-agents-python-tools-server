from fastapi import APIRouter, HTTPException, Depends, Header
from app.schemas.inventory_analysis import InventoryAnalysisRequestWithSelection
from app.services.inventory_analysis.base import IInventoryAnalysisService
from app.services.inventory_analysis.factory import InventoryAnalysisServiceFactory
from app.core.client_config import get_client_config, ClientConfig
from app.lib.logger import log

router = APIRouter(prefix="/api/inventory", tags=["inventory"])

def get_config(x_company_id: str = Header(..., alias="x-company-id")) -> ClientConfig:
    """
    Dependency to get client configuration based on x-company-id header.
    """
    config = get_client_config(x_company_id)
    if not config:
        log.warning(f"Invalid Company ID received: {x_company_id}")
        raise HTTPException(status_code=400, detail="Invalid Company ID or Client Configuration not found")
    return config

def get_service(config: ClientConfig = Depends(get_config)) -> IInventoryAnalysisService:
    """
    Dependency to get the appropriately configured InventoryAnalysisService using the factory.
    """
    try:
        return InventoryAnalysisServiceFactory.get_service(config)
    except NotImplementedError as e:
        raise HTTPException(status_code=501, detail=str(e))

@router.post("/enough-stock")
async def enough_stock(
    request: InventoryAnalysisRequestWithSelection,
    service: IInventoryAnalysisService = Depends(get_service)
):
    try:
        return await service.get_enough_stock(request)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/excess-stock")
async def excess_stock(
    request: InventoryAnalysisRequestWithSelection,
    service: IInventoryAnalysisService = Depends(get_service)
):
    try:
        return await service.get_excess_stock(request)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
