"use client";

import React, { useState, useEffect } from "react";
import Link from "next/link";
import {
  Sparkles,
  ChevronDown,
  ChevronUp,
  X,
  CheckCircle2,
  Circle,
  RotateCcw,
  ArrowRight,
  ExternalLink,
} from "lucide-react";

interface Milestone {
  id: string;
  title: string;
  description: string;
  href: string;
  isComplete: boolean;
}

export function OnboardingChecklist() {
  const [isMinimized, setIsMinimized] = useState(false);
  const [isDismissed, setIsDismissed] = useState(false);
  const [milestones, setMilestones] = useState<Milestone[]>([
    {
      id: "demo",
      title: "Explore Acme Sandbox",
      description: "Pre-seeded DAGs, connections & traces",
      href: "/workflows",
      isComplete: true,
    },
    {
      id: "connectors",
      title: "Inspect Database Connector",
      description: "Enclave AES-256-GCM encryption",
      href: "/connections",
      isComplete: false,
    },
    {
      id: "runs",
      title: "Inspect Live Workflow Run",
      description: "Deterministic RediForge state",
      href: "/runs",
      isComplete: false,
    },
    {
      id: "swagger",
      title: "Review OpenAPI & Swagger Docs",
      description: "Interactive endpoints at /docs",
      href: "http://localhost:8000/docs",
      isComplete: false,
    },
  ]);

  useEffect(() => {
    const dismissed = localStorage.getItem("flowmesh_checklist_dismissed");
    if (dismissed === "true") {
      setIsDismissed(true);
    }
  }, []);

  const completedCount = milestones.filter((m) => m.isComplete).length;
  const progressPct = Math.round((completedCount / milestones.length) * 100);

  const handleDismiss = () => {
    setIsDismissed(true);
    localStorage.setItem("flowmesh_checklist_dismissed", "true");
  };

  const handleOpenTour = () => {
    window.dispatchEvent(new CustomEvent("flowmesh:open-onboarding"));
  };

  const toggleMilestone = (id: string, e: React.MouseEvent) => {
    e.stopPropagation();
    setMilestones((prev) =>
      prev.map((m) => (m.id === id ? { ...m, isComplete: !m.isComplete } : m))
    );
  };

  if (isDismissed) return null;

  return (
    <div className="fixed bottom-5 right-5 z-30 max-w-sm w-full select-none animate-in slide-in-from-bottom-3 duration-300">
      <div className="bg-[#FAF8F5]/98 backdrop-blur-md border border-[#D5CABE] rounded-2xl shadow-xl overflow-hidden transition-all">
        {/* Header Bar */}
        <div
          onClick={() => setIsMinimized((prev) => !prev)}
          className="h-12 px-4 flex items-center justify-between cursor-pointer bg-[#F3EFEA] hover:bg-[#EAE4DC] border-b border-[#D5CABE] transition-colors"
        >
          <div className="flex items-center gap-2">
            <div className="w-5 h-5 rounded-full bg-[#874436] flex items-center justify-center text-white text-[10px] font-bold">
              {progressPct === 100 ? "✓" : `${completedCount}/${milestones.length}`}
            </div>
            <span className="text-xs font-bold text-[#1B1B1B]">
              Launch Milestones ({progressPct}%)
            </span>
          </div>

          <div className="flex items-center gap-1">
            <button
              onClick={(e) => {
                e.stopPropagation();
                handleOpenTour();
              }}
              title="Re-open guided walkthrough"
              className="p-1 rounded text-[#968676] hover:text-[#874436] hover:bg-[#FAF8F5] transition-colors"
            >
              <Sparkles className="w-3.5 h-3.5" />
            </button>
            <button
              onClick={(e) => {
                e.stopPropagation();
                setIsMinimized((prev) => !prev);
              }}
              className="p-1 rounded text-[#968676] hover:text-[#1B1B1B] hover:bg-[#FAF8F5] transition-colors"
            >
              {isMinimized ? <ChevronUp className="w-3.5 h-3.5" /> : <ChevronDown className="w-3.5 h-3.5" />}
            </button>
            <button
              onClick={(e) => {
                e.stopPropagation();
                handleDismiss();
              }}
              title="Dismiss checklist"
              className="p-1 rounded text-[#968676] hover:text-[#1B1B1B] hover:bg-[#FAF8F5] transition-colors"
            >
              <X className="w-3.5 h-3.5" />
            </button>
          </div>
        </div>

        {/* Expandable Content */}
        {!isMinimized && (
          <div className="p-3 space-y-2">
            <div className="w-full bg-[#E7E0D6] h-1.5 rounded-full overflow-hidden">
              <div
                className="bg-[#874436] h-full transition-all duration-300 rounded-full"
                style={{ width: `${progressPct}%` }}
              />
            </div>

            <div className="space-y-1.5 pt-1">
              {milestones.map((m) => (
                <div
                  key={m.id}
                  className="flex items-start gap-2.5 p-2 rounded-lg hover:bg-[#F3EFEA] transition-colors group"
                >
                  <button
                    onClick={(e) => toggleMilestone(m.id, e)}
                    className="mt-0.5 text-[#968676] hover:text-[#874436] transition-colors shrink-0"
                  >
                    {m.isComplete ? (
                      <CheckCircle2 className="w-4 h-4 text-[#2E6B47]" />
                    ) : (
                      <Circle className="w-4 h-4 text-[#B8A99A]" />
                    )}
                  </button>

                  <div className="flex-1 min-w-0">
                    <Link
                      href={m.href}
                      target={m.href.startsWith("http") ? "_blank" : undefined}
                      className="block text-xs font-semibold text-[#1B1B1B] hover:text-[#874436] transition-colors truncate"
                    >
                      {m.title}
                    </Link>
                    <p className="text-[10px] text-[#6B5E51] leading-tight truncate">
                      {m.description}
                    </p>
                  </div>

                  <Link
                    href={m.href}
                    target={m.href.startsWith("http") ? "_blank" : undefined}
                    className="opacity-0 group-hover:opacity-100 text-[#968676] hover:text-[#874436] transition-opacity p-0.5"
                  >
                    {m.href.startsWith("http") ? (
                      <ExternalLink className="w-3 h-3" />
                    ) : (
                      <ArrowRight className="w-3 h-3" />
                    )}
                  </Link>
                </div>
              ))}
            </div>

            <div className="pt-2 border-t border-[#D5CABE]/60 flex items-center justify-between text-[11px]">
              <button
                onClick={handleOpenTour}
                className="text-[#874436] hover:underline font-semibold flex items-center gap-1"
              >
                <Sparkles className="w-3 h-3" />
                Open Interactive Tour
              </button>
              <button
                onClick={handleDismiss}
                className="text-[#968676] hover:text-[#1B1B1B]"
              >
                Hide Checklist
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
