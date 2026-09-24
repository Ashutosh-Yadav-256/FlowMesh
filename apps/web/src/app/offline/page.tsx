"use client";

import React, { useState, useEffect } from "react";
import Link from "next/link";
import { WifiOff, RefreshCw, Home, CheckCircle2, ShieldCheck, Mail } from "lucide-react";

export default function OfflinePage() {
  const [isOnline, setIsOnline] = useState(false);
  const [checking, setChecking] = useState(false);

  useEffect(() => {
    setIsOnline(navigator.onLine);

    const handleOnline = () => setIsOnline(true);
    const handleOffline = () => setIsOnline(false);

    window.addEventListener("online", handleOnline);
    window.addEventListener("offline", handleOffline);

    return () => {
      window.removeEventListener("online", handleOnline);
      window.removeEventListener("offline", handleOffline);
    };
  }, []);

  const handleTestConnection = () => {
    setChecking(true);
    setTimeout(() => {
      setIsOnline(navigator.onLine);
      setChecking(false);
      if (navigator.onLine) {
        window.location.href = "/";
      }
    }, 1200);
  };

  return (
    <div className="min-h-[75vh] flex flex-col items-center justify-center text-center px-4 py-12">
      <div className="relative mb-6">
        <div className={`w-20 h-20 bg-[#FAF8F5] border border-[#D5CABE] rounded-3xl flex items-center justify-center shadow-sm ${isOnline ? "text-emerald-600" : "text-[#874436]"}`}>
          {isOnline ? <CheckCircle2 className="w-10 h-10" /> : <WifiOff className="w-10 h-10" />}
        </div>
        <span className={`absolute -bottom-1 -right-1 px-2 py-0.5 rounded-full text-white text-[10px] font-mono font-bold shadow ${isOnline ? "bg-emerald-600" : "bg-[#874436]"}`}>
          {isOnline ? "ONLINE" : "OFFLINE"}
        </span>
      </div>

      <span className="text-xs font-semibold tracking-widest text-[#968676] uppercase mb-2">
        Network Connectivity Status
      </span>
      <h1 className="text-3xl sm:text-4xl font-black tracking-tight text-[#1B1B1B] mb-3">
        {isOnline ? "Connection Restored" : "You are Currently Offline"}
      </h1>
      <p className="text-sm text-[#5C5C5C] max-w-lg mb-6 leading-relaxed">
        {isOnline
          ? "Your network link has re-established connectivity with the FlowMesh gateway."
          : "Your browser cannot communicate with the local or cloud FlowMesh control plane. Outbound edge agents continue to buffer telemetry locally."}
      </p>

      <div className="bg-[#FAF8F5] border border-[#D5CABE] rounded-2xl p-5 max-w-md w-full mb-8 text-left space-y-2.5 shadow-sm">
        <div className="flex items-center gap-2 text-xs font-bold text-[#1B1B1B]">
          <ShieldCheck className="w-4 h-4 text-[#874436]" />
          <span>Local Cache & Edge Guarantee</span>
        </div>
        <p className="text-xs text-[#5C5C5C] leading-normal">
          FlowMesh is built with offline-first resilience. Workflow executions scheduled on Edge Agents execute autonomously without requiring an active dashboard connection.
        </p>
      </div>

      <div className="flex flex-wrap items-center justify-center gap-3">
        <button
          onClick={handleTestConnection}
          disabled={checking}
          className="inline-flex items-center gap-2 px-5 py-2.5 text-xs font-semibold text-white bg-[#874436] hover:bg-[#6E3529] rounded-xl transition-all shadow-sm active:scale-[0.98] disabled:opacity-70"
        >
          <RefreshCw className={`w-3.5 h-3.5 ${checking ? "animate-spin" : ""}`} />
          <span>{checking ? "Checking Link..." : "Test Connection & Resume"}</span>
        </button>

        <Link
          href="/"
          className="inline-flex items-center gap-2 px-4 py-2.5 text-xs font-semibold text-[#1B1B1B] bg-[#F0EBE4] hover:bg-[#E5DDD4] rounded-xl border border-[#D5CABE] transition-all"
        >
          <Home className="w-4 h-4 text-[#874436]" />
          <span>Dashboard Overview</span>
        </Link>

        <a
          href="mailto:ashutosh4tech@gmail.com?subject=FlowMesh%20Network%20Connectivity%20Issue"
          className="inline-flex items-center gap-2 px-4 py-2.5 text-xs font-medium text-[#5C5C5C] hover:text-[#1B1B1B] transition-colors"
        >
          <Mail className="w-3.5 h-3.5 text-[#874436]" />
          <span>Support (ashutosh4tech@gmail.com)</span>
        </a>
      </div>
    </div>
  );
}
