/**
 * Preview mode: a pretend backend that runs inside the browser, so the website can be
 * clicked through (including the team console) without the FastAPI server.
 *
 * Switched on only when the site is built with VITE_PREVIEW=1. Normal builds never use it.
 * Data lives in this browser tab only (sessionStorage) and resets when the tab closes.
 *
 * Logins in preview:
 *   team console:  team@authentiq.demo / TeamDemo@2026   (demo-only; never the real team password,
 *                  because this file ships inside a public page)
 *   manufacturer:  demo@sahyadrifoods.in / Demo@1234   (or any account you register)
 */

// Loose on purpose: preview data mirrors the backend's JSON, which the real types already describe.

type Keys =
  | "id"
  | "status"
  | "product_id"
  | "product_name"
  | "message"
  | "latitude"
  | "longitude"
  | "email"
  | "password"
  | "rejection_reason"
  | "facility"
  | "distributors"
  | "lat"
  | "lon"
  | "city"
  | "name"
  | "sku"
  | "batch_number"
  | "created_at";
// eslint-disable-next-line @typescript-eslint/no-explicit-any
type Json = { [key: string]: any } & Partial<Record<Keys, any>>;
type Opts = { method?: string; json?: unknown; form?: FormData; token?: string };

export const PREVIEW = import.meta.env.VITE_PREVIEW === "1";

/** Demo-only logins, shown on the login form in preview builds. */
export const DEMO_LOGINS = {
  team: { email: "team@authentiq.demo", password: "TeamDemo@2026" },
  manufacturer: { email: "demo@sahyadrifoods.in", password: "Demo@1234" },
};
const ADMIN = DEMO_LOGINS.team;

type Mfr = {
  id: number;
  email: string;
  password: string;
  company_name: string;
  gstin: string;
  company_address: string;
  phone: string;
  verification_status: "PENDING" | "APPROVED" | "REJECTED" | "SUSPENDED";
  verified_at: string | null;
  rejection_reason: string | null;
  created_at: string;
  document_name: string;
};
type Prod = Json & { product_id: string; manufacturer_id: number };
type ScanRow = {
  product_id: string;
  scanned_at: string;
  location: string | null;
  final_verdict: string;
  flags: string[];
};
type State = {
  mfrs: Mfr[];
  products: Prod[];
  scans: ScanRow[];
  issues: Json[];
  audit: Json[];
  next: number;
};

const ago = (days: number) => new Date(Date.now() - days * 86400000).toISOString();
const hex = (n: number) =>
  Array.from({ length: n }, () => Math.floor(Math.random() * 16).toString(16)).join("");

