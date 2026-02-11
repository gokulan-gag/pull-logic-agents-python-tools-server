from app.services.demand_forecast.base import IDemandForecastService
from app.services.demand_forecast.demand_forecast_service import TymDemandForecastService
from app.core.client_config import ClientConfig, get_client_config
from app.lib.logger import log

class DemandForecastServiceFactory:
    """
    Factory to create the appropriate DemandForecastService based on the company configuration.
    """
    
    @staticmethod
    def get_service(config: ClientConfig) -> IDemandForecastService:
        """
        Returns the appropriate service instance based on the client configuration.
        """
        if config.name == "TYM":
            return TymDemandForecastService(config)
        else:
            # Fallback or error for unknown clients
            # For now, if we have a config but no specific service mapped, we might default or raise
            # But based on user request, we should implement separate classes.
            # If we had Maxlite, checking config.name == "Maxlite" -> return MaxliteDemandForecastService(config)
            log.warning(f"No specific service implementation found for client: {config.name}, default/fallback not implemented.")
            raise NotImplementedError(f"Service for client {config.name} is not implemented.")
