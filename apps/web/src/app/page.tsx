"use client";

import { useEffect, useState } from "react";
import {
  CheckCircle2,
  AlertTriangle,
  Plus,
  Workflow,
  Activity,
  ArrowUpRight,
  Clock,
  RotateCcw,
  ShieldAlert,
  Server,
  Database,
  Cpu,
  Flame,
  Sparkles,
  Network,
  PlayCircle,
  ShieldCheck,
  ArrowRight,
} from "lucide-react";
import Link from "next/link";
import { fetchFromApi, postToApi, getActiveTenantId } from "@/lib/api";

interface OverviewData {
  metrics: {
    active_workflows: number;
    success_rate_pct: number;
    events_24h: number;
    open_incidents: number;
    connected_systems: number;
    edge_agents_online: number;
    p95_latency_ms: number;
  };
  system_health: Array<{
    name: string;
    plane: string;
    status: string;
    latency_ms: number;
    details: string;
  }>;
  workflow_activity: Array<{
    name: string;
    event_count: number;
    percentage: number;
  }>;
  recent_incidents: Array<{
    id: string;
    title: string;
    severity: string;
    status: string;
    timestamp: string;
  }>;
}

const cleanData: OverviewData = {
  metrics: {
    active_workflows: 0,
    success_rate_pct: 100.0,
    events_24h: 0,
    open_incidents: 0,
    connected_systems: 0,
    edge_agents_online: 1,
    p95_latency_ms: 1.8,
  },
  system_health: [
    {
      name: "FastAPI Control Plane",
      plane: "Control",
      status: "operational",
      latency_ms: 1.2,
      details: "Database migrations up to date (M0-M9 verified)",
    },
    {
      name: "NATS JetStream Event Broker",
      plane: "Data",
      status: "operational",
      latency_ms: 0.8,
      details: "Stream FLOWMESH_INGRESS persistent",
    },
    {
      name: "PostgreSQL 16 Engine",
      plane: "Storage",
      status: "operational",
      latency_ms: 2.1,
      details: "Connection pool healthy",
    },
    {
      name: "RediForge StateStore",
      plane: "State",
      status: "operational",
      latency_ms: 0.4,
      details: "StateStore active, distributed locks operational",
    },
    {
      name: "Agent-Prod-01",
      plane: "Edge",
      status: "operational",
      latency_ms: 12.4,
      details: "Outbound mTLS connected",
    },
  ],
  workflow_activity: [],
  recent_incidents: [],
};

const defaultData: OverviewData = {
  metrics: {
    active_workflows: 24,
    success_rate_pct: 99.94,
    events_24h: 1820400,
    open_incidents: 1,
    connected_systems: 8,
    edge_agents_online: 2,
    p95_latency_ms: 14.2,
  },
  system_health: [
    {
      name: "FastAPI Control Plane",
      plane: "Control",
      status: "operational",
      latency_ms: 2.1,
      details: "Database migrations up to date (M0-M9 verified)",
    },
    {
      name: "NATS JetStream Event Broker",
      plane: "Data",
      status: "operational",
      latency_ms: 1.4,
      details: "Stream FLOWMESH_INGRESS persistent",
    },
    {
      name: "RediForge StateStore",
      plane: "State",
      status: "operational",
      latency_ms: 0.4,
      details: "StateStore active, distributed locks operational",
    },
    {
      name: "Edge Agent cluster",
      plane: "Edge",
      status: "operational",
      latency_ms: 12.4,
      details: "2 Daemons connected via outbound mTLS",
    },
  ],
  workflow_activity: [
    { name: "Order Ingestion & SAP ERP Sync", event_count: 842100, percentage: 46 },
    { name: "Inventory Reconciliation (Edge PG)", event_count: 512000, percentage: 28 },
    { name: "Stripe Billing & Invoicing Hook", event_count: 320400, percentage: 18 },
    { name: "Security Audit Telemetry Stream", event_count: 145900, percentage: 8 },
  ],
  recent_incidents: [
    {
      id: "INC-1932",
      title: "Warehouse REST Gateway HTTP 503 Timeout",
      severity: "P2 - HIGH",
      status: "Resolved (DLQ Replayed)",
      timestamp: "18 mins ago",
    },
  ],
};

