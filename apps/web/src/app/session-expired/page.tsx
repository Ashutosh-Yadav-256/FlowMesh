"use client";

import React, { useState } from "react";
import Link from "next/link";
import { Lock, LogIn, RefreshCw, ShieldAlert, ArrowLeft, Mail } from "lucide-react";

export default function SessionExpiredPage() {
  const [refreshing, setRefreshing] = useState(false);

  const handleRefresh = () => {
    setRefreshing(true);
    setTimeout(() => {
      window.location.href = "/";
    }, 1000);
  };

  return (
    <div className="min-h-[75vh] flex flex-col items-center justify-center text-center px-4 py-12">
      <div className="relative mb-6">
        <div className="w-20 h-20 bg-[#FAF8F5] border border-[#D5CABE] rounded-3xl flex items-center justify-center text-amber-700 shadow-sm">
          <Lock className="w-10 h-10" />
        </div>
        <span className="absolute -bottom-1 -right-1 px-2 py-0.5 rounded-full bg-amber-700 text-white text-[10px] font-mono font-bold shadow">
          AUTH
        </span>
      </div>

      <span className="text-xs font-semibold tracking-widest text-amber-800 uppercase mb-2">
        Security Inactivity Timeout
      </span>
      <h1 className="text-3xl sm:text-4xl font-black tracking-tight text-[#1B1B1B] mb-3">
        Session Has Expired
      </h1>
      <p className="text-sm text-[#5C5C5C] max-w-lg mb-6 leading-relaxed">
        Your authentication bearer token has exceeded its maximum idle lifespan (30 minutes) to prevent unauthorized credential hijacking in accordance with enterprise security compliance.
      </p>

      <div className="bg-[#FAF8F5] border border-[#D5CABE] rounded-2xl p-5 max-w-md w-full mb-8 text-left space-y-3 shadow-sm">
        <div className="flex items-center gap-2 text-xs font-bold text-[#1B1B1B]">
          <ShieldAlert className="w-4 h-4 text-[#874436]" />
          <span>Zero Data Loss Protection</span>
        </div>
        <p className="text-xs text-[#5C5C5C] leading-normal">
          Unsaved changes were serialized into your browser session cache. Renewing your token will seamlessly restore your active workspace context.
        </p>
      </div>

      <div className="flex flex-wrap items-center justify-center gap-3">
        <button
          onClick={handleRefresh}
          disabled={refreshing}
          className="inline-flex items-center gap-2 px-5 py-2.5 text-xs font-semibold text-white bg-[#874436] hover:bg-[#6E3529] rounded-xl transition-all shadow-sm active:scale-[0.98] disabled:opacity-70"
        >
          {refreshing ? (
            <>
              <RefreshCw className="w-3.5 h-3.5 animate-spin" />
              <span>Renewing Session...</span>
            </>
          ) : (
            <>
              <LogIn className="w-3.5 h-3.5" />
              <span>Renew Session & Return to App</span>
            </>
          )}
        </button>

        <Link
          href="/"
          className="inline-flex items-center gap-2 px-4 py-2.5 text-xs font-semibold text-[#1B1B1B] bg-[#F0EBE4] hover:bg-[#E5DDD4] rounded-xl border border-[#D5CABE] transition-all"
        >
          <ArrowLeft className="w-3.5 h-3.5" />
          <span>Public Portal</span>
        </Link>

        <a
          href="mailto:ashutosh4tech@gmail.com?subject=FlowMesh%20Session%20Lockout%20Assistance"
          className="inline-flex items-center gap-2 px-4 py-2.5 text-xs font-medium text-[#5C5C5C] hover:text-[#1B1B1B] transition-colors"
        >
          <Mail className="w-3.5 h-3.5 text-[#874436]" />
          <span>Account Help (ashutosh4tech@gmail.com)</span>
        </a>
      </div>
    </div>
  );
}
