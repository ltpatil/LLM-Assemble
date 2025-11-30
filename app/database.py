from sqlmodel import SQLModel, create_engine, Session
import os

# Default to SQLite for local development
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///history.db")

# Handle Render's postgres:// requirement for SQLAlchemy
if DATABASE_URL and DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

connect_args = {"check_same_thread": False} if "sqlite" in DATABASE_URL else {}

engine = create_engine(DATABASE_URL, connect_args=connect_args)

def create_db_and_tables():
    SQLModel.metadata.create_all(engine)

def get_session():
    with Session(engine) as session:
        yield session