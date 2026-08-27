from pathlib import Path

from alembic import command
from alembic.config import Config
from sqlalchemy import inspect

import app.db.models  # noqa: F401
from app.db.database import Base, engine

EXPECTED_TABLE_COUNT = 19
MIGRATION_MESSAGE = "initial schema"


def main():
    model_tables = sorted(Base.metadata.tables.keys())
    if len(model_tables) != EXPECTED_TABLE_COUNT:
        raise RuntimeError(
            f"Expected {EXPECTED_TABLE_COUNT} model tables, "
            f"but found {len(model_tables)}."
        )

    with engine.connect() as connection:
        existing_tables = sorted(inspect(connection).get_table_names())

    if existing_tables:
        raise RuntimeError(
            "Database is not empty. Run python check_setup.py and review the "
            "existing schema before creating the initial migration."
        )

    versions_dir = Path(__file__).parent / "alembic" / "versions"
    existing_revisions = [
        path
        for path in versions_dir.glob("*.py")
        if path.name != "__init__.py"
    ]
    if existing_revisions:
        raise RuntimeError(
            "Migration files already exist in alembic/versions. "
            "Do not create another initial migration."
        )

    config = Config(str(Path(__file__).parent / "alembic.ini"))
    command.revision(
        config,
        message=MIGRATION_MESSAGE,
        autogenerate=True,
    )
    print("Initial Alembic migration created successfully")


if __name__ == "__main__":
    main()
