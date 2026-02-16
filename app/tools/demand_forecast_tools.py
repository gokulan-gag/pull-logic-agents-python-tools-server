from app.services.demand_forecast.factory import DemandForecastServiceFactory
from app.core.client_config import get_client_config
import json
from typing import Dict, Any
from app.schemas.demand_forecast import DemandForecastRequest
from app.core.context import get_company_id
from app.lib.logger import log

class DemandForecastTools:
    def _get_service(self):
        company_id = get_company_id()
        if not company_id:
            raise ValueError(f"Company ID not found in context")
            
        config = get_client_config(company_id)
        if not config:
            raise ValueError(f"Configuration for company {company_id} not found")
        return DemandForecastServiceFactory.get_service(config)

    async def get_demand_forecast(self, request: Dict[str, Any]) -> Dict[str, Any]:
        log.info(f"Request received for demand forecast: {request}")
        try:
            # Convert dict to Pydantic model
            req_model = DemandForecastRequest(**request)
            service = self._get_service()
            
            result = service.get_forecast_explanation(req_model)
            
            # If it's a Pydantic model, convert to dict
            if hasattr(result, "model_dump"):
                response_dict = result.model_dump()
            else:
                response_dict = result
                
            json_output = json.dumps(response_dict, indent=2, default=str)
            log.info(f"Response received for demand forecast: {json_output}")
            
            return {
                "content": [{"type": "text", "text": json_output}],
                "structuredContent": response_dict
            }
        except Exception as e:
            log.error(f"Error calling demand forecast: {str(e)}")
            error_output = {"error": f"Unexpected error: {str(e)}"}
            return {
                "content": [{"type": "text", "text": json.dumps(error_output, indent=2, default=str)}],
                "structuredContent": error_output
            }

demand_forecast_tools = DemandForecastTools()
