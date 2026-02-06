import sys
import logging
from loguru import logger
from datetime import datetime
from app.core.config import settings

class InterceptHandler(logging.Handler):
    """
    Default handler from python logging to intercept standard logging messages
    and redirect them to loguru.
    """
    def emit(self, record):
        try:
            level = logger.level(record.levelname).name
        except ValueError:
            level = record.levelno

        # Find caller from where originated the logged message
        frame, depth = logging.currentframe(), 2
        while frame.f_code.co_filename == logging.__file__:
            frame = frame.f_back
            depth += 1

        logger.opt(depth=depth, exception=record.exc_info).log(level, record.getMessage())

def setup_logging():
    """
    Configure logging with loguru.
    Includes intercepting standard library logging and formatting.
    """
    log_level = settings.LOG_LEVEL.upper()
    log_format = (
        "<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | "
        "<level>{level: <8}</level> | "
        "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - "
        "<level>{message}</level>"
    )

    # Remove default handlers
    logger.remove()

    # Add stdout handler
    logger.add(
        sys.stdout,
        level=log_level,
        format=log_format,
        enqueue=True, # Thread-safe
        backtrace=True,
        diagnose=True if log_level == "DEBUG" else False
    )

    # Optional: Add JSON file logging for production
    # logger.add(
    #     "logs/app.log",
    #     rotation="500 MB",
    #     retention="10 days",
    #     compression="zip",
    #     level=log_level,
    #     serialize=True, # JSON log format
    #     enqueue=True
    # )

    # Intercept standard library logging (e.g., from uvicorn, sqlalchemy)
    logging.basicConfig(handlers=[InterceptHandler()], level=0, force=True)
    
    # Specific libraries can be adjusted here
    for name in ["uvicorn", "uvicorn.error", "uvicorn.access", "sqlalchemy.engine"]:
        _logger = logging.getLogger(name)
        _logger.handlers = [InterceptHandler()]
        _logger.propagate = False

    return logger

# Initialize logger
log = logger
