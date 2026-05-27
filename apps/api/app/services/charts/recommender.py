from typing import Any

from app.schemas.dataset import DatasetProfileResponse, DatasetPreviewResponse


class ChartRecommender:
    def recommend(
        self,
        *,
        profile: DatasetProfileResponse,
        preview: DatasetPreviewResponse,
    ) -> list[dict[str, Any]]:
        recommendations: list[dict[str, Any]] = []
        columns = profile.columns
        numeric_columns = [column for column in columns if column.data_type in {"number", "integer"}]
        category_columns = [column for column in columns if column.data_type == "category"]
        datetime_columns = [column for column in columns if column.data_type == "datetime"]

        if category_columns and numeric_columns:
            category = category_columns[0].name
            metric = numeric_columns[0].name
            recommendations.append(
                self._bar_chart(
                    title=f"{metric} by {category}",
                    category=category,
                    metric=metric,
                    rows=preview.rows,
                ),
            )

        if datetime_columns and numeric_columns:
            date_column = datetime_columns[0].name
            metric = numeric_columns[0].name
            recommendations.append(
                self._line_chart(
                    title=f"{metric} over {date_column}",
                    date_column=date_column,
                    metric=metric,
                    rows=preview.rows,
                ),
            )

        if len(numeric_columns) >= 2:
            x_axis = numeric_columns[0].name
            y_axis = numeric_columns[1].name
            recommendations.append(
                self._scatter_chart(
                    title=f"{y_axis} vs {x_axis}",
                    x_axis=x_axis,
                    y_axis=y_axis,
                    rows=preview.rows,
                ),
            )

        if not recommendations and numeric_columns:
            metric = numeric_columns[0].name
            recommendations.append(
                self._bar_chart(
                    title=f"Top {metric} values",
                    category=preview.columns[0],
                    metric=metric,
                    rows=preview.rows,
                ),
            )

        return recommendations[:6]

    def _bar_chart(
        self,
        *,
        title: str,
        category: str,
        metric: str,
        rows: list[dict[str, Any]],
    ) -> dict[str, Any]:
        grouped: dict[str, float] = {}
        for row in rows:
            key = str(row.get(category) or "Unknown")
            value = to_float(row.get(metric))
            if value is None:
                continue
            grouped[key] = grouped.get(key, 0) + value

        data = [
            {"name": key, "value": round(value, 4)}
            for key, value in sorted(grouped.items(), key=lambda item: abs(item[1]), reverse=True)[:12]
        ]

        return {
            "title": title,
            "chart_type": "bar",
            "config": {
                "xKey": "name",
                "yKey": "value",
                "data": data,
            },
            "query_spec": {
                "category": category,
                "metric": metric,
                "aggregation": "sum",
            },
        }

    def _line_chart(
        self,
        *,
        title: str,
        date_column: str,
        metric: str,
        rows: list[dict[str, Any]],
    ) -> dict[str, Any]:
        data = []
        for row in rows:
            value = to_float(row.get(metric))
            date_value = row.get(date_column)
            if value is None or date_value is None:
                continue
            data.append({"name": str(date_value), "value": value})

        data.sort(key=lambda item: item["name"])

        return {
            "title": title,
            "chart_type": "line",
            "config": {
                "xKey": "name",
                "yKey": "value",
                "data": data[:50],
            },
            "query_spec": {
                "date_column": date_column,
                "metric": metric,
                "aggregation": "raw",
            },
        }

    def _scatter_chart(
        self,
        *,
        title: str,
        x_axis: str,
        y_axis: str,
        rows: list[dict[str, Any]],
    ) -> dict[str, Any]:
        data = []
        for row in rows:
            x_value = to_float(row.get(x_axis))
            y_value = to_float(row.get(y_axis))
            if x_value is None or y_value is None:
                continue
            data.append({"x": x_value, "y": y_value})

        return {
            "title": title,
            "chart_type": "scatter",
            "config": {
                "xKey": "x",
                "yKey": "y",
                "data": data[:200],
            },
            "query_spec": {
                "x_axis": x_axis,
                "y_axis": y_axis,
                "aggregation": "raw",
            },
        }


def to_float(value: Any) -> float | None:
    try:
        if value is None or value == "":
            return None
        return float(value)
    except (TypeError, ValueError):
        return None
