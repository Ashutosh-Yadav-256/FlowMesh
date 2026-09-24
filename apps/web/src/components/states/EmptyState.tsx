"use client";

import React from "react";
import Link from "next/link";
import { FolderPlus, ArrowRight, LucideIcon } from "lucide-react";

interface EmptyStateProps {
  icon?: LucideIcon;
  title: string;
  description: string;
  actionLabel?: string;
  actionHref?: string;
  onActionClick?: () => void;
  secondaryActionLabel?: string;
  secondaryActionHref?: string;
  className?: string;
}

export function EmptyState({
  icon: Icon = FolderPlus,
  title,
  description,
  actionLabel,
  actionHref,
  onActionClick,
  secondaryActionLabel,
  secondaryActionHref,
  className = "",
}: EmptyStateProps) {
  return (
    <div
      className={`flex flex-col items-center justify-center p-8 sm:p-12 text-center rounded-2xl bg-[#FAF8F5] border border-[#D5CABE] shadow-sm ${className}`}
    >
      <div className="relative mb-6">
        <div className="w-16 h-16 rounded-2xl bg-[#F4EFEB] border border-[#E3D9CE] flex items-center justify-center text-[#874436] shadow-inner">
          <Icon className="w-8 h-8" />
        </div>
        <div className="absolute -bottom-1 -right-1 w-6 h-6 rounded-full bg-[#874436] text-white flex items-center justify-center text-[10px] font-bold shadow-md">
          0
        </div>
      </div>

      <h3 className="text-xl font-bold text-[#1B1B1B] tracking-tight mb-2">
        {title}
      </h3>
      <p className="text-sm text-[#5C5C5C] max-w-md leading-relaxed mb-6">
        {description}
      </p>

      <div className="flex flex-wrap items-center justify-center gap-3">
        {actionLabel && (
          actionHref ? (
            <Link
              href={actionHref}
              className="inline-flex items-center gap-2 px-5 py-2.5 rounded-xl bg-[#874436] hover:bg-[#6E3529] text-white font-medium text-xs shadow-sm transition-all active:scale-[0.98]"
            >
              <span>{actionLabel}</span>
              <ArrowRight className="w-3.5 h-3.5" />
            </Link>
          ) : (
            <button
              onClick={onActionClick}
              className="inline-flex items-center gap-2 px-5 py-2.5 rounded-xl bg-[#874436] hover:bg-[#6E3529] text-white font-medium text-xs shadow-sm transition-all active:scale-[0.98]"
            >
              <span>{actionLabel}</span>
              <ArrowRight className="w-3.5 h-3.5" />
            </button>
          )
        )}

        {secondaryActionLabel && secondaryActionHref && (
          <Link
            href={secondaryActionHref}
            className="inline-flex items-center gap-2 px-4 py-2.5 rounded-xl bg-[#F0EBE4] hover:bg-[#E5DDD4] text-[#1B1B1B] font-medium text-xs border border-[#D5CABE] transition-all"
          >
            {secondaryActionLabel}
          </Link>
        )}
      </div>
    </div>
  );
}
