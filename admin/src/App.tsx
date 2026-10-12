import { useCallback, useEffect, useMemo, useState, type FormEvent, type ReactNode } from "react";
import {
  Blocks,
  Building2,
  CheckCircle2,
  Clock,
  Download,
  FileText,
  Loader2,
  LogOut,
  Mail,
  MapPin,
  MessageSquareWarning,
  Package,
  Phone,
  RefreshCw,
  ShieldCheck,
  ShieldOff,
  ShieldX,
  X,
} from "lucide-react";
import * as api from "./api";
import type { Issue, Manufacturer, Product, Stats, Status } from "./api";

// ---------------------------------------------------------------------------
// Shared bits
// ---------------------------------------------------------------------------

const card = "rounded-3xl border border-line bg-surface p-5 shadow-[0_8px_24px_rgba(11,27,58,0.06)] sm:p-6";
const field =
  "w-full rounded-xl border border-line bg-surface px-4 py-3 text-base text-ink outline-none transition-colors focus:border-brand";
const btn =
  "inline-flex items-center justify-center gap-2 rounded-full px-5 py-2.5 text-sm font-semibold transition-all active:scale-[0.98]";
const btnDark = `${btn} bg-brand text-white hover:bg-[#1e3a6e]`;
const btnGhost = `${btn} border-2 border-line bg-surface text-ink hover:border-brand`;
const btnGood = `${btn} bg-genuine text-white hover:brightness-110`;
const btnBad = `${btn} border-2 border-fake/40 bg-surface text-fake hover:bg-fake-soft`;

const TOKEN_KEY = "authentiq.adminToken";
const store = {
  get: () => {
    try {
      return sessionStorage.getItem(TOKEN_KEY);
    } catch {
      return null;
    }
  },
  set: (t: string | null) => {
    try {
      if (t) sessionStorage.setItem(TOKEN_KEY, t);
      else sessionStorage.removeItem(TOKEN_KEY);
    } catch {
      /* storage blocked: session ends on reload */
    }
  },
};

const message = (e: unknown) => (e instanceof Error ? e.message : "Something went wrong.");

const when = (iso: string | null) =>
  iso
    ? new Date(/[zZ]|[+-]\d\d:\d\d$/.test(iso) ? iso : `${iso}Z`).toLocaleString("en-GB", {
        day: "numeric",
        month: "short",
        year: "numeric",
        hour: "2-digit",
        minute: "2-digit",
      })
    : "";

function Logo() {
  return (
    <span className="inline-flex items-center text-[22px] leading-none font-extrabold tracking-[-0.04em]">
      Authenti
      <svg width={23} height={23} viewBox="0 0 100 100" className="ml-[1.5px] translate-y-[2px]" aria-hidden="true">
        <rect x="12" y="12" width="68" height="68" rx="21" fill="none" stroke="currentColor" strokeWidth="15" />
        <rect x="36" y="36" width="20" height="20" rx="5" fill="var(--color-lime)" />
        <path d="M62 62 L90 90" stroke="#fff" strokeWidth="26" strokeLinecap="round" />
        <path d="M64 64 L90 90" stroke="var(--color-lime)" strokeWidth="15" strokeLinecap="round" />
      </svg>
    </span>
  );
}

const STATUS_STYLE: Record<string, string> = {
  PENDING: "bg-warn-soft text-warn",
  APPROVED: "bg-genuine-soft text-genuine",
  REJECTED: "bg-fake-soft text-fake",
  SUSPENDED: "bg-secondary text-subtle",
  OPEN: "bg-warn-soft text-warn",
  REVIEWED: "bg-brand-soft text-brand",
  CLOSED: "bg-secondary text-subtle",
};
function Badge({ status }: { status: string }) {
  return (
    <span className={`rounded-full px-3 py-1 font-mono text-[11px] font-semibold tracking-wider ${STATUS_STYLE[status] ?? ""}`}>
      {status}
    </span>
  );
}

