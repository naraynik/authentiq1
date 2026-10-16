import { useCallback, useEffect, useState, type FormEvent, type ReactNode } from "react";
import {
  Blocks,
  Building2,
  Clock,
  FileText,
  Loader2,
  MapPin,
  Package,
  Plus,
  ShieldX,
  Truck,
  X,
} from "lucide-react";
import type { Product } from "@/lib/samples";
import {
  ApiError,
  getProfile,
  listMyProducts,
  login,
  registerManufacturer,
  registerProduct,
  type Place,
  type Profile,
  type Role,
} from "@/lib/api";
import { card, field, pill, pillGhost } from "@/components/Shell";
import TeamConsole from "@/components/TeamConsole";
import { DEMO_LOGINS, PREVIEW } from "@/lib/preview";

type Stage = "register" | "login";

/** The login is kept in this browser so a page reload does not log you out. */
type Session = { token: string; role: Role };
const SESSION_KEY = "authentiq.session";
const readSession = (): Session | null => {
  try {
    const s = JSON.parse(localStorage.getItem(SESSION_KEY) ?? "null") as Session | null;
    return s?.token && s.role ? s : null;
  } catch {
    return null;
  }
};
const writeSession = (s: Session | null) => {
  try {
    if (s) localStorage.setItem(SESSION_KEY, JSON.stringify(s));
    else localStorage.removeItem(SESSION_KEY);
  } catch {
    /* storage blocked: the session just lasts until reload */
  }
};

const message = (err: unknown) =>
  err instanceof Error ? err.message : "Something went wrong. Try again.";

/** Password rule enforced by the backend (app/core/security.py). */
const PASSWORD_PATTERN = "(?=.*[a-z])(?=.*[A-Z])(?=.*\\d)(?=.*[^A-Za-z0-9]).{8,}";

const label = "grid gap-1.5 text-sm font-semibold";

const STEPS = ["GST ID and Aadhaar", "Manual verification", "Add products"];

/** Three-step progress strip: submit documents, get verified, add products. */
function Steps({ current }: { current: number }) {
  return (
    <ol className="mt-8 grid grid-cols-3 gap-2 text-center text-xs font-semibold sm:text-sm">
      {STEPS.map((s, i) => (
        <li
          key={s}
          aria-current={i === current ? "step" : undefined}
          className={`rounded-2xl px-2 py-3 ${
            i < current
              ? "bg-genuine-soft text-genuine"
              : i === current
                ? "bg-brand text-white"
                : "bg-secondary text-subtle"
          }`}
        >
          <span className="block font-mono text-[11px] opacity-80">STEP {i + 1}</span>
          {s}
        </li>
      ))}
    </ol>
  );
}

