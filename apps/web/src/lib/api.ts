const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

function generateRequestId(): string {
  if (typeof crypto !== "undefined" && typeof crypto.randomUUID === "function") {
    return crypto.randomUUID();
  }
  return "req_" + Math.random().toString(36).substring(2, 11);
}

export function getActiveTenantId(): string {
  if (typeof window !== "undefined") {
    return localStorage.getItem("flowmesh_active_tenant") || "tenant_acme";
  }
  return "tenant_acme";
}

export function setActiveTenantId(tenantId: string): void {
  if (typeof window !== "undefined") {
    localStorage.setItem("flowmesh_active_tenant", tenantId);
    window.dispatchEvent(new Event("flowmesh:tenant_changed"));
  }
}

export async function fetchFromApi<T>(endpoint: string, fallbackData: T): Promise<T> {
  try {
    const tenantId = getActiveTenantId();
    const requestId = generateRequestId();
    const res = await fetch(`${API_BASE_URL}${endpoint}`, {
      cache: "no-store",
      headers: {
        "Content-Type": "application/json",
        "X-Tenant-ID": tenantId,
        "X-Request-ID": requestId,
      },
    });
    if (!res.ok) {
      console.warn(`API error on ${endpoint} [${requestId}]: ${res.statusText}. Using fallback.`);
      return fallbackData;
    }
    return await res.json();
  } catch (err) {

    return fallbackData;
  }
}

export async function postToApi<T>(endpoint: string, body: any = {}): Promise<T | null> {
  try {
    const tenantId = getActiveTenantId();
    const requestId = generateRequestId();
    const res = await fetch(`${API_BASE_URL}${endpoint}`, {
      method: "POST",
      cache: "no-store",
      headers: {
        "Content-Type": "application/json",
        "X-Tenant-ID": tenantId,
        "X-Request-ID": requestId,
      },
      body: JSON.stringify(body),
    });
    if (!res.ok) {
      throw new Error(`API error ${res.status}: ${res.statusText} [request_id: ${requestId}]`);
    }
    return await res.json();
  } catch (err) {
    console.error(`POST error on ${endpoint}:`, err);
    return null;
  }
}

export async function deleteFromApi<T>(endpoint: string): Promise<T | null> {
  try {
    const tenantId = getActiveTenantId();
    const requestId = generateRequestId();
    const res = await fetch(`${API_BASE_URL}${endpoint}`, {
      method: "DELETE",
      cache: "no-store",
      headers: {
        "Content-Type": "application/json",
        "X-Tenant-ID": tenantId,
        "X-Request-ID": requestId,
      },
    });
    if (!res.ok) {
      throw new Error(`API error ${res.status}: ${res.statusText} [request_id: ${requestId}]`);
    }
    return await res.json();
  } catch (err) {
    console.error(`DELETE error on ${endpoint}:`, err);
    return null;
  }
}