function seed(): State {
  const mk = (
    id: number,
    company: string,
    gstin: string,
    email: string,
    city: string,
    status: Mfr["verification_status"],
    days: number,
    reason: string | null = null,
  ): Mfr => ({
    id,
    email,
    password: id === 1 ? "Demo@1234" : "Preview@123",
    company_name: company,
    gstin,
    company_address: `Plot ${10 + id}, MIDC, ${city}, Maharashtra`,
    phone: `+91 98${id}0${id}2 4${id}6${id}0`,
    verification_status: status,
    verified_at: status === "APPROVED" ? ago(days - 1) : null,
    rejection_reason: reason,
    created_at: ago(days),
    document_name: `${company.split(" ")[0]}-aadhaar.pdf`,
  });
  const mfrs = [
    mk(
      1,
      "Sahyadri Foods Pvt Ltd",
      "27AABCS1429B1Z5",
      "demo@sahyadrifoods.in",
      "Nashik",
      "APPROVED",
      12,
    ),
    mk(
      2,
      "Godavari Pharma LLP",
      "27AAGFG7781K1Z2",
      "contact@godavaripharma.in",
      "Aurangabad",
      "PENDING",
      1,
    ),
    mk(
      3,
      "Konkan Spices Co.",
      "27AAKFK3320M1Z9",
      "hello@konkanspices.in",
      "Ratnagiri",
      "PENDING",
      2,
    ),
    mk(4, "Deccan Electronics", "27AADCD5512Q1Z1", "ops@deccanelec.in", "Pune", "APPROVED", 20),
    mk(
      5,
      "Quickmart Traders",
      "27AAQFQ0091R1Z7",
      "sales@quickmart.example",
      "Thane",
      "REJECTED",
      6,
      "GSTIN does not match the company name on the Aadhaar document.",
    ),
    mk(6, "Vidarbha Textiles", "27AAVCV8843P1Z4", "info@vidarbhatex.in", "Nagpur", "SUSPENDED", 30),
  ];
  const tx = `0x${hex(64)}`;
  const products: Prod[] = [
    {
      product_id: "AQ-NSK-0001",
      manufacturer_id: 1,
      product_name: "Herbal Green Tea 100 g",
      batch_number: "B-0427",
      sku: "HGT-100",
      manufacturer_name: "Sahyadri Foods Pvt Ltd",
      current_location: "Nashik",
      next_location: "Godavari Traders",
      facility: {
        name: "Sahyadri Foods plant",
        street: "Plot 11, MIDC Satpur",
        city: "Nashik",
        country: "India",
        lat: 20.01,
        lon: 73.74,
      },
      distributors: [
        {
          name: "Godavari Traders",
          street: "College Road",
          city: "Nashik",
          country: "India",
          lat: 20.0,
          lon: 73.78,
        },
      ],
      registration_tx_hash: tx,
      registration_block: 7012345,
      explorer_url: `https://sepolia.etherscan.io/tx/${tx}`,
      is_onchain: true,
      created_at: ago(5),
    },
  ];
  const scans: ScanRow[] = [
    {
      product_id: "AQ-NSK-0001",
      scanned_at: ago(2),
      location: "Nashik",
      final_verdict: "GENUINE",
      flags: [],
    },
  ];
  const issues: Json[] = [
    {
      id: 1,
      product_id: "AQ-2002",
      message: "The seal on the box looked different from usual.",
      contact: "ravi@example.com",
      latitude: 19.07,
      longitude: 72.87,
      status: "OPEN",
      created_at: ago(0.3),
    },
  ];
  const audit: Json[] = [
    {
      id: 1,
      user_email: "demo@sahyadrifoods.in",
      action: "MANUFACTURER_REGISTERED",
      entity_type: "manufacturer",
      entity_id: "1",
      description: "Sahyadri Foods Pvt Ltd registered",
      ip_address: null,
      created_at: ago(12),
    },
    {
      id: 2,
      user_email: ADMIN.email,
      action: "MANUFACTURER_APPROVED",
      entity_type: "manufacturer",
      entity_id: "1",
      description: "Approved Sahyadri Foods Pvt Ltd",
      ip_address: null,
      created_at: ago(11),
    },
    {
      id: 3,
      user_email: "demo@sahyadrifoods.in",
      action: "PRODUCT_REGISTERED",
      entity_type: "product",
      entity_id: "AQ-NSK-0001",
      description: "Herbal Green Tea 100 g stored on the blockchain",
      ip_address: null,
      created_at: ago(5),
    },
    {
      id: 4,
      user_email: ADMIN.email,
      action: "MANUFACTURER_REJECTED",
      entity_type: "manufacturer",
      entity_id: "5",
      description: "Rejected Quickmart Traders",
      ip_address: null,
      created_at: ago(5.5),
    },
    {
      id: 5,
      user_email: ADMIN.email,
      action: "MANUFACTURER_SUSPENDED",
      entity_type: "manufacturer",
      entity_id: "6",
      description: "Suspended Vidarbha Textiles",
      ip_address: null,
      created_at: ago(3),
    },
    {
      id: 6,
      user_email: "contact@godavaripharma.in",
      action: "MANUFACTURER_REGISTERED",
      entity_type: "manufacturer",
      entity_id: "2",
      description: "Godavari Pharma LLP registered",
      ip_address: null,
      created_at: ago(1),
    },
  ];
  return { mfrs, products, scans, issues, audit, next: 100 };
}

