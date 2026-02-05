"""
LangGraph agent for GraphRAG with tool-calling capabilities.
"""

from typing import Annotated, Literal, TypedDict

from langchain_core.messages import AIMessage, BaseMessage, HumanMessage, SystemMessage
from langgraph.graph import END, StateGraph
from langgraph.graph.message import add_messages
from langgraph.prebuilt import ToolNode

from src.agent.tools import RAG_TOOLS
from src.llm import get_llm


# Agent state type
class AgentState(TypedDict):
    """State for the agent graph."""

    messages: Annotated[list[BaseMessage], add_messages]
    conversation_id: str
    model_id: str


# System prompt for the agent
SYSTEM_PROMPT = """You are a helpful AI assistant with access to a knowledge base of documents and a knowledge graph.

Your capabilities:
1. **search_documents**: Search uploaded documents for relevant information using semantic similarity
2. **search_knowledge_graph**: Find entities (people, organizations, concepts) in the knowledge graph
3. **get_entity_connections**: Explore relationships between entities
4. **hybrid_search**: Search both documents and knowledge graph simultaneously

Guidelines:
- Use tools when you need to find specific information from the user's documents or knowledge graph
- Synthesize information from multiple sources when answering
- Cite your sources when using information from documents
- If you can't find relevant information, say so honestly
- Be concise but thorough in your responses

You have access to the user's uploaded documents and extracted knowledge graph. Use the tools to find relevant information before answering questions about their content."""


def create_agent_graph(model_id: str = None):
    """
    Create the LangGraph agent.

    Args:
        model_id: LLM model ID to use

    Returns:
        Compiled LangGraph
    """
    # Get LLM with tools bound
    llm = get_llm(model_id)
    llm_with_tools = llm.bind_tools(RAG_TOOLS)

    # Tool node
    tool_node = ToolNode(RAG_TOOLS)

    def agent_node(state: AgentState) -> AgentState:
        """Main agent node that decides whether to use tools."""
        messages = state["messages"]

        # Ensure system prompt is first
        if not messages or not isinstance(messages[0], SystemMessage):
            messages = [SystemMessage(content=SYSTEM_PROMPT)] + list(messages)

        # Get response from LLM
        response = llm_with_tools.invoke(messages)

        return {"messages": [response]}

    def should_continue(state: AgentState) -> Literal["tools", "end"]:
        """Determine if we should continue to tools or end."""
        last_message = state["messages"][-1]

        if isinstance(last_message, AIMessage) and last_message.tool_calls:
            return "tools"
        return "end"

    # Build graph
    graph = StateGraph(AgentState)

    # Add nodes
    graph.add_node("agent", agent_node)
    graph.add_node("tools", tool_node)

    # Set entry point
    graph.set_entry_point("agent")

    # Add edges
    graph.add_conditional_edges(
        "agent",
        should_continue,
        {
            "tools": "tools",
            "end": END,
        },
    )
    graph.add_edge("tools", "agent")

    return graph.compile()


class GraphRAGAgent:
    """
    High-level agent interface for GraphRAG.
    """

    def __init__(self, model_id: str = None):
        """
        Initialize agent.

        Args:
            model_id: LLM model ID
        """
        self.model_id = model_id
        self.graph = create_agent_graph(model_id)

    async def chat(
        self,
        message: str,
        conversation_id: str,
        history: list[BaseMessage] = None,
    ) -> str:
        """
        Send a message and get a response.

        Args:
            message: User message
            conversation_id: Conversation ID
            history: Optional message history

        Returns:
            Agent response text
        """
        messages = list(history) if history else []
        messages.append(HumanMessage(content=message))

        state = {
            "messages": messages,
            "conversation_id": conversation_id,
            "model_id": self.model_id or "",
        }

        result = await self.graph.ainvoke(state)

        # Get last AI message
        for msg in reversed(result["messages"]):
            if isinstance(msg, AIMessage):
                return msg.content

        return "I apologize, but I couldn't generate a response."

    async def stream_chat(
        self,
        message: str,
        conversation_id: str,
        history: list[BaseMessage] = None,
    ):
        """
        Stream a response.

        Args:
            message: User message
            conversation_id: Conversation ID
            history: Optional message history

        Yields:
            Response chunks
        """
        messages = list(history) if history else []
        messages.append(HumanMessage(content=message))

        state = {
            "messages": messages,
            "conversation_id": conversation_id,
            "model_id": self.model_id or "",
        }

        async for event in self.graph.astream_events(state, version="v2"):
            if event["event"] == "on_chat_model_stream":
                chunk = event["data"]["chunk"]
                if hasattr(chunk, "content") and chunk.content:
                    yield chunk.content


def get_agent(model_id: str = None) -> GraphRAGAgent:
    """Get agent instance."""
    return GraphRAGAgent(model_id)
