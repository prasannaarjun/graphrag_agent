"""
LangGraph agent tools for RAG operations.
"""

from typing import Annotated, Optional

from langchain_core.tools import tool

from src.knowledge_graph import get_graph_client
from src.llm import get_embedding_model
from src.vector_store import get_pgvector_client


@tool
async def search_documents(
    query: Annotated[str, "The search query to find relevant document chunks"],
    limit: Annotated[int, "Maximum number of results to return"] = 5,
) -> str:
    """
    Search for relevant document chunks using semantic similarity.
    Use this when you need to find information from uploaded documents.
    """
    try:
        embedding_model = get_embedding_model()
        query_embedding = embedding_model.embed_text(query)

        pgvector = get_pgvector_client(dimension=embedding_model.dimension)
        results = await pgvector.similarity_search(
            query_embedding=query_embedding,
            limit=limit,
        )

        if not results:
            return "No relevant documents found."

        output = []
        for i, chunk in enumerate(results, 1):
            source = chunk.metadata.get("filename", "Unknown") if chunk.metadata else "Unknown"
            output.append(f"[{i}] Source: {source}\n{chunk.content}\n")

        return "\n---\n".join(output)

    except Exception as e:
        return f"Error searching documents: {str(e)}"


@tool
async def search_knowledge_graph(
    query: Annotated[str, "Search query for entities in the knowledge graph"],
    entity_type: Annotated[
        Optional[str], "Optional entity type filter (PERSON, ORGANIZATION, etc.)"
    ] = None,
) -> str:
    """
    Search for entities in the knowledge graph by name.
    Use this to find specific people, organizations, concepts, or other entities.
    """
    try:
        graph = get_graph_client()
        entities = await graph.search_entities(
            query_text=query,
            entity_type=entity_type,
            limit=10,
        )

        if not entities:
            return f"No entities found matching '{query}'."

        output = []
        for entity in entities:
            desc = entity.properties.get("description", "")
            output.append(f"- {entity.name} ({entity.type}): {desc}")

        return "Found entities:\n" + "\n".join(output)

    except Exception as e:
        return f"Error searching knowledge graph: {str(e)}"


@tool
async def get_entity_connections(
    entity_name: Annotated[str, "Name of the entity to get connections for"],
) -> str:
    """
    Get relationships and connections for a specific entity.
    Use this to understand how an entity relates to other entities in the knowledge graph.
    """
    try:
        graph = get_graph_client()

        # First find the entity
        entities = await graph.search_entities(entity_name, limit=1)
        if not entities:
            return f"Entity '{entity_name}' not found."

        entity = entities[0]

        # Get relationships
        relationships = await graph.get_entity_relationships(
            entity_id=entity.id,
            direction="both",
            limit=20,
        )

        if not relationships:
            return f"No connections found for '{entity_name}'."

        output = [f"Connections for {entity.name} ({entity.type}):"]
        for rel in relationships:
            if "target_name" in rel:
                output.append(f"  → {rel['rel_type']} → {rel['target_name']}")
            elif "source_name" in rel:
                output.append(f"  ← {rel['rel_type']} ← {rel['source_name']}")
            elif "other_name" in rel:
                output.append(f"  ↔ {rel['rel_type']} ↔ {rel['other_name']}")

        return "\n".join(output)

    except Exception as e:
        return f"Error getting entity connections: {str(e)}"


@tool
async def hybrid_search(
    query: Annotated[str, "Search query combining document and graph search"],
) -> str:
    """
    Perform a hybrid search across both documents and knowledge graph.
    Use this for comprehensive searches that need both textual and structured information.
    """
    try:
        results = []

        # Document search
        embedding_model = get_embedding_model()
        query_embedding = embedding_model.embed_text(query)
        pgvector = get_pgvector_client(dimension=embedding_model.dimension)

        doc_results = await pgvector.similarity_search(
            query_embedding=query_embedding,
            limit=3,
        )

        if doc_results:
            results.append("📄 Document Results:")
            for chunk in doc_results:
                source = chunk.metadata.get("filename", "Unknown") if chunk.metadata else "Unknown"
                # Truncate content
                content = chunk.content[:200] + "..." if len(chunk.content) > 200 else chunk.content
                results.append(f"  [{source}]: {content}")

        # Graph search
        graph = get_graph_client()
        entities = await graph.search_entities(query, limit=5)

        if entities:
            results.append("\n🔗 Knowledge Graph Entities:")
            for entity in entities:
                results.append(f"  - {entity.name} ({entity.type})")

        if not results:
            return "No results found in documents or knowledge graph."

        return "\n".join(results)

    except Exception as e:
        return f"Error in hybrid search: {str(e)}"


# Export all tools
RAG_TOOLS = [
    search_documents,
    search_knowledge_graph,
    get_entity_connections,
    hybrid_search,
]
