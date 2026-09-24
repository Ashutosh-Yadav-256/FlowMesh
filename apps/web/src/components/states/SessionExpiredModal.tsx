"use client";

import React, { useState } from "react";
import { Lock, LogIn, RefreshCw, ShieldAlert } from "lucide-react";

interface SessionExpiredModalProps {
  isOpen?: boolean;
  onRefreshSession?: () => void;
  onLogout?: () => void;
  emailContact?: string;
}

export function SessionExpiredModal({
  isOpen = true,
  onRefreshSession,
  onLogout,
  emailContact = "ashutosh4tech@gmail.com",
}: SessionExpiredModalProps) {
  const [refreshing, setRefreshing] = useState(false);

  if (!isOpen) return null;

  const handleRefresh = async () => {
    setRefreshing(true);
    if (onRefreshSession) {
      await onRefreshSession();
    } else {
      setTimeout(() => {
        window.location.reload();
      }, 1000);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/60 backdrop-blur-sm animate-fade-in">
      <div className="relative w-full max-w-md p-6 sm:p-8 rounded-2xl bg-[#FAF8F5] border border-[#D5CABE] shadow-2xl text-center">
        <div className="w-14 h-14 rounded-2xl bg-amber-50 border border-amber-200 flex items-center justify-center text-amber-700 mx-auto mb-5 shadow-sm">
          <Lock className="w-7 h-7" />
        </div>

        <span className="text-[11px] font-bold tracking-widest text-amber-800 uppercase mb-1">
          Security Timeout
        </span>
        <h3 className="text-xl font-bold text-[#1B1B1B] tracking-tight mb-2">
          Your Session Has Expired
        </h3>
        <p className="text-sm text-[#5C5C5C] leading-relaxed mb-6">
          For data security and tenant isolation compliance, your authentication token has timed out due to inactivity.
        </p>

        <div className="bg-[#F4EFEB] border border-[#E3D9CE] rounded-xl p-3 mb-6 text-xs text-[#5C5C5C] text-left flex items-start gap-2.5">
          <ShieldAlert className="w-4 h-4 text-[#874436] shrink-0 mt-0.5" />
          <span>
            Any unsaved visual workflow modifications are stored in local scratch buffer. If your account is locked, contact{" "}
            <a href={`mailto:${emailContact}`} className="font-semibold text-[#874436] underline">
              {emailContact}
            </a>.
          </span>
        </div>

        <div className="space-y-2.5">
          <button
            onClick={handleRefresh}
            disabled={refreshing}
            className="w-full inline-flex items-center justify-center gap-2 px-5 py-2.5 rounded-xl bg-[#874436] hover:bg-[#6E3529] text-white font-semibold text-xs shadow-sm transition-all active:scale-[0.98] disabled:opacity-70"
          >
            {refreshing ? (
              <>
                <RefreshCw className="w-3.5 h-3.5 animate-spin" />
                <span>Renewing Token...</span>
              </>
            ) : (
              <>
                <LogIn className="w-3.5 h-3.5" />
                <span>Re-Authenticate & Refresh</span>
              </>
            )}
          </button>

          <button
            onClick={onLogout || (() => (window.location.href = "/"))}
            className="w-full px-4 py-2 rounded-xl bg-transparent hover:bg-[#F0EBE4] text-[#5C5C5C] hover:text-[#1B1B1B] font-medium text-xs transition-colors"
          >
            Return to Public Overview
          </button>
        </div>
      </div>
    </div>
  );
}
