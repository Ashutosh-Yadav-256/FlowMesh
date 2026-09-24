
import { getActiveTenantId } from "./api";

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export interface ApiResponse<T> {
  data: T | null;
  error: string | null;
  status: number;
  requestId: string;
}

export class ApiError extends Error {
  constructor(
    public status: number,
    public statusText: string,
    public requestId: string,
    public responseBody?: any
  ) {
    super(`API Error ${status} (${statusText}) [request_id: ${requestId}]`);
    this.name = "ApiError";
  }
}

function generateRequestId(): string {
  if (typeof crypto !== "undefined" && typeof crypto.randomUUID === "function") {
    return crypto.randomUUID();
  }
  return "req_" + Math.random().toString(36).substring(2, 11);
}

export async function request<T>(
  endpoint: string,
  options: RequestInit = {}
): Promise<ApiResponse<T>> {
  const requestId = generateRequestId();
  const tenantId = getActiveTenantId();

  const headers = new Headers(options.headers || {});
  if (!headers.has("Content-Type") && options.body) {
    headers.set("Content-Type", "application/json");
  }
  headers.set("X-Tenant-ID", tenantId);
  headers.set("X-Request-ID", requestId);

  try {
    const res = await fetch(`${API_BASE_URL}${endpoint}`, {
      ...options,
      headers,
    });

    let data: T | null = null;
    let error: string | null = null;

    if (res.status !== 204) {
      try {
        const json = await res.json();
        if (res.ok) {
          data = json;
        } else {
          error = json.message || json.detail || res.statusText;
        }
      } catch {
        error = res.ok ? null : res.statusText;
      }
    }

    return {
      data,
      error,
      status: res.status,
      requestId,
    };
  } catch (err: any) {
    return {
      data: null,
      error: err.message || "Network request failed",
      status: 0,
      requestId,
    };
  }
}

export const apiClient = {
  get: <T>(url: string, init?: RequestInit) => request<T>(url, { ...init, method: "GET" }),
  post: <T>(url: string, body?: any, init?: RequestInit) =>
    request<T>(url, { ...init, method: "POST", body: body ? JSON.stringify(body) : undefined }),
  put: <T>(url: string, body?: any, init?: RequestInit) =>
    request<T>(url, { ...init, method: "PUT", body: body ? JSON.stringify(body) : undefined }),
  patch: <T>(url: string, body?: any, init?: RequestInit) =>
    request<T>(url, { ...init, method: "PATCH", body: body ? JSON.stringify(body) : undefined }),
  delete: <T>(url: string, init?: RequestInit) => request<T>(url, { ...init, method: "DELETE" }),
};
