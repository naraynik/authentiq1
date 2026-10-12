import { useEffect, useRef, useState, type FormEvent } from "react";
import jsQR from "jsqr";
import {
  AlertTriangle,
  Camera,
  CheckCircle2,
  FileText,
  Keyboard,
  MapPin,
  QrCode,
  SearchX,
  ShieldAlert,
  ShieldCheck,
} from "lucide-react";
import { sampleProduct, SAMPLE_REPORTS, type Product } from "@/lib/samples";
import { raiseIssue, scanProduct } from "@/lib/api";
import { card, field, pill, pillGhost } from "@/components/Shell";

type Coords = { lat: number; lon: number } | null;
type Result = { code: string; product: Product | null; sample?: boolean; coords?: Coords };

function CameraScanner({ onCode }: { onCode: (code: string) => void }) {
  const video = useRef<HTMLVideoElement>(null);
  const [on, setOn] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    if (!on) return;
    let stream: MediaStream | undefined;
    let timer = 0;
    let stopped = false;
    const canvas = document.createElement("canvas");

    navigator.mediaDevices
      ?.getUserMedia({ video: { facingMode: "environment" } })
      .then((s) => {
        if (stopped) return s.getTracks().forEach((t) => t.stop());
        stream = s;
        const v = video.current!;
        v.srcObject = s;
        void v.play();
        timer = window.setInterval(() => {
          if (!v.videoWidth) return;
          canvas.width = v.videoWidth;
          canvas.height = v.videoHeight;
          const ctx = canvas.getContext("2d", { willReadFrequently: true })!;
          ctx.drawImage(v, 0, 0);
          const found = jsQR(
            ctx.getImageData(0, 0, canvas.width, canvas.height).data,
            canvas.width,
            canvas.height,
          );
          if (found?.data) {
            setOn(false);
            onCode(found.data);
          }
        }, 250);
      })
      .catch(() => {
        setError("Could not open the camera. Allow camera access, or type the code instead.");
        setOn(false);
      });
    if (!navigator.mediaDevices) {
      setError("This browser cannot open the camera here. Type the code instead.");
      setOn(false);
    }

    return () => {
      stopped = true;
      clearInterval(timer);
      stream?.getTracks().forEach((t) => t.stop());
    };
  }, [on, onCode]);

  return (
    <div>
      <div className="relative aspect-[4/3] overflow-hidden rounded-2xl bg-ink">
        {on ? (
          <>
            <video ref={video} className="size-full object-cover" muted playsInline />
            <div className="scan-frame pointer-events-none absolute inset-[18%] rounded-2xl border-2 border-white/90" />
          </>
        ) : (
          <div className="flex size-full flex-col items-center justify-center gap-4 text-white">
            <Camera className="size-12" strokeWidth={1.2} aria-hidden="true" />
            <button
              type="button"
              className={pill}
              onClick={() => {
                setError("");
                setOn(true);
              }}
            >
              Open camera
            </button>
          </div>
        )}
      </div>
      {on && (
        <button
          type="button"
          className="mt-3 text-sm text-subtle underline"
          onClick={() => setOn(false)}
        >
          Stop camera
        </button>
      )}
      {error && (
        <p role="alert" className="mt-3 text-sm text-fake">
          {error}
        </p>
      )}
    </div>
  );
}

