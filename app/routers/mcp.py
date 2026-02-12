from typing import Any
from fastapi import APIRouter
from fastmcp import FastMCP
from app.tools.inventory_tools import inventory_tools
from app.tools.demand_forecast_tools import demand_forecast_tools
from app.schemas.inventory_analysis import InventoryAnalysisRequestWithSelection, InventoryAnalysisOutput
from app.schemas.demand_forecast import DemandForecastRequest, DemandForecastResponse
from app.core.context import get_company_id, set_company_id
from app.lib.logger import log
from fastmcp.server.dependencies import get_http_request
from fastmcp.server.middleware import Middleware, MiddlewareContext, CallNext
import mcp.types as mt

router = APIRouter(tags=["mcp"])

class HeaderMiddleware(Middleware):
    async def on_request(
        self,
        context: MiddlewareContext[mt.Request[Any, Any]],
        call_next: CallNext[mt.Request[Any, Any], Any],
    ) -> Any:
        try:
            http_req = get_http_request()
            company_id = http_req.headers.get("x-company-id")
            if company_id:
                set_company_id(company_id)
                log.info(f"Set company_id from headers: {company_id}")
        except RuntimeError:
            log.warning("No HTTP request found for MCP message")
        
        return await call_next(context)

# Initialize MCP Server (ASGI only, do NOT set host/port here)
mcp = FastMCP(name="python-tools-server", middleware=[HeaderMiddleware()])

@mcp.tool(
    name="enough_stock_analysis",
    description="Analyze Stocks based on user's query.",
)
async def enough_stock_analysis(
    request: InventoryAnalysisRequestWithSelection
) -> InventoryAnalysisOutput:
    """Analyze Stocks based on user's query."""
    company_id = get_company_id()
    log.info(f"Analyzing enough stock for company: {company_id}")
    
    result = await inventory_tools.enough_stock_analysis(request.model_dump())
    
    return InventoryAnalysisOutput(**result["structuredContent"])

@mcp.tool(
    name="excess_stock_analysis",
    description="Analyze excess stocks based on user's query.",
)
async def excess_stock_analysis(
    request: InventoryAnalysisRequestWithSelection
) -> InventoryAnalysisOutput:
    """Analyze excess stocks based on user's query."""
    company_id = get_company_id()
    log.info(f"Analyzing excess stock for company: {company_id}")
    
    result = await inventory_tools.excess_stock_analysis(request.model_dump())
    
    return InventoryAnalysisOutput(**result["structuredContent"])

@mcp.tool(
    name="demand_forecast_details",
    description="Get demand forecast details based on user's query.",
)
async def demand_forecast_details(
    request: DemandForecastRequest
) -> DemandForecastResponse:
    """Get demand forecast details based on user's query."""
    company_id = get_company_id()
    log.info(f"Getting demand forecast for company: {company_id}")
    
    result = await demand_forecast_tools.get_demand_forecast(request.model_dump())
    
    return DemandForecastResponse(**result["structuredContent"])


# Create streamable HTTP ASGI app
# We set path="/" so that when mounted at "/mcp" in main.py, 
# the MCP endpoint is available at exactly "/mcp"
mcp_app = mcp.http_app(path="/", transport="streamable-http", stateless_http=True)