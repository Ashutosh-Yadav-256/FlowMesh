"use client";

import { useState } from "react";
import { Radio, Search, Filter, CheckCircle2, AlertCircle, RefreshCw, X } from "lucide-react";

interface EventItem {
  id: string;
  type: string;
  source: string;
  status: "PROCESSED" | "FAILED";
  timestamp: string;
  payloadRef: string;
}

const eventsList: EventItem[] = [
  { id: "evt_98231", type: "order.created", source: "SAP ERP", status: "PROCESSED", timestamp: "22:31:02", payloadRef: "ref://blob/98231" },
  { id: "evt_98232", type: "customer.update", source: "PostgreSQL", status: "PROCESSED", timestamp: "22:30:14", payloadRef: "ref://blob/98232" },
  { id: "evt_98233", type: "order.created", source: "SAP ERP", status: "FAILED", timestamp: "22:21:00", payloadRef: "ref://blob/98233" },
  { id: "evt_98234", type: "inventory.update", source: "Warehouse API", status: "PROCESSED", timestamp: "22:15:30", payloadRef: "ref://blob/98234" },
  { id: "evt_98235", type: "shipment.dispatched", source: "Logistics Gateway", status: "PROCESSED", timestamp: "22:10:00", payloadRef: "ref://blob/98235" },
];

export default function EventsPage() {
  const [filterType, setFilterType] = useState("all");
  const [searchQuery, setSearchQuery] = useState("");

  const filteredEvents = eventsList.filter((e) => {
    if (filterType !== "all" && e.type !== filterType) return false;
    if (!searchQuery.trim()) return true;
    const q = searchQuery.toLowerCase().trim();
    return (
      e.id.toLowerCase().includes(q) ||
      e.type.toLowerCase().includes(q) ||
      e.source.toLowerCase().includes(q) ||
      e.status.toLowerCase().includes(q) ||
      e.payloadRef.toLowerCase().includes(q)
    );
  });

  return (
    <div className="space-y-6 max-w-7xl mx-auto">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-slate-900 flex items-center gap-2.5">
            Events Stream
            <span className="text-xs font-semibold text-slate-600 bg-slate-100 px-2 py-0.5 rounded border border-slate-200">
              NATS JetStream Bus
            </span>
          </h1>
          <p className="text-xs text-slate-500 mt-1">
            Durable CloudEvents stream with deduplication and consumer group delivery.
          </p>
        </div>

        <button className="flex items-center gap-1.5 px-3 py-1.5 bg-white hover:bg-slate-100 text-slate-700 rounded-lg text-xs font-semibold border border-slate-200 shadow-sm transition-colors">
          <RefreshCw className="w-3.5 h-3.5 text-indigo-600" />
          Live Stream (Active)
        </button>
      </div>

      <div className="rounded-xl bg-white border border-slate-200 overflow-hidden shadow-sm">
        <div className="p-4 border-b border-slate-100 flex flex-col sm:flex-row sm:items-center justify-between gap-3 text-xs">
          <div className="relative w-full sm:w-80">
            <Search className="w-4 h-4 text-slate-400 absolute left-3 top-1/2 -translate-y-1/2" />
            <input
              type="text"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              placeholder="Search by event ID, type, source..."
              className="w-full bg-slate-50 border border-slate-200 rounded-lg pl-9 pr-8 py-1.5 text-slate-800 focus:outline-none focus:bg-white focus:border-indigo-500"
            />
            {searchQuery && (
              <button
                onClick={() => setSearchQuery("")}
                className="absolute right-2.5 top-1/2 -translate-y-1/2 text-slate-400 hover:text-slate-600 p-0.5"
                title="Clear search"
              >
                <X className="w-3.5 h-3.5" />
              </button>
            )}
          </div>

          <div className="flex items-center gap-2 text-slate-500 flex-wrap">
            <Filter className="w-3.5 h-3.5" />
            <span>Filter:</span>
            {["all", "order.created", "customer.update", "inventory.update"].map((f) => (
              <button
                key={f}
                onClick={() => setFilterType(f)}
                className={`px-2.5 py-1 rounded border text-[11px] font-medium transition-colors ${
                  filterType === f
                    ? "bg-indigo-50 text-indigo-700 border-indigo-200 font-bold"
                    : "bg-slate-50 text-slate-600 border-slate-200 hover:bg-slate-100"
                }`}
              >
                {f}
              </button>
            ))}
          </div>
        </div>

        {filteredEvents.length === 0 ? (
          <div className="p-12 text-center flex flex-col items-center justify-center">
            <div className="w-12 h-12 rounded-xl bg-slate-50 border border-slate-200 flex items-center justify-center text-slate-400 mb-3">
              <Search className="w-6 h-6" />
            </div>
            <h3 className="text-sm font-bold text-slate-800 mb-1">No Matching Events</h3>
            <p className="text-xs text-slate-500 max-w-sm mb-4">
              No events matched &ldquo;{searchQuery}&rdquo;{filterType !== "all" ? ` for filter ${filterType}` : ""}.
            </p>
            <button
              onClick={() => {
                setSearchQuery("");
                setFilterType("all");
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
                <th className="py-3 px-4">Event ID</th>
                <th className="py-3 px-4">Type</th>
                <th className="py-3 px-4">Source</th>
                <th className="py-3 px-4">Status</th>
                <th className="py-3 px-4">Ingress Time</th>
                <th className="py-3 px-4 text-right">Payload</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {filteredEvents.map((evt) => (
                <tr key={evt.id} className="hover:bg-slate-50/80 transition-colors">
                  <td className="py-3.5 px-4 font-mono font-bold text-indigo-700">{evt.id}</td>
                  <td className="py-3.5 px-4 font-bold text-slate-900">{evt.type}</td>
                  <td className="py-3.5 px-4 text-slate-600">{evt.source}</td>
                  <td className="py-3.5 px-4">
                    <span
                      className={`inline-flex items-center gap-1 font-bold text-[10px] px-2 py-0.5 rounded ${
                        evt.status === "PROCESSED"
                          ? "bg-emerald-50 text-emerald-700 border border-emerald-200"
                          : "bg-rose-50 text-rose-700 border border-rose-200"
                      }`}
                    >
                      {evt.status}
                    </span>
                  </td>
                  <td className="py-3.5 px-4 text-slate-500 font-mono">{evt.timestamp}</td>
                  <td className="py-3.5 px-4 text-right">
                    <button className="px-2.5 py-1 text-[11px] bg-white hover:bg-slate-100 text-slate-700 border border-slate-200 rounded font-mono shadow-xs">
                      Inspect
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>
    </div>
  );
}
