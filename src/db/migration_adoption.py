"""Safe adoption helpers for databases created before Alembic."""

from __future__ import annotations

from collections.abc import Collection, Mapping

from sqlalchemy import Engine, MetaData, inspect, text


class ExistingSchemaMismatchError(RuntimeError):
    """Raised when an existing schema does not match the expected baseline."""


BASELINE_TABLES = frozenset(
    {
        "chat_feedback",
        "document_registry",
        "invitations",
        "onboarding_steps",
        "pending_updates",
        "support_tickets",
        "user_module_quizzes",
        "user_section_progress",
        "user_step_progress",
        "users",
    }
)

BASELINE_COLUMNS: Mapping[str, Collection[str]] = {
    "chat_feedback": {"id", "created_at", "user_id", "user_role", "query", "response", "rating"},
    "document_registry": {"id", "s3_key", "filename", "category", "role", "status"},
    "invitations": {"id", "inviter_id", "email", "role", "token"},
    "onboarding_steps": {"id", "role_target", "title", "short_title", "content_version"},
    "pending_updates": {"id", "user_id", "step_id", "is_completed"},
    "support_tickets": {"id", "sender_id", "sender_role", "description", "status"},
    "user_module_quizzes": {"id", "user_id", "module_id", "score", "passed"},
    "user_section_progress": {"id", "user_id", "section_id"},
    "user_step_progress": {"id", "user_id", "step_id"},
    "users": {"id", "email", "hashed_password", "full_name", "role", "status"},
}


def adopt_existing_schema(
    engine: Engine,
    *,
    expected_tables: Collection[str] = BASELINE_TABLES,
    expected_columns: Mapping[str, Collection[str]] | None = None,
    expected_metadata: MetaData | None = None,
    baseline_revision: str = "20260824_01",
) -> str:
    """Stamp a verified pre-Alembic schema at the baseline revision.

    Returns ``empty`` for a fresh database, ``already_versioned`` when Alembic
    already owns the schema, and ``stamped`` after a verified baseline stamp.
    The function never creates or alters application tables.
    """
    existing_tables = set(inspect(engine).get_table_names())
    if "alembic_version" in existing_tables:
        return "already_versioned"
    if not existing_tables:
        return "empty"

    missing = sorted(set(expected_tables) - existing_tables)
    if missing:
        raise ExistingSchemaMismatchError(f"missing required tables: {', '.join(missing)}")

    validate_full_shape = expected_columns is None
    if expected_metadata is None and validate_full_shape:
        from src.db import models  # noqa: F401
        from src.db.base import Base

        expected_metadata = Base.metadata

    required_columns = expected_columns if expected_columns is not None else BASELINE_COLUMNS
    inspector = inspect(engine)
    for table_name in sorted(expected_tables):
        required = set(required_columns.get(table_name, ()))
        if not required:
            continue
        actual_columns = {column["name"]: column for column in inspector.get_columns(table_name)}
        missing_columns = sorted(required - set(actual_columns))
        if missing_columns:
            raise ExistingSchemaMismatchError(f"{table_name} missing required columns: {', '.join(missing_columns)}")

        if expected_metadata is None or table_name not in expected_metadata.tables:
            continue
        expected_table = expected_metadata.tables[table_name]
        columns_to_compare = (
            set(expected_table.columns) if validate_full_shape else {expected_table.c[name] for name in required}
        )
        if validate_full_shape:
            unexpected = sorted(set(actual_columns) - {column.name for column in columns_to_compare})
            if unexpected:
                raise ExistingSchemaMismatchError(f"{table_name} has unexpected columns: {', '.join(unexpected)}")

        for expected_column in columns_to_compare:
            actual_column = actual_columns[expected_column.name]
            actual_type = actual_column["type"]
            if actual_type._type_affinity is not expected_column.type._type_affinity:
                raise ExistingSchemaMismatchError(f"{table_name}.{expected_column.name} type mismatch")
            actual_length = getattr(actual_type, "length", None)
            expected_length = getattr(expected_column.type, "length", None)
            if expected_length is not None and actual_length != expected_length:
                raise ExistingSchemaMismatchError(f"{table_name}.{expected_column.name} length mismatch")
            actual_enum = tuple(getattr(actual_type, "enums", ()) or ())
            expected_enum = tuple(getattr(expected_column.type, "enums", ()) or ())
            if expected_enum and actual_enum != expected_enum:
                raise ExistingSchemaMismatchError(f"{table_name}.{expected_column.name} enum mismatch")
            if not expected_column.primary_key and bool(actual_column["nullable"]) != bool(expected_column.nullable):
                raise ExistingSchemaMismatchError(f"{table_name}.{expected_column.name} nullability mismatch")
            if validate_full_shape and actual_column.get("default") is not None:
                raise ExistingSchemaMismatchError(f"{table_name}.{expected_column.name} default mismatch")

        if validate_full_shape:
            expected_pk = {column.name for column in expected_table.primary_key.columns}
            actual_pk = set(inspector.get_pk_constraint(table_name).get("constrained_columns") or ())
            if actual_pk != expected_pk:
                raise ExistingSchemaMismatchError(f"{table_name} primary key mismatch")

            expected_uniques = {
                (constraint.name, tuple(column.name for column in constraint.columns))
                for constraint in expected_table.constraints
                if constraint.__class__.__name__ == "UniqueConstraint"
            }
            actual_uniques = {
                (constraint.get("name"), tuple(constraint.get("column_names") or ()))
                for constraint in inspector.get_unique_constraints(table_name)
            }
            if actual_uniques != expected_uniques:
                raise ExistingSchemaMismatchError(f"{table_name} unique constraints mismatch")

            expected_indexes = {
                (index.name, tuple(column.name for column in index.columns), bool(index.unique))
                for index in expected_table.indexes
            }
            actual_indexes = {
                (index.get("name"), tuple(index.get("column_names") or ()), bool(index.get("unique")))
                for index in inspector.get_indexes(table_name)
                if not index.get("duplicates_constraint")
            }
            if actual_indexes != expected_indexes:
                raise ExistingSchemaMismatchError(f"{table_name} indexes mismatch")

            expected_foreign_keys = {
                (
                    tuple(element.parent.name for element in constraint.elements),
                    constraint.elements[0].column.table.name,
                    tuple(element.column.name for element in constraint.elements),
                )
                for constraint in expected_table.foreign_key_constraints
            }
            actual_foreign_keys = {
                (
                    tuple(foreign_key.get("constrained_columns") or ()),
                    foreign_key.get("referred_table"),
                    tuple(foreign_key.get("referred_columns") or ()),
                )
                for foreign_key in inspector.get_foreign_keys(table_name)
            }
            if actual_foreign_keys != expected_foreign_keys:
                raise ExistingSchemaMismatchError(f"{table_name} foreign keys mismatch")

    with engine.begin() as connection:
        connection.execute(text("CREATE TABLE alembic_version (version_num VARCHAR(32) NOT NULL PRIMARY KEY)"))
        connection.execute(
            text("INSERT INTO alembic_version (version_num) VALUES (:revision)"),
            {"revision": baseline_revision},
        )
    return "stamped"
