"""Idempotent schema changes introduced by application version 4.2."""

from __future__ import annotations

from sqlalchemy import Engine, inspect, text


def migrate_v42(engine: Engine) -> None:
    """Add project-scoped iServer lifecycle fields without data loss."""
    inspector = inspect(engine)
    if "iserver_services" not in inspector.get_table_names():
        return

    columns = {column["name"] for column in inspector.get_columns("iserver_services")}
    dialect = engine.dialect.name
    with engine.begin() as connection:
        if "project_id" not in columns:
            connection.execute(text("ALTER TABLE iserver_services ADD COLUMN project_id VARCHAR"))
        additions = {
            "dataset_id": "VARCHAR",
            "lifecycle_status": "VARCHAR NOT NULL DEFAULT 'imported'",
            "published_at": "DATETIME",
            "unpublished_at": "DATETIME",
            "last_error": "VARCHAR",
        }
        for name, definition in additions.items():
            if name not in columns:
                connection.execute(text(f"ALTER TABLE iserver_services ADD COLUMN {name} {definition}"))
        if "is_active" in columns:
            connection.execute(text(
                "UPDATE iserver_services SET lifecycle_status = 'published' "
                "WHERE is_active = 1 AND (lifecycle_status IS NULL OR lifecycle_status = 'imported')"
            ))

        index_names = {index["name"] for index in inspect(connection).get_indexes("iserver_services")}
        if "ix_iserver_services_project_id" not in index_names:
            if dialect == "postgresql":
                connection.execute(text(
                    "CREATE INDEX IF NOT EXISTS ix_iserver_services_project_id "
                    "ON iserver_services (project_id)"
                ))
            else:
                connection.execute(text(
                    "CREATE INDEX ix_iserver_services_project_id "
                    "ON iserver_services (project_id)"
                ))
        if "ix_iserver_services_dataset_id" not in index_names:
            connection.execute(text(
                "CREATE INDEX " + ("IF NOT EXISTS " if dialect == "postgresql" else "")
                + "ix_iserver_services_dataset_id ON iserver_services (dataset_id)"
            ))
        if "ix_iserver_services_lifecycle_status" not in index_names:
            connection.execute(text(
                "CREATE INDEX " + ("IF NOT EXISTS " if dialect == "postgresql" else "")
                + "ix_iserver_services_lifecycle_status ON iserver_services (lifecycle_status)"
            ))


if __name__ == "__main__":
    from server.database import engine

    migrate_v42(engine)
    print("v4.2 schema migration complete")
