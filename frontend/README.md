# AuthentiQ website

The AuthentiQ website: landing page, customer **Scan a product** page and **Manufacturers** page. It talks to the FastAPI backend in `../backend`. How to run the whole project: [../README.md](../README.md). What changed: [../CHANGES.md](../CHANGES.md).

```sh
bun install
bun run dev --port 3000   # needs the backend on http://127.0.0.1:8000 (or set VITE_API_URL, see .env.example)
bun run build             # production build in .output/
bun run test
python3 scripts/build-single-html.py   # whole site in one file: dist-single/authentiq.html
```

Use Bun: `npm install` fails on this project's lock file.

## Stack

TanStack Start + Vite + React 19 + Tailwind CSS v4, TypeScript (strict), three.js for the landing-page globe, jsQR for camera QR scanning. Pages switch on the URL hash (`#/`, `#/scan`, `#/manufacturer`), so the single-file build works when opened from disk.

## Where things live

| File | What it is |
|---|---|
| `src/lib/api.ts` | **Every backend call**, the API address, and the plain-language text for the AI flags. |
| `src/lib/samples.ts` | The `Product` type the pages show, and the two built-in sample reports. |
| `src/components/ScanPage.tsx` | Scan QR / enter product ID, scan report, raise an issue, sample reports. |
| `src/components/ManufacturerPage.tsx` | Register / log in, verification status, product registration form, registered products. An ADMIN login here opens the team console instead. |
| `src/components/TeamConsole.tsx` + `src/lib/adminApi.ts` | The AuthentiQ team's console: stats, manufacturer verification (document viewer, approve, reject with reason, suspend / reactivate), customer issues, audit log. Not linked anywhere. |
| `src/routes/index.tsx` | Landing page + the hash-based page switcher (`App`) at the bottom. |
| `src/components/GlobeDemo.tsx` | Landing-page globe demo (marketing only, no backend). |
| `src/components/Shell.tsx` | Logo, header/footer of the inner pages, shared button and card classes. |
| `src/styles.css` | Colour tokens and animations. |

## Backend calls

| Page action | Endpoint |
|---|---|
| Scan / enter a code | `POST /api/verify/report` |
| Raise an issue | `POST /api/issues` |
| Register as manufacturer | `POST /api/auth/manufacturer/register` (multipart; file field `verification_document`) |
| Log in | `POST /api/auth/login` (manufacturer → their dashboard, admin → team console; session stored in `localStorage`) |
| Verification status | `GET /api/manufacturer/profile` |
| Add products | `POST /api/products/register`, one per product |
| Registered products | `GET /api/products/mine` |

## Notes

- **Camera and location** need `https://` or `localhost`.
- **Newer Chrome:** `window.scrollTo()` returns a Promise. Never `return` it from a `useEffect`, or the page crashes to a blank screen.
- **Single-file build:** JavaScript errors show in a red box at the bottom of the page instead of a blank screen (`scripts/single-entry.tsx`). The backend address is baked in at build time.
- **Colours:** this is the navy and gold scheme. Black and lime only changes the tokens in `src/styles.css`, a few hex values in the components and the `--globe-*` values.
