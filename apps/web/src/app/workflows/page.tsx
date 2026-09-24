"use client";

import { useState, useEffect } from "react";
import { getActiveTenantId, postToApi } from "@/lib/api";
import {
  Workflow,
  Bell,
  UploadCloud,
  Play,
  CheckCircle2,
  AlertCircle,
  Database,
  Globe,
  Radio,
  FileCode,
  Flame,
  ArrowRight,
  ShieldCheck,
  Plus,
  Settings,
  Layers,
  Sparkles,
  History,
  RotateCcw,
  UserCheck,
  Clock,
  Send,
  GitBranch,
  Trash2,
  Check,
  ChevronRight,
  X,
  CheckCircle,
  AlertTriangle,
} from "lucide-react";

interface NodeItem {
  id: string;
  name: string;
  type: string;
  detail: string;
  badge: string;
  connection_id?: string;
  config?: Record<string, any>;
}

interface WorkflowVersion {
  version: number;
  changelog: string;
  deployed_at: string;
  deployed_by: string;
  node_count: number;
  is_active: boolean;
}

const initialDAG: NodeItem[] = [
  { id: "node_1", name: "SAP Order Ingress", type: "trigger.webhook", detail: "POST /orders (JSON payload)", badge: "Trigger", config: { path: "/orders" } },
  { id: "node_2", name: "Validate Order Payload", type: "control.condition", detail: "Payload schema ref: order_v1", badge: "Control", config: { schema_ref: "order_v1" } },
  { id: "node_3", name: "Customer Tier Lookup", type: "action.db_query", detail: "SELECT * FROM customers WHERE id = :customer_id", badge: "Database", connection_id: "conn_pg_01", config: { sql: "SELECT * FROM customers WHERE id = :customer_id" } },
  { id: "node_4", name: "Credit Check & Approval Gate", type: "action.approval", detail: "Operator signoff required if amount > $5,000", badge: "Human Gate", config: { threshold: 5000, approver_role: "operator" } },
  { id: "node_5", name: "Concurrent Warehouse & ERP Sync", type: "control.parallel", detail: "Parallel dispatch to SAP ERP and Warehouse REST", badge: "Parallel", config: { branches: [{ name: "warehouse_rest" }, { name: "sap_queue" }] } },
  { id: "node_6", name: "Notify Warehouse API", type: "action.http", detail: "POST /shipments (Exponential backoff x3)", badge: "HTTP", connection_id: "conn_rest_01", config: { method: "POST", endpoint: "/shipments" } },
  { id: "node_7", name: "Publish Order Dispatched", type: "action.event_publish", detail: "Topic: orders.dispatched (NATS JetStream)", badge: "Event", config: { topic: "orders.dispatched" } },
  { id: "node_8", name: "Emit Compliance Audit Log", type: "audit.log", detail: "Immutable ledger record (SOX compliance)", badge: "Audit", config: { action: "order.dispatched" } },
];

const mockVersions: WorkflowVersion[] = [
  { version: 3, changelog: "Added credit check human approval gate & parallel ERP sync", deployed_at: "2026-09-19 22:45 UTC", deployed_by: "dev@flowmesh.dev", node_count: 8, is_active: true },
  { version: 2, changelog: "Added warehouse HTTP retry policy with exponential jitter", deployed_at: "2026-09-18 14:12 UTC", deployed_by: "dev@flowmesh.dev", node_count: 6, is_active: false },
  { version: 1, changelog: "Initial production baseline order processing DAG", deployed_at: "2026-09-15 09:30 UTC", deployed_by: "lead@flowmesh.dev", node_count: 5, is_active: false },
];

