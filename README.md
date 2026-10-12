# AuthentiQ

AuthentiQ is a product authentication system. Manufacturers store their products on a blockchain together with their distributor addresses. A customer scans the QR code on a product and gets a scan report. AI models raise an anomaly when the same code is scanned in places too far apart for the time between scans (a copied code), or far away from every distributor the manufacturer registered. The customer can raise an issue from the report, and the AuthentiQ team handles it in the admin portal.

| Folder | What it is |
|---|---|
| `frontend/` | The website: landing page, **Scan a product**, **Manufacturers** (register, verification status, add products). |
| `admin/` | The **admin portal** for the AuthentiQ team: verify manufacturers (view GSTIN and Aadhaar card, approve / reject / suspend), handle customer issues, see all products and scan numbers. |
| `backend/` | FastAPI API: accounts, products, scans, AI models (Random Forest + GNN), blockchain, customer issues. PostgreSQL database. |
| `blockchain/` | The `ProductVerification` smart contract (Solidity, Hardhat). |
| `ai-engine/` | Training code for the AI models (the trained models are in `backend/app/models/`). |
| `deploy/` | nginx config and the Dockerfile that builds the website + admin portal. |

What changed in this version: [CHANGES.md](CHANGES.md).

---

## How it fits together

```
Browser ──> web (nginx)
              ├─ /          website
              ├─ /admin/    admin portal
              └─ /api/  ──> backend (FastAPI + AI models)
                              ├─> db     PostgreSQL 16   (accounts, products, scans, issues)
                              └─> chain  Ganache          (ProductVerification contract)
```

- The **backend deploys the smart contract by itself** the first time it starts on an empty chain, and remembers its address. Nothing to deploy by hand.
- The blockchain, database and uploaded Aadhaar files are kept in Docker volumes, so they survive restarts and updates.
- Only `web` is reachable from outside. The database and the chain are internal.

---

## Put it online for free (recommended)

**Follow [DEPLOY-RENDER.md](DEPLOY-RENDER.md).** It uses Render for the API, website and admin portal (set up from `render.yaml` in one go), Neon for the database and the public Sepolia test blockchain, so every product record can be looked up on Etherscan. It takes about 45 minutes, all in the browser, with no Docker and no command line.

## Deploy on your own server with Docker

Needs Docker with Compose v2 and about 4 GB of disk (the AI libraries are large).

```bash
git clone <your repo> authentiq && cd authentiq
cp .env.example .env
nano .env              # fill in POSTGRES_PASSWORD, SECRET_KEY, ADMIN_EMAIL, ADMIN_PASSWORD, BLOCKCHAIN_PRIVATE_KEY
docker compose up -d --build
```

`.env.example` shows a one-line command to generate each secret. The backend **refuses to start** in production if `SECRET_KEY` or `ADMIN_PASSWORD` are left at their development defaults.

Then open:

- Website: `http://<server>/`
- Admin portal: `http://<server>/admin/` (log in with `ADMIN_EMAIL` / `ADMIN_PASSWORD`)

### HTTPS (needed for the camera on phones)

Browsers only open the camera and share location on `https://` (or `localhost`). Point a domain at the server, set `DOMAIN=` in `.env`, then:

```bash
docker compose -f docker-compose.yml -f docker-compose.https.yml up -d --build
```

Caddy gets a Let's Encrypt certificate automatically.

### Everyday commands

```bash
docker compose ps                  # what is running
docker compose logs -f backend     # backend log
docker compose up -d --build       # update after pulling new code
docker compose down                # stop (data is kept)
```

Backups: `docker compose exec db pg_dump -U authentiq authentiq > backup.sql`, plus the `chaindata` and `backend_data` volumes.

---

## Run on a Windows laptop

