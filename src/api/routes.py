import time
from datetime import UTC, datetime

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from src.agents.graph import agent
from src.auth.dependencies import get_current_user
from src.config import get_settings
from src.db import get_db
from src.db.models import User
from src.models.schemas import ChatRequest, ChatResponse, ConversationHistoryResponse, RetrievedDocInfo
from src.services.braintrust_service import log_chat_interaction
from src.services.conversation_memory import conversation_memory
from src.services.conversation_store import ConversationStore
from src.services.langfuse_service import get_langfuse_handler

router = APIRouter()


@router.post("/chat", response_model=ChatResponse)
async def chat(
    request: ChatRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ChatResponse:
    """Chat với AI agent RAG (tự động trace vào Langfuse Localhost & Braintrust nếu bật)."""
    start_time = time.perf_counter()
    try:
        user_role = current_user.role.value
        memory_user_id = current_user.id
        settings = get_settings()
        use_postgres_memory = settings.conversation_memory_backend == "postgres"
        conversation = None
        if use_postgres_memory:
            conversation = ConversationStore.get_or_create(db, request.conversation_id, memory_user_id)
            if conversation is None:
                raise HTTPException(status_code=404, detail="Conversation not found")
            history = ConversationStore.load_history(db, request.conversation_id, memory_user_id)
        else:
            history = conversation_memory.get(request.conversation_id, memory_user_id)

        # Initialize Langfuse Localhost Tracing Callback
        langfuse_handler = get_langfuse_handler(user_role=user_role)
        invoke_config = {}
        if langfuse_handler:
            invoke_config["callbacks"] = [langfuse_handler]

        result = await agent.ainvoke(
            {
                "query": request.message,
                "raw_query": request.message,
                "user_role": user_role,
                "conversation_history": history,
            },
            config=invoke_config,
        )
        duration_ms = (time.perf_counter() - start_time) * 1000.0

        response_text = result.get("response", "")
        analysis_text = result.get("analysis", "")
        intent_type = result.get("intent")
        citations_list = result.get("citations", [])
        needs_escalate = result.get("needs_escalation", False)
        ticket_data = result.get("ticket_payload")

        # Map retrieved_docs_detail → list[RetrievedDocInfo]
        raw_docs_detail = result.get("retrieved_docs_detail", [])
        retrieved_docs: list[RetrievedDocInfo] = []
        for doc in raw_docs_detail:
            try:
                retrieved_docs.append(
                    RetrievedDocInfo(
                        doc_name=doc.get("doc_name", "Tài liệu VinFast"),
                        section=doc.get("section", ""),
                        rerank_score=float(doc.get("rerank_score", 0.0)),
                        rrf_score=float(doc.get("rrf_score", 0.0)),
                        content_preview=doc.get("content_preview", ""),
                        content_type=doc.get("content_type", "document"),
                        source_path=doc.get("source_path", ""),
                        timestamp_seconds=doc.get("timestamp_seconds"),
                    )
                )
            except Exception:
                pass  # Bỏ qua chunk lỗi, không làm hỏng toàn bộ response

        if use_postgres_memory and conversation is not None:
            ConversationStore.append_turn(
                db,
                conversation,
                request.message,
                response_text,
                assistant_metadata={
                    "analysis": analysis_text,
                    "intent": intent_type,
                    "citations": citations_list,
                    "retrieved_docs": [doc.model_dump() for doc in retrieved_docs],
                    "needs_escalation": needs_escalate,
                    "ticket_payload": ticket_data,
                },
            )
        elif not use_postgres_memory:
            conversation_memory.append(request.conversation_id, memory_user_id, "user", request.message)
            conversation_memory.append(request.conversation_id, memory_user_id, "assistant", response_text)

        # Auto-log to Braintrust in real-time
        log_chat_interaction(
            message=request.message,
            response=response_text,
            user_role=user_role,
            intent=intent_type,
            citations=citations_list,
            analysis=analysis_text,
            needs_escalation=needs_escalate,
            duration_ms=duration_ms,
        )

        return ChatResponse(
            conversation_id=request.conversation_id,
            response=response_text,
            analysis=analysis_text,
            intent=intent_type,
            citations=citations_list,
            retrieved_docs=retrieved_docs,
            needs_escalation=needs_escalate,
            ticket_payload=ticket_data,
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/chat/conversations/{conversation_id}", response_model=ConversationHistoryResponse)
async def get_conversation_history(
    conversation_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ConversationHistoryResponse:
    """Return the authenticated user's recent messages for chat restoration."""
    settings = get_settings()
    if settings.conversation_memory_backend == "postgres":
        history = ConversationStore.load_display_history(db, conversation_id, current_user.id)
        if history is None:
            raise HTTPException(status_code=404, detail="Conversation not found")
        return ConversationHistoryResponse.model_validate(history)

    messages = conversation_memory.get(conversation_id, current_user.id)
    return ConversationHistoryResponse(
        conversation_id=conversation_id,
        messages=[
            {"id": f"legacy-{index}", "role": item["role"], "content": item["content"], "metadata": {}, "timestamp": datetime.now(UTC)}
            for index, item in enumerate(messages)
        ],
    )


@router.get("/status")
async def agent_status():
    """Kiểm tra trạng thái agent."""
    return {"status": "ready", "agent": "LangGraph Agent v1.0"}
