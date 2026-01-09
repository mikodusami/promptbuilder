"""
LLM Client - Unified interface for multiple LLM providers.
"""

from typing import Optional, AsyncGenerator
from dataclasses import dataclass
import asyncio

from api_config import APIConfig, ProviderConfig


@dataclass
class LLMResponse:
    content: str
    model: str
    provider: str
    input_tokens: int = 0
    output_tokens: int = 0
    error: Optional[str] = None


class LLMClient:
    """Unified client for OpenAI, Anthropic, and Google APIs."""

    def __init__(self, config: APIConfig = None):
        self.config = config or APIConfig()
        self._clients = {}

    def _get_openai_client(self):
        """Get or create OpenAI client."""
        if "openai" not in self._clients:
            try:
                from openai import OpenAI
                provider = self.config.get_provider("openai")
                if provider and provider.api_key:
                    self._clients["openai"] = OpenAI(
                        api_key=provider.api_key,
                        base_url=provider.base_url
                    )
            except ImportError:
                pass
        return self._clients.get("openai")

    def _get_anthropic_client(self):
        """Get or create Anthropic client."""
        if "anthropic" not in self._clients:
            try:
                from anthropic import Anthropic
                provider = self.config.get_provider("anthropic")
                if provider and provider.api_key:
                    self._clients["anthropic"] = Anthropic(
                        api_key=provider.api_key
                    )
            except ImportError:
                pass
        return self._clients.get("anthropic")

    def _get_google_client(self):
        """Get or create Google client."""
        if "google" not in self._clients:
            try:
                import google.generativeai as genai
                provider = self.config.get_provider("google")
                if provider and provider.api_key:
                    genai.configure(api_key=provider.api_key)
                    self._clients["google"] = genai
            except ImportError:
                pass
        return self._clients.get("google")

    async def complete(
        self,
        prompt: str,
        provider: str = None,
        model: str = None,
        system_prompt: str = None,
        max_tokens: int = 4096,
        temperature: float = 0.7
    ) -> LLMResponse:
        """Send a completion request to the specified provider."""
        
        # Auto-select provider if not specified
        if not provider:
            available = self.config.get_available_providers()
            if not available:
                return LLMResponse(
                    content="",
                    model="",
                    provider="",
                    error="No API keys configured. Set OPENAI_API_KEY, ANTHROPIC_API_KEY, or GOOGLE_API_KEY."
                )
            provider = available[0]

        # Auto-select model if not specified
        if not model:
            provider_config = self.config.get_provider(provider)
            if provider_config and provider_config.models:
                model = provider_config.models[0]

        try:
            if provider == "openai":
                return await self._complete_openai(prompt, model, system_prompt, max_tokens, temperature)
            elif provider == "anthropic":
                return await self._complete_anthropic(prompt, model, system_prompt, max_tokens, temperature)
            elif provider == "google":
                return await self._complete_google(prompt, model, system_prompt, max_tokens, temperature)
            else:
                return LLMResponse(content="", model=model, provider=provider, error=f"Unknown provider: {provider}")
        except Exception as e:
            return LLMResponse(content="", model=model, provider=provider, error=str(e))

    async def _complete_openai(self, prompt: str, model: str, system_prompt: str, max_tokens: int, temperature: float) -> LLMResponse:
        """Complete using OpenAI API."""
        client = self._get_openai_client()
        if not client:
            return LLMResponse(content="", model=model, provider="openai", error="OpenAI client not available. Install: pip install openai")

        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        response = await asyncio.to_thread(
            client.chat.completions.create,
            model=model,
            messages=messages,
            max_tokens=max_tokens,
            temperature=temperature
        )

        return LLMResponse(
            content=response.choices[0].message.content,
            model=model,
            provider="openai",
            input_tokens=response.usage.prompt_tokens if response.usage else 0,
            output_tokens=response.usage.completion_tokens if response.usage else 0
        )

    async def _complete_anthropic(self, prompt: str, model: str, system_prompt: str, max_tokens: int, temperature: float) -> LLMResponse:
        """Complete using Anthropic API."""
        client = self._get_anthropic_client()
        if not client:
            return LLMResponse(content="", model=model, provider="anthropic", error="Anthropic client not available. Install: pip install anthropic")

        kwargs = {
            "model": model,
            "max_tokens": max_tokens,
            "messages": [{"role": "user", "content": prompt}]
        }
        if system_prompt:
            kwargs["system"] = system_prompt

        response = await asyncio.to_thread(
            client.messages.create,
            **kwargs
        )

        return LLMResponse(
            content=response.content[0].text,
            model=model,
            provider="anthropic",
            input_tokens=response.usage.input_tokens if response.usage else 0,
            output_tokens=response.usage.output_tokens if response.usage else 0
        )

    async def _complete_google(self, prompt: str, model: str, system_prompt: str, max_tokens: int, temperature: float) -> LLMResponse:
        """Complete using Google Gemini API."""
        genai = self._get_google_client()
        if not genai:
            return LLMResponse(content="", model=model, provider="google", error="Google client not available. Install: pip install google-generativeai")

        full_prompt = f"{system_prompt}\n\n{prompt}" if system_prompt else prompt
        
        gen_model = genai.GenerativeModel(model)
        response = await asyncio.to_thread(
            gen_model.generate_content,
            full_prompt,
            generation_config=genai.types.GenerationConfig(
                max_output_tokens=max_tokens,
                temperature=temperature
            )
        )

        return LLMResponse(
            content=response.text,
            model=model,
            provider="google",
            input_tokens=0,  # Gemini doesn't always return token counts
            output_tokens=0
        )

    def get_available_models_for_provider(self, provider: str) -> list[str]:
        """Get available models for a specific provider."""
        provider_config = self.config.get_provider(provider)
        if provider_config and provider_config.is_available:
            return provider_config.models
        return []
