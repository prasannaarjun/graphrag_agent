"""
Neo4j client for tenant-isolated knowledge graph operations.
"""

from dataclasses import dataclass
from typing import Any, Optional

from neo4j import AsyncDriver, AsyncGraphDatabase

from src.config import get_settings
from src.core.tenant import TenantContext


@dataclass
class Entity:
    """An entity in the knowledge graph."""

    id: str
    name: str
    type: str
    properties: dict[str, Any]
    tenant_id: str


@dataclass
class Relationship:
    """A relationship between entities."""

    source_id: str
    target_id: str
    type: str
    properties: dict[str, Any]
    tenant_id: str


class TenantGraphClient:
    """
    Neo4j client with tenant-level isolation.

    All entities and relationships are tagged with tenant_id
    and queries are automatically scoped to the current tenant.
    """

    _driver: Optional[AsyncDriver] = None

    def __init__(self):
        settings = get_settings()
        self.uri = settings.neo4j_uri
        self.username = settings.neo4j_user
        self.password = settings.neo4j_password

    async def _get_driver(self) -> AsyncDriver:
        """Get or create the Neo4j driver."""
        if TenantGraphClient._driver is None:
            TenantGraphClient._driver = AsyncGraphDatabase.driver(
                self.uri,
                auth=(self.username, self.password),
            )
        return TenantGraphClient._driver

    def _get_tenant_id(self) -> str:
        """Get current tenant ID from context."""
        return TenantContext.get_current().tenant_id

    async def close(self) -> None:
        """Close the Neo4j driver."""
        if TenantGraphClient._driver:
            await TenantGraphClient._driver.close()
            TenantGraphClient._driver = None

    async def create_entity(
        self,
        name: str,
        entity_type: str,
        properties: Optional[dict[str, Any]] = None,
        doc_id: Optional[str] = None,
    ) -> Entity:
        """
        Create an entity in the knowledge graph.

        Args:
            name: Entity name
            entity_type: Type/label for the entity
            properties: Additional properties
            doc_id: Source document ID

        Returns:
            Created Entity
        """
        tenant_id = self._get_tenant_id()
        driver = await self._get_driver()
        props = properties or {}

        entity_id = f"{tenant_id}:{entity_type}:{name}".lower().replace(" ", "_")

        query = """
        MERGE (e:Entity {id: $id})
        SET e.name = $name,
            e.type = $type,
            e.tenant_id = $tenant_id,
            e.doc_id = $doc_id
        SET e += $properties
        RETURN e
        """

        async with driver.session() as session:
            result = await session.run(
                query,
                id=entity_id,
                name=name,
                type=entity_type,
                tenant_id=tenant_id,
                doc_id=doc_id,
                properties=props,
            )
            await result.consume()

        return Entity(
            id=entity_id,
            name=name,
            type=entity_type,
            properties=props,
            tenant_id=tenant_id,
        )

    async def create_relationship(
        self,
        source_id: str,
        target_id: str,
        relationship_type: str,
        properties: Optional[dict[str, Any]] = None,
    ) -> Relationship:
        """
        Create a relationship between entities.

        Args:
            source_id: Source entity ID
            target_id: Target entity ID
            relationship_type: Type of relationship
            properties: Additional properties

        Returns:
            Created Relationship
        """
        tenant_id = self._get_tenant_id()
        driver = await self._get_driver()
        props = properties or {}

        query = f"""
        MATCH (source:Entity {{id: $source_id, tenant_id: $tenant_id}})
        MATCH (target:Entity {{id: $target_id, tenant_id: $tenant_id}})
        MERGE (source)-[r:{relationship_type}]->(target)
        SET r.tenant_id = $tenant_id
        SET r += $properties
        RETURN r
        """

        async with driver.session() as session:
            result = await session.run(
                query,
                source_id=source_id,
                target_id=target_id,
                tenant_id=tenant_id,
                properties=props,
            )
            await result.consume()

        return Relationship(
            source_id=source_id,
            target_id=target_id,
            type=relationship_type,
            properties=props,
            tenant_id=tenant_id,
        )

    async def search_entities(
        self,
        query_text: str,
        entity_type: Optional[str] = None,
        limit: int = 10,
    ) -> list[Entity]:
        """
        Search entities by name (case-insensitive).

        Args:
            query_text: Search query
            entity_type: Optional type filter
            limit: Maximum results

        Returns:
            List of matching entities
        """
        tenant_id = self._get_tenant_id()
        driver = await self._get_driver()

        if entity_type:
            cypher = """
            MATCH (e:Entity)
            WHERE e.tenant_id = $tenant_id
              AND e.type = $entity_type
              AND toLower(e.name) CONTAINS toLower($search_text)
            RETURN e
            LIMIT $limit
            """
            params = {
                "tenant_id": tenant_id,
                "entity_type": entity_type,
                "search_text": query_text,
                "limit": limit,
            }
        else:
            cypher = """
            MATCH (e:Entity)
            WHERE e.tenant_id = $tenant_id
              AND toLower(e.name) CONTAINS toLower($search_text)
            RETURN e
            LIMIT $limit
            """
            params = {
                "tenant_id": tenant_id,
                "search_text": query_text,
                "limit": limit,
            }

        async with driver.session() as session:
            result = await session.run(cypher, **params)
            records = await result.data()

        return [
            Entity(
                id=r["e"]["id"],
                name=r["e"]["name"],
                type=r["e"]["type"],
                properties={
                    k: v for k, v in r["e"].items() if k not in ["id", "name", "type", "tenant_id"]
                },
                tenant_id=tenant_id,
            )
            for r in records
        ]

    async def get_entity_relationships(
        self,
        entity_id: str,
        direction: str = "both",
        limit: int = 50,
    ) -> list[dict]:
        """
        Get relationships for an entity.

        Args:
            entity_id: Entity ID
            direction: 'in', 'out', or 'both'
            limit: Maximum results

        Returns:
            List of relationship info dicts
        """
        tenant_id = self._get_tenant_id()
        driver = await self._get_driver()

        if direction == "out":
            cypher = """
            MATCH (e:Entity {id: $entity_id, tenant_id: $tenant_id})-[r]->(target:Entity)
            WHERE target.tenant_id = $tenant_id
            RETURN type(r) as rel_type, target.id as target_id, target.name as target_name
            LIMIT $limit
            """
        elif direction == "in":
            cypher = """
            MATCH (source:Entity)-[r]->(e:Entity {id: $entity_id, tenant_id: $tenant_id})
            WHERE source.tenant_id = $tenant_id
            RETURN type(r) as rel_type, source.id as source_id, source.name as source_name
            LIMIT $limit
            """
        else:
            cypher = """
            MATCH (e:Entity {id: $entity_id, tenant_id: $tenant_id})-[r]-(other:Entity)
            WHERE other.tenant_id = $tenant_id
            RETURN type(r) as rel_type, other.id as other_id, other.name as other_name
            LIMIT $limit
            """

        async with driver.session() as session:
            result = await session.run(
                cypher,
                entity_id=entity_id,
                tenant_id=tenant_id,
                limit=limit,
            )
            records = await result.data()

        return records

    async def get_subgraph(
        self,
        entity_ids: list[str],
        depth: int = 1,
    ) -> dict:
        """
        Get a subgraph around specified entities.

        Args:
            entity_ids: Starting entity IDs
            depth: How many hops to traverse

        Returns:
            Dict with 'entities' and 'relationships'
        """
        tenant_id = self._get_tenant_id()
        driver = await self._get_driver()

        cypher = """
        MATCH path = (e:Entity)-[r*1..$depth]-(connected:Entity)
        WHERE e.id IN $entity_ids
          AND e.tenant_id = $tenant_id
          AND all(node in nodes(path) WHERE node.tenant_id = $tenant_id)
        RETURN e, relationships(path) as rels, nodes(path) as nodes
        LIMIT 100
        """

        async with driver.session() as session:
            result = await session.run(
                cypher,
                entity_ids=entity_ids,
                tenant_id=tenant_id,
                depth=depth,
            )
            records = await result.data()

        # Deduplicate entities and relationships
        entities = {}
        relationships = []

        for record in records:
            for node in record.get("nodes", []):
                if node["id"] not in entities:
                    entities[node["id"]] = {
                        "id": node["id"],
                        "name": node.get("name"),
                        "type": node.get("type"),
                    }

            for rel in record.get("rels", []):
                relationships.append(
                    {
                        "type": rel.type,
                        "source": rel.start_node["id"],
                        "target": rel.end_node["id"],
                    }
                )

        return {
            "entities": list(entities.values()),
            "relationships": relationships,
        }

    async def delete_by_doc_id(self, doc_id: str) -> int:
        """
        Delete all entities from a document.

        Args:
            doc_id: Document ID

        Returns:
            Number of deleted entities
        """
        tenant_id = self._get_tenant_id()
        driver = await self._get_driver()

        cypher = """
        MATCH (e:Entity {tenant_id: $tenant_id, doc_id: $doc_id})
        DETACH DELETE e
        RETURN count(e) as deleted
        """

        async with driver.session() as session:
            result = await session.run(
                cypher,
                tenant_id=tenant_id,
                doc_id=doc_id,
            )
            record = await result.single()

        return record["deleted"] if record else 0


# Singleton
_graph_client: Optional[TenantGraphClient] = None


def get_graph_client() -> TenantGraphClient:
    """Get or create graph client singleton."""
    global _graph_client
    if _graph_client is None:
        _graph_client = TenantGraphClient()
    return _graph_client
