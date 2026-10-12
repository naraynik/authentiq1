# Changes

## Version 4: free cloud deployment (Render + Neon + Sepolia)

Step-by-step guide: `DEPLOY-RENDER.md`. Rehearsed here with the exact Render start command and settings, a fresh PostgreSQL database, a chain that behaves like Sepolia (chain ID 11155111, a block every 12 seconds) and the website and admin portal built with Render's build commands. The full flow passed, including a restart with a wiped disk. Not tried on the real Render, Neon or Sepolia from here: those need your accounts.

- `render.yaml` Blueprint: API (Python, free plan), website and admin portal (static sites).
- **Aadhaar files are stored in the database** (`manufacturers.verification_document`), because Render's disk is wiped on every restart. Older files on disk still work.
- **The deployed contract address is remembered in the database** (`app_state` table, per chain), so restarts do not deploy a new contract and spend test ETH. If deployment fails (e.g. the wallet is empty), it is retried at most once a minute, and on the next product registration.
- A product whose blockchain write failed can be **submitted again with the same code**.
- **Etherscan links**: set `EXPLORER_TX_URL`; the scan report and the manufacturer's product list link to the transaction.
- **Wallet balance** in `/api/health/blockchain` and in the admin portal header (turns amber below 0.005 ETH).
- `requirements-render.txt`: no PyTorch, so the API fits in 512 MB (about 235 MB measured). The GNN is skipped there, and its tests skip themselves.
- Website: `bun run build:static` makes a plain static build (`dist-static/`) for any static host.
- CORS: `CORS_ORIGIN_REGEX`; in production only listed origins are allowed (no more `*`).
- `postgres://` database URLs are accepted. Interactive API docs are at `/api/docs` and work without internet.
- Friendlier messages on the manufacturer page when the blockchain fails (e.g. "out of test funds").
- Docker: optional database viewer (`docker compose --profile tools up -d adminer`), plus `START-AUTHENTIQ.bat` / `STOP-AUTHENTIQ.bat` for Windows.

## Version 3.1: videos and photos built in

Pexels stopped allowing other sites to link to its files, so the landing page's videos and photos disappeared. They now ship with the site in `frontend/public/media/`: resized from 62 MB of 4K originals to about 4 MB, each video in WebM and MP4 with a still preview image, served by nginx at `/media/`. The single-file build writes a `media/` folder next to `authentiq.html`. `frontend/scripts/prepare-media.sh` redoes the resizing; `CREDITS.md` lists the sources.

## Version 3: complete and deployable

Tested in a production-like setup: PostgreSQL 16, a persistent Ganache chain, the backend on Python 3.11 with PyTorch + PyTorch Geometric, and the website + admin portal built exactly as `deploy/web.Dockerfile` does and served by nginx with `deploy/nginx.conf`. Flow tested in a browser: manufacturer registers → admin views the Aadhaar card and approves in the admin portal → products written to the chain → customer scans (genuine, then a copied code in London) → issue raised → admin marks it reviewed. Then the chain and backend were restarted: the product was still verified on-chain. Backend tests: **60 / 60 pass** (including both GNN tests).

Not tested here: building the Docker images themselves (Docker Hub is blocked in the test machine). `docker compose config` validates, and every command inside the Dockerfiles was run as-is.

**New**
- **Admin portal** (`admin/`, served at `/admin/`): admin-only login; **Verification** with Pending / Approved / Rejected / Suspended filters, company details, **View Aadhaar card** (image or PDF, with download), **Approve**, **Reject** with a reason the manufacturer sees, **Suspend**, **Approve now** for rejected/suspended accounts; **Customer issues** (open / reviewed / closed, location link); **Products** with scan numbers and blockchain block; live "Blockchain online" indicator; refreshes every 30 s. Replaces the old Next.js app.
- **Deployment:** `docker-compose.yml` (db, chain, backend, web), `docker-compose.https.yml` (Caddy, automatic HTTPS), `backend/Dockerfile`, `deploy/web.Dockerfile`, `deploy/nginx.conf`, root `.env.example`, `Makefile`.
- **Automatic contract deployment:** on start the backend uses `CONTRACT_ADDRESS` if a contract is there, else the address saved in `CONTRACT_STATE_FILE`, else deploys `ProductVerification` from the compiled artifact (`backend/app/contracts/ProductVerification.json`, now with bytecode) and saves the address. If the chain is down at start, it retries on the next blockchain call.
- **GNN connected:** each scan now also runs the GNN on the product's scan history (scans as nodes, consecutive scans linked) and blends its counterfeit probability 60/40 with the Random Forest. Scan responses say which models ran (`models_used`).

