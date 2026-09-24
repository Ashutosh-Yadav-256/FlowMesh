"use client";

import React from "react";
import Link from "next/link";
import { LegalLayout } from "@/components/legal/LegalLayout";
import { Cookie, ShieldCheck, Sliders, ExternalLink } from "lucide-react";

export default function CookiePolicyPage() {
  return (
    <LegalLayout
      title="Cookie Policy"
      subtitle="Transparent Storage Governance & Zero Third-Party Advertising Trackers."
      lastUpdated="September 24, 2026"
    >
      <div className="space-y-6">
        <section className="space-y-3">
          <h2 className="text-xl font-bold text-[#1B1B1B] tracking-tight flex items-center gap-2">
            <Cookie className="w-5 h-5 text-[#874436]" />
            1. What Are Cookies & How We Use Local Storage
          </h2>
          <p>
            FlowMesh uses strictly necessary cookies and browser local storage primitives solely to maintain authenticated session state, secure CSRF tokens, and remember your active tenant workspace preference.
          </p>
          <div className="bg-emerald-50 border border-emerald-200 rounded-xl p-4 text-xs text-emerald-800 flex items-start gap-2.5">
            <ShieldCheck className="w-4 h-4 text-emerald-600 shrink-0 mt-0.5" />
            <span>
              <strong>Zero Advertising Cookies:</strong> FlowMesh does not use third-party tracking pixels, marketing cookies, social media widgets, or cross-site tracking beacons.
            </span>
          </div>
        </section>

        <section className="space-y-3">
          <h2 className="text-xl font-bold text-[#1B1B1B] tracking-tight">
            2. Inventory of FlowMesh Storage Keys
          </h2>
          <div className="overflow-x-auto rounded-xl border border-[#D5CABE]">
            <table className="w-full text-left text-xs">
              <thead className="bg-[#F4EFEB] border-b border-[#D5CABE] text-[#1B1B1B] font-bold">
                <tr>
                  <th className="p-3">Cookie / Key Name</th>
                  <th className="p-3">Category</th>
                  <th className="p-3">Lifespan</th>
                  <th className="p-3">Purpose</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-[#EAE2D8] text-[#5C5C5C]">
                <tr>
                  <td className="p-3 font-mono text-[#1B1B1B] font-semibold">flowmesh_session</td>
                  <td className="p-3">Strictly Necessary</td>
                  <td className="p-3">Session / 8h</td>
                  <td className="p-3">Encrypted JWT bearer token verifying user identity and RBAC role.</td>
                </tr>
                <tr>
                  <td className="p-3 font-mono text-[#1B1B1B] font-semibold">flowmesh_tenant</td>
                  <td className="p-3">Functional</td>
                  <td className="p-3">1 Year</td>
                  <td className="p-3">Stores active tenant namespace (e.g. Acme Corp vs Production Workspace).</td>
                </tr>
                <tr>
                  <td className="p-3 font-mono text-[#1B1B1B] font-semibold">flowmesh_csrf</td>
                  <td className="p-3">Strictly Necessary</td>
                  <td className="p-3">Session</td>
                  <td className="p-3">Anti-Cross-Site-Request-Forgery protection token for state mutations.</td>
                </tr>
                <tr>
                  <td className="p-3 font-mono text-[#1B1B1B] font-semibold">flowmesh_consent</td>
                  <td className="p-3">Functional</td>
                  <td className="p-3">1 Year</td>
                  <td className="p-3">Remembers your granular cookie preference choices.</td>
                </tr>
              </tbody>
            </table>
          </div>
        </section>

        <section className="space-y-3">
          <h2 className="text-xl font-bold text-[#1B1B1B] tracking-tight flex items-center gap-2">
            <Sliders className="w-5 h-5 text-[#874436]" />
            3. Managing Your Preferences
          </h2>
          <p>
            You can dynamically adjust or revoke non-essential cookie categories at any time using our interactive settings panel:
          </p>
          <div className="pt-2">
            <Link
              href="/cookie-preferences"
              className="inline-flex items-center gap-2 px-5 py-2.5 rounded-xl bg-[#874436] hover:bg-[#6E3529] text-white text-xs font-semibold shadow-sm transition-all active:scale-[0.98]"
            >
              <Sliders className="w-3.5 h-3.5" />
              <span>Open Cookie Preferences Panel</span>
            </Link>
          </div>
        </section>

        <section className="space-y-3 pt-4 border-t border-[#EAE2D8]">
          <span className="text-xs font-semibold text-[#1B1B1B] block">Questions or Privacy Inquiries:</span>
          <p className="text-xs text-[#5C5C5C]">
            Direct all questions concerning our cookie handling to our designated compliance contact:{" "}
            <a href="mailto:ashutosh4tech@gmail.com" className="font-mono font-bold text-[#874436] hover:underline">
              ashutosh4tech@gmail.com
            </a>
          </p>
        </section>
      </div>
    </LegalLayout>
  );
}
