import { createFileRoute } from "@tanstack/react-router";
import {
  useEffect,
  useRef,
  useState,
  type CSSProperties,
  type MouseEvent,
  type ReactNode,
} from "react";
import ScanPage from "@/components/ScanPage";
import ManufacturerPage from "@/components/ManufacturerPage";
import { Logo, QMark, Shell } from "@/components/Shell";
import {
  Blocks,
  Check,
  BrainCircuit,
  Factory,
  History,
  Mail,
  MapPin,
  Menu,
  QrCode,
  ScanLine,
  ShieldCheck,
  Smartphone,
  X,
} from "lucide-react";
import GlobeDemo from "@/components/GlobeDemo";

// All media ships with the site (frontend/public/media), so nothing depends on
// third-party hotlinks. Relative paths work on the dev server, behind nginx and
// for the single-file build opened next to its media/ folder.
const media = (file: string) => `media/${file}`;
const HERO_VIDEO = media("hero");
const PACK_VIDEO = media("packing");
const SCAN_VIDEO = media("scanning");
const poster = (video: string) => `${video}-poster.jpg`;

/** WebM first (plays everywhere it is supported), MP4/H.264 as the fallback. */
function VideoSources({ video, start = "" }: { video: string; start?: string }) {
  return (
    <>
      <source src={`${video}.webm${start}`} type="video/webm" />
      <source src={`${video}.mp4${start}`} type="video/mp4" />
    </>
  );
}

const NAV = [
  ["Why AuthentiQ", "#why"],
  ["How it works", "#how"],
  ["Live demo", "#demo"],
  ["FAQ", "#faq"],
  ["Contact", "#contact"],
];

const BENEFITS = [
  [Blocks, "Every product recorded on the blockchain. Nobody can edit it later."],
  [BrainCircuit, "Our AI raises an anomaly when a scan does not add up."],
  [Smartphone, "Works in any phone browser. No app to install."],
  [MapPin, "Flags one code scanned in different places at the same time."],
] as const;

const USES = [
  [
    "Stop cloned codes",
    "When one code is scanned in different places at the same time, our AI raises an anomaly.",
    media("cloned-codes.jpg"),
  ],
  [
    "Check the distributor",
    "The manufacturer records which distributor a product goes to. A mismatch raises an anomaly.",
    media("distributor.jpg"),
  ],
  [
    "A record nobody can alter",
    "Each product's hash lives in a smart contract, so results can always be checked against it.",
    media("record.jpg"),
  ],
  [
    "A scan report for every customer",
    "Each scan shows where and when the product was scanned before. Customers can raise an issue from it.",
    media("scan-report.jpg"),
  ],
] as const;

const STEPS = [
  [
    "Register",
    "The manufacturer stores the product on our blockchain, with the distributor it is sent to.",
  ],
  ["Scan", "The customer scans the QR code on the pack with a phone camera."],
  [
    "Scan report",
    "They see the product's record: where and when it was scanned, and its distributor.",
  ],
  [
    "Anomaly",
    "Our AI raises an anomaly if scans or the distributor do not match. The customer can raise an issue.",
  ],
] as const;

const HIGHLIGHTS = [
  [Blocks, "Stored safely", "Every product is recorded and cannot be changed later."],
  [ShieldCheck, "Checked manufacturers", "We verify every manufacturer before they add products."],
  [BrainCircuit, "Smart checks", "Our AI spots scans that do not add up."],
  [History, "Clear scan report", "See where and when your product was scanned."],
  [MapPin, "Copy alerts", "One code in two places at once gets flagged."],
  [Smartphone, "Raise an issue", "Tell us when something looks wrong."],
] as const;

