from sqlalchemy import create_engine, inspect, text

from scripts.migrate_v42 import migrate_v42


def test_migrate_v42_adds_project_scope_column_and_index():
    engine = create_engine("sqlite:///:memory:")
    with engine.begin() as connection:
        connection.execute(text(
            "CREATE TABLE iserver_services ("
            "id VARCHAR PRIMARY KEY, user_id VARCHAR NOT NULL, "
            "service_name VARCHAR NOT NULL)"
        ))

    assert "project_id" not in {column["name"] for column in inspect(engine).get_columns("iserver_services")}

    migrate_v42(engine)
    migrate_v42(engine)

    columns = {column["name"] for column in inspect(engine).get_columns("iserver_services")}
    indexes = {index["name"] for index in inspect(engine).get_indexes("iserver_services")}
    assert "project_id" in columns
    assert "ix_iserver_services_project_id" in indexes


def test_migrate_v42_marks_existing_active_services_as_published():
    engine = create_engine("sqlite:///:memory:")
    with engine.begin() as connection:
        connection.execute(text(
            "CREATE TABLE iserver_services ("
            "id VARCHAR PRIMARY KEY, user_id VARCHAR NOT NULL, service_name VARCHAR NOT NULL, "
            "is_active BOOLEAN NOT NULL)"
        ))
        connection.execute(text(
            "INSERT INTO iserver_services (id, user_id, service_name, is_active) "
            "VALUES ('service_legacy', 'user_owner', 'data-owner', 1)"
        ))

    migrate_v42(engine)

    with engine.connect() as connection:
        row = connection.execute(text(
            "SELECT lifecycle_status, dataset_id FROM iserver_services WHERE id = 'service_legacy'"
        )).mappings().one()
    assert row["lifecycle_status"] == "published"
    assert row["dataset_id"] is None
