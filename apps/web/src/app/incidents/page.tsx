"use client";

import { useState, useEffect } from "react";
import {
  AlertTriangle,
  RotateCcw,
  CheckCircle2,
  ExternalLink,
  Trash2,
  Flame,
  ShieldAlert,
  Server,
  Activity,
  Layers,
  Search,
  X,
} from "lucide-react";
import { fetchFromApi, postToApi, getActiveTenantId } from "@/lib/api";

interface DLQItem {
  id: string;
  event: string;
  workflow: string;
  reason: string;
  attempts: number;
  age: string;
}

const initialDLQ: DLQItem[] = [
  { id: "evt_1932", event: "sap.order.created", workflow: "Order Processing", reason: "HTTP 503 Service Unavailable", attempts: 3, age: "2m ago" },
  { id: "evt_1933", event: "customer.update", workflow: "Customer Sync", reason: "Schema mismatch on 'tax_identifier'", attempts: 3, age: "5m ago" },
  { id: "evt_1934", event: "inventory.update", workflow: "Inventory Stream", reason: "Socket read timeout after 5000ms", attempts: 3, age: "8m ago" },
];

export default function IncidentsPage() {
  const [dlqItems, setDlqItems] = useState<DLQItem[]>(initialDLQ);
  const [replayNotice, setReplayNotice] = useState<string | null>(null);
  const [searchQuery, setSearchQuery] = useState("");

  const loadDLQ = async () => {
    const isAcme = getActiveTenantId() === "tenant_acme";
    const apiItems = await fetchFromApi<any[]>("/api/v1/incidents/dlq", []);
    if (apiItems && apiItems.length > 0) {
      setDlqItems(apiItems.map((item: any) => ({
        id: item.id,
        event: item.event_type || item.event_id || item.id,
        workflow: item.workflow_id || "Order Processing",
        reason: item.reason || "Error",
        attempts: item.attempts || 3,
        age: item.age || "Just now",
      })));
    } else if (isAcme) {
      setDlqItems(initialDLQ);
    } else {
      setDlqItems([]);
    }
  };

  useEffect(() => {
    loadDLQ();
    window.addEventListener("flowmesh:tenant_changed", loadDLQ);
    return () => window.removeEventListener("flowmesh:tenant_changed", loadDLQ);
  }, []);

  const filteredDLQ = dlqItems.filter((item) => {
    if (!searchQuery.trim()) return true;
    const q = searchQuery.toLowerCase().trim();
    return (
      item.id.toLowerCase().includes(q) ||
      item.event.toLowerCase().includes(q) ||
      item.workflow.toLowerCase().includes(q) ||
      item.reason.toLowerCase().includes(q)
    );
  });

  const handleReplaySingle = async (id: string) => {
    const res = await postToApi<any>(`/api/v1/incidents/dlq/${id}/replay`);
    setDlqItems((prev) => prev.filter((i) => i.id !== id));
    setReplayNotice(res?.message || `Successfully re-injected event ${id} into NATS JetStream`);
    setTimeout(() => setReplayNotice(null), 3000);
    await loadDLQ();
  };

  const handleReplayAll = async () => {
    const res = await postToApi<any>("/api/v1/incidents/dlq/replay-all");
    const count = dlqItems.length;
    setDlqItems([]);
    setReplayNotice(res?.message || `Successfully replayed all ${count} DLQ events with zero duplicate side effects`);
    setTimeout(() => setReplayNotice(null), 3500);
    await loadDLQ();
  };

  return (
    <div className="space-y-8 max-w-7xl mx-auto">

      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-slate-900 flex items-center gap-2.5">
            Incidents & Dead Letter Queue
            <span className="text-xs font-semibold text-amber-800 bg-amber-50 px-2 py-0.5 rounded border border-amber-200">
              1 Active Incident
            </span>
          </h1>
          <p className="text-xs text-slate-500 mt-1">
            Correlated failure diagnosis, circuit breaker status, and Dead Letter Queue management.
          </p>
        </div>

        {replayNotice && (
          <div className="flex items-center gap-2 text-xs text-emerald-800 bg-emerald-50 border border-emerald-300 px-3 py-1.5 rounded-lg shadow-sm">
            <CheckCircle2 className="w-4 h-4 text-emerald-600" />
            {replayNotice}
          </div>
        )}
      </div>

      <div className="rounded-xl bg-white border border-slate-200 p-6 space-y-6 shadow-sm">
        <div className="flex items-start justify-between border-b border-slate-100 pb-4">
          <div>
            <div className="flex items-center gap-3">
              <span className="text-xs font-mono font-bold text-slate-700 bg-slate-100 px-2 py-0.5 rounded border border-slate-200">
                INC-1932
              </span>
              <h2 className="text-lg font-bold text-slate-900">Warehouse API Timeout (HTTP 503)</h2>
              <span className="text-[10px] uppercase px-2 py-0.5 rounded font-bold bg-rose-50 text-rose-700 border border-rose-200">
                Severity: HIGH
              </span>
              <span className="text-[10px] uppercase px-2 py-0.5 rounded font-bold bg-emerald-50 text-emerald-700 border border-emerald-200 flex items-center gap-1">
                <CheckCircle2 className="w-3 h-3 text-emerald-600" /> Status: RECOVERED
              </span>
            </div>
            <p className="text-xs text-slate-500 mt-1">
              Affected workflows: <strong className="text-slate-800">Order Processing, Shipment Update</strong>
            </p>
          </div>

          <div className="flex items-center gap-2">
            <button
              onClick={handleReplayAll}
              className="px-3.5 py-1.5 bg-indigo-600 hover:bg-indigo-700 text-white rounded-lg text-xs font-semibold flex items-center gap-1.5 shadow-sm transition-colors"
            >
              <RotateCcw className="w-3.5 h-3.5" />
              Replay Failed Runs
            </button>
            <button className="px-3 py-1.5 bg-white hover:bg-slate-100 text-slate-700 rounded-lg text-xs font-semibold border border-slate-200 shadow-sm transition-colors">
              Disable Workflow
            </button>
            <button className="px-3 py-1.5 bg-white hover:bg-slate-100 text-slate-700 rounded-lg text-xs font-semibold border border-slate-200 shadow-sm transition-colors">
              Open Trace
            </button>
          </div>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 text-xs">

          <div className="space-y-3">
            <h3 className="font-bold text-slate-900 uppercase tracking-wider text-[11px] flex items-center gap-1.5">
              <Activity className="w-3.5 h-3.5 text-indigo-600" />
              Incident Timeline
            </h3>
            <div className="space-y-2 p-3.5 rounded-lg bg-slate-50 border border-slate-200 font-mono text-[11px]">
              <div className="text-slate-700">10:21 API timeout detected on node 'Notify Warehouse'</div>
              <div className="text-slate-500">10:21 Retry #1 dispatched with 200ms exponential backoff</div>
              <div className="text-slate-500">10:22 Retry #2 failed with HTTP 503</div>
              <div className="text-amber-700 font-bold">10:22 Circuit breaker state changed to OPEN (fail-fast active)</div>
              <div className="text-emerald-700">10:23 API recovered (Canary health check HTTP 200)</div>
              <div className="text-emerald-700 font-bold">10:23 Replay successful; circuit breaker restored to CLOSED</div>
            </div>
          </div>

          <div className="space-y-3">
            <h3 className="font-bold text-slate-900 uppercase tracking-wider text-[11px] flex items-center gap-1.5">
              <ShieldAlert className="w-3.5 h-3.5 text-amber-600" />
              Root Cause & Circuit Diagnostics
            </h3>
            <div className="p-3.5 rounded-lg bg-slate-50 border border-slate-200 space-y-2.5">
              <p className="text-slate-700">
                <strong>Root cause:</strong> Warehouse internal upstream API returned HTTP 503 during a gateway container rolling update.
              </p>
              <div className="p-2.5 rounded bg-white border border-slate-200 flex items-center justify-between shadow-xs">
                <div className="flex items-center gap-2">
                  <Flame className="w-4 h-4 text-orange-600" />
                  <div>
                    <p className="font-semibold text-slate-800">RediForge Circuit Breaker</p>
                    <p className="text-[10px] text-slate-500">Target: conn_rest_01 (Warehouse API)</p>
                  </div>
                </div>
                <span className="text-[10px] font-bold px-2 py-0.5 rounded bg-emerald-50 text-emerald-700 border border-emerald-200">
                  CURRENT: CLOSED
                </span>
              </div>
            </div>
          </div>
        </div>
      </div>

      <div className="rounded-xl bg-white border border-slate-200 p-6 space-y-4 shadow-sm">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <AlertTriangle className="w-4 h-4 text-amber-600" />
            <h2 className="text-base font-bold text-slate-900 uppercase tracking-wider">
              Dead Letter Queue (DLQ)
            </h2>
            <span className="text-xs font-mono font-medium text-slate-600 bg-slate-100 px-2 py-0.5 rounded border border-slate-200">
              {dlqItems.length} Unresolved Events
            </span>
          </div>

          <div className="flex items-center gap-2">
            <button
              onClick={handleReplayAll}
              disabled={dlqItems.length === 0}
              className="px-3 py-1.5 bg-indigo-600 hover:bg-indigo-700 text-white rounded-lg text-xs font-semibold flex items-center gap-1.5 disabled:opacity-40 shadow-sm transition-colors"
            >
              <RotateCcw className="w-3 h-3" />
              Replay All Matching
            </button>
            <button
              onClick={() => setDlqItems([])}
              disabled={dlqItems.length === 0}
              className="px-3 py-1.5 bg-white hover:bg-rose-50 text-rose-700 rounded-lg text-xs font-semibold border border-rose-200 flex items-center gap-1.5 disabled:opacity-40 shadow-sm transition-colors"
            >
              <Trash2 className="w-3 h-3" />
              Purge DLQ
            </button>
          </div>
        </div>

        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 pb-2 border-b border-slate-100">
          <div className="relative w-full sm:w-80">
            <Search className="w-3.5 h-3.5 text-slate-400 absolute left-3 top-1/2 -translate-y-1/2" />
            <input
              type="text"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              placeholder="Search DLQ by event ID, workflow, reason..."
              className="w-full bg-slate-50 border border-slate-200 rounded-lg pl-8 pr-7 py-1 text-xs text-slate-800 placeholder-slate-400 focus:outline-none focus:bg-white focus:border-indigo-500"
            />
            {searchQuery && (
              <button
                onClick={() => setSearchQuery("")}
                className="absolute right-2 top-1/2 -translate-y-1/2 text-slate-400 hover:text-slate-600 p-0.5"
                title="Clear"
              >
                <X className="w-3 h-3" />
              </button>
            )}
          </div>

          <div className="text-[11px] text-slate-500 font-medium">
            Showing {filteredDLQ.length} of {dlqItems.length} failed events
          </div>
        </div>

        {dlqItems.length === 0 ? (
          <div className="p-8 rounded-xl bg-slate-50 border border-slate-200 text-center text-xs text-slate-500">
            <CheckCircle2 className="w-8 h-8 text-emerald-600 mx-auto mb-2" />
            <p className="font-bold text-slate-800">Dead Letter Queue is empty</p>
            <p className="text-[11px] text-slate-500 mt-0.5">All events have processed or successfully recovered.</p>
          </div>
        ) : filteredDLQ.length === 0 ? (
          <div className="p-8 rounded-xl bg-slate-50 border border-slate-200 text-center text-xs text-slate-500">
            <Search className="w-6 h-6 text-slate-400 mx-auto mb-2" />
            <p className="font-bold text-slate-800">No DLQ events match &ldquo;{searchQuery}&rdquo;</p>
            <button
              onClick={() => setSearchQuery("")}
              className="mt-2 text-[11px] text-indigo-700 font-bold underline"
            >
              Clear search
            </button>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs">
              <thead className="bg-slate-50 text-slate-500 uppercase tracking-wider text-[10px] border-b border-slate-200 font-semibold">
                <tr>
                  <th className="py-2.5 px-4">Event ID</th>
                  <th className="py-2.5 px-4">Workflow</th>
                  <th className="py-2.5 px-4">Failure Reason</th>
                  <th className="py-2.5 px-4">Attempts</th>
                  <th className="py-2.5 px-4">Age</th>
                  <th className="py-2.5 px-4 text-right">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {filteredDLQ.map((item) => (
                  <tr key={item.id} className="hover:bg-slate-50/80 transition-colors">
                    <td className="py-3 px-4 font-mono font-bold text-indigo-700">{item.id}</td>
                    <td className="py-3 px-4 font-semibold text-slate-800">{item.workflow}</td>
                    <td className="py-3 px-4 text-rose-700 font-mono text-[11px]">{item.reason}</td>
                    <td className="py-3 px-4 text-slate-600 font-mono">{item.attempts} / 3</td>
                    <td className="py-3 px-4 text-slate-500">{item.age}</td>
                    <td className="py-3 px-4 text-right">
                      <div className="flex items-center justify-end gap-2">
                        <button className="px-2 py-1 text-[11px] bg-white hover:bg-slate-100 text-slate-700 border border-slate-200 rounded font-medium shadow-xs">
                          Inspect
                        </button>
                        <button
                          onClick={() => handleReplaySingle(item.id)}
                          className="px-2 py-1 text-[11px] bg-indigo-600 hover:bg-indigo-700 text-white rounded font-semibold flex items-center gap-1 shadow-xs"
                        >
                          <RotateCcw className="w-2.5 h-2.5" /> Replay
                        </button>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
}
