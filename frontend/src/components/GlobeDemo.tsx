import { useEffect, useRef, useState } from "react";
import * as THREE from "three";
import { LAND_MASK } from "@/assets/landmask";

type City = { name: string; lat: number; lon: number };
type Scenario = {
  id: "genuine" | "cloned";
  label: string;
  from: City;
  to: City;
  minutes: number;
  gapLabel: string;
};

const MUMBAI: City = { name: "Mumbai", lat: 19.076, lon: 72.8777 };
const SCENARIOS: Scenario[] = [
  {
    id: "cloned",
    label: "Copied code",
    from: MUMBAI,
    to: { name: "London", lat: 51.5074, lon: -0.1278 },
    minutes: 1,
    gapLabel: "under 1 minute",
  },
  {
    id: "genuine",
    label: "Normal journey",
    from: MUMBAI,
    to: { name: "Pune", lat: 18.5204, lon: 73.8567 },
    minutes: 180,
    gapLabel: "3 hours",
  },
];

const SPEED_LIMIT = 800; // km/h, same threshold the backend uses
const R = 1.6;
const rad = (d: number) => (d * Math.PI) / 180;

/** Great-circle distance in km, the same Haversine formula the backend runs. */
function haversine(a: City, b: City) {
  const dLat = rad(b.lat - a.lat);
  const dLon = rad(b.lon - a.lon);
  const h =
    Math.sin(dLat / 2) ** 2 + Math.cos(rad(a.lat)) * Math.cos(rad(b.lat)) * Math.sin(dLon / 2) ** 2;
  return 6371 * 2 * Math.asin(Math.sqrt(h));
}

function toVec(lat: number, lon: number, r = R) {
  return new THREE.Vector3(
    r * Math.cos(rad(lat)) * Math.sin(rad(lon)),
    r * Math.sin(rad(lat)),
    r * Math.cos(rad(lat)) * Math.cos(rad(lon)),
  );
}

const GENUINE = 0x0b7a55;
const FAKE = 0xc9302a;

