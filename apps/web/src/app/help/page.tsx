"use client";

import React, { useState } from "react";
import Link from "next/link";
import {
  HelpCircle,
  Search,
  BookOpen,
  Cpu,
  Lock,
  Layers,
  Activity,
  ChevronDown,
  ChevronUp,
  Mail,
  ArrowRight,
  ExternalLink,
} from "lucide-react";

interface FaqItem {
  q: string;
  a: string;
  category: string;
}

const faqs: FaqItem[] = [
  {
    category: "Architecture & Security",
    q: "How does FlowMesh prevent firewall breaches with the Edge Agent?",
    a: "FlowMesh uses an outbound-only mTLS architecture (ADR-0001). The Edge Agent initiates all connections outward to the Control Plane over secure WebSocket/mTLS tunnels. Customer firewalls maintain zero open inbound listening ports.",
  },
  {
    category: "Architecture & Security",
    q: "Why does FlowMesh eliminate arbitrary Remote Code Execution (RCE)?",
    a: "Under ADR-0002, arbitrary script evaluation (e.g. eval, bash exec, unvetted python eval) is rejected in favor of cryptographically signed (Ed25519), declarative schema-validated connector invocations and strict allowlists.",
  },
  {
    category: "Java Enterprise Worker",
    q: "How does the Java Enterprise Worker handle high concurrency and avoid race conditions?",
    a: "The Enterprise Worker employs fine-grained partition lock striping (TenantConcurrencyStripingManager) to serialize operations targeting the same tenant/account, while allowing different tenants to execute in parallel across CPU cores. It also uses CompletableFuture scatter-gather fan-outs with non-blocking timeouts and lock-free token bucket rate limiting (CAS AtomicLong).",
  },
  {
    category: "Java Enterprise Worker",
    q: "How are Memory Leaks prevented in the Spring Boot worker?",
    a: "MdcLoggingFilter strictly wraps thread-bound SLF4J MDC operations with MDC.clear() inside a finally block to eliminate ThreadLocal pollution in thread pools. Furthermore, jvm.options configures -XX:+HeapDumpOnOutOfMemoryError and G1GC/ZGC memory region tuning.",
  },
  {
    category: "Code Quality & SonarQube",
    q: "What is the FlowMesh Clean as You Code Quality Gate threshold?",
    a: "Every pull request requires >= 80% code coverage on new code (generated via JaCoCo for Java and pytest-cov for Python), 0 Blocker and 0 Critical issues, and 100% review of security hotspots.",
  },
  {
    category: "Connectors & StateStore",
    q: "What is RediForge and how is it used in FlowMesh?",
    a: "RediForge is FlowMesh's high-performance StateStore backend. It provides sub-millisecond atomic distributed locking, circuit breaker state tracking, and idempotent workflow state persistence across distributed worker nodes.",
  },
];

