/**
 * The AuthentiQ team's console. It is not linked anywhere on the site: it opens
 * when an ADMIN account logs in through the normal Manufacturers -> Log in form.
 */
import { useCallback, useEffect, useMemo, useState, type FormEvent, type ReactNode } from "react";
import {
  Building2,
  CheckCircle2,
  Clock,
  Download,
  FileText,
  History,
  Loader2,
  LogOut,
  MessageSquareWarning,
  PauseCircle,
  PlayCircle,
  RefreshCw,
  ShieldCheck,
  ShieldX,
  X,
} from "lucide-react";
import { ApiError } from "@/lib/api";
import * as team from "@/lib/adminApi";
import type { AuditEntry, Issue, Manufacturer, MfrStatus } from "@/lib/adminApi";
import { card, field, pillGhost, useHideSiteNav } from "@/components/Shell";

const btn =
  "inline-flex items-center justify-center gap-1.5 rounded-full px-3.5 py-1.5 text-xs font-semibold transition-all active:scale-[0.97] disabled:opacity-50";

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

const message = (e: unknown) => (e instanceof Error ? e.message : "Something went wrong.");

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
    <span
      className={`inline-block rounded-full px-2.5 py-0.5 font-mono text-[11px] font-semibold tracking-wider ${STATUS_STYLE[status] ?? "bg-secondary"}`}
    >
      {status}
    </span>
  );
}

function Modal({
  title,
  onClose,
  wide,
  children,
}: {
  title: ReactNode;
  onClose: () => void;
  wide?: boolean;
  children: ReactNode;
}) {
  useEffect(() => {
    const esc = (e: KeyboardEvent) => e.key === "Escape" && onClose();
    window.addEventListener("keydown", esc);
    return () => window.removeEventListener("keydown", esc);
  }, [onClose]);
  return (
    <div
      role="dialog"
      aria-modal="true"
      className="fixed inset-0 z-[60] flex items-center justify-center bg-ink/60 p-4"
      onClick={onClose}
    >
      <div
        className={`flex max-h-[90vh] w-full flex-col overflow-hidden rounded-3xl bg-surface ${wide ? "h-[88vh] max-w-4xl" : "max-w-md"}`}
        onClick={(e) => e.stopPropagation()}
      >
        <div className="flex items-center justify-between gap-3 border-b border-line px-5 py-4">
          <div className="font-bold">{title}</div>
          <button
            type="button"
            onClick={onClose}
            aria-label="Close"
            className="rounded-full p-2 hover:bg-secondary"
          >
            <X className="size-5" />
          </button>
        </div>
        {children}
      </div>
    </div>
  );
}