function Filters<T extends string>({
  value,
  options,
  counts,
  onChange,
}: {
  value: T;
  options: readonly T[];
  counts: Partial<Record<T, number>>;
  onChange: (v: T) => void;
}) {
  return (
    <div role="tablist" className="flex flex-wrap gap-2">
      {options.map((o) => (
        <button
          key={o}
          type="button"
          role="tab"
          aria-selected={value === o}
          onClick={() => onChange(o)}
          className={`rounded-full px-4 py-2 text-sm font-semibold transition-colors ${
            value === o ? "bg-brand text-white" : "bg-surface text-ink ring-1 ring-line hover:ring-brand"
          }`}
        >
          {o.charAt(0) + o.slice(1).toLowerCase()}
          {counts[o] != null && <span className="ml-1.5 opacity-70">{counts[o]}</span>}
        </button>
      ))}
    </div>
  );
}

function Empty({ icon: Icon, children }: { icon: typeof Clock; children: ReactNode }) {
  return (
    <div className={`${card} flex flex-col items-center gap-3 py-12 text-center text-subtle`}>
      <Icon className="size-10" strokeWidth={1.3} aria-hidden="true" />
      {children}
    </div>
  );
}

// ---------------------------------------------------------------------------
// Login
// ---------------------------------------------------------------------------

function Login({ onToken }: { onToken: (t: string) => void }) {
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const submit = async (e: FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    const f = new FormData(e.currentTarget);
    setBusy(true);
    setError("");
    try {
      onToken(await api.login(String(f.get("email")).trim(), String(f.get("password"))));
    } catch (err) {
      setError(message(err));
    } finally {
      setBusy(false);
    }
  };
  return (
    <div className="flex min-h-screen items-center justify-center bg-gradient-to-b from-brand-soft to-paper px-5">
      <div className={`${card} w-full max-w-[420px]`}>
        <Logo />
        <p className="mt-1 font-mono text-xs tracking-widest text-subtle">ADMIN PORTAL</p>
        <h1 className="mt-6 text-2xl font-extrabold">Sign in</h1>
        <p className="mt-1 text-sm text-subtle">For the AuthentiQ team only.</p>
        <form onSubmit={(e) => void submit(e)} className="mt-6 grid gap-4">
          <label className="grid gap-1.5 text-sm font-semibold">
            Email
            <input name="email" type="email" required autoComplete="username" className={field} />
          </label>
          <label className="grid gap-1.5 text-sm font-semibold">
            Password
            <input name="password" type="password" required autoComplete="current-password" className={field} />
          </label>
          {error && (
            <p role="alert" className="rounded-xl bg-fake-soft p-3 text-sm font-semibold text-fake">
              {error}
            </p>
          )}
          <button type="submit" className={`${btnDark} py-3 text-base`} disabled={busy}>
            {busy ? "Signing in…" : "Sign in"}
          </button>
        </form>
      </div>
    </div>
  );
}

// ---------------------------------------------------------------------------
// Verification
// ---------------------------------------------------------------------------

function DocumentViewer({ token, m, onClose }: { token: string; m: Manufacturer; onClose: () => void }) {
  const [doc, setDoc] = useState<{ url: string; type: string } | null>(null);
  const [error, setError] = useState("");
  useEffect(() => {
    let url = "";
    api
      .documentUrl(token, m.id)
      .then((d) => {
        url = d.url;
        setDoc(d);
      })
      .catch((e: unknown) => setError(message(e)));
    return () => {
      if (url) URL.revokeObjectURL(url);
    };
  }, [token, m.id]);
  useEffect(() => {
    const esc = (e: KeyboardEvent) => e.key === "Escape" && onClose();
    window.addEventListener("keydown", esc);
    return () => window.removeEventListener("keydown", esc);
  }, [onClose]);

  return (
    <div
      role="dialog"
      aria-modal="true"
      aria-label={`Verification document of ${m.company_name}`}
      className="fixed inset-0 z-50 flex items-center justify-center bg-ink/60 p-4"
      onClick={onClose}
    >
      <div className="flex h-[88vh] w-full max-w-4xl flex-col overflow-hidden rounded-3xl bg-surface" onClick={(e) => e.stopPropagation()}>
        <div className="flex items-center justify-between gap-3 border-b border-line px-5 py-4">
          <div>
            <p className="font-bold">{m.company_name}</p>
            <p className="font-mono text-xs text-subtle">Aadhaar card · GSTIN {m.gstin}</p>
          </div>
          <div className="flex items-center gap-2">
            {doc && (
              <a href={doc.url} download={`aadhaar-${m.gstin}`} className={btnGhost}>
                <Download className="size-4" aria-hidden="true" /> Download
              </a>
            )}
            <button type="button" onClick={onClose} aria-label="Close" className="rounded-full p-2 hover:bg-secondary">
              <X className="size-5" />
            </button>
          </div>
        </div>
        <div className="flex flex-1 items-center justify-center bg-secondary">
          {error ? (
            <p className="p-6 font-semibold text-fake">{error}</p>
          ) : !doc ? (
            <Loader2 className="size-8 animate-spin text-subtle" />
          ) : doc.type.startsWith("image/") ? (
            <img src={doc.url} alt="Uploaded Aadhaar card" className="max-h-full max-w-full object-contain" />
          ) : (
            <iframe src={doc.url} title="Uploaded Aadhaar card" className="size-full" />
          )}
        </div>
      </div>
    </div>
  );
}

