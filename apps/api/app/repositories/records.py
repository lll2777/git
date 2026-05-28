from __future__ import annotations

from collections.abc import Mapping
from typing import Any
from uuid import UUID


def normalize_record(row: Mapping[str, Any]) -> dict[str, Any]:
    return {key: normalize_value(value) for key, value in row.items()}


def normalize_records(rows: list[Mapping[str, Any]]) -> list[dict[str, Any]]:
    return [normalize_record(row) for row in rows]


def normalize_value(value: Any) -> Any:
    if isinstance(value, UUID):
        return str(value)
    if isinstance(value, list):
        return [normalize_value(item) for item in value]
    if isinstance(value, dict):
        return {key: normalize_value(item) for key, item in value.items()}
    return value
