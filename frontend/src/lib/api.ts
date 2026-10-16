/**
 * Calls to the AuthentiQ FastAPI backend (backend/ in this repo).
 *
 * The backend address comes from VITE_API_URL (see .env.example) and defaults to
 * http://127.0.0.1:8000, which is where `uvicorn app.main:app` listens.
 */
import type { Product, Scan } from "@/lib/samples";
import { PREVIEW, isPreviewError, previewRequest } from "@/lib/preview";

// Written as `import.meta.env.VITE_API_URL` exactly, so both Vite and the single-file
// build (scripts/build-single-html.py, via --define) can replace it at build time.
// Unset -> local backend. Empty string -> same site (in deployment nginx proxies /api).
const configured = import.meta.env.VITE_API_URL;
export const API_URL = (configured ?? "http://127.0.0.1:8000").replace(/\/+$/, "");

export class ApiError extends Error {
  constructor(
    message: string,
    public status: number,
  ) {
    super(message);
  }
}

/** FastAPI errors come as {detail: "text"} or {detail: [{msg: "..."}]} (validation). */
/** Blockchain failures come back as long technical messages; show something a person can act on. */
function friendly(detail: string): string {
  if (/insufficient funds/i.test(detail))
    return "The AuthentiQ blockchain account is out of test funds, so this product was not stored. Please tell the AuthentiQ team, then submit again.";
  if (/blockchain/i.test(detail) && detail.length > 160)
    return "The blockchain could not be reached, so this product was not stored. Please try again in a few minutes.";
  return detail;
}

function errorText(body: unknown, status: number): string {
  const detail = (body as { detail?: unknown } | null)?.detail;
  if (typeof detail === "string") return friendly(detail);
  if (Array.isArray(detail))
    return detail
      .map((d: { msg?: string; loc?: unknown[] }) =>
        [d.loc?.slice(1).join("."), d.msg].filter(Boolean).join(": "),
      )
      .join("; ");
  return `The server answered with an error (${status}).`;
}

export async function request<T>(
  path: string,
  opts: { method?: string; json?: unknown; form?: FormData; token?: string } = {},
): Promise<T> {
  if (PREVIEW) {
    try {
      return await previewRequest<T>(path, opts);
    } catch (e) {
      if (isPreviewError(e)) throw new ApiError(e.message, e.status);
      throw e;
    }
  }
  const headers: Record<string, string> = {};
  if (opts.json !== undefined) headers["Content-Type"] = "application/json";
  if (opts.token) headers["Authorization"] = `Bearer ${opts.token}`;
  let res: Response;
  try {
    res = await fetch(`${API_URL}/api${path}`, {
      method: opts.method ?? (opts.json !== undefined || opts.form ? "POST" : "GET"),
      headers,
      body: opts.form ?? (opts.json !== undefined ? JSON.stringify(opts.json) : null),
    });
  } catch {
    throw new ApiError(
      `Cannot reach the AuthentiQ server${API_URL ? ` at ${API_URL}` : ""}. Check that the backend is running.`,
      0,
    );
  }
  const body: unknown = await res.json().catch(() => null);
  if (!res.ok) throw new ApiError(errorText(body, res.status), res.status);
  return body as T;
}

// ---------------------------------------------------------------------------
// Shapes returned by the backend
// ---------------------------------------------------------------------------

export type Place = {
  name?: string | null | undefined;
  street?: string | null | undefined;
  city?: string | null | undefined;
  country?: string | null | undefined;
  lat?: number | null | undefined;
  lon?: number | null | undefined;
};

type ApiProduct = {
  product_id: string;
  product_name: string;
  batch_number: string;
  sku?: string | null;
  manufacturer_name: string;
  current_location: string;
  next_location: string;
  facility?: Place | null;
  distributors?: Place[] | null;
  registration_tx_hash?: string | null;
  registration_block?: number | null;
  explorer_url?: string | null;
  is_onchain: boolean;
  created_at: string;
};

type ApiHistory = {
  scanned_at: string;
  location: string | null;
  final_verdict: string;
  flags: string[];
};

type ApiReport =
  | { found: false; product_id: string; message: string }
  | {
      found: true;
      product: ApiProduct;
      verification: {
        is_valid?: boolean;
        blockchain_verified?: boolean;
        tampered?: boolean;
        message?: string;
      };
      scan: { final_verdict: string; flags: string[] };
      history: ApiHistory[];
    };

export type Profile = {
  id: number;
  email: string;
  company_name: string;
  gstin: string;
  company_address: string;
  phone: string;
  verification_status: "PENDING" | "APPROVED" | "REJECTED" | "SUSPENDED";
  rejection_reason?: string | null;
};

// ---------------------------------------------------------------------------
// Turning backend data into what the pages show
// ---------------------------------------------------------------------------

export const placeText = (p?: Place | null) =>
  p ? [p.street, p.city, p.country].filter((x) => x && x.trim()).join(", ") : "";

