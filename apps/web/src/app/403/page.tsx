"use client";

import Link from "next/link";
import { ShieldX, Home, Key, Mail, Lock } from "lucide-react";

export default function ForbiddenPage() {
  return (
    <div className="min-h-[75vh] flex flex-col items-center justify-center text-center px-4 py-12">
      <div className="relative mb-6">
        <div className="w-20 h-20 bg-[#FAF8F5] border border-[#D5CABE] rounded-3xl flex items-center justify-center text-amber-700 shadow-sm">
          <ShieldX className="w-10 h-10" />
        </div>
        <span className="absolute -bottom-1 -right-1 px-2 py-0.5 rounded-full bg-amber-700 text-white text-[10px] font-mono font-bold shadow">
          403
        </span>
      </div>

      <span className="text-xs font-semibold tracking-widest text-amber-800 uppercase mb-2">
        HTTP 403 · Access Forbidden
      </span>
      <h1 className="text-3xl sm:text-4xl font-black tracking-tight text-[#1B1B1B] mb-3">
        Permission Denied
      </h1>
      <p className="text-sm text-[#5C5C5C] max-w-lg mb-6 leading-relaxed">
        Your current credentials or API role do not possess the required RBAC privileges to view or mutate this resource within the current tenant boundary.
      </p>

      <div className="bg-[#FAF8F5] border border-[#D5CABE] rounded-2xl p-5 max-w-md w-full mb-8 text-left space-y-3 shadow-sm">
        <div className="flex items-center gap-2 text-xs font-bold text-[#1B1B1B]">
          <Lock className="w-4 h-4 text-[#874436]" />
          <span>Security & Governance Enforcement</span>
        </div>
        <p className="text-xs text-[#5C5C5C] leading-normal">
          FlowMesh enforces strict tenant isolation and zero-trust perimeter gates. To access enterprise ledgers or administrative actions, ask your workspace admin to grant the <code className="bg-[#F0EBE4] px-1.5 py-0.5 rounded text-[#874436] font-mono font-semibold">ENTERPRISE_OPERATOR</code> or <code className="bg-[#F0EBE4] px-1.5 py-0.5 rounded text-[#874436] font-mono font-semibold">ADMIN</code> role.
        </p>
      </div>

      <div className="flex flex-wrap items-center justify-center gap-3">
        <Link
          href="/"
          className="inline-flex items-center gap-2 px-5 py-2.5 text-xs font-semibold text-white bg-[#874436] hover:bg-[#6E3529] rounded-xl transition-all shadow-sm active:scale-[0.98]"
        >
          <Home className="w-4 h-4" />
          <span>Back to Overview</span>
        </Link>
        <Link
          href="/organization"
          className="inline-flex items-center gap-2 px-4 py-2.5 text-xs font-semibold text-[#1B1B1B] bg-[#F0EBE4] hover:bg-[#E5DDD4] rounded-xl border border-[#D5CABE] transition-all"
        >
          <Key className="w-4 h-4 text-[#874436]" />
          <span>View Roles & Organization</span>
        </Link>
        <a
          href="mailto:ashutosh4tech@gmail.com?subject=RBAC%20Permission%20Elevation%20Request&body=Please%20grant%20access%20to%20my%20account."
          className="inline-flex items-center gap-2 px-4 py-2.5 text-xs font-medium text-[#5C5C5C] hover:text-[#1B1B1B] transition-colors"
        >
          <Mail className="w-3.5 h-3.5 text-[#874436]" />
          <span>Request Elevation (ashutosh4tech@gmail.com)</span>
        </a>
      </div>
    </div>
  );
}
