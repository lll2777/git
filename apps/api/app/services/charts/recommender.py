from typing import Any

from app.schemas.dataset import DatasetProfileResponse, DatasetPreviewResponse

FIELD_LABELS = {
    "date": "日期",
    "time": "时间",
    "region": "区域",
    "channel": "渠道",
    "category": "分类",
    "product": "产品",
    "customer": "客户",
    "revenue": "收入",
    "sales": "销售额",
    "cost": "成本",
    "profit": "利润",
    "margin": "利润率",
    "quantity": "数量",
    "price": "价格",
    "amount": "金额",
}


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
            for category_column in category_columns[:2]:
                category = category_column.name
                metric = numeric_columns[0].name
                recommendations.append(
                    self._bar_chart(
                        title=f"{field_label(metric)}按{field_label(category)}汇总",
                        category=category,
                        metric=metric,
                        rows=preview.rows,
                        aggregation="sum",
                    ),
                )
                recommendations.append(
                    self._pie_chart(
                        title=f"{field_label(metric)}按{field_label(category)}占比",
                        category=category,
                        metric=metric,
                        rows=preview.rows,
                    ),
                )

            if len(numeric_columns) >= 2:
                recommendations.append(
                    self._bar_chart(
                        title=f"平均{field_label(numeric_columns[1].name)}按{field_label(category_columns[0].name)}对比",
                        category=category_columns[0].name,
                        metric=numeric_columns[1].name,
                        rows=preview.rows,
                        aggregation="avg",
                    ),
                )

        if datetime_columns and numeric_columns:
            date_column = datetime_columns[0].name
            for metric_column in numeric_columns[:2]:
                metric = metric_column.name
                recommendations.append(
                    self._line_chart(
                        title=f"{field_label(metric)}趋势",
                        date_column=date_column,
                        metric=metric,
                        rows=preview.rows,
                    ),
                )

            recommendations.append(
                self._area_chart(
                    title=f"{field_label(numeric_columns[0].name)}累计趋势",
                    date_column=date_column,
                    metric=numeric_columns[0].name,
                    rows=preview.rows,
                ),
            )

            if len(numeric_columns) >= 2:
                recommendations.append(
                    self._composed_chart(
                        title=f"{field_label(numeric_columns[0].name)}与{field_label(numeric_columns[1].name)}趋势对比",
                        date_column=date_column,
                        metrics=[numeric_columns[0].name, numeric_columns[1].name],
                        rows=preview.rows,
                    ),
                )

        if len(numeric_columns) >= 2:
            x_axis = numeric_columns[0].name
            y_axis = numeric_columns[1].name
            recommendations.append(
                self._scatter_chart(
                    title=f"{field_label(y_axis)}与{field_label(x_axis)}关系",
                    x_axis=x_axis,
                    y_axis=y_axis,
                    rows=preview.rows,
                ),
            )

        if category_columns:
            recommendations.append(
                self._count_pie_chart(
                    title=f"{field_label(category_columns[0].name)}分布",
                    category=category_columns[0].name,
                    rows=preview.rows,
                ),
            )

        if not recommendations and numeric_columns:
            metric = numeric_columns[0].name
            recommendations.append(
                self._bar_chart(
                    title=f"{field_label(metric)}最高值",
                    category=preview.columns[0],
                    metric=metric,
                    rows=preview.rows,
                    aggregation="sum",
                ),
            )

        return recommendations[:10]

    def _bar_chart(
        self,
        *,
        title: str,
        category: str,
        metric: str,
        rows: list[dict[str, Any]],
        aggregation: str,
    ) -> dict[str, Any]:
        grouped: dict[str, list[float]] = {}
        for row in rows:
            key = str(row.get(category) or "未知")
            value = to_float(row.get(metric))
            if value is None:
                continue
            grouped.setdefault(key, []).append(value)

        data = [
            {"name": key, "value": round(aggregate_values(values, aggregation), 4)}
            for key, values in sorted(
                grouped.items(),
                key=lambda item: abs(aggregate_values(item[1], aggregation)),
                reverse=True,
            )[:12]
        ]

        return {
            "title": title,
            "chart_type": "bar" if len(data) <= 8 else "horizontal_bar",
            "config": {
                "xKey": "name",
                "yKey": "value",
                "xLabel": field_label(category),
                "yLabel": field_label(metric),
                "data": data,
            },
            "query_spec": {
                "category": category,
                "metric": metric,
                "aggregation": aggregation,
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
        grouped: dict[str, float] = {}
        for row in rows:
            value = to_float(row.get(metric))
            date_value = row.get(date_column)
            if value is None or date_value is None:
                continue
            key = str(date_value)
            grouped[key] = grouped.get(key, 0) + value

        data = [{"name": key, "value": round(value, 4)} for key, value in grouped.items()]
        data.sort(key=lambda item: item["name"])

        return {
            "title": title,
            "chart_type": "line",
            "config": {
                "xKey": "name",
                "yKey": "value",
                "xLabel": field_label(date_column),
                "yLabel": field_label(metric),
                "data": data[:50],
            },
            "query_spec": {
                "date_column": date_column,
                "metric": metric,
                "aggregation": "sum",
            },
        }

    def _area_chart(
        self,
        *,
        title: str,
        date_column: str,
        metric: str,
        rows: list[dict[str, Any]],
    ) -> dict[str, Any]:
        line_chart = self._line_chart(
            title=title,
            date_column=date_column,
            metric=metric,
            rows=rows,
        )
        cumulative = 0.0
        data = []
        for item in line_chart["config"]["data"]:
            cumulative += to_float(item.get("value")) or 0
            data.append({"name": item["name"], "value": round(cumulative, 4)})

        return {
            "title": title,
            "chart_type": "area",
            "config": {
                **line_chart["config"],
                "data": data,
            },
            "query_spec": {
                "date_column": date_column,
                "metric": metric,
                "aggregation": "cumulative_sum",
            },
        }

    def _composed_chart(
        self,
        *,
        title: str,
        date_column: str,
        metrics: list[str],
        rows: list[dict[str, Any]],
    ) -> dict[str, Any]:
        grouped: dict[str, dict[str, float]] = {}
        for row in rows:
            date_value = row.get(date_column)
            if date_value is None:
                continue
            key = str(date_value)
            grouped.setdefault(key, {"name": key})
            for metric in metrics:
                value = to_float(row.get(metric))
                if value is None:
                    continue
                grouped[key][metric] = grouped[key].get(metric, 0) + value

        data = sorted(grouped.values(), key=lambda item: item["name"])[:50]

        return {
            "title": title,
            "chart_type": "composed",
            "config": {
                "xKey": "name",
                "xLabel": field_label(date_column),
                "data": data,
                "series": [
                    {"key": metrics[0], "label": field_label(metrics[0]), "type": "bar"},
                    {"key": metrics[1], "label": field_label(metrics[1]), "type": "line"},
                ],
            },
            "query_spec": {
                "date_column": date_column,
                "metrics": metrics,
                "aggregation": "sum",
            },
        }

    def _pie_chart(
        self,
        *,
        title: str,
        category: str,
        metric: str,
        rows: list[dict[str, Any]],
    ) -> dict[str, Any]:
        grouped: dict[str, float] = {}
        for row in rows:
            key = str(row.get(category) or "未知")
            value = to_float(row.get(metric))
            if value is None:
                continue
            grouped[key] = grouped.get(key, 0) + value

        data = [
            {"name": key, "value": round(value, 4)}
            for key, value in sorted(grouped.items(), key=lambda item: abs(item[1]), reverse=True)[:8]
            if value != 0
        ]

        return {
            "title": title,
            "chart_type": "pie",
            "config": {
                "xKey": "name",
                "yKey": "value",
                "xLabel": field_label(category),
                "yLabel": field_label(metric),
                "data": data,
            },
            "query_spec": {
                "category": category,
                "metric": metric,
                "aggregation": "sum_share",
            },
        }

    def _count_pie_chart(
        self,
        *,
        title: str,
        category: str,
        rows: list[dict[str, Any]],
    ) -> dict[str, Any]:
        grouped: dict[str, float] = {}
        for row in rows:
            key = str(row.get(category) or "未知")
            grouped[key] = grouped.get(key, 0) + 1

        data = [
            {"name": key, "value": value}
            for key, value in sorted(grouped.items(), key=lambda item: item[1], reverse=True)[:8]
        ]

        return {
            "title": title,
            "chart_type": "pie",
            "config": {
                "xKey": "name",
                "yKey": "value",
                "xLabel": field_label(category),
                "yLabel": "记录数",
                "data": data,
            },
            "query_spec": {
                "category": category,
                "aggregation": "count_share",
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
                "xLabel": field_label(x_axis),
                "yLabel": field_label(y_axis),
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


def aggregate_values(values: list[float], aggregation: str) -> float:
    if not values:
        return 0
    if aggregation == "avg":
        return sum(values) / len(values)
    return sum(values)


def field_label(name: str) -> str:
    normalized = name.strip().lower()
    return FIELD_LABELS.get(normalized, name)