function ManufacturerCard({
  m,
  token,
  onChanged,
}: {
  m: Manufacturer;
  token: string;
  onChanged: (note: string) => void;
}) {
  const [viewing, setViewing] = useState(false);
  const [rejecting, setRejecting] = useState<"REJECTED" | "SUSPENDED" | null>(null);
  const [reason, setReason] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");

  const change = async (status: Status, why?: string) => {
    setBusy(true);
    setError("");
    try {
      await api.setStatus(token, m.id, status, why);
      setRejecting(null);
      setReason("");
      onChanged(`${m.company_name} is now ${status.toLowerCase()}.`);
    } catch (e) {
      setError(message(e));
    } finally {
      setBusy(false);
    }
  };

  const s = m.verification_status;
  return (
    <li className={card}>
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div className="flex items-start gap-4">
          <span className="flex size-12 flex-none items-center justify-center rounded-2xl bg-brand-soft text-brand">
            <Building2 className="size-6" strokeWidth={1.6} aria-hidden="true" />
          </span>
          <div>
            <h3 className="text-lg font-bold">{m.company_name}</h3>
            <p className="font-mono text-sm tracking-wide">GSTIN {m.gstin}</p>
          </div>
        </div>
        <Badge status={s} />
      </div>

      <dl className="mt-5 grid gap-x-6 gap-y-2 text-sm sm:grid-cols-2">
        <div className="flex items-center gap-2">
          <Mail className="size-4 flex-none text-subtle" aria-hidden="true" />
          <dt className="sr-only">Email</dt>
          <dd className="break-all">{m.email}</dd>
        </div>
        <div className="flex items-center gap-2">
          <Phone className="size-4 flex-none text-subtle" aria-hidden="true" />
          <dt className="sr-only">Phone</dt>
          <dd>{m.phone}</dd>
        </div>
        <div className="flex items-start gap-2 sm:col-span-2">
          <MapPin className="mt-0.5 size-4 flex-none text-subtle" aria-hidden="true" />
          <dt className="sr-only">Address</dt>
          <dd>{m.company_address}</dd>
        </div>
        <div className="flex items-center gap-2 text-subtle sm:col-span-2">
          <Clock className="size-4 flex-none" aria-hidden="true" />
          <dt className="sr-only">Dates</dt>
          <dd>
            Registered {when(m.created_at)}
            {m.verified_at && s !== "PENDING" && <> · last decision {when(m.verified_at)}</>}
          </dd>
        </div>
      </dl>
      {m.rejection_reason && s !== "APPROVED" && (
        <p className="mt-3 rounded-xl bg-secondary p-3 text-sm">
          <span className="font-semibold">Reason:</span> {m.rejection_reason}
        </p>
      )}

      {rejecting ? (
        <form
          className="mt-5 grid gap-3"
          onSubmit={(e) => {
            e.preventDefault();
            void change(rejecting, reason.trim());
          }}
        >
          <label className="grid gap-1.5 text-sm font-semibold">
            {rejecting === "REJECTED" ? "Why is this not approved?" : "Why is this account suspended?"} The
            manufacturer sees this.
            <textarea
              required
              rows={2}
              value={reason}
              onChange={(e) => setReason(e.target.value)}
              className={field}
              placeholder={
                rejecting === "REJECTED"
                  ? "For example: the name on the Aadhaar card does not match the GST registration."
                  : "For example: reported products under investigation."
              }
            />
          </label>
          <div className="flex flex-wrap gap-2">
            <button type="submit" className={`${btn} bg-fake text-white`} disabled={busy}>
              {rejecting === "REJECTED" ? "Reject" : "Suspend"}
            </button>
            <button type="button" className={btnGhost} onClick={() => setRejecting(null)}>
              Cancel
            </button>
          </div>
        </form>
      ) : (
        <div className="mt-5 flex flex-wrap gap-2">
          <button type="button" className={btnGhost} onClick={() => setViewing(true)}>
            <FileText className="size-4" aria-hidden="true" /> View Aadhaar card
          </button>
          {s !== "APPROVED" && (
            <button type="button" className={btnGood} disabled={busy} onClick={() => void change("APPROVED")}>
              <ShieldCheck className="size-4" aria-hidden="true" />
              {s === "PENDING" ? "Approve" : "Approve now"}
            </button>
          )}
          {s === "PENDING" && (
            <button type="button" className={btnBad} disabled={busy} onClick={() => setRejecting("REJECTED")}>
              <ShieldX className="size-4" aria-hidden="true" /> Reject
            </button>
          )}
          {s === "APPROVED" && (
            <button type="button" className={btnBad} disabled={busy} onClick={() => setRejecting("SUSPENDED")}>
              <ShieldOff className="size-4" aria-hidden="true" /> Suspend
            </button>
          )}
        </div>
      )}
      {error && (
        <p role="alert" className="mt-3 text-sm font-semibold text-fake">
          {error}
        </p>
      )}
      {viewing && <DocumentViewer token={token} m={m} onClose={() => setViewing(false)} />}
    </li>
  );
}