export default function GlobeDemo() {
  const mount = useRef<HTMLDivElement>(null);
  const api = useRef<{ play: (s: Scenario) => void } | null>(null);
  const [scenario, setScenario] = useState<Scenario>(SCENARIOS[0]!);

  const km = haversine(scenario.from, scenario.to);
  const speed = km / (scenario.minutes / 60);
  const fake = speed > SPEED_LIMIT;

  useEffect(() => {
    const el = mount.current;
    if (!el) return;
    const reduce = window.matchMedia("(prefers-reduced-motion: reduce)").matches;

    const renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true });
    renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
    el.appendChild(renderer.domElement);
    const scene = new THREE.Scene();
    const camera = new THREE.PerspectiveCamera(34, 1, 0.1, 50);
    camera.position.z = 6.2;

    const globe = new THREE.Group();
    scene.add(globe);
    // Earth: a flat, map-like globe. Land and sea colours come from the site theme.
    const css = getComputedStyle(el);
    const landColor = css.getPropertyValue("--globe-land").trim() || "#24467f";
    const seaColor = css.getPropertyValue("--globe-sea").trim() || "#dfe9f7";
    const canvas = document.createElement("canvas");
    canvas.width = 2048;
    canvas.height = 1024;
    const ctx = canvas.getContext("2d")!;
    ctx.fillStyle = seaColor;
    ctx.fillRect(0, 0, canvas.width, canvas.height);
    const earthTex = new THREE.CanvasTexture(canvas);
    earthTex.colorSpace = THREE.SRGBColorSpace;
    earthTex.anisotropy = 8;
    let disposed = false;
    const mask = new Image();
    mask.onload = () => {
      if (disposed) return;
      // Turn the grey mask into "land colour with alpha", then paint it over the sea.
      const tmp = document.createElement("canvas");
      tmp.width = mask.width;
      tmp.height = mask.height;
      const tctx = tmp.getContext("2d")!;
      tctx.drawImage(mask, 0, 0);
      const img = tctx.getImageData(0, 0, tmp.width, tmp.height);
      const land = new THREE.Color(landColor);
      const [lr, lg, lb] = [land.r, land.g, land.b].map((v) =>
        Math.round(255 * (v <= 0.0031308 ? v * 12.92 : 1.055 * v ** (1 / 2.4) - 0.055)),
      ) as [number, number, number];
      for (let i = 0; i < img.data.length; i += 4) {
        img.data[i + 3] = 255 - img.data[i]!; // water is white in the mask
        img.data[i] = lr;
        img.data[i + 1] = lg;
        img.data[i + 2] = lb;
      }
      tctx.putImageData(img, 0, 0);
      ctx.imageSmoothingQuality = "high";
      ctx.drawImage(tmp, 0, 0, canvas.width, canvas.height);
      earthTex.needsUpdate = true;
    };
    mask.src = LAND_MASK;
    const earth = new THREE.Mesh(
      new THREE.SphereGeometry(R, 96, 64),
      new THREE.MeshStandardMaterial({ map: earthTex, roughness: 1, metalness: 0 }),
    );
    // three.js puts longitude 0 on +X; this file's toVec() puts it on +Z.
    earth.rotation.y = -Math.PI / 2;
    globe.add(earth);
    scene.add(new THREE.AmbientLight(0xffffff, 2.3));
    const sun = new THREE.DirectionalLight(0xffffff, 1.1);
    sun.position.set(-3, 3, 5);
    scene.add(sun);

    // graticule
    const pts: number[] = [];
    const seg = (a: THREE.Vector3, b: THREE.Vector3) => pts.push(a.x, a.y, a.z, b.x, b.y, b.z);
    for (let lat = -75; lat <= 75; lat += 15)
      for (let lon = -180; lon < 180; lon += 4)
        seg(toVec(lat, lon, R * 1.001), toVec(lat, lon + 4, R * 1.001));
    for (let lon = -180; lon < 180; lon += 15)
      for (let lat = -88; lat < 88; lat += 4)
        seg(toVec(lat, lon, R * 1.001), toVec(lat + 4, lon, R * 1.001));
    const gratGeo = new THREE.BufferGeometry();
    gratGeo.setAttribute("position", new THREE.Float32BufferAttribute(pts, 3));
    globe.add(
      new THREE.LineSegments(
        gratGeo,
        new THREE.LineBasicMaterial({ color: 0xffffff, transparent: true, opacity: 0.1 }),
      ),
    );

    const dotGeo = new THREE.SphereGeometry(0.05, 20, 20);
    const ringGeo = new THREE.RingGeometry(0.058, 0.078, 32);
    const haloGeo = new THREE.RingGeometry(0.09, 0.11, 32);
    const makeMarker = () => {
      const m = new THREE.Group();
      const mat = new THREE.MeshBasicMaterial({ color: GENUINE });
      const halo = new THREE.Mesh(
        haloGeo,
        new THREE.MeshBasicMaterial({ color: GENUINE, transparent: true, side: THREE.DoubleSide }),
      );
      // white ring so the dot stands out against land and sea
      const ring = new THREE.Mesh(
        ringGeo,
        new THREE.MeshBasicMaterial({ color: 0xffffff, side: THREE.DoubleSide }),
      );
      m.add(new THREE.Mesh(dotGeo, mat), ring, halo);
      globe.add(m);
      return { m, mat, halo };
    };
    const a = makeMarker();
    const b = makeMarker();

    // The route is a thin tube (plain WebGL lines are only one pixel wide).
    const ARC_N = 120;
    const ARC_SIDES = 8;
    const arcMat = new THREE.MeshBasicMaterial({ color: FAKE });
    const arc = new THREE.Mesh(new THREE.BufferGeometry(), arcMat);
    globe.add(arc);

    let target = { x: 0, y: 0 };
    let zoom = 1; // below 1 moves the camera in for short journeys
    let baseZ = 6.2;
    let playStart = performance.now();

    const place = (mk: ReturnType<typeof makeMarker>, c: City) => {
      const v = toVec(c.lat, c.lon, R * 1.01);
      mk.m.position.copy(v);
      mk.m.lookAt(v.clone().multiplyScalar(2));
    };

    const play = (s: Scenario) => {
      const isFake = haversine(s.from, s.to) / (s.minutes / 60) > SPEED_LIMIT;
      const color = isFake ? FAKE : GENUINE;
      place(a, s.from);
      place(b, s.to);
      a.mat.color.set(GENUINE);
      (a.halo.material as THREE.MeshBasicMaterial).color.set(GENUINE);
      b.mat.color.set(color);
      (b.halo.material as THREE.MeshBasicMaterial).color.set(color);
      arcMat.color.set(color);

      const va = toVec(s.from.lat, s.from.lon, 1);
      const vb = toVec(s.to.lat, s.to.lon, 1);
      const angle = va.angleTo(vb);
      // Two nearby cities would sit on top of each other, so zoom in and shrink the markers.
      const near = angle < 0.15;
      zoom = near ? 0.5 : 1;
      for (const mk of [a, b]) mk.m.scale.setScalar(near ? 0.32 : 1);
      const lift = Math.min(0.45, angle * 0.35);
      const points: THREE.Vector3[] = [];
      for (let i = 0; i <= ARC_N; i++) {
        const t = i / ARC_N;
        points.push(
          new THREE.Vector3()
            .copy(va)
            .multiplyScalar(Math.sin((1 - t) * angle) / Math.sin(angle))
            .add(vb.clone().multiplyScalar(Math.sin(t * angle) / Math.sin(angle)))
            .normalize()
            .multiplyScalar(R * (1.015 + Math.sin(Math.PI * t) * lift)),
        );
      }
      arc.geometry.dispose();
      arc.geometry = new THREE.TubeGeometry(
        new THREE.CatmullRomCurve3(points),
        ARC_N,
        near ? 0.004 : 0.014,
        ARC_SIDES,
      );

      const mid = va.clone().add(vb).normalize();
      target = { x: Math.asin(mid.y) * 0.75, y: -Math.atan2(mid.x, mid.z) };
      playStart = performance.now();
    };
    api.current = { play };
    play(SCENARIOS[0]!);
    globe.rotation.set(target.x, target.y - 0.6, 0);

    const resize = () => {
      const { clientWidth: w, clientHeight: h } = el;
      renderer.setSize(w, h);
      camera.aspect = w / h;
      baseZ = w / h < 1 ? 7.4 : 6.2;
      camera.position.z = baseZ * zoom;
      camera.updateProjectionMatrix();
    };
    resize();
    const ro = new ResizeObserver(resize);
    ro.observe(el);

    let visible = true;
    const io = new IntersectionObserver(([e]) => {
      visible = e?.isIntersecting ?? true;
    });
    io.observe(el);

    let raf = 0;
    const frame = () => {
      raf = requestAnimationFrame(frame);
      if (!visible) return;
      const now = performance.now();
      const ease = reduce ? 1 : 0.07;
      globe.rotation.x += (target.x - globe.rotation.x) * ease;
      globe.rotation.y += (target.y - globe.rotation.y) * ease;
      camera.position.z += (baseZ * zoom - camera.position.z) * ease;
      const p = reduce ? 1 : Math.min(1, Math.max(0, (now - playStart - 500) / 1400));
      arc.geometry.setDrawRange(0, Math.floor(p * ARC_N) * ARC_SIDES * 6);
      b.m.visible = p >= 1;
      const pulse = reduce ? 1 : 1 + ((now / 900) % 1) * 1.6;
      for (const mk of [a, b]) {
        mk.halo.scale.setScalar(pulse);
        (mk.halo.material as THREE.MeshBasicMaterial).opacity = reduce
          ? 0.6
          : 1 - ((now / 900) % 1);
      }
      renderer.render(scene, camera);
    };
    frame();

    return () => {
      cancelAnimationFrame(raf);
      ro.disconnect();
      io.disconnect();
      try {
        scene.traverse((o) => {
          if (o instanceof THREE.Mesh || o instanceof THREE.Line) {
            o.geometry.dispose();
            (Array.isArray(o.material) ? o.material : [o.material]).forEach((m) => m.dispose());
          }
        });
        disposed = true;
        earthTex.dispose();
        renderer.dispose();
        renderer.domElement.remove();
      } catch {
        /* a failed GPU clean-up must not take the page down */
      }
    };
  }, []);

  const choose = (s: Scenario) => {
    setScenario(s);
    api.current?.play(s);
  };

  const fmt = (n: number) => Math.round(n).toLocaleString("en-US");

  return (
    <div className="grid overflow-hidden rounded-2xl border border-line bg-surface lg:grid-cols-[1.1fr_1fr]">
      <div className="relative min-h-[340px] border-b border-line globe-bg lg:min-h-[520px] lg:border-r lg:border-b-0">
        <div
          ref={mount}
          className="absolute inset-0"
          role="img"
          aria-label={`Globe showing a scan in ${scenario.from.name} followed by a scan in ${scenario.to.name}`}
        />
      </div>

      <div className="flex flex-col p-6 sm:p-8">
        <div
          role="group"
          aria-label="Choose a scenario"
          className="inline-flex self-start rounded-full border border-line bg-paper p-1"
        >
          {SCENARIOS.map((s) => (
            <button
              key={s.id}
              type="button"
              aria-pressed={scenario.id === s.id}
              onClick={() => choose(s)}
              className={`rounded-full px-4 py-2 text-sm font-medium transition-colors ${
                scenario.id === s.id ? "bg-ink text-white" : "text-subtle hover:text-ink"
              }`}
            >
              {s.label}
            </button>
          ))}
        </div>

        <ol className="mt-8 space-y-4 font-mono text-sm">
          <li className="flex items-center justify-between gap-4">
            <span className="flex items-center gap-3">
              <span className="size-2 rounded-full bg-genuine" />
              Scan 1 · {scenario.from.name}
            </span>
            <span className="text-subtle">10:42:07</span>
          </li>
          <li className="flex items-center justify-between gap-4">
            <span className="flex items-center gap-3">
              <span className={`size-2 rounded-full ${fake ? "bg-fake" : "bg-genuine"}`} />
              Scan 2 · {scenario.to.name}
            </span>
            <span className="text-subtle">{fake ? "10:42:51" : "13:42:07"}</span>
          </li>
        </ol>

        <dl className="mt-8 grid grid-cols-2 gap-px overflow-hidden rounded-xl border border-line bg-line">
          {[
            ["Distance", `${fmt(km)} km`],
            ["Time between scans", scenario.gapLabel],
            [
              "Implied speed",
              fake ? `over ${fmt(Math.floor(speed / 1000) * 1000)} km/h` : `${fmt(speed)} km/h`,
            ],
            ["Allowed maximum", `${SPEED_LIMIT} km/h`],
          ].map(([k, v]) => (
            <div key={k} className="bg-surface p-4">
              <dt className="text-xs text-subtle">{k}</dt>
              <dd className="mt-1 font-mono text-base font-medium">{v}</dd>
            </div>
          ))}
        </dl>

        <div
          aria-live="polite"
          className={`mt-6 rounded-xl p-5 ${fake ? "bg-fake-soft text-fake" : "bg-genuine-soft text-genuine"}`}
        >
          <p className="font-mono text-xs tracking-widest">AI MODEL</p>
          <p className="mt-1 text-2xl font-semibold tracking-tight">
            {fake ? "Anomaly raised" : "No anomaly"}
          </p>
          <p className="mt-1 text-sm text-ink/80">
            {fake
              ? "No product travels that fast. The same code is in two places at once, so the customer is warned and can raise an issue."
              : "A normal journey for one product. The blockchain record and the scan history agree."}
          </p>
        </div>

        <p className="mt-auto pt-6 text-xs text-subtle">
          Illustrative scans. The distance is calculated live with the Haversine formula the backend
          uses.
        </p>
      </div>
    </div>
  );
}
