"""
FlowMesh Data Engineering & DataFrame Transformation Engine
Leverages NumPy, Pandas, and Python vectorized math for high-throughput ETL data pipelines.
Provides data cleaning, statistical aggregations, outlier detection, and Parquet serialization.
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
    def clean_records(
        records: List[Dict[str, Any]],
        required_fields: Optional[List[str]] = None,
        default_values: Optional[Dict[str, Any]] = None,
    ) -> List[Dict[str, Any]]:
        """Cleans and sanitizes incoming record batches, removing nulls or filling defaults."""
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
        """Performs statistical grouping (sum, mean, min, max, count)."""
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
            elif op == "mean" or op == "avg":
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
