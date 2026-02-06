from pydantic import BaseModel, Field
from typing import Optional, Dict, Any

class DemandForecastParams(BaseModel):
    region: str = "All"
    forecast_date: str = "2026-12-07"
    period: str = "cumulative"
    filter_name: str = "Region"
    filter_value: str = "Gulf Coast"
    series_id: str = "ALL"
    company_id: str = "f80d6409-cb1d-4af1-8e1c-1b90f657b9bd"
    sales_type: str = "Retail"

class DemandForecastMetadata(BaseModel):
    target_date: str
    filter_name: str
    filter_value: str
    period: str
    series_id: Optional[str] = None

class DemandForecastResponse(BaseModel):
    forecasted_demand: float
    average_demand_per_week: float
    change_vs_last_month_actual_sales: float = 0.0
    change_vs_same_month_last_year: float = 0.0
    coefficient_of_variation: float = 0.0
    current_month_forecasted_demand: float = 0.0
    prev_month_actual_sales: float = 0.0
    same_month_last_year_actual_sales: float = 0.0
    actual_sales_yoy_percentage_changes: list[float] = []
    trend: Optional[float] = None
    seasonality: Optional[float] = None
    confidence_interval: Optional[Dict[str, Any]] = None
    metadata: Optional[DemandForecastMetadata] = None