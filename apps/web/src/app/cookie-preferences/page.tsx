"use client";

import React, { useState, useEffect } from "react";
import { LegalLayout } from "@/components/legal/LegalLayout";
import { Sliders, Check, ShieldCheck, Lock, Save, RefreshCw } from "lucide-react";

export default function CookiePreferencesPage() {
  const [preferences, setPreferences] = useState({
    necessary: true,
    functional: true,
    telemetry: false,
    marketing: false,
  });
  const [saved, setSaved] = useState(false);

  useEffect(() => {
    try {
      const stored = localStorage.getItem("flowmesh_cookie_preferences");
      if (stored) {
        setPreferences(JSON.parse(stored));
      }
    } catch (e) {
      console.warn("Could not read local cookie preferences", e);
    }
  }, []);

  const handleToggle = (key: "functional" | "telemetry") => {
    setPreferences((prev) => ({
      ...prev,
      [key]: !prev[key],
    }));
    setSaved(false);
  };

  const handleSave = () => {
    try {
      localStorage.setItem("flowmesh_cookie_preferences", JSON.stringify(preferences));
      setSaved(true);
      setTimeout(() => setSaved(false), 3000);
    } catch (e) {
      console.error("Could not persist cookie preferences", e);
    }
  };

  const handleAcceptAll = () => {
    const all = { necessary: true, functional: true, telemetry: true, marketing: false };
    setPreferences(all);
    localStorage.setItem("flowmesh_cookie_preferences", JSON.stringify(all));
    setSaved(true);
    setTimeout(() => setSaved(false), 3000);
  };

  const handleRejectNonEssential = () => {
    const min = { necessary: true, functional: false, telemetry: false, marketing: false };
    setPreferences(min);
    localStorage.setItem("flowmesh_cookie_preferences", JSON.stringify(min));
    setSaved(true);
    setTimeout(() => setSaved(false), 3000);
  };

  return (
    <LegalLayout
      title="Cookie Preferences"
      subtitle="Interactive Consent Management & Granular Local Storage Governance."
      lastUpdated="September 24, 2026"
    >
      <div className="space-y-6">
        <div className="bg-[#F4EFEB] border border-[#E3D9CE] rounded-xl p-4 text-xs text-[#5C5C5C] leading-relaxed">
          FlowMesh respects your privacy by default. We do not engage in ad-tech tracking or data brokerage. Use the toggles below to configure non-essential storage preferences.
        </div>

        <div className="space-y-4">
          {}
          <div className="p-5 rounded-2xl bg-[#FAF8F5] border border-[#D5CABE] flex items-start justify-between gap-4">
            <div className="space-y-1 max-w-lg">
              <div className="flex items-center gap-2">
                <span className="font-bold text-sm text-[#1B1B1B]">1. Strictly Necessary Cookies</span>
                <span className="text-[10px] font-bold text-emerald-700 bg-emerald-50 px-2 py-0.5 rounded border border-emerald-200 uppercase">
                  Always Active
                </span>
              </div>
              <p className="text-xs text-[#5C5C5C] leading-relaxed">
                Essential for core system functionality, CSRF defense, and secure cryptographic token authentication. Cannot be switched off without breaking platform functionality.
              </p>
            </div>
            <div className="flex items-center text-xs text-[#968676] font-semibold gap-1.5 pt-1">
              <Lock className="w-3.5 h-3.5" />
              <span>Locked</span>
            </div>
          </div>

          {}
          <div className="p-5 rounded-2xl bg-[#FAF8F5] border border-[#D5CABE] flex items-start justify-between gap-4">
            <div className="space-y-1 max-w-lg">
              <span className="font-bold text-sm text-[#1B1B1B] block">2. Functional & Workspace Memory</span>
              <p className="text-xs text-[#5C5C5C] leading-relaxed">
                Persists your active tenant workspace, UI theme settings, collapsed sidebar state, and draft DAG configurations in your local browser cache.
              </p>
            </div>
            <label className="relative inline-flex items-center cursor-pointer pt-1">
              <input
                type="checkbox"
                checked={preferences.functional}
                onChange={() => handleToggle("functional")}
                className="sr-only peer"
              />
              <div className="w-11 h-6 bg-[#D5CABE] peer-focus:outline-none rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[6px] after:left-[2px] after:bg-white after:border-[#D5CABE] after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-[#874436]"></div>
            </label>
          </div>

          {}
          <div className="p-5 rounded-2xl bg-[#FAF8F5] border border-[#D5CABE] flex items-start justify-between gap-4">
            <div className="space-y-1 max-w-lg">
              <span className="font-bold text-sm text-[#1B1B1B] block">3. Performance & Anonymous Diagnostics</span>
              <p className="text-xs text-[#5C5C5C] leading-relaxed">
                Permits client-side collection of anonymous UI rendering durations and connector latency metrics to improve WebAssembly and DAG visualization performance.
              </p>
            </div>
            <label className="relative inline-flex items-center cursor-pointer pt-1">
              <input
                type="checkbox"
                checked={preferences.telemetry}
                onChange={() => handleToggle("telemetry")}
                className="sr-only peer"
              />
              <div className="w-11 h-6 bg-[#D5CABE] peer-focus:outline-none rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[6px] after:left-[2px] after:bg-white after:border-[#D5CABE] after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-[#874436]"></div>
            </label>
          </div>

          {}
          <div className="p-5 rounded-2xl bg-[#F4EFEB] border border-[#E3D9CE] flex items-start justify-between gap-4 opacity-75">
            <div className="space-y-1 max-w-lg">
              <div className="flex items-center gap-2">
                <span className="font-bold text-sm text-[#1B1B1B]">4. Advertising & Marketing Trackers</span>
                <span className="text-[10px] font-bold text-zinc-500 bg-zinc-200 px-2 py-0.5 rounded uppercase">
                  Permanently Disabled
                </span>
              </div>
              <p className="text-xs text-[#5C5C5C] leading-relaxed">
                Third-party advertising trackers and behavioral remarketing pixels are completely banned from FlowMesh binaries.
              </p>
            </div>
            <div className="flex items-center text-xs text-[#968676] font-semibold gap-1.5 pt-1">
              <ShieldCheck className="w-4 h-4 text-emerald-600" />
              <span>Zero Trackers</span>
            </div>
          </div>
        </div>

        {}
        <div className="pt-4 border-t border-[#EAE2D8] flex flex-wrap items-center justify-between gap-4">
          <div className="flex flex-wrap items-center gap-3">
            <button
              onClick={handleSave}
              className="inline-flex items-center gap-2 px-5 py-2.5 rounded-xl bg-[#874436] hover:bg-[#6E3529] text-white text-xs font-semibold shadow-sm transition-all active:scale-[0.98]"
            >
              <Save className="w-3.5 h-3.5" />
              <span>Save Custom Preferences</span>
            </button>

            <button
              onClick={handleAcceptAll}
              className="inline-flex items-center gap-2 px-4 py-2.5 rounded-xl bg-[#FAF8F5] hover:bg-[#F0EBE4] border border-[#D5CABE] text-[#1B1B1B] text-xs font-semibold transition-all"
            >
              <span>Accept Functional</span>
            </button>

            <button
              onClick={handleRejectNonEssential}
              className="inline-flex items-center gap-2 px-4 py-2.5 rounded-xl bg-[#FAF8F5] hover:bg-[#F0EBE4] border border-[#D5CABE] text-[#5C5C5C] text-xs font-medium transition-all"
            >
              <span>Reject Non-Essential</span>
            </button>
          </div>

          {saved && (
            <div className="flex items-center gap-2 text-xs font-semibold text-emerald-700 bg-emerald-50 px-3 py-1.5 rounded-lg border border-emerald-200 animate-fade-in">
              <Check className="w-4 h-4 text-emerald-600" />
              <span>Preferences Saved to Browser Storage</span>
            </div>
          )}
        </div>

        <div className="pt-4 text-xs text-[#5C5C5C] border-t border-[#EAE2D8]">
          Have questions or want your IP address cleared from server access logs? Contact our compliance desk at{" "}
          <a href="mailto:ashutosh4tech@gmail.com" className="font-mono font-bold text-[#874436] hover:underline">
            ashutosh4tech@gmail.com
          </a>.
        </div>
      </div>
    </LegalLayout>
  );
}
