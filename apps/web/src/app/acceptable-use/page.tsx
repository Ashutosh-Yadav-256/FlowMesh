"use client";

import React from "react";
import { LegalLayout } from "@/components/legal/LegalLayout";
import { CheckSquare, ShieldAlert, Ban, AlertTriangle } from "lucide-react";

export default function AcceptableUsePage() {
  return (
    <LegalLayout
      title="Acceptable Use Policy (AUP)"
      subtitle="Operational Safety, System Integrity Standards & Anti-Abuse Provisions."
      lastUpdated="September 24, 2026"
    >
      <div className="space-y-6">
        <section className="space-y-3">
          <h2 className="text-xl font-bold text-[#1B1B1B] tracking-tight flex items-center gap-2">
            <CheckSquare className="w-5 h-5 text-[#874436]" />
            1. Purpose & Scope
          </h2>
          <p>
            This Acceptable Use Policy specifies permitted and prohibited uses of the FlowMesh platform, APIs, connectors, and Edge Agent infrastructure. It applies to all operators, tenants, and automated service principals.
          </p>
        </section>

        <section className="space-y-3">
          <h2 className="text-xl font-bold text-[#1B1B1B] tracking-tight flex items-center gap-2">
            <Ban className="w-5 h-5 text-[#874436]" />
            2. Strictly Prohibited Activities
          </h2>
          <div className="space-y-2.5">
            {[
              {
                title: "Denial of Service & Infrastructure Saturation",
                desc: "Attempting to exhaust Redis/RediForge memory queues, NATS message rings, or worker thread pools through deliberate unthrottled recursion or synthetic deadlocks.",
              },
              {
                title: "Malware & Exploit Delivery",
                desc: "Using FlowMesh connectors or webhook endpoints to transmit malicious executables, command-and-control payloads, or crypto-mining scripts.",
              },
              {
                title: "Unauthorized Security Probing",
                desc: "Performing invasive port scanning, fuzzing, or penetration attacks against FlowMesh hosted control plane infrastructure outside of our Responsible Disclosure guidelines.",
              },
              {
                title: "Spam & Deceptive Communications",
                desc: "Configuring automated email, SMS, or messaging DAG connectors to distribute unsolicited bulk marketing messages or credential phishing forms.",
              },
              {
                title: "Bypassing Tenancy Controls",
                desc: "Attempting to forge tenant headers (X-Tenant-ID) or manipulate JWT subject claims to inspect cross-tenant audit trails or execution logs.",
              },
            ].map((rule, idx) => (
              <div key={idx} className="p-3.5 rounded-xl bg-[#F4EFEB] border border-[#E3D9CE] text-xs">
                <span className="font-bold text-[#874436] block mb-1">
                  {idx + 1}. {rule.title}
                </span>
                <p className="text-[#5C5C5C] leading-normal">{rule.desc}</p>
              </div>
            ))}
          </div>
        </section>

        <section className="space-y-3">
          <h2 className="text-xl font-bold text-[#1B1B1B] tracking-tight flex items-center gap-2">
            <ShieldAlert className="w-5 h-5 text-[#874436]" />
            3. Enforcement & Tenant Suspension
          </h2>
          <p>
            FlowMesh reserves the right to immediately isolate or revoke API tokens and quarantine offending Edge Agent instances upon detection of active AUP violations to safeguard multi-tenant platform stability.
          </p>
        </section>

        <section className="space-y-3 pt-4 border-t border-[#EAE2D8]">
          <span className="text-xs font-semibold text-[#1B1B1B] block">Abuse & Security Violation Reporting:</span>
          <p className="text-xs text-[#5C5C5C]">
            Report suspected abuses or terms violations immediately to our security and compliance officer:{" "}
            <a href="mailto:ashutosh4tech@gmail.com" className="font-mono font-bold text-[#874436] hover:underline">
              ashutosh4tech@gmail.com
            </a>
          </p>
        </section>
      </div>
    </LegalLayout>
  );
}
