"""
Tests for LangGraph agent components.
"""


from src.agent.graph import SYSTEM_PROMPT
from src.agent.tools import RAG_TOOLS


class TestAgentTools:
    """Tests for agent tools."""

    def test_rag_tools_defined(self):
        """Test that RAG tools are properly defined."""
        assert len(RAG_TOOLS) == 4

        tool_names = [t.name for t in RAG_TOOLS]
        assert "search_documents" in tool_names
        assert "search_knowledge_graph" in tool_names
        assert "get_entity_connections" in tool_names
        assert "hybrid_search" in tool_names

    def test_search_documents_tool(self):
        """Test search_documents tool metadata."""
        search_tool = next(t for t in RAG_TOOLS if t.name == "search_documents")

        assert search_tool.description is not None
        assert "document" in search_tool.description.lower()

    def test_search_knowledge_graph_tool(self):
        """Test search_knowledge_graph tool metadata."""
        search_tool = next(t for t in RAG_TOOLS if t.name == "search_knowledge_graph")

        assert search_tool.description is not None
        assert "knowledge graph" in search_tool.description.lower()

    def test_hybrid_search_tool(self):
        """Test hybrid_search tool metadata."""
        search_tool = next(t for t in RAG_TOOLS if t.name == "hybrid_search")

        assert search_tool.description is not None
        assert "hybrid" in search_tool.description.lower()


class TestAgentConfig:
    """Tests for agent configuration."""

    def test_system_prompt_exists(self):
        """Test that system prompt is defined."""
        assert SYSTEM_PROMPT is not None
        assert len(SYSTEM_PROMPT) > 100

    def test_system_prompt_mentions_tools(self):
        """Test that system prompt mentions available tools."""
        assert "search_documents" in SYSTEM_PROMPT
        assert "search_knowledge_graph" in SYSTEM_PROMPT
        assert "hybrid_search" in SYSTEM_PROMPT

    def test_system_prompt_guidelines(self):
        """Test that system prompt includes guidelines."""
        assert "Guidelines" in SYSTEM_PROMPT or "guidelines" in SYSTEM_PROMPT.lower()
