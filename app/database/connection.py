"""
Database connection management with async PostgreSQL support
Handles both local development and GKE production connections
"""

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import declarative_base
from sqlalchemy import text
from contextlib import asynccontextmanager
import logging
from typing import AsyncGenerator
from ..config import config

logger = logging.getLogger(__name__)

# SQLAlchemy setup
Base = declarative_base()
engine = None
async_session_factory = None


async def init_database():
    """Initialize database connection and session factory"""
    global engine, async_session_factory
    
    try:
        # Get database URL from config (handles environment-based database selection)
        database_url = config.database_url
        
        logger.info(f"Initializing database connection...")
        db_info = config.get_database_info()
        logger.info(f"Environment: {db_info['environment']}, Database: {db_info['database_name']}")
        
        # Create async engine with connection pooling
        engine = create_async_engine(
            database_url,
            echo=config.DB_ECHO,  # Set to True for SQL logging in development
            pool_size=config.DB_POOL_SIZE,
            max_overflow=config.DB_MAX_OVERFLOW,
            pool_pre_ping=config.DB_POOL_PRE_PING,  # Verify connections before use
            pool_recycle=config.DB_POOL_RECYCLE,   # Recycle connections after specified seconds
            pool_timeout=config.DB_POOL_TIMEOUT,
            connect_args={
                "server_settings": {
                    "application_name": "ca-rebates-tool",
                }
            }
        )
        
        # Create session factory
        async_session_factory = async_sessionmaker(
            engine,
            class_=AsyncSession,
            expire_on_commit=False,
            autoflush=True,
            autocommit=False
        )
        
        # Test the connection
        await test_connection()
        
        logger.info("Database connection initialized successfully")
        
    except Exception as e:
        logger.error(f"Failed to initialize database connection: {e}")
        raise


async def test_connection():
    """Test database connectivity"""
    if not engine:
        raise RuntimeError("Database engine not initialized")
    
    try:
        async with engine.begin() as conn:
            # Simple query to test connection
            result = await conn.execute(text("SELECT 1 as test"))
            row = result.fetchone()
            if row and row.test == 1:
                logger.info("Database connection test successful")
                return True
            else:
                logger.error("Database connection test failed - unexpected result")
                return False
                
    except Exception as e:
        logger.error(f"Database connection test failed: {e}")
        raise


@asynccontextmanager
async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    """
    Get database session with proper error handling and cleanup
    
    Usage:
        async with get_db_session() as session:
            # Your database operations here
            result = await session.execute(select(User))
    """
    if not async_session_factory:
        raise RuntimeError("Database not initialized. Call init_database() first.")
    
    async with async_session_factory() as session:
        try:
            logger.debug("Database session created")
            yield session
            await session.commit()
            logger.debug("Database transaction committed")
            
        except Exception as e:
            logger.error(f"Database transaction failed, rolling back: {e}")
            await session.rollback()
            raise
            
        finally:
            await session.close()
            logger.debug("Database session closed")


async def get_db_session_dependency():
    """
    FastAPI dependency for database sessions
    
    Usage in routes:
        async def my_route(db: AsyncSession = Depends(get_db_session_dependency)):
            # Your database operations here
    """
    async with get_db_session() as session:
        yield session


async def close_database():
    """Close database connections and cleanup"""
    global engine, async_session_factory
    
    try:
        if engine:
            await engine.dispose()
            logger.info("Database connections closed")
        
        engine = None
        async_session_factory = None
        
    except Exception as e:
        logger.error(f"Error closing database connections: {e}")


async def get_database_info():
    """Get database connection information for health checks"""
    if not engine:
        return {
            "status": "disconnected",
            "error": "Database engine not initialized"
        }
    
    try:
        async with engine.begin() as conn:
            # Get database version and connection info
            version_result = await conn.execute(text("SELECT version()"))
            version = version_result.scalar()
            
            # Get current database name
            db_result = await conn.execute(text("SELECT current_database()"))
            database_name = db_result.scalar()
            
            # Get connection count (if user has permissions)
            try:
                conn_result = await conn.execute(
                    text("SELECT count(*) FROM pg_stat_activity WHERE datname = current_database()")
                )
                active_connections = conn_result.scalar()
            except Exception:
                active_connections = "N/A (insufficient permissions)"
            
            return {
                "status": "connected",
                "database_name": database_name,
                "version": version,
                "active_connections": active_connections,
                "pool_size": config.DB_POOL_SIZE,
                "max_overflow": config.DB_MAX_OVERFLOW,
                "pool_timeout": config.DB_POOL_TIMEOUT,
                "pool_recycle": config.DB_POOL_RECYCLE,
                "pool_pre_ping": config.DB_POOL_PRE_PING,
                "environment": config.APP_ENVIRONMENT
            }
            
    except Exception as e:
        return {
            "status": "error",
            "error": str(e)
        }


# Health check function for monitoring
async def health_check() -> dict:
    """Perform database health check"""
    try:
        start_time = __import__('time').time()
        await test_connection()
        response_time = (__import__('time').time() - start_time) * 1000  # Convert to milliseconds
        
        db_info = await get_database_info()
        
        return {
            "healthy": True,
            "response_time_ms": round(response_time, 2),
            "database_info": db_info
        }
        
    except Exception as e:
        return {
            "healthy": False,
            "error": str(e),
            "database_info": await get_database_info()
        }


def get_async_engine():
    """Get the async database engine"""
    global engine
    if not engine:
        raise RuntimeError("Database engine not initialized. Call init_database() first.")
    return engine
