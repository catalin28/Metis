"""Configuration management for Metis."""

import os
from typing import Optional

from pydantic import Field
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings."""
    
    # API Keys
    fmp_api_key: str = Field(default="test_key", env="FMP_API_KEY")
    openai_api_key: str = Field(default="test_key", env="OPENAI_API_KEY")
    
    # Database
    database_url: str = Field(default="sqlite:///metis.db", env="DATABASE_URL")
    test_database_url: Optional[str] = Field(None, env="TEST_DATABASE_URL")
    
    # Redis
    redis_url: Optional[str] = Field("redis://localhost:6379/0", env="REDIS_URL")
    
    # OpenAI
    openai_project_id: Optional[str] = Field(None, env="OPENAI_PROJECT_ID")
    competitive_intel_assistant_id: Optional[str] = Field(None, env="COMPETITIVE_INTEL_ASSISTANT_ID")
    linguistic_analysis_assistant_id: Optional[str] = Field(None, env="LINGUISTIC_ANALYSIS_ASSISTANT_ID")
    
    # Competitive Intelligence
    competitive_intelligence_enabled: bool = Field(True, env="COMPETITIVE_INTELLIGENCE_ENABLED")
    max_peers_per_analysis: int = Field(5, env="MAX_PEERS_PER_ANALYSIS")
    min_market_cap_ratio: float = Field(0.3, env="MIN_MARKET_CAP_RATIO")
    max_market_cap_ratio: float = Field(3.0, env="MAX_MARKET_CAP_RATIO")
    parallel_company_limit: int = Field(6, env="PARALLEL_COMPANY_LIMIT")
    competitive_report_timeout: int = Field(600, env="COMPETITIVE_REPORT_TIMEOUT")
    
    # LLM Configuration
    llm_response_cache_enabled: bool = Field(True, env="LLM_RESPONSE_CACHE_ENABLED")
    llm_cache_ttl_days: int = Field(90, env="LLM_CACHE_TTL_DAYS")
    token_budget_per_client_monthly: int = Field(500000, env="TOKEN_BUDGET_PER_CLIENT_MONTHLY")
    
    # Storage
    store_comparative_history: bool = Field(True, env="STORE_COMPARATIVE_HISTORY")
    history_retention_months: int = Field(24, env="HISTORY_RETENTION_MONTHS")
    
    # API Configuration
    api_host: str = Field("0.0.0.0", env="API_HOST")
    api_port: int = Field(8000, env="API_PORT")
    api_workers: int = Field(4, env="API_WORKERS")
    
    # Security
    secret_key: str = Field(default="dev-secret-key-change-in-production", env="SECRET_KEY")
    api_key_header: str = Field("X-API-Key", env="API_KEY_HEADER")
    
    # Development
    debug: bool = Field(False, env="DEBUG")
    testing: bool = Field(False, env="TESTING")
    log_level: str = Field("INFO", env="LOG_LEVEL")
    
    model_config = {
        "env_file": ".env",
        "case_sensitive": False,
        "extra": "ignore"  # Ignore extra fields from .env
    }


settings = Settings()


def get_config():
    """Get application settings for backward compatibility."""
    return {
        'COMPETITIVE_INTELLIGENCE_ENABLED': settings.competitive_intelligence_enabled,
        'PARALLEL_COMPANY_LIMIT': settings.parallel_company_limit,
        'COMPETITIVE_INTEL_TIMEOUT_MINUTES': settings.competitive_report_timeout // 60,
        'MAX_PEERS_PER_ANALYSIS': settings.max_peers_per_analysis,
        'LLM_CACHE_ENABLED': settings.llm_response_cache_enabled,
        'TOKEN_BUDGET_PER_CLIENT_MONTHLY': settings.token_budget_per_client_monthly
    }