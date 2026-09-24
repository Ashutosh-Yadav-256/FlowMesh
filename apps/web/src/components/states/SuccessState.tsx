"use client";

import React from "react";
import { CheckCircle2, ArrowRight, Home, ExternalLink } from "lucide-react";
import Link from "next/link";

interface SuccessStateProps {
  title?: string;
  message?: string;
  transactionId?: string;
  primaryActionLabel?: string;
  primaryActionHref?: string;
  onPrimaryAction?: () => void;
  secondaryActionLabel?: string;
  secondaryActionHref?: string;
  metadata?: Record<string, string | number>;
  className?: string;
}

export function SuccessState({
  title = "Operation Completed Successfully",
  message = "Your workflow execution or configuration has been committed to the distributed state store.",
  transactionId,
  primaryActionLabel = "View Runs",
  primaryActionHref = "/runs",
  onPrimaryAction,
  secondaryActionLabel = "Back to Overview",
  secondaryActionHref = "/",
  metadata,
  className = "",
}: SuccessStateProps) {
  return (
    <div
      className={`min-h-[50vh] flex flex-col items-center justify-center p-8 sm:p-12 text-center rounded-2xl bg-[#FAF8F5] border border-[#D5CABE] shadow-sm ${className}`}
    >
      <div className="w-16 h-16 rounded-2xl bg-emerald-50 border border-emerald-200 flex items-center justify-center text-emerald-600 mb-6 shadow-sm">
        <CheckCircle2 className="w-8 h-8" />
      </div>

      <span className="text-[11px] font-bold tracking-widest text-emerald-700 uppercase mb-1">
        Verified & Committed
      </span>
      <h3 className="text-2xl font-bold text-[#1B1B1B] tracking-tight mb-2">
        {title}
      </h3>
      <p className="text-sm text-[#5C5C5C] max-w-md leading-relaxed mb-6">
        {message}
      </p>

      {transactionId && (
        <div className="bg-[#F4EFEB] border border-[#E3D9CE] rounded-xl px-4 py-2.5 mb-6 flex items-center gap-2">
          <span className="text-[11px] text-[#968676] font-medium">Reference ID:</span>
          <span className="font-mono text-xs font-bold text-[#1B1B1B]">{transactionId}</span>
        </div>
      )}

      {metadata && Object.keys(metadata).length > 0 && (
        <div className="w-full max-w-sm bg-[#F4EFEB] border border-[#E3D9CE] rounded-xl p-4 mb-6 text-left divide-y divide-[#E3D9CE]">
          {Object.entries(metadata).map(([key, val]) => (
            <div key={key} className="py-1.5 flex justify-between items-center text-xs">
              <span className="text-[#968676] capitalize">{key.replace(/_/g, " ")}:</span>
              <span className="font-semibold text-[#1B1B1B]">{String(val)}</span>
            </div>
          ))}
        </div>
      )}

      <div className="flex flex-wrap items-center justify-center gap-3">
        {primaryActionHref ? (
          <Link
            href={primaryActionHref}
            className="inline-flex items-center gap-2 px-5 py-2.5 rounded-xl bg-[#874436] hover:bg-[#6E3529] text-white font-medium text-xs shadow-sm transition-all active:scale-[0.98]"
          >
            <span>{primaryActionLabel}</span>
            <ArrowRight className="w-3.5 h-3.5" />
          </Link>
        ) : onPrimaryAction ? (
          <button
            onClick={onPrimaryAction}
            className="inline-flex items-center gap-2 px-5 py-2.5 rounded-xl bg-[#874436] hover:bg-[#6E3529] text-white font-medium text-xs shadow-sm transition-all active:scale-[0.98]"
          >
            <span>{primaryActionLabel}</span>
            <ArrowRight className="w-3.5 h-3.5" />
          </button>
        ) : null}

        {secondaryActionHref && (
          <Link
            href={secondaryActionHref}
            className="inline-flex items-center gap-2 px-4 py-2.5 rounded-xl bg-[#F0EBE4] hover:bg-[#E5DDD4] text-[#1B1B1B] font-medium text-xs border border-[#D5CABE] transition-all"
          >
            <Home className="w-3.5 h-3.5 text-[#874436]" />
            <span>{secondaryActionLabel}</span>
          </Link>
        )}
      </div>
    </div>
  );
}
