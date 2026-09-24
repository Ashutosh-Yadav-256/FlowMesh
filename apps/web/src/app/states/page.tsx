"use client";

import React, { useState } from "react";
import Link from "next/link";
import {
  Layers,
  Search,
  ShieldX,
  AlertOctagon,
  Wrench,
  WifiOff,
  FolderPlus,
  SearchX,
  Loader2,
  AlertTriangle,
  CheckCircle2,
  Lock,
  ArrowRight,
  ExternalLink,
} from "lucide-react";

import { EmptyState } from "@/components/states/EmptyState";
import { NoSearchResults } from "@/components/states/NoSearchResults";
import { LoadingState } from "@/components/states/LoadingState";
import { ErrorState } from "@/components/states/ErrorState";
import { SuccessState } from "@/components/states/SuccessState";
import { SessionExpiredModal } from "@/components/states/SessionExpiredModal";

type StateKey =
  | "404"
  | "403"
  | "500"
  | "maintenance"
  | "offline"
  | "empty"
  | "no-results"
  | "loading"
  | "error"
  | "success"
  | "session-expired";

const statesList: { key: StateKey; label: string; icon: React.ElementType; badge: string; directRoute?: string }[] = [
  { key: "404", label: "404 Not Found", icon: Search, badge: "HTTP", directRoute: "/404" },
  { key: "403", label: "403 Forbidden", icon: ShieldX, badge: "Security", directRoute: "/403" },
  { key: "500", label: "500 Server Error", icon: AlertOctagon, badge: "System", directRoute: "/500" },
  { key: "maintenance", label: "Maintenance Mode", icon: Wrench, badge: "Ops", directRoute: "/maintenance" },
  { key: "offline", label: "Offline Mode", icon: WifiOff, badge: "Network", directRoute: "/offline" },
  { key: "empty", label: "Empty State", icon: FolderPlus, badge: "Data" },
  { key: "no-results", label: "No Search Results", icon: SearchX, badge: "Filter" },
  { key: "loading", label: "Loading State", icon: Loader2, badge: "Async" },
  { key: "error", label: "Error State", icon: AlertTriangle, badge: "Fault" },
  { key: "success", label: "Success State", icon: CheckCircle2, badge: "Committed" },
  { key: "session-expired", label: "Session Expired", icon: Lock, badge: "Auth", directRoute: "/session-expired" },
];

