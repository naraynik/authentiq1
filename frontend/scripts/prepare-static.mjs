// Prepares scripts/static/ for `vite build -c vite.static.config.ts`:
// a plain single-page build of the site (no server rendering), used for hosting
// on any static host (Render static site, Vercel, Netlify, nginx).
import { mkdirSync, readFileSync, writeFileSync } from "node:fs";

const src = readFileSync("src/routes/index.tsx", "utf8");
let page = src.replace('import { createFileRoute } from "@tanstack/react-router";\n', "");
const a = page.indexOf("export const Route = createFileRoute");
const b = page.indexOf("function Landing() {");
if (a < 0 || b < 0) throw new Error("src/routes/index.tsx changed shape; update prepare-static.mjs");
page = page.slice(0, a) + page.slice(b);
page = page.replace("function App() {", "export function App() {").replaceAll('from "./', 'from "../../src/routes/');

mkdirSync("scripts/static", { recursive: true });
writeFileSync("scripts/static/Page.tsx", page);
const entry = readFileSync("scripts/single-entry.tsx", "utf8");
writeFileSync(
  "scripts/static/main.tsx",
  'import "@fontsource-variable/plus-jakarta-sans";\nimport "@fontsource-variable/geist-mono";\nimport "../../src/styles.css";\n' + entry,
);
writeFileSync(
  "scripts/static/index.html",
  `<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>AuthentiQ | Product authentication system</title>
<meta name="description" content="AuthentiQ is a product authentication system. Scan the QR code on a product to see where it came from and whether anything looks wrong.">
<link rel="icon" href="./favicon.svg" type="image/svg+xml">
</head>
<body>
<div id="root"></div>
<script type="module" src="./main.tsx"></script>
</body>
</html>
`,
);
console.log("scripts/static ready");
