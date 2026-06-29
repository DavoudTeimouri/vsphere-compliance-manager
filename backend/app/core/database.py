from sqlalchemy import create_engine, text
from sqlalchemy.exc import IntegrityError, ProgrammingError
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
            exists = conn.execute(text(
                f"SELECT 1 FROM pg_type WHERE typname = '{name}'"
            )).scalar()
            if not exists:
                vals = ", ".join(f"'{v}'" for v in values)
                conn.execute(text(
                    f"CREATE TYPE {name} AS ENUM ({vals})"
                ))
        conn.commit()


def _table_exists(table_name: str) -> bool:
    """Check if a specific table exists in the public schema."""
    with engine.connect() as conn:
        result = conn.execute(text(
            "SELECT 1 FROM pg_catalog.pg_class c "
            "JOIN pg_catalog.pg_namespace n ON n.oid = c.relnamespace "
            "WHERE n.nspname = 'public' AND c.relname = :table"
        ), {"table": table_name}).scalar()
        return result is not None


def init_db() -> None:
    """Create enum types then all tables. Fully idempotent — safe every startup."""
    create_enums()
    if not _table_exists("users"):
        Base.metadata.create_all(bind=engine)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