const FAQ = [
  [
    "Does AuthentiQ create the QR codes?",
    "No. Manufacturers store their products on our blockchain. The QR code on the pack leads to that product's record and its scan report.",
  ],
  [
    "What does a customer see after scanning?",
    "A scan report: the product's blockchain record, the distributor the manufacturer entered, and where and when the code has been scanned before.",
  ],
  [
    "What counts as an anomaly?",
    "Two things. The same code scanned in different locations at the same time, which no single product can do. Or a distributor address that does not match the one the manufacturer entered.",
  ],
  [
    "Who raises the anomaly?",
    "Our AI model raises it automatically from the scan data. A customer who sees something wrong in the scan report can also raise an issue.",
  ],
  [
    "What does the blockchain add?",
    "Each product is stored in a smart contract. Nobody can quietly edit or delete it, so the scan report is always checked against a record that cannot be changed after the fact.",
  ],
  [
    "Does an anomaly change the blockchain record?",
    "No. The product's on-chain record stays exactly as it was. The anomaly is kept alongside the scan history.",
  ],
  [
    "Do customers need an app?",
    "No. Scanning runs in the phone's browser using the camera and location permission.",
  ],
  [
    "How does a manufacturer get started?",
    "Register with your GST ID and upload your Aadhaar card. Our team verifies you by hand. After that you can enter product details and distributor addresses, which are stored on our blockchain.",
  ],
];

const BRANCH = ["#0b1b3a", "#9a7209", "#b8860b", "#1e3a6e", "#7c5c07", "#d4a017"];

const TEAM = [
  ["Monish Patil", "mkpatil371323"],
  ["Anushka Patil", "arpatil371323"],
  ["Narayni Khaparde", "npkhaparde370223"],
  ["Pranjal Wagh", "ppwagh371324"],
] as const;

const COMPARE = [
  [
    "A copied QR code looks just like the real one.",
    "Every scan is checked against the product's record.",
  ],
  [
    "You cannot tell where else a code was scanned.",
    "The scan report shows where and when it was scanned.",
  ],
  [
    "You do not know which distributor it should come from.",
    "The registered distributor is shown on the report.",
  ],
  [
    "If something looks wrong, there is nowhere to say so.",
    "You can raise an issue straight from the report.",
  ],
] as const;

const pill =
  "inline-flex items-center justify-center rounded-full bg-gradient-to-r from-[#0b1b3a] to-[#1e3a6e] px-7 py-3 text-[15px] font-semibold text-white aq-btn";
const h2 = "text-3xl leading-tight font-bold sm:text-[2.75rem]";

function StepVisual({ step }: { step: number }) {
  if (step === 0 || step === 1)
    return (
      <video
        key={step}
        className="size-full object-cover"
        poster={poster(step === 0 ? PACK_VIDEO : SCAN_VIDEO)}
        muted
        loop
        playsInline
        preload="metadata"
        aria-hidden="true"
      >
        <VideoSources video={step === 0 ? PACK_VIDEO : SCAN_VIDEO} start="#t=0.5" />
      </video>
    );
  const row =
    "flex items-center justify-between gap-2 rounded-lg bg-surface px-3 py-1.5 text-xs shadow-sm";
  if (step === 2)
    return (
      <div className="flex size-full flex-col justify-center gap-1.5 bg-brand-soft p-4">
        <p className="font-mono text-[10px] tracking-widest text-subtle">SCAN REPORT</p>
        <p className={row}>
          <span className="text-subtle">Blockchain record</span>
          <span className="font-semibold text-genuine">Found</span>
        </p>
        <p className={row}>
          <span className="text-subtle">Distributor</span>
          <span className="font-semibold">Mumbai</span>
        </p>
        <p className={row}>
          <span className="text-subtle">Scan 1 · 10:42</span>
          <span className="font-semibold">Mumbai</span>
        </p>
        <p className={row}>
          <span className="text-subtle">Scan 2 · 10:42</span>
          <span className="font-semibold text-fake">London</span>
        </p>
      </div>
    );
  return (
    <div className="flex size-full flex-col justify-center gap-2 bg-fake-soft p-4">
      <div className="rounded-xl bg-surface px-3 py-2.5 shadow-sm">
        <p className="font-mono text-[10px] tracking-widest text-fake">AI · ANOMALY RAISED</p>
        <p className="mt-0.5 text-sm font-semibold">Scanned in 2 locations at the same time</p>
      </div>
      <div className="rounded-xl bg-surface px-3 py-2.5 shadow-sm">
        <p className="text-sm font-semibold">Distributor does not match</p>
      </div>
      <span className="rounded-full bg-fake px-3 py-2 text-center text-sm font-semibold text-white">
        Raise an issue
      </span>
    </div>
  );
}

