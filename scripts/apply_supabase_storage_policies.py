from __future__ import annotations

import os
from pathlib import Path

from sqlalchemy import create_engine, text


ROOT = Path(__file__).resolve().parents[1]
POLICY_FILE = ROOT / "infra" / "supabase" / "storage-policies.sql"


def main() -> None:
    database_url = os.environ.get("DATABASE_URL")
    if not database_url:
        raise SystemExit("DATABASE_URL is required.")
    if not POLICY_FILE.exists():
        raise SystemExit(f"Missing storage policy file: {POLICY_FILE}")

    engine = create_engine(database_url, pool_pre_ping=True)
    with engine.begin() as connection:
        connection.exec_driver_sql(POLICY_FILE.read_text(encoding="utf-8"))
        bucket = connection.execute(
            text("select id from storage.buckets where id = 'datasets'"),
        ).scalar_one_or_none()
        policies = list(
            connection.execute(
                text(
                    """
                    select policyname
                    from pg_policies
                    where schemaname = 'storage'
                      and tablename = 'objects'
                      and policyname like 'Authenticated users%dataset%'
                    order by policyname
                    """,
                ),
            ),
        )

    if bucket != "datasets":
        raise SystemExit("Storage bucket was not created.")
    if len(policies) != 4:
        raise SystemExit(f"Expected 4 storage policies, found {len(policies)}.")

    print("storage policies complete")


if __name__ == "__main__":
    main()