const KEY = "authentiq.preview";
let state: State | null = null;
function db(): State {
  if (state) return state;
  try {
    const saved = sessionStorage.getItem(KEY);
    if (saved) state = JSON.parse(saved) as State;
  } catch {
    /* storage unavailable: start fresh */
  }
  state ??= seed();
  return state;
}
function save() {
  try {
    sessionStorage.setItem(KEY, JSON.stringify(state));
  } catch {
    /* ignore */
  }
}

class PreviewError extends Error {
  constructor(
    message: string,
    public status: number,
  ) {
    super(message);
  }
}
const fail = (status: number, detail: string): never => {
  throw new PreviewError(detail, status);
};

function who(token?: string): { role: "ADMIN" } | { role: "MANUFACTURER"; mfr: Mfr } {
  if (token === "preview-admin") return { role: "ADMIN" };
  const m = token?.match(/^preview-mfr-(\d+)$/);
  const mfr = m ? db().mfrs.find((x) => x.id === Number(m[1])) : undefined;
  if (!mfr) return fail(401, "Please log in again.");
  return { role: "MANUFACTURER", mfr };
}
const needAdmin = (t?: string) => {
  if (who(t).role !== "ADMIN") fail(403, "Not allowed.");
};

function log(
  user_email: string | null,
  action: string,
  entity_type: string,
  entity_id: string,
  description: string,
) {
  const s = db();
  s.audit.unshift({
    id: s.next++,
    user_email,
    action,
    entity_type,
    entity_id,
    description,
    ip_address: null,
    created_at: new Date().toISOString(),
  });
}

const publicMfr = ({ password: _p, document_name: _d, ...m }: Mfr) => m;