const M_FILTERS = ["PENDING", "APPROVED", "REJECTED", "SUSPENDED", "ALL"] as const;

function Verification({ token, list, reload }: { token: string; list: Manufacturer[]; reload: () => void }) {
  const [filter, setFilter] = useState<(typeof M_FILTERS)[number]>("PENDING");
  const [note, setNote] = useState("");
  const counts = useMemo(() => {
    const c: Partial<Record<(typeof M_FILTERS)[number], number>> = { ALL: list.length };
    for (const m of list) c[m.verification_status] = (c[m.verification_status] ?? 0) + 1;
    return c;
  }, [list]);
  const shown = list
    .filter((m) => filter === "ALL" || m.verification_status === filter)
    .sort((a, b) => b.created_at.localeCompare(a.created_at));

  return (
    <section>
      <div className="flex flex-wrap items-end justify-between gap-4">
        <div>
          <h1 className="text-3xl font-extrabold">Manufacturer verification</h1>
          <p className="mt-1 text-subtle">
            Check the GSTIN and Aadhaar card, then approve. Approved manufacturers can register products.
          </p>
        </div>
        <Filters value={filter} options={M_FILTERS} counts={counts} onChange={setFilter} />
      </div>
      {note && (
        <p role="status" className="mt-5 flex items-center gap-2 rounded-2xl bg-genuine-soft p-4 font-semibold text-genuine">
          <CheckCircle2 className="size-5" aria-hidden="true" /> {note}
        </p>
      )}
      {shown.length ? (
        <ul className="mt-6 grid gap-4 lg:grid-cols-2">
          {shown.map((m) => (
            <ManufacturerCard
              key={`${m.id}-${m.verification_status}`}
              m={m}
              token={token}
              onChanged={(n) => {
                setNote(n);
                reload();
              }}
            />
          ))}
        </ul>
      ) : (
        <div className="mt-6">
          <Empty icon={ShieldCheck}>
            {filter === "PENDING" ? "No manufacturers are waiting for verification." : "Nothing here."}
          </Empty>
        </div>
      )}
    </section>
  );
}

// ---------------------------------------------------------------------------
// Issues
// ---------------------------------------------------------------------------

