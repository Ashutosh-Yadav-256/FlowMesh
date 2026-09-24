"use client";

import { useState, useEffect } from "react";
import { Search, Terminal, ExternalLink, Command } from "lucide-react";
import { SearchModal } from "./SearchModal";

export function Header() {
  const [isSearchOpen, setIsSearchOpen] = useState(false);

  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if ((e.metaKey || e.ctrlKey) && e.key.toLowerCase() === "k") {
        e.preventDefault();
        setIsSearchOpen((prev) => !prev);
      }
    };
    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, []);

  return (
    <>
      <header className="h-16 bg-[#FAF8F5]/95 backdrop-blur-md border-b border-[#D5CABE] flex items-center justify-between px-8 sticky top-0 z-30 ml-64 shadow-sm">

        <div className="flex items-center gap-6 w-[420px]">
          <div
            onClick={() => setIsSearchOpen(true)}
            onFocus={() => setIsSearchOpen(true)}
            className="relative w-full cursor-pointer group"
          >
            <Search className="w-4 h-4 text-[#968676] group-hover:text-[#874436] absolute left-3 top-1/2 -translate-y-1/2 transition-colors" />
            <input
              type="text"
              readOnly
              onClick={() => setIsSearchOpen(true)}
              onFocus={() => setIsSearchOpen(true)}
              onKeyDown={() => setIsSearchOpen(true)}
              placeholder="Search workflows, runs, events, connections..."
              className="w-full bg-[#F3EFEA] group-hover:bg-[#FAF8F5] border border-[#D5CABE] group-hover:border-[#874436] rounded-lg pl-9 pr-14 py-1.5 text-xs text-[#1B1B1B] placeholder-[#968676] cursor-pointer transition-all shadow-inner"
            />
            <div className="absolute right-2.5 top-1/2 -translate-y-1/2 flex items-center gap-0.5 px-1.5 py-0.5 rounded bg-[#E7E0D6] border border-[#D5CABE] text-[10px] text-[#6B5E51] font-mono shadow-xs">
              <Command className="w-2.5 h-2.5" />
              <span>K</span>
            </div>
          </div>
        </div>

        <div className="hidden lg:flex items-center gap-2 text-[10px] font-bold uppercase tracking-widest text-[#874436]">
          <span>FLOWMESH PLATFORM</span>
          <span className="text-[#D5CABE]">·</span>
          <span className="text-[#968676]">ENTERPRISE WORKFLOW</span>
        </div>

        <div className="flex items-center gap-4">
          <div className="flex items-center gap-2 bg-[#F0F5F2] border border-[#D1E2D8] px-3 py-1 rounded-full text-xs text-[#2E6B47]">
            <span className="w-2 h-2 rounded-full bg-[#2E6B47]"></span>
            <span className="font-semibold text-[11px]">Control Plane 99.9%</span>
          </div>

          <div className="flex items-center gap-2 bg-[#F0F3FA] border border-[#DFE6F5] px-3 py-1 rounded-full text-xs text-[#455CA1]">
            <span className="w-2 h-2 rounded-full bg-[#455CA1]"></span>
            <span className="font-semibold text-[11px]">NATS JetStream</span>
          </div>

          <a
            href="http://localhost:8000/docs"
            target="_blank"
            rel="noreferrer"
            className="flex items-center gap-1.5 text-xs text-[#4F4F4F] hover:text-[#1B1B1B] transition-colors px-2.5 py-1.5 rounded-lg border border-[#D5CABE] hover:bg-[#F3EFEA] bg-[#FAF8F5]"
          >
            <Terminal className="w-3.5 h-3.5 text-[#968676]" />
            <span className="font-medium">Swagger</span>
            <ExternalLink className="w-3 h-3 text-[#B8A99A]" />
          </a>

          <div className="h-4 w-[1px] bg-[#D5CABE]"></div>

          <div className="w-8 h-8 rounded-full bg-[#1B1B1B] flex items-center justify-center text-xs font-semibold text-white shadow-sm">
            AG
          </div>
        </div>
      </header>

      <SearchModal isOpen={isSearchOpen} onClose={() => setIsSearchOpen(false)} />
    </>
  );
}
