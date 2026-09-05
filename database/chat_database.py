import os

from sqlalchemy import create_engine, Column, String, Integer, DateTime
from sqlalchemy.orm import sessionmaker, declarative_base, Session
from dotenv import load_dotenv
from datetime import datetime
load_dotenv()

DB_URL = os.getenv("DB_URL")

engine = create_engine(DB_URL)
sessionLocal = sessionmaker(bind=engine)
Base = declarative_base()

class CHATTable(Base):
    __tablename__ = "Chat_DataBase_Table"
    
    id = Column(Integer, primary_key=True)
    thread_id = Column(String)
    user_msg = Column(String, nullable=False)
    ai_reply = Column(String)
    timestamp = Column(DateTime, default=datetime.now)
    
Base.metadata.create_all(bind=engine)

def get_db():
    db = sessionLocal()
    try:
        if db:
            yield db
    finally:
        db.close()
        
def stream_and_save_chat(db: Session, thread_id: str, user_msg: str, ai_reply: str):
    new_chat = CHATTable(
        thread_id=thread_id,
        user_msg=user_msg,
        ai_reply=ai_reply
    )
    db.add(new_chat)
    db.commit()
    db.refresh(new_chat)
    return new_chat

def get_chat_history(db, thread_id: str):
    return (
        db.query(CHATTable)
        .filter(CHATTable.thread_id == thread_id)
        .order_by(CHATTable.timestamp.asc())
        .all()
    )

def fetch_all_threads(db):
    results = db.query(CHATTable.thread_id).distinct().all()
    return [r[0] for r in results if r[0]]