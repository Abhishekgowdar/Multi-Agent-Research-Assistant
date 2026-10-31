"""Configuration management"""

import os
import yaml
from pathlib import Path
from typing import Dict, Any
from pydantic import BaseModel
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


class AgentConfig(BaseModel):
    """Configuration for an individual agent"""
    model: str
    max_retries: int = 3
    timeout: int = 30


class DataSourceConfig(BaseModel):
    """Configuration for a data source"""
    enabled: bool = True
    max_results: int = 50


class MemoryConfig(BaseModel):
    """Memory system configuration"""
    type: str = "chromadb"
    path: str = "./data/chroma_db"
    collection_name: str = "research_papers"


class Settings:
    """Application settings"""

    def __init__(self, config_path: str = None):
        if config_path is None:
            config_path = Path(__file__).parent.parent.parent / "config" / "settings.yaml"

        with open(config_path, 'r') as f:
            self.config = yaml.safe_load(f)

        # Environment variables
        self.llm_provider = os.getenv("LLM_PROVIDER", "groq").lower()
        self.gemini_api_key = os.getenv("GEMINI_API_KEY", "")
        self.groq_api_key = os.getenv("GROQ_API_KEY", "")
        self.pubmed_email = os.getenv("PUBMED_EMAIL", "")
        self.semantic_scholar_api_key = os.getenv("SEMANTIC_SCHOLAR_API_KEY", "")

        # Validate - need at least one API key
        if not self.gemini_api_key and not self.groq_api_key:
            raise ValueError("No LLM API key found! Set either GEMINI_API_KEY or GROQ_API_KEY in .env")

    def get_agent_config(self, agent_name: str) -> AgentConfig:
        """Get configuration for a specific agent"""
        agent_cfg = self.config.get('agents', {}).get(agent_name, {})
        return AgentConfig(**agent_cfg)

    def get_data_source_config(self, source_name: str) -> DataSourceConfig:
        """Get configuration for a data source"""
        source_cfg = self.config.get('data_sources', {}).get(source_name, {})
        return DataSourceConfig(**source_cfg)

    def get_memory_config(self) -> MemoryConfig:
        """Get memory configuration"""
        memory_cfg = self.config.get('memory', {}).get('vector_db', {})
        return MemoryConfig(**memory_cfg)

    def get(self, key: str, default: Any = None) -> Any:
        """Get any configuration value"""
        keys = key.split('.')
        value = self.config
        for k in keys:
            if isinstance(value, dict):
                value = value.get(k, default)
            else:
                return default
        return value


# Global settings instance
settings = Settings()
