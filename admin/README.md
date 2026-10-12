# AuthentiQ admin portal

For the AuthentiQ team: verify manufacturers (GSTIN + Aadhaar card → approve, reject with a reason, suspend), handle customer issues, and see all registered products and scan numbers. Only `ADMIN` accounts can log in (created from `ADMIN_EMAIL` / `ADMIN_PASSWORD` by `python -m app.seed_admin`, which the Docker image runs on every start).

```sh
bun install
bun run dev        # http://localhost:3001, talks to the backend at http://127.0.0.1:8000
bun run build      # static files in dist/ (served at /admin/ by deploy/nginx.conf)
```

`VITE_API_URL` sets the backend address at build time; empty means "same site" (the deployment default). The login token is kept in `sessionStorage`, so closing the tab logs you out.

Everything is in `src/App.tsx` (screens) and `src/api.ts` (backend calls). Colours match the website (`src/styles.css`).
