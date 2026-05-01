import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from dotenv import load_dotenv

# Load .env locally (Railway ignores this)
load_dotenv()

# Strip so empty/whitespace in .env still means "no database" (local workbench in-memory mode).
_raw_db_url = os.getenv("DATABASE_URL")
DATABASE_URL = (_raw_db_url.strip() if _raw_db_url else None) or None

# Allow database to be optional for match engine testing / localhost without Postgres
if not DATABASE_URL:
    DATABASE_URL = None

# Only create engine if DATABASE_URL is set
if DATABASE_URL:
    engine = create_engine(
        DATABASE_URL,
        pool_pre_ping=True,
    )
else:
    engine = None

SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
)

Base = declarative_base()
