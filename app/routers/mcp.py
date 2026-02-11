from fastapi import APIRouter
from mcp.server.fastmcp import FastMCP
from app.tools.inventory_tools import inventory_tools
from app.schemas.inventory_analysis import InventoryAnalysisRequestWithSelection
from app.core.context import set_company_id, get_company_id
from app.lib.logger import log

router = APIRouter(tags=["mcp"])

# Initialize MCP Server
mcp = FastMCP(
    name="python-tools-server",
    description="Python Tools Server",
    host="0.0.0.0",
    port=8000,
    reload=True,
)


@mcp.tool(
    name="enough_stock_analysis",
    description="Analyze Stocks based on user's query.",
    structured_output=True,
)
async def enough_stock_analysis(
    request: InventoryAnalysisRequestWithSelection
) -> dict:
    """Analyze Stocks based on user's query."""
    company_id = get_company_id()
    log.info(f"Analyzing enough stock for company: {company_id}")
    
    return await inventory_tools.enough_stock_analysis(request)
