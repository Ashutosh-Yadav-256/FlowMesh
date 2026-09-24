"use client";

import { useState } from "react";
import {
  Activity,
  Radio,
  Cpu,
  Database,
  Server,
  Flame,
  ArrowUpRight,
  ExternalLink,
  Search,
  CheckCircle2,
  AlertCircle,
  Layers,
  BarChart3,
  Clock,
} from "lucide-react";

interface SpanRecord {
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

const mockTraces: Record<string, { id: string; run_id: string; wf: string; duration_ms: number; status: "OK" | "ERROR"; spans: SpanRecord[] }> = {
  "4bf92f3577b34da6a3ce929d0e0e4736": {
    id: "4bf92f3577b34da6a3ce929d0e0e4736",
    run_id: "RUN-92831",
    wf: "Order Processing (v3)",
    duration_ms: 2840,
    status: "OK",
    spans: [
      {
        name: "POST /api/v1/events (HTTP Ingress)",
        service: "flowmesh-api",
        time: "0ms - 42ms (42ms)",
        duration_ms: 42,
        width: "15%",
        bg: "bg-indigo-600",
        status: "OK",
        attributes: { "http.method": "POST", "http.status": "200", "client.ip": "10.0.4.12" },
      },
      {
        name: "nats.publish(events.acme.orders)",
        service: "nats-jetstream",
        time: "42ms - 58ms (16ms)",
        duration_ms: 16,
        width: "12%",
        bg: "bg-sky-600",
        status: "OK",
        attributes: { "stream": "ORDERS", "partition": "0", "ack": "true" },
      },
      {
        name: "worker.consume(events.acme.orders)",
        service: "workflow-engine",
        time: "58ms - 80ms (22ms)",
        duration_ms: 22,
        width: "14%",
        bg: "bg-slate-700",
        status: "OK",
        attributes: { "worker.id": "worker-pool-01", "state_machine": "resumable" },
      },
      {
        name: "agent.command_dispatch(postgres.query)",
        service: "edge-agent-prod-01",
        time: "80ms - 210ms (130ms)",
        duration_ms: 130,
        width: "35%",
        bg: "bg-emerald-600",
        status: "OK",
        attributes: { "connector": "postgres", "connection_id": "conn_pg_01", "policy": "allow", "mtls": "verified" },
      },
      {
        name: "agent.command_dispatch(rest.notify)",
        service: "edge-agent-prod-01",
        time: "210ms - 1060ms (850ms)",
        duration_ms: 850,
        width: "70%",
        bg: "bg-amber-600",
        status: "OK",
        attributes: { "connector": "rest", "connection_id": "conn_rest_01", "status_code": "201" },
      },
      {
        name: "audit.append_event()",
        service: "audit-service",
        time: "1060ms - 1105ms (45ms)",
        duration_ms: 45,
        width: "18%",
        bg: "bg-slate-500",
        status: "OK",
        attributes: { "ledger": "immutable_audit_log", "checksum": "sha256:7fa89..." },
      },
    ],
  },
  "8ca15e2190184fa9b6ee178d8a0f9122": {
    id: "8ca15e2190184fa9b6ee178d8a0f9122",
    run_id: "RUN-92830",
    wf: "Order Processing (v3)",
    duration_ms: 4120,
    status: "ERROR",
    spans: [
      {
        name: "POST /api/v1/events (HTTP Ingress)",
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
        name: "worker.consume(events.acme.orders)",
        service: "workflow-engine",
        time: "55ms - 4120ms (4065ms)",
        duration_ms: 4065,
        width: "95%",
        bg: "bg-rose-600",
        status: "ERROR",
        attributes: { "retries": "3", "dlq_routed": "true" },
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
        attributes: { "connector": "postgres", "rows": "1" },
      },
      {
        name: "agent.command_dispatch(rest.notify)",
        service: "edge-agent-prod-01",
        time: "195ms - 4100ms (3905ms)",
        duration_ms: 3905,
        width: "90%",
        bg: "bg-rose-600",
        status: "ERROR",
        attributes: { "connector": "rest", "circuit_breaker": "OPEN", "http_status": "503" },
        error: "HTTP 503 Service Unavailable: Warehouse gateway backend connection timeout",
      },
    ],
  },
};

export default function ObservabilityPage() {
  const [selectedTraceId, setSelectedTraceId] = useState("4bf92f3577b34da6a3ce929d0e0e4736");
  const [searchQuery, setSearchQuery] = useState("");
  const [selectedSpan, setSelectedSpan] = useState<SpanRecord | null>(null);

  const activeTrace = mockTraces[selectedTraceId] || mockTraces["4bf92f3577b34da6a3ce929d0e0e4736"];

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault();
    if (!searchQuery.trim()) return;
    for (const [tid, trace] of Object.entries(mockTraces)) {
      if (tid.includes(searchQuery.trim()) || trace.run_id.toLowerCase().includes(searchQuery.trim().toLowerCase())) {
        setSelectedTraceId(tid);
        return;
      }
    }
  };