/** Shows the uploaded Aadhaar card (image or PDF) with a download button. */
function DocumentViewer({
  token,
  m,
  onClose,
}: {
  token: string;
  m: Manufacturer;
  onClose: () => void;
}) {
  const [doc, setDoc] = useState<{ url: string; type: string } | null>(null);
  const [error, setError] = useState("");
  useEffect(() => {
    let url = "";
    team
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
  return (
    <Modal
      wide
      onClose={onClose}
      title={
        <span className="flex flex-wrap items-center gap-3">
          {m.company_name}
          <span className="font-mono text-xs font-normal text-subtle">
            Aadhaar card · GSTIN {m.gstin}
          </span>
          {doc && (
            <a
              href={doc.url}
              download={`aadhaar-${m.gstin}`}
              className={`${btn} border border-line hover:border-brand`}
            >
              <Download className="size-3.5" aria-hidden="true" /> Download
            </a>
          )}
        </span>
      }
    >
      <div className="flex flex-1 items-center justify-center bg-secondary">
        {error ? (
          <p className="p-6 font-semibold text-fake">{error}</p>
        ) : !doc ? (
          <Loader2 className="size-8 animate-spin text-subtle" />
        ) : doc.type.startsWith("image/") ? (
          <img
            src={doc.url}
            alt="Uploaded Aadhaar card"
            className="max-h-full max-w-full object-contain"
          />
        ) : (
          <iframe src={doc.url} title="Uploaded Aadhaar card" className="size-full" />
        )}
      </div>
    </Modal>
  );
}

/** Small popup asking for the rejection reason, which the manufacturer sees. */
function RejectDialog({
  m,
  onCancel,
  onReject,
}: {
  m: Manufacturer;
  onCancel: () => void;
  onReject: (reason: string) => Promise<void>;
}) {
  const [reason, setReason] = useState("");
  const [busy, setBusy] = useState(false);
  const submit = async (e: FormEvent) => {
    e.preventDefault();
    setBusy(true);
    await onReject(reason.trim());
    setBusy(false);
  };
  return (
    <Modal title={`Reject ${m.company_name}`} onClose={onCancel}>
      <form onSubmit={(e) => void submit(e)} className="grid gap-4 p-5">
        <label className="grid gap-1.5 text-sm font-semibold">
          Reason (the manufacturer sees this)
          <textarea
            required
            autoFocus
            rows={3}
            value={reason}
            onChange={(e) => setReason(e.target.value)}
            className={field}
            placeholder="For example: the name on the Aadhaar card does not match the GST registration."
          />
        </label>
        <div className="flex justify-end gap-2">
          <button type="button" className={pillGhost} onClick={onCancel}>
            Cancel
          </button>
          <button
            type="submit"
            disabled={busy || !reason.trim()}
            className="inline-flex items-center justify-center rounded-full bg-fake px-6 py-3 text-[15px] font-semibold text-white disabled:opacity-50"
          >
            Reject
          </button>
        </div>
      </form>
    </Modal>
  );
}

// ---------------------------------------------------------------------------
// Manufacturers
// ---------------------------------------------------------------------------

const FILTERS = ["ALL", "PENDING", "APPROVED", "REJECTED", "SUSPENDED"] as const;
type Filter = (typeof FILTERS)[number];

function Manufacturers({
  token,
  list,
  reload,
}: {
  token: string;
  list: Manufacturer[];
  reload: () => void;
}) {
  const [filter, setFilter] = useState<Filter>("PENDING");
  const [viewing, setViewing] = useState<Manufacturer | null>(null);
  const [rejecting, setRejecting] = useState<Manufacturer | null>(null);
  const [busyId, setBusyId] = useState<number | null>(null);
  const [note, setNote] = useState<{ ok: boolean; text: string } | null>(null);

  const counts = useMemo(() => {
    const c: Partial<Record<Filter, number>> = { ALL: list.length };
    for (const m of list) c[m.verification_status] = (c[m.verification_status] ?? 0) + 1;
    return c;
  }, [list]);
  const shown = list
    .filter((m) => filter === "ALL" || m.verification_status === filter)
    .sort((a, b) => b.created_at.localeCompare(a.created_at));

  const change = async (m: Manufacturer, status: MfrStatus, reason?: string) => {
    setBusyId(m.id);
    setNote(null);
    try {
      await team.setManufacturerStatus(token, m.id, status, reason);
      setNote({ ok: true, text: `${m.company_name} is now ${status.toLowerCase()}.` });
      reload();
    } catch (e) {
      setNote({ ok: false, text: message(e) });
    } finally {
      setBusyId(null);
    }
  };

  return (
    <section>
      <div role="tablist" className="flex flex-wrap gap-2">
        {FILTERS.map((f) => (
          <button
            key={f}
            type="button"
            role="tab"
            aria-selected={filter === f}
            onClick={() => setFilter(f)}
            className={`rounded-full px-4 py-2 text-sm font-semibold transition-colors ${
              filter === f
                ? "bg-brand text-white"
                : "bg-surface text-ink ring-1 ring-line hover:ring-brand"
            }`}
          >
            {f.charAt(0) + f.slice(1).toLowerCase()}
            <span className="ml-1.5 opacity-70">{counts[f] ?? 0}</span>
          </button>
        ))}
      </div>

      {note && (
        <p
          role="status"
          className={`mt-4 flex items-center gap-2 rounded-2xl p-3 text-sm font-semibold ${note.ok ? "bg-genuine-soft text-genuine" : "bg-fake-soft text-fake"}`}
        >
          {note.ok && <CheckCircle2 className="size-4" aria-hidden="true" />} {note.text}
        </p>
      )}

      <div className={`${card} mt-4 overflow-x-auto !p-0`}>
        {shown.length ? (
          <table className="w-full min-w-[860px] text-left text-sm">
            <thead className="border-b border-line text-subtle">
              <tr>
                {["Company", "GSTIN", "Contact email", "Registered", "Status", "Actions"].map(
                  (h) => (
                    <th key={h} className="px-4 py-3 font-semibold">
                      {h}
                    </th>
                  ),
                )}
              </tr>
            </thead>
            <tbody className="divide-y divide-line">
              {shown.map((m) => {
                const s = m.verification_status;
                const busy = busyId === m.id;
                return (
                  <tr key={m.id} className="align-top">
                    <td className="px-4 py-3">
                      <span className="font-semibold">{m.company_name}</span>
                      <span className="block text-xs text-subtle">
                        {m.company_address} · {m.phone}
                      </span>
                      {m.rejection_reason && s !== "APPROVED" && (
                        <span className="mt-1 block text-xs text-fake">
                          Reason: {m.rejection_reason}
                        </span>
                      )}
                    </td>
                    <td className="px-4 py-3 font-mono">{m.gstin}</td>
                    <td className="px-4 py-3 break-all">{m.email}</td>
                    <td className="px-4 py-3 whitespace-nowrap text-subtle">
                      {when(m.created_at)}
                    </td>
                    <td className="px-4 py-3">
                      <Badge status={s} />
                    </td>
                    <td className="px-4 py-3">
                      <div className="flex flex-wrap gap-1.5">
                        <button
                          type="button"
                          onClick={() => setViewing(m)}
                          className={`${btn} border border-line hover:border-brand`}
                        >
                          <FileText className="size-3.5" aria-hidden="true" /> View document
                        </button>
                        {(s === "PENDING" || s === "REJECTED") && (
                          <button
                            type="button"
                            disabled={busy}
                            onClick={() => void change(m, "APPROVED")}
                            className={`${btn} bg-genuine text-white hover:brightness-110`}
                          >
                            <ShieldCheck className="size-3.5" aria-hidden="true" /> Approve
                          </button>
                        )}
                        {s === "PENDING" && (
                          <button
                            type="button"
                            disabled={busy}
                            onClick={() => setRejecting(m)}
                            className={`${btn} bg-fake text-white hover:brightness-110`}
                          >
                            <ShieldX className="size-3.5" aria-hidden="true" /> Reject
                          </button>
                        )}
                        {s === "APPROVED" && (
                          <button
                            type="button"
                            disabled={busy}
                            onClick={() =>
                              void change(m, "SUSPENDED", "Access suspended by the AuthentiQ team.")
                            }
                            className={`${btn} bg-[#d97706] text-white hover:brightness-110`}
                          >
                            <PauseCircle className="size-3.5" aria-hidden="true" /> Suspend
                          </button>
                        )}
                        {s === "SUSPENDED" && (
                          <button
                            type="button"
                            disabled={busy}
                            onClick={() => void change(m, "APPROVED")}
                            className={`${btn} border border-genuine text-genuine hover:bg-genuine-soft`}
                          >
                            <PlayCircle className="size-3.5" aria-hidden="true" /> Reactivate
                          </button>
                        )}
                        {busy && <Loader2 className="size-4 animate-spin text-subtle" />}
                      </div>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        ) : (
          <p className="p-10 text-center text-subtle">
            {filter === "PENDING"
              ? "No manufacturers are waiting for verification."
              : "No manufacturers here."}
          </p>
        )}
      </div>

      {viewing && <DocumentViewer token={token} m={viewing} onClose={() => setViewing(null)} />}
      {rejecting && (
        <RejectDialog
          m={rejecting}
          onCancel={() => setRejecting(null)}
          onReject={async (reason) => {
            await change(rejecting, "REJECTED", reason);
            setRejecting(null);
          }}
        />
      )}
    </section>
  );
}

// ---------------------------------------------------------------------------
// Customer issues
// ---------------------------------------------------------------------------

function Issues({ token, list, reload }: { token: string; list: Issue[]; reload: () => void }) {
  const [error, setError] = useState("");
  const move = async (i: Issue, status: Issue["status"]) => {
    setError("");
    try {
      await team.setIssueStatus(token, i.id, status);
      reload();
    } catch (e) {
      setError(message(e));
    }
  };
  if (!list.length)
    return (
      <p className={`${card} text-center text-subtle`}>No customer has raised an issue yet.</p>
    );
  return (
    <section className="grid gap-3">
      {error && <p className="font-semibold text-fake">{error}</p>}
      {list.map((i) => (
        <article key={i.id} className={`${card} !p-5`}>
          <div className="flex flex-wrap items-center justify-between gap-3">
            <p className="font-mono text-sm font-semibold">Product code {i.product_id}</p>
            <div className="flex items-center gap-3">
              <span className="text-sm text-subtle">{when(i.created_at)}</span>
              <Badge status={i.status} />
            </div>
          </div>
          <p className="mt-2 whitespace-pre-wrap">{i.message}</p>
          <p className="mt-2 flex flex-wrap gap-x-5 text-sm text-subtle">
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
          <div className="mt-3 flex flex-wrap gap-2">
            {i.status === "OPEN" && (
              <button
                type="button"
                className={`${btn} bg-brand text-white`}
                onClick={() => void move(i, "REVIEWED")}
              >
                Mark reviewed
              </button>
            )}
            {i.status !== "CLOSED" && (
              <button
                type="button"
                className={`${btn} border border-line`}
                onClick={() => void move(i, "CLOSED")}
              >
                Close
              </button>
            )}
            {i.status !== "OPEN" && (
              <button
                type="button"
                className={`${btn} border border-line`}
                onClick={() => void move(i, "OPEN")}
              >
                Reopen
              </button>
            )}
          </div>
        </article>
      ))}
    </section>
  );
}

// ---------------------------------------------------------------------------
// Audit log
// ---------------------------------------------------------------------------

const ACTION_STYLE: [RegExp, string][] = [
  [/APPROVED|REACTIVATED/, "bg-genuine-soft text-genuine"],
  [/REJECTED/, "bg-fake-soft text-fake"],
  [/SUSPENDED/, "bg-warn-soft text-warn"],
  [/REGISTERED/, "bg-brand-soft text-brand"],
];

function AuditLog({ list }: { list: AuditEntry[] }) {
  if (!list.length)
    return <p className={`${card} text-center text-subtle`}>No actions recorded yet.</p>;
  return (
    <div className={`${card} overflow-x-auto !p-0`}>
      <table className="w-full min-w-[760px] text-left text-sm">
        <thead className="border-b border-line text-subtle">
          <tr>
            {["When", "Action", "By", "Details"].map((h) => (
              <th key={h} className="px-4 py-3 font-semibold">
                {h}
              </th>
            ))}
          </tr>
        </thead>
        <tbody className="divide-y divide-line">
          {list.map((a) => (
            <tr key={a.id} className="align-top">
              <td className="px-4 py-3 whitespace-nowrap text-subtle">{when(a.created_at)}</td>
              <td className="px-4 py-3">
                <span
                  className={`inline-block rounded-full px-2.5 py-0.5 font-mono text-[11px] font-semibold ${ACTION_STYLE.find(([re]) => re.test(a.action))?.[1] ?? "bg-secondary text-subtle"}`}
                >
                  {a.action.replaceAll("_", " ")}
                </span>
              </td>
              <td className="px-4 py-3 break-all">{a.user_email ?? "System"}</td>
              <td className="px-4 py-3">{a.description}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

// ---------------------------------------------------------------------------
// Console
// ---------------------------------------------------------------------------

type Tab = "manufacturers" | "issues" | "audit";

export default function TeamConsole({ token, onLogout }: { token: string; onLogout: () => void }) {
  useHideSiteNav();
  const [tab, setTab] = useState<Tab>("manufacturers");
  const [email, setEmail] = useState("");
  const [mfrs, setMfrs] = useState<Manufacturer[]>([]);
  const [issues, setIssues] = useState<Issue[]>([]);
  const [audit, setAudit] = useState<AuditEntry[]>([]);
  const [chain, setChain] = useState<team.ChainHealth["blockchain"] | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const load = useCallback(() => {
    setLoading(true);
    setError("");
    Promise.all([
      team.adminMe(token).then((m) => setEmail(m.email)),
      team.listManufacturers(token).then(setMfrs),
      team.listIssues(token).then(setIssues),
      team.listAuditLogs(token).then(setAudit),
      team.chainHealth().then(
        (h) => setChain(h.blockchain ?? null),
        () => setChain(null),
      ),
    ])
      .catch((e: unknown) => {
        if (e instanceof ApiError && (e.status === 401 || e.status === 403)) onLogout();
        else setError(message(e));
      })
      .finally(() => setLoading(false));
  }, [token, onLogout]);

  useEffect(() => {
    load();
    const t = window.setInterval(load, 30000);
    return () => window.clearInterval(t);
  }, [load]);

  const count = (s: MfrStatus) => mfrs.filter((m) => m.verification_status === s).length;
  const pending = count("PENDING");
  const openIssues = issues.filter((i) => i.status === "OPEN").length;
  const stats: [string, number, typeof Building2, string, boolean][] = [
    ["Registered manufacturers", mfrs.length, Building2, "text-ink", false],
    ["Pending approvals", pending, Clock, "text-warn", pending > 0],
    ["Approved companies", count("APPROVED"), ShieldCheck, "text-genuine", false],
    ["Suspended accounts", count("SUSPENDED"), PauseCircle, "text-subtle", false],
  ];
  const tabs: [Tab, string, typeof Building2, number][] = [
    ["manufacturers", "Manufacturers", Building2, pending],
    ["issues", "Customer issues", MessageSquareWarning, openIssues],
    ["audit", "Audit log", History, 0],
  ];
  const balance = chain?.wallet_balance_eth;
  const lowFunds = chain?.contract_accessible && balance != null && balance < 0.005;

  return (
    <div className="mx-auto max-w-[1180px]">
      <div className="flex flex-wrap items-end justify-between gap-4">
        <div>
          <p className="font-mono text-xs tracking-widest text-subtle">AUTHENTIQ TEAM</p>
          <h1 className="mt-1 text-3xl font-extrabold sm:text-4xl">Verification console</h1>
          <p className="mt-1 text-sm text-subtle">Signed in as {email || "…"}</p>
        </div>
        <div className="flex flex-wrap items-center gap-2">
          <span
            title={
              chain?.contract_accessible
                ? `Block ${chain.latest_block}${balance != null ? ` · wallet ${balance.toFixed(4)} test ETH` : ""}`
                : "The blockchain cannot be reached"
            }
            className={`flex items-center gap-1.5 rounded-full px-3 py-1.5 text-xs font-semibold ${
              !chain?.contract_accessible
                ? "bg-fake-soft text-fake"
                : lowFunds
                  ? "bg-warn-soft text-warn"
                  : "bg-genuine-soft text-genuine"
            }`}
          >
            <span
              className={`size-2 rounded-full ${!chain?.contract_accessible ? "bg-fake" : lowFunds ? "bg-warn" : "bg-genuine"}`}
            />
            {!chain?.contract_accessible
              ? "Blockchain offline"
              : lowFunds
                ? "Wallet low on test ETH"
                : "Blockchain online"}
            {chain?.contract_accessible && balance != null && (
              <span className="font-mono font-normal opacity-80">{balance.toFixed(3)} ETH</span>
            )}
          </span>
          <button
            type="button"
            onClick={load}
            aria-label="Refresh"
            className="rounded-full p-2.5 hover:bg-secondary"
          >
            <RefreshCw className={`size-4 ${loading ? "animate-spin" : ""}`} />
          </button>
          <button type="button" onClick={onLogout} className={pillGhost}>
            <LogOut className="mr-2 size-4" aria-hidden="true" /> Log out
          </button>
        </div>
      </div>

      {error && (
        <p role="alert" className="mt-6 rounded-2xl bg-fake-soft p-4 font-semibold text-fake">
          {error}
        </p>
      )}

      <div className="mt-6 grid grid-cols-2 gap-4 lg:grid-cols-4">
        {stats.map(([label, value, Icon, color, attention]) => (
          <div
            key={label}
            className={`${card} relative !p-5 ${attention ? "ring-2 ring-lime" : ""}`}
          >
            <Icon className={`size-6 ${color}`} strokeWidth={1.6} aria-hidden="true" />
            <p className={`mt-3 text-3xl font-extrabold ${color}`}>{value}</p>
            <p className="text-sm text-subtle">{label}</p>
            {attention && (
              <span className="absolute top-4 right-4 flex items-center gap-1.5 rounded-full bg-lime px-2.5 py-1 text-[11px] font-bold text-ink">
                <span className="size-1.5 animate-pulse rounded-full bg-ink" /> Needs attention
              </span>
            )}
          </div>
        ))}
      </div>

      <nav aria-label="Console sections" className="mt-8 flex flex-wrap gap-1 border-b border-line">
        {tabs.map(([id, label, Icon, n]) => (
          <button
            key={id}
            type="button"
            aria-current={tab === id ? "page" : undefined}
            onClick={() => setTab(id)}
            className={`-mb-px flex items-center gap-2 border-b-2 px-4 py-3 text-sm font-semibold transition-colors ${
              tab === id
                ? "border-brand text-brand"
                : "border-transparent text-subtle hover:text-ink"
            }`}
          >
            <Icon className="size-4" aria-hidden="true" />
            {label}
            {n > 0 && (
              <span className="rounded-full bg-lime px-2 py-0.5 text-[11px] font-bold text-ink">
                {n}
              </span>
            )}
          </button>
        ))}
      </nav>

      <div className="mt-6">
        {tab === "manufacturers" && <Manufacturers token={token} list={mfrs} reload={load} />}
        {tab === "issues" && <Issues token={token} list={issues} reload={load} />}
        {tab === "audit" && <AuditLog list={audit} />}
      </div>
    </div>
  );
}
