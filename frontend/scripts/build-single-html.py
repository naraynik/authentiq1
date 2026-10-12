"""
Builds the whole site into ONE self-contained HTML file (dist-single/authentiq.html)
that opens by double-click, with no server. Used for sharing demos.

Run from the project root:  python3 scripts/build-single-html.py
Needs: bun (or swap the bun commands for npx/npm equivalents).
"""
import glob
import json
import os
import re
import subprocess

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(ROOT)

# 1. A copy of the landing route without TanStack's route wrapper, so it can be bundled alone.
src = open("src/routes/index.tsx").read()
src = src.replace('import { createFileRoute } from "@tanstack/react-router";\n', "")
a, b = src.index("export const Route = createFileRoute"), src.index("function Landing() {")
src = src[:a] + src[b:]
src = src.replace("function App() {", "export function App() {")
os.makedirs("scripts/.single", exist_ok=True)
open("scripts/.single/Page.tsx", "w").write(src.replace('from "./', 'from "../../src/routes/'))
open("scripts/.single/main.tsx", "w").write(open("scripts/single-entry.tsx").read())

# 2. Compile the Tailwind CSS through the normal Vite build, then bundle the JS.
subprocess.run("bun run build", shell=True, check=True)
subprocess.run(
    "bun build scripts/.single/main.tsx --minify --format=iife --target=browser "
    "--define process.env.NODE_ENV='\"production\"' "
    # The backend address baked into the file (set VITE_API_URL to change it).
    f"--define import.meta.env.VITE_API_URL='{json.dumps(os.environ.get('VITE_API_URL', 'http://127.0.0.1:8000'))}' "
    "--outfile scripts/.single/app.js",
    shell=True,
    check=True,
)
css = open(glob.glob(".output/public/assets/styles-*.css")[0]).read()
css = re.sub(r"@font-face\{[^}]*\}", "", css)  # fonts come from Google Fonts instead
css = css.replace("Plus Jakarta Sans Variable", "Plus Jakarta Sans").replace("Geist Mono Variable", "Geist Mono")
js = open("scripts/.single/app.js").read().replace("</script", "<\\/script")

head = """<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>AuthentiQ | Product authentication system</title>
<meta name="description" content="AuthentiQ is a product authentication system. Scan the QR code on a product to see where it came from and whether anything looks wrong.">
<link rel="icon" href="data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 100 100'%3E%3Crect width='100' height='100' rx='24' fill='%230b1b3a'/%3E%3Cg transform='translate(14 14) scale(.72)'%3E%3Crect x='12' y='12' width='68' height='68' rx='21' fill='none' stroke='%23fff' stroke-width='15'/%3E%3Crect x='36' y='36' width='20' height='20' rx='5' fill='%23d4a017'/%3E%3Cpath d='M62 62 L90 90' stroke='%230b1b3a' stroke-width='26' stroke-linecap='round'/%3E%3Cpath d='M64 64 L90 90' stroke='%23d4a017' stroke-width='15' stroke-linecap='round'/%3E%3C/g%3E%3C/svg%3E">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Geist+Mono:wght@400;500&family=Plus+Jakarta+Sans:wght@300;400;500;600;700;800&display=swap" rel="stylesheet">
"""
os.makedirs("dist-single", exist_ok=True)
open("dist-single/authentiq.html", "w").write(
    head + "<style>" + css + "</style>\n</head>\n<body>\n<div id=\"root\"></div>\n<script>" + js + "</script>\n</body>\n</html>\n"
)
# The page loads its videos and photos from media/ next to it.
import shutil
shutil.rmtree("dist-single/media", ignore_errors=True)
if os.path.isdir("public/media"):
    shutil.copytree("public/media", "dist-single/media")
print("Wrote dist-single/authentiq.html (+ dist-single/media/)")