const I_FILTERS = ["OPEN", "REVIEWED", "CLOSED", "ALL"] as const;

function Issues({ token, list, reload }: { token: string; list: Issue[]; reload: () => void }) {
  const [filter, setFilter] = useState<(typeof I_FILTERS)[number]>("OPEN");
  const [error, setError] = useState("");
  const counts = useMemo(() => {
    const c: Partial<Record<(typeof I_FILTERS)[number], number>> = { ALL: list.length };
    for (const i of list) c[i.status] = (c[i.status] ?? 0) + 1;
    return c;
  }, [list]);
  const shown = list.filter((i) => filter === "ALL" || i.status === filter);
  const move = async (i: Issue, status: Issue["status"]) => {
    setError("");
    try {
      await api.setIssueStatus(token, i.id, status);
      reload();
    } catch (e) {
      setError(message(e));
    }
  };

  return (
    <section>
      <div className="flex flex-wrap items-end justify-between gap-4">
        <div>
          <h1 className="text-3xl font-extrabold">Customer issues</h1>
          <p className="mt-1 text-subtle">Problems customers raised from a scan report.</p>
        </div>
        <Filters value={filter} options={I_FILTERS} counts={counts} onChange={setFilter} />
      </div>
      {error && (
        <p role="alert" className="mt-4 font-semibold text-fake">
          {error}
        </p>
      )}
      {shown.length ? (
        <ul className="mt-6 grid gap-4">
          {shown.map((i) => (
            <li key={i.id} className={card}>
              <div className="flex flex-wrap items-center justify-between gap-3">
                <p className="font-mono text-sm font-semibold">
                  Product code {i.product_id}
                </p>
                <div className="flex items-center gap-3">
                  <span className="text-sm text-subtle">{when(i.created_at)}</span>
                  <Badge status={i.status} />
                </div>
              </div>
              <p className="mt-3 text-[15px] whitespace-pre-wrap">{i.message}</p>
              <p className="mt-3 flex flex-wrap gap-x-5 gap-y-1 text-sm text-subtle">
                {i.contact && <span>Contact: {i.contact}</span>}
                {i.latitude != null && i.longitude != null && (
                  <a
                    className="underline hover:text-brand"
                    target="_blank"
                    rel="noreferrer"
                    href={`https://www.openstreetmap.org/?mlat=${i.latitude}&mlon=${i.longitude}#map=11/${i.latitude}/${i.longitude}`}
                  >
                    Location {i.latitude.toFixed(3)}, {i.longitude.toFixed(3)}
                  </a>
                )}
              </p>
              <div className="mt-4 flex flex-wrap gap-2">
                {i.status === "OPEN" && (
                  <button type="button" className={btnDark} onClick={() => void move(i, "REVIEWED")}>
                    Mark reviewed
                  </button>
                )}
                {i.status !== "CLOSED" && (
                  <button type="button" className={btnGhost} onClick={() => void move(i, "CLOSED")}>
                    Close
                  </button>
                )}
                {i.status !== "OPEN" && (
                  <button type="button" className={btnGhost} onClick={() => void move(i, "OPEN")}>
                    Reopen
                  </button>
                )}
              </div>
            </li>
          ))}
        </ul>
      ) : (
        <div className="mt-6">
          <Empty icon={MessageSquareWarning}>No issues here.</Empty>
        </div>
      )}
    </section>
  );
}

// ---------------------------------------------------------------------------
// Products
// ---------------------------------------------------------------------------

