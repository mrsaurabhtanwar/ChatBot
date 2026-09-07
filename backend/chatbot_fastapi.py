from fastapi import FastAPI, Depends
from backend.chatbot_core import workflow
from database.chat_database import get_db, stream_and_save_chat, fetch_all_threads, get_chat_history
from sqlalchemy.orm import Session
from pydantic import BaseModel

app = FastAPI(
    title="AI ChatBot", 
    description="AI Chatbot with LangGraph and SQLite conversation history", 
    version="1.0.0"
)
 
class ChatRequest(BaseModel):
    thread_id: str
    message: str

@app.get("/")
def home():
    return {
        "msg": "AI ChatBot API is running",
        "info": "/docs"
    }

@app.post("/chat")
def chat_bot(request: ChatRequest, db: Session = Depends(get_db)):
    history = get_chat_history(db, request.thread_id)
    
    messages = [("system", "You are a helpful AI assistant.")]
    for h in history:
        messages.append(("human", h.user_msg))
        if h.ai_reply:
            messages.append(("ai", h.ai_reply))
    messages.append(("human", request.message))
    
    response = workflow.invoke({"messages": messages})
    ai_msg = response["messages"][-1].content
    
    stream_and_save_chat(db, request.thread_id, request.message, ai_msg)
    
    return {
        "thread_id": request.thread_id,
        "ai_msg": ai_msg
    }

@app.get('/threads')
def get_threads(db: Session = Depends(get_db)):
    return {
        "threads": fetch_all_threads(db)
    }

@app.get("/threads/{thread_id}")
def chat_history(thread_id: str, db: Session = Depends(get_db)):
    history = get_chat_history(db, thread_id)
    return [
        {
            "user_msg": h.user_msg,
            "ai_reply": h.ai_reply,
            "timestamp": str(h.timestamp)
        }
        for h in history
    ]