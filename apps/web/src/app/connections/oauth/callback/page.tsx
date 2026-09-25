"use client";

import { useEffect, useState, Suspense } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import { CheckCircle2, AlertCircle, RotateCw, ExternalLink, ShieldCheck, ArrowLeft } from "lucide-react";
import { postToApi } from "@/lib/api";

function OAuthCallbackContent() {
  const router = useRouter();
  const searchParams = useSearchParams();

  const [status, setStatus] = useState<"processing" | "success" | "error">("processing");
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [connectionDetails, setConnectionDetails] = useState<any>(null);
  const [providerName, setProviderName] = useState<string>("External Service");

  useEffect(() => {
    async function handleExchange() {
      const code = searchParams.get("code");
      const state = searchParams.get("state");
      const oauthError = searchParams.get("error");
      const oauthErrorDesc = searchParams.get("error_description");

      // Check if external provider returned an OAuth error
      if (oauthError) {
        setStatus("error");
        setErrorMessage(
          oauthErrorDesc || `Authentication failed with error code: ${oauthError}`
        );
        return;
      }

      if (!code) {
        setStatus("error");
        setErrorMessage("No authorization code received from the external login provider.");
        return;
      }

      // Retrieve pending connection context from sessionStorage
      let pendingData: any = null;
      try {
        const raw = sessionStorage.getItem("flowmesh_pending_oauth");
        if (raw) {
          pendingData = JSON.parse(raw);
        }
      } catch (e) {
        console.warn("Failed to parse pending OAuth session state", e);
      }

      const provider = pendingData?.provider || searchParams.get("provider") || "stripe";
      const connectionName = pendingData?.name || `${provider.toUpperCase()} Production Connection`;
      const agentId = pendingData?.agent_id || null;
      setProviderName(provider.toUpperCase());

      // CSRF State validation
      if (pendingData?.state && state && pendingData.state !== state) {
        setStatus("error");
        setErrorMessage("CSRF state mismatch. The authorization response may have been forged or intercepted.");
        return;
      }

      try {
        // Exchange authorization code server-to-server with FlowMesh backend
        const res = await postToApi<{
          id: string;
          name: string;
          type: string;
          status: string;
          created_at: string;
        }>("/api/v1/connections/oauth/exchange", {
          provider,
          name: connectionName,
          auth_code: code,
          account_id: searchParams.get("account_id") || undefined,
          agent_id: agentId,
          environment: pendingData?.environment || "production",
        });

        if (res && res.id) {
          // Clear session storage
          sessionStorage.removeItem("flowmesh_pending_oauth");
          setConnectionDetails(res);
          setStatus("success");

          // Auto-redirect to connections dashboard after 3 seconds
          setTimeout(() => {
            router.push(`/connections?authenticated=1&provider=${provider}`);
          }, 3000);
        } else {
          setStatus("error");
          setErrorMessage("Backend failed to exchange OAuth authorization code into an encrypted connection.");
        }
      } catch (err: any) {
        setStatus("error");
        setErrorMessage(err.message || "Failed to complete official OAuth handshake with backend.");
      }
    }

    handleExchange();
  }, [searchParams, router]);

  return (
    <div className="min-h-[70vh] flex items-center justify-center p-4">
      <div className="w-full max-w-lg bg-[#FAF8F5] border border-[#D5CABE] rounded-2xl shadow-xl p-8 space-y-6">
        {status === "processing" && (
          <div className="text-center space-y-4">
            <div className="w-14 h-14 mx-auto rounded-2xl bg-[#F8EBE8] border border-[#EED1CB] flex items-center justify-center text-[#874436]">
              <RotateCw className="w-7 h-7 animate-spin" />
            </div>
            <div>
              <h2 className="text-lg font-bold text-[#1B1B1B]">
                Completing Official {providerName} Authorization
              </h2>
              <p className="text-xs text-[#7A7165] mt-1 max-w-sm mx-auto">
                FlowMesh is verifying your external OAuth authorization code and establishing envelope encryption with master keys.
              </p>
            </div>
            <div className="p-3 bg-white border border-[#D5CABE] rounded-xl text-left font-mono text-[11px] text-[#7A7165] space-y-1">
              <div className="flex justify-between">
                <span>Phase:</span>
                <span className="text-[#874436] font-semibold">Exchanging Authorization Code</span>
              </div>
              <div className="flex justify-between">
                <span>Encryption:</span>
                <span className="text-[#2E6B47] font-semibold">AES-256-GCM Envelope Active</span>
              </div>
            </div>
          </div>
        )}

        {status === "success" && (
          <div className="text-center space-y-4">
            <div className="w-14 h-14 mx-auto rounded-2xl bg-emerald-50 border border-emerald-200 flex items-center justify-center text-emerald-600">
              <CheckCircle2 className="w-8 h-8" />
            </div>
            <div>
              <h2 className="text-lg font-bold text-slate-900">
                Official Authentication Established
              </h2>
              <p className="text-xs text-slate-600 mt-1 max-w-sm mx-auto">
                Your connection to <strong>{providerName}</strong> has been successfully authorized directly via the official service.
              </p>
            </div>
            {connectionDetails && (
              <div className="p-4 bg-white border border-emerald-200 rounded-xl text-left font-mono text-xs text-slate-700 space-y-1.5">
                <div className="flex justify-between">
                  <span>Connection ID:</span>
                  <span className="font-bold text-slate-900">{connectionDetails.id}</span>
                </div>
                <div className="flex justify-between">
                  <span>Name:</span>
                  <span className="font-bold text-slate-900">{connectionDetails.name}</span>
                </div>
                <div className="flex justify-between">
                  <span>Provider:</span>
                  <span className="text-emerald-700 uppercase font-bold">{connectionDetails.type}</span>
                </div>
                <div className="flex justify-between">
                  <span>Status:</span>
                  <span className="px-2 py-0.5 rounded text-[10px] bg-emerald-100 text-emerald-800 font-bold uppercase">
                    {connectionDetails.status}
                  </span>
                </div>
              </div>
            )}
            <div className="pt-2">
              <button
                onClick={() => router.push("/connections")}
                className="w-full py-2.5 bg-[#874436] hover:bg-[#6E362A] text-white rounded-lg text-xs font-semibold shadow-sm transition-colors"
              >
                Return to Connections Console
              </button>
              <p className="text-[10px] text-slate-400 mt-2">Redirecting automatically in 3 seconds...</p>
            </div>
          </div>
        )}

        {status === "error" && (
          <div className="text-center space-y-4">
            <div className="w-14 h-14 mx-auto rounded-2xl bg-rose-50 border border-rose-200 flex items-center justify-center text-rose-600">
              <AlertCircle className="w-8 h-8" />
            </div>
            <div>
              <h2 className="text-lg font-bold text-slate-900">
                Official Authorization Failed
              </h2>
              <p className="text-xs text-rose-700 mt-1 max-w-sm mx-auto">
                {errorMessage || "The external service declined the authorization request or the code expired."}
              </p>
            </div>
            <div className="pt-2 flex gap-3">
              <button
                onClick={() => router.push("/connections")}
                className="w-full py-2.5 bg-slate-100 hover:bg-slate-200 text-slate-800 rounded-lg text-xs font-semibold flex items-center justify-center gap-1.5 transition-colors"
              >
                <ArrowLeft className="w-4 h-4" />
                Back to Connections
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

export default function OAuthCallbackPage() {
  return (
    <Suspense
      fallback={
        <div className="min-h-[70vh] flex items-center justify-center">
          <div className="text-center space-y-2">
            <RotateCw className="w-6 h-6 animate-spin text-[#874436] mx-auto" />
            <p className="text-xs text-[#7A7165]">Loading OAuth state...</p>
          </div>
        </div>
      }
    >
      <OAuthCallbackContent />
    </Suspense>
  );
}