export default function StatesShowcasePage() {
  const [activeState, setActiveState] = useState<StateKey>("empty");
  const [loadingVariant, setLoadingVariant] = useState<"spinner" | "skeleton-grid" | "table">("spinner");
  const [errorInline, setErrorInline] = useState(false);
  const [showSessionModal, setShowSessionModal] = useState(false);

  return (
    <div className="space-y-8 max-w-6xl mx-auto pb-16">
      {}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 pb-6 border-b border-[#D5CABE]">
        <div>
          <div className="flex items-center gap-2 text-xs font-semibold text-[#874436] uppercase tracking-wider mb-1">
            <Layers className="w-4 h-4" />
            <span>Design System & Resilience</span>
          </div>
          <h1 className="text-3xl font-black text-[#1B1B1B] tracking-tight">
            UX States & System Resilience Gallery
          </h1>
          <p className="text-sm text-[#5C5C5C] mt-1 max-w-2xl">
            Interactive preview of all 11 enterprise user experience states, system fallbacks, and boundary error views across the FlowMesh platform.
          </p>
        </div>

        <div className="flex items-center gap-2">
          <span className="text-xs text-[#968676]">Primary Contact:</span>
          <a
            href="mailto:ashutosh4tech@gmail.com"
            className="text-xs font-mono font-semibold text-[#874436] bg-[#F4EFEB] px-2.5 py-1 rounded-lg border border-[#E3D9CE] hover:underline"
          >
            ashutosh4tech@gmail.com
          </a>
        </div>
      </div>

      {}
      <div className="bg-[#FAF8F5] border border-[#D5CABE] rounded-2xl p-2.5 shadow-sm">
        <div className="flex items-center gap-1.5 overflow-x-auto pb-1 scrollbar-thin">
          {statesList.map((item) => {
            const Icon = item.icon;
            const isSelected = activeState === item.key;
            return (
              <button
                key={item.key}
                onClick={() => {
                  setActiveState(item.key);
                  if (item.key === "session-expired") {
                    setShowSessionModal(true);
                  }
                }}
                className={`flex items-center gap-2 px-3.5 py-2 rounded-xl text-xs font-medium whitespace-nowrap transition-all ${
                  isSelected
                    ? "bg-[#874436] text-white font-semibold shadow-sm"
                    : "text-[#5C5C5C] hover:text-[#1B1B1B] hover:bg-[#F0EBE4]"
                }`}
              >
                <Icon className={`w-3.5 h-3.5 ${isSelected ? "text-white" : "text-[#968676]"}`} />
                <span>{item.label}</span>
                <span
                  className={`text-[9px] font-bold px-1.5 py-0.2 rounded-full uppercase ${
                    isSelected ? "bg-white/20 text-white" : "bg-[#EAE2D8] text-[#7A6C5D]"
                  }`}
                >
                  {item.badge}
                </span>
              </button>
            );
          })}
        </div>
      </div>

      {}
      <div className="relative">
        {}
        {statesList.find((s) => s.key === activeState)?.directRoute && (
          <div className="mb-4 flex items-center justify-between p-3 rounded-xl bg-[#F4EFEB] border border-[#E3D9CE] text-xs">
            <span className="text-[#5C5C5C]">
              This state also exists as a dedicated direct route at:{" "}
              <code className="font-mono font-bold text-[#874436]">
                {statesList.find((s) => s.key === activeState)?.directRoute}
              </code>
            </span>
            <Link
              href={statesList.find((s) => s.key === activeState)!.directRoute!}
              target="_blank"
              className="inline-flex items-center gap-1 text-[#874436] hover:underline font-semibold"
            >
              <span>Open Standalone</span>
              <ExternalLink className="w-3.5 h-3.5" />
            </Link>
          </div>
        )}

        {}
        <div className="transition-all duration-200">
          {activeState === "empty" && (
            <EmptyState
              title="No Active Workflows Configured"
              description="You have not created any DAG orchestration flows in this tenant workspace yet. Create your first automated enterprise workflow or import a pre-built template."
              actionLabel="Create New Workflow"
              actionHref="/workflows"
              secondaryActionLabel="Browse Template Library"
              secondaryActionHref="/workflows"
            />
          )}

          {activeState === "no-results" && (
            <NoSearchResults
              query="sap_hana_reconciliation"
              onClearFilters={() => alert("Filters reset!")}
              suggestions={[
                "Verify tenant scope in the active workspace switcher",
                "Ensure connector name is spelled correctly (e.g. sap_erp)",
                "Try searching by transaction reference or trace ID",
              ]}
              helpHref="/help"
            />
          )}

          {activeState === "loading" && (
            <div className="space-y-4">
              <div className="flex items-center justify-center gap-2 p-2 bg-[#F4EFEB] border border-[#E3D9CE] rounded-xl max-w-sm mx-auto mb-4">
                <span className="text-xs font-semibold text-[#5C5C5C]">Variant:</span>
                {(["spinner", "skeleton-grid", "table"] as const).map((v) => (
                  <button
                    key={v}
                    onClick={() => setLoadingVariant(v)}
                    className={`px-2.5 py-1 rounded-lg text-xs font-medium capitalize transition-all ${
                      loadingVariant === v ? "bg-[#874436] text-white" : "text-[#5C5C5C] hover:bg-[#EAE2D8]"
                    }`}
                  >
                    {v.replace("-", " ")}
                  </button>
                ))}
              </div>
              <LoadingState variant={loadingVariant} />
            </div>
          )}

          {activeState === "error" && (
            <div className="space-y-4">
              <div className="flex items-center justify-center gap-2 mb-2">
                <button
                  onClick={() => setErrorInline(!errorInline)}
                  className="text-xs font-medium px-3 py-1.5 rounded-lg bg-[#F0EBE4] border border-[#D5CABE] text-[#1B1B1B]"
                >
                  Toggle Variant: {errorInline ? "Inline Banner" : "Full Page Card"}
                </button>
              </div>
              <ErrorState
                inline={errorInline}
                title="Distributed Transaction Deadlock Detected"
                errorCode="ERR_TXN_DEADLOCK_409"
                message="Two parallel worker tasks attempted to acquire lock stripe partition #28 simultaneously. Circuit breaker interrupted execution to preserve ledger parity."
                technicalDetails="io.flowmesh.enterprise.concurrency.LockContentionException: Stripe #28 locked by thread flowmesh-recon-14
  at io.flowmesh.enterprise.concurrency.TenantConcurrencyStripingManager.executeInTenantStripe
  at io.flowmesh.enterprise.service.TransactionProcessingService.processTransaction
  at io.flowmesh.enterprise.controller.EnterpriseTransactionController.recordTransaction"
                onRetry={() => alert("Retrying transaction processing...")}
                supportEmail="ashutosh4tech@gmail.com"
              />
            </div>
          )}

          {activeState === "success" && (
            <SuccessState
              title="Enterprise Batch Reconciliation Committed"
              message="150 transactions successfully verified across Oracle ERP and Stripe ledger. Zero discrepancy detected."
              transactionId="BATCH-RECON-874291-SUCCESS"
              primaryActionLabel="Inspect Runs"
              primaryActionHref="/runs"
              secondaryActionLabel="Return to Overview"
              secondaryActionHref="/"
              metadata={{
                total_transactions: 150,
                matched_parity: "100%",
                execution_duration: "182ms",
                audit_trace: "SEC-LOG-99214",
              }}
            />
          )}

          {activeState === "404" && (
            <div className="p-4 rounded-2xl bg-[#FAF8F5] border border-[#D5CABE]">
              <iframe src="/404" className="w-full h-[520px] rounded-xl border border-[#E3D9CE]" />
            </div>
          )}

          {activeState === "403" && (
            <div className="p-4 rounded-2xl bg-[#FAF8F5] border border-[#D5CABE]">
              <iframe src="/403" className="w-full h-[520px] rounded-xl border border-[#E3D9CE]" />
            </div>
          )}

          {activeState === "500" && (
            <div className="p-4 rounded-2xl bg-[#FAF8F5] border border-[#D5CABE]">
              <iframe src="/server-error" className="w-full h-[520px] rounded-xl border border-[#E3D9CE]" />
            </div>
          )}

          {activeState === "maintenance" && (
            <div className="p-4 rounded-2xl bg-[#FAF8F5] border border-[#D5CABE]">
              <iframe src="/maintenance" className="w-full h-[520px] rounded-xl border border-[#E3D9CE]" />
            </div>
          )}

          {activeState === "offline" && (
            <div className="p-4 rounded-2xl bg-[#FAF8F5] border border-[#D5CABE]">
              <iframe src="/offline" className="w-full h-[520px] rounded-xl border border-[#E3D9CE]" />
            </div>
          )}

          {activeState === "session-expired" && (
            <div className="p-8 text-center rounded-2xl bg-[#FAF8F5] border border-[#D5CABE]">
              <h3 className="text-xl font-bold mb-2">Session Expired Modal Triggered</h3>
              <p className="text-sm text-[#5C5C5C] mb-4">
                Click below to preview the modal prompt or view the dedicated route.
              </p>
              <div className="flex items-center justify-center gap-3">
                <button
                  onClick={() => setShowSessionModal(true)}
                  className="px-4 py-2 rounded-xl bg-[#874436] text-white text-xs font-semibold shadow"
                >
                  Open Session Expired Modal
                </button>
                <Link
                  href="/session-expired"
                  className="px-4 py-2 rounded-xl bg-[#F0EBE4] border border-[#D5CABE] text-[#1B1B1B] text-xs font-medium"
                >
                  Open /session-expired Route
                </Link>
              </div>

              <SessionExpiredModal
                isOpen={showSessionModal}
                onRefreshSession={() => {
                  setShowSessionModal(false);
                  alert("Session renewed!");
                }}
                onLogout={() => setShowSessionModal(false)}
                emailContact="ashutosh4tech@gmail.com"
              />
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
