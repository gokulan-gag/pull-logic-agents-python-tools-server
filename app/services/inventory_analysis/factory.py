from app.services.inventory_analysis.base import IInventoryAnalysisService
from app.services.inventory_analysis.inventory_analysis_service import MaxliteInventoryAnalysisService
from app.core.client_config import ClientConfig, get_client_config
from app.lib.logger import log

class InventoryAnalysisServiceFactory:
    """
    Factory to create the appropriate InventoryAnalysisService based on the company configuration.
    """
    
    @staticmethod
    def get_service(config: ClientConfig) -> IInventoryAnalysisService:
        """
        Returns the appropriate service instance based on the client configuration.
        """
        if config.name == "Maxlite":
            return MaxliteInventoryAnalysisService(config)
        else:
            # Fallback or error for unknown clients
            log.warning(f"No specific service implementation found for client: {config.name}")
            # Identify if we should default to Maxlite or raise error. 
            # For now, following demand_forecast pattern, we raise or log.
            # But let's assume Maxlite is default if strictly needed or raise NotImplemented
            raise NotImplementedError(f"Service for client {config.name} is not implemented.")
