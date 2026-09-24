"use client";

import React from "react";
import { SearchX, RotateCcw, HelpCircle } from "lucide-react";
import Link from "next/link";

interface NoSearchResultsProps {
  query?: string;
  onClearFilters?: () => void;
  suggestions?: string[];
  helpHref?: string;
  className?: string;
}

export function NoSearchResults({
  query = "",
  onClearFilters,
  suggestions = ["Check for spelling errors", "Try broader search parameters", "Remove active filters"],
  helpHref = "/help",
  className = "",
}: NoSearchResultsProps) {
  return (
    <div
      className={`flex flex-col items-center justify-center p-8 sm:p-12 text-center rounded-2xl bg-[#FAF8F5] border border-[#D5CABE] shadow-sm ${className}`}
    >
      <div className="w-16 h-16 rounded-2xl bg-[#F4EFEB] border border-[#E3D9CE] flex items-center justify-center text-[#968676] mb-5 shadow-inner">
        <SearchX className="w-8 h-8" />
      </div>

      <span className="text-[11px] font-bold tracking-widest text-[#968676] uppercase mb-1">
        Zero Matches
      </span>
      <h3 className="text-xl font-bold text-[#1B1B1B] tracking-tight mb-2">
        No Results Found {query && <span className="text-[#874436]">for &ldquo;{query}&rdquo;</span>}
      </h3>
      <p className="text-sm text-[#5C5C5C] max-w-md leading-relaxed mb-6">
        No workflows, agents, connector runs, or audit records match your current criteria.
      </p>

      {suggestions.length > 0 && (
        <div className="bg-[#F4EFEB] border border-[#E3D9CE] rounded-xl p-4 max-w-sm w-full mb-6 text-left">
          <span className="text-[11px] font-semibold text-[#1B1B1B] uppercase tracking-wider block mb-2">
            Suggested adjustments:
          </span>
          <ul className="text-xs text-[#5C5C5C] space-y-1.5 list-disc pl-4">
            {suggestions.map((item, idx) => (
              <li key={idx}>{item}</li>
            ))}
          </ul>
        </div>
      )}

      <div className="flex flex-wrap items-center justify-center gap-3">
        {onClearFilters && (
          <button
            onClick={onClearFilters}
            className="inline-flex items-center gap-2 px-5 py-2.5 rounded-xl bg-[#874436] hover:bg-[#6E3529] text-white font-medium text-xs shadow-sm transition-all active:scale-[0.98]"
          >
            <RotateCcw className="w-3.5 h-3.5" />
            <span>Reset Search & Filters</span>
          </button>
        )}

        <Link
          href={helpHref}
          className="inline-flex items-center gap-2 px-4 py-2.5 rounded-xl bg-[#F0EBE4] hover:bg-[#E5DDD4] text-[#1B1B1B] font-medium text-xs border border-[#D5CABE] transition-all"
        >
          <HelpCircle className="w-3.5 h-3.5 text-[#874436]" />
          <span>Documentation & Help</span>
        </Link>
      </div>
    </div>
  );
}
