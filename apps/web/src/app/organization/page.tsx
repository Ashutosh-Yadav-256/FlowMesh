"use client";

import { Building2, Users, Shield, Key, Plus } from "lucide-react";

export default function OrganizationPage() {
  return (
    <div className="space-y-6 max-w-5xl mx-auto text-xs">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-slate-900 flex items-center gap-2.5">
            Organization & Tenancy
            <span className="text-xs font-semibold text-slate-600 bg-slate-100 px-2 py-0.5 rounded border border-slate-200">
              Multi-Tenant Isolation
            </span>
          </h1>
          <p className="text-xs text-slate-500 mt-1">
            Manage organization members, RBAC roles (Owner, Operator, Developer, Viewer), and API access tokens.
          </p>
        </div>

        <button className="flex items-center gap-1.5 px-3.5 py-1.5 bg-indigo-600 hover:bg-indigo-700 text-white rounded-lg font-semibold shadow-sm transition-colors">
          <Plus className="w-3.5 h-3.5" />
          Invite Team Member
        </button>
      </div>

      <div className="p-6 rounded-xl bg-white border border-slate-200 space-y-4 shadow-sm">
        <h2 className="text-sm font-bold text-slate-900 uppercase tracking-wider flex items-center gap-2">
          <Building2 className="w-4 h-4 text-indigo-600" />
          Active Tenant Context
        </h2>
        <div className="grid grid-cols-3 gap-4">
          <div className="p-3.5 rounded-lg bg-slate-50 border border-slate-200">
            <span className="text-slate-500 text-[11px] font-medium">Organization Name</span>
            <p className="font-bold text-slate-900 text-sm mt-0.5">Acme Global Corporation</p>
          </div>
          <div className="p-3.5 rounded-lg bg-slate-50 border border-slate-200">
            <span className="text-slate-500 text-[11px] font-medium">Tenant Identifier</span>
            <p className="font-bold font-mono text-indigo-700 text-sm mt-0.5">tenant_acme</p>
          </div>
          <div className="p-3.5 rounded-lg bg-slate-50 border border-slate-200">
            <span className="text-slate-500 text-[11px] font-medium">Isolation Level</span>
            <p className="font-bold text-emerald-700 text-sm mt-0.5">Row-Level Security (RLS)</p>
          </div>
        </div>
      </div>

      <div className="rounded-xl bg-white border border-slate-200 overflow-hidden shadow-sm">
        <div className="p-4 border-b border-slate-100 flex items-center justify-between">
          <span className="font-bold text-slate-900 uppercase text-[11px] flex items-center gap-2">
            <Users className="w-4 h-4 text-indigo-600" />
            Members & Role Assignments
          </span>
          <span className="text-slate-500 font-medium">4 Active Members</span>
        </div>

        <table className="w-full text-left">
          <thead className="bg-slate-50 text-slate-500 uppercase tracking-wider text-[10px] border-b border-slate-200 font-semibold">
            <tr>
              <th className="py-3 px-4">User</th>
              <th className="py-3 px-4">Email</th>
              <th className="py-3 px-4">Role</th>
              <th className="py-3 px-4">Auth Source</th>
              <th className="py-3 px-4 text-right">Actions</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-100">
            {[
              { name: "Alex Mercer", email: "alex.mercer@acme.corp", role: "Owner", auth: "OIDC (Okta)" },
              { name: "Elena Rostova", email: "elena.rostova@acme.corp", role: "Operator", auth: "OIDC (Okta)" },
              { name: "Dev Team Lead", email: "dev.lead@acme.corp", role: "Developer", auth: "OIDC (Okta)" },
              { name: "Compliance Auditor", email: "auditor@acme.corp", role: "Viewer", auth: "OIDC (Okta)" },
            ].map((u) => (
              <tr key={u.email} className="hover:bg-slate-50/80 transition-colors">
                <td className="py-3 px-4 font-bold text-slate-900">{u.name}</td>
                <td className="py-3 px-4 text-slate-600 font-mono">{u.email}</td>
                <td className="py-3 px-4">
                  <span className="px-2 py-0.5 rounded font-bold text-[10px] bg-indigo-50 text-indigo-700 border border-indigo-200">
                    {u.role}
                  </span>
                </td>
                <td className="py-3 px-4 text-slate-500">{u.auth}</td>
                <td className="py-3 px-4 text-right">
                  <button className="text-slate-500 hover:text-slate-800 font-medium">Edit</button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
