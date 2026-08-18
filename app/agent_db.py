import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from dotenv import load_dotenv

load_dotenv()

AGENT_DATABASE_URL = os.getenv("AGENT_DATABASE_URL")
if not AGENT_DATABASE_URL:
    raise RuntimeError("AGENT_DATABASE_URL not set in .env")

# Deliberately a SEPARATE engine from database.py's read-only connection
# to aromatichug_db. This one points at aromatichug_agent, a database the
# agent fully owns — conversations, messages, and later the approval
# queue live here. Physically separating databases means a bug here can
# never write into PHP's tables, regardless of any application-level
# mistake.
agent_engine = create_engine(
    AGENT_DATABASE_URL,
    pool_size=5,
    max_overflow=5,
    pool_pre_ping=True,
)

AgentSessionLocal = sessionmaker(bind=agent_engine, autoflush=False, autocommit=False)

Base = declarative_base()


def get_agent_db():
    db = AgentSessionLocal()
    try:
        yield db
    finally:
        db.close()