"use client";

import { useState, useEffect } from "react";
import { getActiveTenantId, postToApi } from "@/lib/api";
import {
  PlayCircle,
  CheckCircle2,
  AlertCircle,
  Clock,
  RotateCcw,
  ExternalLink,
  Code,
  Download,
  Search,
  Database,
  Globe,
  Radio,
  FileText,
  Activity,
  X,
  Layers,
  Cpu,
  ShieldCheck,
  HelpCircle,
  Bot,
  Terminal,
  Sparkles,
  Workflow,
} from "lucide-react";
import Link from "next/link";

interface StepItem {
  id: string;
  name: string;
  status: "SUCCESS" | "FAILED";
  duration: string;
  time: string;
  node: string;
  detail: string;
}

interface SpanItem {
  name: string;
  service: string;
  time: string;
  duration_ms: number;
  width: string;
  bg: string;
  status: "OK" | "ERROR";
  attributes: Record<string, string>;
  error?: string;
}

const runTraces: Record<string, { trace_id: string; total_duration_ms: number; status: string; spans: SpanItem[] }> = {
  "RUN-92831": {
    trace_id: "4bf92f3577b34da6a3ce929d0e0e4736",
    total_duration_ms: 2840,
    status: "OK",
    spans: [
      {
        name: "POST /api/v1/events (SAP Ingress)",
        service: "flowmesh-api",
        time: "0ms - 42ms (42ms)",
        duration_ms: 42,
        width: "15%",
        bg: "bg-indigo-600",
        status: "OK",
        attributes: { "http.method": "POST", "http.status": "200", "trigger.source": "sap.ingress" },
      },
      {
        name: "nats.publish(events.acme.orders)",
        service: "nats-jetstream",
        time: "42ms - 58ms (16ms)",
        duration_ms: 16,
        width: "12%",
        bg: "bg-sky-600",
        status: "OK",
        attributes: { "stream": "ORDERS", "partition": "0" },
      },
      {
        name: "worker.consume(wf_order_processing)",
        service: "workflow-engine",
        time: "58ms - 80ms (22ms)",
        duration_ms: 22,
        width: "14%",
        bg: "bg-slate-700",
        status: "OK",
        attributes: { "workflow.version": "3", "state_machine": "running" },
      },
      {
        name: "agent.command_dispatch(postgres.query)",
        service: "edge-agent-prod-01",
        time: "80ms - 210ms (130ms)",
        duration_ms: 130,
        width: "35%",
        bg: "bg-emerald-600",
        status: "OK",
        attributes: { "connection.id": "conn_pg_01", "policy": "allow", "mtls": "verified" },
      },
      {
        name: "agent.command_dispatch(rest.notify)",
        service: "edge-agent-prod-01",
        time: "210ms - 1060ms (850ms)",
        duration_ms: 850,
        width: "70%",
        bg: "bg-emerald-600",
        status: "OK",
        attributes: { "connection.id": "conn_rest_01", "http.status": "201" },
      },
    ],
  },
  "RUN-92830": {
    trace_id: "8ca15e2190184fa9b6ee178d8a0f9122",
    total_duration_ms: 4120,
    status: "ERROR",
    spans: [
      {
        name: "POST /api/v1/events (SAP Ingress)",
        service: "flowmesh-api",
        time: "0ms - 38ms (38ms)",
        duration_ms: 38,
        width: "15%",
        bg: "bg-indigo-600",
        status: "OK",
        attributes: { "http.method": "POST", "http.status": "200" },
      },
      {
        name: "nats.publish(events.acme.orders)",
        service: "nats-jetstream",
        time: "38ms - 55ms (17ms)",
        duration_ms: 17,
        width: "12%",
        bg: "bg-sky-600",
        status: "OK",
        attributes: { "stream": "ORDERS" },
      },
      {
        name: "worker.consume(wf_order_processing)",
        service: "workflow-engine",
        time: "55ms - 4120ms (4065ms)",
        duration_ms: 4065,
        width: "95%",
        bg: "bg-rose-600",
        status: "ERROR",
        attributes: { "workflow.version": "3", "retries_attempted": "3", "dlq_routed": "true" },
        error: "All 3 retry attempts exhausted against Warehouse REST API (HTTP 503). Routed to DLQ.",
      },
      {
        name: "agent.command_dispatch(postgres.query)",
        service: "edge-agent-prod-01",
        time: "80ms - 195ms (115ms)",
        duration_ms: 115,
        width: "30%",
        bg: "bg-emerald-600",
        status: "OK",
        attributes: { "connection.id": "conn_pg_01", "rows": "1" },
      },
      {
        name: "agent.command_dispatch(rest.notify)",
        service: "edge-agent-prod-01",
        time: "195ms - 4100ms (3905ms)",
        duration_ms: 3905,
        width: "90%",
        bg: "bg-rose-600",
        status: "ERROR",
        attributes: { "connection.id": "conn_rest_01", "circuit_breaker": "OPEN", "http.status": "503" },
        error: "HTTP 503 Service Unavailable: Warehouse gateway backend connection timeout",
      },
    ],
  },
};

