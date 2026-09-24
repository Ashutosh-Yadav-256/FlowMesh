"use client";

import React from "react";
import { LegalLayout } from "@/components/legal/LegalLayout";
import { Scale, CheckCircle2, ShieldAlert, Cpu } from "lucide-react";

export default function TermsOfServicePage() {
  return (
    <LegalLayout
      title="Terms of Service"
      subtitle="Enterprise Software Licensing, Acceptable Use & Service Legal Agreement."
      lastUpdated="September 24, 2026"
    >
      <div className="space-y-6">
        <section className="space-y-3">
          <h2 className="text-xl font-bold text-[#1B1B1B] tracking-tight flex items-center gap-2">
            <Scale className="w-5 h-5 text-[#874436]" />
            1. Acceptance of Terms & Licensing Model
          </h2>
          <p>
            By accessing, deploying, installing, or interacting with the FlowMesh software, web console, or Edge Agent binaries, you represent that you have the organizational authority to bind your legal entity to these Terms of Service.
          </p>
          <p>
            FlowMesh is distributed as open-source software under the <strong>Apache License, Version 2.0</strong>, supplemented by enterprise commercial SLAs for proprietary connectors and mission-critical support agreements.
          </p>
        </section>

        <section className="space-y-3">
          <h2 className="text-xl font-bold text-[#1B1B1B] tracking-tight flex items-center gap-2">
            <Cpu className="w-5 h-5 text-[#874436]" />
            2. Customer Responsibilities & Edge Security
          </h2>
          <ul className="list-disc pl-5 space-y-2 text-[#5C5C5C]">
            <li>
              <strong>Credential Custody:</strong> You are solely responsible for provisioning and maintaining the secrecy of your Data Encryption Keys (DEK), API master keys, and private mTLS certificates.
            </li>
            <li>
              <strong>Network Boundary Configuration:</strong> Edge Agents require outbound-only internet or VPC egress to reach the control plane. You must ensure corporate firewall rules allow authorized WebSocket / mTLS traffic.
            </li>
            <li>
              <strong>Compliance With Local Law:</strong> You agree not to execute automated workflows that violate anti-money laundering regulations, sanctions lists (OFAC), or privacy laws.
            </li>
          </ul>
        </section>

        <section className="space-y-3">
          <h2 className="text-xl font-bold text-[#1B1B1B] tracking-tight flex items-center gap-2">
            <ShieldAlert className="w-5 h-5 text-[#874436]" />
            3. Limitation of Liability & Warranty Disclaimer
          </h2>
          <div className="bg-[#FAF8F5] border border-[#D5CABE] rounded-xl p-4 text-xs text-[#5C5C5C] leading-relaxed">
            TO THE MAXIMUM EXTENT PERMITTED BY APPLICABLE LAW, FLOWMESH AND ITS CONTRIBUTORS PROVIDE THE PLATFORM &ldquo;AS IS&rdquo; AND &ldquo;AS AVAILABLE,&rdquo; WITHOUT WARRANTIES OF ANY KIND, EITHER EXPRESS OR IMPLIED. UNDER NO CIRCUMSTANCES SHALL FLOWMESH BE LIABLE FOR INDIRECT, INCIDENTAL, SPECIAL, CONSEQUENTIAL, OR PUNITIVE DAMAGES, INCLUDING LOSS OF PROFITS, DATA CORRUPTION, OR SYSTEM DOWNTIME RESULTING FROM AUTOMATED DAG ACTIONS.
          </div>
        </section>

        <section className="space-y-3">
          <h2 className="text-xl font-bold text-[#1B1B1B] tracking-tight flex items-center gap-2">
            <CheckCircle2 className="w-5 h-5 text-[#874436]" />
            4. Enterprise SLA & Legal Inquiries
          </h2>
          <p>
            For enterprise customers holding active service-level agreements, enterprise support escalations, billing inquiries, or legal notices, send correspondence exclusively to:
          </p>
          <div className="bg-[#F4EFEB] border border-[#E3D9CE] rounded-xl p-4 flex items-center justify-between">
            <span className="text-xs font-semibold text-[#1B1B1B]">Designated Legal Representative:</span>
            <a
              href="mailto:ashutosh4tech@gmail.com?subject=FlowMesh%20Terms%20of%20Service%20Inquiry"
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
