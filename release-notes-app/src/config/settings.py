"""Configuration management for the release notes generator."""

import os
from typing import Optional


class AppConfig:
    """Application configuration settings."""
    
    def __init__(self):
        self.openai_endpoint = os.getenv(
            "ENDPOINT_URL", 
            "https://icm-enrichment-openai.openai.azure.com/"
        )
        self.deployment_name = os.getenv("DEPLOYMENT_NAME", "ICM-Enrichment-AI")
        self.search_endpoint = os.getenv(
            "SEARCH_ENDPOINT", 
            "https://tkishnani-search.search.windows.net"
        )
        self.default_semantic_config = "vector-1720899450481-semantic-configuration"
        self.api_version = "2024-05-01-preview"
    
    def get_search_index(self, semantic_config: str) -> str:
        """Extract search index name from semantic configuration."""
        return semantic_config.replace("-semantic-configuration", "")
    
    def get_semantic_config(self, documentation_config: Optional[str]) -> str:
        """Get semantic configuration, using default if none provided."""
        return documentation_config or self.default_semantic_config


# Global configuration instance
config = AppConfig()
