"use client";

import React, { useState } from "react";
import Link from "next/link";
import {
  LifeBuoy,
  Send,
  CheckCircle2,
  Clock,
  ShieldCheck,
  Mail,
  AlertTriangle,
  MessageSquare,
  FileQuestion,
  Headphones,
} from "lucide-react";

export default function SupportPage() {
  const [submitted, setSubmitted] = useState(false);
  const [formData, setFormData] = useState({
    subject: "",
    severity: "P3",
    component: "Workflow Engine",
    traceId: "",
    message: "",
  });

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    setSubmitted(true);
  };

  return (
    <div className="max-w-6xl mx-auto space-y-8 pb-16">
      {}
      <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4 pb-6 border-b border-[#D5CABE]">
        <div>
          <div className="flex items-center gap-2 text-xs font-semibold text-[#874436] uppercase tracking-wider mb-1">
            <Headphones className="w-4 h-4" />
            <span>Enterprise Operations</span>
          </div>
          <h1 className="text-3xl sm:text-4xl font-black text-[#1B1B1B] tracking-tight">
            Enterprise Support & Escalations
          </h1>
          <p className="text-sm text-[#5C5C5C] mt-1 max-w-2xl">
            Direct access to FlowMesh core platform architects, emergency triage dispatch, and enterprise SLA coverage.
          </p>
        </div>

        <div className="flex items-center gap-3">
          <Link
            href="/help"
            className="inline-flex items-center gap-2 px-4 py-2.5 rounded-xl bg-[#FAF8F5] hover:bg-[#F0EBE4] border border-[#D5CABE] text-[#1B1B1B] text-xs font-semibold transition-all shadow-sm"
          >
            <FileQuestion className="w-3.5 h-3.5 text-[#874436]" />
            <span>Search Help Center</span>
          </Link>
        </div>
      </div>

      {}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <div className="p-5 rounded-2xl bg-[#FAF8F5] border border-[#D5CABE] shadow-sm space-y-2">
          <div className="flex items-center justify-between">
            <span className="text-[10px] font-bold text-rose-700 bg-rose-50 px-2 py-0.5 rounded border border-rose-200">
              P1 · Blocker
            </span>
            <span className="text-xs font-mono font-bold text-[#1B1B1B]">&lt; 15 Mins SLA</span>
          </div>
          <h3 className="font-bold text-sm text-[#1B1B1B]">Production Outage</h3>
          <p className="text-xs text-[#5C5C5C] leading-normal">
            Complete data plane failure, financial transaction deadlock, or edge agent communication severed.
          </p>
        </div>

        <div className="p-5 rounded-2xl bg-[#FAF8F5] border border-[#D5CABE] shadow-sm space-y-2">
          <div className="flex items-center justify-between">
            <span className="text-[10px] font-bold text-amber-800 bg-amber-50 px-2 py-0.5 rounded border border-amber-200">
              P2 · Major
            </span>
            <span className="text-xs font-mono font-bold text-[#1B1B1B]">&lt; 2 Hours SLA</span>
          </div>
          <h3 className="font-bold text-sm text-[#1B1B1B]">Degraded Performance</h3>
          <p className="text-xs text-[#5C5C5C] leading-normal">
            High retry latency in connector runtime, schema drift warning on secondary ERP tables, or rate limit threshold breach.
          </p>
        </div>

        <div className="p-5 rounded-2xl bg-[#FAF8F5] border border-[#D5CABE] shadow-sm space-y-2">
          <div className="flex items-center justify-between">
            <span className="text-[10px] font-bold text-[#7A6C5D] bg-[#F4EFEB] px-2 py-0.5 rounded border border-[#E3D9CE]">
              P3 · Standard
            </span>
            <span className="text-xs font-mono font-bold text-[#1B1B1B]">&lt; 8 Hours SLA</span>
          </div>
          <h3 className="font-bold text-sm text-[#1B1B1B]">General Assistance</h3>
          <p className="text-xs text-[#5C5C5C] leading-normal">
            Custom connector implementation guidance, DAG template reviews, and RBAC role assignment queries.
          </p>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-12 gap-8">
        {}
        <div className="lg:col-span-8 bg-[#FAF8F5] border border-[#D5CABE] rounded-2xl p-6 sm:p-8 shadow-sm space-y-6">
          <div className="flex items-center gap-2 pb-4 border-b border-[#EAE2D8]">
            <MessageSquare className="w-5 h-5 text-[#874436]" />
            <h2 className="text-lg font-bold text-[#1B1B1B]">Submit Technical Incident or Support Ticket</h2>
          </div>

          {submitted ? (
            <div className="p-8 text-center space-y-4 bg-[#F4EFEB] rounded-xl border border-[#E3D9CE]">
              <div className="w-14 h-14 rounded-2xl bg-emerald-50 border border-emerald-200 flex items-center justify-center text-emerald-600 mx-auto">
                <CheckCircle2 className="w-7 h-7" />
              </div>
              <h3 className="text-xl font-bold text-[#1B1B1B]">Support Dispatch Initiated</h3>
              <p className="text-xs text-[#5C5C5C] max-w-md mx-auto leading-relaxed">
                Your incident ticket has been queued with reference ID{" "}
                <code className="font-mono font-bold text-[#874436]">TICKET-FLOW-88219</code>. An engineer has been paged and will respond to{" "}
                <strong>ashutosh4tech@gmail.com</strong> in accordance with your chosen SLA tier.
              </p>
              <button
                onClick={() => setSubmitted(false)}
                className="px-4 py-2 rounded-xl bg-[#874436] text-white text-xs font-semibold hover:bg-[#6E3529] transition-all"
              >
                Submit Another Ticket
              </button>
            </div>
          ) : (
            <form onSubmit={handleSubmit} className="space-y-4">
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                <div>
                  <label className="block text-xs font-bold text-[#1B1B1B] mb-1.5">
                    Incident Severity Level
                  </label>
                  <select
                    value={formData.severity}
                    onChange={(e) => setFormData({ ...formData, severity: e.target.value })}
                    className="w-full text-xs rounded-xl bg-white border border-[#D5CABE] p-2.5 text-[#1B1B1B] focus:outline-none focus:ring-2 focus:ring-[#874436]/20 focus:border-[#874436]"
                  >
                    <option value="P1">P1 - Production Outage (&lt;15 min SLA)</option>
                    <option value="P2">P2 - Critical Function Impaired (&lt;2 hr SLA)</option>
                    <option value="P3">P3 - Major Issue (&lt;8 hr SLA)</option>
                    <option value="P4">P4 - Minor / Feature Request</option>
                  </select>
                </div>

                <div>
                  <label className="block text-xs font-bold text-[#1B1B1B] mb-1.5">
                    Component / Service
                  </label>
                  <select
                    value={formData.component}
                    onChange={(e) => setFormData({ ...formData, component: e.target.value })}
                    className="w-full text-xs rounded-xl bg-white border border-[#D5CABE] p-2.5 text-[#1B1B1B] focus:outline-none focus:ring-2 focus:ring-[#874436]/20 focus:border-[#874436]"
                  >
                    <option value="Enterprise Worker">Enterprise Worker (Spring Boot 3)</option>
                    <option value="Workflow Engine">Workflow Engine (DAG Runner)</option>
                    <option value="Edge Agent">Edge Agent (Go Static Daemon)</option>
                    <option value="RediForge StateStore">RediForge StateStore / Locks</option>
                    <option value="Connectors">Connectors (SAP, Oracle, Stripe)</option>
                    <option value="Web Console">Web Console & Visual Editor</option>
                  </select>
                </div>
              </div>

              <div>
                <label className="block text-xs font-bold text-[#1B1B1B] mb-1.5">
                  Subject / Summary
                </label>
                <input
                  type="text"
                  required
                  placeholder="e.g. Distributed transaction deadlock during Oracle ERP reconciliation"
                  value={formData.subject}
                  onChange={(e) => setFormData({ ...formData, subject: e.target.value })}
                  className="w-full text-xs rounded-xl bg-white border border-[#D5CABE] p-2.5 text-[#1B1B1B] focus:outline-none focus:ring-2 focus:ring-[#874436]/20 focus:border-[#874436]"
                />
              </div>

              <div>
                <label className="block text-xs font-bold text-[#1B1B1B] mb-1.5">
                  Trace ID or Run UUID (Optional)
                </label>
                <input
                  type="text"
                  placeholder="e.g. 9f82d1c3a84b4ef0874e0192a"
                  value={formData.traceId}
                  onChange={(e) => setFormData({ ...formData, traceId: e.target.value })}
                  className="w-full text-xs font-mono rounded-xl bg-white border border-[#D5CABE] p-2.5 text-[#1B1B1B] focus:outline-none focus:ring-2 focus:ring-[#874436]/20 focus:border-[#874436]"
                />
              </div>

              <div>
                <label className="block text-xs font-bold text-[#1B1B1B] mb-1.5">
                  Detailed Diagnostic Description & Steps to Reproduce
                </label>
                <textarea
                  required
                  rows={5}
                  placeholder="Describe what occurred, expected outcome, and paste any relevant logs from MdcLoggingFilter or JVM metrics..."
                  value={formData.message}
                  onChange={(e) => setFormData({ ...formData, message: e.target.value })}
                  className="w-full text-xs rounded-xl bg-white border border-[#D5CABE] p-2.5 text-[#1B1B1B] focus:outline-none focus:ring-2 focus:ring-[#874436]/20 focus:border-[#874436]"
                />
              </div>

              <div className="pt-2 flex items-center justify-between">
                <span className="text-[11px] text-[#5C5C5C]">
                  Direct support response will be sent to <strong>ashutosh4tech@gmail.com</strong>
                </span>
                <button
                  type="submit"
                  className="inline-flex items-center gap-2 px-6 py-2.5 rounded-xl bg-[#874436] hover:bg-[#6E3529] text-white text-xs font-semibold shadow-sm transition-all active:scale-[0.98]"
                >
                  <Send className="w-3.5 h-3.5" />
                  <span>Dispatch Support Request</span>
                </button>
              </div>
            </form>
          )}
        </div>

        {}
        <div className="lg:col-span-4 space-y-4">
          <div className="p-6 rounded-2xl bg-[#FAF8F5] border border-[#D5CABE] shadow-sm space-y-4">
            <span className="text-[10px] font-bold text-[#874436] uppercase tracking-widest block">
              Dedicated Support Desk
            </span>

            <div className="space-y-3 text-xs">
              <div className="flex items-start gap-2.5">
                <Mail className="w-4 h-4 text-[#874436] shrink-0 mt-0.5" />
                <div>
                  <span className="font-bold text-[#1B1B1B] block">Direct Escalation Email:</span>
                  <a
                    href="mailto:ashutosh4tech@gmail.com"
                    className="font-mono text-[11px] font-bold text-[#874436] hover:underline break-all"
                  >
                    ashutosh4tech@gmail.com
                  </a>
                </div>
              </div>

              <div className="flex items-start gap-2.5">
                <Clock className="w-4 h-4 text-[#874436] shrink-0 mt-0.5" />
                <div>
                  <span className="font-bold text-[#1B1B1B] block">Operating Hours:</span>
                  <span className="text-[#5C5C5C]">24/7/365 for P1 Incidents · 9am - 6pm UTC for P2-P4</span>
                </div>
              </div>

              <div className="flex items-start gap-2.5">
                <ShieldCheck className="w-4 h-4 text-[#874436] shrink-0 mt-0.5" />
                <div>
                  <span className="font-bold text-[#1B1B1B] block">Security Verification:</span>
                  <span className="text-[#5C5C5C]">Encrypted communications and GPG key verification on request.</span>
                </div>
              </div>
            </div>
          </div>

          <div className="p-5 rounded-2xl bg-[#F4EFEB] border border-[#E3D9CE] space-y-2 text-xs">
            <span className="font-bold text-[#1B1B1B] block">Emergency Production Outage?</span>
            <p className="text-[#5C5C5C] leading-normal">
              If all control plane endpoints are unreachable, email{" "}
              <a href="mailto:ashutosh4tech@gmail.com" className="font-mono font-bold text-[#874436] underline">
                ashutosh4tech@gmail.com
              </a>{" "}
              with the subject line <code className="bg-white px-1 py-0.5 rounded text-[#874436]">P1-OUTAGE</code> to trigger on-call automated paging.
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}