function Report({ result, onReset }: { result: Result; onReset: () => void }) {
  const { product, code } = result;
  const [issueOpen, setIssueOpen] = useState(false);
  const [issueText, setIssueText] = useState("");
  const [sent, setSent] = useState(false);
  const [sending, setSending] = useState(false);
  const [issueError, setIssueError] = useState("");

  if (!product)
    return (
      <div className={`${card} text-center`}>
        <SearchX className="mx-auto size-12 text-fake" strokeWidth={1.3} aria-hidden="true" />
        <h2 className="mt-4 text-2xl font-bold">No record found</h2>
        <p className="mx-auto mt-2 max-w-md">
          The code <span className="font-mono font-semibold">{code}</span> is not stored on the
          AuthentiQ blockchain. The manufacturer may not have registered this product, or the code
          may be fake.
        </p>
        <button type="button" className={`${pill} mt-6`} onClick={onReset}>
          Scan another product
        </button>
      </div>
    );

  const bad = product.anomalies.length > 0;
  const submit = async (e: FormEvent) => {
    e.preventDefault();
    if (result.sample) return setSent(true); // sample reports are not sent anywhere
    setSending(true);
    setIssueError("");
    try {
      await raiseIssue(product.code, issueText, result.coords ?? null);
      setSent(true);
    } catch (err) {
      setIssueError(err instanceof Error ? err.message : "Could not send the issue.");
    } finally {
      setSending(false);
    }
  };

  return (
    <div className="grid gap-6">
      <div
        aria-live="polite"
        className={`rounded-3xl p-6 sm:p-8 ${bad ? "bg-fake-soft" : "bg-genuine-soft"}`}
      >
        <div className="flex items-start gap-4">
          {bad ? (
            <AlertTriangle
              className="size-10 flex-none text-fake"
              strokeWidth={1.6}
              aria-hidden="true"
            />
          ) : (
            <CheckCircle2
              className="size-10 flex-none text-genuine"
              strokeWidth={1.6}
              aria-hidden="true"
            />
          )}
          <div>
            <p
              className={`font-mono text-xs tracking-widest ${bad ? "text-fake" : "text-genuine"}`}
            >
              AI MODEL
            </p>
            <h2 className="text-2xl font-bold">{bad ? "Anomaly raised" : "No anomaly found"}</h2>
            {bad ? (
              <ul className="mt-2 list-disc space-y-1 pl-5">
                {product.anomalies.map((a) => (
                  <li key={a}>{a}</li>
                ))}
              </ul>
            ) : (
              <p className="mt-1">The blockchain record and the scan history agree.</p>
            )}
          </div>
        </div>
      </div>

      <div className={card}>
        <p className="font-mono text-xs tracking-widest text-subtle">
          {result.sample ? "SAMPLE SCAN REPORT" : "SCAN REPORT"}
        </p>
        <h2 className="mt-1 text-2xl font-bold">{product.name}</h2>
        <dl className="mt-6 grid gap-px overflow-hidden rounded-2xl border border-line bg-line sm:grid-cols-2">
          {[
            ["Product code", product.code],
            ["Batch", product.batch],
            ["Manufacturer", product.manufacturer],
            ...product.distributors.map(
              (d, i) =>
                [
                  product.distributors.length > 1
                    ? `Registered distributor ${i + 1}`
                    : "Registered distributor",
                  [d.name, d.address].filter(Boolean).join(", "),
                ] as const,
            ),
            [
              "Blockchain record",
              product.block != null
                ? `Block ${product.block}`
                : product.onChain === false
                  ? "Not on the blockchain yet"
                  : "On the blockchain",
            ],
            [
              "Transaction",
              product.txHash
                ? `${product.txHash.slice(0, 14)}…${product.txHash.slice(-6)}`
                : "None",
            ],
          ].map(([k, v]) => (
            <div key={k} className="bg-surface p-4">
              <dt className="text-xs text-subtle">{k}</dt>
              <dd className="mt-1 font-semibold break-words">{v}</dd>
            </div>
          ))}
        </dl>

        {product.explorerUrl && (
          <a
            href={product.explorerUrl}
            target="_blank"
            rel="noreferrer"
            className="mt-4 inline-flex items-center gap-2 text-sm font-semibold text-brand underline"
          >
            See this record on the public blockchain (Etherscan) ↗
          </a>
        )}

        <h3 className="mt-8 text-lg font-bold">Where this code has been scanned</h3>
        <ol className="mt-3 divide-y divide-line border-y border-line">
          {product.scans.map((s, i) => (
            <li key={i} className="flex items-center justify-between gap-4 py-3">
              <span className="flex items-center gap-2.5">
                <MapPin
                  className={`size-4 ${s.flagged ? "text-fake" : "text-brand"}`}
                  aria-hidden="true"
                />
                <span className={s.flagged ? "font-semibold text-fake" : ""}>{s.place}</span>
                {!result.sample && i === product.scans.length - 1 && (
                  <span className="rounded-full bg-brand-soft px-2 py-0.5 text-xs font-semibold text-brand">
                    This scan
                  </span>
                )}
              </span>
              <span className="font-mono text-sm text-subtle">{s.time}</span>
            </li>
          ))}
        </ol>
      </div>

      <div className={card}>
        <h3 className="text-lg font-bold">Does something look wrong?</h3>
        <p className="mt-1">
          If you bought this from a different distributor, or the scan history does not look right,
          tell us.
        </p>
        {sent ? (
          <p
            role="status"
            className="mt-4 rounded-xl bg-genuine-soft p-4 font-semibold text-genuine"
          >
            Thank you. Your issue has been recorded.
          </p>
        ) : issueOpen ? (
          <form onSubmit={submit} className="mt-4 grid gap-3">
            <label className="grid gap-1.5 text-sm font-semibold">
              What is wrong?
              <textarea
                required
                rows={3}
                value={issueText}
                onChange={(e) => setIssueText(e.target.value)}
                className={field}
                placeholder="For example: I bought this in Delhi, not from the distributor shown."
              />
            </label>
            {issueError && (
              <p role="alert" className="text-sm font-semibold text-fake">
                {issueError}
              </p>
            )}
            <div className="flex flex-wrap gap-3">
              <button type="submit" className={pill} disabled={sending}>
                {sending ? "Sending…" : "Send issue"}
              </button>
              <button type="button" className={pillGhost} onClick={() => setIssueOpen(false)}>
                Cancel
              </button>
            </div>
          </form>
        ) : (
          <div className="mt-4 flex flex-wrap gap-3">
            <button type="button" className={pill} onClick={() => setIssueOpen(true)}>
              Raise an issue
            </button>
            <button type="button" className={pillGhost} onClick={onReset}>
              Scan another product
            </button>
          </div>
        )}
      </div>
    </div>
  );
}

