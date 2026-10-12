/** Calls to the AuthentiQ backend's admin endpoints. */

const raw = import.meta.env.VITE_API_URL as string | undefined;
// Unset -> local backend. Empty string -> same site (nginx proxies /api in deployment).
export const API_URL = (raw ?? "http://127.0.0.1:8000").replace(/\/+$/, "");

export class ApiError extends Error {
  constructor(
    message: string,
    public status: number,
  ) {
    super(message);
  }
}

function errorText(body: unknown, status: number): string {
  const detail = (body as { detail?: unknown } | null)?.detail;
  if (typeof detail === "string") return detail;
  if (Array.isArray(detail)) return detail.map((d: { msg?: string }) => d.msg).join("; ");
  return `The server answered with an error (${status}).`;
}

async function call(path: string, token: string | null, init: RequestInit = {}): Promise<Response> {
  const headers = new Headers(init.headers);
  if (token) headers.set("Authorization", `Bearer ${token}`);
  if (init.body && typeof init.body === "string") headers.set("Content-Type", "application/json");
  let res: Response;
  try {
    res = await fetch(`${API_URL}/api${path}`, { ...init, headers });
  } catch {
    throw new ApiError(`Cannot reach the AuthentiQ server at ${API_URL || "this site"}.`, 0);
  }
  if (!res.ok) {
    const body: unknown = await res.json().catch(() => null);
    throw new ApiError(errorText(body, res.status), res.status);
  }
  return res;
}

const json = async <T,>(path: string, token: string | null, init?: RequestInit) =>
  (await (await call(path, token, init)).json()) as T;

export type Status = "PENDING" | "APPROVED" | "REJECTED" | "SUSPENDED";

export type Manufacturer = {
  id: number;
  email: string | null;
  company_name: string;
  gstin: string;
  company_address: string;
  phone: string;
  verification_status: Status;
  verified_at: string | null;
  rejection_reason: string | null;
  created_at: string;
};

export type Issue = {
  id: number;
  product_id: string;
  message: string;
  contact: string | null;
  latitude: number | null;
  longitude: number | null;
  status: "OPEN" | "REVIEWED" | "CLOSED";
  created_at: string;
};

export type Product = {
  product_id: string;
  product_name: string;
  manufacturer_name: string;
  batch_number: string;
  sku: string | null;
  status: string;
  is_onchain: boolean;
  registration_block: number | null;
  registration_tx_hash: string | null;
  distributors: { name?: string | null; city?: string | null }[];
  created_at: string;
};

export type Stats = {
  total_scans: number;
  genuine_count: number;
  suspicious_count: number;
  counterfeit_count: number;
};

export type Health = {
  status: string;
  blockchain?: {
    status: string;
    contract_accessible: boolean;
    latest_block: number | null;
    chain_id?: number | null;
    wallet_balance_eth?: number | null;
  };
};

export async function login(email: string, password: string): Promise<string> {
  const r = await json<{ access_token: string; role: string }>("/auth/login", null, {
    method: "POST",
    body: JSON.stringify({ email, password }),
  });
  if (r.role !== "ADMIN") throw new ApiError("This account is not an admin account.", 403);
  return r.access_token;
}

export const me = (t: string) => json<{ email: string }>("/admin/me", t);
export const listManufacturers = (t: string) => json<Manufacturer[]>("/admin/manufacturers", t);
export const setStatus = (t: string, id: number, status: Status, rejection_reason?: string) =>
  json(`/admin/manufacturers/${id}/status`, t, {
    method: "PUT",
    body: JSON.stringify({ status, rejection_reason: rejection_reason || null }),
  });
export const listIssues = (t: string) => json<Issue[]>("/admin/issues", t);
export const setIssueStatus = (t: string, id: number, status: Issue["status"]) =>
  json(`/admin/issues/${id}/status`, t, { method: "PUT", body: JSON.stringify({ status }) });
export const listProducts = (t: string) => json<Product[]>("/products", t);
export const scanStats = (t: string) => json<Stats>("/scans/stats", t);
export const health = () => json<Health>("/health/blockchain", null);

/** The verification document (Aadhaar) as a blob URL the browser can show. */
export async function documentUrl(t: string, id: number): Promise<{ url: string; type: string }> {
  const res = await call(`/admin/manufacturers/${id}/document`, t);
  const blob = await res.blob();
  return { url: URL.createObjectURL(blob), type: blob.type };
}
