# app/main.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.lib.logger import setup_logging
from app.lib.exceptions import register_error_handlers
from app.core.config import settings
from app.routers.demand_forecast import router as demand_forecast_router
from app.routers.inventory_analysis import router as inventory_analysis_router
from app.routers.mcp import mcp_app

# Initialize structured logging
log = setup_logging()

app = FastAPI(
    title=settings.PROJECT_NAME,
    description="Production-grade FastAPI server with MSSQL pooling, MCP tools, and structured logging.",
    lifespan=mcp_app.lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
    allow_credentials=True,
)

register_error_handlers(app)

@app.get("/health")
def health():
    return {"status": "ok"}

app.include_router(demand_forecast_router, prefix="/api")
app.include_router(inventory_analysis_router, prefix="/api")

#    This makes all MCP tools available under /mcp path
app.mount("/mcp", mcp_app)

@app.get("/debug/routes")
def list_routes():
    routes = []
    for route in app.routes:
        if hasattr(route, "path"):
            routes.append({"path": route.path, "methods": getattr(route, "methods", [])})
    return routes


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