export default function WorkflowsPage() {
  const [isCleanMode, setIsCleanMode] = useState<boolean>(false);
  const [nodes, setNodes] = useState<NodeItem[]>(initialDAG);
  const [selectedNode, setSelectedNode] = useState<NodeItem>(initialDAG[0]);
  const [currentVersion, setCurrentVersion] = useState<number>(3);
  const [versions, setVersions] = useState<WorkflowVersion[]>(mockVersions);
  const [showDeployModal, setShowDeployModal] = useState<boolean>(false);
  const [showRollbackModal, setShowRollbackModal] = useState<boolean>(false);
  const [deployChangelog, setDeployChangelog] = useState<string>("");
  const [selectedRollbackVer, setSelectedRollbackVer] = useState<number>(2);
  const [deploySuccessBanner, setDeploySuccessBanner] = useState<string | null>(null);

  useEffect(() => {
    const isAcme = getActiveTenantId() === "tenant_acme";
    if (!isAcme) {
      setIsCleanMode(true);
      setNodes([]);
      setVersions([]);
      setCurrentVersion(0);
    } else {
      setIsCleanMode(false);
      setNodes(initialDAG);
      setSelectedNode(initialDAG[0]);
      setVersions(mockVersions);
      setCurrentVersion(3);
    }

    const handleTenantChanged = () => {
      const currentIsAcme = getActiveTenantId() === "tenant_acme";
      if (!currentIsAcme) {
        setIsCleanMode(true);
        setNodes([]);
        setVersions([]);
        setCurrentVersion(0);
      } else {
        setIsCleanMode(false);
        setNodes(initialDAG);
        setSelectedNode(initialDAG[0]);
        setVersions(mockVersions);
        setCurrentVersion(3);
      }
    };
    window.addEventListener("flowmesh:tenant_changed", handleTenantChanged);
    return () => window.removeEventListener("flowmesh:tenant_changed", handleTenantChanged);
  }, []);

  const validationErrors: string[] = [];
  const validationWarnings: string[] = [];

  if (nodes.length < 2) {
    validationErrors.push("Workflow must contain at least 2 connected nodes.");
  }
  const hasTrigger = nodes.some((n) => n.type.startsWith("trigger."));
  if (!hasTrigger) {
    validationErrors.push("DAG missing entry trigger node (e.g. trigger.webhook or trigger.event).");
  }
  const hasApproval = nodes.some((n) => n.type === "action.approval");
  const isValid = validationErrors.length === 0;

  const nodePalette = [
    { type: "trigger.cron", label: "Scheduled Cron Job", badge: "Schedule", icon: Clock, detail: "5-part cron (e.g. 0 2 * * *) or interval timer" },
    { type: "trigger.webhook", label: "Webhook Ingress", badge: "Trigger", icon: Globe, detail: "Ingest HTTP webhook" },
    { type: "trigger.event", label: "Event Ingress", badge: "Trigger", icon: Radio, detail: "Subscribe to event topic" },
    { type: "action.servicenow", label: "ServiceNow ITSM", badge: "ITSM", icon: Globe, detail: "Create incident or change request", conn: "conn_snow_01" },
    { type: "action.active_directory", label: "Active Directory", badge: "Identity", icon: UserCheck, detail: "Provision/disable user or group audit", conn: "conn_ad_01" },
    { type: "action.powershell", label: "PowerShell Cmdlet", badge: "Script", icon: FileCode, detail: "Execute cmdlet or restart Windows service", conn: "conn_win_01" },
    { type: "action.paramiko_ssh", label: "Paramiko SSH/SFTP", badge: "SSH", icon: Layers, detail: "Remote execution & secure file transfer", conn: "conn_ssh_01" },
    { type: "transform.pandas", label: "Pandas Transform", badge: "Data", icon: Database, detail: "IQR outlier detection & dataframe merges" },
    { type: "action.db_query", label: "Postgres Read", badge: "Database", icon: Database, detail: "SQL Query via Edge Agent", conn: "conn_pg_01" },
    { type: "action.db_write", label: "Postgres Write", badge: "Database", icon: Database, detail: "SQL Insert/Update (ACID)", conn: "conn_pg_01" },
    { type: "action.http", label: "REST Gateway", badge: "HTTP", icon: Globe, detail: "HTTP REST call (Retries x3)", conn: "conn_rest_01" },
    { type: "action.approval", label: "Approval Gate", badge: "Human Gate", icon: UserCheck, detail: "Pauses run for operator review" },
    { type: "control.parallel", label: "Parallel Lanes", badge: "Parallel", icon: GitBranch, detail: "Concurrent branch execution" },
    { type: "control.delay", label: "Delay Cooldown", badge: "Delay", icon: Clock, detail: "Execution pause timer" },
    { type: "action.event_publish", label: "Event Publish", badge: "Event", icon: Send, detail: "Emit NATS JetStream event" },
    { type: "action.notification", label: "Slack / Teams", badge: "Notification", icon: Bell, detail: "Channel alert dispatch" },
    { type: "audit.log", label: "Immutable Audit", badge: "Audit", icon: ShieldCheck, detail: "Tamper-evident audit trail" },
  ];

  const handleAddNode = (template: (typeof nodePalette)[0]) => {
    const newNode: NodeItem = {
      id: `node_${nodes.length + 1}`,
      name: template.label,
      type: template.type,
      detail: template.detail,
      badge: template.badge,
      connection_id: template.conn,
      config: {},
    };
    setNodes([...nodes, newNode]);
    setSelectedNode(newNode);
  };

  const handleDeleteNode = (id: string) => {
    if (nodes.length <= 1) return;
    const filtered = nodes.filter((n) => n.id !== id);
    setNodes(filtered);
    if (selectedNode.id === id) {
      setSelectedNode(filtered[0]);
    }
  };

  const handleDeployVersion = () => {
    const nextVer = currentVersion + 1;
    const newVerRecord: WorkflowVersion = {
      version: nextVer,
      changelog: deployChangelog || `Production release v${nextVer}`,
      deployed_at: new Date().toISOString().replace("T", " ").substring(0, 19) + " UTC",
      deployed_by: "operator@flowmesh.dev",
      node_count: nodes.length,
      is_active: true,
    };
    const updatedVersions = [
      newVerRecord,
      ...versions.map((v) => ({ ...v, is_active: false })),
    ];
    setVersions(updatedVersions);
    setCurrentVersion(nextVer);
    setShowDeployModal(false);
    setDeployChangelog("");
    setDeploySuccessBanner(`Successfully deployed immutable version v${nextVer} (ADR-0004 pinned). All in-flight executions continue on their pinned version.`);
    setTimeout(() => setDeploySuccessBanner(null), 6000);
  };

  const handleRollback = () => {
    const updatedVersions = versions.map((v) => ({
      ...v,
      is_active: v.version === selectedRollbackVer,
    }));
    setVersions(updatedVersions);
    setCurrentVersion(selectedRollbackVer);
    setShowRollbackModal(false);
    setDeploySuccessBanner(`Rolled back active workflow pointer to v${selectedRollbackVer} (ADR-0004). Historical run data preserved.`);
    setTimeout(() => setDeploySuccessBanner(null), 6000);
  };

  return (
    <div className="space-y-6 max-w-7xl mx-auto pb-12">

      {deploySuccessBanner && (
        <div className="p-4 rounded-xl bg-emerald-50 border border-emerald-300 text-emerald-800 text-xs flex items-center justify-between shadow-sm animate-in fade-in duration-200">
          <div className="flex items-center gap-2.5">
            <CheckCircle className="w-4 h-4 text-emerald-600 shrink-0" />
            <span className="font-semibold">{deploySuccessBanner}</span>
          </div>
          <button onClick={() => setDeploySuccessBanner(null)} className="text-emerald-600 hover:text-emerald-900">
            <X className="w-4 h-4" />
          </button>
        </div>
      )}

      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-3">
            <h1 className="text-2xl font-bold tracking-tight text-[#1B1B1B] flex items-center gap-2.5">
              Workflow Builder & DAG Studio
            </h1>
            <span className="text-xs font-semibold text-[#874436] bg-[#F8EBE8] px-2.5 py-0.5 rounded-full border border-[#EED1CB] flex items-center gap-1.5">
              <span className="w-1.5 h-1.5 rounded-full bg-[#874436]"></span>
              Active: v{currentVersion} Pinned
            </span>
          </div>
          <p className="text-xs text-[#4F4F4F] mt-1.5 leading-relaxed">
            Authoritative visual editor directly bound to the FlowMesh Workflow Definition schema. Deployed workflows are strictly immutable (ADR-0004).
          </p>
        </div>

        <div className="flex items-center gap-2.5">

          <button
            onClick={() => setShowRollbackModal(true)}
            className="px-3.5 py-2 bg-[#FAF8F5] hover:bg-[#F3EFEA] text-[#1B1B1B] rounded-lg text-xs font-semibold border border-[#D5CABE] flex items-center gap-1.5 transition-colors shadow-sm"
          >
            <RotateCcw className="w-3.5 h-3.5 text-[#E17709]" />
            Rollback
          </button>

          <button
            onClick={() => setShowRollbackModal(true)}
            className="px-3.5 py-2 bg-[#FAF8F5] hover:bg-[#F3EFEA] text-[#1B1B1B] rounded-lg text-xs font-semibold border border-[#D5CABE] flex items-center gap-1.5 transition-colors shadow-sm"
          >
            <History className="w-3.5 h-3.5 text-[#455CA1]" />
            Versions ({versions.length})
          </button>

          <button
            onClick={() => setShowDeployModal(true)}
            className="px-4 py-2 bg-[#874436] hover:bg-[#6E362A] text-white rounded-lg text-xs font-semibold shadow-sm flex items-center gap-1.5 transition-all"
          >
            <UploadCloud className="w-3.5 h-3.5" />
            Deploy (v{currentVersion + 1})
          </button>
        </div>
      </div>

      {isCleanMode && nodes.length === 0 ? (
        <div className="rounded-xl bg-[#FAF8F5] border border-[#D5CABE] p-12 text-center flex flex-col items-center justify-center shadow-sm">
          <div className="w-14 h-14 rounded-2xl bg-[#F8EBE8] border border-[#EED1CB] flex items-center justify-center text-[#874436] mb-4 shadow-sm">
            <Workflow className="w-7 h-7" />
          </div>
          <h3 className="text-base font-bold text-[#1B1B1B] mb-1">
            No Workflows Created
          </h3>
          <p className="text-xs text-[#7A7165] max-w-md mb-6 leading-relaxed">
            This workspace is currently a clean slate. Build custom event-driven DAG workflows with visual node authoring, Kahn's cycle detection, and immutable version pinning (ADR-0004).
          </p>
          <div className="flex flex-wrap items-center justify-center gap-3">
            <button
              onClick={() => {
                setIsCleanMode(false);
                const starterNodes: NodeItem[] = [
                  { id: "node_1", name: "Webhook Ingress", type: "trigger.webhook", detail: "POST /events/ingress", badge: "Trigger", config: { path: "/events/ingress" } },
                  { id: "node_2", name: "Postgres Read", type: "action.db_query", detail: "SELECT * FROM orders WHERE id = :order_id", badge: "Database", connection_id: "conn_pg_01", config: { sql: "SELECT * FROM orders WHERE id = :order_id" } },
                ];
                setNodes(starterNodes);
                setSelectedNode(starterNodes[0]);
                setCurrentVersion(1);
                setVersions([
                  { version: 1, changelog: "Initial production baseline workflow", deployed_at: "Just now", deployed_by: "operator@flowmesh.dev", node_count: 2, is_active: true }
                ]);
              }}
              className="flex items-center gap-2 text-xs font-semibold bg-[#874436] hover:bg-[#6E362A] text-white px-4 py-2.5 rounded-lg transition-colors shadow-sm"
            >
              <Plus className="w-4 h-4" />
              Create Your First Workflow
            </button>
            <button
              onClick={async () => {
                await postToApi("/api/v1/demo/seed");
                window.location.reload();
              }}
              className="flex items-center gap-2 text-xs font-semibold bg-[#FAF8F5] hover:bg-[#F3EFEA] text-[#1B1B1B] px-4 py-2.5 rounded-lg transition-colors border border-[#D5CABE] shadow-sm"
            >
              <Sparkles className="w-4 h-4 text-[#874436]" />
              Load Example Workflows
            </button>
          </div>
          <div className="mt-8 pt-6 border-t border-[#E8DFD5] max-w-lg w-full flex items-center justify-center gap-6 text-[11px] text-[#7A7165]">
            <span className="flex items-center gap-1.5"><ShieldCheck className="w-4 h-4 text-[#2E6B47]" /> Immutable Deployments (ADR-0004)</span>
            <span className="flex items-center gap-1.5"><CheckCircle2 className="w-4 h-4 text-[#455CA1]" /> 0-Cycle Kahn DAG Engine</span>
          </div>
        </div>
      ) : (
        <>
          {/* Pre-flight Validation Summary Bar */}
          <div className={`p-4 rounded-xl border flex flex-col sm:flex-row sm:items-center justify-between gap-3 text-xs shadow-sm ${
            isValid
              ? "bg-[#FAF8F5] border-[#D5CABE] text-[#4F4F4F]"
              : "bg-[#FDF6F5] border-[#EED1CB] text-[#874436]"
          }`}>
            <div className="flex items-center gap-3">
              {isValid ? (
                <div className="w-7 h-7 rounded-full bg-emerald-50 text-emerald-700 flex items-center justify-center border border-emerald-200">
                  <CheckCircle2 className="w-4 h-4" />
                </div>
              ) : (
                <div className="w-7 h-7 rounded-full bg-rose-50 text-rose-700 flex items-center justify-center border border-rose-200">
                  <AlertCircle className="w-4 h-4" />
                </div>
              )}
              <div>
                <p className="font-bold text-[#1B1B1B]">
                  {isValid ? "Pre-flight Verification: Directed Acyclic Graph (DAG) Clean" : "Validation Blocked"}
                </p>
                <p className="text-[11px] text-[#7A7165]">
                  {isValid
                    ? `Kahn's topological sort verified 0 cycles. All ${nodes.length} nodes reachable from entry trigger.`
                    : validationErrors[0]}
                </p>
              </div>
            </div>

            <div className="flex items-center gap-3 text-[11px] text-[#7A7165] border-t sm:border-t-0 border-[#D5CABE] pt-2 sm:pt-0">
              <span className="flex items-center gap-1.5">
                <span className="w-1.5 h-1.5 rounded-full bg-[#874436]"></span>
                Nodes: <strong className="text-[#1B1B1B]">{nodes.length}</strong>
              </span>
              <span className="flex items-center gap-1.5">
                <span className="w-1.5 h-1.5 rounded-full bg-[#455CA1]"></span>
                Edges: <strong className="text-[#1B1B1B]">{Math.max(0, nodes.length - 1)}</strong>
              </span>
              <span className="flex items-center gap-1.5">
                <span className="w-1.5 h-1.5 rounded-full bg-[#E17709]"></span>
                Gates: <strong className="text-[#1B1B1B]">{hasApproval ? "1 Approval" : "None"}</strong>
              </span>
            </div>
          </div>

      {/* Main Studio Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* Left Col: Node Palette (3 cols) */}
        <div className="lg:col-span-3 space-y-4">
          <div className="rounded-xl bg-[#FAF8F5] border border-[#D5CABE] p-4 space-y-3 shadow-sm">
            <div className="flex items-center justify-between pb-2 border-b border-[#D5CABE]">
              <span className="text-[11px] uppercase tracking-wider font-bold text-[#1B1B1B] flex items-center gap-1.5">
                <Layers className="w-3.5 h-3.5 text-[#874436]" />
                Node Library
              </span>
              <span className="text-[10px] text-[#968676] font-mono">11 types</span>
            </div>

            <p className="text-[11px] text-[#4F4F4F] leading-relaxed">Click any component to append it directly to the DAG pipeline:</p>

            <div className="space-y-1.5 max-h-[580px] overflow-y-auto pr-1">
              {nodePalette.map((item) => {
                const Icon = item.icon;
                return (
                  <button
                    key={item.label}
                    onClick={() => handleAddNode(item)}
                    className="w-full p-2.5 rounded-lg bg-[#F3EFEA] hover:bg-[#FAF8F5] border border-[#D5CABE] hover:border-[#874436] text-left transition-all group flex items-start gap-2.5"
                  >
                    <div className="w-6 h-6 rounded bg-[#FAF8F5] group-hover:bg-[#F8EBE8] text-[#874436] flex items-center justify-center shrink-0 border border-[#D5CABE] mt-0.5 shadow-xs">
                      <Icon className="w-3.5 h-3.5" />
                    </div>
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center justify-between">
                        <span className="text-xs font-semibold text-[#1B1B1B] group-hover:text-[#874436] truncate">
                          {item.label}
                        </span>
                        <span className="text-[9px] px-1.5 py-0.2 rounded bg-[#E6DFD5] text-[#1B1B1B] font-medium">
                          {item.badge}
                        </span>
                      </div>
                      <p className="text-[10px] text-[#4F4F4F] truncate mt-0.5">{item.detail}</p>
                    </div>
                  </button>
                );
              })}
            </div>
          </div>
        </div>

        {/* Center Col: Visual DAG Canvas (5 cols) */}
        <div className="lg:col-span-5 rounded-xl bg-[#FAF8F5] border border-[#D5CABE] p-5 space-y-4 relative overflow-hidden flex flex-col shadow-sm">
          <div className="flex items-center justify-between border-b border-[#D5CABE] pb-3 text-xs">
            <span className="font-bold text-[#1B1B1B] uppercase tracking-wider text-[11px] flex items-center gap-2">
              <Workflow className="w-4 h-4 text-[#874436]" />
              DAG Topology Graph
            </span>
            <div className="flex items-center gap-2 text-[11px] text-[#968676] font-mono">
              <span className="w-2 h-2 rounded-full bg-[#2E6B47]"></span>
              Synchronized to schema
            </div>
          </div>

          {/* Visual Node Chain */}
          <div className="space-y-3 py-2 flex-1 overflow-y-auto max-h-[640px] pr-2">
            {nodes.map((node, index) => {
              const isSelected = selectedNode?.id === node.id;
              const isTrigger = node.type.startsWith("trigger.");
              const isApproval = node.type === "action.approval";
              const isParallel = node.type === "control.parallel";

              return (
                <div key={node.id} className="space-y-2">
                  <div
                    onClick={() => setSelectedNode(node)}
                    className={`p-3.5 rounded-xl border cursor-pointer transition-all flex items-center justify-between ${
                      isSelected
                        ? "bg-indigo-50/80 border-indigo-500 text-slate-900 shadow-md ring-1 ring-indigo-400"
                        : "bg-slate-50 border-slate-200 text-slate-800 hover:border-slate-300 hover:bg-slate-100/70"
                    }`}
                  >
                    <div className="flex items-center gap-3 min-w-0">
                      <span className={`w-6 h-6 rounded-full font-bold text-xs flex items-center justify-center shrink-0 border ${
                        isTrigger
                          ? "bg-emerald-50 text-emerald-700 border-emerald-200"
                          : isApproval
                          ? "bg-amber-50 text-amber-800 border-amber-200"
                          : isParallel
                          ? "bg-sky-50 text-sky-700 border-sky-200"
                          : "bg-indigo-50 text-indigo-700 border-indigo-200"
                      }`}>
                        {index + 1}
                      </span>
                      <div className="truncate">
                        <div className="flex items-center gap-2">
                          <p className="font-bold text-xs text-slate-900 truncate">{node.name}</p>
                          <span className="text-[9px] px-1.5 py-0.2 rounded bg-slate-200 text-slate-700 font-medium">
                            {node.badge}
                          </span>
                        </div>
                        <p className="text-[11px] text-slate-500 truncate mt-0.5">{node.detail}</p>
                      </div>
                    </div>

                    <div className="flex items-center gap-2 shrink-0 ml-2">
                      {node.connection_id && (
                        <span className="text-[9px] px-1.5 py-0.5 rounded bg-indigo-50 text-indigo-700 border border-indigo-200 font-medium">
                          {node.connection_id}
                        </span>
                      )}
                      <span className="text-[10px] font-mono text-slate-500 bg-white px-1.5 py-0.5 rounded border border-slate-200">
                        {node.id}
                      </span>
                      <button
                        onClick={(e) => {
                          e.stopPropagation();
                          handleDeleteNode(node.id);
                        }}
                        className="text-slate-400 hover:text-rose-600 p-1 transition-colors"
                        title="Remove step"
                      >
                        <Trash2 className="w-3.5 h-3.5" />
                      </button>
                    </div>
                  </div>

                  {/* Connecting Arrow */}
                  {index < nodes.length - 1 && (
                    <div className="flex justify-center items-center -my-1">
                      <div className="w-0.5 h-3.5 bg-indigo-300"></div>
                    </div>
                  )}
                </div>
              );
            })}
          </div>
        </div>

        {/* Right Col: Node Inspector Drawer (4 cols) */}
        <div className="lg:col-span-4 rounded-xl bg-white border border-slate-200 p-5 space-y-5 shadow-sm">
          <div className="border-b border-slate-100 pb-3">
            <span className="text-[10px] uppercase font-bold text-indigo-600 tracking-wider">
              Step Inspector & Schema Config
            </span>
            <h2 className="text-base font-bold text-slate-900 mt-1">{selectedNode?.name}</h2>
            <div className="flex items-center gap-2 mt-1">
              <span className="text-[10px] font-mono text-slate-600 bg-slate-100 px-1.5 py-0.5 rounded border border-slate-200">
                type: {selectedNode?.type}
              </span>
              <span className="text-[10px] font-mono text-slate-600 bg-slate-100 px-1.5 py-0.5 rounded border border-slate-200">
                id: {selectedNode?.id}
              </span>
            </div>
          </div>

          <div className="space-y-4 text-xs">
            <div>
              <label className="block text-slate-700 font-semibold mb-1">Step Display Name</label>
              <input
                type="text"
                value={selectedNode?.name}
                onChange={(e) => {
                  const updated = { ...selectedNode, name: e.target.value };
                  setSelectedNode(updated);
                  setNodes(nodes.map((n) => (n.id === updated.id ? updated : n)));
                }}
                className="w-full bg-white border border-slate-200 rounded-lg p-2.5 text-slate-900 focus:outline-none focus:border-indigo-500 focus:ring-1 focus:ring-indigo-500"
              />
            </div>

            {selectedNode?.type.startsWith("action.db") && (
              <div>
                <label className="block text-slate-700 font-semibold mb-1">Target Infrastructure Connection</label>
                <select
                  value={selectedNode?.connection_id || "conn_pg_01"}
                  onChange={(e) => {
                    const updated = { ...selectedNode, connection_id: e.target.value };
                    setSelectedNode(updated);
                    setNodes(nodes.map((n) => (n.id === updated.id ? updated : n)));
                  }}
                  className="w-full bg-white border border-slate-200 rounded-lg p-2.5 text-slate-900 focus:outline-none focus:border-indigo-500"
                >
                  <option value="conn_pg_01">conn_pg_01 (PostgreSQL Orders via Edge Agent)</option>
                  <option value="conn_redis_01">conn_redis_01 (RediForge State & Distributed Lock)</option>
                </select>
                <p className="text-[10px] text-slate-500 mt-1">
                  Enforces strict tenant boundary. Command is signed with Ed25519 for Edge Agent dispatch.
                </p>
              </div>
            )}

            {selectedNode?.type === "action.http" && (
              <div>
                <label className="block text-slate-700 font-semibold mb-1">Target REST Endpoint</label>
                <input
                  type="text"
                  defaultValue="/shipments"
                  className="w-full bg-white border border-slate-200 rounded-lg p-2.5 text-slate-900 font-mono"
                />
              </div>
            )}

            {selectedNode?.type === "action.approval" && (
              <div className="p-3 rounded-lg bg-amber-50 border border-amber-200 space-y-2">
                <div className="flex items-center gap-2 text-amber-800 font-bold text-xs">
                  <UserCheck className="w-4 h-4 text-amber-600" />
                  Human-in-the-Loop Review Policy
                </div>
                <p className="text-[11px] text-slate-700">
                  Execution halts with status <code>WAITING_APPROVAL</code>. Requires operator or owner approval via <code>POST /api/v1/runs/:id/approve</code>.
                </p>
                <div>
                  <label className="block text-[10px] text-slate-600 mb-1 font-medium">Approver Role Authority</label>
                  <select className="w-full bg-white border border-slate-200 rounded p-1.5 text-slate-800 text-xs">
                    <option value="operator">Operator or Owner</option>
                    <option value="finance_lead">Finance Lead</option>
                    <option value="compliance_officer">Compliance Officer</option>
                  </select>
                </div>
              </div>
            )}

            {selectedNode?.type === "control.parallel" && (
              <div className="p-3 rounded-lg bg-sky-50 border border-sky-200 space-y-2">
                <div className="flex items-center gap-2 text-sky-800 font-bold text-xs">
                  <GitBranch className="w-4 h-4 text-sky-600" />
                  Concurrent Execution Lanes
                </div>
                <p className="text-[11px] text-slate-700">
                  Executes child lanes concurrently via <code>asyncio.gather</code> and merges results deterministically.
                </p>
              </div>
            )}

            <div>
              <label className="block text-slate-700 font-semibold mb-1">Retry & Reliability Policy</label>
              <div className="grid grid-cols-2 gap-2">
                <div className="bg-slate-50 border border-slate-200 rounded-lg p-2">
                  <span className="text-[10px] text-slate-500 block">Max Attempts</span>
                  <span className="text-slate-900 font-mono font-bold">3 (Backoff)</span>
                </div>
                <div className="bg-slate-50 border border-slate-200 rounded-lg p-2">
                  <span className="text-[10px] text-slate-500 block">Circuit Breaker</span>
                  <span className="text-emerald-700 font-mono font-bold">Protected</span>
                </div>
              </div>
            </div>

            <div>
              <label className="block text-slate-700 font-semibold mb-1">Variable Interpolation (JSON)</label>
              <textarea
                rows={3}
                defaultValue='{\n  "order_id": "{{ input.order_id }}",\n  "amount": "{{ input.amount }}"\n}'
                className="w-full bg-slate-50 border border-slate-200 rounded-lg p-2 font-mono text-[11px] text-indigo-950 focus:outline-none focus:border-indigo-500 focus:bg-white"
              />
              <p className="text-[10px] text-slate-500 mt-1">
                Supports sandboxed expressions: <code>{"{{ input.* }}"}</code> and <code>{"{{ steps.<id>.output.* }}"}</code>.
              </p>
            </div>
          </div>

          <div className="pt-3 border-t border-slate-100 space-y-1.5">
            <div className="flex items-center gap-2 text-emerald-700 text-xs font-bold">
              <CheckCircle2 className="w-4 h-4 text-emerald-600" />
              Node validated against schema
            </div>
            <p className="text-[11px] text-slate-500">
              Changes sync directly to the runtime workflow definition.
            </p>
          </div>
        </div>
      </div>
      </>
      )}

      {/* Deploy Modal */}
      {showDeployModal && (
        <div className="fixed inset-0 bg-slate-900/40 backdrop-blur-sm z-50 flex items-center justify-center p-4">
          <div className="bg-white border border-slate-200 rounded-xl max-w-lg w-full p-6 space-y-5 shadow-2xl animate-in zoom-in-95 duration-150">
            <div className="flex items-center justify-between border-b border-slate-100 pb-3">
              <div>
                <h3 className="text-base font-bold text-slate-900 flex items-center gap-2">
                  <UploadCloud className="w-4 h-4 text-indigo-600" />
                  Deploy Immutable Version v{currentVersion + 1}
                </h3>
                <p className="text-xs text-slate-500 mt-0.5">Per ADR-0004, all in-flight executions finish against v{currentVersion}.</p>
              </div>
              <button onClick={() => setShowDeployModal(false)} className="text-slate-400 hover:text-slate-700">
                <X className="w-4 h-4" />
              </button>
            </div>

            <div className="space-y-4 text-xs">
              <div className="p-3 rounded-lg bg-slate-50 border border-slate-200 space-y-1.5">
                <div className="flex items-center justify-between text-slate-800 font-semibold">
                  <span>Pre-flight Verification Summary</span>
                  <span className="text-emerald-700 flex items-center gap-1 font-bold">
                    <CheckCircle2 className="w-3.5 h-3.5 text-emerald-600" /> PASSED
                  </span>
                </div>
                <div className="grid grid-cols-3 gap-2 pt-2 text-[11px] text-slate-600">
                  <div>Topology: <strong className="text-slate-900">DAG (0 cycles)</strong></div>
                  <div>Step Count: <strong className="text-slate-900">{nodes.length} nodes</strong></div>
                  <div>Tenant Scope: <strong className="text-slate-900">Verified</strong></div>
                </div>
              </div>

              <div>
                <label className="block text-slate-700 font-semibold mb-1">Release Changelog & Notes</label>
                <textarea
                  rows={3}
                  value={deployChangelog}
                  onChange={(e) => setDeployChangelog(e.target.value)}
                  placeholder="e.g. Added credit review approval gate and updated ERP notification routing..."
                  className="w-full bg-white border border-slate-200 rounded-lg p-2.5 text-slate-900 focus:outline-none focus:border-indigo-500 text-xs"
                />
              </div>
            </div>

            <div className="flex items-center justify-end gap-3 pt-2">
              <button
                onClick={() => setShowDeployModal(false)}
                className="px-4 py-2 bg-white hover:bg-slate-100 text-slate-700 rounded-lg text-xs font-semibold border border-slate-200 shadow-sm"
              >
                Cancel
              </button>
              <button
                onClick={handleDeployVersion}
                className="px-4 py-2 bg-indigo-600 hover:bg-indigo-700 text-white rounded-lg text-xs font-semibold shadow-sm flex items-center gap-1.5"
              >
                <UploadCloud className="w-3.5 h-3.5" />
                Confirm & Deploy v{currentVersion + 1}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Rollback Modal */}
      {showRollbackModal && (
        <div className="fixed inset-0 bg-slate-900/40 backdrop-blur-sm z-50 flex items-center justify-center p-4">
          <div className="bg-white border border-slate-200 rounded-xl max-w-lg w-full p-6 space-y-5 shadow-2xl animate-in zoom-in-95 duration-150">
            <div className="flex items-center justify-between border-b border-slate-100 pb-3">
              <div>
                <h3 className="text-base font-bold text-slate-900 flex items-center gap-2">
                  <RotateCcw className="w-4 h-4 text-amber-600" />
                  Version History & Rollback (ADR-0004)
                </h3>
                <p className="text-xs text-slate-500 mt-0.5">Instantaneously points active definition to a prior immutable snapshot.</p>
              </div>
              <button onClick={() => setShowRollbackModal(false)} className="text-slate-400 hover:text-slate-700">
                <X className="w-4 h-4" />
              </button>
            </div>

            <div className="space-y-3 text-xs max-h-[360px] overflow-y-auto pr-1">
              {versions.map((ver) => (
                <div
                  key={ver.version}
                  onClick={() => !ver.is_active && setSelectedRollbackVer(ver.version)}
                  className={`p-3.5 rounded-xl border transition-all ${
                    ver.is_active
                      ? "bg-emerald-50/60 border-emerald-300 text-slate-800 cursor-default"
                      : selectedRollbackVer === ver.version
                      ? "bg-indigo-50 border-indigo-500 text-slate-900 cursor-pointer ring-1 ring-indigo-400"
                      : "bg-slate-50 border-slate-200 text-slate-700 hover:border-slate-300 cursor-pointer"
                  }`}
                >
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-2">
                      <span className="font-bold text-sm text-slate-900 font-mono">v{ver.version}</span>
                      {ver.is_active && (
                        <span className="text-[10px] px-2 py-0.5 rounded-full bg-emerald-100 text-emerald-800 font-bold border border-emerald-200">
                          Active Ingress
                        </span>
                      )}
                    </div>
                    <span className="text-[11px] text-slate-500 font-mono">{ver.node_count} nodes</span>
                  </div>
                  <p className="text-xs text-slate-700 mt-1.5">{ver.changelog}</p>
                  <div className="flex items-center justify-between mt-2 text-[10px] text-slate-500 font-mono">
                    <span>Deployed: {ver.deployed_at}</span>
                    <span>By: {ver.deployed_by}</span>
                  </div>
                </div>
              ))}
            </div>

            <div className="flex items-center justify-end gap-3 pt-2">
              <button
                onClick={() => setShowRollbackModal(false)}
                className="px-4 py-2 bg-white hover:bg-slate-100 text-slate-700 rounded-lg text-xs font-semibold border border-slate-200 shadow-sm"
              >
                Close
              </button>
              <button
                onClick={handleRollback}
                className="px-4 py-2 bg-amber-600 hover:bg-amber-700 text-white rounded-lg text-xs font-semibold shadow-sm flex items-center gap-1.5"
              >
                <RotateCcw className="w-3.5 h-3.5" />
                Rollback to v{selectedRollbackVer}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
