"""
Background worker entry point.
Run as a separate process for scheduled analysis tasks.

Usage (standalone):
    python -m app.worker

Docker Compose adds this as the 'worker' service.
"""
import time
import logging
from app.core.logging_config import setup_logging, get_logger

setup_logging()
logger = get_logger("worker")


def main() -> None:
    from app.core.database import engine, Base
    from app.core.scheduler import start_scheduler, stop_scheduler

    logger.info("VCM worker starting")
    Base.metadata.create_all(bind=engine)
    start_scheduler()

    try:
        while True:
            time.sleep(60)
    except KeyboardInterrupt:
        logger.info("VCM worker shutting down")
    finally:
        stop_scheduler()


if __name__ == "__main__":
    main()