function Auth({ onSignIn }: { onSignIn: (session: Session) => void }) {
  const [stage, setStage] = useState<Stage>("register");
  const [file, setFile] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const isRegister = stage === "register";

  const submit = async (e: FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    const data = new FormData(e.currentTarget);
    const email = String(data.get("email")).trim();
    const password = String(data.get("password"));
    setBusy(true);
    setError("");
    try {
      if (isRegister) {
        data.set("gstin", String(data.get("gstin")).trim().toUpperCase());
        await registerManufacturer(data);
      }
      // Log straight in after registering, so the pending screen can check the status.
      onSignIn(await login(email, password));
    } catch (err) {
      setError(message(err));
    } finally {
      setBusy(false);
    }
  };

  return (
    <div className="mx-auto max-w-[560px]">
      <div className="text-center">
        <h1 className="text-4xl font-extrabold sm:text-5xl">For manufacturers</h1>
        <p className="mx-auto mt-4 max-w-md text-lg">
          Store your products on the AuthentiQ blockchain so customers can check them.
        </p>
      </div>

      <Steps current={0} />

      <div className={`${card} mt-6`}>
        <div role="tablist" className="grid grid-cols-2 rounded-full bg-brand-soft p-1">
          {(["register", "login"] as const).map((s) => (
            <button
              key={s}
              type="button"
              role="tab"
              aria-selected={stage === s}
              onClick={() => {
                setStage(s);
                setError("");
              }}
              className={`rounded-full py-2.5 text-sm font-semibold transition-colors ${
                stage === s ? "bg-brand text-white" : "text-ink hover:text-brand"
              }`}
            >
              {s === "register" ? "Register" : "Log in"}
            </button>
          ))}
        </div>

        {PREVIEW && !isRegister && (
          <div className="mt-5 rounded-2xl bg-brand-soft p-4 text-sm text-ink">
            <p className="font-semibold">Demo accounts (sample data)</p>
            <p className="mt-1">
              Manufacturer: <code>{DEMO_LOGINS.manufacturer.email}</code> /{" "}
              <code>{DEMO_LOGINS.manufacturer.password}</code>
            </p>
            <p>
              AuthentiQ team: <code>{DEMO_LOGINS.team.email}</code> /{" "}
              <code>{DEMO_LOGINS.team.password}</code>
            </p>
          </div>
        )}

        <form onSubmit={(e) => void submit(e)} className="mt-7 grid gap-4">
          {isRegister && (
            <>
              <label className={label}>
                Company name
                <input name="company_name" required className={field} autoComplete="organization" />
              </label>
              <label className={label}>
                GST ID (GSTIN)
                <input
                  name="gstin"
                  required
                  maxLength={15}
                  pattern="[0-9]{2}[A-Za-z]{5}[0-9]{4}[A-Za-z][A-Za-z0-9][Zz][A-Za-z0-9]"
                  title="15 characters, for example 27ABCDE1234F1Z5"
                  placeholder="27ABCDE1234F1Z5"
                  className={`${field} font-mono uppercase placeholder:normal-case`}
                  autoComplete="off"
                />
                <span className="font-normal text-subtle">
                  15 characters, as on your GST certificate.
                </span>
              </label>
              <label className={label}>
                Registered company address
                <input
                  name="company_address"
                  required
                  className={field}
                  autoComplete="street-address"
                  placeholder="Plot 14, MIDC, Nashik, Maharashtra"
                />
              </label>
              <label className={label}>
                Phone number
                <input
                  name="phone"
                  type="tel"
                  required
                  className={field}
                  autoComplete="tel"
                  placeholder="+91 98765 43210"
                />
              </label>
            </>
          )}
          <label className={label}>
            Work email
            <input name="email" type="email" required className={field} autoComplete="email" />
          </label>
          <label className={label}>
            Password
            <input
              name="password"
              type="password"
              required
              minLength={8}
              pattern={isRegister ? PASSWORD_PATTERN : undefined}
              title={
                isRegister
                  ? "At least 8 characters with an uppercase letter, a lowercase letter, a number and a symbol"
                  : undefined
              }
              className={field}
              autoComplete={isRegister ? "new-password" : "current-password"}
            />
            {isRegister && (
              <span className="font-normal text-subtle">
                At least 8 characters, with an uppercase letter, a lowercase letter, a number and a
                symbol.
              </span>
            )}
          </label>
          {isRegister && (
            <label className={label}>
              Aadhaar card (PDF, PNG or JPG, up to 5 MB)
              <span className="flex cursor-pointer items-center gap-3 rounded-xl border border-dashed border-brand/60 bg-brand-soft px-4 py-4 font-normal">
                <FileText className="size-6 flex-none text-brand" aria-hidden="true" />
                <span>{file || "Choose a file. Our team checks it by hand before approval."}</span>
                <input
                  type="file"
                  name="verification_document"
                  accept=".pdf,.png,.jpg,.jpeg"
                  required
                  className="sr-only"
                  onChange={(e) => setFile(e.target.files?.[0]?.name ?? "")}
                />
              </span>
            </label>
          )}
          {error && (
            <p role="alert" className="rounded-xl bg-fake-soft p-4 text-sm font-semibold text-fake">
              {error}
            </p>
          )}
          <button type="submit" className={`${pill} mt-2`} disabled={busy}>
            {busy ? "Please wait…" : isRegister ? "Submit for verification" : "Log in"}
          </button>
        </form>
      </div>
    </div>
  );
}

