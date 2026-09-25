"use client";

import { useState, useEffect } from "react";
import { ShieldCheck, FileText, CheckCircle2, AlertOctagon, Search, X, Filter } from "lucide-react";
import { fetchFromApi, getActiveTenantId } from "@/lib/api";

interface AuditItem {
  id: string;
  time: string;
  actor: string;
  action: string;
  resource: string;
  result: "ALLOWED" | "DENIED" | "SUCCESS";
  detail: string;
}

const defaultAuditRecords: AuditItem[] = [
  { id: "aud_1001", time: "22:31:02", actor: "system:nats-worker", action: "workflow.execute", resource: "workflow:wf_order_processing", result: "SUCCESS", detail: "Completed Run #RUN-92831 in 2.84s" },
  { id: "aud_1002", time: "22:25:10", actor: "alex.dev@acme.corp", action: "connection.rotate_secret", resource: "connection:conn_pg_01", result: "ALLOWED", detail: "Generated AES-256-GCM v3 cipher" },
  { id: "aud_1003", time: "22:22:00", actor: "system:circuit-breaker", action: "circuit_breaker.trip", resource: "connection:conn_rest_01", result: "SUCCESS", detail: "Tripped circuit after 3 consecutive failures" },
  { id: "aud_1004", time: "21:40:12", actor: "agent:agent-prod-01", action: "policy.evaluate", resource: "postgres:drop_table_attempt", result: "DENIED", detail: "Blocked DDL drop query via deny-by-default allowlist" },
];

