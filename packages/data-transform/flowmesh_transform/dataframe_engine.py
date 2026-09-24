"""
FlowMesh Data Engineering & DataFrame Transformation Engine
Leverages NumPy, Pandas, and Python vectorized math for high-throughput ETL data pipelines.
Provides data cleaning, statistical aggregations, outlier detection, merging, and format serialization.
"""

import math
from typing import List, Dict, Any, Optional

try:
    import numpy as np
    import pandas as pd
    HAS_PANDAS = True
except ImportError:
    HAS_PANDAS = False


class DataFrameEngine:
    """Enterprise ETL data transformation engine for FlowMesh DAG steps."""

    @staticmethod
    def to_dataframe(records: List[Dict[str, Any]]) -> Any:
        """Converts incoming records list to a pandas DataFrame."""
        if not HAS_PANDAS:
            raise RuntimeError("pandas is not available in environment")
        return pd.DataFrame(records)

    @staticmethod
    def clean_records(
        records: List[Dict[str, Any]],
        required_fields: Optional[List[str]] = None,
        default_values: Optional[Dict[str, Any]] = None,
    ) -> List[Dict[str, Any]]:
        """Cleans and sanitizes incoming record batches, removing nulls or filling defaults."""
        if HAS_PANDAS and records:
            df = pd.DataFrame(records)
            if required_fields:
                df = df.dropna(subset=[f for f in required_fields if f in df.columns])
            if default_values:
                df = df.fillna(value=default_values)
            return df.to_dict(orient="records")

        cleaned = []
        req = required_fields or []
        defaults = default_values or {}

        for row in records:
            if any(row.get(f) is None for f in req):
                continue

            sanitized_row = dict(row)
            for key, def_val in defaults.items():
                if sanitized_row.get(key) is None:
                    sanitized_row[key] = def_val

            cleaned.append(sanitized_row)
        return cleaned

    @staticmethod
    def apply_vectorized_multiplier(
        records: List[Dict[str, Any]],
        target_column: str,
        multiplier: float,
        result_column: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """Multiplies numerical column values using vectorized math."""
        if HAS_PANDAS and records:
            df = pd.DataFrame(records)
            out_col = result_column or target_column
            if target_column in df.columns:
                df[out_col] = (pd.to_numeric(df[target_column], errors="coerce").fillna(0.0) * multiplier).round(4)
                return df.to_dict(orient="records")

        out_col = result_column or target_column
        res = []
        for r in records:
            row_copy = dict(r)
            val = row_copy.get(target_column, 0.0)
            try:
                row_copy[out_col] = round(float(val) * multiplier, 4)
            except (ValueError, TypeError):
                row_copy[out_col] = 0.0
            res.append(row_copy)
        return res

    @staticmethod
    def aggregate_by_dimension(
        records: List[Dict[str, Any]],
        group_key: str,
        measure_key: str,
        operation: str = "sum",
    ) -> Dict[str, float]:
        """Performs statistical grouping (sum, mean, min, max, count) using pandas groupby."""
        if HAS_PANDAS and records:
            df = pd.DataFrame(records)
            if group_key in df.columns and measure_key in df.columns:
                df[measure_key] = pd.to_numeric(df[measure_key], errors="coerce").fillna(0.0)
                op = operation.lower()
                agg_map = {"avg": "mean", "sum": "sum", "mean": "mean", "min": "min", "max": "max", "count": "count"}
                func = agg_map.get(op, "sum")
                grouped = df.groupby(group_key)[measure_key].agg(func)
                return {str(k): round(float(v), 2) for k, v in grouped.items()}

        groups: Dict[str, List[float]] = {}
        for r in records:
            k = str(r.get(group_key, "UNKNOWN"))
            v = float(r.get(measure_key, 0.0))
            if k not in groups:
                groups[k] = []
            groups[k].append(v)

        result: Dict[str, float] = {}
        for k, values in groups.items():
            if not values:
                result[k] = 0.0
                continue

            op = operation.lower()
            if op == "sum":
                result[k] = round(sum(values), 2)
            elif op in ("mean", "avg"):
                result[k] = round(sum(values) / len(values), 2)
            elif op == "min":
                result[k] = round(min(values), 2)
            elif op == "max":
                result[k] = round(max(values), 2)
            elif op == "count":
                result[k] = float(len(values))
            else:
                result[k] = round(sum(values), 2)
        return result

    @staticmethod
    def merge_datasets(
        left_records: List[Dict[str, Any]],
        right_records: List[Dict[str, Any]],
        on: str,
        how: str = "inner",
    ) -> List[Dict[str, Any]]:
        """Joins two record streams using pandas merge (e.g., AD users joined with ServiceNow incidents)."""
        if not HAS_PANDAS:
            raise RuntimeError("pandas is required for merge_datasets")
        left_df = pd.DataFrame(left_records)
        right_df = pd.DataFrame(right_records)
        if left_df.empty or right_df.empty:
            return []
        merged_df = pd.merge(left_df, right_df, on=on, how=how)
        return merged_df.to_dict(orient="records")

    @staticmethod
    def statistical_summary(records: List[Dict[str, Any]], columns: Optional[List[str]] = None) -> Dict[str, Any]:
        """Calculates descriptive statistics (mean, std, min, 25%, 50%, 75%, max) via pandas describe()."""
        if not HAS_PANDAS:
            raise RuntimeError("pandas is required for statistical_summary")
        df = pd.DataFrame(records)
        target_cols = [c for c in (columns or df.columns) if c in df.columns]
        desc = df[target_cols].describe().round(3)
        return desc.to_dict()

    @staticmethod
    def detect_outliers_iqr(
        records: List[Dict[str, Any]],
        column: str,
        multiplier: float = 1.5,
    ) -> List[Dict[str, Any]]:
        """Detects data anomalies using Interquartile Range (IQR) method in Pandas."""
        if not HAS_PANDAS:
            return []
        df = pd.DataFrame(records)
        if column not in df.columns or df.empty:
            return []

        series = pd.to_numeric(df[column], errors="coerce").dropna()
        if len(series) < 4:
            return []

        q1 = series.quantile(0.25)
        q3 = series.quantile(0.75)
        iqr = q3 - q1
        lower_bound = q1 - (multiplier * iqr)
        upper_bound = q3 + (multiplier * iqr)

        outlier_mask = (df[column] < lower_bound) | (df[column] > upper_bound)
        outlier_df = df[outlier_mask].copy()
        outlier_df["anomaly_type"] = "IQR_OUTLIER"
        return outlier_df.to_dict(orient="records")

    @staticmethod
    def detect_outliers_zscore(
        records: List[Dict[str, Any]],
        measure_key: str,
        threshold: float = 2.0,
    ) -> List[Dict[str, Any]]:
        """Identifies statistical anomalies using standard normal Z-score."""
        values = []
        for r in records:
            try:
                values.append(float(r.get(measure_key, 0.0)))
            except (ValueError, TypeError):
                pass

        if len(values) < 2:
            return []

        mean_val = sum(values) / len(values)
        variance = sum((x - mean_val) ** 2 for x in values) / len(values)
        std_dev = math.sqrt(variance)

        if std_dev == 0.0:
            return []

        outliers = []
        for r in records:
            val = float(r.get(measure_key, 0.0))
            z_score = abs(val - mean_val) / std_dev
            if z_score > threshold:
                annotated = dict(r)
                annotated["z_score"] = round(z_score, 2)
                outliers.append(annotated)

        return outliers

    @staticmethod
    def export_to_csv(records: List[Dict[str, Any]]) -> str:
        """Serializes records to CSV format string using pandas."""
        if not HAS_PANDAS:
            raise RuntimeError("pandas is required for export_to_csv")
        df = pd.DataFrame(records)
        return df.to_csv(index=False)
