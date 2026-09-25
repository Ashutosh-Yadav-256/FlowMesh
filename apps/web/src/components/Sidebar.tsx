"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { FlowMeshBrand } from "@/components/FlowMeshLogo";
import { useState, useEffect } from "react";
import { getActiveTenantId, setActiveTenantId, postToApi } from "@/lib/api";
import {
  LayoutDashboard,
  Network,
  Workflow,
  PlayCircle,
  AlertTriangle,
  Cpu,
  Radio,
  FileText,
  Activity,
  Settings,
  Building2,
  Flame,
  ChevronDown,
  Check,
  RotateCcw,
  Sparkles,
  HelpCircle,
  Layers,
  Scale,
  Server,
  X,
} from "lucide-react";

const navItems = [
  { name: "Overview", href: "/", icon: LayoutDashboard },
  { name: "Enterprise Console", href: "/enterprise", icon: Server, badge: "Spring Boot" },
  { name: "Connections", href: "/connections", icon: Network },
  { name: "Workflows", href: "/workflows", icon: Workflow },
  { name: "Runs", href: "/runs", icon: PlayCircle },
  { name: "Incidents & DLQ", href: "/incidents", icon: AlertTriangle, badge: "1" },
  { name: "Edge Agents", href: "/agents", icon: Cpu, badge: "2 Active" },
  { name: "Events", href: "/events", icon: Radio },
  { name: "Audit Trail", href: "/audit", icon: FileText },
  { name: "Observability", href: "/observability", icon: Activity },
];

const bottomNavItems = [
  { name: "Settings & State", href: "/settings", icon: Settings },
  { name: "Organization", href: "/organization", icon: Building2 },
  { name: "Support & Help", href: "/support", icon: HelpCircle },
  { name: "UX States Gallery", href: "/states", icon: Layers },
  { name: "Legal & Policies", href: "/privacy", icon: Scale },
];

const workspaces = [
  {
    id: "tenant_acme",
    name: "Acme Global Corp",
    mode: "Client Demo",
    description: "Pre-seeded DAGs, connections & traces",
    badgeBg: "bg-[#F8EBE8] text-[#874436] border-[#EED1CB]",
    dotBg: "bg-[#874436]",
  },
  {
    id: "tenant_prod",
    name: "Production Workspace",
    mode: "Clean Slate",
    description: "Zero mock data · Production-ready",
    badgeBg: "bg-emerald-50 text-emerald-700 border-emerald-200",
    dotBg: "bg-emerald-600",
  },
];