function handle(path: string, o: Opts): unknown {
  const s = db();
  const method = o.method ?? (o.json !== undefined || o.form ? "POST" : "GET");
  const body = (o.json ?? {}) as Json;
  const [route] = path.split("?");

  // --- accounts ---------------------------------------------------------
  if (route === "/auth/login") {
    const email = String(body.email ?? "")
      .trim()
      .toLowerCase();
    const password = String(body.password ?? "");
    if (email === ADMIN.email && password === ADMIN.password)
      return { access_token: "preview-admin", role: "ADMIN" };
    const m = s.mfrs.find((x) => x.email === email);
    if (!m || m.password !== password) fail(401, "Incorrect email or password.");
    return { access_token: `preview-mfr-${m!.id}`, role: "MANUFACTURER" };
  }
  if (route === "/auth/manufacturer/register") {
    const f = o.form!;
    const email = String(f.get("email") ?? "")
      .trim()
      .toLowerCase();
    if (email === ADMIN.email || s.mfrs.some((x) => x.email === email))
      fail(400, "An account with this email already exists.");
    const doc = f.get("verification_document");
    const m: Mfr = {
      id: s.next++,
      email,
      password: String(f.get("password") ?? ""),
      company_name: String(f.get("company_name") ?? ""),
      gstin: String(f.get("gstin") ?? "").toUpperCase(),
      company_address: String(f.get("company_address") ?? ""),
      phone: String(f.get("phone") ?? ""),
      verification_status: "PENDING",
      verified_at: null,
      rejection_reason: null,
      created_at: new Date().toISOString(),
      document_name: doc instanceof File ? doc.name : "document.pdf",
    };
    s.mfrs.push(m);
    log(
      email,
      "MANUFACTURER_REGISTERED",
      "manufacturer",
      String(m.id),
      `${m.company_name} registered`,
    );
    return { verification_status: "PENDING", company_name: m.company_name };
  }
  if (route === "/manufacturer/profile") {
    const w = who(o.token);
    if (w.role !== "MANUFACTURER") return fail(403, "Not allowed.");
    return publicMfr(w.mfr);
  }

  // --- products ----------------------------------------------------------
  if (route === "/products/mine") {
    const w = who(o.token);
    if (w.role !== "MANUFACTURER") return fail(403, "Not allowed.");
    return s.products.filter((p) => p.manufacturer_id === w.mfr.id).reverse();
  }
  if (route === "/products/register") {
    const w = who(o.token);
    if (w.role !== "MANUFACTURER") return fail(403, "Not allowed.");
    if (w.mfr.verification_status !== "APPROVED") fail(403, "Your account is not approved yet.");
    const id = String(body.product_id || `AQ-${hex(8).toUpperCase()}`);
    if (s.products.some((p) => p.product_id === id))
      fail(400, "A product with this code already exists.");
    const facility = (body.facility ?? {}) as Json;
    const distributors = (body.distributors ?? []) as Json[];
    const tx = `0x${hex(64)}`;
    const block = 7012345 + s.next;
    s.products.push({
      product_id: id,
      manufacturer_id: w.mfr.id,
      product_name: body.product_name,
      batch_number: body.batch_number,
      sku: body.sku ?? null,
      manufacturer_name: w.mfr.company_name,
      current_location: String(facility.city ?? ""),
      next_location: String(distributors[0]?.name ?? ""),
      facility,
      distributors,
      registration_tx_hash: tx,
      registration_block: block,
      explorer_url: `https://sepolia.etherscan.io/tx/${tx}`,
      is_onchain: true,
      created_at: new Date().toISOString(),
    });
    log(
      w.mfr.email,
      "PRODUCT_REGISTERED",
      "product",
      id,
      `${String(body.product_name)} stored on the blockchain`,
    );
    return { product_id: id, transaction_hash: tx, block_number: block };
  }

  // --- customer -----------------------------------------------------------
  if (route === "/verify/report") {
    const id = String(body.product_id ?? "").trim();
    const p = s.products.find((x) => x.product_id === id);
    if (!p) return { found: false, product_id: id, message: "This code is not registered." };
    const lat = typeof body.latitude === "number" ? body.latitude : null;
    const dists = (p.distributors as Json[]) ?? [];
    const near =
      lat === null || dists.some((d) => typeof d.lat === "number" && Math.abs(d.lat - lat) < 1.5);
    const flags = near ? [] : ["Scan is far from every registered distributor"];
    s.scans.push({
      product_id: id,
      scanned_at: new Date().toISOString(),
      location:
        lat === null
          ? null
          : near
            ? String(dists[0]?.city ?? "Near distributor")
            : "Far from distributors",
      final_verdict: flags.length ? "SUSPICIOUS" : "GENUINE",
      flags,
    });
    return {
      found: true,
      product: p,
      verification: { is_valid: true, blockchain_verified: true, tampered: false },
      scan: { final_verdict: flags.length ? "SUSPICIOUS" : "GENUINE", flags },
      history: s.scans.filter((x) => x.product_id === id).reverse(),
    };
  }
  if (route === "/issues") {
    s.issues.unshift({
      id: s.next++,
      product_id: body.product_id,
      message: body.message,
      contact: null,
      latitude: body.latitude ?? null,
      longitude: body.longitude ?? null,
      status: "OPEN",
      created_at: new Date().toISOString(),
    });
    return { ok: true };
  }

  // --- team console --------------------------------------------------------
  if (route === "/health/blockchain")
    return {
      blockchain: {
        contract_accessible: true,
        latest_block: 7012345 + s.next,
        wallet_balance_eth: 0.0462,
      },
    };
  if (route === "/admin/me") {
    needAdmin(o.token);
    return { email: ADMIN.email };
  }
  if (route === "/admin/manufacturers") {
    needAdmin(o.token);
    return [...s.mfrs].reverse().map(publicMfr);
  }
  let m = route?.match(/^\/admin\/manufacturers\/(\d+)\/status$/);
  if (m && method === "PUT") {
    needAdmin(o.token);
    const mfr = s.mfrs.find((x) => x.id === Number(m![1])) ?? fail(404, "Not found.");
    const status = body.status as Mfr["verification_status"];
    mfr.verification_status = status;
    mfr.rejection_reason =
      status === "APPROVED" ? null : ((body.rejection_reason as string | null) ?? null);
    if (status === "APPROVED") mfr.verified_at = new Date().toISOString();
    log(
      ADMIN.email,
      `MANUFACTURER_${status}`,
      "manufacturer",
      String(mfr.id),
      `${status[0]}${status.slice(1).toLowerCase()} ${mfr.company_name}`,
    );
    return publicMfr(mfr);
  }
  if (route === "/admin/issues") {
    needAdmin(o.token);
    return s.issues;
  }
  m = route?.match(/^\/admin\/issues\/(\d+)\/status$/);
  if (m && method === "PUT") {
    needAdmin(o.token);
    const issue = s.issues.find((x) => x.id === Number(m![1])) ?? fail(404, "Not found.");
    issue.status = body.status;
    log(
      ADMIN.email,
      `ISSUE_${String(body.status)}`,
      "issue",
      String(issue.id),
      `Issue on ${String(issue.product_id)} marked ${String(body.status).toLowerCase()}`,
    );
    return issue;
  }
  if (route === "/admin/audit-logs") {
    needAdmin(o.token);
    return [...s.audit]
      .sort((a, b) => String(b.created_at).localeCompare(String(a.created_at)))
      .slice(0, 200);
  }
  return fail(404, `Preview mode has no page for ${path}.`);
}

