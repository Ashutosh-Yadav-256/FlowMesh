"use client";

import React, { useState } from "react";
import { AlertTriangle, RotateCcw, Mail, ChevronDown, ChevronUp, Copy, Check } from "lucide-react";
import Link from "next/link";

interface ErrorStateProps {
  title?: string;
  message?: string;
  errorCode?: string;
  technicalDetails?: string;
  onRetry?: () => void;
  supportEmail?: string;
  inline?: boolean;
  className?: string;
}

export function ErrorState({
  title = "System Operation Encountered an Error",
  message = "An unexpected error occurred while executing the transaction or reading from the state store.",
  errorCode = "ERR_FLOWMESH_500",
  technicalDetails,
  onRetry,
  supportEmail = "ashutosh4tech@gmail.com",
  inline = false,
  className = "",
}: ErrorStateProps) {
  const [showDetails, setShowDetails] = useState(false);
  const [copied, setCopied] = useState(false);

  const handleCopy = () => {
    if (technicalDetails) {
      navigator.clipboard.writeText(`Error: ${errorCode}\n${technicalDetails}`);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    }
  };

  if (inline) {
    return (
      <div className={`p-4 rounded-xl bg-[#FDF6F5] border border-[#F5C6CB] text-[#721C24] ${className}`}>
        <div className="flex items-start gap-3">
          <AlertTriangle className="w-5 h-5 text-[#874436] shrink-0 mt-0.5" />
          <div className="flex-1">
            <h4 className="text-xs font-bold text-[#874436] tracking-tight">{title}</h4>
            <p className="text-xs text-[#5C5C5C] mt-1">{message}</p>
          </div>
          {onRetry && (
            <button
              onClick={onRetry}
              className="text-xs font-semibold px-3 py-1.5 rounded-lg bg-[#874436] text-white hover:bg-[#6E3529] transition-all"
            >
              Retry
            </button>
          )}
        </div>
      </div>
    );
  }

  return (
    <div
      className={`min-h-[50vh] flex flex-col items-center justify-center p-8 sm:p-12 text-center rounded-2xl bg-[#FAF8F5] border border-[#D5CABE] shadow-sm ${className}`}
    >
      <div className="w-16 h-16 rounded-2xl bg-[#FDF6F5] border border-[#EED1CB] flex items-center justify-center text-[#874436] mb-6 shadow-sm">
        <AlertTriangle className="w-8 h-8" />
      </div>

      <span className="text-[11px] font-mono font-semibold tracking-wider text-[#874436] uppercase mb-1">
        {errorCode}
      </span>
      <h3 className="text-2xl font-bold text-[#1B1B1B] tracking-tight mb-2">
        {title}
      </h3>
      <p className="text-sm text-[#5C5C5C] max-w-md leading-relaxed mb-6">
        {message}
      </p>

      {technicalDetails && (
        <div className="max-w-lg w-full mb-6 text-left">
          <button
            onClick={() => setShowDetails(!showDetails)}
            className="flex items-center gap-1.5 text-xs text-[#968676] hover:text-[#1B1B1B] font-medium mx-auto mb-2 transition-colors"
          >
            <span>{showDetails ? "Hide Diagnostic Trace" : "Show Diagnostic Trace"}</span>
            {showDetails ? <ChevronUp className="w-3.5 h-3.5" /> : <ChevronDown className="w-3.5 h-3.5" />}
          </button>

          {showDetails && (
            <div className="relative bg-[#1B1B1B] text-[#FAF8F5] rounded-xl p-4 font-mono text-[11px] overflow-x-auto shadow-inner border border-[#333]">
              <button
                onClick={handleCopy}
                className="absolute top-2.5 right-2.5 p-1.5 rounded bg-zinc-800 hover:bg-zinc-700 text-zinc-300 transition-colors"
                title="Copy trace to clipboard"
              >
                {copied ? <Check className="w-3.5 h-3.5 text-emerald-400" /> : <Copy className="w-3.5 h-3.5" />}
              </button>
              <pre className="whitespace-pre-wrap break-all pr-8">{technicalDetails}</pre>
            </div>
          )}
        </div>
      )}

      <div className="flex flex-wrap items-center justify-center gap-3">
        {onRetry && (
          <button
            onClick={onRetry}
            className="inline-flex items-center gap-2 px-5 py-2.5 rounded-xl bg-[#874436] hover:bg-[#6E3529] text-white font-medium text-xs shadow-sm transition-all active:scale-[0.98]"
          >
            <RotateCcw className="w-3.5 h-3.5" />
            <span>Retry Operation</span>
          </button>
        )}

        <a
          href={`mailto:${supportEmail}?subject=Incident%20Report%20[${errorCode}]&body=I%20encountered%20an%20error:%20${errorCode}`}
          className="inline-flex items-center gap-2 px-4 py-2.5 rounded-xl bg-[#F0EBE4] hover:bg-[#E5DDD4] text-[#1B1B1B] font-medium text-xs border border-[#D5CABE] transition-all"
        >
          <Mail className="w-3.5 h-3.5 text-[#874436]" />
          <span>Report to Support ({supportEmail})</span>
        </a>
      </div>
    </div>
  );
}
