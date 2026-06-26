from sqlalchemy import create_engine, text, inspect
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from app.core.config import settings

engine = create_engine(
    settings.DATABASE_URL,
    pool_size=settings.DB_POOL_SIZE,
    max_overflow=settings.DB_MAX_OVERFLOW,
    pool_pre_ping=True,
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def create_enums() -> None:
    """Create PostgreSQL ENUM types if they do not already exist."""
    enums = [
        ("userrole",      ("admin", "operator", "viewer")),
        ("analysistype",  ("drs", "storage", "full")),
        ("analysisstatus",("pending", "running", "completed", "failed")),
    ]
    with engine.connect() as conn:
        for name, values in enums:
            # Check if type already exists (safe across all PostgreSQL versions)
            result = conn.execute(text(
                f"SELECT 1 FROM pg_type WHERE typname = '{name}'"
            ))
            if not result.fetchone():
                vals = ", ".join(f"'{v}'" for v in values)
                conn.execute(text(f"CREATE TYPE {name} AS ENUM ({vals})"))
        conn.commit()


def init_db() -> None:
    """Create enum types then all tables. Fully idempotent — safe every startup."""
    create_enums()
    # Only create tables if they don't already exist (avoids duplicate type errors)
    inspector = inspect(engine)
    if not inspector.get_table_names():
        Base.metadata.create_all(bind=engine)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