  return (
    <div className="space-y-6 max-w-7xl mx-auto">

      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-slate-900 flex items-center gap-2.5">
            Observability & Distributed Traces
            <span className="text-xs font-semibold text-emerald-700 bg-emerald-50 px-2 py-0.5 rounded border border-emerald-200">
              OpenTelemetry v1.44
            </span>
          </h1>
          <p className="text-xs text-slate-500 mt-1">
            End-to-end trace propagation across Webhooks → NATS Headers → Engine Workers → Edge Agent execution.
          </p>
        </div>

        <div className="flex items-center gap-2.5">
          <a
            href="http://localhost:3001"
            target="_blank"
            rel="noreferrer"
            className="px-3.5 py-1.5 bg-white hover:bg-slate-100 text-slate-700 rounded-lg text-xs font-semibold border border-slate-200 flex items-center gap-1.5 transition-colors shadow-sm"
          >
            <BarChart3 className="w-3.5 h-3.5 text-amber-600" />
            Grafana Dashboards (:3001)
          </a>
          <a
            href="http://localhost:8000/metrics"
            target="_blank"
            rel="noreferrer"
            className="px-3.5 py-1.5 bg-indigo-600 hover:bg-indigo-700 text-white rounded-lg text-xs font-semibold flex items-center gap-1.5 transition-colors shadow-sm"
          >
            <Activity className="w-3.5 h-3.5" />
            Prometheus Metrics (:8000/metrics)
          </a>
        </div>
      </div>

      <div className="grid grid-cols-4 gap-4 text-xs">
        <div className="p-4 rounded-xl bg-white border border-slate-200 shadow-sm">
          <span className="text-slate-500 font-semibold">p95 Execution Latency</span>
          <p className="text-2xl font-extrabold text-slate-900 mt-1">42.8ms</p>
          <span className="text-[11px] text-emerald-700 font-medium mt-1 block">Within 50ms SLO</span>
        </div>
        <div className="p-4 rounded-xl bg-white border border-slate-200 shadow-sm">
          <span className="text-slate-500 font-semibold">NATS JetStream Queue Depth</span>
          <p className="text-2xl font-extrabold text-slate-900 mt-1">0 msg</p>
          <span className="text-[11px] text-emerald-700 font-medium mt-1 block">Zero consumer lag</span>
        </div>
        <div className="p-4 rounded-xl bg-white border border-slate-200 shadow-sm">
          <span className="text-slate-500 font-semibold">StateStore Lock Contention</span>
          <p className="text-2xl font-extrabold text-slate-900 mt-1">0.02%</p>
          <span className="text-[11px] text-indigo-700 font-medium mt-1 block">RediForge atomic leases</span>
        </div>
        <div className="p-4 rounded-xl bg-white border border-slate-200 shadow-sm">
          <span className="text-slate-500 font-semibold">Edge Agent Roundtrip</span>
          <p className="text-2xl font-extrabold text-slate-900 mt-1">12.4ms</p>
          <span className="text-[11px] text-slate-500 mt-1 block">mTLS tunnel latency</span>
        </div>
      </div>

      <div className="rounded-xl bg-white border border-slate-200 p-4 flex items-center justify-between gap-4 shadow-sm">
        <form onSubmit={handleSearch} className="flex-1 max-w-md relative">
          <Search className="w-4 h-4 text-slate-400 absolute left-3 top-2.5" />
          <input
            type="text"
            placeholder="Search by Trace ID or Run ID (e.g. RUN-92830)..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="w-full bg-slate-50 border border-slate-200 rounded-lg pl-9 pr-3 py-1.5 text-xs text-slate-900 placeholder-slate-400 focus:outline-none focus:bg-white focus:border-indigo-500 focus:ring-1 focus:ring-indigo-500"
          />
        </form>

        <div className="flex items-center gap-2 text-xs">
          <span className="text-slate-500 font-medium text-[11px]">Quick Switch:</span>
          {Object.entries(mockTraces).map(([tid, trace]) => (
            <button
              key={tid}
              onClick={() => {
                setSelectedTraceId(tid);
                setSelectedSpan(null);
              }}
              className={`px-3 py-1 rounded-md text-xs font-mono transition-colors flex items-center gap-1.5 ${
                selectedTraceId === tid
                  ? "bg-indigo-50 text-indigo-700 border border-indigo-300 font-bold"
                  : "bg-slate-50 text-slate-600 hover:text-slate-900 border border-slate-200"
              }`}
            >
              <span
                className={`w-1.5 h-1.5 rounded-full ${
                  trace.status === "ERROR" ? "bg-rose-500" : "bg-emerald-500"
                }`}
              ></span>
              {trace.run_id} ({trace.duration_ms}ms)
            </button>
          ))}
        </div>
      </div>

      <div className="rounded-xl bg-white border border-slate-200 p-6 space-y-5 shadow-sm">

        <div className="flex items-center justify-between border-b border-slate-100 pb-4">
          <div>
            <div className="flex items-center gap-3">
              <span className="text-xs font-bold uppercase tracking-wider text-indigo-600">
                Distributed Trace
              </span>
              <span
                className={`text-[10px] px-2 py-0.5 rounded font-bold uppercase ${
                  activeTrace.status === "ERROR"
                    ? "bg-rose-100 text-rose-800 border border-rose-200"
                    : "bg-emerald-100 text-emerald-800 border border-emerald-200"
                }`}
              >
                {activeTrace.status}
              </span>
            </div>
            <p className="font-mono text-slate-900 text-base font-bold mt-1">
              Trace ID: {activeTrace.id}
            </p>
            <p className="text-xs text-slate-500 mt-0.5">
              Associated Run: <strong className="text-slate-800">#{activeTrace.run_id}</strong> | Workflow:{" "}
              <strong className="text-slate-800">{activeTrace.wf}</strong>
            </p>
          </div>

          <div className="text-right">
            <span className="text-xs text-slate-500 block">Total End-to-End Latency</span>
            <span className="font-mono text-xl font-bold text-slate-900">{activeTrace.duration_ms}ms</span>
          </div>
        </div>

        <div className="space-y-2 text-xs">
          <div className="flex items-center justify-between text-[11px] text-slate-500 font-mono pb-1 border-b border-slate-100 font-semibold">
            <span>SPAN EXECUTION TREE</span>
            <span>RELATIVE TIMING WATERFALL</span>
          </div>

          {activeTrace.spans.map((s, idx) => {
            const isSelected = selectedSpan?.name === s.name;
            return (
              <div
                key={idx}
                onClick={() => setSelectedSpan(s)}
                className={`p-3 rounded-lg border cursor-pointer transition-all ${
                  isSelected
                    ? "bg-indigo-50/80 border-indigo-400 shadow-sm"
                    : "bg-slate-50 border-slate-200 hover:border-slate-300 hover:bg-slate-100/70"
                }`}
              >
                <div className="flex justify-between font-mono text-[11px] mb-2">
                  <div className="flex items-center gap-2">
                    <span
                      className={`w-2 h-2 rounded-full ${
                        s.status === "ERROR" ? "bg-rose-500" : "bg-emerald-500"
                      }`}
                    ></span>
                    <span className="text-slate-900 font-bold">{s.name}</span>
                    <span className="text-[10px] px-1.5 py-0.2 rounded bg-white text-slate-600 border border-slate-200 uppercase font-medium">
                      {s.service}
                    </span>
                  </div>
                  <span className="text-slate-500">{s.time}</span>
                </div>

                <div className="w-full bg-slate-200 h-2.5 rounded-full overflow-hidden flex items-center">
                  <div className={`h-2.5 rounded-full ${s.bg}`} style={{ width: s.width }}></div>
                </div>

                {s.error && (
                  <div className="mt-2 text-[11px] text-rose-800 bg-rose-50 border border-rose-200 p-2 rounded flex items-center gap-2">
                    <AlertCircle className="w-3.5 h-3.5 text-rose-600 shrink-0" />
                    <span>{s.error}</span>
                  </div>
                )}
              </div>
            );
          })}
        </div>

        {selectedSpan && (
          <div className="p-4 rounded-xl bg-slate-50 border border-slate-200 space-y-3 animate-fade-in">
            <div className="flex items-center justify-between text-xs border-b border-slate-200 pb-2">
              <span className="font-bold text-slate-900 flex items-center gap-2">
                <Layers className="w-3.5 h-3.5 text-indigo-600" />
                Span Detail: {selectedSpan.name} ({selectedSpan.service})
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
    </div>
  );
}