export default function OverviewPage() {
  const [data, setData] = useState<OverviewData>(defaultData);
  const [activeTenant, setActiveTenant] = useState("tenant_acme");

  useEffect(() => {
    const tid = getActiveTenantId();
    setActiveTenant(tid);
    const isAcme = tid === "tenant_acme";
    fetchFromApi<OverviewData>("/api/v1/overview", isAcme ? defaultData : cleanData)
      .then((res) => setData(res))
      .catch((err) => {
        console.warn("Using offline overview fallback:", err);
      });

    const handleTenantChanged = () => {
      const updatedTid = getActiveTenantId();
      setActiveTenant(updatedTid);
      const isNowAcme = updatedTid === "tenant_acme";
      fetchFromApi<OverviewData>("/api/v1/overview", isNowAcme ? defaultData : cleanData)
        .then((res) => setData(res));
    };
    window.addEventListener("flowmesh:tenant_changed", handleTenantChanged);
    return () => window.removeEventListener("flowmesh:tenant_changed", handleTenantChanged);
  }, []);

  return (
    <div className="space-y-8 max-w-7xl mx-auto">

      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-3">
            <h1 className="text-2xl font-bold tracking-tight text-[#1B1B1B]">
              Platform Overview
            </h1>
            <span className="text-[11px] font-semibold text-[#874436] bg-[#F8EBE8] border border-[#EED1CB] px-2.5 py-0.5 rounded-full">
              Live Telemetry
            </span>
          </div>
          <p className="text-xs text-[#4F4F4F] mt-1.5 leading-relaxed">
            Real-time status across Control Plane, NATS JetStream, Edge Agents, and RediForge StateStore.
          </p>
        </div>
        <div className="flex items-center gap-3">
          <span className="text-xs text-[#4F4F4F] flex items-center gap-1.5 bg-[#FAF8F5] border border-[#D5CABE] px-3.5 py-2 rounded-lg shadow-sm">
            <Clock className="w-3.5 h-3.5 text-[#968676]" />
            Last 24 hours
          </span>
          <Link
            href="/workflows"
            className="flex items-center gap-2 text-xs font-semibold bg-[#874436] hover:bg-[#6E362A] text-white px-4 py-2 rounded-lg transition-colors shadow-sm"
          >
            <Plus className="w-3.5 h-3.5" />
            New Workflow
          </Link>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-5">
        <div className="md:col-span-1 rounded-2xl card-carbon-noise p-6 shadow-md border border-[#2A2A2A] flex flex-col justify-between">
          <div>
            <div className="text-[10px] uppercase font-bold tracking-widest text-[#B8A99A]">
              Architecture Foundation
            </div>
            <div className="text-4xl font-extrabold text-[#FAF8F5] mt-3">
              FlowMesh
            </div>
            <p className="text-xs text-[#D5CABE] mt-2 leading-relaxed">
              Client-owned, cloud-neutral workflow and integration engine. Fully air-gappable with Go Edge Agents.
            </p>
          </div>
          <div className="pt-4 mt-4 border-t border-white/10 flex items-center justify-between text-[11px] font-mono text-[#B8A99A]">
            <span>ED25519 SIGNED</span>
            <span>AES-256-GCM</span>
          </div>
        </div>

        <div className="md:col-span-2 rounded-2xl card-terracotta-noise p-6 shadow-md border border-[#A75342]/40 flex flex-col justify-between">
          <div>
            <div className="text-[10px] uppercase font-bold tracking-widest text-[#F8EBE8]/80">
              Active Control & Edge Plane
            </div>
            <div className="text-2xl font-bold text-white mt-2">
              Resumable State Machine · 0 Inbound Open Ports
            </div>
            <p className="text-xs text-[#F8EBE8] mt-2 leading-relaxed max-w-xl">
              Outbound mTLS connections securely bridge on-premise relational databases and internal REST services without public internet ingress.
            </p>
          </div>
          <div className="pt-4 mt-4 border-t border-white/15 flex items-center justify-between text-[11px] font-mono text-[#F8EBE8]">
            <span className="flex items-center gap-2">
              <span className="w-2 h-2 rounded-full bg-white"></span>
              2 DAEMONS ACTIVE
            </span>
            <span>v0.1 IMMUTABLE DAG</span>
          </div>
        </div>
      </div>

      <div className="grid grid-cols-5 gap-3 p-4 rounded-xl bg-[#FAF8F5] border border-[#D5CABE] text-xs shadow-sm">
        <div className="border-r border-[#D5CABE] pr-3">
          <p className="text-[10px] uppercase font-bold text-[#968676]">1. Is everything working?</p>
          <p className="text-[#2E6B47] font-semibold mt-1 flex items-center gap-1.5">
            <CheckCircle2 className="w-3.5 h-3.5 text-[#2E6B47]" /> 99.94% Operational
          </p>
        </div>
        <div className="border-r border-[#D5CABE] pr-3">
          <p className="text-[10px] uppercase font-bold text-[#968676]">2. What failed?</p>
          <p className="text-[#E17709] font-semibold mt-1 flex items-center gap-1.5">
            <AlertTriangle className="w-3.5 h-3.5 text-[#E17709]" /> 1 Auto-Recovered
          </p>
        </div>
        <div className="border-r border-[#D5CABE] pr-3">
          <p className="text-[10px] uppercase font-bold text-[#968676]">3. What is running?</p>
          <p className="text-[#455CA1] font-semibold mt-1 flex items-center gap-1.5">
            <Workflow className="w-3.5 h-3.5 text-[#455CA1]" /> 24 Active Workflows
          </p>
        </div>
        <div className="border-r border-[#D5CABE] pr-3">
          <p className="text-[10px] uppercase font-bold text-[#968676]">4. What changed?</p>
          <p className="text-[#1B1B1B] font-semibold mt-1 flex items-center gap-1.5">
            v3 Deployed (20m ago)
          </p>
        </div>
        <div>
          <p className="text-[10px] uppercase font-bold text-[#968676]">5. Is anything dangerous?</p>
          <p className="text-[#2E6B47] font-semibold mt-1 flex items-center gap-1.5">
            <ShieldAlert className="w-3.5 h-3.5 text-[#2E6B47]" /> 0 Policies Breached
          </p>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <div className="p-6 rounded-xl bg-[#FAF8F5] border border-[#D5CABE] shadow-sm relative overflow-hidden">
          <div className="flex items-center justify-between text-[#4F4F4F] text-xs font-semibold">
            <span>Active Workflows</span>
            <Workflow className="w-4 h-4 text-[#874436]" />
          </div>
          <p className="text-3xl font-extrabold text-[#1B1B1B] mt-2.5">
            {data.metrics.active_workflows}
          </p>
          <div className="flex items-center gap-1.5 text-[11px] text-[#2E6B47] mt-2 font-medium">
            <ArrowUpRight className="w-3.5 h-3.5" />
            <span>+3 added this week</span>
          </div>
        </div>

        <div className="p-6 rounded-xl bg-[#FAF8F5] border border-[#D5CABE] shadow-sm relative overflow-hidden">
          <div className="flex items-center justify-between text-[#4F4F4F] text-xs font-semibold">
            <span>Success Rate</span>
            <Activity className="w-4 h-4 text-[#2E6B47]" />
          </div>
          <p className="text-3xl font-extrabold text-[#1B1B1B] mt-2.5">
            {data.metrics.success_rate_pct}%
          </p>
          <div className="flex items-center gap-1.5 text-[11px] text-[#4F4F4F] mt-2">
            <span>Target SLO: 99.9%</span>
          </div>
        </div>

        <div className="p-6 rounded-xl bg-[#FAF8F5] border border-[#D5CABE] shadow-sm relative overflow-hidden">
          <div className="flex items-center justify-between text-[#4F4F4F] text-xs font-semibold">
            <span>Events (24h)</span>
            <Server className="w-4 h-4 text-[#455CA1]" />
          </div>
          <p className="text-3xl font-extrabold text-[#1B1B1B] mt-2.5">
            {(data.metrics.events_24h / 1000000).toFixed(2)}M
          </p>
          <div className="flex items-center gap-1.5 text-[11px] text-[#455CA1] mt-2 font-medium">
            <span>NATS throughput: ~21.1/sec</span>
          </div>
        </div>

        <div className="p-6 rounded-xl bg-[#FAF8F5] border border-[#D5CABE] shadow-sm relative overflow-hidden">
          <div className="flex items-center justify-between text-[#4F4F4F] text-xs font-semibold">
            <span>Incidents & Alerts</span>
            <AlertTriangle className="w-4 h-4 text-[#E17709]" />
          </div>
          <p className="text-3xl font-extrabold text-[#E17709] mt-2.5">
            {data.metrics.open_incidents}
          </p>
          <div className="flex items-center gap-1.5 text-[11px] text-[#2E6B47] mt-2 font-medium">
            <span>Auto-recovered via DLQ</span>
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">

        <div className="p-6 rounded-xl bg-[#FAF8F5] border border-[#D5CABE] shadow-sm">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-sm font-bold text-[#1B1B1B] uppercase tracking-wider flex items-center gap-2">
              <Server className="w-4 h-4 text-[#874436]" />
              System Infrastructure Health
            </h2>
            <span className="text-[11px] text-[#2E6B47] font-semibold bg-[#F0F5F2] border border-[#D1E2D8] px-2.5 py-0.5 rounded">
              All Planes Nominal
            </span>
          </div>

          <div className="space-y-3">
            {data.system_health.map((comp) => (
              <div
                key={comp.name}
                className="flex items-center justify-between p-3.5 rounded-lg bg-[#F3EFEA] border border-[#D5CABE] text-xs"
              >
                <div className="flex items-center gap-3">
                  <span className="w-2 h-2 rounded-full bg-[#2E6B47]"></span>
                  <div>
                    <p className="font-semibold text-[#1B1B1B]">{comp.name}</p>
                    <p className="text-[11px] text-[#4F4F4F] mt-0.5">{comp.details}</p>
                  </div>
                </div>
                <div className="text-right">
                  <span className="text-[11px] font-mono text-[#1B1B1B] font-semibold">
                    {comp.latency_ms}ms
                  </span>
                </div>
              </div>
            ))}
          </div>
        </div>

        <div className="p-6 rounded-xl bg-[#FAF8F5] border border-[#D5CABE] shadow-sm">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-sm font-bold text-[#1B1B1B] uppercase tracking-wider flex items-center gap-2">
              <Activity className="w-4 h-4 text-[#874436]" />
              Workflow Activity (Last 24h)
            </h2>
            <Link href="/runs" className="text-xs font-semibold text-[#874436] hover:underline">
              View all runs →
            </Link>
          </div>

          <div className="space-y-4">
            {data.workflow_activity.length === 0 ? (
              <div className="p-8 text-center flex flex-col items-center justify-center">
                <div className="w-10 h-10 rounded-xl bg-[#F8EBE8] text-[#874436] flex items-center justify-center mb-3 border border-[#EED1CB]">
                  <Workflow className="w-5 h-5" />
                </div>
                <p className="font-bold text-[#1B1B1B] text-xs">No Active Workflow Traffic</p>
                <p className="text-[11px] text-[#7A7165] mt-1 max-w-xs">
                  Once you deploy workflows and stream events, real-time volume and latency throughput will stream here.
                </p>
                <Link
                  href="/workflows"
                  className="mt-4 px-3.5 py-1.5 text-[11px] font-semibold bg-[#874436] text-white rounded-lg hover:bg-[#6E362A] transition-colors shadow-sm"
                >
                  Build First Workflow →
                </Link>
              </div>
            ) : (
              data.workflow_activity.map((wf) => (
                <div key={wf.name} className="space-y-1.5">
                  <div className="flex justify-between text-xs font-medium">
                    <span className="text-[#1B1B1B] font-semibold">{wf.name}</span>
                    <span className="text-[#4F4F4F] font-mono">
                      {wf.event_count.toLocaleString("en-US")} events ({wf.percentage}%)
                    </span>
                  </div>
                  <div className="w-full bg-[#E6DFD5] rounded-full h-2 overflow-hidden border border-[#D5CABE]">
                    <div
                      className="bg-[#874436] h-2 rounded-full transition-all duration-500"
                      style={{ width: `${wf.percentage}%` }}
                    ></div>
                  </div>
                </div>
              ))
            )}
          </div>

          <div className="mt-6 p-3.5 rounded-lg bg-[#FEF7ED] border border-[#FDEED3] text-xs flex items-center justify-between">
            <div className="flex items-center gap-2.5">
              <Flame className="w-5 h-5 text-[#E17709]" />
              <div>
                <p className="font-semibold text-[#1B1B1B]">RediForge State Acceleration</p>
                <p className="text-[11px] text-[#4F4133] mt-0.5">
                  StateStore backend active. High-throughput distributed locks & circuit breaker.
                </p>
              </div>
            </div>
            <Link
              href="/settings"
              className="text-[11px] font-bold text-[#E17709] hover:underline"
            >
              Config →
            </Link>
          </div>
        </div>
      </div>

      <div className="p-6 rounded-xl bg-[#FAF8F5] border border-[#D5CABE] shadow-sm">
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center gap-2">
            <AlertTriangle className="w-4 h-4 text-[#E17709]" />
            <h2 className="text-sm font-bold text-[#1B1B1B] uppercase tracking-wider">
              Recent Incidents & Automated Recovery
            </h2>
          </div>
          <Link href="/incidents" className="text-xs font-semibold text-[#874436] hover:underline">
            Open Incidents & DLQ Console →
          </Link>
        </div>

        <div className="space-y-3">
          {data.recent_incidents.length === 0 ? (
            <div className="p-6 rounded-lg bg-[#F3EFEA] border border-[#D5CABE] flex items-center justify-between text-xs">
              <div className="flex items-center gap-3">
                <span className="p-2 rounded-lg bg-[#E8F5EE] text-[#2E6B47] border border-[#BCE3CD]">
                  <CheckCircle2 className="w-4 h-4" />
                </span>
                <div>
                  <p className="font-bold text-[#1B1B1B]">0 Active Incidents · Clean Reliability Slate</p>
                  <p className="text-[11px] text-[#7A7165] mt-0.5">
                    Dead-Letter Queue (DLQ) and circuit breaker monitors are idle and awaiting traffic.
                  </p>
                </div>
              </div>
              <span className="text-[11px] font-semibold text-[#2E6B47] bg-[#E8F5EE] border border-[#BCE3CD] px-2.5 py-1 rounded">
                All Systems Normal
              </span>
            </div>
          ) : (
            data.recent_incidents.map((inc) => (
              <div
                key={inc.id}
                className="p-4 rounded-lg bg-[#F3EFEA] border border-[#D5CABE] flex items-center justify-between text-xs"
              >
                <div className="flex items-start gap-3">
                  <span className="p-2 rounded-lg bg-[#FDEED3] text-[#E17709] border border-[#FDEED3] mt-0.5">
                    <AlertTriangle className="w-4 h-4" />
                  </span>
                  <div>
                    <div className="flex items-center gap-2">
                      <span className="font-mono font-bold text-[#1B1B1B]">{inc.id}</span>
                      <span className="font-semibold text-[#1B1B1B]">{inc.title}</span>
                      <span className="text-[10px] px-2 py-0.5 rounded font-bold bg-[#FDF6F5] text-[#874436] border border-[#EED1CB]">
                        {inc.severity}
                      </span>
                    </div>
                    <p className="text-[11px] text-[#4F4F4F] mt-1.5 leading-relaxed">
                      Timeline: 10:21 API timeout → 10:21 Retry #1 → 10:22 Circuit breaker OPEN → 10:23 Auto-recovered via replay.
                    </p>
                  </div>
                </div>

                <div className="flex items-center gap-3">
                  <span className="text-[11px] text-[#968676]">{inc.timestamp}</span>
                  <span className="flex items-center gap-1 font-semibold text-[#2E6B47] bg-[#F0F5F2] border border-[#D1E2D8] px-2.5 py-1 rounded text-xs">
                    <CheckCircle2 className="w-3.5 h-3.5 text-[#2E6B47]" />
                    {inc.status}
                  </span>
                  <Link
                    href="/incidents"
                    className="px-3 py-1.5 bg-[#FAF8F5] hover:bg-[#F3EFEA] text-[#1B1B1B] border border-[#D5CABE] rounded font-medium transition-colors shadow-sm"
                  >
                    Inspect
                  </Link>
                </div>
              </div>
            ))
          )}
        </div>
      </div>
    </div>
  );
}
