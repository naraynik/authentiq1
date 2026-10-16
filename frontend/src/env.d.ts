interface ImportMetaEnv {
  /** Backend address, e.g. http://127.0.0.1:8000 (see .env.example). */
  readonly VITE_API_URL?: string;
  /** "1" = preview build: a pretend backend in the browser (src/lib/preview.ts). */
  readonly VITE_PREVIEW?: string;
}
interface ImportMeta {
  readonly env: ImportMetaEnv;
}
