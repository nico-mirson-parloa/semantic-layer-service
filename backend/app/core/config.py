"""
Configuration management using Pydantic Settings
"""
from typing import Optional
from pydantic_settings import BaseSettings
from pydantic import Field, field_validator


class Settings(BaseSettings):
    """Application settings"""
    
    # Database - Not needed, everything in Databricks
    database_url: Optional[str] = Field(
        default=None,
        description="PostgreSQL connection string (not used)"
    )
    
    # Redis - Not needed, can cache in Databricks temp views
    redis_url: Optional[str] = Field(
        default=None,
        description="Redis connection string (not used)"
    )
    
    # Databricks
    databricks_host: Optional[str] = Field(
        default=None,
        description="Databricks workspace hostname (e.g., dbc-12345678-90ab.cloud.databricks.com)"
    )
    
    databricks_token: Optional[str] = Field(
        default=None,
        description="Databricks personal access token"
    )
    
    databricks_http_path: Optional[str] = Field(
        default=None,
        description="SQL warehouse HTTP path (e.g., /sql/1.0/warehouses/abcd1234efgh5678)"
    )
    
    # Optional direct warehouse id for Statements API; if not provided, we extract from http_path
    databricks_warehouse_id: Optional[str] = Field(
        default=None,
        description="Databricks SQL Warehouse ID; if not provided, extracted from DATABRICKS_HTTP_PATH"
    )
    
    databricks_genie_space_id: Optional[str] = Field(
        default=None,
        description="Databricks Genie space ID (from URL: /genie/rooms/<space_id>)"
    )
    
    # API Settings
    api_prefix: str = "/api"
    debug: bool = Field(default=False, description="Debug mode")
    
    # Semantic Models
    semantic_models_path: str = Field(
        default="./semantic-models",
        description="Path to semantic models directory (legacy - now using volumes)"
    )
    
    # Unity Catalog Volumes
    volume_base_path: str = Field(
        default="/Volumes/semantic_layer/metrics",
        description="Base path for Unity Catalog volumes storing metrics"
    )
    
    # Authentication
    secret_key: str = Field(
        default="your-secret-key-change-this-in-production",
        description="JWT secret key for authentication"
    )
    
    algorithm: str = Field(
        default="HS256",
        description="JWT algorithm"
    )
    
    access_token_expire_minutes: int = Field(
        default=30,
        description="JWT token expiration time in minutes"
    )
    
    # Slack Integration
    slack_webhook_url: Optional[str] = Field(
        default=None,
        description="Slack webhook URL for alerts and notifications"
    )
    
    @field_validator("databricks_host")
    @classmethod
    def validate_databricks_host(cls, v: Optional[str]) -> Optional[str]:
        """Validate Databricks host configuration"""
        if v:
            # Remove https:// prefix if present
            if v.startswith("https://"):
                return v[8:]
            elif v.startswith("http://"):
                return v[7:]
        return v

    # LLM Configuration
    enable_llm_analysis: bool = Field(
        default=True,
        description="Enable LLM-based table analysis for smarter metric suggestions"
    )
    
    databricks_foundation_model_endpoint: str = Field(
        default="databricks-llama-4-maverick",
        description="Databricks Foundation Model endpoint to use for analysis"
    )
    
    llm_analysis_timeout: int = Field(
        default=30,
        description="Timeout in seconds for LLM analysis requests"
    )

    # Lineage Cache Settings
    LINEAGE_CACHE_TTL_MINUTES: int = Field(
        default=15,
        description="Cache TTL in minutes for lineage queries"
    )

    LINEAGE_CACHE_MAX_SIZE: int = Field(
        default=1000,
        description="Maximum number of cache entries before eviction"
    )

    LINEAGE_CACHE_ENABLED: bool = Field(
        default=True,
        description="Enable lineage caching to reduce repeated Unity Catalog queries"
    )

    @property
    def warehouse_id(self) -> Optional[str]:
        """Return explicit warehouse id or extract it from HTTP path."""
        if self.databricks_warehouse_id:
            return self.databricks_warehouse_id
        if self.databricks_http_path and "/warehouses/" in self.databricks_http_path:
            try:
                parts = self.databricks_http_path.strip("/").split("/")
                idx = parts.index("warehouses")
                if idx + 1 < len(parts):
                    return parts[idx + 1]
            except Exception:
                return None
        return None
    
    class Config:
        env_file = [".env", "../.env"]  # Look in current dir and parent dir
        case_sensitive = False


# Create settings instance
settings = Settings()