**Backend fixes and settings**
- `scikit-learn` pinned to 1.5.x: the models were saved with 1.5.0, and newer versions warn that results may be invalid.
- `ENVIRONMENT=production` refuses to start with the default `SECRET_KEY` or `ADMIN_PASSWORD`.
- `CORS_ORIGINS` env setting (comma-separated) instead of the hard-coded list with `"*"`.
- Approving a manufacturer clears an old rejection reason.

**Website**
- `VITE_API_URL` may be empty to call the API on the same site (used behind nginx).

**Removed:** `admin-portal/` (old Next.js app), `docker-compose.full.yml` and the old `Makefile` (they built the Next.js app). The older docs moved to `docs/original/`.

---

## Version 2: website connected to the backend

This version connects the new website (`frontend/`) to the existing backend. Backend changes are **additive**: every existing endpoint and request shape still works, and the existing tests still pass. Please review the backend list below.

Tested here end to end: register → admin approve → add products (written to a local Hardhat chain) → customer scan → copied-code anomaly → raise an issue. Tested on both SQLite and PostgreSQL 16, including upgrading a database created by the previous version. Backend tests: 58 pass. (At that point PyTorch was not installed in the test machine, so the 2 GNN tests were skipped as failures; fixed in version 3.)

---

## Backend (`backend/`): please review

### New and changed endpoints

| Endpoint | What | Auth |
|---|---|---|
| `POST /api/verify/report` **(new)** | One call for the scan page. Body: `{product_id, latitude?, longitude?, location?}`. Records the scan (same `scan_service` pipeline as `/api/verify/scan`), runs the DB + blockchain check, returns `{found, product, verification, scan, history}`. `found: false` for unknown codes. Matches product IDs exactly first, then case-insensitively (customers type IDs). | Public |
| `POST /api/issues` **(new)** | Customer raises an issue: `{product_id, message, contact?, latitude?, longitude?}`. Accepted for unregistered codes too (likely fakes); the reply says `registered_product: true/false`. | Public |
| `GET /api/admin/issues` **(new)** | List issues, newest first. `?status=OPEN` filter. | Admin |
| `PUT /api/admin/issues/{id}/status` **(new)** | `{status: OPEN \| REVIEWED \| CLOSED}`. | Admin |
| `GET /api/products/mine` **(new)** | The logged-in manufacturer's products. | Manufacturer (any status) |
| `POST /api/products/register` **(extended)** | Also accepts `sku`, `facility` `{street, city, country, lat, lon}` and `distributors` `[{name, street, city, country, lat, lon}]`. `product_id` is now optional (generated as `AQ-XXXXXXXX`), `manufacturing_date` defaults to now, and `current_location` / `next_location` default to the facility / first distributor as text. The old body still works unchanged. Now also saves the block number. | Approved manufacturer |
| `GET /api/products`, `GET /api/products/{id}` | Responses include the new fields (`sku`, `facility`, `distributors`, `registration_block`). | unchanged |

Unused by the website but untouched: `/api/verify/{qr_code}`, `/api/verify/scan`, `/api/scans/*`, location/status updates, batch registration, admin manufacturer endpoints.

### Database

- `products`: 4 new **nullable** columns: `sku` (varchar), `facility` (JSON), `distributors` (JSON), `registration_block` (integer).
- New table `issues` (`app/models/issue.py`).
- Existing databases are upgraded automatically on start: `create_all` makes the new table and `app/database/upgrade.py` adds the missing product columns (idempotent, SQLite and PostgreSQL). If you use Alembic instead: `alembic upgrade head` runs the new migration `002_web_frontend_fields` (also idempotent).

### AI / scan logic (`app/services/scan_service.py`)

