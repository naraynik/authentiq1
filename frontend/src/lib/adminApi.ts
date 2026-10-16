/** Calls for the AuthentiQ team's console (opens after an ADMIN account logs in). */
import { API_URL, ApiError, request } from "@/lib/api";
import { PREVIEW, previewDocument } from "@/lib/preview";

export type MfrStatus = "PENDING" | "APPROVED" | "REJECTED" | "SUSPENDED";

export type Manufacturer = {
  id: number;
  email: string | null;
  company_name: string;
  gstin: string;
  company_address: string;
  phone: string;
  verification_status: MfrStatus;
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

export type AuditEntry = {
  id: number;
  user_email: string | null;
  action: string;
  entity_type: string;
  entity_id: string | null;
  description: string | null;
  ip_address: string | null;
  created_at: string;
};

export type ChainHealth = {
  blockchain?: {
    contract_accessible: boolean;
    latest_block: number | null;
    wallet_balance_eth?: number | null;
  };
};

export const adminMe = (t: string) => request<{ email: string }>("/admin/me", { token: t });
export const listManufacturers = (t: string) =>
  request<Manufacturer[]>("/admin/manufacturers", { token: t });
export const setManufacturerStatus = (t: string, id: number, status: MfrStatus, reason?: string) =>
  request(`/admin/manufacturers/${id}/status`, {
    method: "PUT",
    json: { status, rejection_reason: reason || null },
    token: t,
  });
export const listIssues = (t: string) => request<Issue[]>("/admin/issues", { token: t });
export const setIssueStatus = (t: string, id: number, status: Issue["status"]) =>
  request(`/admin/issues/${id}/status`, { method: "PUT", json: { status }, token: t });
export const listAuditLogs = (t: string) =>
  request<AuditEntry[]>("/admin/audit-logs?limit=200", { token: t });
export const chainHealth = () => request<ChainHealth>("/health/blockchain");

/** The uploaded verification document as a blob URL the browser can show or save. */
export async function documentUrl(t: string, id: number): Promise<{ url: string; type: string }> {
  if (PREVIEW) return previewDocument(id);
  let res: Response;
  try {
    res = await fetch(`${API_URL}/api/admin/manufacturers/${id}/document`, {
      headers: { Authorization: `Bearer ${t}` },
    });
  } catch {
    throw new ApiError("Cannot reach the AuthentiQ server.", 0);
  }
  if (!res.ok) throw new ApiError("The document could not be loaded.", res.status);
  const blob = await res.blob();
  return { url: URL.createObjectURL(blob), type: blob.type };
}
