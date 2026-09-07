import os
from datetime import datetime
from dotenv import load_dotenv
from sqlalchemy import create_engine, Column, String, Integer, DateTime, func
from sqlalchemy.orm import sessionmaker, declarative_base, Session

load_dotenv()

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DEFAULT_DB_FILE = os.path.join(BASE_DIR, "chat_database.db")
DEFAULT_DB_URL = f"sqlite:///{DEFAULT_DB_FILE.replace(os.sep, '/')}"

raw_db_url = os.getenv("DB_URL")
if not raw_db_url or "chat_database.db" in raw_db_url:
    DB_URL = DEFAULT_DB_URL
elif raw_db_url.startswith("sqlite:///") and not os.path.isabs(raw_db_url.replace("sqlite:///", "")):
    rel_path = raw_db_url.replace("sqlite:///", "")
    project_root = os.path.abspath(os.path.join(BASE_DIR, ".."))
    abs_path = os.path.abspath(os.path.join(project_root, rel_path))
    os.makedirs(os.path.dirname(abs_path), exist_ok=True)
    DB_URL = f"sqlite:///{abs_path.replace(os.sep, '/')}"
else:
    DB_URL = raw_db_url

connect_args = {"check_same_thread": False} if DB_URL.startswith("sqlite") else {}
engine = create_engine(DB_URL, connect_args=connect_args)
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
    results = (
        db.query(CHATTable.thread_id)
        .group_by(CHATTable.thread_id)
        .order_by(func.max(CHATTable.timestamp).desc())
        .all()
    )
    return [r[0] for r in results if r[0]]