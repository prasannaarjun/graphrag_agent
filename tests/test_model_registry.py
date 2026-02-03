"""
Tests for Phase 2: Document Pipeline components.
"""


from src.llm.model_registry import get_model_registry


class TestModelRegistry:
    """Tests for model registry."""

    def test_load_models_from_yaml(self):
        """Test loading models from YAML config."""
        registry = get_model_registry()

        assert registry.default_model is not None
        assert registry.default_embedding is not None

    def test_get_model(self):
        """Test getting a model by ID."""
        registry = get_model_registry()

        model = registry.get_model("llama-3.3-70b")

        assert model is not None
        assert model.id == "llama-3.3-70b"
        assert model.provider == "groq"
        assert model.context_window > 0

    def test_get_embedding(self):
        """Test getting an embedding model by ID."""
        registry = get_model_registry()

        embedding = registry.get_embedding("minilm")

        assert embedding is not None
        assert embedding.id == "minilm"
        assert embedding.dimension == 384

    def test_list_models(self):
        """Test listing all models."""
        registry = get_model_registry()

        models = registry.list_models()

        assert len(models) > 0
        assert any(m.id == "llama-3.3-70b" for m in models)

    def test_list_embeddings(self):
        """Test listing all embeddings."""
        registry = get_model_registry()

        embeddings = registry.list_embeddings()

        assert len(embeddings) > 0
        assert any(e.id == "minilm" for e in embeddings)

    def test_get_default_model(self):
        """Test getting default model."""
        registry = get_model_registry()

        default = registry.get_default_model()

        assert default is not None
        assert default.id == registry.default_model
