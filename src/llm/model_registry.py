"""
Model registry for loading LLM and embedding models from YAML configuration.
"""

from dataclasses import dataclass, field
from functools import lru_cache
from pathlib import Path
from typing import Optional

import yaml


@dataclass
class ModelConfig:
    """Configuration for an LLM model."""

    id: str
    name: str
    model_id: str
    context_window: int
    description: str
    provider: str
    recommended: bool = False


@dataclass
class EmbeddingConfig:
    """Configuration for an embedding model."""

    id: str
    name: str
    model_id: str
    dimension: int
    description: str
    recommended: bool = False


@dataclass
class ModelRegistry:
    """Registry for managing LLM and embedding models."""

    default_model: str = ""
    default_embedding: str = ""
    _models: dict[str, ModelConfig] = field(default_factory=dict)
    _embeddings: dict[str, EmbeddingConfig] = field(default_factory=dict)

    def __post_init__(self):
        """Load models from YAML on initialization."""
        self._load_from_yaml()

    def _load_from_yaml(self) -> None:
        """Load model configurations from YAML file."""
        # Try multiple paths
        config_paths = [
            Path("config/models.yaml"),
            Path(__file__).parent.parent.parent / "config" / "models.yaml",
        ]

        config_path = None
        for path in config_paths:
            if path.exists():
                config_path = path
                break

        if not config_path:
            # Use defaults if no config file found
            self.default_model = "llama-3.3-70b"
            self.default_embedding = "minilm"
            return

        with open(config_path) as f:
            config = yaml.safe_load(f)

        self.default_model = config.get("default_model", "llama-3.3-70b")
        self.default_embedding = config.get("default_embedding", "minilm")

        # Load provider models
        providers = config.get("providers", {})
        for provider_name, provider_config in providers.items():
            for model_data in provider_config.get("models", []):
                model = ModelConfig(
                    id=model_data["id"],
                    name=model_data["name"],
                    model_id=model_data["model_id"],
                    context_window=model_data["context_window"],
                    description=model_data["description"],
                    provider=provider_name,
                    recommended=model_data.get("recommended", False),
                )
                self._models[model.id] = model

        # Load embeddings
        for emb_data in config.get("embeddings", []):
            embedding = EmbeddingConfig(
                id=emb_data["id"],
                name=emb_data["name"],
                model_id=emb_data["model_id"],
                dimension=emb_data["dimension"],
                description=emb_data["description"],
                recommended=emb_data.get("recommended", False),
            )
            self._embeddings[embedding.id] = embedding

    def get_model(self, model_id: str) -> Optional[ModelConfig]:
        """Get model configuration by ID."""
        return self._models.get(model_id)

    def get_embedding(self, embedding_id: str) -> Optional[EmbeddingConfig]:
        """Get embedding configuration by ID."""
        return self._embeddings.get(embedding_id)

    def list_models(self) -> list[ModelConfig]:
        """List all available models."""
        return list(self._models.values())

    def list_embeddings(self) -> list[EmbeddingConfig]:
        """List all available embeddings."""
        return list(self._embeddings.values())

    def get_default_model(self) -> Optional[ModelConfig]:
        """Get the default model configuration."""
        return self.get_model(self.default_model)

    def get_default_embedding(self) -> Optional[EmbeddingConfig]:
        """Get the default embedding configuration."""
        return self.get_embedding(self.default_embedding)


@lru_cache
def get_model_registry() -> ModelRegistry:
    """Get singleton model registry instance."""
    return ModelRegistry()
