"""
Unit Tests for FlowMesh Pandas DataFrame Transformation Engine
Validates DataFrame conversions, statistical summaries, joins, and IQR anomaly detection.
"""

import pytest
import pandas as pd
from flowmesh_transform.dataframe_engine import DataFrameEngine


def test_dataframe_conversions_and_cleaning():
    raw_records = [
        {"id": 1, "name": "srv-01", "cpu_pct": 45.2, "status": "UP"},
        {"id": 2, "name": "srv-02", "cpu_pct": None, "status": None},
        {"id": 3, "name": None, "cpu_pct": 89.1, "status": "UP"},
    ]

    # Convert to DataFrame
    df = DataFrameEngine.to_dataframe(raw_records)
    assert isinstance(df, pd.DataFrame)
    assert len(df) == 3

    # Clean records
    cleaned = DataFrameEngine.clean_records(
        raw_records,
        required_fields=["name"],
        default_values={"cpu_pct": 0.0, "status": "UNKNOWN"},
    )
    assert len(cleaned) == 2
    assert cleaned[1]["cpu_pct"] == 0.0
    assert cleaned[1]["status"] == "UNKNOWN"


def test_dataframe_vectorized_multiplier():
    records = [{"item": "compute_unit", "cost": 10.0}, {"item": "storage_gb", "cost": 0.25}]
    scaled = DataFrameEngine.apply_vectorized_multiplier(
        records, target_column="cost", multiplier=1.15, result_column="cost_with_tax"
    )
    assert scaled[0]["cost_with_tax"] == 11.5
    assert scaled[1]["cost_with_tax"] == 0.2875


def test_dataframe_aggregate_by_dimension():
    records = [
        {"datacenter": "us-east", "latency_ms": 12.0},
        {"datacenter": "us-east", "latency_ms": 16.0},
        {"datacenter": "eu-central", "latency_ms": 45.0},
    ]
    mean_latencies = DataFrameEngine.aggregate_by_dimension(
        records, group_key="datacenter", measure_key="latency_ms", operation="mean"
    )
    assert mean_latencies["us-east"] == 14.0
    assert mean_latencies["eu-central"] == 45.0


def test_dataframe_merge_datasets():
    # Merge Active Directory users with ServiceNow Incidents
    ad_users = [
        {"username": "jdoe", "department": "Platform Eng", "email": "jdoe@acme.corp"},
        {"username": "asmith", "department": "Security Ops", "email": "asmith@acme.corp"},
    ]
    snow_incidents = [
        {"incident_id": "INC001", "assigned_to": "jdoe", "priority": "P1"},
        {"incident_id": "INC002", "assigned_to": "jdoe", "priority": "P2"},
        {"incident_id": "INC003", "assigned_to": "asmith", "priority": "P3"},
    ]

    merged = DataFrameEngine.merge_datasets(
        left_records=snow_incidents,
        right_records=ad_users,
        on="username",
        how="inner",
    ) if "username" in snow_incidents[0] else DataFrameEngine.merge_datasets(
        left_records=[{"username": r["assigned_to"], **r} for r in snow_incidents],
        right_records=ad_users,
        on="username",
        how="inner",
    )

    assert len(merged) == 3
    assert merged[0]["department"] in ("Platform Eng", "Security Ops")


def test_dataframe_iqr_outlier_detection():
    # 9 normal measurements around 20ms and 1 extreme spike at 250ms
    latency_series = [
        {"req_id": f"req_{i}", "latency": 20.0 + (i % 3)} for i in range(10)
    ]
    latency_series.append({"req_id": "req_spike", "latency": 250.0})

    outliers = DataFrameEngine.detect_outliers_iqr(latency_series, column="latency", multiplier=1.5)
    assert len(outliers) == 1
    assert outliers[0]["req_id"] == "req_spike"
    assert outliers[0]["anomaly_type"] == "IQR_OUTLIER"


def test_dataframe_export_to_csv():
    records = [{"a": 1, "b": "hello"}, {"a": 2, "b": "world"}]
    csv_str = DataFrameEngine.export_to_csv(records)
    assert "a,b" in csv_str
    assert "1,hello" in csv_str
