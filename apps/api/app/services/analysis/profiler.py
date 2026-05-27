from __future__ import annotations

from dataclasses import dataclass
from io import BytesIO
from pathlib import Path
from typing import Any
from warnings import catch_warnings, simplefilter

import numpy as np
import pandas as pd

from app.schemas.dataset import DatasetColumnProfile


@dataclass(frozen=True)
class DatasetAnalysisResult:
    row_count: int
    column_count: int
    columns: list[DatasetColumnProfile]
    preview_columns: list[str]
    preview_rows: list[dict[str, Any]]
    summary: dict[str, Any]
    missing_values: dict[str, Any]
    outliers: dict[str, Any]
    correlations: dict[str, Any]
    time_series: dict[str, Any]
    categorical_aggregates: dict[str, Any]


class DatasetProfiler:
    def analyze(self, *, content: bytes, filename: str) -> DatasetAnalysisResult:
        dataframe = self._read_dataframe(content=content, filename=filename)
        dataframe = self._normalize_columns(dataframe)

        row_count = int(len(dataframe))
        column_count = int(len(dataframe.columns))
        columns = [self._profile_column(dataframe, column) for column in dataframe.columns]
        preview_rows = sanitize_json(dataframe.head(50).to_dict(orient="records"))

        return DatasetAnalysisResult(
            row_count=row_count,
            column_count=column_count,
            columns=columns,
            preview_columns=list(map(str, dataframe.columns)),
            preview_rows=preview_rows,
            summary={
                "row_count": row_count,
                "column_count": column_count,
                "numeric_column_count": len(dataframe.select_dtypes(include=["number"]).columns),
                "datetime_column_count": len(dataframe.select_dtypes(include=["datetime"]).columns),
                "duplicate_row_count": int(dataframe.duplicated().sum()) if row_count else 0,
            },
            missing_values=self._missing_values(dataframe),
            outliers=self._outliers(dataframe),
            correlations=self._correlations(dataframe),
            time_series=self._time_series(dataframe),
            categorical_aggregates=self._categorical_aggregates(dataframe),
        )

    def _read_dataframe(self, *, content: bytes, filename: str) -> pd.DataFrame:
        extension = Path(filename).suffix.lower()
        buffer = BytesIO(content)

        if extension == ".csv":
            return pd.read_csv(buffer)
        if extension in {".xls", ".xlsx"}:
            return pd.read_excel(buffer)

        raise ValueError("Unsupported file extension.")

    def _normalize_columns(self, dataframe: pd.DataFrame) -> pd.DataFrame:
        dataframe = dataframe.copy()
        seen: dict[str, int] = {}
        columns: list[str] = []

        for index, column in enumerate(dataframe.columns):
            name = str(column).strip() or f"column_{index + 1}"
            count = seen.get(name, 0)
            seen[name] = count + 1
            columns.append(name if count == 0 else f"{name}_{count + 1}")

        dataframe.columns = columns
        return dataframe

    def _profile_column(self, dataframe: pd.DataFrame, column: str) -> DatasetColumnProfile:
        series = dataframe[column]
        data_type = infer_data_type(series)
        nullable = bool(series.isna().any())
        missing_count = int(series.isna().sum())
        unique_count = int(series.nunique(dropna=True))
        non_null = series.dropna()

        min_value: str | None = None
        max_value: str | None = None
        mean_value: float | None = None
        median_value: float | None = None
        stddev_value: float | None = None
        profile: dict[str, Any] = {}

        if data_type in {"number", "integer"} and not non_null.empty:
            numeric = pd.to_numeric(non_null, errors="coerce").dropna()
            if not numeric.empty:
                min_value = str(sanitize_scalar(numeric.min()))
                max_value = str(sanitize_scalar(numeric.max()))
                mean_value = sanitize_float(numeric.mean())
                median_value = sanitize_float(numeric.median())
                stddev_value = sanitize_float(numeric.std())
                profile["quartiles"] = sanitize_json(numeric.quantile([0.25, 0.5, 0.75]).to_dict())
        elif data_type == "datetime" and not non_null.empty:
            datetime_series = parse_datetime(non_null).dropna()
            if not datetime_series.empty:
                min_value = str(datetime_series.min())
                max_value = str(datetime_series.max())
        elif not non_null.empty:
            top_values = non_null.astype(str).value_counts().head(10).to_dict()
            profile["top_values"] = sanitize_json(top_values)

        return DatasetColumnProfile(
            name=column,
            original_name=column,
            data_type=data_type,
            semantic_type=infer_semantic_type(column, data_type),
            nullable=nullable,
            missing_count=missing_count,
            unique_count=unique_count,
            min_value=min_value,
            max_value=max_value,
            mean_value=mean_value,
            median_value=median_value,
            stddev_value=stddev_value,
            profile=profile,
        )

    def _missing_values(self, dataframe: pd.DataFrame) -> dict[str, Any]:
        missing = dataframe.isna().sum()
        return {
            column: {
                "count": int(count),
                "percentage": round(float(count / len(dataframe) * 100), 2) if len(dataframe) else 0,
            }
            for column, count in missing.items()
            if int(count) > 0
        }

    def _outliers(self, dataframe: pd.DataFrame) -> dict[str, Any]:
        result: dict[str, Any] = {}
        numeric_dataframe = dataframe.select_dtypes(include=["number"])

        for column in numeric_dataframe.columns:
            series = numeric_dataframe[column].dropna()
            if len(series) < 4:
                continue
            q1 = series.quantile(0.25)
            q3 = series.quantile(0.75)
            iqr = q3 - q1
            if iqr == 0:
                continue
            lower = q1 - 1.5 * iqr
            upper = q3 + 1.5 * iqr
            count = int(((series < lower) | (series > upper)).sum())
            if count:
                result[column] = {
                    "method": "iqr",
                    "count": count,
                    "lower_bound": sanitize_float(lower),
                    "upper_bound": sanitize_float(upper),
                }

        return result

    def _correlations(self, dataframe: pd.DataFrame) -> dict[str, Any]:
        numeric_dataframe = dataframe.select_dtypes(include=["number"])
        if len(numeric_dataframe.columns) < 2:
            return {}

        correlation = numeric_dataframe.corr(numeric_only=True).round(4)
        pairs: list[dict[str, Any]] = []
        columns = list(correlation.columns)
        for left_index, left in enumerate(columns):
            for right in columns[left_index + 1 :]:
                value = correlation.loc[left, right]
                if pd.notna(value):
                    pairs.append(
                        {
                            "left": left,
                            "right": right,
                            "correlation": sanitize_float(value),
                        },
                    )

        pairs.sort(key=lambda item: abs(item["correlation"] or 0), reverse=True)
        return {"pairs": pairs[:20]}

    def _time_series(self, dataframe: pd.DataFrame) -> dict[str, Any]:
        result: dict[str, Any] = {}

        for column in dataframe.columns:
            if infer_data_type(dataframe[column]) != "datetime":
                parsed = parse_datetime(dataframe[column])
            else:
                parsed = dataframe[column]

            parsed = parsed.dropna()
            if parsed.empty:
                continue

            result[column] = {
                "min": str(parsed.min()),
                "max": str(parsed.max()),
                "non_null_count": int(len(parsed)),
            }

        return result

    def _categorical_aggregates(self, dataframe: pd.DataFrame) -> dict[str, Any]:
        result: dict[str, Any] = {}
        numeric_columns = list(dataframe.select_dtypes(include=["number"]).columns)
        if not numeric_columns:
            return result

        for column in dataframe.columns:
            if column in numeric_columns:
                continue
            unique_count = dataframe[column].nunique(dropna=True)
            if unique_count == 0 or unique_count > 50:
                continue

            grouped = (
                dataframe.groupby(column, dropna=True)[numeric_columns]
                .mean(numeric_only=True)
                .head(10)
                .round(4)
            )
            result[column] = sanitize_json(grouped.reset_index().to_dict(orient="records"))

        return result


