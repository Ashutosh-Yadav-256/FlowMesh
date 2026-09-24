"use client";

import React from "react";
import { LegalLayout } from "@/components/legal/LegalLayout";
import { Bug, ShieldCheck, Mail, AlertTriangle, CheckCircle2 } from "lucide-react";

export default function ResponsibleDisclosurePage() {
  return (
    <LegalLayout
      title="Responsible Disclosure Program"
      subtitle="Coordinated Vulnerability Reporting, Safe Harbor & Security Research Guidelines."
      lastUpdated="September 24, 2026"
    >
      <div className="space-y-6">
        <section className="space-y-3">
          <h2 className="text-xl font-bold text-[#1B1B1B] tracking-tight flex items-center gap-2">
            <Bug className="w-5 h-5 text-[#874436]" />
            1. Commitment to Coordinated Disclosure
          </h2>
          <p>
            Security is paramount to FlowMesh. We deeply appreciate the global cybersecurity research community assisting us in identifying and remediating potential vulnerabilities in our open-source repositories and cloud services.
          </p>
        </section>

        <section className="space-y-3">
          <h2 className="text-xl font-bold text-[#1B1B1B] tracking-tight flex items-center gap-2">
            <ShieldCheck className="w-5 h-5 text-[#874436]" />
            2. Safe Harbor Protections
          </h2>
          <div className="bg-emerald-50 border border-emerald-200 rounded-xl p-4 text-xs text-emerald-800 leading-relaxed">
            <strong>LEGAL SAFE HARBOR GUARANTEE:</strong> FlowMesh will not pursue legal action (under the CFAA or DMCA anti-circumvention provisions) against security researchers who discover and report vulnerabilities in good faith, in accordance with the guidelines below, and without exploiting customer data or disrupting services.
          </div>
        </section>

        <section className="space-y-3">
          <h2 className="text-xl font-bold text-[#1B1B1B] tracking-tight">
            3. Research Rules of Engagement
          </h2>
          <ul className="text-xs text-[#5C5C5C] space-y-2 list-disc pl-5">
            <li>
              <strong>No Data Exfiltration:</strong> Do not access, download, or tamper with customer records, tenant database contents, or proprietary workflow definitions.
            </li>
            <li>
              <strong>No Denial of Service:</strong> Refrain from running automated volumetric fuzzers or stress tests that degrade control plane availability.
            </li>
            <li>
              <strong>90-Day Embargo:</strong> Provide us a reasonable window (typically 90 days) to patch and release fixes before publicly publishing vulnerability details or CVE writeups.
            </li>
            <li>
              <strong>Testing Accounts:</strong> Conduct all active penetration testing using self-hosted local Docker instances or dedicated test tenant namespaces.
            </li>
          </ul>
        </section>

        <section className="space-y-3 pt-4 border-t border-[#EAE2D8]">
          <h2 className="text-xl font-bold text-[#1B1B1B] tracking-tight flex items-center gap-2">
            <Mail className="w-5 h-5 text-[#874436]" />
            4. How to Submit a Vulnerability Report
          </h2>
          <p>
            Please email encrypted or detailed technical reports directly to our dedicated security contact. Do not file public GitHub issues for security vulnerabilities.
          </p>
          <div className="bg-[#FAF8F5] border border-[#D5CABE] rounded-xl p-4 flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3">
            <div>
              <span className="text-xs font-bold text-[#1B1B1B] block">Security Response Contact:</span>
              <span className="text-xs text-[#5C5C5C]">Triage acknowledgment within 24 hours</span>
            </div>
            <a
              href="mailto:ashutosh4tech@gmail.com?subject=VULNERABILITY%20REPORT:%20[Brief%20Description]"
              className="text-xs font-mono font-bold text-[#874436] hover:underline"
            >
              ashutosh4tech@gmail.com
            </a>
          </div>
        </section>
      </div>
    </LegalLayout>
  );
}
