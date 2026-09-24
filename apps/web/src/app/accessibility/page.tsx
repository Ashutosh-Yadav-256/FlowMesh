"use client";

import React from "react";
import { LegalLayout } from "@/components/legal/LegalLayout";
import { Eye, CheckCircle2, Keyboard, Monitor, Mail } from "lucide-react";

export default function AccessibilityStatementPage() {
  return (
    <LegalLayout
      title="Accessibility Statement"
      subtitle="Commitment to Digital Accessibility, Universal Access & WCAG 2.1 AA Standards."
      lastUpdated="September 24, 2026"
    >
      <div className="space-y-6">
        <section className="space-y-3">
          <h2 className="text-xl font-bold text-[#1B1B1B] tracking-tight flex items-center gap-2">
            <Eye className="w-5 h-5 text-[#874436]" />
            1. Our Universal Accessibility Commitment
          </h2>
          <p>
            FlowMesh is dedicated to ensuring that our enterprise integration web console, documentation, and workflow visualizations are accessible to everyone, including engineers and operators with visual, auditory, motor, or cognitive disabilities.
          </p>
          <div className="bg-emerald-50 border border-emerald-200 rounded-xl p-4 text-xs text-emerald-800 flex items-start gap-2.5">
            <CheckCircle2 className="w-4 h-4 text-emerald-600 shrink-0 mt-0.5" />
            <span>
              <strong>Target Standard:</strong> We adhere to the World Wide Web Consortium (W3C) <strong>Web Content Accessibility Guidelines (WCAG) 2.1 Level AA</strong> across all interactive dashboard interfaces.
            </span>
          </div>
        </section>

        <section className="space-y-3">
          <h2 className="text-xl font-bold text-[#1B1B1B] tracking-tight flex items-center gap-2">
            <Monitor className="w-5 h-5 text-[#874436]" />
            2. Concrete Measures Implemented
          </h2>
          <ul className="list-disc pl-5 space-y-2 text-[#5C5C5C]">
            <li>
              <strong>High Contrast Ratios:</strong> Text in Carbon (<code>#1B1B1B</code>) against our Warm Linen backdrop (<code>#E6DFD5</code>) provides a contrast ratio exceeding <strong>8.4:1</strong>, well above the WCAG AAA threshold of 7:1.
            </li>
            <li>
              <strong>Screen Reader Compatibility:</strong> Semantic HTML5 elements (&lt;nav&gt;, &lt;main&gt;, &lt;aside&gt;, &lt;header&gt;) paired with WAI-ARIA roles ensure compatibility with VoiceOver, NVDA, and JAWS.
            </li>
            <li>
              <strong>Keyboard-Only Operability:</strong> All navigation links, modal dialogs, and workspace switches can be operated using <kbd className="px-1.5 py-0.5 rounded bg-[#F0EBE4] border border-[#D5CABE] text-xs font-mono">Tab</kbd>, <kbd className="px-1.5 py-0.5 rounded bg-[#F0EBE4] border border-[#D5CABE] text-xs font-mono">Enter</kbd>, and <kbd className="px-1.5 py-0.5 rounded bg-[#F0EBE4] border border-[#D5CABE] text-xs font-mono">Esc</kbd>. Focus indicators remain prominent at all times.
            </li>
            <li>
              <strong>Reduced Motion Support:</strong> The interface respects the operating system preference <code>prefers-reduced-motion: reduce</code>, disabling non-essential transitions and pulsing spinners.
            </li>
          </ul>
        </section>

        <section className="space-y-3">
          <h2 className="text-xl font-bold text-[#1B1B1B] tracking-tight flex items-center gap-2">
            <Mail className="w-5 h-5 text-[#874436]" />
            3. Feedback & Accessibility Remediation Contact
          </h2>
          <p>
            If you encounter any accessibility barrier or require an alternative format of our compliance documentation or visual workflow graphs, reach out directly to our accessibility coordinator:
          </p>
          <div className="bg-[#FAF8F5] border border-[#D5CABE] rounded-xl p-4 flex items-center justify-between">
            <div>
              <span className="text-xs font-bold text-[#1B1B1B] block">Accessibility Desk:</span>
              <span className="text-xs text-[#5C5C5C]">Guaranteed response within 48 business hours</span>
            </div>
            <a
              href="mailto:ashutosh4tech@gmail.com?subject=FlowMesh%20Accessibility%20Barrier%20Report"
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