def infer_data_type(series: pd.Series) -> str:
    non_null = series.dropna()
    if non_null.empty:
        return "unknown"
    if pd.api.types.is_bool_dtype(series):
        return "boolean"
    if pd.api.types.is_integer_dtype(series):
        return "integer"
    if pd.api.types.is_numeric_dtype(series):
        return "number"
    if pd.api.types.is_datetime64_any_dtype(series):
        return "datetime"

    numeric = pd.to_numeric(non_null, errors="coerce")
    if numeric.notna().mean() >= 0.9:
        return "integer" if (numeric.dropna() % 1 == 0).all() else "number"

    parsed_dates = parse_datetime(non_null)
    if parsed_dates.notna().mean() >= 0.9:
        return "datetime"

    unique_ratio = non_null.nunique(dropna=True) / len(non_null)
    return "category" if unique_ratio <= 0.2 or non_null.nunique(dropna=True) <= 50 else "string"


def infer_semantic_type(column: str, data_type: str) -> str | None:
    lower = column.lower()
    if "email" in lower:
        return "email"
    if lower.endswith("_id") or lower == "id":
        return "identifier"
    if data_type == "datetime" or "date" in lower or "time" in lower:
        return "time"
    if any(token in lower for token in ["amount", "revenue", "sales", "price", "cost"]):
        return "currency"
    return None


def parse_datetime(series: pd.Series) -> pd.Series:
    with catch_warnings():
        simplefilter("ignore", UserWarning)
        return pd.to_datetime(series, errors="coerce")


def sanitize_float(value: Any) -> float | None:
    if value is None or pd.isna(value):
        return None
    numeric = float(value)
    if np.isinf(numeric) or np.isnan(numeric):
        return None
    return numeric


def sanitize_scalar(value: Any) -> Any:
    if value is None:
        return None
    if isinstance(value, (np.integer,)):
        return int(value)
    if isinstance(value, (np.floating,)):
        return sanitize_float(value)
    if isinstance(value, (pd.Timestamp,)):
        return value.isoformat()
    if pd.isna(value):
        return None
    return value


def sanitize_json(value: Any) -> Any:
    if isinstance(value, dict):
        return {str(key): sanitize_json(item) for key, item in value.items()}
    if isinstance(value, list):
        return [sanitize_json(item) for item in value]
    if isinstance(value, tuple):
        return [sanitize_json(item) for item in value]
    return sanitize_scalar(value)