type Distributor = { name: string; street: string; city: string; country: string; coords: string };
type Item = { name: string; sku: string; batch: string; code: string };

const emptyDistributor: Distributor = { name: "", street: "", city: "", country: "", coords: "" };
const emptyItem: Item = { name: "", sku: "", batch: "", code: "" };

/** "19.0760, 72.8777" -> {lat, lon}; empty -> {}; anything else -> null (invalid). */
function parseCoords(text: string): { lat?: number; lon?: number } | null {
  if (!text.trim()) return {};
  const m = text.trim().match(/^(-?\d+(?:\.\d+)?)\s*,\s*(-?\d+(?:\.\d+)?)$/);
  if (!m) return null;
  const lat = Number(m[1]);
  const lon = Number(m[2]);
  return Math.abs(lat) <= 90 && Math.abs(lon) <= 180 ? { lat, lon } : null;
}

function Section({
  icon: Icon,
  title,
  hint,
  children,
}: {
  icon: typeof Blocks;
  title: string;
  hint: string;
  children: ReactNode;
}) {
  return (
    <section className={card}>
      <div className="flex items-center gap-4">
        <span className="flex size-12 flex-none items-center justify-center rounded-2xl bg-brand-soft text-brand">
          <Icon className="size-6" strokeWidth={1.6} aria-hidden="true" />
        </span>
        <div>
          <h2 className="text-xl font-bold">{title}</h2>
          <p className="text-sm text-subtle">{hint}</p>
        </div>
      </div>
      <div className="mt-6">{children}</div>
    </section>
  );
}

/** Labelled text input bound to one key of a small form object. */
function Field<T extends Record<string, string>>({
  text,
  k,
  value,
  set,
  placeholder,
  wide,
  readOnly,
}: {
  text: string;
  k: keyof T & string;
  value: T;
  set: (v: T) => void;
  placeholder: string;
  wide?: boolean;
  readOnly?: boolean;
}) {
  return (
    <label className={`${label} ${wide ? "sm:col-span-2" : ""}`}>
      {text}
      <input
        value={value[k]}
        onChange={(e) => set({ ...value, [k]: e.target.value })}
        placeholder={placeholder}
        readOnly={readOnly}
        className={`${field} ${readOnly ? "bg-secondary text-subtle" : ""}`}
      />
    </label>
  );
}

const grid = "grid gap-4 sm:grid-cols-2";
const addBtn =
  "mt-5 inline-flex items-center gap-2 rounded-full border-2 border-brand bg-surface px-5 py-2.5 text-sm font-semibold text-brand transition-colors hover:bg-brand hover:text-white";
const chip = "flex items-center justify-between gap-3 rounded-xl bg-secondary px-4 py-3 text-sm";

type Stored = { name: string; code: string; block: number | null; error?: string };

