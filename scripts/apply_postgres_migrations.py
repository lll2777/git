from __future__ import annotations

import os
from pathlib import Path

from sqlalchemy import create_engine, text


ROOT = Path(__file__).resolve().parents[1]
MIGRATIONS_DIR = ROOT / "infra" / "postgres"


def main() -> None:
    database_url = os.environ.get("DATABASE_URL")
    if not database_url:
        raise SystemExit("DATABASE_URL is required.")

    engine = create_engine(database_url, pool_pre_ping=True)
    migrations = sorted(MIGRATIONS_DIR.glob("*.sql"))
    if not migrations:
        raise SystemExit(f"No migrations found in {MIGRATIONS_DIR}.")

    with engine.begin() as connection:
        connection.execute(
            text(
                """
                create table if not exists schema_migrations (
                  version text primary key,
                  applied_at timestamptz not null default now()
                )
                """,
            ),
        )

        applied = {
            row[0]
            for row in connection.execute(
                text("select version from schema_migrations"),
            )
        }

        for migration in migrations:
            version = migration.name
            if version in applied:
                print(f"skip {version}")
                continue

            print(f"apply {version}")
            connection.exec_driver_sql(migration.read_text(encoding="utf-8"))
            connection.execute(
                text("insert into schema_migrations (version) values (:version)"),
                {"version": version},
            )

    print("migrations complete")


if __name__ == "__main__":
    main()
