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
            vals = ", ".join(f"'{v}'" for v in values)
            conn.execute(text(
                f"DO $$ BEGIN "
                f"CREATE TYPE {name} AS ENUM ({vals}); "
                f"EXCEPTION WHEN duplicate_object THEN NULL; "
                f"END $$;"
            ))
        conn.commit()


def init_db() -> None:
    """Create enum types then all tables. Fully idempotent — safe every startup."""
    create_enums()
    try:
        Base.metadata.create_all(bind=engine)
    except (IntegrityError, ProgrammingError):
        pass  # Tables already exist — safe to ignore on restart


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
