from dataclasses import dataclass

@dataclass
class Config:
    db_path: str = "final_working_database.db"
    sqlite_path: str = "sqlite:///final_working_database.db"
    sonnet_model: str = "claude-3-sonnet-20240229"
    haiku_model: str = "claude-3-haiku-20240307"
    api_key: str = ""  # Anthropic API key
    cache_enabled: bool = True
    cache_dir: str = ".cache"
    cache_ttl: int = 86400  # Cache TTL in seconds (24 hours)

class ConfigError(Exception):
    """Custom exception for configuration errors"""
    pass 