/** Card that lifts and tilts toward the pointer; any video inside plays while hovered. */
function TiltCard({ children }: { children: ReactNode }) {
  const onMove = (e: MouseEvent<HTMLDivElement>) => {
    const el = e.currentTarget;
    const r = el.getBoundingClientRect();
    const x = (e.clientX - r.left) / r.width - 0.5;
    const y = (e.clientY - r.top) / r.height - 0.5;
    el.style.setProperty("--ry", `${x * 10}deg`);
    el.style.setProperty("--rx", `${-y * 10}deg`);
  };
  const video = (el: HTMLElement) => el.querySelector("video");
  return (
    <div
      className="tilt-card h-full"
      onMouseMove={onMove}
      onMouseEnter={(e) =>
        void video(e.currentTarget)
          ?.play()
          .catch(() => undefined)
      }
      onMouseLeave={(e) => {
        e.currentTarget.style.setProperty("--ry", "0deg");
        e.currentTarget.style.setProperty("--rx", "0deg");
        video(e.currentTarget)?.pause();
      }}
    >
      {children}
    </div>
  );
}

export const Route = createFileRoute("/")({
  head: () => ({
    meta: [
      { title: "AuthentiQ | Product authentication system" },
      {
        name: "description",
        content:
          "AuthentiQ is a product authentication system. Scan the QR code on a product to see where it came from and whether anything looks wrong.",
      },
      { property: "og:title", content: "AuthentiQ | Product authentication system" },
      { property: "og:type", content: "website" },
    ],
  }),
  component: App,
});

