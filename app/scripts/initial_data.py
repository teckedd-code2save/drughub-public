import logging
from typing import Any

from sqlmodel import Session

from app.utils.database import engine, init_db

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def init() -> Any:
    with Session(engine) as session:
        return init_db(session)


def main() -> None:
    logger.info("Creating initial data")
    super = init()
    logger.info(f"Superuser created: {super}")
    logger.info("Initial data created")


if __name__ == "__main__":
    main()
