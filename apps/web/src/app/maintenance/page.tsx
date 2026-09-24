"use client";

import Link from "next/link";
import { Wrench, Clock, CheckCircle2, RefreshCw, Mail } from "lucide-react";

export default function MaintenancePage() {
  const handleCheckStatus = () => {
    window.location.reload();
  };

  return (
    <div className="min-h-[75vh] flex flex-col items-center justify-center text-center px-4 py-12">
      <div className="relative mb-6">
        <div className="w-20 h-20 bg-[#FAF8F5] border border-[#D5CABE] rounded-3xl flex items-center justify-center text-[#874436] shadow-sm">
          <Wrench className="w-10 h-10 animate-bounce" />
        </div>
        <span className="absolute -bottom-1 -right-1 px-2 py-0.5 rounded-full bg-[#874436] text-white text-[10px] font-mono font-bold shadow">
          OPS
        </span>
      </div>

      <span className="text-xs font-semibold tracking-widest text-[#968676] uppercase mb-2">
        Scheduled Infrastructure Upgrade
      </span>
      <h1 className="text-3xl sm:text-4xl font-black tracking-tight text-[#1B1B1B] mb-3">
        System Under Maintenance
      </h1>
      <p className="text-sm text-[#5C5C5C] max-w-lg mb-6 leading-relaxed">
        The FlowMesh control plane is undergoing an immutable version migration and state store index optimization. Edge Agent outbound-only buffers continue to queue telemetry locally.
      </p>

      <div className="bg-[#FAF8F5] border border-[#D5CABE] rounded-2xl p-6 max-w-md w-full mb-8 text-left space-y-3.5 shadow-sm">
        <div className="flex items-center justify-between text-xs font-bold text-[#1B1B1B] pb-2 border-b border-[#E3D9CE]">
          <div className="flex items-center gap-2">
            <Clock className="w-4 h-4 text-[#874436]" />
            <span>Estimated Window</span>
          </div>
          <span className="text-[11px] font-mono text-[#874436]">~15 Minutes Remaining</span>
        </div>

        <div className="space-y-2 text-xs">
          <div className="flex items-center justify-between">
            <span className="text-[#5C5C5C]">Edge Agent Local Spool:</span>
            <span className="font-semibold text-emerald-700 flex items-center gap-1">
              <CheckCircle2 className="w-3.5 h-3.5" /> Buffering Safe
            </span>
          </div>
          <div className="flex items-center justify-between">
            <span className="text-[#5C5C5C]">Database Migration:</span>
            <span className="font-semibold text-amber-700">Alembic In-Progress (0.9.4)</span>
          </div>
          <div className="flex items-center justify-between">
            <span className="text-[#5C5C5C]">Data Sovereignty:</span>
            <span className="font-semibold text-emerald-700">100% Preserved</span>
          </div>
        </div>
      </div>

      <div className="flex flex-wrap items-center justify-center gap-3">
        <button
          onClick={handleCheckStatus}
          className="inline-flex items-center gap-2 px-5 py-2.5 text-xs font-semibold text-white bg-[#874436] hover:bg-[#6E3529] rounded-xl transition-all shadow-sm active:scale-[0.98]"
        >
          <RefreshCw className="w-3.5 h-3.5" />
          <span>Check Status & Refresh</span>
        </button>
        <Link
          href="/support"
          className="inline-flex items-center gap-2 px-4 py-2.5 text-xs font-semibold text-[#1B1B1B] bg-[#F0EBE4] hover:bg-[#E5DDD4] rounded-xl border border-[#D5CABE] transition-all"
        >
          <span>Support Status</span>
        </Link>
        <a
          href="mailto:ashutosh4tech@gmail.com?subject=Maintenance%20Status%20Inquiry"
          className="inline-flex items-center gap-2 px-4 py-2.5 text-xs font-medium text-[#5C5C5C] hover:text-[#1B1B1B] transition-colors"
        >
          <Mail className="w-3.5 h-3.5 text-[#874436]" />
          <span>Contact ashutosh4tech@gmail.com</span>
        </a>
      </div>
    </div>
  );
}
