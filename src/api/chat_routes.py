"""
Chat API routes with streaming support.
"""

import json
import uuid
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from langchain_core.messages import AIMessage, HumanMessage
from pydantic import BaseModel
from sqlalchemy import select

from src.agent import get_agent
from src.auth.dependencies import get_current_user
from src.core.tenant import TenantContext
from src.db import Conversation, Message, get_db_session

router = APIRouter(prefix="/chat", tags=["Chat"])


class ChatRequest(BaseModel):
    """Request model for chat."""

    message: str
    conversation_id: Optional[str] = None
    model_id: Optional[str] = None


class ChatResponse(BaseModel):
    """Response model for chat."""

    conversation_id: str
    message_id: str
    content: str
    sources: Optional[list[dict]] = None


class ConversationInfo(BaseModel):
    """Conversation info."""

    id: str
    title: Optional[str]
    created_at: str
    message_count: int


class ConversationListResponse(BaseModel):
    """Response for listing conversations."""

    conversations: list[ConversationInfo]
    total: int


@router.post("", response_model=ChatResponse)
async def chat(
    request: ChatRequest,
    user: TenantContext = Depends(get_current_user),
):
    """
    Send a message and get a response.

    POST /chat
    """
    TenantContext.set(user.tenant_id, user.user_id, user.email)

    try:
        # Get or create conversation
        conversation_id = request.conversation_id or str(uuid.uuid4())

        async with get_db_session() as session:
            # Check if conversation exists
            result = await session.execute(
                select(Conversation).where(
                    Conversation.id == conversation_id,
                    Conversation.tenant_id == user.tenant_id,
                )
            )
            conversation = result.scalar_one_or_none()

            if not conversation:
                # Create new conversation
                conversation = Conversation(
                    id=conversation_id,
                    tenant_id=user.tenant_id,
                    user_id=user.user_id,
                    title=request.message[:50] + "..."
                    if len(request.message) > 50
                    else request.message,
                    model_id=request.model_id,
                )
                session.add(conversation)

            # Load message history
            history_result = await session.execute(
                select(Message)
                .where(
                    Message.conversation_id == conversation_id,
                    Message.tenant_id == user.tenant_id,
                )
                .order_by(Message.created_at)
            )
            history_messages = history_result.scalars().all()

            # Convert to LangChain messages
            history = []
            for msg in history_messages:
                if msg.role == "user":
                    history.append(HumanMessage(content=msg.content))
                else:
                    history.append(AIMessage(content=msg.content))

            # Save user message
            user_msg = Message(
                id=str(uuid.uuid4()),
                conversation_id=conversation_id,
                tenant_id=user.tenant_id,
                role="user",
                content=request.message,
            )
            session.add(user_msg)

        # Get agent response
        agent = get_agent(request.model_id)
        response_content = await agent.chat(
            message=request.message,
            conversation_id=conversation_id,
            history=history,
        )

        # Save assistant message
        async with get_db_session() as session:
            assistant_msg = Message(
                id=str(uuid.uuid4()),
                conversation_id=conversation_id,
                tenant_id=user.tenant_id,
                role="assistant",
                content=response_content,
            )
            session.add(assistant_msg)

        return ChatResponse(
            conversation_id=conversation_id,
            message_id=assistant_msg.id,
            content=response_content,
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Chat failed: {str(e)}")


@router.post("/stream")
async def chat_stream(
    request: ChatRequest,
    user: TenantContext = Depends(get_current_user),
):
    """
    Stream a chat response using Server-Sent Events.

    POST /chat/stream
    """
    TenantContext.set(user.tenant_id, user.user_id, user.email)

    conversation_id = request.conversation_id or str(uuid.uuid4())

    async def generate():
        try:
            # Load history
            history = []
            async with get_db_session() as session:
                # Get or create conversation
                result = await session.execute(
                    select(Conversation).where(
                        Conversation.id == conversation_id,
                        Conversation.tenant_id == user.tenant_id,
                    )
                )
                conversation = result.scalar_one_or_none()

                if not conversation:
                    conversation = Conversation(
                        id=conversation_id,
                        tenant_id=user.tenant_id,
                        user_id=user.user_id,
                        title=request.message[:50],
                        model_id=request.model_id,
                    )
                    session.add(conversation)

                # Load history
                history_result = await session.execute(
                    select(Message)
                    .where(
                        Message.conversation_id == conversation_id,
                        Message.tenant_id == user.tenant_id,
                    )
                    .order_by(Message.created_at)
                )

                for msg in history_result.scalars().all():
                    if msg.role == "user":
                        history.append(HumanMessage(content=msg.content))
                    else:
                        history.append(AIMessage(content=msg.content))

                # Save user message
                user_msg = Message(
                    id=str(uuid.uuid4()),
                    conversation_id=conversation_id,
                    tenant_id=user.tenant_id,
                    role="user",
                    content=request.message,
                )
                session.add(user_msg)

            # Send conversation ID first
            yield f"data: {json.dumps({'type': 'start', 'conversation_id': conversation_id})}\n\n"

            # Stream response
            agent = get_agent(request.model_id)
            full_response = ""

            async for chunk in agent.stream_chat(
                message=request.message,
                conversation_id=conversation_id,
                history=history,
            ):
                full_response += chunk
                yield f"data: {json.dumps({'type': 'chunk', 'content': chunk})}\n\n"

            # Save assistant message
            async with get_db_session() as session:
                assistant_msg = Message(
                    id=str(uuid.uuid4()),
                    conversation_id=conversation_id,
                    tenant_id=user.tenant_id,
                    role="assistant",
                    content=full_response,
                )
                session.add(assistant_msg)

            yield f"data: {json.dumps({'type': 'end', 'message_id': assistant_msg.id})}\n\n"

        except Exception as e:
            yield f"data: {json.dumps({'type': 'error', 'error': str(e)})}\n\n"

    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
        },
    )