export default function AuditPage() {
  const [records, setRecords] = useState<AuditItem[]>(defaultAuditRecords);
  const [searchQuery, setSearchQuery] = useState("");
  const [outcomeFilter, setOutcomeFilter] = useState<"ALL" | "ALLOWED" | "DENIED" | "SUCCESS">("ALL");

  const loadAudit = async () => {
    const isAcme = getActiveTenantId() === "tenant_acme";
    const apiRecords = await fetchFromApi<any[]>("/api/v1/audit", []);
    if (apiRecords && apiRecords.length > 0) {
      setRecords(apiRecords.map((r: any) => ({
        id: r.id,
        time: r.timestamp?.includes("T") ? r.timestamp.split("T")[1].substring(0, 8) : r.timestamp,
        actor: r.actor,
        action: r.action,
        resource: r.resource,
        result: (r.result?.toUpperCase() === "SUCCESS" || r.result?.toUpperCase() === "ALLOWED") ? r.result.toUpperCase() as any : "DENIED",
        detail: JSON.stringify(r.metadata || {}),
      })));
    } else if (isAcme) {
      setRecords(defaultAuditRecords);
    } else {
      setRecords([]);
    }
  };

  useEffect(() => {
    loadAudit();
    window.addEventListener("flowmesh:tenant_changed", loadAudit);
    return () => window.removeEventListener("flowmesh:tenant_changed", loadAudit);
  }, []);

  const filteredRecords = records.filter((r) => {
    if (outcomeFilter !== "ALL" && r.result !== outcomeFilter) return false;
    if (!searchQuery.trim()) return true;
    const q = searchQuery.toLowerCase().trim();
    return (
      r.id.toLowerCase().includes(q) ||
      r.actor.toLowerCase().includes(q) ||
      r.action.toLowerCase().includes(q) ||
      r.resource.toLowerCase().includes(q) ||
      r.result.toLowerCase().includes(q) ||
      r.detail.toLowerCase().includes(q)
    );
  });

  return (
    <div className="space-y-6 max-w-7xl mx-auto">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-slate-900 flex items-center gap-2.5">
            Audit Trail
            <span className="text-xs font-semibold text-slate-600 bg-slate-100 px-2 py-0.5 rounded border border-slate-200">
              Append-Only Ledger
            </span>
          </h1>
          <p className="text-xs text-slate-500 mt-1">
            Cryptographically sealed audit log recording every mutation, policy check, and credential rotation.
          </p>
        </div>

        <div className="flex items-center gap-2 text-xs text-emerald-700 bg-emerald-50 border border-emerald-200 px-3 py-1.5 rounded-lg shadow-sm">
          <ShieldCheck className="w-4 h-4 text-emerald-600" />
          No UPDATE / DELETE permissions granted on audit_events
        </div>
      </div>

      <div className="rounded-xl bg-white border border-slate-200 overflow-hidden shadow-sm">

        <div className="p-4 border-b border-slate-100 flex flex-col sm:flex-row sm:items-center justify-between gap-3 text-xs">
          <div className="relative w-full sm:w-80">
            <Search className="w-4 h-4 text-slate-400 absolute left-3 top-1/2 -translate-y-1/2" />
            <input
              type="text"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              placeholder="Search audit records by ID, actor, resource..."
              className="w-full bg-slate-50 border border-slate-200 rounded-lg pl-9 pr-8 py-1.5 text-slate-800 focus:outline-none focus:bg-white focus:border-indigo-500"
            />
            {searchQuery && (
              <button
                onClick={() => setSearchQuery("")}
                className="absolute right-2.5 top-1/2 -translate-y-1/2 text-slate-400 hover:text-slate-600 p-0.5"
                title="Clear"
              >
                <X className="w-3.5 h-3.5" />
              </button>
            )}
          </div>

          <div className="flex items-center gap-2 text-slate-500 flex-wrap">
            <Filter className="w-3.5 h-3.5" />
            <span>Outcome:</span>
            {(["ALL", "SUCCESS", "ALLOWED", "DENIED"] as const).map((outcome) => (
              <button
                key={outcome}
                onClick={() => setOutcomeFilter(outcome)}
                className={`px-2.5 py-1 rounded border text-[11px] font-medium transition-colors ${
                  outcomeFilter === outcome
                    ? "bg-indigo-50 text-indigo-700 border-indigo-200 font-bold"
                    : "bg-slate-50 text-slate-600 border-slate-200 hover:bg-slate-100"
                }`}
              >
                {outcome}
              </button>
            ))}
          </div>
        </div>

        {filteredRecords.length === 0 ? (
          <div className="p-12 text-center flex flex-col items-center justify-center">
            <div className="w-12 h-12 rounded-xl bg-slate-50 border border-slate-200 flex items-center justify-center text-slate-400 mb-3">
              <Search className="w-6 h-6" />
            </div>
            <h3 className="text-sm font-bold text-slate-800 mb-1">No Audit Records Found</h3>
            <p className="text-xs text-slate-500 max-w-sm mb-4">
              No audit entries matched &ldquo;{searchQuery}&rdquo;{outcomeFilter !== "ALL" ? ` with outcome: ${outcomeFilter}` : ""}.
            </p>
            <button
              onClick={() => {
                setSearchQuery("");
                setOutcomeFilter("ALL");
              }}
              className="px-3.5 py-1.5 text-xs font-semibold text-indigo-700 bg-indigo-50 hover:bg-indigo-100 border border-indigo-200 rounded-lg transition-colors"
            >
              Clear Search & Filter
            </button>
          </div>
        ) : (
          <table className="w-full text-left text-xs">
            <thead className="bg-slate-50 text-slate-500 uppercase tracking-wider text-[10px] border-b border-slate-200 font-semibold">
              <tr>
                <th className="py-3 px-4">Audit ID</th>
                <th className="py-3 px-4">Timestamp</th>
                <th className="py-3 px-4">Actor</th>
                <th className="py-3 px-4">Action</th>
                <th className="py-3 px-4">Resource</th>
                <th className="py-3 px-4">Outcome</th>
                <th className="py-3 px-4">Audit Details</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {filteredRecords.map((r) => (
              <tr key={r.id} className="hover:bg-slate-50/80 transition-colors">
                <td className="py-3.5 px-4 font-mono font-bold text-indigo-700">{r.id}</td>
                <td className="py-3.5 px-4 font-mono text-slate-500">{r.time}</td>
                <td className="py-3.5 px-4 font-semibold text-slate-800">{r.actor}</td>
                <td className="py-3.5 px-4 font-mono text-slate-700">{r.action}</td>
                <td className="py-3.5 px-4 font-mono text-indigo-700">{r.resource}</td>
                <td className="py-3.5 px-4">
                  <span
                    className={`inline-flex items-center gap-1 font-bold text-[10px] px-2 py-0.5 rounded ${
                      r.result === "DENIED"
                        ? "bg-rose-50 text-rose-700 border border-rose-200"
                        : "bg-emerald-50 text-emerald-700 border border-emerald-200"
                    }`}
                  >
                    {r.result}
                  </span>
                </td>
                <td className="py-3.5 px-4 text-slate-600">{r.detail}</td>
              </tr>
            ))}
            </tbody>
          </table>
        )}
      </div>
    </div>
  );
}