function Products({ list, stats }: { list: Product[]; stats: Stats | null }) {
  const [q, setQ] = useState("");
  const shown = list.filter((p) =>
    `${p.product_name} ${p.product_id} ${p.manufacturer_name} ${p.batch_number}`.toLowerCase().includes(q.toLowerCase()),
  );
  const boxes: [string, number | undefined, string][] = [
    ["Products registered", list.length, "text-ink"],
    ["Scans", stats?.total_scans, "text-ink"],
    ["Genuine scans", stats?.genuine_count, "text-genuine"],
    ["Flagged scans", stats ? stats.suspicious_count + stats.counterfeit_count : undefined, "text-fake"],
  ];
  return (
    <section>
      <h1 className="text-3xl font-extrabold">Products</h1>
      <p className="mt-1 text-subtle">Everything manufacturers have registered.</p>
      <div className="mt-6 grid grid-cols-2 gap-4 lg:grid-cols-4">
        {boxes.map(([label, value, color]) => (
          <div key={label} className={card}>
            <p className="text-sm text-subtle">{label}</p>
            <p className={`mt-1 text-3xl font-extrabold ${color}`}>{value ?? "–"}</p>
          </div>
        ))}
      </div>
      <input
        value={q}
        onChange={(e) => setQ(e.target.value)}
        placeholder="Search by product, code, manufacturer or batch"
        className={`${field} mt-6`}
        aria-label="Search products"
      />
      {shown.length ? (
        <div className={`${card} mt-4 overflow-x-auto p-0 sm:p-0`}>
          <table className="w-full min-w-[720px] text-left text-sm">
            <thead className="border-b border-line text-subtle">
              <tr>
                {["Product", "Code", "Manufacturer", "Distributor", "Blockchain", "Registered"].map((h) => (
                  <th key={h} className="px-5 py-3 font-semibold">
                    {h}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody className="divide-y divide-line">
              {shown.map((p) => (
                <tr key={p.product_id}>
                  <td className="px-5 py-3">
                    <span className="font-semibold">{p.product_name}</span>
                    <span className="block text-xs text-subtle">
                      Batch {p.batch_number}
                      {p.sku && ` · SKU ${p.sku}`}
                    </span>
                  </td>
                  <td className="px-5 py-3 font-mono">{p.product_id}</td>
                  <td className="px-5 py-3">{p.manufacturer_name}</td>
                  <td className="px-5 py-3">
                    {p.distributors?.map((d) => [d.name, d.city].filter(Boolean).join(", ")).join("; ") || "–"}
                  </td>
                  <td className="px-5 py-3">
                    {p.is_onchain ? (
                      <span className="text-genuine">
                        {p.registration_block != null ? `Block ${p.registration_block}` : "On chain"}
                      </span>
                    ) : (
                      <span className="text-fake">Not on chain</span>
                    )}
                  </td>
                  <td className="px-5 py-3 whitespace-nowrap text-subtle">{when(p.created_at)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      ) : (
        <div className="mt-4">
          <Empty icon={Package}>No products yet.</Empty>
        </div>
      )}
    </section>
  );
}

// ---------------------------------------------------------------------------
// App
// ---------------------------------------------------------------------------

type Tab = "verification" | "issues" | "products";

export default function App() {
  const [token, setToken] = useState<string | null>(store.get);
  const [email, setEmail] = useState("");
  const [tab, setTab] = useState<Tab>("verification");
  const [mfrs, setMfrs] = useState<Manufacturer[]>([]);
  const [issues, setIssues] = useState<Issue[]>([]);
  const [products, setProducts] = useState<Product[]>([]);
  const [stats, setStats] = useState<Stats | null>(null);
  const [health, setHealth] = useState<api.Health | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const signIn = (t: string) => {
    store.set(t);
    setToken(t);
  };
  const signOut = useCallback(() => {
    store.set(null);
    setToken(null);
    setMfrs([]);
    setIssues([]);
  }, []);

  const load = useCallback(() => {
    if (!token) return;
    setLoading(true);
    setError("");
    Promise.all([
      api.me(token).then((m) => setEmail(m.email)),
      api.listManufacturers(token).then(setMfrs),
      api.listIssues(token).then(setIssues),
      api.listProducts(token).then(setProducts),
      api.scanStats(token).then(setStats),
      api.health().then(setHealth, () => setHealth(null)),
    ])
      .catch((e: unknown) => {
        if (e instanceof api.ApiError && (e.status === 401 || e.status === 403)) signOut();
        else setError(message(e));
      })
      .finally(() => setLoading(false));
  }, [token, signOut]);

  useEffect(() => {
    load();
    const t = window.setInterval(load, 30000);
    return () => window.clearInterval(t);
  }, [load]);

  if (!token) return <Login onToken={signIn} />;

  const pending = mfrs.filter((m) => m.verification_status === "PENDING").length;
  const open = issues.filter((i) => i.status === "OPEN").length;
  const tabs: [Tab, typeof ShieldCheck, string, number][] = [
    ["verification", ShieldCheck, "Verification", pending],
    ["issues", MessageSquareWarning, "Customer issues", open],
    ["products", Blocks, "Products", 0],
  ];
  const chainOk = health?.blockchain?.contract_accessible;
  const balance = health?.blockchain?.wallet_balance_eth;
  // Each product costs a little test ETH; warn before registrations start failing.
  const lowFunds = chainOk && balance != null && balance < 0.005;

  return (
    <div className="min-h-screen">
      <header className="sticky top-0 z-40 border-b border-line bg-surface/90 backdrop-blur">
        <div className="mx-auto flex max-w-[1280px] flex-wrap items-center justify-between gap-x-4 gap-y-2 px-5 py-3">
          <div className="flex items-center gap-3">
            <Logo />
            <span className="rounded-full bg-brand px-2.5 py-1 font-mono text-[10px] font-semibold tracking-widest text-white">
              ADMIN
            </span>
          </div>
          <nav aria-label="Sections" className="order-3 flex w-full gap-1 overflow-x-auto sm:order-none sm:w-auto">
            {tabs.map(([id, Icon, label, n]) => (
              <button
                key={id}
                type="button"
                aria-current={tab === id ? "page" : undefined}
                onClick={() => setTab(id)}
                className={`flex items-center gap-2 rounded-full px-4 py-2 text-sm font-semibold whitespace-nowrap transition-colors ${
                  tab === id ? "bg-brand-soft text-brand" : "text-subtle hover:text-ink"
                }`}
              >
                <Icon className="size-4" aria-hidden="true" />
                {label}
                {n > 0 && (
                  <span className="rounded-full bg-lime px-2 py-0.5 text-[11px] font-bold text-ink">{n}</span>
                )}
              </button>
            ))}
          </nav>
          <div className="flex items-center gap-3 text-sm">
            <span
              title={
                !chainOk
                  ? "Blockchain not reachable"
                  : `Blockchain connected, block ${health?.blockchain?.latest_block}` +
                    (balance != null ? `. Wallet: ${balance.toFixed(4)} test ETH` : "") +
                    (lowFunds ? ". Running low: top it up from a faucet (DEPLOY-RENDER.md, step 3)." : "")
              }
              className={`hidden items-center gap-1.5 rounded-full px-3 py-1 text-xs font-semibold md:flex ${
                !chainOk
                  ? "bg-fake-soft text-fake"
                  : lowFunds
                    ? "bg-warn-soft text-warn"
                    : "bg-genuine-soft text-genuine"
              }`}
            >
              <span
                className={`size-2 rounded-full ${!chainOk ? "bg-fake" : lowFunds ? "bg-warn" : "bg-genuine"}`}
              />
              {!chainOk ? "Blockchain offline" : lowFunds ? "Wallet low on test ETH" : "Blockchain online"}
              {chainOk && balance != null && (
                <span className="font-mono font-normal opacity-80">{balance.toFixed(3)} ETH</span>
              )}
            </span>
            <button type="button" onClick={load} aria-label="Refresh" className="rounded-full p-2 hover:bg-secondary">
              <RefreshCw className={`size-4 ${loading ? "animate-spin" : ""}`} />
            </button>
            <button type="button" onClick={signOut} className={btnGhost} title={email ? `Signed in as ${email}` : undefined}>
              <LogOut className="size-4" aria-hidden="true" /> Log out
            </button>
          </div>
        </div>
      </header>
      <main className="mx-auto max-w-[1280px] px-5 py-8">
        {error && (
          <p role="alert" className="mb-6 rounded-2xl bg-fake-soft p-4 font-semibold text-fake">
            {error}
          </p>
        )}
        {tab === "verification" && <Verification token={token} list={mfrs} reload={load} />}
        {tab === "issues" && <Issues token={token} list={issues} reload={load} />}
        {tab === "products" && <Products list={products} stats={stats} />}
      </main>
    </div>
  );
}