function Landing() {
  const [menuOpen, setMenuOpen] = useState(false);
  const [hot, setHot] = useState<number | null>(null);
  const [openFaq, setOpenFaq] = useState<number | null>(0);
  const root = useRef<HTMLDivElement>(null);

  // Scroll effects, done with direct DOM updates so scrolling never re-renders the page.
  useEffect(() => {
    const el = root.current;
    if (!el) return;
    const bar = el.querySelector<HTMLElement>(".scroll-bar");
    const header = el.querySelector("header");
    const links = [...el.querySelectorAll<HTMLAnchorElement>("header nav a[href^='#']")];
    const sections = ["why", "how", "demo", "faq", "contact"]
      .map((id) => document.getElementById(id))
      .filter((x): x is HTMLElement => !!x);
    let ticking = false;
    const update = () => {
      ticking = false;
      const y = window.scrollY;
      const max = document.documentElement.scrollHeight - window.innerHeight;
      if (bar) bar.style.transform = `scaleX(${max > 0 ? Math.min(1, y / max) : 0})`;
      header?.classList.toggle("is-scrolled", y > 40);
      let current = "";
      for (const sec of sections)
        if (sec.getBoundingClientRect().top < window.innerHeight * 0.4) current = sec.id;
      for (const a of links)
        a.classList.toggle("is-active", a.getAttribute("href") === `#${current}`);
    };
    const onScroll = () => {
      if (!ticking) {
        ticking = true;
        requestAnimationFrame(update);
      }
    };
    update();
    window.addEventListener("scroll", onScroll, { passive: true });

    // Reveal elements as they enter the viewport.
    el.classList.add("reveal-on");
    const io = new IntersectionObserver(
      (entries) => {
        for (const e of entries)
          if (e.isIntersecting) {
            e.target.classList.add("in");
            io.unobserve(e.target);
          }
      },
      { rootMargin: "0px 0px -8% 0px", threshold: 0.12 },
    );
    el.querySelectorAll(".rv").forEach((n) => io.observe(n));
    return () => {
      window.removeEventListener("scroll", onScroll);
      io.disconnect();
    };
  }, []);

  return (
    <div ref={root} className="overflow-x-clip bg-surface">
      <div className="scroll-bar" aria-hidden="true" />
      <header className="site-header pointer-events-none fixed inset-x-0 top-0 z-50">
        <div className="header-row mx-auto flex h-24 max-w-[1180px] items-center justify-between px-5">
          <a
            href="#/"
            aria-label="AuthentiQ home"
            className="pointer-events-auto rounded-full bg-surface/85 px-4 py-2 backdrop-blur"
          >
            <Logo />
          </a>
          <nav
            aria-label="Main"
            className="header-nav pointer-events-auto hidden items-center gap-1 rounded-full bg-surface py-1.5 pr-1.5 pl-4 shadow-[0_5px_14px_rgba(11,27,58,0.08)] lg:flex"
          >
            {NAV.map(([label, href]) => (
              <a
                key={href}
                href={href}
                className="nav-link px-3.5 py-3 text-[15px] transition-colors hover:text-brand"
              >
                {label}
              </a>
            ))}
            <a href="#/scan" className={pill}>
              Scan a product
            </a>
          </nav>
          <button
            type="button"
            aria-label={menuOpen ? "Close menu" : "Open menu"}
            aria-expanded={menuOpen}
            onClick={() => setMenuOpen(!menuOpen)}
            className="pointer-events-auto flex size-12 items-center justify-center rounded-xl bg-surface text-brand shadow-[0_3px_8px_rgba(11,27,58,0.15)] lg:hidden"
          >
            {menuOpen ? <X /> : <Menu />}
          </button>
        </div>
        {menuOpen && (
          <nav
            aria-label="Mobile"
            className="pointer-events-auto absolute top-[84px] right-5 flex w-64 flex-col rounded-3xl bg-surface/95 px-6 py-4 shadow-[0_10px_35px_rgba(11,27,58,0.13)] backdrop-blur lg:hidden"
          >
            {[...NAV, ["Scan a product", "#/scan"]].map(([label, href]) => (
              <a
                key={href}
                href={href}
                onClick={() => setMenuOpen(false)}
                className="py-3 text-base"
              >
                {label}
              </a>
            ))}
          </nav>
        )}
      </header>

      <main>
        {/* Hero */}
        <section className="relative flex min-h-[640px] items-center bg-gradient-to-br from-brand-soft via-surface to-[#efe3bf] px-5 pt-28 pb-14 lg:h-[84vh] lg:pt-24">
          <video
            className="hero-video absolute inset-0 size-full object-cover"
            poster={poster(HERO_VIDEO)}
            autoPlay
            muted
            loop
            playsInline
            preload="metadata"
            aria-hidden="true"
          >
            <VideoSources video={HERO_VIDEO} />
          </video>
          <div className="relative mx-auto w-full max-w-[1180px]">
            <div className="hero-in mx-auto max-w-[640px] rounded-xl bg-surface/80 px-6 py-10 text-center shadow-[0_20px_60px_rgba(11,27,58,0.12)] sm:px-9 sm:py-14 lg:mx-0 hero-shift">
              <h1 className="text-4xl leading-tight font-extrabold sm:text-[2.6rem]">
                <span className="text-ink">Is your product</span>{" "}
                <span className="hl">the real thing?</span>
              </h1>
              <p className="mx-auto mt-6 max-w-[480px] text-lg leading-relaxed sm:text-xl">
                AuthentiQ is a product authentication system. Scan the QR code on a product to see
                where it came from and whether anything looks wrong.
              </p>
              <div className="mt-8 flex flex-wrap justify-center gap-3">
                <a href="#/scan" className={pill}>
                  Scan a product
                </a>
                <a
                  href="#/manufacturer"
                  className="inline-flex items-center justify-center gap-2 rounded-full border-2 border-ink bg-surface px-7 py-3 text-[15px] font-semibold text-ink transition-colors hover:bg-lime"
                >
                  <Factory className="size-[18px]" aria-hidden="true" />
                  Register as manufacturer
                </a>
              </div>
              <div className="marquee mt-10 overflow-hidden" aria-hidden="true">
                <div className="marquee-track flex w-max gap-10 text-[15px] font-semibold text-ink/70">
                  {[0, 1].map((k) =>
                    [
                      "Stored on blockchain",
                      "AI checks",
                      "No app needed",
                      "Clear scan report",
                      "Verified manufacturers",
                      "Raise an issue",
                    ].map((t) => (
                      <span key={`${k}${t}`} className="flex items-center gap-2 whitespace-nowrap">
                        <span className="size-1.5 rounded-full bg-brand" />
                        {t}
                      </span>
                    )),
                  )}
                </div>
              </div>
            </div>
          </div>
        </section>

        {/* Benefit strip */}
        <div className="bg-brand-soft px-4 py-4">
          <ul className="mx-auto grid max-w-[1280px] grid-cols-1 gap-2 sm:grid-cols-2 lg:grid-cols-4">
            {BENEFITS.map(([Icon, text]) => (
              <li
                key={text}
                className="lift rv group flex min-h-[110px] items-center gap-4 rounded-2xl bg-surface px-6 py-4"
                style={
                  { "--d": `${BENEFITS.findIndex((b) => b[1] === text) * 90}ms` } as CSSProperties
                }
              >
                <Icon
                  className="size-11 flex-none text-[#b8860b] transition-transform duration-300 group-hover:scale-110 group-hover:-rotate-6"
                  strokeWidth={1.2}
                  aria-hidden="true"
                />
                <p className="text-[15px] leading-snug text-ink">{text}</p>
              </li>
            ))}
          </ul>
        </div>

        {/* Why */}
        <section
          id="why"
          className="mx-auto grid max-w-[1180px] gap-10 px-5 py-20 lg:grid-cols-2 lg:gap-14 lg:py-28"
        >
          <div className="rv self-start lg:sticky lg:top-32">
            <h2 className={`${h2} max-w-[500px]`}>A code that scans is not proof on its own</h2>
            <p className="mt-5 max-w-[430px] text-lg">
              A copied QR code still scans. The scan report shows what the code alone cannot: where
              else it has been scanned, and which distributor it should have come from.
            </p>
            <a href="#demo" className={`${pill} mt-7`}>
              See an anomaly raised
            </a>
          </div>
          <div className="grid gap-5">
            {USES.map(([title, text, src]) => (
              <article
                key={title}
                className="use-card rv group flex min-h-[170px] items-center justify-between gap-5 rounded-3xl border border-[#0b1b3a] bg-[#fffdf7] py-4 pr-4 pl-7 shadow-[2px_5px_0_#f0dfa8]"
              >
                <div>
                  <h3 className="text-xl font-bold">{title}</h3>
                  <p className="mt-2.5 max-w-[270px] text-[15px]">{text}</p>
                </div>
                <img
                  src={src}
                  alt=""
                  loading="lazy"
                  className="h-32 w-36 flex-none rounded-2xl object-cover transition-transform duration-500 group-hover:scale-[1.05] sm:h-36 sm:w-48"
                />
              </article>
            ))}
          </div>
        </section>

        {/* Process */}
        <section id="how" className="mx-auto max-w-[1180px] px-5 py-20 text-center lg:py-24">
          <h2 className={`${h2} rv`}>Simple to use, hard to fool</h2>
          <p className="mt-4">
            Four steps from the factory to the customer. Hover a card to look closer.
          </p>
          <ol className="steps mt-14 grid gap-6 text-left sm:grid-cols-2 lg:grid-cols-4">
            {STEPS.map(([title, text], i) => (
              <li key={title} className="rv" style={{ "--d": `${i * 110}ms` } as CSSProperties}>
                <TiltCard>
                  <article className="tilt-inner flex h-full flex-col overflow-hidden rounded-3xl border border-line bg-surface">
                    <div className="relative aspect-[4/3] overflow-hidden">
                      <StepVisual step={i} />
                    </div>
                    <div className="flex-1 px-6 py-6">
                      <p className="text-3xl font-light text-[#a9b1c2]">0{i + 1}</p>
                      <h3 className="mt-1 text-xl font-bold text-[#9a7209]">{title}</h3>
                      <p className="mt-2 text-[15px]">{text}</p>
                    </div>
                  </article>
                </TiltCard>
              </li>
            ))}
          </ol>
        </section>

        {/* Demo */}
        <section id="demo" className="bg-paper">
          <div className="mx-auto max-w-[1180px] px-5 py-20 lg:py-24">
            <div className="text-center">
              <h2 className={`${h2} rv`}>Same code, two cities, same time</h2>
              <p className="mt-4">
                Switch between a normal journey and a copied code to see when the AI raises an
                anomaly.
              </p>
            </div>
            <div className="rv mt-12">
              <GlobeDemo />
            </div>
          </div>
        </section>

        {/* Highlights mind map */}
        <section className="mx-auto max-w-[1180px] px-5 py-20 text-center lg:py-28">
          <h2 className={`${h2} rv`}>Key highlights</h2>
          <p className="mt-4">Everything AuthentiQ does for you, at a glance.</p>

          <div className="relative mx-auto mt-14 max-w-[1040px]">
            {/* branches (desktop) */}
            <svg
              className="absolute inset-0 hidden size-full lg:block"
              viewBox="0 0 1000 420"
              preserveAspectRatio="none"
              aria-hidden="true"
            >
              {[50, 210, 370].flatMap((y, i) => [
                <path
                  key={`l${y}`}
                  d={`M500 210 C 420 210, 420 ${y}, 340 ${y}`}
                  fill="none"
                  stroke={BRANCH[i]}
                  strokeLinecap="round"
                  vectorEffect="non-scaling-stroke"
                  className="branch"
                  style={{
                    strokeWidth: hot === i ? 6 : 3,
                    opacity: hot === null || hot === i ? 1 : 0.25,
                  }}
                />,
                <path
                  key={`r${y}`}
                  d={`M500 210 C 580 210, 580 ${y}, 660 ${y}`}
                  fill="none"
                  stroke={BRANCH[i + 3]}
                  strokeLinecap="round"
                  vectorEffect="non-scaling-stroke"
                  className="branch"
                  style={{
                    strokeWidth: hot === i + 3 ? 6 : 3,
                    opacity: hot === null || hot === i + 3 ? 1 : 0.25,
                  }}
                />,
              ])}
            </svg>

            <div className="relative grid gap-4 lg:h-[420px] lg:grid-cols-[34%_32%_34%] lg:gap-0">
              <div className="order-1 flex items-center justify-center lg:order-2">
                <div className="hub rv relative flex flex-col items-center gap-2 rounded-full bg-gradient-to-br from-[#0b1b3a] to-[#1e3a6e] px-10 py-7 text-white shadow-[0_14px_40px_rgba(11,27,58,0.3)]">
                  <QMark size={44} ink="#ffffff" gap="var(--color-ink)" />
                  <span className="text-lg font-extrabold">AuthentiQ</span>
                </div>
              </div>
              {[0, 3].map((start) => (
                <ul
                  key={start}
                  className={`flex flex-col gap-4 lg:justify-between lg:gap-0 ${start === 0 ? "order-2 lg:order-1" : "order-3"}`}
                >
                  {HIGHLIGHTS.slice(start, start + 3).map(([Icon, title, text], i) => (
                    <li
                      key={title}
                      onMouseEnter={() => setHot(start + i)}
                      onMouseLeave={() => setHot(null)}
                      className="node rv flex cursor-default items-center gap-4 rounded-full border-2 bg-surface px-5 py-3 text-left lg:h-[100px]"
                      style={
                        {
                          borderColor: BRANCH[start + i],
                          "--d": `${150 + i * 120}ms`,
                          "--c": BRANCH[start + i],
                        } as CSSProperties
                      }
                    >
                      <span
                        className="flex size-12 flex-none items-center justify-center rounded-full text-white"
                        style={{ background: BRANCH[start + i] }}
                      >
                        <Icon className="size-6" strokeWidth={1.6} aria-hidden="true" />
                      </span>
                      <span>
                        <span className="block font-bold">{title}</span>
                        <span className="text-sm">{text}</span>
                      </span>
                    </li>
                  ))}
                </ul>
              ))}
            </div>
          </div>
        </section>

        {/* With / without */}
        <section className="bg-paper px-5 py-20 lg:py-24">
          <div className="mx-auto max-w-[1040px]">
            <div className="text-center">
              <h2 className={`${h2} rv`}>What changes with AuthentiQ</h2>
              <p className="mt-4">The same product, checked two ways.</p>
            </div>
            <div className="mt-12 grid gap-6 md:grid-cols-2">
              <div className="rv rounded-3xl border border-line bg-surface p-7 sm:p-9">
                <h3 className="text-xl font-bold text-subtle">Without AuthentiQ</h3>
                <ul className="mt-6 space-y-5">
                  {COMPARE.map(([without]) => (
                    <li key={without} className="row-nudge flex gap-3">
                      <span className="mt-0.5 flex size-6 flex-none items-center justify-center rounded-full bg-fake-soft text-fake">
                        <X className="size-4" strokeWidth={2.5} aria-hidden="true" />
                      </span>
                      <span className="text-subtle">{without}</span>
                    </li>
                  ))}
                </ul>
              </div>
              <div
                className="lift rv rounded-3xl border-2 border-brand bg-surface p-7 shadow-[0_18px_44px_rgba(11,27,58,0.14)] sm:p-9"
                style={{ "--d": "140ms" } as CSSProperties}
              >
                <h3 className="text-xl font-bold text-brand">With AuthentiQ</h3>
                <ul className="mt-6 space-y-5">
                  {COMPARE.map(([, withIt]) => (
                    <li key={withIt} className="row-nudge flex gap-3">
                      <span className="mt-0.5 flex size-6 flex-none items-center justify-center rounded-full bg-genuine-soft text-genuine">
                        <Check className="size-4" strokeWidth={2.5} aria-hidden="true" />
                      </span>
                      <span>{withIt}</span>
                    </li>
                  ))}
                </ul>
              </div>
            </div>
          </div>
        </section>

        {/* Next steps */}
        <section className="mx-auto max-w-[1180px] px-5 py-20 text-center lg:py-24">
          <h2 className={`${h2} rv`}>Immediate next steps</h2>
          <div className="mx-auto mt-14 grid max-w-[920px] gap-8 md:grid-cols-2">
            {(
              [
                [
                  media("check-product.jpg"),
                  "Check a product",
                  "Have a product in your hand? Scan its QR code and see its scan report in your browser.",
                  "Scan a product",
                  "#/scan",
                ],
                [
                  media("protect-products.jpg"),
                  "Protect your products",
                  "Register with your GST ID and Aadhaar, get verified, then add your products and distributor addresses to the blockchain.",
                  "Register as a manufacturer",
                  "#/manufacturer",
                ],
              ] as const
            ).map(([src, title, text, cta, href]) => (
              <article
                key={title}
                className="lift rv group overflow-hidden rounded-2xl bg-secondary"
              >
                <div className="h-44 overflow-hidden">
                  <img
                    src={src}
                    alt=""
                    loading="lazy"
                    className="size-full object-cover transition-transform duration-700 group-hover:scale-110"
                  />
                </div>
                <div className="px-8 py-8">
                  <h3 className="text-2xl font-bold">{title}</h3>
                  <p className="mx-auto mt-3 min-h-[72px] max-w-[330px]">{text}</p>
                  <a href={href} className={`${pill} mt-4`}>
                    {cta}
                  </a>
                </div>
              </article>
            ))}
          </div>
        </section>

        {/* FAQ */}
        <section id="faq" className="mx-auto max-w-[900px] px-5 py-20 lg:py-24">
          <div className="text-center">
            <h2 className={`${h2} rv`}>Answers to your top questions</h2>
            <p className="mt-4">What customers see, and when an anomaly is raised.</p>
          </div>
          <div className="rv mt-12 divide-y divide-line border-y border-line">
            {FAQ.map(([q, a], i) => {
              const isOpen = openFaq === i;
              return (
                <div key={q} className="faq-item">
                  <button
                    type="button"
                    aria-expanded={isOpen}
                    onClick={() => setOpenFaq(isOpen ? null : i)}
                    className="flex w-full items-start justify-between gap-6 py-6 text-left text-lg font-bold transition-colors hover:text-brand"
                  >
                    {q}
                    <span
                      aria-hidden="true"
                      className={`flex size-8 flex-none items-center justify-center rounded-full text-2xl leading-none font-normal transition-all duration-300 ${
                        isOpen ? "rotate-45 bg-brand text-white" : "bg-brand-soft text-brand"
                      }`}
                    >
                      +
                    </span>
                  </button>
                  <div className={`faq-body ${isOpen ? "open" : ""}`}>
                    <div>
                      <p className="max-w-[780px] pb-6 leading-relaxed">{a}</p>
                    </div>
                  </div>
                </div>
              );
            })}
          </div>
        </section>
      </main>

      <footer id="contact" className="bg-ink text-white">
        <div className="mx-auto max-w-[1180px] px-5 pt-16 pb-9">
          <div className="grid gap-12 lg:grid-cols-[1fr_1.6fr]">
            <div>
              <Logo dark />
              <p className="mt-4 max-w-xs text-white/60">
                A product authentication system. Scan a product to see where it came from.
              </p>
              <nav aria-label="Footer" className="mt-6 grid gap-2 text-[15px]">
                {NAV.map(([label, href]) => (
                  <a key={href} href={href} className="w-fit hover:text-lime">
                    {label}
                  </a>
                ))}
                <a href="#/scan" className="w-fit hover:text-lime">
                  Scan a product
                </a>
              </nav>
            </div>

            <div>
              <h2 className="text-2xl font-bold">Contact us</h2>
              <p className="mt-2 text-white/60">Questions or feedback? Write to any of us.</p>
              <ul className="mt-6 grid gap-4 sm:grid-cols-2">
                {TEAM.map(([name, id]) => (
                  <li key={id}>
                    <a
                      href={`mailto:${id}@kkwagh.edu.in`}
                      className="lift group flex items-center gap-4 rounded-2xl bg-white/10 px-5 py-4 hover:bg-white/15"
                    >
                      <span className="flex size-11 flex-none items-center justify-center rounded-full bg-lime text-ink">
                        <Mail className="size-5" strokeWidth={1.8} aria-hidden="true" />
                      </span>
                      <span className="min-w-0">
                        <span className="block font-bold">{name}</span>
                        <span className="block text-sm break-all text-white/60 group-hover:text-lime">
                          {id}@kkwagh.edu.in
                        </span>
                      </span>
                    </a>
                  </li>
                ))}
              </ul>
            </div>
          </div>
          <p className="mt-12 border-t border-white/15 pt-6 text-sm text-white/60">
            © AuthentiQ. Photos and video from Pexels and Unsplash.
          </p>
        </div>
      </footer>
    </div>
  );
}