export function Sidebar() {
  const pathname = usePathname();
  const [activeTenant, setActiveTenant] = useState("tenant_acme");
  const [dropdownOpen, setDropdownOpen] = useState(false);
  const [busy, setBusy] = useState(false);
  const [mobileOpen, setMobileOpen] = useState(false);

  useEffect(() => {
    setActiveTenant(getActiveTenantId());
    const handleTenantChanged = () => setActiveTenant(getActiveTenantId());
    const handleToggle = () => setMobileOpen((prev) => !prev);

    window.addEventListener("flowmesh:tenant_changed", handleTenantChanged);
    window.addEventListener("flowmesh:toggle_sidebar", handleToggle);
    return () => {
      window.removeEventListener("flowmesh:tenant_changed", handleTenantChanged);
      window.removeEventListener("flowmesh:toggle_sidebar", handleToggle);
    };
  }, []);

  useEffect(() => {
    setMobileOpen(false);
  }, [pathname]);

  const handleSelectWorkspace = (tenantId: string) => {
    if (tenantId === activeTenant) {
      setDropdownOpen(false);
      return;
    }
    setActiveTenantId(tenantId);
    setDropdownOpen(false);
    window.location.reload();
  };

  const handleSeedDemo = async () => {
    setBusy(true);
    await postToApi("/api/v1/demo/seed");
    setBusy(false);
    setDropdownOpen(false);
    window.location.reload();
  };

  const handleResetWorkspace = async () => {
    if (!confirm("Are you sure you want to reset this workspace to a clean state?")) return;
    setBusy(true);
    await postToApi("/api/v1/demo/reset");
    setBusy(false);
    setDropdownOpen(false);
    window.location.reload();
  };

  const currentWs = workspaces.find((w) => w.id === activeTenant) || workspaces[0];

  return (
    <>
      {mobileOpen && (
        <div
          className="fixed inset-0 z-40 bg-black/40 backdrop-blur-xs lg:hidden"
          onClick={() => setMobileOpen(false)}
        />
      )}
      <aside
        className={`w-64 bg-[#FAF8F5] border-r border-[#D5CABE] flex flex-col h-screen fixed left-0 top-0 z-50 select-none shadow-sm transition-transform duration-200 lg:translate-x-0 ${
          mobileOpen ? "translate-x-0" : "-translate-x-full lg:translate-x-0"
        }`}
      >
        <div className="h-16 flex items-center px-6 border-b border-[#D5CABE] justify-between">
          <Link href="/" className="group block" onClick={() => setMobileOpen(false)}>
            <FlowMeshBrand />
          </Link>
          <button
            onClick={() => setMobileOpen(false)}
            className="lg:hidden p-1.5 rounded-lg text-[#7A7165] hover:text-[#1B1B1B] hover:bg-[#F3EFEA]"
            title="Close Menu"
          >
            <X className="w-4 h-4" />
          </button>
        </div>

      <div className="px-3 py-2.5 border-b border-[#D5CABE] relative">
        <button
          onClick={() => setDropdownOpen(!dropdownOpen)}
          className="w-full bg-[#F3EFEA] hover:bg-[#EAE4DC] border border-[#D5CABE] rounded-lg p-2.5 flex items-center justify-between text-xs transition-colors shadow-sm text-left"
        >
          <div className="flex items-center gap-2 min-w-0">
            <span className={`w-2 h-2 rounded-full shrink-0 ${currentWs.dotBg}`} />
            <div className="truncate">
              <p className="font-bold text-[#1B1B1B] truncate text-xs">{currentWs.name}</p>
              <div className="flex items-center gap-1.5 mt-0.5">
                <span className={`text-[9px] font-semibold px-1.5 py-0.2 rounded border ${currentWs.badgeBg}`}>
                  {currentWs.mode}
                </span>
                <span className="text-[10px] text-[#968676] truncate font-mono">
                  {currentWs.id}
                </span>
              </div>
            </div>
          </div>
          <ChevronDown className={`w-3.5 h-3.5 text-[#968676] shrink-0 transition-transform duration-150 ${dropdownOpen ? "rotate-180" : ""}`} />
        </button>

        {dropdownOpen && (
          <>
            <div
              className="fixed inset-0 z-20"
              onClick={() => setDropdownOpen(false)}
            />
            <div className="absolute left-3 right-3 top-full mt-1.5 bg-[#FAF8F5] border border-[#D5CABE] rounded-xl shadow-xl z-30 p-2 space-y-1.5 animate-in fade-in duration-100">
              <div className="px-2 py-1 text-[10px] font-bold text-[#968676] uppercase tracking-wider">
                Select Workspace Mode
              </div>

              {workspaces.map((ws) => {
                const isSelected = ws.id === activeTenant;
                return (
                  <button
                    key={ws.id}
                    onClick={() => handleSelectWorkspace(ws.id)}
                    className={`w-full text-left p-2 rounded-lg border transition-all flex items-start justify-between text-xs ${
                      isSelected
                        ? "bg-[#F3EFEA] border-[#874436]/40 shadow-xs"
                        : "bg-white hover:bg-[#F8F5F0] border-[#E8DFD5]"
                    }`}
                  >
                    <div>
                      <div className="flex items-center gap-1.5">
                        <span className={`w-1.5 h-1.5 rounded-full ${ws.dotBg}`} />
                        <span className="font-bold text-[#1B1B1B] text-[11px]">{ws.name}</span>
                        <span className={`text-[9px] font-semibold px-1 rounded border ${ws.badgeBg}`}>
                          {ws.mode}
                        </span>
                      </div>
                      <p className="text-[10px] text-[#7A7165] mt-1 leading-tight">
                        {ws.description}
                      </p>
                    </div>
                    {isSelected && (
                      <Check className="w-3.5 h-3.5 text-[#874436] shrink-0 mt-0.5 ml-1" />
                    )}
                  </button>
                );
              })}

              <div className="pt-2 border-t border-[#E8DFD5] flex flex-col gap-1">
                {activeTenant === "tenant_acme" ? (
                  <button
                    disabled={busy}
                    onClick={handleSeedDemo}
                    className="w-full flex items-center justify-center gap-1.5 py-1.5 px-2 rounded-lg text-[10px] font-semibold bg-[#F8EBE8] hover:bg-[#F2DCD6] text-[#874436] border border-[#EED1CB] transition-colors"
                  >
                    <Sparkles className="w-3 h-3 text-[#874436]" />
                    {busy ? "Resetting Demo..." : "Re-seed Client Demo Data"}
                  </button>
                ) : (
                  <button
                    disabled={busy}
                    onClick={handleSeedDemo}
                    className="w-full flex items-center justify-center gap-1.5 py-1.5 px-2 rounded-lg text-[10px] font-semibold bg-emerald-50 hover:bg-emerald-100 text-emerald-700 border border-emerald-200 transition-colors"
                  >
                    <Sparkles className="w-3 h-3 text-emerald-600" />
                    {busy ? "Seeding..." : "Load Client Demo Showcase"}
                  </button>
                )}
                <button
                  disabled={busy}
                  onClick={handleResetWorkspace}
                  className="w-full flex items-center justify-center gap-1.5 py-1 px-2 rounded-lg text-[10px] text-[#968676] hover:text-[#874436] hover:bg-[#FDF6F5] transition-colors"
                >
                  <RotateCcw className="w-2.5 h-2.5" />
                  Reset to 0-Record Clean Slate
                </button>
              </div>
            </div>
          </>
        )}
      </div>

      <div className="flex-1 overflow-y-auto px-3 py-4 space-y-1">
        <div className="px-3 pb-2 text-[10px] font-bold uppercase tracking-wider text-[#968676]">
          Core Platform
        </div>
        {navItems.map((item) => {
          const isActive = item.href === "/" ? pathname === "/" : pathname.startsWith(item.href);
          const Icon = item.icon;
          return (
            <Link
              key={item.name}
              href={item.href}
              className={`flex items-center justify-between px-3 py-2 rounded-lg text-xs font-medium transition-all ${
                isActive
                  ? "bg-[#874436] text-white font-semibold shadow-sm"
                  : "text-[#4F4F4F] hover:text-[#1B1B1B] hover:bg-[#F3EFEA]"
              }`}
            >
              <div className="flex items-center gap-2.5">
                <Icon
                  className={`w-4 h-4 ${
                    isActive ? "text-white" : "text-[#968676]"
                  }`}
                />
                <span>{item.name}</span>
              </div>
              {item.badge && (
                <span
                  className={`text-[10px] px-1.5 py-0.2 rounded font-semibold ${
                    isActive
                      ? "bg-white/20 text-white"
                      : item.badge === "1"
                      ? "bg-[#FDF6F5] text-[#874436] border border-[#EED1CB]"
                      : "bg-[#F0F3FA] text-[#455CA1] border border-[#DFE6F5]"
                  }`}
                >
                  {item.badge}
                </span>
              )}
            </Link>
          );
        })}
      </div>

      <div className="px-4 py-2">
        <div className="p-2.5 rounded-lg bg-[#FEF7ED] border border-[#FDEED3] text-xs">
          <div className="flex items-center gap-1.5 text-[#E17709] font-semibold text-[11px] mb-1">
            <Flame className="w-3.5 h-3.5 text-[#E17709]" />
            RediForge Connected
          </div>
          <p className="text-[10px] text-[#4F4133] leading-tight">
            StateStore backend active. High-throughput distributed locks & circuit breaker.
          </p>
        </div>
      </div>

      <div className="p-3 border-t border-[#D5CABE] space-y-1">
        <button
          onClick={() => {
            if (typeof window !== "undefined") {
              window.dispatchEvent(new CustomEvent("flowmesh:open-onboarding"));
            }
          }}
          className="w-full flex items-center justify-between px-3 py-2 rounded-lg text-xs font-medium text-[#874436] hover:bg-[#F8EBE8] border border-[#EED1CB] bg-[#FDF6F5] transition-all shadow-xs group mb-1"
        >
          <div className="flex items-center gap-2">
            <Sparkles className="w-3.5 h-3.5 text-[#874436] group-hover:rotate-12 transition-transform" />
            <span className="font-semibold">Getting Started Tour</span>
          </div>
          <span className="text-[9px] font-semibold px-1.5 py-0.2 rounded bg-white/80 border border-[#EED1CB]">4 Steps</span>
        </button>
        {bottomNavItems.map((item) => {
          const isActive = pathname.startsWith(item.href);
          const Icon = item.icon;
          return (
            <Link
              key={item.name}
              href={item.href}
              className={`flex items-center gap-2.5 px-3 py-2 rounded-lg text-xs font-medium transition-all ${
                isActive
                  ? "bg-[#874436] text-white font-semibold shadow-sm"
                  : "text-[#4F4F4F] hover:text-[#1B1B1B] hover:bg-[#F3EFEA]"
              }`}
            >
              <Icon className={`w-4 h-4 ${isActive ? "text-white" : "text-[#968676]"}`} />
              <span>{item.name}</span>
            </Link>
          );
        })}
      </div>
    </aside>
    </>
  );
}
