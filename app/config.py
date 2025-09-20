"""
Configuration module for CVS Rebate Analytics Backend
Centralizes environment variable management and data source configuration
"""

import os
from typing import Literal, List
from dotenv import load_dotenv

# Load environment variables with priority:
# 1. System environment variables (production/CI)
# 2. .env.{environment} file (if exists)  
# 3. .env file (local development)
# 4. Default values

# Load base .env file first
load_dotenv()

# Load environment-specific .env file if it exists
env_name = os.getenv('APP_ENVIRONMENT', 'development')
env_file = f".env.{env_name}"
if os.path.exists(env_file):
    load_dotenv(env_file, override=True)


class Config:
    """Application configuration"""
    
    # ===== APPLICATION CONFIGURATION =====
    APP_NAME: str = os.getenv('APP_NAME', 'PSS Knowledge Assist')
    APP_VERSION: str = os.getenv('APP_VERSION', '1.0.0')
    
    # Environment: development (local), test (docker/GKE), production (docker/GKE)
    APP_ENVIRONMENT: Literal['development', 'test', 'production'] = os.getenv('APP_ENVIRONMENT', 'development')
    
    PORT: int = int(os.getenv('PORT', '8000'))
    LOG_LEVEL: str = os.getenv('LOG_LEVEL', 'INFO')
    
    
    # ===== GOOGLE CLOUD CONFIGURATION =====
    GCP_PROJECT_ID: str = os.getenv('GCP_PROJECT_ID', 'pbm-dev-careassist-genai-poc')
    
    # Gemini Data Analytics API Configuration
    BILLING_PROJECT: str = os.getenv('BILLING_PROJECT', 'pbm-dev-careassist-genai-poc')
    LOCATION: str = os.getenv('LOCATION', 'global')
    BASE_URL: str = os.getenv('BASE_URL', 'https://geminidataanalytics.googleapis.com')
    
    # BigQuery Database Configuration
    BQ_DATASET: str = os.getenv('BQ_DATASET', 'RebateExposure')
    BQ_TABLE: str = os.getenv('BQ_TABLE', 'RebateExposure')
    
    # ===== DATABASE CONFIGURATION =====
    # PostgreSQL Configuration (GKE-based)
    DB_HOST: str = os.getenv('DB_HOST', 'postgres-service')  # GKE cluster IP
    DB_PORT: int = int(os.getenv('DB_PORT', '5432'))
    DB_USER: str = os.getenv('DB_USER', 'postgres')
    DB_PASSWORD: str = os.getenv('DB_PASSWORD', 'password')
    
    @property
    def database_name(self) -> str:
        """Get database name based on environment"""        
        # Environment-based database selection for PSS Knowledge Assist
        if self.APP_ENVIRONMENT == 'production':
            return os.getenv('PROD_DB_NAME', 'pss_knowledge_assist_prod')
        elif self.APP_ENVIRONMENT == 'test':
            return os.getenv('TEST_DB_NAME', 'pss_knowledge_assist_test')
        elif self.APP_ENVIRONMENT == 'development':
            return os.getenv('DEV_DB_NAME', 'pss_knowledge_assist_dev')
        else:
            # Fallback to development database for unknown environments
            return os.getenv('DEV_DB_NAME', 'pss_knowledge_assist_dev')

    
    # Database connection settings
    DB_ECHO: bool = os.getenv('DB_ECHO', 'false').lower() == 'true'  # SQL logging
    DB_POOL_SIZE: int = int(os.getenv('DB_POOL_SIZE', '5'))
    DB_MAX_OVERFLOW: int = int(os.getenv('DB_MAX_OVERFLOW', '10'))
    DB_POOL_TIMEOUT: int = int(os.getenv('DB_POOL_TIMEOUT', '30'))
    DB_POOL_RECYCLE: int = int(os.getenv('DB_POOL_RECYCLE', '3600'))  # Recycle connections after seconds
    DB_POOL_PRE_PING: bool = os.getenv('DB_POOL_PRE_PING', 'true').lower() == 'true'  # Verify connections before use
    
    # Security Configuration
    SECRET_KEY: str = os.getenv('SECRET_KEY', 'your-super-secret-key-change-this-in-production')
    ACCESS_TOKEN_EXPIRE_MINUTES: int = int(os.getenv('ACCESS_TOKEN_EXPIRE_MINUTES', '30'))
    REFRESH_TOKEN_EXPIRE_DAYS: int = int(os.getenv('REFRESH_TOKEN_EXPIRE_DAYS', '7'))
    
    # ===== CACHE CONFIGURATION =====
    # Cache settings for message results and chart data
    CACHE_ENABLED: bool = os.getenv('CACHE_ENABLED', 'true').lower() == 'true'
    CACHE_TTL_SECONDS: int = int(os.getenv('CACHE_TTL_SECONDS', '1800'))  # 30 minutes default
    CACHE_MAX_SIZE_MB: int = int(os.getenv('CACHE_MAX_SIZE_MB', '100'))  # 100MB max cache size
    CACHE_CLEANUP_INTERVAL: int = int(os.getenv('CACHE_CLEANUP_INTERVAL', '300'))  # Cleanup every 5 minutes
    
    @property
    def database_url(self) -> str:
        """Get the appropriate database URL based on environment"""
        db_name = self.database_name
        return f"postgresql+asyncpg://{self.DB_USER}:{self.DB_PASSWORD}@{self.DB_HOST}:{self.DB_PORT}/{db_name}"
    
    @property
    def sync_database_url(self) -> str:
        """Get synchronous database URL for Alembic migrations"""
        db_name = self.database_name
        return f"postgresql://{self.DB_USER}:{self.DB_PASSWORD}@{self.DB_HOST}:{self.DB_PORT}/{db_name}"
    
    def get_database_info(self) -> dict:
        """Get current database configuration info for debugging"""
        return {
            'environment': self.APP_ENVIRONMENT,
            'database_name': self.database_name,
            'host': self.DB_HOST,
            'port': self.DB_PORT,
            'database_url_preview': self.database_url.replace(self.DB_PASSWORD, '***')
        }
    
    def get_config_info(self) -> dict:
        """Get configuration loading information for debugging"""
        env_name = os.getenv('APP_ENVIRONMENT', 'development')
        env_file = f".env.{env_name}"
        
        return {
            'environment': self.APP_ENVIRONMENT,
            'config_sources': {
                'base_env_file': '.env' if os.path.exists('.env') else 'Not found',
                'environment_specific_file': env_file if os.path.exists(env_file) else 'Not found',
                'system_env_vars': 'Available',
            },
            'database_config': self.get_database_info()
        }
    
    # CORS Configuration
    CORS_ORIGINS: List[str] = os.getenv('CORS_ORIGINS', 'http://localhost:3000,http://localhost:8080').split(',')
    CORS_ALLOW_CREDENTIALS: bool = os.getenv('CORS_ALLOW_CREDENTIALS', 'true').lower() == 'true'
    

# Export configuration instance
config = Config() 