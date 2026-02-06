from fastapi import APIRouter, HTTPException, Depends
from app.services.demand_forecast.demand_forecast_service import demand_forecast_service
from app.schemas.demand_forecast import DemandForecastParams, DemandForecastResponse
from app.lib.logger import log

router = APIRouter(prefix="/demand-forecast", tags=["Demand Forecast"])

@router.get("/explain", response_model=DemandForecastResponse)
def explain_demand_forecast(params: DemandForecastParams = Depends()):
    """
    Endpoint to explain demand forecast using OOPS-based service.
    """
    try:
        log.info(f"Explaining demand forecast with params: {params}")
        result = demand_forecast_service.get_forecast_explanation(params)
        return result
    except Exception as e:
        log.exception(f"Failed to explain demand forecast: {e}")
        raise HTTPException(status_code=500, detail=str(e))