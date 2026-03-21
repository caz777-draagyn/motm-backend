import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from dotenv import load_dotenv

# Load .env locally (Railway ignores this)
load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")

# Allow database to be optional for match engine testing
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