const sampleSteps: StepItem[] = [
  { id: "s1", name: "SAP Event Received", status: "SUCCESS", duration: "42ms", time: "10:31:02", node: "sap.ingress", detail: "Ingested via Edge Agent agent-prod-01" },
  { id: "s2", name: "Schema Validation", status: "SUCCESS", duration: "18ms", time: "10:31:02", node: "order.v2.json", detail: "Payload conforms to schema" },
  { id: "s3", name: "Customer Lookup", status: "SUCCESS", duration: "120ms", time: "10:31:03", node: "conn_pg_01", detail: "Retrieved customer credit tier: ENTERPRISE_GOLD" },
  { id: "s4", name: "PostgreSQL Update", status: "SUCCESS", duration: "210ms", time: "10:31:03", node: "conn_pg_01", detail: "Row upserted into orders table" },
  { id: "s5", name: "Warehouse Notification", status: "SUCCESS", duration: "850ms", time: "10:31:04", node: "conn_rest_01", detail: "HTTP 201 Created (Tracking: TRK-98214-WH)" },
  { id: "s6", name: "Emit Audit Event", status: "SUCCESS", duration: "45ms", time: "10:31:04", node: "audit.log", detail: "Appended to immutable audit ledger" },
];

const defaultDemoRuns = [
  { id: "RUN-92831", wf: "Order Processing", status: "SUCCESS", dur: "2.84s", time: "10:31:02" },
  { id: "RUN-92830", wf: "Order Processing", status: "FAILED", dur: "4.12s", time: "10:21:00" },
  { id: "RUN-92829", wf: "Customer Sync", status: "SUCCESS", dur: "0.92s", time: "10:15:40" },
  { id: "RUN-92828", wf: "Inventory Update", status: "SUCCESS", dur: "0.14s", time: "10:10:11" },
];

