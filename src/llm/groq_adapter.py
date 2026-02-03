"""
Groq LLM adapter with YAML-based model configuration.
"""

from typing import Optional

from langchain_core.language_models import BaseChatModel
from langchain_groq import ChatGroq

from src.config import get_settings
from src.llm.model_registry import get_model_registry


class GroqAdapter:
    """Groq LLM adapter with YAML-based model configuration."""

    def __init__(self, model_id: Optional[str] = None):
        """
        Initialize Groq adapter.

        Args:
            model_id: Model ID from models.yaml (e.g., 'llama-3.3-70b')
                     If None, uses default from config.
        """
        settings = get_settings()
        registry = get_model_registry()

        # Use provided model or default
        model_id = model_id or registry.default_model
        model_config = registry.get_model(model_id)

        if not model_config:
            raise ValueError(f"Unknown model: {model_id}")

        if model_config.provider != "groq":
            raise ValueError(f"Model {model_id} is not a Groq model")

        self.config = model_config
        self.model = ChatGroq(
            api_key=settings.groq_api_key,
            model_name=model_config.model_id,
            temperature=0.1,
            max_retries=3,
        )

    def get_llm(self) -> BaseChatModel:
        """Get the underlying LangChain LLM."""
        return self.model

    async def generate(self, messages: list) -> str:
        """
        Generate a response from messages.

        Args:
            messages: List of message dicts or LangChain messages

        Returns:
            Generated response content
        """
        response = await self.model.ainvoke(messages)
        return response.content


def get_llm(model_id: Optional[str] = None) -> BaseChatModel:
    """
    Factory function for getting LLM instance.

    Args:
        model_id: Optional model ID

    Returns:
        LangChain BaseChatModel
    """
    return GroqAdapter(model_id).get_llm()
