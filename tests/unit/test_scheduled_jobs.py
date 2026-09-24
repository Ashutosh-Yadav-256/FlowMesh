"""
Unit Tests for FlowMesh Scheduled Jobs & Cron Trigger Engine
Validates 5-part cron parsing, interval evaluation, job registration, and execution dispatch.
"""

from datetime import datetime, timezone
import pytest
from flowmesh_engine.scheduler import CronScheduleParser, WorkflowScheduler, ScheduledJob


def test_cron_schedule_parser():
    # 1. Matching reference time: 2026-09-24 14:30 (Thursday, DOW=4)
    dt_match = datetime(2026, 9, 24, 14, 30, tzinfo=timezone.utc)
    assert CronScheduleParser.is_due("30 14 * * *", dt_match) is True
    assert CronScheduleParser.is_due("0 14 * * *", dt_match) is False

    # 2. Step syntax
    assert CronScheduleParser.is_due("*/15 * * * *", dt_match) is True
    assert CronScheduleParser.is_due("*/20 * * * *", dt_match) is False

    # 3. Special aliases
    dt_top_of_hour = datetime(2026, 9, 24, 15, 0, tzinfo=timezone.utc)
    assert CronScheduleParser.is_due("@hourly", dt_top_of_hour) is True


@pytest.mark.asyncio
async def test_workflow_scheduler_lifecycle():
    sched = WorkflowScheduler()

    # Register
    job = sched.register_job(
        job_id="job_test_01",
        name="Nightly Backup Job",
        schedule="0 2 * * *",
        workflow_id="wf_backup",
        tenant_id="tenant_acme",
    )
    assert job.job_id == "job_test_01"
    assert sched.get_job("job_test_01") is not None

    # List
    jobs = sched.list_jobs(tenant_id="tenant_acme")
    assert len(jobs) == 1
    assert jobs[0]["name"] == "Nightly Backup Job"

    # Manual Trigger
    res = await sched.trigger_now("job_test_01")
    assert res["status"] == "TRIGGERED"
    assert job.run_count == 1
    assert job.last_status == "COMPLETED"

    # Unregister
    assert sched.unregister_job("job_test_01") is True
    assert sched.get_job("job_test_01") is None
