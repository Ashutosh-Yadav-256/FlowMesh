"use client";

import React from "react";
import { LegalLayout } from "@/components/legal/LegalLayout";
import { Database, ShieldCheck, FileText, CheckCircle2, Lock } from "lucide-react";

export default function DpaPage() {
  return (
    <LegalLayout
      title="Data Processing Agreement (DPA)"
      subtitle="Standard Contractual Clauses (SCCs), Technical & Organizational Measures (TOMs) & GDPR Article 28."
      lastUpdated="September 24, 2026"
    >
      <div className="space-y-6">
        <section className="space-y-3">
          <h2 className="text-xl font-bold text-[#1B1B1B] tracking-tight flex items-center gap-2">
            <Database className="w-5 h-5 text-[#874436]" />
            1. Scope & Definitions Under GDPR Article 28
          </h2>
          <p>
            This Data Processing Agreement (&ldquo;DPA&rdquo;) governs the processing of Personal Data in connection with the deployment and management of the FlowMesh platform. For the purposes of Regulation (EU) 2016/679 (GDPR), the <strong>Customer acts as the Data Controller</strong> and <strong>FlowMesh acts as the Data Processor</strong> solely with respect to control plane administrative metadata.
          </p>
          <div className="bg-[#FAF8F5] border border-[#D5CABE] rounded-xl p-4 text-xs text-[#5C5C5C] leading-relaxed">
            <strong>DATA PLANE EXCLUSION:</strong> Because FlowMesh Edge Agents process ERP records and database contents exclusively inside Customer-controlled private infrastructure, FlowMesh does not receive, ingest, or process Customer transactional payload data.
          </div>
        </section>

        <section className="space-y-3">
          <h2 className="text-xl font-bold text-[#1B1B1B] tracking-tight flex items-center gap-2">
            <Lock className="w-5 h-5 text-[#874436]" />
            2. Technical & Organizational Measures (TOMs)
          </h2>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-xs">
            <div className="p-4 rounded-xl bg-[#F4EFEB] border border-[#E3D9CE] space-y-1.5">
              <span className="font-bold text-[#1B1B1B] block">Encryption in Transit & at Rest</span>
              <p className="text-[#5C5C5C]">
                All control plane communications require TLS 1.3. Credentials are encrypted via AES-256-GCM envelope encryption using customer-held Key Encryption Keys (KEK).
              </p>
            </div>
            <div className="p-4 rounded-xl bg-[#F4EFEB] border border-[#E3D9CE] space-y-1.5">
              <span className="font-bold text-[#1B1B1B] block">Zero Inbound Attack Surface</span>
              <p className="text-[#5C5C5C]">
                Edge Agents execute outbound-only mTLS connections. Zero inbound ports are opened in customer corporate firewalls (ADR-0001).
              </p>
            </div>
            <div className="p-4 rounded-xl bg-[#F4EFEB] border border-[#E3D9CE] space-y-1.5">
              <span className="font-bold text-[#1B1B1B] block">Denial of Remote Code Execution</span>
              <p className="text-[#5C5C5C]">
                No arbitrary script evaluation (ADR-0002). All tasks execute signed, declarative schema-validated connector invocations.
              </p>
            </div>
            <div className="p-4 rounded-xl bg-[#F4EFEB] border border-[#E3D9CE] space-y-1.5">
              <span className="font-bold text-[#1B1B1B] block">Multi-Tenant Isolation</span>
              <p className="text-[#5C5C5C]">
                Strict row-level tenant scoping enforced at the repository and state store layers preventing cross-tenant leakage.
              </p>
            </div>
          </div>
        </section>

        <section className="space-y-3">
          <h2 className="text-xl font-bold text-[#1B1B1B] tracking-tight flex items-center gap-2">
            <ShieldCheck className="w-5 h-5 text-[#874436]" />
            3. Security Incident & Breach Notification
          </h2>
          <p>
            In the event of a confirmed security incident affecting the FlowMesh control plane, FlowMesh shall notify affected Customer administrators without undue delay and in all events within <strong>48 hours</strong> of becoming aware of the breach.
          </p>
        </section>

        <section className="space-y-3 pt-4 border-t border-[#EAE2D8]">
          <h2 className="text-xl font-bold text-[#1B1B1B] tracking-tight flex items-center gap-2">
            <FileText className="w-5 h-5 text-[#874436]" />
            4. Execution of DPA & Contact
          </h2>
          <p>
            To execute a countersigned copy of this DPA incorporating European Commission Standard Contractual Clauses (SCCs), direct your request to:
          </p>
          <div className="bg-[#FAF8F5] border border-[#D5CABE] rounded-xl p-4 flex items-center justify-between">
            <span className="text-xs font-semibold text-[#1B1B1B]">Authorized Signatory:</span>
            <a
              href="mailto:ashutosh4tech@gmail.com?subject=FlowMesh%20DPA%20Execution%20Request"
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