/** Same contract as the real request(): resolves with the body or throws {message, status}. */
export async function previewRequest<T>(path: string, opts: Opts): Promise<T> {
  await new Promise((r) => setTimeout(r, path === "/products/register" ? 900 : 150));
  const result = handle(path, opts);
  save();
  return result as T;
}

export const isPreviewError = (e: unknown): e is PreviewError => e instanceof PreviewError;

/** A sample "uploaded document" so View document has something to show. */
export function previewDocument(id: number): { url: string; type: string } {
  needAdmin("preview-admin");
  const m = db().mfrs.find((x) => x.id === id);
  const esc = (t: string) =>
    t.replace(/[<>&]/g, (c) => ({ "<": "&lt;", ">": "&gt;", "&": "&amp;" })[c]!);
  const svg = `<svg xmlns="http://www.w3.org/2000/svg" width="640" height="400" viewBox="0 0 640 400">
<rect width="640" height="400" rx="24" fill="#f4f6fb"/><rect x="0" y="0" width="640" height="70" rx="24" fill="#0b1b3a"/>
<text x="32" y="45" font-family="sans-serif" font-size="22" fill="#d4a017" font-weight="700">SAMPLE DOCUMENT (preview)</text>
<rect x="32" y="100" width="150" height="180" rx="12" fill="#dfe4ee"/>
<text x="216" y="130" font-family="sans-serif" font-size="20" fill="#0b1b3a" font-weight="700">${esc(m?.company_name ?? "Company")}</text>
<text x="216" y="170" font-family="sans-serif" font-size="16" fill="#44506b">GSTIN: ${esc(m?.gstin ?? "")}</text>
<text x="216" y="200" font-family="sans-serif" font-size="16" fill="#44506b">Aadhaar: XXXX XXXX ${1000 + id}</text>
<text x="216" y="230" font-family="sans-serif" font-size="16" fill="#44506b">File: ${esc(m?.document_name ?? "")}</text>
<text x="32" y="350" font-family="sans-serif" font-size="14" fill="#7a8399">In the real system this shows the file the manufacturer uploaded.</text></svg>`;
  return {
    url: URL.createObjectURL(new Blob([svg], { type: "image/svg+xml" })),
    type: "image/svg+xml",
  };
}
