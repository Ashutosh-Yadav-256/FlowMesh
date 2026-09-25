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

export function getAuthToken(): string | null {
  if (typeof window !== "undefined") {
    return localStorage.getItem("flowmesh_token");
  }
  return null;
}

export function setAuthToken(token: string): void {
  if (typeof window !== "undefined") {
    localStorage.setItem("flowmesh_token", token);
  }
}

export function removeAuthToken(): void {
  if (typeof window !== "undefined") {
    localStorage.removeItem("flowmesh_token");
  }
}

function getRequestHeaders(): Record<string, string> {
  const headers: Record<string, string> = {
    "Content-Type": "application/json",
    "X-Tenant-ID": getActiveTenantId(),
    "X-Request-ID": generateRequestId(),
  };
  const token = getAuthToken();
  if (token) {
    headers["Authorization"] = `Bearer ${token}`;
  }
  return headers;
}

export async function fetchFromApi<T>(endpoint: string, fallbackData: T): Promise<T> {
  try {
    const headers = getRequestHeaders();
    const res = await fetch(`${API_BASE_URL}${endpoint}`, {
      cache: "no-store",
      headers,
    });
    if (res.status === 401 && typeof window !== "undefined") {
      window.dispatchEvent(new CustomEvent("flowmesh:session_expired"));
    }
    if (!res.ok) {
      console.warn(`API error ${res.status} on ${endpoint} [${headers["X-Request-ID"]}]: ${res.statusText}. Using fallback.`);
      return fallbackData;
    }
    return await res.json();
  } catch (err) {
    console.warn(`API network failure on ${endpoint}:`, err);
    return fallbackData;
  }
}

export async function postToApi<T>(endpoint: string, body: any = {}): Promise<T | null> {
  try {
    const headers = getRequestHeaders();
    const res = await fetch(`${API_BASE_URL}${endpoint}`, {
      method: "POST",
      cache: "no-store",
      headers,
      body: JSON.stringify(body),
    });
    if (res.status === 401 && typeof window !== "undefined") {
      window.dispatchEvent(new CustomEvent("flowmesh:session_expired"));
    }
    if (!res.ok) {
      const errText = await res.text().catch(() => "");
      throw new Error(`API error ${res.status}: ${res.statusText} - ${errText}`);
    }
    return await res.json();
  } catch (err) {
    console.error(`POST error on ${endpoint}:`, err);
    return null;
  }
}

export async function deleteFromApi<T>(endpoint: string): Promise<T | null> {
  try {
    const headers = getRequestHeaders();
    const res = await fetch(`${API_BASE_URL}${endpoint}`, {
      method: "DELETE",
      cache: "no-store",
      headers,
    });
    if (res.status === 401 && typeof window !== "undefined") {
      window.dispatchEvent(new CustomEvent("flowmesh:session_expired"));
    }
    if (!res.ok) {
      const errText = await res.text().catch(() => "");
      throw new Error(`API error ${res.status}: ${res.statusText} - ${errText}`);
    }
    return await res.json();
  } catch (err) {
    console.error(`DELETE error on ${endpoint}:`, err);
    return null;
  }
}

const WORKER_BASE_URL = process.env.NEXT_PUBLIC_WORKER_API_URL || "http://localhost:8082";

export async function fetchFromWorker<T>(endpoint: string, fallbackData: T): Promise<T> {
  try {
    const tenantId = getActiveTenantId();
    const requestId = generateRequestId();
    const res = await fetch(`${WORKER_BASE_URL}${endpoint}`, {
      cache: "no-store",
      headers: {
        "Content-Type": "application/json",
        "X-Tenant-ID": tenantId,
        "X-Request-ID": requestId,
      },
    });
    if (!res.ok) return fallbackData;
    return await res.json();
  } catch {
    return fallbackData;
  }
}

export async function postToWorker<T>(endpoint: string, body: any = {}): Promise<T | null> {
  try {
    const tenantId = getActiveTenantId();
    const requestId = generateRequestId();
    const res = await fetch(`${WORKER_BASE_URL}${endpoint}`, {
      method: "POST",
      cache: "no-store",
      headers: {
        "Content-Type": "application/json",
        "X-Tenant-ID": tenantId,
        "X-Request-ID": requestId,
      },
      body: JSON.stringify(body),
    });
    if (!res.ok) return null;
    return await res.json();
  } catch {
    return null;
  }
}

