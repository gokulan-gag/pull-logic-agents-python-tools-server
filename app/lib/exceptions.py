from fastapi import Request, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from sqlalchemy.exc import SQLAlchemyError
import time
from app.lib.logger import log

class AppError(Exception):
    """Base class for application errors"""
    def __init__(self, message: str, status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR):
        self.message = message
        self.status_code = status_code
        super().__init__(message)

async def global_exception_handler(request: Request, exc: Exception):
    """
    Catch-all exception handler for any unhandled exceptions.
    """
    log.exception(f"Unhandled exception occurred: {exc}")
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": "Internal Server Error",
            "message": "An unexpected error occurred. Please try again later.",
            "path": request.url.path
        }
    )

async def app_error_handler(request: Request, exc: AppError):
    """
    Handler for custom application errors.
    """
    log.warning(f"AppError: {exc.message} on {request.url.path}")
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": "Application Error",
            "message": exc.message,
            "path": request.url.path
        }
    )

async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """
    Handler for FastAPI request validation errors.
    """
    log.warning(f"Validation error: {exc.errors()} on {request.url.path}")
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "error": "Validation Error",
            "details": exc.errors(),
            "path": request.url.path
        }
    )

async def sqlalchemy_exception_handler(request: Request, exc: SQLAlchemyError):
    """
    Handler for SQLAlchemy/Database errors.
    """
    log.exception(f"Database error: {str(exc)} on {request.url.path}")
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": "Database Error",
            "message": "A database error occurred while processing your request.",
            "path": request.url.path
        }
    )

async def logging_middleware(request: Request, call_next):
    """
    Middleware to log every request and its execution time.
    """
    start_time = time.time()
    
    # Generate a request ID if needed (can use a library or just uuid)
    request_id = request.headers.get("X-Request-ID", "internal")
    
    log.info(f"START: {request.method} {request.url.path} - ID: {request_id}")
    
    try:
        response = await call_next(request)
        process_time = (time.time() - start_time) * 1000
        
        log.info(
            f"END: {request.method} {request.url.path} - "
            f"Status: {response.status_code} - "
            f"Time: {process_time:.2f}ms"
        )
        
        response.headers["X-Process-Time"] = f"{process_time:.2f}ms"
        return response
        
    except Exception as e:
        # Re-raise to be caught by global handlers
        raise e

def register_error_handlers(app):
    """Registers all exception handlers for the FastAPI application."""
    app.add_exception_handler(Exception, global_exception_handler)
    app.add_exception_handler(AppError, app_error_handler)
    app.add_exception_handler(RequestValidationError, validation_exception_handler)
    app.add_exception_handler(SQLAlchemyError, sqlalchemy_exception_handler)
    
    # Register middleware
    app.middleware("http")(logging_middleware)
