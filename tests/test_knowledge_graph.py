"""
Tests for Phase 3: Knowledge Graph and Agent components.
"""


from src.knowledge_graph.extraction import (
    ExtractedEntity,
    ExtractedRelationship,
    ExtractionResult,
)
from src.knowledge_graph.tenant_graph import Entity, Relationship


class TestEntityModels:
    """Tests for entity and relationship models."""

    def test_entity_creation(self):
        """Test creating an Entity."""
        entity = Entity(
            id="test:person:john",
            name="John Doe",
            type="PERSON",
            properties={"description": "A test person"},
            tenant_id="tenant-123",
        )

        assert entity.id == "test:person:john"
        assert entity.name == "John Doe"
        assert entity.type == "PERSON"
        assert entity.tenant_id == "tenant-123"
        assert entity.properties["description"] == "A test person"

    def test_relationship_creation(self):
        """Test creating a Relationship."""
        rel = Relationship(
            source_id="entity-1",
            target_id="entity-2",
            type="WORKS_FOR",
            properties={"since": "2020"},
            tenant_id="tenant-123",
        )

        assert rel.source_id == "entity-1"
        assert rel.target_id == "entity-2"
        assert rel.type == "WORKS_FOR"
        assert rel.tenant_id == "tenant-123"


class TestExtractionModels:
    """Tests for extraction result models."""

    def test_extracted_entity(self):
        """Test ExtractedEntity creation."""
        entity = ExtractedEntity(
            name="OpenAI",
            type="ORGANIZATION",
            description="An AI research company",
        )

        assert entity.name == "OpenAI"
        assert entity.type == "ORGANIZATION"
        assert entity.description == "An AI research company"

    def test_extracted_relationship(self):
        """Test ExtractedRelationship creation."""
        rel = ExtractedRelationship(
            source="John",
            target="OpenAI",
            type="WORKS_FOR",
            description="John works at OpenAI",
        )

        assert rel.source == "John"
        assert rel.target == "OpenAI"
        assert rel.type == "WORKS_FOR"

    def test_extraction_result(self):
        """Test ExtractionResult with entities and relationships."""
        entities = [
            ExtractedEntity("John", "PERSON", "A developer"),
            ExtractedEntity("OpenAI", "ORGANIZATION", "AI company"),
        ]
        relationships = [
            ExtractedRelationship("John", "OpenAI", "WORKS_FOR", ""),
        ]

        result = ExtractionResult(
            entities=entities,
            relationships=relationships,
        )

        assert len(result.entities) == 2
        assert len(result.relationships) == 1
        assert result.entities[0].name == "John"
        assert result.relationships[0].source == "John"