export default function HelpCenterPage() {
  const [searchQuery, setSearchQuery] = useState("");
  const [openFaq, setOpenFaq] = useState<number | null>(0);
  const [selectedCategory, setSelectedCategory] = useState<string>("All");

  const categories = ["All", "Architecture & Security", "Java Enterprise Worker", "Code Quality & SonarQube", "Connectors & StateStore"];

  const filteredFaqs = faqs.filter((faq) => {
    const matchesCategory = selectedCategory === "All" || faq.category === selectedCategory;
    const matchesQuery =
      faq.q.toLowerCase().includes(searchQuery.toLowerCase()) ||
      faq.a.toLowerCase().includes(searchQuery.toLowerCase());
    return matchesCategory && matchesQuery;
  });

  return (
    <div className="max-w-6xl mx-auto space-y-8 pb-16">
      {}
      <div className="text-center max-w-3xl mx-auto space-y-4 pt-4 pb-2">
        <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-[#FAF8F5] border border-[#D5CABE] text-[#874436] text-xs font-semibold uppercase tracking-wider">
          <HelpCircle className="w-3.5 h-3.5" />
          <span>Documentation & Knowledge Base</span>
        </div>
        <h1 className="text-4xl sm:text-5xl font-black text-[#1B1B1B] tracking-tight">
          How Can We Help You?
        </h1>
        <p className="text-sm text-[#5C5C5C] leading-relaxed">
          Comprehensive guides, architectural decision records, troubleshooting playbooks, and best practices for the FlowMesh platform.
        </p>

        {}
        <div className="relative max-w-xl mx-auto pt-2">
          <Search className="w-4 h-4 text-[#968676] absolute left-4 top-1/2 -translate-y-1/2" />
          <input
            type="text"
            placeholder="Search documentation, concurrency patterns, or error codes..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="w-full text-xs rounded-2xl bg-[#FAF8F5] border border-[#D5CABE] pl-11 pr-4 py-3.5 text-[#1B1B1B] shadow-sm placeholder:text-[#968676] focus:outline-none focus:ring-2 focus:ring-[#874436]/20 focus:border-[#874436]"
          />
        </div>
      </div>

      {}
      <div className="flex flex-wrap items-center justify-center gap-2 pt-2">
        {categories.map((cat) => (
          <button
            key={cat}
            onClick={() => setSelectedCategory(cat)}
            className={`px-3.5 py-1.5 rounded-xl text-xs font-medium transition-all ${
              selectedCategory === cat
                ? "bg-[#874436] text-white font-semibold shadow-sm"
                : "bg-[#FAF8F5] hover:bg-[#F0EBE4] border border-[#D5CABE] text-[#5C5C5C] hover:text-[#1B1B1B]"
            }`}
          >
            {cat}
          </button>
        ))}
      </div>

      {}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        {[
          {
            title: "System Architecture",
            desc: "Hybrid cloud 3-tier model, outbound mTLS, and zero RCE tenets.",
            icon: Layers,
            href: "/privacy",
          },
          {
            title: "Java Concurrency",
            desc: "CompletableFuture scatter-gather, striped locking & Virtual Threads.",
            icon: Cpu,
            href: "/states",
          },
          {
            title: "SonarQube Quality",
            desc: "JaCoCo coverage, static analysis rules & CI quality gate criteria.",
            icon: Activity,
            href: "/security-policy",
          },
          {
            title: "Support Escalation",
            desc: "24/7 SLA triage, incident dispatch, and technical support.",
            icon: HelpCircle,
            href: "/support",
          },
        ].map((card, i) => {
          const Icon = card.icon;
          return (
            <Link
              key={i}
              href={card.href}
              className="p-5 rounded-2xl bg-[#FAF8F5] border border-[#D5CABE] shadow-sm hover:border-[#874436] transition-all group space-y-2 block"
            >
              <div className="w-10 h-10 rounded-xl bg-[#F4EFEB] border border-[#E3D9CE] flex items-center justify-center text-[#874436] group-hover:scale-105 transition-transform">
                <Icon className="w-5 h-5" />
              </div>
              <h3 className="font-bold text-sm text-[#1B1B1B] group-hover:text-[#874436] transition-colors">
                {card.title}
              </h3>
              <p className="text-xs text-[#5C5C5C] leading-normal">{card.desc}</p>
            </Link>
          );
        })}
      </div>

      {}
      <div className="bg-[#FAF8F5] border border-[#D5CABE] rounded-2xl p-6 sm:p-8 shadow-sm space-y-4">
        <h2 className="text-xl font-bold text-[#1B1B1B] tracking-tight mb-2">
          Frequently Answered Architectural Questions
        </h2>

        <div className="divide-y divide-[#EAE2D8]">
          {filteredFaqs.length > 0 ? (
            filteredFaqs.map((faq, idx) => {
              const isOpen = openFaq === idx;
              return (
                <div key={idx} className="py-4 space-y-2">
                  <button
                    onClick={() => setOpenFaq(isOpen ? null : idx)}
                    className="w-full flex items-center justify-between text-left gap-4 group"
                  >
                    <span className="text-sm font-bold text-[#1B1B1B] group-hover:text-[#874436] transition-colors">
                      {faq.q}
                    </span>
                    {isOpen ? (
                      <ChevronUp className="w-4 h-4 text-[#874436] shrink-0" />
                    ) : (
                      <ChevronDown className="w-4 h-4 text-[#968676] shrink-0" />
                    )}
                  </button>

                  {isOpen && (
                    <p className="text-xs text-[#5C5C5C] leading-relaxed pt-1 animate-fade-in">
                      {faq.a}
                    </p>
                  )}
                </div>
              );
            })
          ) : (
            <div className="py-8 text-center text-xs text-[#968676]">
              No questions found matching your search term. Reach out to support below.
            </div>
          )}
        </div>
      </div>

      {}
      <div className="p-8 rounded-2xl bg-[#874436] text-[#FAF8F5] flex flex-col sm:flex-row sm:items-center sm:justify-between gap-6 shadow-md">
        <div className="space-y-1">
          <h3 className="text-xl font-bold tracking-tight">Need 1-on-1 Enterprise Architecture Support?</h3>
          <p className="text-xs text-[#E6DFD5] leading-relaxed max-w-xl">
            Our principal integration engineers can review your custom DAG topologies, high-throughput JDBC configurations, or edge deployment manifests.
          </p>
        </div>

        <a
          href="mailto:ashutosh4tech@gmail.com?subject=FlowMesh%20Architecture%20Inquiry"
          className="inline-flex items-center gap-2 px-5 py-3 rounded-xl bg-white text-[#874436] text-xs font-bold shadow hover:bg-[#FAF8F5] transition-all shrink-0 active:scale-[0.98]"
        >
          <Mail className="w-4 h-4" />
          <span>Email ashutosh4tech@gmail.com</span>
        </a>
      </div>
    </div>
  );
}
