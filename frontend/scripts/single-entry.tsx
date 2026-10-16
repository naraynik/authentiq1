import { Component, type ReactNode } from "react";
import { createRoot } from "react-dom/client";
import { App } from "./Page";

/** Shows any runtime error on the page itself instead of a blank screen. */
function show(title: string, detail: string) {
  let box = document.getElementById("aq-error");
  if (!box) {
    box = document.createElement("pre");
    box.id = "aq-error";
    box.style.cssText =
      "position:fixed;left:12px;right:12px;bottom:12px;z-index:99999;max-height:60vh;overflow:auto;margin:0;padding:16px;border-radius:12px;background:#fff;border:2px solid #c9302a;color:#1c2b4a;font:13px/1.5 ui-monospace,monospace;white-space:pre-wrap";
    document.body.appendChild(box);
  }
  box.textContent += `${title}\n${detail}\n\n`;
}
window.addEventListener("error", (e) => show("ERROR: " + e.message, String(e.error?.stack ?? "")));
window.addEventListener("unhandledrejection", (e) =>
  show("REJECTION", String(e.reason?.stack ?? e.reason)),
);

class Boundary extends Component<{ children: ReactNode }, { failed: boolean }> {
  override state = { failed: false };
  static getDerivedStateFromError() {
    return { failed: true };
  }
  override componentDidCatch(error: Error, info: { componentStack?: string | null }) {
    show(
      "RENDER ERROR: " + error.message,
      (error.stack ?? "") + "\n" + (info.componentStack ?? ""),
    );
  }
  override render() {
    if (this.state.failed)
      return (
        <p style={{ padding: 40, fontSize: 18 }}>
          Something went wrong on this page. The details are in the box below.{" "}
          <a href="#/" onClick={() => location.reload()} style={{ textDecoration: "underline" }}>
            Reload
          </a>
        </p>
      );
    return this.props.children;
  }
}

createRoot(document.getElementById("root")!).render(
  <Boundary>
    <App />
  </Boundary>,
);
