from abc import ABC, abstractmethod
from app.schemas.demand_forecast import DemandForecastRequest, DemandForecastResponse

class IDemandForecastService(ABC):
    @abstractmethod
    def get_forecast_explanation(self, params: DemandForecastRequest) -> DemandForecastResponse:
        pass
