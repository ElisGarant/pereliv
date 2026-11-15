import { useEffect, useState } from "react";
import { api, DIRS, type User } from "../api";
import { ErrorBox, Loading, useToast } from "../ui";

type A = { id: number; user: User; direction: string; age_group: string; hours: string; experience: string; goal: string; about: string;
  role_test: { top: string; scores: Record<string, number>; smart: number } | null };

export default function Applications() {
  const [status, setStatus] = useState("pending");
  const [list, setList] = useState<A[] | null>(null);
  const [err, setErr] = useState("");
  const toast = useToast();
  const load = () => { setList(null); api<A[]>(`/api/admin/applications?status=${status}`).then(setList).catch((e) => setErr(e.message)); };
  useEffect(load, [status]);
  const decide = async (a: A, decision: string) => {
    try { await api(`/api/admin/applications/${a.id}/decision`, { method: "POST", body: { decision } }); toast(`${a.user.first_name}: бот отправил ответ`); load(); }
    catch (e) { toast((e as Error).message); }
  };
  if (err) return <ErrorBox text={err} retry={load} />;
  return (
    <div className="stack">
      <div className="chips">{[["pending", "Новые"], ["waitlist", "Лист ожидания"]].map(([k, n]) => <button key={k} className={status === k ? "on" : ""} onClick={() => setStatus(k)}>{n}</button>)}</div>
      {!list ? <Loading /> : !list.length ? <div className="card empty">Заявок нет</div> : list.map((a) => (
        <section className="card stack" key={a.id}>
          <div className="row"><div className="ava">{a.user.first_name[0]}</div><div className="grow"><b>{a.user.first_name} {a.user.last_name ?? ""}</b>
            <span className="xs mute">{a.user.username ? `@${a.user.username} · ` : ""}{DIRS[a.direction]} · {a.age_group} · {a.hours}</span></div></div>
          {a.role_test && <div className="sm">Тест: <b>{DIRS[a.role_test.top]}</b> · задачи {a.role_test.smart}/2</div>}
          <div className="sm mute">Опыт: {a.experience} · цель: {a.goal}{a.about ? ` · «${a.about}»` : ""}</div>
          <div className="row" style={{ gap: 6, flexWrap: "wrap" }}>
            <button className="btn s pri" onClick={() => decide(a, "approved")}>Взять</button>
            <button className="btn s" onClick={() => decide(a, "waitlist")}>В лист ожидания</button>
            <button className="btn s" onClick={() => decide(a, "rejected")}>Отказать</button>
          </div>
        </section>
      ))}
    </div>
  );
}
