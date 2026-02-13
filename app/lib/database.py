import urllib
from typing import Generator
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session, declarative_base
from sqlalchemy.engine import Engine
from loguru import logger as log
from app.core.config import settings

class DatabaseManager:
    """
    Singleton Database Manager for MSSQL using SQLAlchemy.
    Provides connection pooling and session management.
    """
    _instance = None
    _engine: Engine = None
    _SessionFactory = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(DatabaseManager, cls).__new__(cls)
            cls._instance._initialize()
        return cls._instance

    def _initialize(self):
        # Database connection details
        driver = settings.DB_DRIVER
        server = settings.DB_SERVER
        database = settings.DB_NAME
        user = settings.DB_USER
        password = settings.DB_PASSWORD
        port = settings.DB_PORT

        # Connection pooling settings
        pool_size = settings.DB_POOL_SIZE
        max_overflow = settings.DB_MAX_OVERFLOW
        pool_recycle = settings.DB_POOL_RECYCLE
        pool_pre_ping = settings.DB_POOL_PRE_PING

        quoted_password = urllib.parse.quote_plus(password)
        
        connection_url = (
            f"mssql+pyodbc://{user}:{quoted_password}@{server}:{port}/{database}"
            f"?driver={driver}&Encrypt=yes&TrustServerCertificate=no"
        )

        try:
            self._engine = create_engine(
                connection_url,
                pool_size=pool_size,
                max_overflow=max_overflow,
                pool_recycle=pool_recycle,
                pool_pre_ping=pool_pre_ping,
                # pool_timeout=30, # Default is 30
                echo=False # Set to True for debugging SQL queries
            )
            
            self._SessionFactory = sessionmaker(
                bind=self._engine,
                autocommit=False,
                autoflush=False
            )
            
            log.info(f"Successfully initialized DB engine for {server}")
        except Exception as e:
            log.error(f"Error initializing database engine: {str(e)}")
            raise e

    def get_session(self) -> Session:
        """Returns a new session object."""
        if self._SessionFactory is None:
            raise Exception("Database Manager not initialized.")
        return self._SessionFactory()

    @property
    def engine(self) -> Engine:
        return self._engine

Base = declarative_base()

# Global instance
db_manager = DatabaseManager()

def get_db() -> Generator[Session, None, None]:
    """
    Dependency helper to get a DB session. 
    Use with FastAPI: Depends(get_db)
    """
    db = db_manager.get_session()
    try:
        yield db
    finally:
        db.close()
