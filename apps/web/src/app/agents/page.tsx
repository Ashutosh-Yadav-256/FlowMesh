"use client";

import { useState } from "react";
import {
  Cpu,
  Server,
  CheckCircle2,
  AlertCircle,
  ShieldCheck,
  RotateCw,
  Copy,
  Terminal,
  Layers,
  Database,
  Globe,
  FileCode,
  Lock,
} from "lucide-react";

interface AgentItem {
  id: string;
  name: string;
  version: string;
  status: "healthy" | "offline" | "degraded";
  connectorsCount: number;
  cpu: number;
  memory: number;
  queue: number;
  heartbeatSec: number;
  certExpiresDays: number;
}

const agentsList: AgentItem[] = [
  { id: "agent-prod-01", name: "production-01", version: "v0.4.2", status: "healthy", connectorsCount: 8, cpu: 12.4, memory: 31.2, queue: 14, heartbeatSec: 3, certExpiresDays: 82 },
  { id: "agent-wh-01", name: "warehouse-01", version: "v0.4.2", status: "healthy", connectorsCount: 3, cpu: 8.1, memory: 22.5, queue: 2, heartbeatSec: 4, certExpiresDays: 82 },
  { id: "agent-stg-01", name: "staging-01", version: "v0.4.2", status: "offline", connectorsCount: 5, cpu: 0, memory: 0, queue: 0, heartbeatSec: 1420, certExpiresDays: 45 },
];

