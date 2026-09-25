"use client";

import { useState, useEffect } from "react";
import { Building2, Users, Shield, Key, Plus, Trash2, CheckCircle2, Copy } from "lucide-react";
import { fetchFromApi, postToApi, deleteFromApi, getActiveTenantId } from "@/lib/api";

export default function OrganizationPage() {
  const [tenant, setTenant] = useState<any>({
    id: "tenant_acme",
    name: "Acme Global Corporation",
    role: "owner",
  });
  const [apiKeys, setApiKeys] = useState<any[]>([]);
  const [showKeyModal, setShowKeyModal] = useState(false);
  const [newKeyName, setNewKeyName] = useState("");
  const [newKeyRole, setNewKeyRole] = useState("developer");
  const [generatedSecret, setGeneratedSecret] = useState<string | null>(null);
  const [copied, setCopied] = useState(false);

  const loadData = async () => {
    const tData = await fetchFromApi<any>("/api/v1/tenants/current", {
      id: getActiveTenantId(),
      name: "Active Workspace",
      role: "owner",
    });
    if (tData) setTenant(tData);

    const keys = await fetchFromApi<any[]>("/api/v1/api-keys", []);
    if (keys) setApiKeys(keys);
  };

  useEffect(() => {
    loadData();
    window.addEventListener("flowmesh:tenant_changed", loadData);
    return () => window.removeEventListener("flowmesh:tenant_changed", loadData);
  }, []);

  const handleCreateKey = async () => {
    if (!newKeyName.trim()) return;
    const res = await postToApi<any>("/api/v1/api-keys", {
      name: newKeyName.trim(),
      role: newKeyRole,
    });
    if (res?.secret_key) {
      setGeneratedSecret(res.secret_key);
      await loadData();
    }
  };

  const handleRevokeKey = async (id: string) => {
    if (!confirm("Are you sure you want to revoke this API key?")) return;
    await deleteFromApi(`/api/v1/api-keys/${id}`);
    await loadData();
  };

  const handleCopySecret = () => {
    if (!generatedSecret) return;
    navigator.clipboard.writeText(generatedSecret);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <div className="space-y-6 max-w-5xl mx-auto text-xs pb-12">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-slate-900 flex items-center gap-2.5">
            Organization & Tenancy
            <span className="text-xs font-semibold text-slate-600 bg-slate-100 px-2 py-0.5 rounded border border-slate-200">
              Multi-Tenant Isolation
            </span>
          </h1>
          <p className="text-xs text-slate-500 mt-1">
            Manage organization members, RBAC roles, and automated CI/CD API access keys.
          </p>
        </div>

        <button
          onClick={() => {
            setShowKeyModal(true);
            setGeneratedSecret(null);
            setNewKeyName("");
          }}
          className="flex items-center gap-1.5 px-3.5 py-1.5 bg-indigo-600 hover:bg-indigo-700 text-white rounded-lg font-semibold shadow-sm transition-colors"
        >
          <Key className="w-3.5 h-3.5" />
          Generate API Key
        </button>
      </div>

      <div className="p-6 rounded-xl bg-white border border-slate-200 space-y-4 shadow-sm">
        <h2 className="text-sm font-bold text-slate-900 uppercase tracking-wider flex items-center gap-2">
          <Building2 className="w-4 h-4 text-indigo-600" />
          Active Tenant Context
        </h2>
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
          <div className="p-3.5 rounded-lg bg-slate-50 border border-slate-200">
            <span className="text-slate-500 text-[11px] font-medium">Organization Name</span>
            <p className="font-bold text-slate-900 text-sm mt-0.5">{tenant.name}</p>
          </div>
          <div className="p-3.5 rounded-lg bg-slate-50 border border-slate-200">
            <span className="text-slate-500 text-[11px] font-medium">Tenant Identifier</span>
            <p className="font-bold font-mono text-indigo-700 text-sm mt-0.5">{tenant.id}</p>
          </div>
          <div className="p-3.5 rounded-lg bg-slate-50 border border-slate-200">
            <span className="text-slate-500 text-[11px] font-medium">Your Role</span>
            <p className="font-bold text-emerald-700 text-sm mt-0.5 capitalize">{tenant.role}</p>
          </div>
        </div>
      </div>

      {/* API Keys Table */}
      <div className="rounded-xl bg-white border border-slate-200 overflow-hidden shadow-sm">
        <div className="p-4 border-b border-slate-100 flex items-center justify-between">
          <span className="font-bold text-slate-900 uppercase text-[11px] flex items-center gap-2">
            <Key className="w-4 h-4 text-indigo-600" />
            Active API Keys ({apiKeys.length})
          </span>
          <span className="text-slate-500">Automated Pipeline Keys</span>
        </div>

        {apiKeys.length === 0 ? (
          <div className="p-6 text-center text-slate-500">
            No API keys issued for this workspace. Click &quot;Generate API Key&quot; to issue a pipeline secret.
          </div>
        ) : (
          <table className="w-full text-left">
            <thead className="bg-slate-50 text-slate-500 uppercase tracking-wider text-[10px] border-b border-slate-200 font-semibold">
              <tr>
                <th className="py-3 px-4">Key Name</th>
                <th className="py-3 px-4">Prefix</th>
                <th className="py-3 px-4">Role</th>
                <th className="py-3 px-4">Created</th>
                <th className="py-3 px-4 text-right">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {apiKeys.map((k) => (
                <tr key={k.id} className="hover:bg-slate-50/80 transition-colors">
                  <td className="py-3 px-4 font-bold text-slate-900">{k.name}</td>
                  <td className="py-3 px-4 font-mono text-indigo-700">{k.key_prefix}...</td>
                  <td className="py-3 px-4">
                    <span className="px-2 py-0.5 rounded font-bold text-[10px] bg-indigo-50 text-indigo-700 border border-indigo-200 uppercase">
                      {k.role}
                    </span>
                  </td>
                  <td className="py-3 px-4 text-slate-500 font-mono">
                    {k.created_at ? new Date(k.created_at).toLocaleDateString() : ""}
                  </td>
                  <td className="py-3 px-4 text-right">
                    <button
                      onClick={() => handleRevokeKey(k.id)}
                      className="text-rose-600 hover:text-rose-800 font-medium inline-flex items-center gap-1"
                    >
                      <Trash2 className="w-3 h-3" /> Revoke
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>

      {/* Members Section */}
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

      {/* Generate API Key Modal */}
      {showKeyModal && (
        <div className="fixed inset-0 z-50 bg-slate-900/40 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="w-full max-w-md bg-white border border-slate-200 rounded-2xl p-6 space-y-4 shadow-2xl">
            <h3 className="text-base font-bold text-slate-900 flex items-center gap-2">
              <Key className="w-4 h-4 text-indigo-600" />
              Generate API Token
            </h3>

            {generatedSecret ? (
              <div className="space-y-3">
                <div className="p-3 bg-emerald-50 border border-emerald-200 rounded-lg text-emerald-800 text-xs">
                  Make sure to copy your API key now. You won&apos;t be able to see it again!
                </div>
                <div className="p-3 bg-slate-900 text-emerald-400 font-mono text-xs rounded-lg flex items-center justify-between">
                  <span className="truncate mr-2">{generatedSecret}</span>
                  <button
                    onClick={handleCopySecret}
                    className="p-1.5 bg-slate-800 hover:bg-slate-700 text-white rounded transition-colors"
                  >
                    {copied ? <CheckCircle2 className="w-4 h-4 text-emerald-400" /> : <Copy className="w-4 h-4" />}
                  </button>
                </div>
                <div className="flex justify-end pt-2">
                  <button
                    onClick={() => setShowKeyModal(false)}
                    className="px-4 py-2 bg-slate-800 hover:bg-slate-700 text-white rounded-lg text-xs font-semibold"
                  >
                    Close
                  </button>
                </div>
              </div>
            ) : (
              <div className="space-y-4">
                <div>
                  <label className="block text-slate-700 font-semibold mb-1">Key Name</label>
                  <input
                    type="text"
                    value={newKeyName}
                    onChange={(e) => setNewKeyName(e.target.value)}
                    placeholder="e.g. GitHub Actions CI Deployer"
                    className="w-full border border-slate-200 rounded-lg p-2 text-slate-900 focus:outline-none focus:border-indigo-500"
                  />
                </div>
                <div>
                  <label className="block text-slate-700 font-semibold mb-1">Role</label>
                  <select
                    value={newKeyRole}
                    onChange={(e) => setNewKeyRole(e.target.value)}
                    className="w-full border border-slate-200 rounded-lg p-2 text-slate-900 focus:outline-none focus:border-indigo-500"
                  >
                    <option value="developer">Developer</option>
                    <option value="operator">Operator</option>
                    <option value="viewer">Viewer</option>
                    <option value="owner">Owner</option>
                  </select>
                </div>
                <div className="flex justify-end gap-2 pt-2">
                  <button
                    onClick={() => setShowKeyModal(false)}
                    className="px-4 py-2 bg-slate-100 hover:bg-slate-200 text-slate-700 rounded-lg text-xs font-semibold"
                  >
                    Cancel
                  </button>
                  <button
                    onClick={handleCreateKey}
                    className="px-4 py-2 bg-indigo-600 hover:bg-indigo-700 text-white rounded-lg text-xs font-semibold"
                  >
                    Generate Key
                  </button>
                </div>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
