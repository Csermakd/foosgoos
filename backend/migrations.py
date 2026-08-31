"""
Tiny forward-only migration helper for SQLite.

SQLAlchemy's `Base.metadata.create_all()` creates *missing tables* but it
will never add a *column* to a table that already exists. The existing
foosball.db predates the match-lifecycle and goal_events work, so without
this the app would boot and then blow up on the first query mentioning
`matches.status`.

This is deliberately not Alembic. There is one database, on one machine,
and every change so far is an additive `ADD COLUMN` with a default. If we
ever need to rename or drop a column, that is the moment to graduate to a
real migration tool.
"""
from sqlalchemy import inspect, text

# table -> column -> the DDL fragment used in "ALTER TABLE .. ADD COLUMN .."
ADDITIVE_COLUMNS = {
    "matches": {
        "status": "VARCHAR(20) NOT NULL DEFAULT 'completed'",
        "started_at": "DATETIME",
        "ended_at": "DATETIME",
        "video_path": "VARCHAR",
    },
    "player_stats": {
        "own_goals": "INTEGER DEFAULT 0",
        "matches_played": "INTEGER DEFAULT 0",
        "matches_won": "INTEGER DEFAULT 0",
    },
}


def run_migrations(engine) -> list:
    """Add any missing columns. Returns a list of the changes applied."""
    applied = []
    inspector = inspect(engine)
    existing_tables = set(inspector.get_table_names())

    with engine.begin() as conn:
        for table, columns in ADDITIVE_COLUMNS.items():
            if table not in existing_tables:
                continue  # create_all() will build it with every column
            present = {c["name"] for c in inspector.get_columns(table)}
            for name, ddl in columns.items():
                if name in present:
                    continue
                conn.execute(text(f"ALTER TABLE {table} ADD COLUMN {name} {ddl}"))
                applied.append(f"{table}.{name}")

        # Rows that existed before the lifecycle columns were added are
        # historical, already-finished matches. Backfill so nothing looks
        # like a stale in-progress game to the vision service.
        if "matches" in existing_tables and applied:
            conn.execute(text(
                "UPDATE matches SET started_at = timestamp "
                "WHERE started_at IS NULL"
            ))
            conn.execute(text(
                "UPDATE matches SET ended_at = timestamp "
                "WHERE ended_at IS NULL AND status = 'completed'"
            ))

    return applied
