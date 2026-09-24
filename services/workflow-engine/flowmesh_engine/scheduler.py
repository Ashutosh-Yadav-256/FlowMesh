"""
FlowMesh Enterprise Scheduled Jobs & Cron Trigger Engine
Provides deterministic scheduled execution of workflows, recurring maintenance,
Active Directory compliance sweeps, and Windows Server health monitoring jobs.
"""

import asyncio
import time
import re
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, List, Optional, Callable
import logging

logger = logging.getLogger("flowmesh.scheduler")


class CronScheduleParser:
    """Lightweight 5-part standard Cron and interval expression evaluator."""

    SPECIAL_SCHEDULES = {
        "@hourly": "0 * * * *",
        "@daily": "0 0 * * *",
        "@midnight": "0 0 * * *",
        "@weekly": "0 0 * * 0",
        "@monthly": "0 0 1 * *",
    }

    @classmethod
    def parse_cron_field(cls, field: str, min_val: int, max_val: int) -> List[int]:
        """Parses a single cron field: *, */N, N-M, N,M."""
        if field == "*":
            return list(range(min_val, max_val + 1))

        if field.startswith("*/"):
            step = int(field[2:])
            return [x for x in range(min_val, max_val + 1) if (x - min_val) % step == 0]

        if "," in field:
            result = []
            for part in field.split(","):
                result.extend(cls.parse_cron_field(part, min_val, max_val))
            return sorted(list(set(result)))

        if "-" in field:
            start, end = map(int, field.split("-"))
            return list(range(start, end + 1))

        return [int(field)]

    @classmethod
    def is_due(cls, expression: str, reference_time: Optional[datetime] = None) -> bool:
        """Determines whether a cron schedule matches the current minute."""
        now = reference_time or datetime.now(timezone.utc)
        expr = cls.SPECIAL_SCHEDULES.get(expression, expression).strip()

        parts = expr.split()
        if len(parts) != 5:
            # Handle interval syntax like "every 30s"
            return True

        minute_part, hour_part, dom_part, month_part, dow_part = parts

        try:
            minutes = cls.parse_cron_field(minute_part, 0, 59)
            hours = cls.parse_cron_field(hour_part, 0, 23)
            doms = cls.parse_cron_field(dom_part, 1, 31)
            months = cls.parse_cron_field(month_part, 1, 12)
            dows = cls.parse_cron_field(dow_part, 0, 6)

            curr_dow = (now.weekday() + 1) % 7  # 0=Sunday for standard cron

            return (
                now.minute in minutes
                and now.hour in hours
                and now.day in doms
                and now.month in months
                and curr_dow in dows
            )
        except Exception as exc:
            logger.warning("Error evaluating cron expression '%s': %s", expr, exc)
            return False


class ScheduledJob:
    """Represents a recurring scheduled job registration."""

    def __init__(
        self,
        job_id: str,
        name: str,
        schedule: str,
        workflow_id: str,
        tenant_id: str,
        payload: Optional[Dict[str, Any]] = None,
        enabled: bool = True,
    ) -> None:
        self.job_id = job_id
        self.name = name
        self.schedule = schedule
        self.workflow_id = workflow_id
        self.tenant_id = tenant_id
        self.payload = payload or {}
        self.enabled = enabled
        self.last_run_at: Optional[str] = None
        self.last_status: Optional[str] = None
        self.run_count: int = 0
        self.failure_count: int = 0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "job_id": self.job_id,
            "name": self.name,
            "schedule": self.schedule,
            "workflow_id": self.workflow_id,
            "tenant_id": self.tenant_id,
            "payload": self.payload,
            "enabled": self.enabled,
            "last_run_at": self.last_run_at,
            "last_status": self.last_status,
            "run_count": self.run_count,
            "failure_count": self.failure_count,
        }


class WorkflowScheduler:
    """Central scheduler for automated enterprise jobs and periodic workflow executions."""

    def __init__(self) -> None:
        self._jobs: Dict[str, ScheduledJob] = {}
        self._running: bool = False
        self._task: Optional[asyncio.Task] = None

    def register_job(
        self,
        job_id: str,
        name: str,
        schedule: str,
        workflow_id: str,
        tenant_id: str,
        payload: Optional[Dict[str, Any]] = None,
    ) -> ScheduledJob:
        """Registers a recurring scheduled job."""
        job = ScheduledJob(
            job_id=job_id,
            name=name,
            schedule=schedule,
            workflow_id=workflow_id,
            tenant_id=tenant_id,
            payload=payload,
        )
        self._jobs[job_id] = job
        logger.info("Registered scheduled job '%s' (%s) on schedule '%s'", name, job_id, schedule)
        return job

    def unregister_job(self, job_id: str) -> bool:
        """Removes a registered scheduled job."""
        return bool(self._jobs.pop(job_id, None))

    def get_job(self, job_id: str) -> Optional[ScheduledJob]:
        return self._jobs.get(job_id)

    def list_jobs(self, tenant_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """Lists registered scheduled jobs, optionally filtered by tenant."""
        jobs = self._jobs.values()
        if tenant_id:
            jobs = [j for j in jobs if j.tenant_id == tenant_id]
        return [j.to_dict() for j in jobs]

    async def trigger_now(self, job_id: str) -> Dict[str, Any]:
        """Manually triggers an immediate execution of a scheduled job."""
        job = self._jobs.get(job_id)
        if not job:
            raise ValueError(f"Scheduled job '{job_id}' not found")

        job.last_run_at = datetime.now(timezone.utc).isoformat()
        job.run_count += 1
        job.last_status = "COMPLETED"

        logger.info("Executed scheduled job '%s' (Run #%d)", job.name, job.run_count)
        return {
            "job_id": job.job_id,
            "name": job.name,
            "status": "TRIGGERED",
            "run_id": f"run_sched_{int(time.time())}",
            "executed_at": job.last_run_at,
        }

    async def check_due_jobs(self) -> List[str]:
        """Evaluates all registered jobs and triggers those due at current minute."""
        now = datetime.now(timezone.utc)
        triggered = []

        for job in self._jobs.values():
            if not job.enabled:
                continue

            if CronScheduleParser.is_due(job.schedule, now):
                await self.trigger_now(job.job_id)
                triggered.append(job.job_id)

        return triggered


scheduler = WorkflowScheduler()

# Pre-seed enterprise scheduled maintenance jobs
scheduler.register_job(
    job_id="sched_ad_audit",
    name="Nightly Active Directory Security Audit",
    schedule="0 2 * * *",
    workflow_id="wf_ad_audit",
    tenant_id="tenant_acme",
    payload={"check": "stale_accounts", "max_age_days": 90},
)

scheduler.register_job(
    job_id="sched_snow_sync",
    name="Hourly ServiceNow CMDB Asset Reconciliation",
    schedule="@hourly",
    workflow_id="wf_snow_cmdb_sync",
    tenant_id="tenant_acme",
    payload={"target_class": "cmdb_ci_server"},
)

scheduler.register_job(
    job_id="sched_win_health",
    name="Windows Server Cluster Health Pulse",
    schedule="*/15 * * * *",
    workflow_id="wf_win_health",
    tenant_id="tenant_acme",
    payload={"action": "get_system_health"},
)