export default function AgentsPage() {
  const [selectedAgent, setSelectedAgent] = useState<AgentItem>(agentsList[0]);
  const [showEnrollModal, setShowEnrollModal] = useState(false);
  const [copied, setCopied] = useState(false);

  const curlCommand = "curl -fsSL https://install.flowmesh.dev | sh -s -- --token flm_enroll_live_acme_8921";

  const handleCopy = () => {
    navigator.clipboard.writeText(curlCommand);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <div className="space-y-6 max-w-7xl mx-auto">

      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-slate-900 flex items-center gap-2.5">
            Edge Agents
            <span className="text-xs font-semibold text-slate-600 bg-slate-100 px-2 py-0.5 rounded border border-slate-200">
              Customer Network Daemons
            </span>
          </h1>
          <p className="text-xs text-slate-500 mt-1">
            Outbound mTLS agents executing connectors inside customer private VPCs with local SQLite buffering.
          </p>
        </div>

        <button
          onClick={() => setShowEnrollModal(true)}
          className="flex items-center gap-1.5 text-xs font-semibold bg-indigo-600 hover:bg-indigo-700 text-white px-4 py-2 rounded-lg transition-colors shadow-sm"
        >
          <Server className="w-4 h-4" />
          Register Agent
        </button>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">

        <div className="lg:col-span-2 rounded-xl bg-white border border-slate-200 overflow-hidden shadow-sm">
          <div className="p-4 border-b border-slate-100 flex items-center justify-between text-xs">
            <span className="font-bold text-slate-800 uppercase text-[11px]">Registered Daemons</span>
            <span className="text-slate-500">Showing {agentsList.length} total</span>
          </div>

          <table className="w-full text-left text-xs">
            <thead className="bg-slate-50 text-slate-500 uppercase tracking-wider text-[10px] border-b border-slate-200 font-semibold">
              <tr>
                <th className="py-3 px-4">Agent</th>
                <th className="py-3 px-4">Version</th>
                <th className="py-3 px-4">Status</th>
                <th className="py-3 px-4">Connectors</th>
                <th className="py-3 px-4 text-right">Action</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {agentsList.map((agent) => {
                const isSelected = selectedAgent.id === agent.id;
                return (
                  <tr
                    key={agent.id}
                    onClick={() => setSelectedAgent(agent)}
                    className={`cursor-pointer transition-colors ${
                      isSelected ? "bg-indigo-50/70" : "hover:bg-slate-50/80"
                    }`}
                  >
                    <td className="py-3.5 px-4 font-medium text-slate-800">
                      <div className="flex items-center gap-2">
                        <Cpu className="w-4 h-4 text-indigo-600" />
                        <div>
                          <p className="font-bold text-slate-900">{agent.name}</p>
                          <p className="text-[10px] font-mono text-slate-500">{agent.id}</p>
                        </div>
                      </div>
                    </td>
                    <td className="py-3.5 px-4 font-mono text-slate-600">{agent.version}</td>
                    <td className="py-3.5 px-4">
                      <span
                        className={`inline-flex items-center gap-1 text-[11px] font-semibold px-2 py-0.5 rounded ${
                          agent.status === "healthy"
                            ? "text-emerald-700 bg-emerald-50 border border-emerald-200"
                            : "text-slate-600 bg-slate-100 border border-slate-200"
                        }`}
                      >
                        <span
                          className={`w-1.5 h-1.5 rounded-full ${
                            agent.status === "healthy" ? "bg-emerald-500" : "bg-slate-400"
                          }`}
                        ></span>
                        {agent.status}
                      </span>
                    </td>
                    <td className="py-3.5 px-4 font-mono text-slate-600">
                      {agent.connectorsCount} configured
                    </td>
                    <td className="py-3.5 px-4 text-right">
                      <button className="px-2.5 py-1 text-[11px] bg-white hover:bg-slate-100 text-slate-700 border border-slate-200 rounded font-medium shadow-xs">
                        Inspect
                      </button>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>

        <div className="rounded-xl bg-white border border-slate-200 p-6 space-y-6 text-xs shadow-sm">
          <div>
            <div className="flex items-center justify-between">
              <span className="text-[10px] uppercase font-bold text-indigo-600 tracking-wider">
                Edge Agent Inspector
              </span>
              <span className="font-mono text-[10px] text-slate-500">{selectedAgent.version}</span>
            </div>
            <h2 className="text-lg font-bold text-slate-900 mt-1">Agent: {selectedAgent.name}</h2>
            <div className="flex items-center gap-2 mt-1">
              <span className="text-emerald-700 font-bold flex items-center gap-1">
                <CheckCircle2 className="w-3.5 h-3.5 text-emerald-600" /> HEALTHY
              </span>
              <span className="text-slate-300">•</span>
              <span className="text-slate-500">Last heartbeat: {selectedAgent.heartbeatSec}s ago</span>
            </div>
          </div>

          <div className="grid grid-cols-3 gap-2 text-center">
            <div className="p-3 rounded-lg bg-slate-50 border border-slate-200">
              <p className="text-[10px] uppercase text-slate-500 font-semibold">CPU</p>
              <p className="text-lg font-bold text-slate-900 mt-1">{selectedAgent.cpu}%</p>
            </div>
            <div className="p-3 rounded-lg bg-slate-50 border border-slate-200">
              <p className="text-[10px] uppercase text-slate-500 font-semibold">Memory</p>
              <p className="text-lg font-bold text-slate-900 mt-1">{selectedAgent.memory}%</p>
            </div>
            <div className="p-3 rounded-lg bg-slate-50 border border-slate-200">
              <p className="text-[10px] uppercase text-slate-500 font-semibold">Queue</p>
              <p className="text-lg font-bold text-indigo-700 mt-1">{selectedAgent.queue}</p>
            </div>
          </div>

          <div className="space-y-2">
            <p className="font-bold text-slate-800 uppercase tracking-wider text-[11px]">
              Active Connectors
            </p>
            <div className="space-y-1.5">
              {[
                { name: "PostgreSQL", type: "DB" },
                { name: "SAP ERP", type: "ERP" },
                { name: "Warehouse API", type: "REST" },
                { name: "SFTP Gateway", type: "SFTP" },
              ].map((c) => (
                <div
                  key={c.name}
                  className="flex items-center justify-between p-2 rounded bg-slate-50 border border-slate-200"
                >
                  <span className="font-semibold text-slate-800">{c.name}</span>
                  <span className="text-emerald-700 font-bold flex items-center gap-1">
                    <CheckCircle2 className="w-3.5 h-3.5 text-emerald-600" /> Healthy
                  </span>
                </div>
              ))}
            </div>
          </div>

          <div className="space-y-2">
            <p className="font-bold text-slate-800 uppercase tracking-wider text-[11px]">
              Security & Policy Enforcement
            </p>
            <div className="p-3 rounded-lg bg-slate-50 border border-slate-200 space-y-2">
              <div className="flex justify-between">
                <span className="text-slate-500">mTLS Certificate:</span>
                <span className="text-emerald-700 font-bold">Valid</span>
              </div>
              <div className="flex justify-between">
                <span className="text-slate-500">Expires in:</span>
                <span className="text-slate-800 font-mono font-medium">{selectedAgent.certExpiresDays} days</span>
              </div>
              <div className="flex justify-between">
                <span className="text-slate-500">Policy Engine:</span>
                <span className="text-indigo-700 font-bold">Strict Deny Allowlist</span>
              </div>
            </div>
          </div>

          <div className="grid grid-cols-2 gap-2 pt-2">
            <button className="py-2 bg-white hover:bg-slate-100 text-slate-700 border border-slate-200 rounded font-semibold transition-colors shadow-xs">
              Rotate Certificate
            </button>
            <button className="py-2 bg-white hover:bg-slate-100 text-slate-700 border border-slate-200 rounded font-semibold transition-colors shadow-xs">
              Restart Agent
            </button>
          </div>
        </div>
      </div>

      {showEnrollModal && (
        <div className="fixed inset-0 z-50 bg-slate-900/40 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="w-full max-w-lg bg-white border border-slate-200 rounded-2xl p-6 space-y-4 shadow-2xl">
            <h2 className="text-base font-bold text-slate-900 flex items-center gap-2">
              <Server className="w-5 h-5 text-indigo-600" />
              Register New FlowMesh Edge Agent
            </h2>
            <p className="text-xs text-slate-500">
              Run this command on your private Linux or container host. The agent generates a CSR, establishes outbound mTLS, and registers with this tenant.
            </p>

            <div className="p-3 rounded-lg bg-slate-50 border border-slate-200 flex items-center justify-between font-mono text-[11px] text-indigo-950">
              <span className="truncate mr-2">{curlCommand}</span>
              <button
                onClick={handleCopy}
                className="p-1.5 bg-white hover:bg-slate-100 border border-slate-200 rounded text-slate-700 transition-colors shadow-xs"
              >
                {copied ? <CheckCircle2 className="w-4 h-4 text-emerald-600" /> : <Copy className="w-4 h-4" />}
              </button>
            </div>

            <div className="flex justify-end pt-2">
              <button
                onClick={() => setShowEnrollModal(false)}
                className="px-4 py-2 bg-indigo-600 hover:bg-indigo-700 text-white rounded-lg text-xs font-semibold shadow-sm"
              >
                Done
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