/** Hash routing, so the whole site also works as a single file opened from disk. */
function App() {
  const [hash, setHash] = useState("");
  useEffect(() => {
    const read = () => setHash(window.location.hash);
    read();
    // Handle in-page links ourselves so navigation also works where the browser
    // blocks or ignores hash changes (embedded previews, sandboxed frames).
    const onClick = (e: globalThis.MouseEvent) => {
      const a = (e.target as Element | null)?.closest?.("a[href^='#']");
      if (!a) return;
      e.preventDefault();
      const next = a.getAttribute("href") ?? "";
      setHash(next);
      try {
        window.history.pushState(null, "", next);
      } catch {
        /* address bar cannot be updated here; the page still switches */
      }
    };
    document.addEventListener("click", onClick);
    window.addEventListener("hashchange", read);
    window.addEventListener("popstate", read);
    return () => {
      document.removeEventListener("click", onClick);
      window.removeEventListener("hashchange", read);
      window.removeEventListener("popstate", read);
    };
  }, []);
  const page = hash.startsWith("#/scan")
    ? "scan"
    : hash.startsWith("#/manufacturer")
      ? "manufacturer"
      : "home";
  useEffect(() => {
    if (page !== "home" || hash.length < 3 || hash.startsWith("#/")) {
      // Do not return this call: newer Chrome makes scrollTo return a Promise,
      // and React would then try to call that as the effect's clean-up.
      window.scrollTo({ top: 0 });
      return;
    }
    const t = setTimeout(() => document.getElementById(hash.slice(1))?.scrollIntoView(), 50);
    return () => clearTimeout(t);
  }, [page, hash]);

  // The landing page stays mounted (just hidden) while another page is open,
  // so switching pages never tears down its video and 3D scene.
  return (
    <>
      <div hidden={page !== "home"}>
        <Landing />
      </div>
      {page === "scan" && (
        <Shell page="scan">
          <ScanPage />
        </Shell>
      )}
      {page === "manufacturer" && (
        <Shell page="manufacturer">
          <ManufacturerPage />
        </Shell>
      )}
    </>
  );
}
