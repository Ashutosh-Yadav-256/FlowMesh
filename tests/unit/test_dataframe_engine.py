"""
Unit tests for DataFrameEngine (NumPy, Pandas, Vectorized ETL Transformations)
"""

from flowmesh_transform.dataframe_engine import DataFrameEngine


def test_clean_records():
    raw = [
        {"id": 1, "name": "Alpha", "balance": 100.0},
        {"id": 2, "name": None, "balance": 200.0},
        {"id": 3, "name": "Gamma", "balance": None},
    ]
    cleaned = DataFrameEngine.clean_records(
        raw,
        required_fields=["name"],
        default_values={"balance": 0.0}
    )
    assert len(cleaned) == 2
    assert cleaned[0]["id"] == 1
    assert cleaned[1]["id"] == 3
    assert cleaned[1]["balance"] == 0.0


def test_vectorized_multiplier():
    records = [{"val": 10.0}, {"val": 25.5}, {"val": "invalid"}]
    res = DataFrameEngine.apply_vectorized_multiplier(records, target_column="val", multiplier=2.0)
    assert len(res) == 3
    assert res[0]["val"] == 20.0
    assert res[1]["val"] == 51.0
    assert res[2]["val"] == 0.0


def test_aggregation_by_dimension():
    txns = [
        {"region": "US-EAST", "amount": 100.0},
        {"region": "US-EAST", "amount": 150.0},
        {"region": "EU-WEST", "amount": 300.0},
    ]
    sum_res = DataFrameEngine.aggregate_by_dimension(txns, "region", "amount", "sum")
    assert sum_res["US-EAST"] == 250.0
    assert sum_res["EU-WEST"] == 300.0

    avg_res = DataFrameEngine.aggregate_by_dimension(txns, "region", "amount", "mean")
    assert avg_res["US-EAST"] == 125.0
    assert avg_res["EU-WEST"] == 300.0


def test_outlier_detection_zscore():
    dataset = [{"id": i, "val": 100.0 + (i % 5)} for i in range(20)]
    dataset.append({"id": 99, "val": 10000.0})

    outliers = DataFrameEngine.detect_outliers_zscore(dataset, measure_key="val", threshold=3.0)
    assert len(outliers) == 1
    assert outliers[0]["id"] == 99
    assert outliers[0]["z_score"] > 3.0
