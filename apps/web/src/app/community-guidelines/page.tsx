"use client";

import React from "react";
import { LegalLayout } from "@/components/legal/LegalLayout";
import { Users, Heart, ShieldCheck, MessageSquare, Mail } from "lucide-react";

export default function CommunityGuidelinesPage() {
  return (
    <LegalLayout
      title="Community Guidelines"
      subtitle="Code of Conduct, Collaborative Standards & Open-Source Community Norms."
      lastUpdated="September 24, 2026"
    >
      <div className="space-y-6">
        <section className="space-y-3">
          <h2 className="text-xl font-bold text-[#1B1B1B] tracking-tight flex items-center gap-2">
            <Heart className="w-5 h-5 text-[#874436]" />
            1. Our Pledge
          </h2>
          <p>
            We as members, contributors, and maintainers of the FlowMesh open-source ecosystem pledge to make participation in our project and our community a harassment-free experience for everyone, regardless of age, body size, visible or invisible disability, ethnicity, gender identity, level of experience, education, nationality, personal appearance, race, religion, or sexual identity.
          </p>
        </section>

        <section className="space-y-3">
          <h2 className="text-xl font-bold text-[#1B1B1B] tracking-tight flex items-center gap-2">
            <Users className="w-5 h-5 text-[#874436]" />
            2. Expected Standards of Conduct
          </h2>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-xs">
            <div className="p-4 rounded-xl bg-[#F4EFEB] border border-[#E3D9CE] space-y-1.5">
              <span className="font-bold text-[#1B1B1B] block">Empathetic Technical Discourse</span>
              <p className="text-[#5C5C5C]">
                Focus on constructive criticism during pull request reviews. Disagree with code designs respectfully without personal attacks.
              </p>
            </div>
            <div className="p-4 rounded-xl bg-[#F4EFEB] border border-[#E3D9CE] space-y-1.5">
              <span className="font-bold text-[#1B1B1B] block">Inclusivity in Documentation</span>
              <p className="text-[#5C5C5C]">
                Use gender-neutral language, accessible code examples, and clear architectural diagrams that welcome junior and senior contributors alike.
              </p>
            </div>
            <div className="p-4 rounded-xl bg-[#F4EFEB] border border-[#E3D9CE] space-y-1.5">
              <span className="font-bold text-[#1B1B1B] block">Responsible Testing</span>
              <p className="text-[#5C5C5C]">
                Ensure PRs provide comprehensive unit tests, respect SonarQube quality gates, and avoid committing mock credentials or API keys.
              </p>
            </div>
            <div className="p-4 rounded-xl bg-[#F4EFEB] border border-[#E3D9CE] space-y-1.5">
              <span className="font-bold text-[#1B1B1B] block">Community Mentorship</span>
              <p className="text-[#5C5C5C]">
                Help newcomers navigate our monorepo architecture, Go edge daemons, and Java Spring Boot enterprise workers.
              </p>
            </div>
          </div>
        </section>

        <section className="space-y-3 pt-4 border-t border-[#EAE2D8]">
          <h2 className="text-xl font-bold text-[#1B1B1B] tracking-tight flex items-center gap-2">
            <Mail className="w-5 h-5 text-[#874436]" />
            3. Reporting & Enforcement
          </h2>
          <p>
            Instances of abusive, harassing, or otherwise unacceptable behavior may be reported to the community conduct committee by contacting our lead maintainer directly:
          </p>
          <div className="bg-[#FAF8F5] border border-[#D5CABE] rounded-xl p-4 flex items-center justify-between">
            <span className="text-xs font-semibold text-[#1B1B1B]">Conduct Lead:</span>
            <a
              href="mailto:ashutosh4tech@gmail.com?subject=Code%20of%20Conduct%20Report"
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
