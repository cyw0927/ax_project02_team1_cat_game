from sqlalchemy import inspect, text

import app.db.models  # noqa: F401
from app.db.database import Base, engine

EXPECTED_TABLE_COUNT = 19


def main():
    model_tables = sorted(Base.metadata.tables.keys())

    print(f"Registered model tables: {len(model_tables)}")
    for table_name in model_tables:
        print(f"- {table_name}")

    if len(model_tables) != EXPECTED_TABLE_COUNT:
        raise RuntimeError(
            f"Expected {EXPECTED_TABLE_COUNT} model tables, "
            f"but found {len(model_tables)}."
        )

    with engine.connect() as connection:
        connection.execute(text("SELECT 1"))
        print("Database connection successful")

        inspector = inspect(connection)
        existing_tables = sorted(inspector.get_table_names())

    print(f"Existing database tables: {len(existing_tables)}")
    for table_name in existing_tables:
        print(f"- {table_name}")

    if not existing_tables:
        print("Database is empty and ready for the initial Alembic migration.")
    elif "alembic_version" in existing_tables:
        print("Alembic is already managing this database.")
    else:
        print(
            "Warning: database tables already exist without alembic_version. "
            "Do not create the initial migration until this state is reviewed."
        )


if __name__ == "__main__":
    main()