/** Backend timestamps are UTC without a zone marker. */
const when = (iso: string) =>
  new Date(/[zZ]|[+-]\d\d:\d\d$/.test(iso) ? iso : `${iso}Z`).toLocaleString("en-GB", {
    day: "numeric",
    month: "short",
    hour: "2-digit",
    minute: "2-digit",
  });

/** The AI model's flags, in words a customer understands. */
const FLAG_TEXT: [RegExp, string][] = [
  [
    /impossible travel|duplicated qr/i,
    "This code was scanned in places too far apart for the time between the scans. The code may have been copied.",
  ],
  [
    /registered distributor/i,
    "This scan is far from every distributor the manufacturer registered.",
  ],
  [/geographical velocity/i, "This scan's location does not fit the product's registered route."],
  [/high scan frequency/i, "This code has been scanned unusually often in the last 24 hours."],
  [/pre-mature scan/i, "This code was scanned very soon after the product was registered."],
];
export const flagText = (flag: string) => FLAG_TEXT.find(([re]) => re.test(flag))?.[1] ?? flag;

function toProduct(p: ApiProduct, history: ApiHistory[] = [], extra: string[] = []): Product {
  const scans: Scan[] = history.map((h) => ({
    time: when(h.scanned_at),
    place: h.location || "Location not shared",
    flagged: h.final_verdict !== "GENUINE",
  }));
  const anomalies = new Set(extra);
  history
    .filter((h) => h.final_verdict !== "GENUINE")
    .forEach((h) =>
      h.flags
        // A scan soon after registration is normal while testing; not worth alarming customers.
        .filter((f) => !/pre-mature scan/i.test(f))
        .forEach((f) => anomalies.add(flagText(f))),
    );
  if (history.some((h) => h.final_verdict === "UNREGISTERED"))
    anomalies.add("This product is not yet confirmed on the blockchain.");
  const tx = p.registration_tx_hash;
  return {
    code: p.product_id,
    name: p.product_name,
    batch: p.batch_number,
    sku: p.sku ?? undefined,
    facility: placeText(p.facility) || p.current_location,
    manufacturer: p.manufacturer_name,
    distributors: p.distributors?.length
      ? p.distributors.map((d) => ({ name: d.name || "Distributor", address: placeText(d) }))
      : [{ name: p.next_location, address: "" }],
    txHash: tx ? (tx.startsWith("0x") ? tx : `0x${tx}`) : null,
    block: p.registration_block ?? null,
    onChain: p.is_onchain,
    explorerUrl: p.explorer_url ?? null,
    scans,
    anomalies: [...anomalies],
  };
}

// ---------------------------------------------------------------------------
// Customer side
// ---------------------------------------------------------------------------

/** Record this scan and get the full scan report, or null if the code is not registered. */
export async function scanProduct(
  code: string,
  coords: { lat: number; lon: number } | null,
): Promise<Product | null> {
  const r = await request<ApiReport>("/verify/report", {
    json: { product_id: code.trim(), latitude: coords?.lat, longitude: coords?.lon },
  });
  if (!r.found) return null;
  const extra: string[] = [];
  if (r.verification.tampered || (r.product.is_onchain && r.verification.is_valid === false))
    extra.push(
      r.verification.message ?? "The database record does not match the blockchain record.",
    );
  return toProduct(r.product, r.history, extra);
}

export async function raiseIssue(
  code: string,
  message: string,
  coords: { lat: number; lon: number } | null,
) {
  await request("/issues", {
    json: { product_id: code, message, latitude: coords?.lat, longitude: coords?.lon },
  });
}

// ---------------------------------------------------------------------------
// Manufacturer side
// ---------------------------------------------------------------------------

/** Multipart form: company_name, gstin, company_address, phone, email, password, verification_document. */
export async function registerManufacturer(form: FormData) {
  return request<{ verification_status: string; company_name: string }>(
    "/auth/manufacturer/register",
    { form },
  );
}

export type Role = "MANUFACTURER" | "ADMIN";

/** One login for everyone: the role decides which dashboard opens. */
export async function login(
  email: string,
  password: string,
): Promise<{ token: string; role: Role }> {
  const r = await request<{ access_token: string; role: string }>("/auth/login", {
    json: { email, password },
  });
  if (r.role !== "MANUFACTURER" && r.role !== "ADMIN")
    throw new ApiError("This account cannot sign in here.", 403);
  return { token: r.access_token, role: r.role };
}

export const getProfile = (token: string) => request<Profile>("/manufacturer/profile", { token });

export async function listMyProducts(token: string): Promise<Product[]> {
  const list = await request<ApiProduct[]>("/products/mine", { token });
  return list.map((p) => toProduct(p));
}

export type NewProduct = {
  product_id?: string | undefined;
  product_name: string;
  batch_number: string;
  sku?: string | undefined;
  facility: Place;
  distributors: Place[];
};

export async function registerProduct(token: string, input: NewProduct) {
  return request<{
    product_id: string;
    transaction_hash: string | null;
    block_number: number | null;
  }>("/products/register", { json: input, token });
}