**Easiest (one click):** install [Docker Desktop](https://www.docker.com/products/docker-desktop/), open it once, then double-click **`START-AUTHENTIQ.bat`** in the project folder. The first time it creates `.env` with new passwords, saves the admin login in `ADMIN-LOGIN.txt`, builds everything (5–15 minutes the first time) and opens:

- Website: http://localhost:8080/
- Admin portal: http://localhost:8080/admin/
- API docs: http://localhost:8080/api/docs
- Database viewer: http://localhost:8081

`STOP-AUTHENTIQ.bat` stops it; your data is kept for next time.

**Without Docker (for development):** install Python 3.11, Node.js 18+, [Bun](https://bun.sh) (`powershell -c "irm bun.sh/install.ps1 | iex"`) and PostgreSQL 16 (or use SQLite, see below). Then once:

```powershell
cd backend
python -m venv venv; venv\Scripts\activate
pip install torch --index-url https://download.pytorch.org/whl/cpu
pip install -r requirements.txt
copy .env.example .env            # set DATABASE_URL, ADMIN_PASSWORD, ...
python -m app.seed_admin
cd ..\blockchain; npm install
cd ..\frontend;   bun install
cd ..\admin;      bun install
```

And each time: `.\start-project.ps1` (stop with `.\stop-project.ps1`). Or by hand, each in its own window:

```powershell
cd blockchain; npm run chain:start                                    # blockchain on :8545
cd backend;    venv\Scripts\activate; python -m uvicorn app.main:app --reload --port 8000
cd frontend;   bun run dev --port 3000                                # website   http://localhost:3000
cd admin;      bun run dev                                            # admin     http://localhost:3001
```

The backend's `BLOCKCHAIN_PRIVATE_KEY` must be an account that has funds on that chain (for `npm run chain:start`, the first account of its mnemonic). The contract is deployed automatically if it is missing.

**Quick try without PostgreSQL:** set `DATABASE_URL=sqlite:///./authentiq.db` in `backend/.env`.

---

## Try the whole flow

1. **Website → Manufacturers → Register.** GSTIN must be a valid format (e.g. `27AAACA1234A1Z5`). Password: 8+ characters with upper case, lower case, a number and a symbol. Upload a PDF/PNG/JPG under 5 MB as the Aadhaar card. You see **Verification pending**.
2. **Admin portal → Verification.** Open **View Aadhaar card**, then **Approve** (or **Reject** with a reason, which the manufacturer sees).
3. **Website** → **Check status again** → fill in a distributor (with coordinates, e.g. `20.0050, 73.7600`), the facility and the products → **Submit registration**. Each product gets a code to put in its QR.
4. **Website → Scan a product → Enter product ID** with that code → **No anomaly found**.
5. Scan the same code again from far away (Chrome DevTools → More tools → Sensors → Location → London, then **Share my location**) → **Anomaly raised**.
6. **Raise an issue** on the report → it appears in **Admin portal → Customer issues**.

The **sample reports** (True product / False product) on the scan page are built into the website.

---

## Look inside: database, API and blockchain

**Database (Adminer, a web database viewer).** Start it with the stack:

```bash
docker compose --profile tools up -d adminer
```

Open http://localhost:8081 (on a remote server, first run `ssh -L 8081:127.0.0.1:8081 you@server`). Log in with System **PostgreSQL**, Server **db**, Username **authentiq**, Password = `POSTGRES_PASSWORD` from `.env`, Database **authentiq**. The tables:

| Table | What is in it |
|---|---|
| `users` | Logins (admin and manufacturers). Passwords are stored only as bcrypt hashes. |
| `manufacturers` | Company, GSTIN, address, phone, verification status, rejection reason, path of the Aadhaar file |
| `products` | Every registered product with SKU, batch, facility, distributors, blockchain transaction and block |
| `scan_history` | Every customer scan: time, location, AI scores, verdict (GENUINE / SUSPICIOUS / COUNTERFEIT) and the reasons |
| `issues` | Problems customers raised from a scan report |
| `location_history`, `audit_logs` | Product route updates, and every admin decision (who approved whom, when) |

Adminer can also edit rows. Make changes through the admin portal or the API instead, so the blockchain and the database stay in step.

**API (interactive docs).** http://localhost/api/docs (or http://127.0.0.1:8000/api/docs when running the backend by hand) lists every endpoint and lets you try them: press **Authorize**, paste a token from `POST /api/auth/login`, then **Try it out**.

**Blockchain.** `GET /api/health/blockchain` shows the chain, latest block and contract address. `GET /api/products/{id}` returns a product from both the database and the smart contract side by side, and `GET /api/verify/{id}` says whether they match.

**Logs.** `docker compose logs -f backend` shows each request, contract deployment and AI model loading.

## Tests

```bash
cd backend && python -m pytest -q tests   # 60 tests
cd frontend && bun run test
```

## Notes

- **Blockchain:** a private Ganache chain run by you (chain ID 1337). Moving to a public testnet such as Sepolia means pointing `RPC_URL` at it, funding `BLOCKCHAIN_PRIVATE_KEY`, and removing the `chain` service.
- **Aadhaar files** are stored in the `backend_data` volume and are only reachable through the admin API. Never commit `.env`, `backend/uploads/` or `backend/data/` (`.gitignore` excludes them).
- **Media:** the landing page's videos and photos ship with the site in `frontend/public/media/` (resized to about 4 MB in total; each video in WebM and MP4). Sources and how to replace them: `frontend/public/media/CREDITS.md`.
- Older team docs are in `docs/original/` (they describe the earlier Next.js frontend).

## Team

Monish Patil (mkpatil371323@kkwagh.edu.in) · Anushka Patil (arpatil371323@kkwagh.edu.in) · Narayani Khaparde (npkhaparde370223@kkwagh.edu.in) · Pranjal Wagh (ppwagh371324@kkwagh.edu.in)
