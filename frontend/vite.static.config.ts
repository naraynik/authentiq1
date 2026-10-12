// Plain static build of the website: `bun run build:static` -> dist-static/
// (see scripts/prepare-static.mjs). The normal `vite build` keeps using vite.config.ts.
import { fileURLToPath } from "node:url";
import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";
import tailwindcss from "@tailwindcss/vite";

export default defineConfig({
  root: fileURLToPath(new URL("./scripts/static", import.meta.url)),
  publicDir: fileURLToPath(new URL("./public", import.meta.url)),
  base: "./",
  plugins: [react(), tailwindcss()],
  resolve: { alias: { "@": fileURLToPath(new URL("./src", import.meta.url)) } },
  build: { outDir: fileURLToPath(new URL("./dist-static", import.meta.url)), emptyOutDir: true },
});