function Dashboard({
  token,
  profile,
  onLogout,
}: {
  token: string;
  profile: Profile;
  onLogout: () => void;
}) {
  const company = profile.company_name;
  const [details, setDetails] = useState({
    company,
    gst: profile.gstin,
    email: profile.email,
  });
  const [facility, setFacility] = useState({ street: "", city: "", country: "", coords: "" });
  const [dist, setDist] = useState(emptyDistributor);
  const [distributors, setDistributors] = useState<Distributor[]>([]);
  const [item, setItem] = useState(emptyItem);
  const [items, setItems] = useState<Item[]>([]);
  const [error, setError] = useState("");
  const [stored, setStored] = useState<Stored[]>([]);
  const [products, setProducts] = useState<Product[]>([]);
  const [open, setOpen] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  const refresh = useCallback(() => {
    listMyProducts(token)
      .then(setProducts)
      .catch((err: unknown) => setError(message(err)));
  }, [token]);
  useEffect(refresh, [refresh]);

  const addDistributor = () => {
    if (!dist.name.trim() || !dist.city.trim())
      return setError("Enter at least the distributor name and city, then add the distributor.");
    if (!parseCoords(dist.coords))
      return setError(
        "Write distributor coordinates as latitude, longitude, e.g. 19.0760, 72.8777.",
      );
    setDistributors([...distributors, dist]);
    setDist(emptyDistributor);
    setError("");
  };
  const addItem = () => {
    if (!item.name.trim() || !item.batch.trim())
      return setError("Enter at least the product name and batch / serial, then add the product.");
    setItems([...items, item]);
    setItem(emptyItem);
    setError("");
  };
  const useLocation = () =>
    navigator.geolocation?.getCurrentPosition(
      (p) =>
        setFacility((f) => ({
          ...f,
          coords: `${p.coords.latitude.toFixed(4)}, ${p.coords.longitude.toFixed(4)}`,
        })),
      () => setError("Could not read your location. Type the coordinates instead."),
    );

  const submit = async (e: FormEvent) => {
    e.preventDefault();
    if (busy) return;
    if (!items.length || !distributors.length)
      return setError("Add at least one distributor and one product before you submit.");
    const facilityCoords = parseCoords(facility.coords);
    if (!facilityCoords)
      return setError(
        "Write the facility coordinates as latitude, longitude, e.g. 19.0760, 72.8777.",
      );
    const toPlace = (d: Distributor | typeof facility, name?: string): Place => ({
      name: name || undefined,
      street: d.street.trim() || undefined,
      city: d.city.trim() || undefined,
      country: d.country.trim() || undefined,
      ...parseCoords(d.coords),
    });
    setBusy(true);
    setError("");
    // One request per product, one after another (each is a blockchain transaction).
    const results: Stored[] = [];
    const failed: Item[] = [];
    for (const it of items) {
      try {
        const r = await registerProduct(token, {
          product_id: it.code.trim() || undefined,
          product_name: it.name.trim(),
          batch_number: it.batch.trim(),
          sku: it.sku.trim() || undefined,
          facility: toPlace(facility),
          distributors: distributors.map((d) => toPlace(d, d.name.trim())),
        });
        results.push({ name: it.name, code: r.product_id, block: r.block_number });
      } catch (err) {
        results.push({ name: it.name, code: it.code, block: null, error: message(err) });
        failed.push(it);
        if (err instanceof ApiError && err.status === 401) break;
      }
    }
    setStored(results);
    setItems(failed); // keep the ones that failed so they can be fixed and sent again
    if (!failed.length) setDistributors([]);
    setBusy(false);
    refresh();
  };

  return (
    <div className="mx-auto max-w-[860px]">
      <div className="flex flex-wrap items-end justify-between gap-4">
        <div>
          <p className="font-mono text-xs tracking-widest text-genuine">
            VERIFIED MANUFACTURER · {company}
          </p>
          <h1 className="mt-1 text-3xl font-extrabold sm:text-4xl">Register your products</h1>
          <p className="mt-2 max-w-xl">
            Add your company, distributor locations, facility and products. They are stored on the
            AuthentiQ blockchain.
          </p>
        </div>
        <button type="button" className={pillGhost} onClick={onLogout}>
          Log out
        </button>
      </div>

      <form onSubmit={(e) => void submit(e)} className="mt-8 grid gap-5" noValidate>
        <Section
          icon={Building2}
          title="Company details"
          hint="From your verified account. Contact AuthentiQ to change them."
        >
          <div className={grid}>
            <Field
              text="Company name"
              k="company"
              readOnly
              value={details}
              set={setDetails}
              placeholder="Acme Electronics Pvt Ltd"
            />
            <Field
              text="GST number"
              k="gst"
              readOnly
              value={details}
              set={setDetails}
              placeholder="27AAECA1234F1Z5"
            />
            <Field
              text="Contact email"
              k="email"
              readOnly
              value={details}
              set={setDetails}
              placeholder="trust@acme.co"
            />
          </div>
        </Section>

        <Section
          icon={Truck}
          title="Distributor locations"
          hint="Add each distributor stop on a product's journey."
        >
          {distributors.length > 0 && (
            <ul className="mb-5 grid gap-2">
              {distributors.map((d, i) => (
                <li key={i} className={chip}>
                  <span>
                    <strong>{d.name}</strong> ·{" "}
                    {[d.street, d.city, d.country].filter(Boolean).join(", ")}
                  </span>
                  <button
                    type="button"
                    aria-label={`Remove ${d.name}`}
                    onClick={() => setDistributors(distributors.filter((_, j) => j !== i))}
                    className="text-subtle hover:text-fake"
                  >
                    <X className="size-4" />
                  </button>
                </li>
              ))}
            </ul>
          )}
          <div className={grid}>
            <Field
              text="Distributor name"
              k="name"
              value={dist}
              set={setDist}
              placeholder="Northstar Distribution"
            />
            <Field
              text="Street address"
              k="street"
              value={dist}
              set={setDist}
              placeholder="Warehouse 8, Logistics Park"
            />
            <Field text="City" k="city" value={dist} set={setDist} placeholder="Dubai" />
            <Field
              text="Country"
              k="country"
              value={dist}
              set={setDist}
              placeholder="United Arab Emirates"
            />
            <Field
              text="Coordinates (optional)"
              k="coords"
              value={dist}
              set={setDist}
              placeholder="25.2048, 55.2708"
            />
          </div>
          <button type="button" className={addBtn} onClick={addDistributor}>
            <Plus className="size-4" aria-hidden="true" />
            Add distributor
          </button>
        </Section>

        <Section
          icon={MapPin}
          title="Facility location"
          hint="Where these products are manufactured."
        >
          <div className={grid}>
            <Field
              wide
              text="Street address"
              k="street"
              value={facility}
              set={setFacility}
              placeholder="Plot 14, MIDC Industrial Area"
            />
            <Field text="City" k="city" value={facility} set={setFacility} placeholder="Mumbai" />
            <Field
              text="Country"
              k="country"
              value={facility}
              set={setFacility}
              placeholder="India"
            />
            <Field
              text="Coordinates"
              k="coords"
              value={facility}
              set={setFacility}
              placeholder="19.0760, 72.8777"
            />
          </div>
          <button type="button" className={addBtn} onClick={useLocation}>
            <MapPin className="size-4" aria-hidden="true" />
            Use my current location
          </button>
        </Section>

        <Section
          icon={Package}
          title="Products"
          hint="Use the code already printed in your product's QR, or leave it blank and we create one."
        >
          {items.length > 0 && (
            <ul className="mb-5 grid gap-2">
              {items.map((it, i) => (
                <li key={i} className={chip}>
                  <span>
                    <strong>{it.name}</strong> ·{" "}
                    {[it.sku, it.batch, it.code].filter(Boolean).join(" · ")}
                  </span>
                  <button
                    type="button"
                    aria-label={`Remove ${it.name}`}
                    onClick={() => setItems(items.filter((_, j) => j !== i))}
                    className="text-subtle hover:text-fake"
                  >
                    <X className="size-4" />
                  </button>
                </li>
              ))}
            </ul>
          )}
          <div className={grid}>
            <Field
              text="Product name"
              k="name"
              value={item}
              set={setItem}
              placeholder="Premium Wireless Headphones"
            />
            <Field text="SKU" k="sku" value={item} set={setItem} placeholder="ACM-HP-220" />
            <Field
              text="Batch / serial"
              k="batch"
              value={item}
              set={setItem}
              placeholder="B-2026-09"
            />
            <Field
              text="Code in your QR (optional)"
              k="code"
              value={item}
              set={setItem}
              placeholder="Leave blank to create one"
            />
          </div>
          <button type="button" className={addBtn} onClick={addItem}>
            <Plus className="size-4" aria-hidden="true" />
            Add product
          </button>
        </Section>

        {error && (
          <p role="alert" className="rounded-xl bg-fake-soft p-4 text-sm font-semibold text-fake">
            {error}
          </p>
        )}
        <div className="flex flex-wrap items-center gap-4">
          <button type="submit" className={pill} disabled={busy}>
            {busy ? (
              <>
                <Loader2 className="mr-2 size-4 animate-spin" aria-hidden="true" />
                Storing on the blockchain…
              </>
            ) : (
              "Submit registration"
            )}
          </button>
          <span className="text-sm text-subtle">
            {items.length} {items.length === 1 ? "product" : "products"} · {distributors.length}{" "}
            {distributors.length === 1 ? "distributor" : "distributors"} added
          </span>
        </div>
        {stored.length > 0 && (
          <div role="status" className="grid gap-3">
            {stored.some((p) => !p.error) && (
              <div className="rounded-2xl bg-genuine-soft p-5 text-genuine">
                <p className="font-bold">Stored on the blockchain:</p>
                <ul className="mt-2 space-y-1 text-sm">
                  {stored
                    .filter((p) => !p.error)
                    .map((p) => (
                      <li key={p.code}>
                        {p.name} · code <span className="font-mono font-semibold">{p.code}</span>
                        {p.block != null && <> · block {p.block}</>}
                      </li>
                    ))}
                </ul>
                <p className="mt-3 text-sm text-ink">
                  Put each code in the QR printed on that product. Customers scan it to see the
                  report.
                </p>
              </div>
            )}
            {stored.some((p) => p.error) && (
              <div className="rounded-2xl bg-fake-soft p-5 text-fake">
                <p className="font-bold">
                  Not stored (still in the list above, fix and submit again):
                </p>
                <ul className="mt-2 space-y-1 text-sm">
                  {stored
                    .filter((p) => p.error)
                    .map((p, i) => (
                      <li key={i}>
                        {p.name}: {p.error}
                      </li>
                    ))}
                </ul>
              </div>
            )}
          </div>
        )}
      </form>

      {products.length > 0 && (
        <div className={`${card} mt-8`}>
          <h2 className="flex items-center gap-2 text-xl font-bold">
            <Blocks className="size-6 text-brand" aria-hidden="true" />
            Your registered products
          </h2>
          <ul className="mt-4 divide-y divide-line">
            {products.map((p) => (
              <li key={p.code} className="py-4">
                <button
                  type="button"
                  aria-expanded={open === p.code}
                  onClick={() => setOpen(open === p.code ? null : p.code)}
                  className="flex w-full flex-wrap items-center justify-between gap-3 text-left"
                >
                  <span>
                    <span className="block font-bold">{p.name}</span>
                    <span className="text-sm text-subtle">
                      <span className="font-mono">{p.code}</span> · Batch {p.batch}
                      {p.sku && <> · SKU {p.sku}</>} ·{" "}
                      {p.distributors.map((d) => d.name).join(", ")}
                    </span>
                  </span>
                  {p.anomalies.length > 0 && (
                    <span className="rounded-full bg-fake-soft px-3 py-1 text-sm font-semibold text-fake">
                      Anomaly
                    </span>
                  )}
                </button>
                {open === p.code && (
                  <div className="mt-4 rounded-2xl bg-secondary p-4 text-sm">
                    <p className="font-mono break-all text-subtle">
                      {p.txHash
                        ? `${p.block != null ? `Block ${p.block} · ` : ""}${p.txHash}`
                        : "Not on the blockchain yet"}
                    </p>
                    {p.explorerUrl && (
                      <a
                        href={p.explorerUrl}
                        target="_blank"
                        rel="noreferrer"
                        className="mt-1 inline-block font-semibold text-brand underline"
                      >
                        View on Etherscan ↗
                      </a>
                    )}
                    {p.distributors.map((d, i) => (
                      <p key={i} className="mt-2">
                        Distributor: {[d.name, d.address].filter(Boolean).join(", ")}
                      </p>
                    ))}
                    {p.facility && <p className="mt-1">Facility: {p.facility}</p>}
                    {p.anomalies.map((a) => (
                      <p
                        key={a}
                        className="mt-3 rounded-lg bg-fake-soft p-3 font-semibold text-fake"
                      >
                        {a}
                      </p>
                    ))}
                  </div>
                )}
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
}

export default function ManufacturerPage() {
  const [session, setSession] = useState<Session | null>(readSession);
  const token = session?.token ?? null;
  const [profile, setProfile] = useState<Profile | null>(null);
  const [checking, setChecking] = useState(false);
  const [error, setError] = useState("");

  const signIn = (s: Session) => {
    writeSession(s);
    setSession(s);
  };
  const logout = useCallback(() => {
    writeSession(null);
    setSession(null);
    setProfile(null);
    setError("");
  }, []);

  const check = useCallback(() => {
    if (!token || session?.role !== "MANUFACTURER") return;
    setChecking(true);
    setError("");
    getProfile(token)
      .then(setProfile)
      .catch((err: unknown) => {
        if (err instanceof ApiError && (err.status === 401 || err.status === 403)) logout();
        else setError(message(err));
      })
      .finally(() => setChecking(false));
  }, [token, session?.role, logout]);
  useEffect(check, [check]);

  const status = profile?.verification_status;

  return (
    <div className="px-5 pt-32 pb-24">
      {!token ? (
        <Auth onSignIn={signIn} />
      ) : session?.role === "ADMIN" ? (
        <TeamConsole token={token} onLogout={logout} />
      ) : status === "APPROVED" ? (
        <Dashboard token={token} profile={profile!} onLogout={logout} />
      ) : !profile ? (
        <div className={`${card} mx-auto max-w-[560px] text-center`}>
          {error ? (
            <>
              <p role="alert" className="font-semibold text-fake">
                {error}
              </p>
              <div className="mt-5 flex flex-wrap justify-center gap-3">
                <button type="button" className={pill} onClick={check}>
                  Try again
                </button>
                <button type="button" className={pillGhost} onClick={logout}>
                  Log out
                </button>
              </div>
            </>
          ) : (
            <p className="flex items-center justify-center gap-2 text-subtle">
              <Loader2 className="size-5 animate-spin" aria-hidden="true" /> Loading your account…
            </p>
          )}
        </div>
      ) : (
        <div className="mx-auto max-w-[560px]">
          <Steps current={1} />
          <div className={`${card} mt-6 text-center`}>
            {status === "PENDING" ? (
              <>
                <Clock
                  className="mx-auto size-12 text-brand"
                  strokeWidth={1.3}
                  aria-hidden="true"
                />
                <h1 className="mt-4 text-3xl font-extrabold">Verification pending</h1>
                <p className="mx-auto mt-3 max-w-md">
                  Thank you, {profile.company_name}. Our team is checking your GST ID and Aadhaar
                  card by hand. You can add products once your account is verified.
                </p>
              </>
            ) : (
              <>
                <ShieldX
                  className="mx-auto size-12 text-fake"
                  strokeWidth={1.3}
                  aria-hidden="true"
                />
                <h1 className="mt-4 text-3xl font-extrabold">
                  {status === "REJECTED" ? "Verification not approved" : "Account suspended"}
                </h1>
                <p className="mx-auto mt-3 max-w-md">
                  {profile.rejection_reason || "Please contact the AuthentiQ team for details."}
                </p>
              </>
            )}
            {error && (
              <p role="alert" className="mt-4 text-sm font-semibold text-fake">
                {error}
              </p>
            )}
            <div className="mt-6 flex flex-wrap justify-center gap-3">
              <button type="button" className={pill} onClick={check} disabled={checking}>
                {checking ? "Checking…" : "Check status again"}
              </button>
              <button type="button" className={pillGhost} onClick={logout}>
                Log out
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
