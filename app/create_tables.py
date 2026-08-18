"""
Run once to create the agent's own tables (conversations, messages) in
aromatichug_agent. Safe to re-run — create_all() skips tables that
already exist.

Usage:
    uv run python -m app.create_tables
"""
from .agent_db import Base, agent_engine
from . import models  # noqa: F401 — import registers models with Base

if __name__ == "__main__":
    Base.metadata.create_all(bind=agent_engine)
    print("Agent tables created (or already existed).")