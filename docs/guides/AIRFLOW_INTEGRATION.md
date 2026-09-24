# Apache Airflow & FlowMesh Bi-Directional Integration Guide

This guide details how Apache Airflow and FlowMesh operate together in hybrid enterprise data architectures:
1. **FlowMesh triggers Airflow DAGs**: FlowMesh acts as an event ingress/edge engine triggering heavy Airflow batch ETL pipelines.
2. **Airflow triggers FlowMesh DAGs**: Airflow DAGs invoke FlowMesh zero-trust connectors to reach on-premise databases (Oracle, MS SQL Server, IBM MQ) without VPNs or opened firewall ports.

---

## 1. Custom Airflow Operator: `FlowMeshTriggerOperator`

Drop this Python operator into your Airflow `plugins/` directory:

```python
from airflow.models.baseoperator import BaseOperator
import requests

class FlowMeshTriggerOperator(BaseOperator):
    """
    Airflow custom operator that dispatches execution to FlowMesh's zero-trust edge engine.
    """
    def __init__(self, workflow_id: str, tenant_id: str, flowmesh_url: str = "http://flowmesh-api:8000", **kwargs):
        super().__init__(**kwargs)
        self.workflow_id = workflow_id
        self.tenant_id = tenant_id
        self.flowmesh_url = flowmesh_url

    def execute(self, context):
        headers = {
            "X-Tenant-ID": self.tenant_id,
            "Authorization": f"Bearer {context.get('params', {}).get('token', 'secret')}"
        }
        payload = {"triggered_by": f"airflow_dag_{context['dag'].dag_id}"}
        
        response = requests.post(
            f"{self.flowmesh_url}/api/v1/workflows/{self.workflow_id}/execute",
            json=payload,
            headers=headers,
            timeout=30
        )
        response.raise_for_status()
        run_data = response.json()
        self.log.info(f"FlowMesh Workflow Run Initiated: {run_data.get('run_id')}")
        return run_data.get("run_id")
```

---

## 2. Example Airflow DAG

```python
from datetime import datetime
from airflow import DAG
from airflow.operators.python import PythonOperator
from flowmesh_plugin import FlowMeshTriggerOperator

with DAG(
    dag_id="daily_enterprise_ledger_sync",
    start_date=datetime(2026, 1, 1),
    schedule_interval="@daily",
    catchup=False,
) as dag:

    # Step 1: FlowMesh extracts on-premise transactions via Go Edge Agent
    extract_onprem = FlowMeshTriggerOperator(
        task_id="extract_onprem_ledger",
        workflow_id="wf_oracle_extract_daily",
        tenant_id="finance_enterprise"
    )

    # Step 2: Airflow runs Spark/Pandas transformation
    transform_data = PythonOperator(
        task_id="transform_parquet",
        python_callable=lambda: print("Transforming Parquet in Data Lake...")
    )

    extract_onprem >> transform_data
```