@router.get("/conversations", response_model=ConversationListResponse)
async def list_conversations(
    user: TenantContext = Depends(get_current_user),
):
    """
    List all conversations for the current user.

    GET /chat/conversations
    """
    TenantContext.set(user.tenant_id, user.user_id, user.email)

    try:
        async with get_db_session() as session:
            result = await session.execute(
                select(Conversation)
                .where(
                    Conversation.tenant_id == user.tenant_id,
                    Conversation.user_id == user.user_id,
                )
                .order_by(Conversation.created_at.desc())
            )
            conversations = result.scalars().all()

            conv_list = []
            for conv in conversations:
                # Count messages
                msg_result = await session.execute(
                    select(Message).where(Message.conversation_id == conv.id)
                )
                msg_count = len(msg_result.scalars().all())

                conv_list.append(
                    ConversationInfo(
                        id=conv.id,
                        title=conv.title,
                        created_at=str(conv.created_at),
                        message_count=msg_count,
                    )
                )

        return ConversationListResponse(
            conversations=conv_list,
            total=len(conv_list),
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to list conversations: {str(e)}")


@router.get("/conversations/{conversation_id}")
async def get_conversation(
    conversation_id: str,
    user: TenantContext = Depends(get_current_user),
):
    """
    Get a conversation with its messages.

    GET /chat/conversations/{conversation_id}
    """
    TenantContext.set(user.tenant_id, user.user_id, user.email)

    try:
        async with get_db_session() as session:
            # Get conversation
            result = await session.execute(
                select(Conversation).where(
                    Conversation.id == conversation_id,
                    Conversation.tenant_id == user.tenant_id,
                )
            )
            conversation = result.scalar_one_or_none()

            if not conversation:
                raise HTTPException(status_code=404, detail="Conversation not found")

            # Get messages
            msg_result = await session.execute(
                select(Message)
                .where(Message.conversation_id == conversation_id)
                .order_by(Message.created_at)
            )
            messages = msg_result.scalars().all()

            return {
                "id": conversation.id,
                "title": conversation.title,
                "model_id": conversation.model_id,
                "created_at": str(conversation.created_at),
                "messages": [
                    {
                        "id": msg.id,
                        "role": msg.role,
                        "content": msg.content,
                        "created_at": str(msg.created_at),
                    }
                    for msg in messages
                ],
            }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get conversation: {str(e)}")


@router.delete("/conversations/{conversation_id}")
async def delete_conversation(
    conversation_id: str,
    user: TenantContext = Depends(get_current_user),
):
    """
    Delete a conversation.

    DELETE /chat/conversations/{conversation_id}
    """
    TenantContext.set(user.tenant_id, user.user_id, user.email)

    try:
        async with get_db_session() as session:
            result = await session.execute(
                select(Conversation).where(
                    Conversation.id == conversation_id,
                    Conversation.tenant_id == user.tenant_id,
                )
            )
            conversation = result.scalar_one_or_none()

            if not conversation:
                raise HTTPException(status_code=404, detail="Conversation not found")

            await session.delete(conversation)

        return {"status": "deleted", "id": conversation_id}

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to delete conversation: {str(e)}")
