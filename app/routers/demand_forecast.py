from fastapi import APIRouter, HTTPException, Depends, Header
from app.services.demand_forecast.base import IDemandForecastService
from app.services.demand_forecast.factory import DemandForecastServiceFactory
from app.schemas.demand_forecast import DemandForecastParams, DemandForecastResponse
from app.lib.logger import log
from app.core.client_config import get_client_config, ClientConfig

router = APIRouter(prefix="/api/demand-forecast", tags=["Demand Forecast"])

def get_config(x_company_id: str = Header(..., alias="x-company-id")) -> ClientConfig:
    """
    Dependency to get client configuration based on x-company-id header.
    """
    config = get_client_config(x_company_id)
    if not config:
        log.warning(f"Invalid Company ID received: {x_company_id}")
        raise HTTPException(status_code=400, detail="Invalid Company ID or Client Configuration not found")
    return config

def get_service(config: ClientConfig = Depends(get_config)) -> IDemandForecastService:
    """
    Dependency to get the appropriately configured DemandForecastService using the factory.
    """
    try:
        return DemandForecastServiceFactory.get_service(config)
    except NotImplementedError as e:
        raise HTTPException(status_code=501, detail=str(e))

@router.post("/", response_model=DemandForecastResponse)
def get_demand_forecast(
    params: DemandForecastParams = Depends(),
    x_company_id: str = Header(..., alias="x-company-id"),
    service: IDemandForecastService = Depends(get_service)
):
    """
    Endpoint to get demand forecast details.
    """
    try:        
        params.company_id = x_company_id
        result = service.get_forecast_explanation(params)
        return result
    except Exception as e:
        log.exception(f"Failed to explain demand forecast: {e}")
        raise HTTPException(status_code=500, detail=str(e))