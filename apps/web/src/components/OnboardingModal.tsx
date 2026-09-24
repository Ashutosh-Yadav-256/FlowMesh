"use client";

import React, { useState, useEffect } from "react";
import {
  Sparkles,
  X,
  ArrowRight,
  ArrowLeft,
  CheckCircle2,
  ShieldCheck,
  Cpu,
  Workflow,
  AlertTriangle,
  PlayCircle,
  Database,
  Layers,
  ChevronRight,
  RotateCcw,
  ExternalLink,
  Terminal,
} from "lucide-react";
import { FlowMeshSymbol } from "./FlowMeshLogo";

export type PersonaType = "architect" | "sre" | "developer";

export function OnboardingModal() {
  const [isOpen, setIsOpen] = useState(false);
  const [step, setStep] = useState(0);
  const [persona, setPersona] = useState<PersonaType>("architect");
  const [isTestingConn, setIsTestingConn] = useState(false);
  const [connTested, setConnTested] = useState(false);
  const [isRunningWorkflow, setIsRunningWorkflow] = useState(false);
  const [workflowRunComplete, setWorkflowRunComplete] = useState(false);

  useEffect(() => {
    const hasSeen = localStorage.getItem("flowmesh_onboarding_completed");
    if (!hasSeen) {
      const timer = setTimeout(() => setIsOpen(true), 600);
      return () => clearTimeout(timer);
    }
  }, []);

  useEffect(() => {
    const handleOpen = () => {
      setStep(0);
      setIsOpen(true);
    };
    window.addEventListener("flowmesh:open-onboarding", handleOpen);
    return () => window.removeEventListener("flowmesh:open-onboarding", handleOpen);
  }, []);

  const handleClose = () => {
    localStorage.setItem("flowmesh_onboarding_completed", "true");
    setIsOpen(false);
  };

  const handleSimulateConnection = () => {
    setIsTestingConn(true);
    setTimeout(() => {
      setIsTestingConn(false);
      setConnTested(true);
    }, 800);
  };

  const handleSimulateWorkflow = () => {
    setIsRunningWorkflow(true);
    setTimeout(() => {
      setIsRunningWorkflow(false);
      setWorkflowRunComplete(true);
    }, 1200);
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 sm:p-6 bg-black/50 backdrop-blur-sm animate-in fade-in duration-200">
      <div
        className="w-full max-w-2xl bg-[#FAF8F5] border border-[#D5CABE] rounded-2xl shadow-2xl overflow-hidden flex flex-col max-h-[90vh]"
        role="dialog"
        aria-modal="true"
      >
        {/* Header Bar */}
        <div className="h-14 px-6 border-b border-[#D5CABE] flex items-center justify-between bg-[#F3EFEA]/80">
          <div className="flex items-center gap-2.5">
            <div className="w-7 h-7 rounded-lg bg-[#874436] flex items-center justify-center text-white shadow-xs">
              <FlowMeshSymbol className="w-4 h-4 text-white" />
            </div>
            <span className="text-xs font-bold uppercase tracking-wider text-[#1B1B1B]">
              FlowMesh Onboarding
            </span>
            <span className="text-[10px] font-semibold px-2 py-0.5 rounded-full bg-[#E7E0D6] text-[#6B5E51] border border-[#D5CABE]">
              Step {step + 1} of 4
            </span>
          </div>

          <div className="flex items-center gap-2">
            <button
              onClick={handleClose}
              className="text-xs text-[#968676] hover:text-[#1B1B1B] px-2 py-1 rounded transition-colors"
            >
              Skip Tour
            </button>
            <button
              onClick={handleClose}
              className="w-7 h-7 rounded-lg flex items-center justify-center text-[#968676] hover:text-[#1B1B1B] hover:bg-[#EAE4DC] transition-colors"
            >
              <X className="w-4 h-4" />
            </button>
          </div>
        </div>

        {/* Modal Body */}
        <div className="p-6 sm:p-8 overflow-y-auto flex-1 text-[#1B1B1B]">
          {/* STEP 0: Welcome & Persona Selection */}
          {step === 0 && (
            <div className="space-y-6">
              <div className="space-y-2">
                <div className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full bg-[#F8EBE8] border border-[#EED1CB] text-[11px] font-semibold text-[#874436]">
                  <Sparkles className="w-3.5 h-3.5 text-[#874436]" />
                  <span>Sovereign Enterprise Integration</span>
                </div>
                <h2 className="text-2xl font-bold tracking-tight text-[#1B1B1B]">
                  Welcome to FlowMesh
                </h2>
                <p className="text-sm text-[#4F4F4F] leading-relaxed">
                  FlowMesh provides client-owned, cloud-neutral workflow orchestration with
                  hybrid edge execution, RediForge state persistence, and automated dead-letter safety.
                </p>
              </div>

              <div>
                <label className="text-xs font-bold uppercase tracking-wider text-[#6B5E51] block mb-3">
                  Choose Your Primary Focus:
                </label>
                <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
                  <button
                    type="button"
                    onClick={() => setPersona("architect")}
                    className={`p-4 rounded-xl border text-left transition-all ${
                      persona === "architect"
                        ? "bg-[#FAF8F5] border-[#874436] shadow-sm ring-1 ring-[#874436]"
                        : "bg-[#F3EFEA] border-[#D5CABE] hover:bg-[#EFEAE2]"
                    }`}
                  >
                    <Workflow
                      className={`w-5 h-5 mb-2 ${
                        persona === "architect" ? "text-[#874436]" : "text-[#968676]"
                      }`}
                    />
                    <div className="font-semibold text-xs text-[#1B1B1B]">Integration Architect</div>
                    <p className="text-[11px] text-[#6B5E51] mt-1 leading-snug">
                      Design robust DAGs, connectors, and schema mappings.
                    </p>
                  </button>

                  <button
                    type="button"
                    onClick={() => setPersona("sre")}
                    className={`p-4 rounded-xl border text-left transition-all ${
                      persona === "sre"
                        ? "bg-[#FAF8F5] border-[#874436] shadow-sm ring-1 ring-[#874436]"
                        : "bg-[#F3EFEA] border-[#D5CABE] hover:bg-[#EFEAE2]"
                    }`}
                  >
                    <AlertTriangle
                      className={`w-5 h-5 mb-2 ${
                        persona === "sre" ? "text-[#874436]" : "text-[#968676]"
                      }`}
                    />
                    <div className="font-semibold text-xs text-[#1B1B1B]">Reliability / SRE</div>
                    <p className="text-[11px] text-[#6B5E51] mt-1 leading-snug">
                      DLQ incident recovery, circuit breakers, and zero data loss.
                    </p>
                  </button>

                  <button
                    type="button"
                    onClick={() => setPersona("developer")}
                    className={`p-4 rounded-xl border text-left transition-all ${
                      persona === "developer"
                        ? "bg-[#FAF8F5] border-[#874436] shadow-sm ring-1 ring-[#874436]"
                        : "bg-[#F3EFEA] border-[#D5CABE] hover:bg-[#EFEAE2]"
                    }`}
                  >
                    <Cpu
                      className={`w-5 h-5 mb-2 ${
                        persona === "developer" ? "text-[#874436]" : "text-[#968676]"
                      }`}
                    />
                    <div className="font-semibold text-xs text-[#1B1B1B]">Platform Engineer</div>
                    <p className="text-[11px] text-[#6B5E51] mt-1 leading-snug">
                      Edge agent daemons, OpenAPI specs, and microservices.
                    </p>
                  </button>
                </div>
              </div>

              <div className="p-3.5 rounded-xl bg-[#F0F5F2] border border-[#D1E2D8] flex items-center justify-between text-xs text-[#2E6B47]">
                <div className="flex items-center gap-2">
                  <CheckCircle2 className="w-4 h-4 text-[#2E6B47] shrink-0" />
                  <span>
                    <strong>Acme Global Corp</strong> demo workspace is ready with pre-seeded DAGs & connectors.
                  </span>
                </div>
              </div>
            </div>
          )}

          {/* STEP 1: Connectors & Security Enclave */}
          {step === 1 && (
            <div className="space-y-6">
              <div className="space-y-2">
                <div className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full bg-[#F0F3FA] border border-[#DFE6F5] text-[11px] font-semibold text-[#455CA1]">
                  <Database className="w-3.5 h-3.5 text-[#455CA1]" />
                  <span>Sovereign Enclave Security</span>
                </div>
                <h3 className="text-xl font-bold tracking-tight text-[#1B1B1B]">
                  Connect External Systems Safely
                </h3>
                <p className="text-xs text-[#4F4F4F] leading-relaxed">
                  Connections decouple authentication from workflow logic. Secrets are encrypted using
                  envelope AES-256-GCM and never leave your private deployment enclave.
                </p>
              </div>

              {/* Interactive Connector Simulation */}
              <div className="p-4 rounded-xl border border-[#D5CABE] bg-[#F3EFEA] space-y-3">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-3">
                    <div className="w-9 h-9 rounded-lg bg-[#FAF8F5] border border-[#D5CABE] flex items-center justify-center text-[#874436] font-bold text-xs">
                      PG
                    </div>
                    <div>
                      <div className="text-xs font-bold text-[#1B1B1B]">Acme Core Warehouse</div>
                      <div className="text-[10px] text-[#968676] font-mono">postgresql+asyncpg://internal-db:5432</div>
                    </div>
                  </div>

                  <span
                    className={`text-[10px] font-semibold px-2 py-0.5 rounded-full border ${
                      connTested
                        ? "bg-[#F0F5F2] text-[#2E6B47] border-[#D1E2D8]"
                        : "bg-[#E7E0D6] text-[#6B5E51] border-[#D5CABE]"
                    }`}
                  >
                    {connTested ? "Verified · 4.2ms" : "Unverified"}
                  </span>
                </div>

                <div className="flex items-center justify-between pt-2 border-t border-[#D5CABE]/60">
                  <span className="text-[11px] text-[#6B5E51]">
                    {connTested
                      ? "Round-trip handshake verified. Enclave keys bound to tenant."
                      : "Click below to execute an authenticated sandbox handshake:"}
                  </span>
                  <button
                    onClick={handleSimulateConnection}
                    disabled={isTestingConn || connTested}
                    className="px-3 py-1.5 rounded-lg bg-[#FAF8F5] hover:bg-white border border-[#D5CABE] text-xs font-semibold text-[#1B1B1B] shadow-xs transition-all disabled:opacity-60"
                  >
                    {isTestingConn ? "Handshaking..." : connTested ? "Connected ✓" : "Test Connection"}
                  </button>
                </div>
              </div>
            </div>
          )}

          {/* STEP 2: Declarative DAG Workflows */}
          {step === 2 && (
            <div className="space-y-6">
              <div className="space-y-2">
                <div className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full bg-[#F8EBE8] border border-[#EED1CB] text-[11px] font-semibold text-[#874436]">
                  <Workflow className="w-3.5 h-3.5 text-[#874436]" />
                  <span>Deterministic Execution Engine</span>
                </div>
                <h3 className="text-xl font-bold tracking-tight text-[#1B1B1B]">
                  Visual DAGs with RediForge State
                </h3>
                <p className="text-xs text-[#4F4F4F] leading-relaxed">
                  Every workflow is compiled into an execution graph. Step transitions, circuit breakers,
                  and retry policies guarantee that state is never corrupted or duplicated.
                </p>
              </div>

              {/* Interactive Workflow Simulation */}
              <div className="p-4 rounded-xl border border-[#D5CABE] bg-[#F3EFEA] space-y-4">
                <div className="flex items-center justify-between">
                  <span className="text-xs font-bold text-[#1B1B1B]">order-fulfillment-pipeline</span>
                  <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-[#FAF8F5] border border-[#D5CABE] text-[#4F4F4F]">
                    DAG · 3 Steps
                  </span>
                </div>

                <div className="grid grid-cols-3 gap-2 text-center text-[10px]">
                  <div
                    className={`p-2.5 rounded-lg border transition-colors ${
                      isRunningWorkflow || workflowRunComplete
                        ? "bg-[#F0F5F2] border-[#D1E2D8] text-[#2E6B47] font-semibold"
                        : "bg-[#FAF8F5] border-[#D5CABE] text-[#4F4F4F]"
                    }`}
                  >
                    1. Ingest Payload
                  </div>
                  <div
                    className={`p-2.5 rounded-lg border transition-colors ${
                      workflowRunComplete
                        ? "bg-[#F0F5F2] border-[#D1E2D8] text-[#2E6B47] font-semibold"
                        : isRunningWorkflow
                        ? "bg-[#FEF7ED] border-[#FDEED3] text-[#E17709] animate-pulse"
                        : "bg-[#FAF8F5] border-[#D5CABE] text-[#4F4F4F]"
                    }`}
                  >
                    2. Schema Validate
                  </div>
                  <div
                    className={`p-2.5 rounded-lg border transition-colors ${
                      workflowRunComplete
                        ? "bg-[#F0F5F2] border-[#D1E2D8] text-[#2E6B47] font-semibold"
                        : "bg-[#FAF8F5] border-[#D5CABE] text-[#4F4F4F]"
                    }`}
                  >
                    3. Commit State
                  </div>
                </div>

                <div className="flex items-center justify-between pt-2 border-t border-[#D5CABE]/60">
                  <span className="text-[11px] text-[#6B5E51]">
                    {workflowRunComplete
                      ? "Execution trace recorded: run_sandbox_01 (18ms elapsed)"
                      : "Trigger a test execution to watch state store transitions:"}
                  </span>
                  <button
                    onClick={handleSimulateWorkflow}
                    disabled={isRunningWorkflow || workflowRunComplete}
                    className="px-3 py-1.5 rounded-lg bg-[#874436] hover:bg-[#6E362A] text-white text-xs font-semibold shadow-xs transition-all disabled:opacity-60 flex items-center gap-1.5"
                  >
                    <PlayCircle className="w-3.5 h-3.5" />
                    {isRunningWorkflow ? "Executing..." : workflowRunComplete ? "Run Succeeded ✓" : "Run Workflow"}
                  </button>
                </div>
              </div>
            </div>
          )}

          {/* STEP 3: Zero-Data-Loss DLQ & Next Steps */}
          {step === 3 && (
            <div className="space-y-6">
              <div className="space-y-2">
                <div className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full bg-[#F0F5F2] border border-[#D1E2D8] text-[11px] font-semibold text-[#2E6B47]">
                  <CheckCircle2 className="w-3.5 h-3.5 text-[#2E6B47]" />
                  <span>Ready for Exploration</span>
                </div>
                <h3 className="text-xl font-bold tracking-tight text-[#1B1B1B]">
                  You&apos;re All Set to Build
                </h3>
                <p className="text-xs text-[#4F4F4F] leading-relaxed">
                  Your sandbox is fully primed. You can test circuit breakers in the Dead-Letter Queue (DLQ),
                  deploy edge daemons, or search any entity using <kbd className="px-1.5 py-0.5 rounded bg-[#E7E0D6] border border-[#D5CABE] text-[10px] font-mono">⌘K</kbd>.
                </p>
              </div>

              <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                <div className="p-3.5 rounded-xl bg-[#FAF8F5] border border-[#D5CABE] space-y-1.5">
                  <div className="text-xs font-bold text-[#1B1B1B] flex items-center gap-1.5">
                    <AlertTriangle className="w-3.5 h-3.5 text-[#874436]" />
                    Dead-Letter Queue (DLQ)
                  </div>
                  <p className="text-[11px] text-[#6B5E51] leading-relaxed">
                    Failed webhook events are isolated with full stack traces. Edit and replay payloads with 1-click.
                  </p>
                </div>

                <div className="p-3.5 rounded-xl bg-[#FAF8F5] border border-[#D5CABE] space-y-1.5">
                  <div className="text-xs font-bold text-[#1B1B1B] flex items-center gap-1.5">
                    <Terminal className="w-3.5 h-3.5 text-[#455CA1]" />
                    REST API & Swagger
                  </div>
                  <p className="text-[11px] text-[#6B5E51] leading-relaxed">
                    Full programmatic control. Access OpenAPI documentation at <code>/docs</code> directly from the header.
                  </p>
                </div>
              </div>

              <div className="p-3 rounded-lg bg-[#FEF7ED] border border-[#FDEED3] text-xs text-[#C66506] flex items-center gap-2">
                <RotateCcw className="w-4 h-4 shrink-0" />
                <span>
                  Tip: You can re-open this tour anytime or reset demo data from the sidebar workspace switcher.
                </span>
              </div>
            </div>
          )}
        </div>

        {/* Footer Navigation Controls */}
        <div className="h-16 px-6 border-t border-[#D5CABE] bg-[#F3EFEA]/80 flex items-center justify-between">
          <div>
            {step > 0 && (
              <button
                onClick={() => setStep((prev) => prev - 1)}
                className="px-3.5 py-2 rounded-lg border border-[#D5CABE] hover:bg-[#FAF8F5] text-xs font-semibold text-[#1B1B1B] flex items-center gap-1.5 transition-colors"
              >
                <ArrowLeft className="w-3.5 h-3.5" />
                Back
              </button>
            )}
          </div>

          <div className="flex items-center gap-2">
            {step < 3 ? (
              <button
                onClick={() => setStep((prev) => prev + 1)}
                className="px-4 py-2 rounded-lg bg-[#874436] hover:bg-[#6E362A] text-white text-xs font-semibold shadow-xs flex items-center gap-1.5 transition-colors"
              >
                Continue
                <ArrowRight className="w-3.5 h-3.5" />
              </button>
            ) : (
              <button
                onClick={handleClose}
                className="px-5 py-2 rounded-lg bg-[#874436] hover:bg-[#6E362A] text-white text-xs font-semibold shadow-xs flex items-center gap-1.5 transition-colors"
              >
                Go to Dashboard
                <CheckCircle2 className="w-3.5 h-3.5" />
              </button>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
