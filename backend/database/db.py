import os
import tempfile
from pathlib import Path

from sqlalchemy import create_engine, inspect, text
from sqlalchemy.orm import sessionmaker

from .models import Base

default_db_path = Path(tempfile.gettempdir()) / "fraudshield.db"
DATABASE_URL = os.getenv("DATABASE_URL", f"sqlite:///{default_db_path.as_posix()}")

engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def create_tables():
    Base.metadata.create_all(bind=engine)

    # Backfill columns for older local SQLite databases used during development.
    inspector = inspect(engine)
    existing_tables = set(inspector.get_table_names())
    if "transactions" not in existing_tables:
        return

    existing_columns = {
        column["name"] for column in inspector.get_columns("transactions")
    }
    column_statements = {
        "sender": "ALTER TABLE transactions ADD COLUMN sender VARCHAR",
        "location": "ALTER TABLE transactions ADD COLUMN location VARCHAR",
        "event_time": "ALTER TABLE transactions ADD COLUMN event_time DATETIME",
    }

    with engine.begin() as connection:
        for column_name, statement in column_statements.items():
            if column_name not in existing_columns:
                connection.execute(text(statement))

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