type Mode = "qr" | "id" | "sample";

const OPTIONS = [
  ["qr", QrCode, "Scan QR code", "Use your camera on the code printed on the product."],
  ["id", Keyboard, "Enter product ID", "Type the ID printed next to the QR code."],
] as const;

export default function ScanPage() {
  const [mode, setMode] = useState<Mode>("qr");
  const [code, setCode] = useState("");
  const [result, setResult] = useState<Result | null>(null);
  const [coords, setCoords] = useState<Coords>(null);
  const [locError, setLocError] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const place = coords
    ? `${coords.lat.toFixed(3)}, ${coords.lon.toFixed(3)}`
    : "Location not shared";

  const shareLocation = () => {
    if (!navigator.geolocation) return setLocError("This browser cannot share location here.");
    navigator.geolocation.getCurrentPosition(
      (p) => {
        setCoords({ lat: p.coords.latitude, lon: p.coords.longitude });
        setLocError("");
      },
      () => {
        setCoords(null);
        setLocError("Location was not shared. The report still works, with fewer checks.");
      },
    );
  };

  const show = (r: Result) => {
    setResult(r);
    window.scrollTo({ top: 0 });
  };
  const run = async (c: string) => {
    const clean = c.trim();
    if (!clean || busy) return;
    setBusy(true);
    setError("");
    try {
      show({ code: clean, product: await scanProduct(clean, coords), coords });
    } catch (err) {
      setError(err instanceof Error ? err.message : "Something went wrong. Try again.");
    } finally {
      setBusy(false);
    }
  };
  const sample = (c: string) => show({ code: c, product: sampleProduct(c), sample: true });

  if (result)
    return (
      <div className="mx-auto max-w-[860px] px-5 pt-32 pb-24">
        <Report
          key={result.code + result.product?.scans.length}
          result={result}
          onReset={() => setResult(null)}
        />
      </div>
    );

  return (
    <div className="mx-auto max-w-[860px] px-5 pt-32 pb-24">
      <div className="text-center">
        <h1 className="text-4xl font-extrabold sm:text-5xl">Scan a product</h1>
        <p className="mx-auto mt-4 max-w-lg text-lg">Choose how you want to check your product.</p>
      </div>

      <div role="tablist" aria-label="How to check" className="mt-10 grid gap-4 sm:grid-cols-2">
        {OPTIONS.map(([id, Icon, title, text]) => (
          <button
            key={id}
            type="button"
            role="tab"
            aria-selected={mode === id}
            onClick={() => setMode(id)}
            className={`flex items-center gap-4 rounded-3xl border-2 p-5 text-left transition-colors ${
              mode === id
                ? "border-brand bg-brand-soft"
                : "border-line bg-surface hover:border-brand/50"
            }`}
          >
            <span
              className={`flex size-14 flex-none items-center justify-center rounded-2xl ${
                mode === id ? "bg-brand text-white" : "bg-brand-soft text-brand"
              }`}
            >
              <Icon className="size-7" strokeWidth={1.6} aria-hidden="true" />
            </span>
            <span>
              <span className="block text-lg font-bold">{title}</span>
              <span className="text-sm text-subtle">{text}</span>
            </span>
          </button>
        ))}
      </div>

      {mode !== "sample" && (
        <div className={`${card} mt-5`}>
          {mode === "qr" ? (
            <div className="mx-auto max-w-[460px]">
              <CameraScanner onCode={(c) => void run(c)} />
            </div>
          ) : (
            <form
              onSubmit={(e) => {
                e.preventDefault();
                void run(code);
              }}
              className="mx-auto grid max-w-[460px] gap-3"
            >
              <label className="grid gap-1.5 text-sm font-semibold">
                Product ID
                <input
                  value={code}
                  onChange={(e) => setCode(e.target.value)}
                  className={field}
                  placeholder="The ID printed next to the QR code"
                  autoComplete="off"
                  required
                />
              </label>
              <button type="submit" className={pill} disabled={busy}>
                {busy ? "Checking…" : "See scan report"}
              </button>
            </form>
          )}

          {busy && mode === "qr" && (
            <p role="status" className="mt-4 text-center text-sm font-semibold text-brand">
              Checking this code…
            </p>
          )}
          {error && (
            <p
              role="alert"
              className="mx-auto mt-4 max-w-[460px] rounded-xl bg-fake-soft p-4 text-sm font-semibold text-fake"
            >
              {error}
            </p>
          )}
          <div className="mx-auto mt-6 flex max-w-[460px] items-center justify-between gap-3 rounded-xl bg-brand-soft px-4 py-3 text-sm">
            <span className="flex items-center gap-2">
              <MapPin className="size-4 text-brand" aria-hidden="true" />
              {place}
            </span>
            <button
              type="button"
              className="font-semibold text-brand underline"
              onClick={shareLocation}
            >
              Share my location
            </button>
          </div>
          {locError && (
            <p className="mx-auto mt-2 max-w-[460px] text-center text-xs text-subtle">{locError}</p>
          )}
        </div>
      )}

      <div className={`${card} mt-5`}>
        <div className="flex flex-wrap items-center justify-between gap-4">
          <div className="flex items-center gap-4">
            <span className="flex size-14 flex-none items-center justify-center rounded-2xl bg-brand-soft text-brand">
              <FileText className="size-7" strokeWidth={1.6} aria-hidden="true" />
            </span>
            <div>
              <h2 className="text-lg font-bold">View a sample report</h2>
              <p className="text-sm text-subtle">
                No product at hand? See what a scan report looks like.
              </p>
            </div>
          </div>
          {mode !== "sample" && (
            <button type="button" className={pillGhost} onClick={() => setMode("sample")}>
              View a sample report
            </button>
          )}
        </div>

        {mode === "sample" && (
          <div className="mt-6 grid gap-4 sm:grid-cols-2">
            <button
              type="button"
              onClick={() => sample(SAMPLE_REPORTS.genuine)}
              className="rounded-2xl border-2 border-genuine/40 bg-genuine-soft p-5 text-left transition-colors hover:border-genuine"
            >
              <ShieldCheck className="size-9 text-genuine" strokeWidth={1.6} aria-hidden="true" />
              <span className="mt-3 block text-lg font-bold">True product</span>
              <span className="text-sm">A genuine product. No anomaly found.</span>
            </button>
            <button
              type="button"
              onClick={() => sample(SAMPLE_REPORTS.fake)}
              className="rounded-2xl border-2 border-fake/40 bg-fake-soft p-5 text-left transition-colors hover:border-fake"
            >
              <ShieldAlert className="size-9 text-fake" strokeWidth={1.6} aria-hidden="true" />
              <span className="mt-3 block text-lg font-bold">False product</span>
              <span className="text-sm">A copied code. The AI raises an anomaly.</span>
            </button>
          </div>
        )}
      </div>
    </div>
  );
}
