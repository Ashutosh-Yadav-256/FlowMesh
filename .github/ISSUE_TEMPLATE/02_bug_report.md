---
name: "Defect / Bug Report"
about: "Report a reproducible defect with triage severity and root cause details"
title: "[BUG] <Brief summary of defect>"
labels: ["bug", "triage"]
assignees: ""
---

## Defect Information
- **Jira / Linear Issue Key:** `FLOW-____`
- **Severity:** `[P1 - Blocker / Outage | P2 - Critical Function Impaired | P3 - Major | P4 - Minor / Cosmetic]`
- **Environment:** `[Production | Staging | Local Docker Compose]`
- **Service Affected:** `[enterprise-worker | api | web | agent | state-store]`

---

## Steps to Reproduce
1. Submit transaction payload with tenant ID `tenant-acme`...
2. Invoke endpoint `POST /api/v1/enterprise/transactions`...
3. Inspect thread dump or log stream...

---

## Expected vs. Actual Behavior
- **Expected:** [Describe expected outcome]
- **Actual:** [Describe observed error, timeout, or state inconsistency]

---

## Diagnostic Logs & Telemetry
```text
[Paste relevant logs with MDC traceId, exception stack trace, or GC pause alert]
```

---

## Root Cause Hypothesis & Fix Strategy
- **Root Cause Category:** `[Concurrency / Race Condition | Memory Leak | DB Lock Contention | Network Timeout | Logic Error]`
- **Proposed Resolution:** [Technical approach to resolve and prevent regression]
- **Regression Test Required:** [Specify unit or integration test to guard fix]
