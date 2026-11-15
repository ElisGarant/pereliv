import { tg } from "./tg";

const BASE = import.meta.env.VITE_API_URL ?? "";

export class ApiError extends Error {
  constructor(public status: number, message: string) {
    super(message);
  }
}

export async function api<T>(path: string, opts: { method?: string; body?: unknown } = {}): Promise<T> {
  const headers: Record<string, string> = { "Content-Type": "application/json" };
  if (tg?.initData) headers.Authorization = `tma ${tg.initData}`;
  else if (import.meta.env.VITE_DEV_USER) headers["X-Dev-User"] = String(import.meta.env.VITE_DEV_USER);
  const r = await fetch(BASE + path, { method: opts.method ?? "GET", headers, body: opts.body === undefined ? undefined : JSON.stringify(opts.body) });
  if (r.status === 204) return undefined as T;
  const data = await r.json().catch(() => ({}));
  if (!r.ok) {
    const d = (data as { detail?: unknown }).detail;
    const msg = typeof d === "string" ? d
      : Array.isArray(d) ? "Проверь поля: " + d.map((x: { loc?: unknown[]; msg?: string }) => `${(x.loc ?? []).slice(1).join(".")} ${x.msg ?? ""}`.trim()).join("; ")
      : "Что-то пошло не так. Попробуй ещё раз";
    throw new ApiError(r.status, msg);
  }
  return data as T;
}

export type Role = "guest" | "student" | "member" | "mentor" | "manager" | "admin";
export const RANK: Record<Role, number> = { guest: 0, student: 1, member: 2, mentor: 3, manager: 4, admin: 5 };
export type User = { id: number; first_name: string; last_name?: string | null; username?: string | null; role: Role; direction: string | null; ref_code: string | null };
export type Me = { user: User; application: { id: number; status: "pending" | "approved" | "rejected" | "waitlist"; direction: string } | null; ref_link: string | null };
export const DIRS: Record<string, string> = { inv: "Инвайтинг", msg: "Переписка", call: "Звонки", lead: "Лидген" };
