"use client";

import React from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import {
  Shield,
  FileText,
  Cookie,
  Sliders,
  AlertCircle,
  Eye,
  Database,
  CheckSquare,
  Lock,
  Bug,
  Users,
  Printer,
  Mail,
  Scale,
} from "lucide-react";

interface LegalLayoutProps {
  title: string;
  subtitle: string;
  lastUpdated?: string;
  children: React.ReactNode;
}

const legalNav = [
  { name: "Privacy Policy", href: "/privacy", icon: Shield },
  { name: "Terms of Service", href: "/terms", icon: Scale },
  { name: "Cookie Policy", href: "/cookies", icon: Cookie },
  { name: "Cookie Preferences", href: "/cookie-preferences", icon: Sliders },
  { name: "Disclaimer", href: "/disclaimer", icon: AlertCircle },
  { name: "Accessibility Statement", href: "/accessibility", icon: Eye },
  { name: "Data Processing Agreement", href: "/dpa", icon: Database },
  { name: "Acceptable Use Policy", href: "/acceptable-use", icon: CheckSquare },
  { name: "Security Policy", href: "/security-policy", icon: Lock },
  { name: "Responsible Disclosure", href: "/responsible-disclosure", icon: Bug },
  { name: "Community Guidelines", href: "/community-guidelines", icon: Users },
];

export function LegalLayout({
  title,
  subtitle,
  lastUpdated = "September 24, 2026",
  children,
}: LegalLayoutProps) {
  const pathname = usePathname();

  const handlePrint = () => {
    window.print();
  };

  return (
    <div className="max-w-7xl mx-auto space-y-8 pb-16">
      {}
      <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4 pb-6 border-b border-[#D5CABE]">
        <div>
          <div className="flex items-center gap-2 text-xs font-semibold text-[#874436] uppercase tracking-wider mb-1">
            <Scale className="w-4 h-4" />
            <span>Legal, Trust & Compliance Center</span>
          </div>
          <h1 className="text-3xl sm:text-4xl font-black text-[#1B1B1B] tracking-tight">
            {title}
          </h1>
          <p className="text-sm text-[#5C5C5C] mt-1 max-w-2xl">{subtitle}</p>
        </div>

        <div className="flex flex-wrap items-center gap-3">
          <button
            onClick={handlePrint}
            className="inline-flex items-center gap-2 px-3.5 py-2 rounded-xl bg-[#FAF8F5] hover:bg-[#F0EBE4] border border-[#D5CABE] text-[#1B1B1B] text-xs font-semibold transition-all shadow-sm active:scale-[0.98]"
          >
            <Printer className="w-3.5 h-3.5 text-[#874436]" />
            <span>Print Document</span>
          </button>

          <a
            href="mailto:ashutosh4tech@gmail.com?subject=Legal%20Inquiry%20FlowMesh"
            className="inline-flex items-center gap-2 px-3.5 py-2 rounded-xl bg-[#874436] hover:bg-[#6E3529] text-white text-xs font-semibold transition-all shadow-sm active:scale-[0.98]"
          >
            <Mail className="w-3.5 h-3.5" />
            <span>Legal Contact</span>
          </a>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-12 gap-8 items-start">
        {}
        <aside className="lg:col-span-3 sticky top-6 space-y-4">
          <div className="bg-[#FAF8F5] border border-[#D5CABE] rounded-2xl p-3.5 shadow-sm space-y-1">
            <span className="text-[10px] font-bold text-[#968676] uppercase tracking-widest px-3 py-1 block">
              Policies & Agreements
            </span>
            {legalNav.map((item) => {
              const Icon = item.icon;
              const isActive = pathname === item.href;
              return (
                <Link
                  key={item.name}
                  href={item.href}
                  className={`flex items-center gap-2.5 px-3 py-2 rounded-xl text-xs font-medium transition-all ${
                    isActive
                      ? "bg-[#874436] text-white font-semibold shadow-sm"
                      : "text-[#5C5C5C] hover:text-[#1B1B1B] hover:bg-[#F0EBE4]"
                  }`}
                >
                  <Icon className={`w-3.5 h-3.5 ${isActive ? "text-white" : "text-[#968676]"}`} />
                  <span>{item.name}</span>
                </Link>
              );
            })}
          </div>

          {}
          <div className="bg-[#FAF8F5] border border-[#D5CABE] rounded-2xl p-4 shadow-sm space-y-2">
            <span className="text-[10px] font-bold text-[#874436] uppercase tracking-widest block">
              Data Protection & Compliance
            </span>
            <p className="text-[11px] text-[#5C5C5C] leading-relaxed">
              For privacy notices, DPA executions, or GDPR/CCPA data subject requests:
            </p>
            <a
              href="mailto:ashutosh4tech@gmail.com"
              className="text-xs font-mono font-bold text-[#874436] hover:underline block break-all"
            >
              ashutosh4tech@gmail.com
            </a>
            <div className="pt-2 border-t border-[#EAE2D8] flex items-center justify-between text-[10px] text-[#968676]">
              <span>Last Version: 2.4.0</span>
              <span>{lastUpdated}</span>
            </div>
          </div>
        </aside>

        {}
        <div className="lg:col-span-9 bg-[#FAF8F5] border border-[#D5CABE] rounded-2xl p-6 sm:p-10 shadow-sm text-sm text-[#333] space-y-6 leading-relaxed">
          {children}
        </div>
      </div>
    </div>
  );
}
