from fastapi import FastAPI

app = FastAPI(
    title="AI ChatBot",
    description="A modern AI chatbot built with FastAPI",
    version="0.1.0",
)


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