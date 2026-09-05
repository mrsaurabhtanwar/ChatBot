from fastapi import FastAPI, Depends
from backend.chatbot_core import workflow, memory
from database.chat_database import get_db, stream_and_save_chat, fetch_all_threads, get_chat_history
from sqlalchemy.orm import Session
from pydantic import BaseModel

app = FastAPI(
    title="AI ChatBot with SynapticMemory", 
    description="Multi-tenant AI Chatbot with STM/LTM Cognitive Memory and Contradiction Resolution", 
    version="1.0.0"
)
 
class ChatRequest(BaseModel):
    thread_id: str
    message: str

@app.get("/")
def home():
    return {
        "msg": "AI ChatBot API with SynapticMemory is running",
        "info": "/docs"
    }

@app.post("/chat")
def chat_bot(request: ChatRequest, db: Session = Depends(get_db)):
    # 1. Fetch dense sub-300 token memory context for this thread
    memory_context = memory.get_system_prompt_context(user_id=request.thread_id, query=request.message)
    
    # 2. Build system prompt + dialogue
    messages = [
        ("system", f"You are a helpful AI assistant. Adhere strictly to the user's active ground truth beliefs:\n\n{memory_context}"),
        ("human", request.message)
    ]
    
    # 3. Invoke LangGraph workflow
    response = workflow.invoke({"messages": messages})
    ai_msg = response["messages"][-1].content
    
    # 4. Record turn into SynapticMemory (updates beliefs, resolves contradictions, applies decay)
    memory.record_chat_turn(
        user_id=request.thread_id,
        user_message=request.message,
        assistant_reply=ai_msg
    )
    
    # 5. Persist to chat database log
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

@app.get("/memory/{thread_id}")
def get_memory_state(thread_id: str):
    """Returns the SynapticMemory ground truth facts and resolved contradictions."""
    return memory.get_user_memory_summary(thread_id)