from fastapi import APIRouter


from app.schemas.chat import ChatRequest, ChatResponse
from app.services.chat_service import ChatService

router = APIRouter(
    prefix="/chat",
    tags=["Chat"]
)

chat_service = ChatService()


@router.post("/", response_model=ChatResponse)
def chat(request: ChatRequest):

    reply = chat_service.chat(request.message)

    return ChatResponse(
        reply= reply
    )