import { createContext, useCallback, useContext, useState, type ReactNode } from "react";

const ToastCtx = createContext<(t: string) => void>(() => {});
export const useToast = () => useContext(ToastCtx);

export function ToastProvider({ children }: { children: ReactNode }) {
  const [text, setText] = useState("");
  const [on, setOn] = useState(false);
  const show = useCallback((t: string) => {
    setText(t);
    setOn(true);
    window.clearTimeout((show as unknown as { t?: number }).t);
    (show as unknown as { t?: number }).t = window.setTimeout(() => setOn(false), 2400);
  }, []);
  return (
    <ToastCtx.Provider value={show}>
      {children}
      <div className={`toast ${on ? "on" : ""}`} role="status">{text}</div>
    </ToastCtx.Provider>
  );
}

export const fmtT = (s: number) => `${String(Math.floor(s / 60)).padStart(2, "0")}:${String(Math.floor(s % 60)).padStart(2, "0")}`;

export function Loading() {
  return <div className="empty">Загружаю…</div>;
}

export function ErrorBox({ text, retry }: { text: string; retry?: () => void }) {
  return (
    <div className="card empty">
      <p style={{ margin: "0 0 12px" }}>{text}</p>
      {retry && <button className="btn s" onClick={retry}>Повторить</button>}
    </div>
  );
}

/** Мини-Markdown для конспектов: ## заголовок, - список, > фраза, **жирный**, [мм:сс] тайм-код. Текст экранируется. */
export function md(src: string): string {
  const e = src.replace(/[&<>"]/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" })[c]!)
    .replace(/\*\*(.+?)\*\*/g, "<b>$1</b>").replace(/\[(\d{1,2}:\d{2})\]/g, '<span class="tc">$1</span>');
  let h = "", ul = false;
  for (const line of e.split("\n")) {
    const t = line.trim();
    if (t.startsWith("- ")) { if (!ul) { h += '<ul class="rules">'; ul = true; } h += `<li>${t.slice(2)}</li>`; continue; }
    if (ul) { h += "</ul>"; ul = false; }
    if (!t) continue;
    if (t.startsWith("## ")) h += `<h4>${t.slice(3)}</h4>`;
    else if (t.startsWith("&gt; ")) h += `<div class="script">${t.slice(5)}</div>`;
    else h += `<p>${t}</p>`;
  }
  return ul ? h + "</ul>" : h;
}