1. **Distributor check (new).** If the customer shared their location and the manufacturer gave coordinates for distributors or the facility, a scan more than `DISTRIBUTOR_RADIUS_KM = 150` km from all of them gets the flag `Scan Location Does Not Match Registered Distributor`, is passed to the Random Forest as `is_location_anomaly = 1`, and the anomaly score is raised to at least 0.40 (so the verdict is at least SUSPICIOUS). The radius is a guess; adjust it.
2. **Bug fix: "Location not shared" counted as a different place.** Previously a scan with no location following a scan with coordinates (or two scans with different text) was treated as a 500 km jump, so a customer who did not share location within 6 minutes of another scan got **COUNTERFEIT**. Place names are now only compared when neither scan has coordinates and both actually name a place.
3. **Compare with the last scan that has coordinates.** When the current scan has coordinates, distance and speed are measured from the most recent scan *with* coordinates, so a scan without location in between can no longer hide a copied code.
4. Response's `behavioral_analysis` also includes `distributor_mismatch` and `nearest_registered_place_km`.

### Fixes to setup

- `requirements.txt`: added **`web3`** (the blockchain service imports it but it was missing), and pinned **`sqlalchemy<2.1`**: SQLAlchemy 2.1 makes `postgresql://` URLs use the psycopg 3 driver, so a fresh `pip install` fails with `No module named 'psycopg'` because we ship psycopg2.
- `alembic/versions/001_initial_schema.py`: boolean defaults were `sa.text('1')` / `sa.text('0')`, which PostgreSQL rejects (`column "is_active" is of type boolean but default expression is of type integer`). Now `sa.true()` / `sa.false()`.
- `app/seed_admin.py` creates the tables first, so it works before the API has ever started.

### Tests

`tests/test_web_frontend.py` (6 tests): structured product registration and `/products/mine`, old payload still works, genuine scan then copied code (London), unshared location is not a different place, unknown code, issues (public create, admin-only list).

### Not changed, worth a look later

- `ALLOWED_ORIGINS` includes `"*"` together with `allow_credentials=True`. Fine for development. In deployment the website and API share a domain; set `CORS_ORIGINS` if they do not (version 3).
- `Pre-mature Scan Sequence` flags scans within 30 minutes of `manufacturing_date`. Since the website does not ask for a manufacturing date (it defaults to now), freshly registered products get this flag on their first scans. It does not change the verdict on its own, and the website does not show it to customers.
- The verification documents are stored under `backend/uploads/documents/`. That folder is in `.gitignore`; the test uploads that were in the zip were removed.
- The AI models are trained on synthetic optical/IoT features; scan behaviour is mapped onto them in `ai_client._scan_feature_row`. Retraining on real scan data (velocity, distance, distributor match) would make the AI scores more meaningful. The hard rules (impossible travel, distributor distance) do not depend on it.

---

## Website (`frontend/`)

- `src/lib/api.ts` **(new)**: every backend call. Backend address from `VITE_API_URL` (default `http://127.0.0.1:8000`, see `.env.example`). Turns the AI flags into plain sentences for customers.
- `src/lib/samples.ts` replaces `demoStore.ts`: now only the two built-in sample reports.
- **Scan page:** real scans through `POST /api/verify/report`, sends real latitude/longitude when the customer shares location, loading and error states ("Cannot reach the AuthentiQ server…"), multiple distributors in the report, real **Raise an issue**. Sample reports stay local.
- **Manufacturer page:** real register (multipart, now also asks for **company address** and **phone**, which the backend requires, and explains the password rule), real login (JWT kept in the browser so a reload keeps you logged in), **Verification pending** with **Check status again** (the demo "Continue as verified" button is gone), rejected/suspended screens with the reason, product form prefilled and locked with the verified company details, coordinates validated, optional **Code in your QR** per product, products sent one by one with per-product success/failure, **Your registered products** from `/api/products/mine`.
- Removed the "This page runs on sample data" notes.
- The single-file build bakes in the backend address (`scripts/build-single-html.py`).
- Colour scheme: this is the navy and gold version. The black and lime version only differs in colour values.


## Removed from the package

- `AuthentiQ_Completed_Phase4_Work/`: an older snapshot of the backend and contract scripts (`backend/` is newer, e.g. it has the Phase 5 tests). It is still in the original backend zip if anyone needs it.
- Root `package-lock.json` (the npm workspace pointed at the old frontend). Root `package.json` now just has helper scripts.