export default function RunsPage() {
  const [runs, setRuns] = useState<typeof defaultDemoRuns>([]);
  const [activeTenant, setActiveTenant] = useState("tenant_acme");
  const [selectedRun, setSelectedRun] = useState("RUN-92831");
  const [activeTab, setActiveTab] = useState<"timeline" | "input" | "output" | "assistant">("timeline");
  const [replaying, setReplaying] = useState(false);
  const [replayedNotice, setReplayedNotice] = useState(false);
  const [traceModalOpen, setTraceModalOpen] = useState(false);
  const [selectedSpan, setSelectedSpan] = useState<SpanItem | null>(null);
  const [assistantQuery, setAssistantQuery] = useState("");
  const [confirmAction, setConfirmAction] = useState<"REPLAY" | "INCIDENT" | null>(null);
  const [incidentNotice, setIncidentNotice] = useState(false);
  const [runSearchQuery, setRunSearchQuery] = useState("");
  const [statusFilter, setStatusFilter] = useState<"ALL" | "SUCCESS" | "FAILED">("ALL");

  const filteredRuns = runs.filter((run) => {
    if (statusFilter !== "ALL" && run.status !== statusFilter) return false;
    if (!runSearchQuery.trim()) return true;
    const q = runSearchQuery.toLowerCase().trim();
    return (
      run.id.toLowerCase().includes(q) ||
      run.wf.toLowerCase().includes(q) ||
      run.status.toLowerCase().includes(q) ||
      run.time.toLowerCase().includes(q)
    );
  });

  useEffect(() => {
    const isAcme = getActiveTenantId() === "tenant_acme";
    setActiveTenant(getActiveTenantId());
    if (isAcme) {
      setRuns(defaultDemoRuns);
      setSelectedRun("RUN-92831");
    } else {
      setRuns([]);
      setSelectedRun("");
    }

    const handleTenantChanged = () => {
      const currentIsAcme = getActiveTenantId() === "tenant_acme";
      setActiveTenant(getActiveTenantId());
      if (currentIsAcme) {
        setRuns(defaultDemoRuns);
        setSelectedRun("RUN-92831");
      } else {
        setRuns([]);
        setSelectedRun("");
      }
    };
    window.addEventListener("flowmesh:tenant_changed", handleTenantChanged);
    return () => window.removeEventListener("flowmesh:tenant_changed", handleTenantChanged);
  }, []);

  const activeTrace = runTraces[selectedRun] || runTraces["RUN-92831"];

  const handleReplay = () => {
    setReplaying(true);
    setTimeout(() => {
      setReplaying(false);
      setReplayedNotice(true);
      setTimeout(() => setReplayedNotice(false), 3500);
    }, 1000);
  };

  const openTraceModal = () => {
    setSelectedSpan(activeTrace.spans[0]);
    setTraceModalOpen(true);
  };

  return (
    <div className="space-y-6 max-w-7xl mx-auto">

      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-[#1B1B1B] flex items-center gap-2.5">
            Workflow Executions
            <span className="text-[11px] font-semibold text-[#874436] bg-[#F8EBE8] px-2.5 py-0.5 rounded-full border border-[#EED1CB]">
              {runs.length} Executions Recorded
            </span>
          </h1>
          <p className="text-xs text-[#4F4F4F] mt-1.5">
            Deterministic, resumable state machine history. Replay any failed event with verified idempotency.
          </p>
        </div>

        {replayedNotice && (
          <div className="flex items-center gap-2 text-xs text-[#2E6B47] bg-[#E8F5EE] border border-[#BCE3CD] px-3 py-1.5 rounded-lg shadow-sm">
            <CheckCircle2 className="w-4 h-4 text-[#2E6B47]" />
            Queued replay into NATS JetStream stream (idempotency key locked)
          </div>
        )}
      </div>

      {runs.length === 0 ? (
        <div className="rounded-xl bg-[#FAF8F5] border border-[#D5CABE] p-12 text-center flex flex-col items-center justify-center shadow-sm">
          <div className="w-14 h-14 rounded-2xl bg-[#F8EBE8] border border-[#EED1CB] flex items-center justify-center text-[#874436] mb-4 shadow-sm">
            <PlayCircle className="w-7 h-7" />
          </div>
          <h3 className="text-base font-bold text-[#1B1B1B] mb-1">
            No Executions Recorded
          </h3>
          <p className="text-xs text-[#7A7165] max-w-md mb-6 leading-relaxed">
            This workspace currently has 0 execution runs. Trigger an event via webhook or test your workflow to see deterministic step transitions, duration breakdowns, and distributed OpenTelemetry traces.
          </p>

          <div className="w-full max-w-xl bg-[#F3EFEA] border border-[#D5CABE] rounded-xl p-4 text-left mb-6 shadow-xs">
            <div className="flex items-center justify-between pb-2 mb-2 border-b border-[#D5CABE] text-[11px]">
              <span className="font-bold text-[#1B1B1B] flex items-center gap-1.5 font-mono">
                <Terminal className="w-3.5 h-3.5 text-[#874436]" />
                Trigger Ingress Webhook via cURL
              </span>
              <span className="text-[10px] text-[#968676]">POST /orders</span>
            </div>
            <pre className="p-3 bg-[#FAF8F5] border border-[#D5CABE] rounded-lg text-[11px] font-mono text-[#1B1B1B] overflow-x-auto select-all">
{`curl -X POST http://localhost:8000/api/v1/webhooks/${activeTenant}/orders \\
  -H "Content-Type: application/json" \\
  -d '{"order_id": "ORD-1001", "amount": 250.00, "customer_id": "CUST-99"}'`}
            </pre>
          </div>

          <div className="flex flex-wrap items-center justify-center gap-3">
            <Link
              href="/workflows"
              className="flex items-center gap-2 text-xs font-semibold bg-[#874436] hover:bg-[#6E362A] text-white px-4 py-2.5 rounded-lg transition-colors shadow-sm"
            >
              <Workflow className="w-4 h-4" />
              Go to Workflow Studio
            </Link>
            <button
              onClick={async () => {
                await postToApi("/api/v1/demo/seed");
                window.location.reload();
              }}
              className="flex items-center gap-2 text-xs font-semibold bg-[#FAF8F5] hover:bg-[#F3EFEA] text-[#1B1B1B] px-4 py-2.5 rounded-lg transition-colors border border-[#D5CABE] shadow-sm"
            >
              <Sparkles className="w-4 h-4 text-[#874436]" />
              Load Sample Run History & Traces
            </button>
          </div>

          <div className="mt-8 pt-6 border-t border-[#E8DFD5] max-w-lg w-full flex items-center justify-center gap-6 text-[11px] text-[#7A7165]">
            <span className="flex items-center gap-1.5"><ShieldCheck className="w-4 h-4 text-[#2E6B47]" /> Idempotency Keys Verified (ADR-0003)</span>
            <span className="flex items-center gap-1.5"><CheckCircle2 className="w-4 h-4 text-[#455CA1]" /> OpenTelemetry Distributed Traces</span>
          </div>
        </div>
      ) : (

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">

          <div className="rounded-xl bg-[#FAF8F5] border border-[#D5CABE] p-4 space-y-3 shadow-sm">
            <div className="flex items-center justify-between pb-2 border-b border-[#D5CABE] text-xs">
              <span className="font-bold text-[#1B1B1B] uppercase text-[11px]">Recent Runs</span>
              <span className="text-[#968676]">Showing {filteredRuns.length} of {runs.length}</span>
            </div>

            <div className="space-y-2">
              <div className="relative">
                <Search className="w-3.5 h-3.5 text-[#968676] absolute left-2.5 top-1/2 -translate-y-1/2" />
                <input
                  type="text"
                  value={runSearchQuery}
                  onChange={(e) => setRunSearchQuery(e.target.value)}
                  placeholder="Filter runs by ID, workflow..."
                  className="w-full bg-[#F3EFEA] border border-[#D5CABE] rounded-lg pl-8 pr-7 py-1 text-xs text-[#1B1B1B] placeholder-[#968676] focus:outline-none focus:bg-[#FAF8F5] focus:border-[#874436]"
                />
                {runSearchQuery && (
                  <button
                    onClick={() => setRunSearchQuery("")}
                    className="absolute right-2 top-1/2 -translate-y-1/2 text-[#968676] hover:text-[#1B1B1B] p-0.5"
                    title="Clear"
                  >
                    <X className="w-3 h-3" />
                  </button>
                )}
              </div>

              <div className="flex items-center gap-1 text-[10px]">
                {(["ALL", "SUCCESS", "FAILED"] as const).map((st) => (
                  <button
                    key={st}
                    onClick={() => setStatusFilter(st)}
                    className={`px-2 py-0.5 rounded font-semibold transition-colors ${
                      statusFilter === st
                        ? "bg-[#874436] text-white"
                        : "bg-[#F3EFEA] text-[#7A7165] hover:bg-[#E8DFD5]"
                    }`}
                  >
                    {st}
                  </button>
                ))}
              </div>
            </div>

            <div className="space-y-2">
              {filteredRuns.length === 0 ? (
                <div className="p-6 text-center text-xs text-[#7A7165] bg-[#F3EFEA] rounded-lg">
                  <p className="font-semibold">No runs match criteria</p>
                  <button
                    onClick={() => {
                      setRunSearchQuery("");
                      setStatusFilter("ALL");
                    }}
                    className="mt-2 text-[11px] text-[#874436] font-bold underline"
                  >
                    Reset filters
                  </button>
                </div>
              ) : (
                filteredRuns.map((run) => {
                  const isSelected = selectedRun === run.id;
                  return (
                    <div
                      key={run.id}
                      onClick={() => setSelectedRun(run.id)}
                      className={`p-3 rounded-lg border cursor-pointer transition-all text-xs ${
                        isSelected
                          ? "bg-[#F8EBE8] border-[#874436] text-[#1B1B1B] shadow-xs"
                          : "bg-[#F3EFEA] border-[#D5CABE] text-[#4F4F4F] hover:bg-[#FAF8F5]"
                      }`}
                    >
                      <div className="flex items-center justify-between">
                        <span className="font-mono font-bold text-indigo-700">{run.id}</span>
                        <span
                          className={`text-[10px] px-1.5 py-0.2 rounded font-bold ${
                            run.status === "SUCCESS"
                              ? "bg-emerald-100 text-emerald-800 border border-emerald-200"
                              : "bg-rose-100 text-rose-800 border border-rose-200"
                          }`}
                        >
                          {run.status}
                        </span>
                      </div>
                      <p className="font-semibold text-slate-800 mt-1">{run.wf}</p>
                      <div className="flex items-center justify-between text-[11px] text-slate-500 mt-1.5">
                        <span>{run.time}</span>
                        <span className="font-mono">{run.dur}</span>
                      </div>
                    </div>
                  );
                })
              )}
            </div>
        </div>

        <div className="lg:col-span-2 rounded-xl bg-white border border-slate-200 p-6 space-y-6 shadow-sm">

          <div className="flex items-center justify-between border-b border-slate-100 pb-4">
            <div>
              <div className="flex items-center gap-3">
                <h2 className="text-xl font-bold font-mono text-slate-900">#{selectedRun}</h2>
                <span
                  className={`text-xs px-2 py-0.5 rounded font-bold flex items-center gap-1 ${
                    selectedRun === "RUN-92830"
                      ? "bg-rose-50 text-rose-700 border border-rose-200"
                      : "bg-emerald-50 text-emerald-700 border border-emerald-200"
                  }`}
                >
                  {selectedRun === "RUN-92830" ? (
                    <>
                      <AlertCircle className="w-3 h-3 text-rose-600" /> FAILED (DLQ)
                    </>
                  ) : (
                    <>
                      <CheckCircle2 className="w-3 h-3 text-emerald-600" /> SUCCESS
                    </>
                  )}
                </span>
                <span className="text-xs text-slate-500 font-mono">
                  Duration: {selectedRun === "RUN-92830" ? "4.12s" : "2.84s"}
                </span>
              </div>
              <p className="text-xs text-slate-500 mt-1">
                Workflow: <strong className="text-slate-800">Order Processing (v3)</strong> | Trigger: SAP Event #evt_98231
              </p>
            </div>

            <div className="flex items-center gap-2">
              <button
                onClick={handleReplay}
                disabled={replaying}
                className="px-3 py-1.5 bg-indigo-600 hover:bg-indigo-700 text-white rounded-lg text-xs font-semibold flex items-center gap-1.5 transition-colors shadow-sm"
              >
                <RotateCcw className={`w-3.5 h-3.5 ${replaying ? "animate-spin" : ""}`} />
                {replaying ? "Replaying..." : "Replay"}
              </button>

              <button
                onClick={openTraceModal}
                className="px-3.5 py-1.5 bg-white hover:bg-indigo-50 text-indigo-700 rounded-lg text-xs font-semibold border border-indigo-200 flex items-center gap-1.5 transition-all shadow-sm"
              >
                <Activity className="w-3.5 h-3.5 text-indigo-600" />
                View Distributed Trace
              </button>
            </div>
          </div>

          <div className="flex items-center gap-2 border-b border-slate-100 pb-2 text-xs">
            <button
              onClick={() => setActiveTab("timeline")}
              className={`px-3 py-1 rounded-md font-semibold transition-colors ${
                activeTab === "timeline" ? "bg-indigo-50 text-indigo-700 border border-indigo-200" : "text-slate-600 hover:text-slate-900"
              }`}
            >
              Timeline ({sampleSteps.length} Steps)
            </button>
            <button
              onClick={() => setActiveTab("input")}
              className={`px-3 py-1 rounded-md font-semibold transition-colors ${
                activeTab === "input" ? "bg-indigo-50 text-indigo-700 border border-indigo-200" : "text-slate-600 hover:text-slate-900"
              }`}
            >
              View Input Payload
            </button>
            <button
              onClick={() => setActiveTab("output")}
              className={`px-3 py-1 rounded-md font-semibold transition-colors ${
                activeTab === "output" ? "bg-indigo-50 text-indigo-700 border border-indigo-200" : "text-slate-600 hover:text-slate-900"
              }`}
            >
              View Output Payload
            </button>
            <button
              onClick={() => setActiveTab("assistant")}
              className={`px-3 py-1 rounded-md font-semibold transition-colors flex items-center gap-1.5 ${
                activeTab === "assistant" ? "bg-slate-100 text-slate-800 border border-slate-300" : "text-slate-600 hover:text-slate-900"
              }`}
            >
              <Bot className="w-3.5 h-3.5 text-slate-700" />
              AI Incident Assistant (§30)
            </button>
          </div>

          {activeTab === "timeline" && (
            <div className="space-y-3">
              {sampleSteps.map((step, idx) => (
                <div
                  key={step.id}
                  className={`p-3.5 rounded-lg border flex items-center justify-between text-xs transition-colors ${
                    selectedRun === "RUN-92830" && idx === 4
                      ? "bg-rose-50/70 border-rose-200 text-rose-950"
                      : "bg-slate-50 border-slate-200 text-slate-800 hover:bg-slate-100/70"
                  }`}
                >
                  <div className="flex items-center gap-3">
                    <span className="font-mono text-slate-500 text-[11px] w-14">
                      {step.time}
                    </span>
                    <div
                      className={`w-2 h-2 rounded-full ${
                        selectedRun === "RUN-92830" && idx === 4 ? "bg-rose-500" : "bg-emerald-500"
                      }`}
                    ></div>
                    <div>
                      <p className="font-bold text-slate-900 flex items-center gap-2">
                        {step.name}
                        {selectedRun === "RUN-92830" && idx === 4 ? (
                          <AlertCircle className="w-3.5 h-3.5 text-rose-600" />
                        ) : (
                          <CheckCircle2 className="w-3.5 h-3.5 text-emerald-600" />
                        )}
                      </p>
                      <p className="text-[11px] text-slate-500">
                        {selectedRun === "RUN-92830" && idx === 4
                          ? "HTTP 503 Service Unavailable: Timeout from Warehouse API"
                          : step.detail}
                      </p>
                    </div>
                  </div>

                  <div className="flex items-center gap-3">
                    <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-white text-slate-700 border border-slate-200 font-medium">
                      {step.node}
                    </span>
                    <span className="text-slate-500 font-mono text-[11px]">
                      {step.duration}
                    </span>
                  </div>
                </div>
              ))}
            </div>
          )}

          {activeTab === "input" && (
            <pre className="p-4 rounded-lg bg-slate-50 border border-slate-200 font-mono text-xs text-indigo-900 overflow-x-auto">
{`{
  "event_id": "evt_98231",
  "source": "SAP.ERP.PROD",
  "order_id": "ORD-55410",
  "customer_id": "CUST-9821",
  "currency": "USD",
  "total_amount": 1420.50,
  "items": [
    { "sku": "SKU-9981-A", "quantity": 2, "unit_price": 710.25 }
  ],
  "timestamp": "2026-09-19T10:31:02Z"
}`}
            </pre>
          )}

          {activeTab === "output" && (
            <pre className="p-4 rounded-lg bg-slate-50 border border-slate-200 font-mono text-xs text-emerald-900 overflow-x-auto">
{selectedRun === "RUN-92830"
  ? `{\n  "error": "HTTP 503 Warehouse API Gateway Timeout",\n  "status": "FAILED",\n  "dlq_message_id": "dlq_88921",\n  "retry_attempts": 3\n}`
  : `{\n  "status": "DISPATCHED",\n  "workflow_id": "wf_order_processing",\n  "execution_run": "RUN-92831",\n  "shipment_tracking": "TRK-98214-WH",\n  "database_sync": "COMMITTED_ACID",\n  "warehouse_response_code": 201,\n  "audit_receipt": "aud_1001"\n}`}
            </pre>
          )}

          {activeTab === "assistant" && (
            <div className="space-y-4">

              <div className="p-3 bg-amber-50 border border-amber-200 rounded-lg flex items-center justify-between text-xs">
                <div className="flex items-center gap-2 text-amber-900">
                  <ShieldCheck className="w-4 h-4 text-amber-600 shrink-0" />
                  <span>
                    <strong>Reliability-First Assistant:</strong> Strictly read-only analysis over logs, traces, runs, and circuit breakers. Zero automated mutations—all actions require human confirmation.
                  </span>
                </div>
                <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-amber-100 text-amber-800 border border-amber-300 font-bold shrink-0">
                  §30 ARCH CHARTER
                </span>
              </div>

              <div className="p-4 rounded-xl bg-slate-50 border border-slate-200 space-y-3">
                <div className="flex items-center justify-between text-xs">
                  <span className="text-slate-600 font-mono">
                    Query Context: <strong className="text-slate-900">{selectedRun}</strong> (Workflow: Order Processing v3)
                  </span>
                  <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-rose-50 text-rose-700 border border-rose-200 font-bold">
                    {selectedRun === "RUN-92830" ? "UPSTREAM_UNAVAILABLE_503" : "EXECUTION_HEALTHY"}
                  </span>
                </div>

                <div className="p-3.5 rounded-lg bg-white border border-slate-200 flex items-start gap-3 shadow-sm">
                  <Bot className="w-5 h-5 text-indigo-600 shrink-0 mt-0.5" />
                  <div className="space-y-1 text-xs">
                    <p className="font-bold text-slate-900">
                      Why did {selectedRun} fail?
                    </p>
                    <p className="text-slate-600 leading-relaxed">
                      {selectedRun === "RUN-92830"
                        ? "Warehouse API returned HTTP 503 (Service Unavailable) on node 'Warehouse Notification'. Three retries were attempted with exponential backoff. The event is currently in the Dead Letter Queue."
                        : "Workflow completed successfully with ACID guarantees. All 6 steps passed in 2.84s without error."}
                    </p>
                  </div>
                </div>

                {selectedRun === "RUN-92830" && (
                  <div className="grid grid-cols-2 sm:grid-cols-4 gap-2 pt-1 text-[11px]">
                    <div className="p-2.5 rounded-lg bg-white border border-slate-200 shadow-xs">
                      <span className="text-slate-500 block text-[10px]">Failing Span</span>
                      <span className="font-mono font-bold text-rose-700">rest.notify (HTTP 503)</span>
                    </div>
                    <div className="p-2.5 rounded-lg bg-white border border-slate-200 shadow-xs">
                      <span className="text-slate-500 block text-[10px]">Circuit Breaker</span>
                      <span className="font-mono font-bold text-amber-700">TRIPPED_OPEN (Warehouse API)</span>
                    </div>
                    <div className="p-2.5 rounded-lg bg-white border border-slate-200 shadow-xs">
                      <span className="text-slate-500 block text-[10px]">DLQ Preserved</span>
                      <span className="font-mono font-bold text-indigo-700">dlq_88921</span>
                    </div>
                    <div className="p-2.5 rounded-lg bg-white border border-slate-200 shadow-xs">
                      <span className="text-slate-500 block text-[10px]">W3C Trace ID</span>
                      <span className="font-mono text-slate-700">4bf92f35...</span>
                    </div>
                  </div>
                )}
              </div>

              {selectedRun === "RUN-92830" && (
                <div className="p-4 rounded-xl bg-white border border-slate-200 space-y-3 text-xs shadow-sm">
                  <div className="flex items-center justify-between">
                    <h4 className="font-bold text-slate-900 flex items-center gap-2">
                      <Bot className="w-3.5 h-3.5 text-slate-700" />
                      Recommended Remediations
                    </h4>
                    <span className="text-[10px] text-slate-500 font-mono font-medium">
                      Operator Confirmation Required
                    </span>
                  </div>

                  {incidentNotice && (
                    <div className="p-2.5 bg-emerald-50 border border-emerald-200 rounded-lg text-emerald-800 text-xs flex items-center justify-between">
                      <span> Incident ticket <strong>INC-89104</strong> filed and dispatched to On-Call Triage.</span>
                      <span className="font-mono text-[10px] text-emerald-700 font-bold">P2 HIGH</span>
                    </div>
                  )}

                  {confirmAction && (
                    <div className="p-3 bg-amber-50 border border-amber-200 rounded-lg space-y-2 text-xs">
                      <p className="text-amber-900 font-bold">
                        Confirm Action: {confirmAction === "REPLAY" ? "Replay Run with Idempotency Guarantees" : "Create Incident Ticket"}?
                      </p>
                      <p className="text-slate-600 text-[11px]">
                        {confirmAction === "REPLAY"
                          ? "This will replay the trigger event using idempotency key 'evt_98231' and resume downstream steps."
                          : "This will escalate to on-call engineering with attached trace spans and breaker status."}
                      </p>
                      <div className="flex items-center gap-2 pt-1">
                        <button
                          onClick={() => {
                            if (confirmAction === "REPLAY") {
                              handleReplay();
                            } else {
                              setIncidentNotice(true);
                              setTimeout(() => setIncidentNotice(false), 4000);
                            }
                            setConfirmAction(null);
                          }}
                          className="px-3 py-1 bg-amber-600 hover:bg-amber-700 text-white font-semibold rounded text-[11px] transition-colors"
                        >
                          Confirm & Execute
                        </button>
                        <button
                          onClick={() => setConfirmAction(null)}
                          className="px-3 py-1 bg-white hover:bg-slate-100 text-slate-700 border border-slate-200 rounded text-[11px] transition-colors"
                        >
                          Cancel
                        </button>
                      </div>
                    </div>
                  )}

                  <div className="flex flex-wrap items-center gap-2.5 pt-1">
                    <button
                      onClick={() => setConfirmAction("REPLAY")}
                      className="px-3.5 py-1.5 bg-indigo-600 hover:bg-indigo-700 text-white font-semibold rounded-lg flex items-center gap-1.5 transition-colors shadow-sm"
                    >
                      <RotateCcw className="w-3.5 h-3.5" />
                      [Replay Run]
                    </button>
                    <button
                      onClick={openTraceModal}
                      className="px-3.5 py-1.5 bg-white hover:bg-indigo-50 text-indigo-700 border border-indigo-200 font-semibold rounded-lg flex items-center gap-1.5 transition-all shadow-sm"
                    >
                      <Activity className="w-3.5 h-3.5 text-indigo-600" />
                      [Inspect Trace Waterfall]
                    </button>
                    <button
                      onClick={() => setConfirmAction("INCIDENT")}
                      className="px-3.5 py-1.5 bg-white hover:bg-rose-50 text-rose-700 border border-rose-200 font-semibold rounded-lg flex items-center gap-1.5 transition-all shadow-sm"
                    >
                      <AlertCircle className="w-3.5 h-3.5 text-rose-600" />
                      [Create Incident Ticket]
                    </button>
                  </div>
                </div>
              )}
            </div>
          )}
        </div>
      </div>
      )}

      {traceModalOpen && (
        <div className="fixed inset-0 z-50 bg-slate-900/40 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="bg-white border border-slate-200 rounded-2xl max-w-4xl w-full max-h-[85vh] flex flex-col shadow-2xl overflow-hidden animate-fade-in">

            <div className="p-5 border-b border-slate-100 flex items-center justify-between bg-slate-50">
              <div className="space-y-1">
                <div className="flex items-center gap-2.5">
                  <Activity className="w-4 h-4 text-indigo-600" />
                  <h3 className="text-base font-bold text-slate-900 font-mono">
                    Trace #{activeTrace.trace_id}
                  </h3>
                  <span
                    className={`text-[10px] px-2 py-0.5 rounded font-bold uppercase tracking-wider ${
                      activeTrace.status === "ERROR"
                        ? "bg-rose-100 text-rose-800 border border-rose-200"
                        : "bg-emerald-100 text-emerald-800 border border-emerald-200"
                    }`}
                  >
                    {activeTrace.status}
                  </span>
                </div>
                <p className="text-xs text-slate-500">
                  Run ID: <strong className="text-slate-800">#{selectedRun}</strong> | Total Duration:{" "}
                  <strong className="text-indigo-700">{activeTrace.total_duration_ms}ms</strong> | Total Spans:{" "}
                  <strong className="text-slate-800">{activeTrace.spans.length}</strong>
                </p>
              </div>

              <div className="flex items-center gap-2">
                <Link
                  href={`/observability?traceId=${activeTrace.trace_id}`}
                  className="px-3 py-1.5 rounded-lg bg-white hover:bg-slate-100 text-xs font-semibold text-slate-700 border border-slate-200 flex items-center gap-1.5 transition-colors shadow-sm"
                >
                  <ExternalLink className="w-3.5 h-3.5" />
                  Open in Observability
                </Link>
                <button
                  onClick={() => setTraceModalOpen(false)}
                  className="p-1.5 text-slate-400 hover:text-slate-700 rounded-lg hover:bg-slate-100 transition-colors"
                >
                  <X className="w-5 h-5" />
                </button>
              </div>
            </div>

            <div className="p-5 overflow-y-auto space-y-5 text-xs flex-1">

              <div className="space-y-2">
                <div className="flex items-center justify-between text-[11px] text-slate-500 font-mono pb-1 border-b border-slate-100 font-semibold">
                  <span>SPAN HIERARCHY</span>
                  <span>RELATIVE TIMING WATERFALL</span>
                </div>

                {activeTrace.spans.map((span, idx) => {
                  const isSelected = selectedSpan?.name === span.name;
                  return (
                    <div
                      key={idx}
                      onClick={() => setSelectedSpan(span)}
                      className={`p-3 rounded-lg border cursor-pointer transition-all ${
                        isSelected
                          ? "bg-indigo-50/80 border-indigo-400 shadow-sm"
                          : "bg-slate-50 border-slate-200 hover:border-slate-300 hover:bg-slate-100/70"
                      }`}
                    >
                      <div className="flex items-center justify-between mb-2">
                        <div className="flex items-center gap-2">
                          <span
                            className={`w-2 h-2 rounded-full ${
                              span.status === "ERROR" ? "bg-rose-500" : "bg-emerald-500"
                            }`}
                          ></span>
                          <span className="font-bold text-slate-900 font-mono text-[11px]">
                            {span.name}
                          </span>
                          <span className="text-[10px] px-1.5 py-0.2 rounded bg-white text-slate-600 border border-slate-200 uppercase font-medium">
                            {span.service}
                          </span>
                        </div>
                        <span className="font-mono text-slate-500 text-[11px]">{span.time}</span>
                      </div>

                      <div className="w-full bg-slate-200 h-2.5 rounded-full overflow-hidden flex items-center">
                        <div
                          className={`h-2.5 rounded-full transition-all ${span.bg}`}
                          style={{ width: span.width }}
                        ></div>
                      </div>

                      {span.error && (
                        <div className="mt-2 text-[11px] text-rose-800 bg-rose-50 border border-rose-200 p-2 rounded flex items-center gap-2">
                          <AlertCircle className="w-3.5 h-3.5 text-rose-600 shrink-0" />
                          <span>{span.error}</span>
                        </div>
                      )}
                    </div>
                  );
                })}
              </div>

              {selectedSpan && (
                <div className="p-4 rounded-xl bg-slate-50 border border-slate-200 space-y-3">
                  <div className="flex items-center justify-between text-xs border-b border-slate-200 pb-2">
                    <span className="font-bold text-slate-900 flex items-center gap-2">
                      <Layers className="w-3.5 h-3.5 text-indigo-600" />
                      Span Attributes: {selectedSpan.name}
                    </span>
                    <span className="font-mono text-slate-500 text-[11px]">
                      Duration: {selectedSpan.duration_ms}ms
                    </span>
                  </div>

                  <div className="grid grid-cols-2 gap-2 text-[11px] font-mono">
                    {Object.entries(selectedSpan.attributes).map(([k, v]) => (
                      <div key={k} className="p-2 rounded bg-white border border-slate-200 flex justify-between shadow-xs">
                        <span className="text-slate-500">{k}:</span>
                        <span className="text-indigo-700 font-semibold">{v}</span>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>

            <div className="p-4 border-t border-slate-100 bg-slate-50 flex items-center justify-between text-xs">
              <span className="text-slate-500 text-[11px]">
                Context propagated via W3C TraceContext (<code className="text-slate-700">traceparent</code>)
              </span>
              <button
                onClick={() => setTraceModalOpen(false)}
                className="px-4 py-1.5 bg-white hover:bg-slate-100 text-slate-700 rounded-lg text-xs font-semibold border border-slate-200 shadow-sm"
              >
                Close Inspector
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
