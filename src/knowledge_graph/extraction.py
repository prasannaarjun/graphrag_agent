"""
Entity extraction from documents using LLM.
"""

import json
import re
from dataclasses import dataclass
from typing import Optional

from langchain_core.messages import HumanMessage, SystemMessage

from src.llm import get_llm


@dataclass
class ExtractedEntity:
    """An entity extracted from text."""

    name: str
    type: str
    description: str


@dataclass
class ExtractedRelationship:
    """A relationship extracted from text."""

    source: str
    target: str
    type: str
    description: str


@dataclass
class ExtractionResult:
    """Result of entity extraction."""

    entities: list[ExtractedEntity]
    relationships: list[ExtractedRelationship]


EXTRACTION_SYSTEM_PROMPT = """You are an expert at extracting entities and relationships from text.

Extract the following types of entities:
- PERSON: People, individuals, characters
- ORGANIZATION: Companies, institutions, groups
- LOCATION: Places, cities, countries
- CONCEPT: Ideas, theories, methodologies
- TECHNOLOGY: Tools, frameworks, systems
- EVENT: Historical events, meetings, occurrences
- PRODUCT: Products, services, offerings

For each entity, provide:
- name: The entity name as it appears
- type: One of the types above
- description: Brief description based on context

For relationships, identify how entities relate:
- source: Source entity name
- target: Target entity name
- type: Relationship type (e.g., WORKS_FOR, LOCATED_IN, CREATED, USES, etc.)
- description: Brief description of the relationship

Return your response as JSON:
{
  "entities": [{"name": "...", "type": "...", "description": "..."}],
  "relationships": [{"source": "...", "target": "...", "type": "...", "description": "..."}]
}

Focus on the most important and clearly stated entities and relationships.
Limit to 10 entities and 10 relationships per chunk."""


class EntityExtractor:
    """
    Extract entities and relationships from text using LLM.
    """

    def __init__(self, model_id: Optional[str] = None):
        """
        Initialize extractor.

        Args:
            model_id: LLM model ID for extraction
        """
        self.llm = get_llm(model_id)

    async def extract(self, text: str) -> ExtractionResult:
        """
        Extract entities and relationships from text.

        Args:
            text: Text to extract from

        Returns:
            ExtractionResult with entities and relationships
        """
        messages = [
            SystemMessage(content=EXTRACTION_SYSTEM_PROMPT),
            HumanMessage(content=f"Extract entities and relationships from this text:\n\n{text}"),
        ]

        response = await self.llm.ainvoke(messages)
        content = response.content

        # Parse JSON from response
        try:
            # Try to find JSON in the response
            json_match = re.search(r"\{[\s\S]*\}", content)
            if json_match:
                data = json.loads(json_match.group())
            else:
                return ExtractionResult(entities=[], relationships=[])
        except json.JSONDecodeError:
            return ExtractionResult(entities=[], relationships=[])

        # Parse entities
        entities = []
        for e in data.get("entities", []):
            if all(k in e for k in ["name", "type"]):
                entities.append(
                    ExtractedEntity(
                        name=e["name"],
                        type=e["type"].upper(),
                        description=e.get("description", ""),
                    )
                )

        # Parse relationships
        relationships = []
        for r in data.get("relationships", []):
            if all(k in r for k in ["source", "target", "type"]):
                relationships.append(
                    ExtractedRelationship(
                        source=r["source"],
                        target=r["target"],
                        type=r["type"].upper().replace(" ", "_"),
                        description=r.get("description", ""),
                    )
                )

        return ExtractionResult(
            entities=entities,
            relationships=relationships,
        )

    async def extract_and_store(
        self,
        text: str,
        doc_id: str,
        graph_client,
    ) -> ExtractionResult:
        """
        Extract entities/relationships and store in graph.

        Args:
            text: Text to extract from
            doc_id: Source document ID
            graph_client: TenantGraphClient instance

        Returns:
            ExtractionResult
        """
        result = await self.extract(text)

        # Create entities in graph
        entity_map = {}
        for entity in result.entities:
            created = await graph_client.create_entity(
                name=entity.name,
                entity_type=entity.type,
                properties={"description": entity.description},
                doc_id=doc_id,
            )
            entity_map[entity.name] = created.id

        # Create relationships
        for rel in result.relationships:
            source_id = entity_map.get(rel.source)
            target_id = entity_map.get(rel.target)

            if source_id and target_id:
                await graph_client.create_relationship(
                    source_id=source_id,
                    target_id=target_id,
                    relationship_type=rel.type,
                    properties={"description": rel.description},
                )

        return result


def get_entity_extractor(model_id: Optional[str] = None) -> EntityExtractor:
    """Get entity extractor instance."""
    return EntityExtractor(model_id)
