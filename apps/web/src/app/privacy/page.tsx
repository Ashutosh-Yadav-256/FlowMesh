"use client";

import React from "react";
import { LegalLayout } from "@/components/legal/LegalLayout";
import { Shield, Lock, Database, UserCheck, AlertCircle } from "lucide-react";

export default function PrivacyPolicyPage() {
  return (
    <LegalLayout
      title="Privacy Policy"
      subtitle="Enterprise Data Sovereignty, Zero-Exfiltration Guarantee & Global Compliance."
      lastUpdated="September 24, 2026"
    >
      <div className="space-y-6">
        <section className="space-y-3">
          <h2 className="text-xl font-bold text-[#1B1B1B] tracking-tight flex items-center gap-2">
            <Shield className="w-5 h-5 text-[#874436]" />
            1. Core Architectural Principle: Zero Data Exfiltration
          </h2>
          <p>
            FlowMesh is engineered as a <strong>client-owned, self-hosted, cloud-neutral enterprise integration platform</strong>. Unlike traditional multi-tenant SaaS integration tools (such as Zapier, Workato, or MuleSoft Cloud), FlowMesh does not ingest, copy, store, or train machine learning models on your enterprise database records or proprietary transaction payloads.
          </p>
          <div className="bg-[#F4EFEB] border border-[#E3D9CE] rounded-xl p-4 text-xs space-y-2">
            <span className="font-bold text-[#1B1B1B] block">Enterprise Data Sovereignty Guarantee:</span>
            <p className="text-[#5C5C5C]">
              Customer ERP records, relational database contents, and credential keys are processed inside your corporate network boundary via the FlowMesh Edge Agent. Only cryptographic heartbeat attestations and anonymized orchestration execution metadata traverse the control plane.
            </p>
          </div>
        </section>

        <section className="space-y-3">
          <h2 className="text-xl font-bold text-[#1B1B1B] tracking-tight flex items-center gap-2">
            <Database className="w-5 h-5 text-[#874436]" />
            2. Categories of Information Processed
          </h2>
          <ul className="list-disc pl-5 space-y-2 text-[#5C5C5C]">
            <li>
              <strong>Account & Administrative Identity:</strong> Name, work email address, SSO/SAML assertion tokens, and organization namespace.
            </li>
            <li>
              <strong>Workflow Metadata & DAG Topologies:</strong> Workflow step graphs, connector configuration templates (excluding plain text passwords, which are envelope encrypted via AES-256-GCM), and cron trigger schedules.
            </li>
            <li>
              <strong>Telemetry & Observability:</strong> Execution run timestamps, step statuses (SUCCESS, FAILED, RETRY), duration in milliseconds, and distributed trace IDs.
            </li>
          </ul>
        </section>

        <section className="space-y-3">
          <h2 className="text-xl font-bold text-[#1B1B1B] tracking-tight flex items-center gap-2">
            <Lock className="w-5 h-5 text-[#874436]" />
            3. Envelope Encryption & Key Management
          </h2>
          <p>
            All connection credentials (e.g. database connection strings, Stripe API keys, SAP service accounts) are encrypted at rest using envelope encryption. A Master Key Encryption Key (KEK) is supplied by your infrastructure (AWS KMS, HashiCorp Vault, or local environment secret) and is never accessible to FlowMesh personnel.
          </p>
        </section>

        <section className="space-y-3">
          <h2 className="text-xl font-bold text-[#1B1B1B] tracking-tight flex items-center gap-2">
            <UserCheck className="w-5 h-5 text-[#874436]" />
            4. Rights Under GDPR, CCPA / CPRA & Global Frameworks
          </h2>
          <p>
            Depending on your jurisdiction, you retain statutory rights to access, rectify, export, or permanently delete personal account metadata stored in the control plane. To exercise these rights or request a certified data deletion receipt:
          </p>
          <div className="bg-[#FAF8F5] border border-[#D5CABE] rounded-xl p-4 flex items-center justify-between">
            <div>
              <span className="text-xs font-bold text-[#1B1B1B] block">Data Protection Officer (DPO) Contact:</span>
              <span className="text-xs text-[#5C5C5C]">Sole designated privacy representative</span>
            </div>
            <a
              href="mailto:ashutosh4tech@gmail.com?subject=GDPR%20Data%20Subject%20Request"
              className="text-xs font-mono font-bold text-[#874436] hover:underline"
            >
              ashutosh4tech@gmail.com
            </a>
          </div>
        </section>

        <section className="space-y-3">
          <h2 className="text-xl font-bold text-[#1B1B1B] tracking-tight flex items-center gap-2">
            <AlertCircle className="w-5 h-5 text-[#874436]" />
            5. Sub-Processors & Infrastructure Neutrality
          </h2>
          <p>
            FlowMesh operates with zero third-party telemetry beacons, advertising trackers, or external behavioral trackers. When deployed on-premise or in private VPCs, zero outbound internet connections are made without explicit tenant administrator authorization.
          </p>
        </section>
      </div>
    </LegalLayout>
  );
}
