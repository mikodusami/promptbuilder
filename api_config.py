"""
API Configuration - Manage LLM provider API keys and settings.
Users supply their own keys via environment variables or config file.
"""

import os
from pathlib import Path
from dataclasses import dataclass, field
from typing import Optional
import json

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass


@dataclass
class ProviderConfig:
    name: str
    api_key: Optional[str]
    base_url: Optional[str] = None
    models: list[str] = field(default_factory=list)
    is_available: bool = False


class APIConfig:
    """Manage API keys for multiple LLM providers."""
    
    CONFIG_PATH = Path.home() / ".promptbuilder" / "api_config.json"
    
    PROVIDERS = {
        "openai": {
            "env_key": "OPENAI_API_KEY",
            "models": ["gpt-4o", "gpt-4o-mini", "gpt-4-turbo", "gpt-3.5-turbo"],
            "base_url": None
        },
        "anthropic": {
            "env_key": "ANTHROPIC_API_KEY",
            "models": ["claude-3-5-sonnet-20241022", "claude-3-opus-20240229", "claude-3-haiku-20240307"],
            "base_url": None
        },
        "google": {
            "env_key": "GOOGLE_API_KEY",
            "models": ["gemini-1.5-pro", "gemini-1.5-flash", "gemini-pro"],
            "base_url": None
        }
    }

    def __init__(self):
        self.providers: dict[str, ProviderConfig] = {}
        self._load_config()

    def _load_config(self):
        """Load API keys from environment and config file."""
        # Load from config file first
        file_config = {}
        if self.CONFIG_PATH.exists():
            try:
                with open(self.CONFIG_PATH) as f:
                    file_config = json.load(f)
            except Exception:
                pass

        # Initialize providers
        for name, info in self.PROVIDERS.items():
            # Priority: env var > config file
            api_key = os.getenv(info["env_key"]) or file_config.get(name, {}).get("api_key")
            base_url = file_config.get(name, {}).get("base_url") or info["base_url"]
            
            self.providers[name] = ProviderConfig(
                name=name,
                api_key=api_key,
                base_url=base_url,
                models=info["models"],
                is_available=bool(api_key)
            )

    def save_config(self):
        """Save current config to file."""
        self.CONFIG_PATH.parent.mkdir(parents=True, exist_ok=True)
        
        config = {}
        for name, provider in self.providers.items():
            if provider.api_key:
                config[name] = {
                    "api_key": provider.api_key,
                    "base_url": provider.base_url
                }
        
        with open(self.CONFIG_PATH, 'w') as f:
            json.dump(config, f, indent=2)

    def set_api_key(self, provider: str, api_key: str, base_url: str = None):
        """Set API key for a provider."""
        if provider not in self.providers:
            raise ValueError(f"Unknown provider: {provider}")
        
        self.providers[provider].api_key = api_key
        self.providers[provider].is_available = bool(api_key)
        if base_url:
            self.providers[provider].base_url = base_url
        
        self.save_config()

    def get_available_providers(self) -> list[str]:
        """Get list of providers with valid API keys."""
        return [name for name, p in self.providers.items() if p.is_available]

    def get_available_models(self) -> list[tuple[str, str]]:
        """Get all available models as (provider, model) tuples."""
        models = []
        for name, provider in self.providers.items():
            if provider.is_available:
                for model in provider.models:
                    models.append((name, model))
        return models

    def get_provider(self, name: str) -> Optional[ProviderConfig]:
        """Get provider config by name."""
        return self.providers.get(name)

    def has_any_provider(self) -> bool:
        """Check if at least one provider is configured."""
        return any(p.is_available for p in self.providers.values())
