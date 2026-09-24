"use client";

import Link from "next/link";
import { AlertOctagon, RotateCcw, Home, Mail, Activity } from "lucide-react";

export default function ServerErrorPage() {
  const handleReload = () => {
    window.location.reload();
  };

  return (
    <div className="min-h-[75vh] flex flex-col items-center justify-center text-center px-4 py-12">
      <div className="relative mb-6">
        <div className="w-20 h-20 bg-[#FAF8F5] border border-[#D5CABE] rounded-3xl flex items-center justify-center text-rose-600 shadow-sm">
          <AlertOctagon className="w-10 h-10" />
        </div>
        <span className="absolute -bottom-1 -right-1 px-2 py-0.5 rounded-full bg-rose-600 text-white text-[10px] font-mono font-bold shadow">
          500
        </span>
      </div>

      <span className="text-xs font-semibold tracking-widest text-rose-700 uppercase mb-2">
        HTTP 500 · Internal Service Error
      </span>
      <h1 className="text-3xl sm:text-4xl font-black tracking-tight text-[#1B1B1B] mb-3">
        Unexpected Server Fault
      </h1>
      <p className="text-sm text-[#5C5C5C] max-w-lg mb-6 leading-relaxed">
        The distributed workflow orchestrator or an upstream connector returned an unhandled fault. Automatic retry policies and Dead Letter Queues (DLQ) have captured the event context.
      </p>

      <div className="bg-[#FAF8F5] border border-[#D5CABE] rounded-2xl p-5 max-w-md w-full mb-8 text-left space-y-3 shadow-sm">
        <div className="flex items-center justify-between text-xs font-bold text-[#1B1B1B]">
          <div className="flex items-center gap-2">
            <Activity className="w-4 h-4 text-[#874436]" />
            <span>Telemetry & Incident Logging</span>
          </div>
          <span className="text-[10px] font-mono text-emerald-600 bg-emerald-50 px-2 py-0.5 rounded border border-emerald-200">
            AUTO-DISPATCHED
          </span>
        </div>
        <p className="text-xs text-[#5C5C5C] leading-normal font-mono text-[11px] bg-[#F4EFEB] p-3 rounded-lg border border-[#E3D9CE]">
          TRACE_ID: 9f82d1c3a84b4ef0874e0192a<br />
          STATESTORE: REDIFORGE_CONNECTED<br />
          CIRCUIT_BREAKER: HALF_OPEN
        </p>
      </div>

      <div className="flex flex-wrap items-center justify-center gap-3">
        <button
          onClick={handleReload}
          className="inline-flex items-center gap-2 px-5 py-2.5 text-xs font-semibold text-white bg-[#874436] hover:bg-[#6E3529] rounded-xl transition-all shadow-sm active:scale-[0.98]"
        >
          <RotateCcw className="w-4 h-4" />
          <span>Reload & Retry</span>
        </button>
        <Link
          href="/"
          className="inline-flex items-center gap-2 px-4 py-2.5 text-xs font-semibold text-[#1B1B1B] bg-[#F0EBE4] hover:bg-[#E5DDD4] rounded-xl border border-[#D5CABE] transition-all"
        >
          <Home className="w-4 h-4 text-[#874436]" />
          <span>Return Home</span>
        </Link>
        <a
          href="mailto:ashutosh4tech@gmail.com?subject=FlowMesh%20500%20Server%20Error%20Report&body=Trace%20ID:%209f82d1c3a84b4ef0874e0192a"
          className="inline-flex items-center gap-2 px-4 py-2.5 text-xs font-medium text-[#5C5C5C] hover:text-[#1B1B1B] transition-colors"
        >
          <Mail className="w-3.5 h-3.5 text-[#874436]" />
          <span>Escalate to ashutosh4tech@gmail.com</span>
        </a>
      </div>
    </div>
  );
}
