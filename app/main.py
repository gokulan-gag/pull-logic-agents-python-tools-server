from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import text
from app.lib.database import get_db
from app.lib.logger import setup_logging
from app.lib.exceptions import register_error_handlers
from app.routers.demand_forecast import router as demand_forecast_router
from app.core.config import settings

# Initialize structured logging
log = setup_logging()

app = FastAPI(
    title=settings.PROJECT_NAME,
    description="Production-grade FastAPI server with MSSQL pooling and structured logging."
)

# Register global exception handlers and middleware
register_error_handlers(app)

@app.get("/health")
def health():
    return {"status": "ok"}

@app.get("/db-test")
def test_db(db: Session = Depends(get_db)):
    """
    Test database connectivity.
    """
    result = db.execute(text("SELECT 1")).scalar()
    log.info("Database connectivity test successful")
    return {"status": "connected", "result": result}

@app.get("/error-test")
def test_error():
    """
    Test global exception handling.
    """
    log.info("Triggering a test error")
    raise Exception("This is a manual test error")

app.include_router(demand_forecast_router)
