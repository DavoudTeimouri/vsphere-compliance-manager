from sqlalchemy import create_engine, text
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
    """Create PostgreSQL ENUM types if they do not already exist.

    Uses a single atomic DO block with exception handler to handle
    concurrent creation by multiple workers safely.
    """
    enums = [
        ("userrole",      ("admin", "operator", "viewer")),
        ("analysistype",  ("drs", "storage", "full")),
        ("analysisstatus",("pending", "running", "completed", "failed")),
    ]
    # Build a single DO block that creates all enums with exception handling
    enum_defs = []
    for name, values in enums:
        vals = ", ".join(f"'{v}'" for v in values)
        enum_defs.append(
            f"BEGIN CREATE TYPE {name} AS ENUM ({vals}); "
            f"EXCEPTION WHEN duplicate_object THEN NULL; END;"
        )
    sql = "DO $$ " + " ".join(enum_defs) + " $$"
    with engine.connect() as conn:
        conn.execute(text(sql))
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
