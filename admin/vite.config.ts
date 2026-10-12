import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";
import tailwindcss from "@tailwindcss/vite";

// base "./" so the built portal works under any path (served at /admin/ in deployment).
export default defineConfig({
  base: "./",
  plugins: [react(), tailwindcss()],
});
