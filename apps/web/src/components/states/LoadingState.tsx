"use client";

import React from "react";
import { Loader2, Sparkles } from "lucide-react";

interface LoadingStateProps {
  message?: string;
  subMessage?: string;
  variant?: "spinner" | "skeleton-grid" | "table" | "compact";
  className?: string;
}

export function LoadingState({
  message = "Loading enterprise workflow state...",
  subMessage = "Synchronizing with control plane & RediForge StateStore",
  variant = "spinner",
  className = "",
}: LoadingStateProps) {
  if (variant === "compact") {
    return (
      <div className={`flex items-center gap-3 p-4 rounded-xl bg-[#FAF8F5] border border-[#D5CABE] ${className}`}>
        <Loader2 className="w-4 h-4 animate-spin text-[#874436]" />
        <span className="text-xs text-[#5C5C5C] font-medium">{message}</span>
      </div>
    );
  }

  if (variant === "skeleton-grid") {
    return (
      <div className={`space-y-4 ${className}`}>
        <div className="flex items-center justify-between">
          <div className="h-6 w-48 bg-[#E6DFD5] animate-pulse rounded-lg" />
          <div className="h-8 w-24 bg-[#E6DFD5] animate-pulse rounded-lg" />
        </div>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          {[1, 2, 3].map((i) => (
            <div key={i} className="p-6 rounded-2xl bg-[#FAF8F5] border border-[#D5CABE] space-y-4">
              <div className="flex items-center gap-3">
                <div className="w-10 h-10 rounded-xl bg-[#E6DFD5] animate-pulse" />
                <div className="space-y-1.5 flex-1">
                  <div className="h-3.5 w-28 bg-[#E6DFD5] animate-pulse rounded" />
                  <div className="h-2.5 w-16 bg-[#E6DFD5] animate-pulse rounded" />
                </div>
              </div>
              <div className="space-y-2 pt-2">
                <div className="h-2.5 w-full bg-[#E6DFD5] animate-pulse rounded" />
                <div className="h-2.5 w-4/5 bg-[#E6DFD5] animate-pulse rounded" />
              </div>
              <div className="pt-2 flex justify-between items-center">
                <div className="h-5 w-20 bg-[#E6DFD5] animate-pulse rounded-full" />
                <div className="h-5 w-14 bg-[#E6DFD5] animate-pulse rounded" />
              </div>
            </div>
          ))}
        </div>
      </div>
    );
  }

  if (variant === "table") {
    return (
      <div className={`rounded-2xl bg-[#FAF8F5] border border-[#D5CABE] overflow-hidden ${className}`}>
        <div className="p-4 border-b border-[#D5CABE] bg-[#F4EFEB] flex items-center justify-between">
          <div className="h-4 w-32 bg-[#E6DFD5] animate-pulse rounded" />
          <div className="h-4 w-20 bg-[#E6DFD5] animate-pulse rounded" />
        </div>
        <div className="divide-y divide-[#EAE2D8]">
          {[1, 2, 3, 4, 5].map((row) => (
            <div key={row} className="p-4 flex items-center gap-4">
              <div className="w-8 h-8 rounded-lg bg-[#E6DFD5] animate-pulse" />
              <div className="h-3.5 w-40 bg-[#E6DFD5] animate-pulse rounded" />
              <div className="h-3.5 w-24 bg-[#E6DFD5] animate-pulse rounded ml-auto" />
              <div className="h-3.5 w-16 bg-[#E6DFD5] animate-pulse rounded" />
            </div>
          ))}
        </div>
      </div>
    );
  }

  return (
    <div
      className={`min-h-[50vh] flex flex-col items-center justify-center p-8 text-center rounded-2xl bg-[#FAF8F5] border border-[#D5CABE] shadow-sm ${className}`}
    >
      <div className="relative mb-6">
        <div className="w-16 h-16 rounded-2xl bg-[#F4EFEB] border border-[#E3D9CE] flex items-center justify-center text-[#874436] shadow-sm">
          <Loader2 className="w-8 h-8 animate-spin text-[#874436]" />
        </div>
        <div className="absolute -top-1 -right-1 w-5 h-5 rounded-full bg-[#874436] text-white flex items-center justify-center">
          <Sparkles className="w-3 h-3 text-white animate-pulse" />
        </div>
      </div>

      <h3 className="text-xl font-bold text-[#1B1B1B] tracking-tight mb-2">
        {message}
      </h3>
      <p className="text-sm text-[#5C5C5C] max-w-md leading-relaxed">
        {subMessage}
      </p>

      <div className="mt-6 flex items-center gap-2">
        <span className="w-2 h-2 rounded-full bg-[#874436] animate-ping" />
        <span className="text-[11px] font-mono text-[#968676] uppercase tracking-wider">
          Polling StateStore · Distributed Workers Online
        </span>
      </div>
    </div>
  );
}
