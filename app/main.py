from fastapi import FastAPI
from app.api.chat import router as chat_router

app = FastAPI(
    title="AI ChatBot",
    description="A modern AI chatbot built with FastAPI",
    version="0.1.0",
)

app.include_router(chat_router)

@app.get("/")
def root():
    return {
        "message": "AI ChatBot API is running!"
    }


@app.get("/health")
def health():
    return {
        "status": "ok"
    }