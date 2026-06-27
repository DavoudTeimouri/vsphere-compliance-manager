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
            # PostgreSQL: CREATE TYPE IF NOT EXISTS (available since PG 9.5)
            vals = ", ".join(f"'{v}'" for v in values)
            conn.execute(text(
                f"CREATE TYPE IF NOT EXISTS {name} AS ENUM ({vals})"
            ))
        conn.commit()


def _tables_exist() -> bool:
    """Check if application tables exist in the database."""
    try:
        with engine.connect() as conn:
            result = conn.execute(text(
                "SELECT 1 FROM pg_catalog.pg_class c "
                "JOIN pg_catalog.pg_namespace n ON n.oid = c.relnamespace "
                "WHERE n.nspname = 'public' AND c.relname = 'users'"
            )).scalar()
            return result is not None
    except Exception:
        return False


def init_db() -> None:
    """Create enum types then all tables. Fully idempotent — safe every startup."""
    create_enums()
    if not _tables_exist():
        Base.metadata.create_all(bind=engine)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
