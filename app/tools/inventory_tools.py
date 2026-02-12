from app.services.inventory_analysis.factory import InventoryAnalysisServiceFactory
from app.core.client_config import get_client_config
import json
from typing import Dict, Any
from app.schemas.inventory_analysis import InventoryAnalysisRequestWithSelection, InventoryAnalysisRequestWithSelection
from app.core.context import get_company_id

class InventoryTools:
    def _get_service(self):
        company_id = get_company_id()
        if not company_id:
            # Fallback for now or raise error
            raise ValueError(f"Company ID not found in context")
            
        config = get_client_config(company_id)
        if not config:
            raise ValueError(f"Configuration for company {company_id} not found")
        return InventoryAnalysisServiceFactory.get_service(config)

    async def enough_stock_analysis(self, request: Dict[str, Any]) -> Dict[str, Any]:
        print("Request received for inventory analysis:", request)
        try:
            # Convert dict to Pydantic model
            req_model = InventoryAnalysisRequestWithSelection(**request)
            service = self._get_service()
            response = await service.get_enough_stock(req_model)
            
            json_output = json.dumps(response, indent=2)
            
            return {
                "content": [{"type": "text", "text": json_output}],
                "structuredContent": {
                    "results": json_output,
                    "executionId": response.get("executionId", ""),
                    "nextToken": response.get("nextToken", "") or "",
                    "hasMore": response.get("hasMore", False),
                    "count": response.get("count", 0)
                }
            }
        except Exception as e:
            print("Error calling inventory analysis:", str(e))
            error_output = {"error": f"Unexpected error: {str(e)}"}
            return {
                "content": [{"type": "text", "text": json.dumps(error_output, indent=2)}],
                "structuredContent": {
                    "results": json.dumps(error_output),
                    "executionId": "",
                    "nextToken": "",
                    "hasMore": False,
                    "count": 0
                }
            }

    async def excess_stock_analysis(self, request: Dict[str, Any]) -> Dict[str, Any]:
        print("Request received for excess inventory analysis:", request)
        try:
            req_model = InventoryAnalysisRequestWithSelection(**request)
            service = self._get_service()
            response = await service.get_excess_stock(req_model)
            
            json_output = json.dumps(response, indent=2)
            
            return {
                "content": [{"type": "text", "text": json_output}],
                "structuredContent": {
                    "results": json_output,
                    "executionId": response.get("executionId", ""),
                    "nextToken": response.get("nextToken", "") or "",
                    "hasMore": response.get("hasMore", False),
                    "count": response.get("count", 0)
                }
            }
        except Exception as e:
            print("Error calling excess inventory analysis:", str(e))
            error_output = {"error": f"Unexpected error: {str(e)}"}
            return {
                "content": [{"type": "text", "text": json.dumps(error_output, indent=2)}],
                "structuredContent": {
                    "results": json.dumps(error_output),
                    "executionId": "",
                    "nextToken": "",
                    "hasMore": False,
                    "count": 0
                }
            }

inventory_tools = InventoryTools()
