import { useEffect, useState } from "react";
import { api, DIRS } from "../api";
import { ErrorBox, Loading, useToast } from "../ui";

type O = { id: number; type: string; title: string; client: string; rate: string; unit: string; volume: string; deadline: string;
  seats: number; taken: number; brief: string; rules: string[]; my_status: "requested" | "active" | "done" | null };

export default function Orders() {
  const [list, setList] = useState<O[] | null>(null);
  const [err, setErr] = useState("");
  const [open, setOpen] = useState<number | null>(null);
  const toast = useToast();
  const load = () => api<O[]>("/api/orders").then(setList).catch((e) => setErr(e.message));
  useEffect(() => { load(); }, []);
  if (err) return <ErrorBox text={err} retry={load} />;
  if (!list) return <Loading />;
  const take = async (o: O) => {
    try { await api(`/api/orders/${o.id}/take`, { method: "POST" }); toast("Отклик отправлен менеджеру"); load(); }
    catch (e) { toast((e as Error).message); }
  };
  return (
    <div className="stack">
      {!list.length && <div className="card empty">Открытых заказов пока нет. Новые придут уведомлением в бот.</div>}
      {list.map((o) => (
        <section className="card" key={o.id}>
          <button className="ord" onClick={() => setOpen(open === o.id ? null : o.id)}>
            <div className="btw"><span className={`tag ${o.type === "inv" ? "acc" : ""}`}>{DIRS[o.type] ?? o.type}</span><span className="price">{o.rate} <span className="xs mute">{o.unit}</span></span></div>
            <h4>{o.title}</h4>
            <div className="meta"><span>Объём <b>{o.volume}</b></span><span>Срок <b>{o.deadline}</b></span><span>Мест <b>{o.taken}/{o.seats}</b></span></div>
          </button>
          {open === o.id && (
            <div className="stack" style={{ marginTop: 8 }}>
              <div className="sm mute">Заказчик: {o.client}</div>
              <p className="prose" style={{ margin: 0 }}>{o.brief}</p>
              {o.rules.length > 0 && <ul className="rules">{o.rules.map((r) => <li key={r}>{r}</li>)}</ul>}
              {o.my_status === "active" ? <Report id={o.id} type={o.type} />
                : o.my_status === "requested" ? <span className="tag warn">Ждём подтверждения менеджера</span>
                : <button className="btn pri w" disabled={o.taken >= o.seats} onClick={() => take(o)}>{o.taken >= o.seats ? "Мест нет" : "Взять заказ"}</button>}
            </div>
          )}
        </section>
      ))}
    </div>
  );
}

function Report({ id, type }: { id: number; type: string }) {
  const inv = type === "inv";
  const [a, setA] = useState(""), [b, setB] = useState(""), [c, setC] = useState("");
  const toast = useToast();
  const send = async (e: React.FormEvent) => {
    e.preventDefault();
    const numbers: Record<string, number> = {};
    if (a) numbers[inv ? "invited" : "processed"] = Number(a);
    if (b) numbers[inv ? "sources" : "paid"] = Number(b);
    try { await api(`/api/orders/${id}/reports`, { method: "POST", body: { numbers, comment: c } }); toast("Отчёт отправлен"); setA(""); setB(""); setC(""); }
    catch (err) { toast((err as Error).message); }
  };
  return (
    <form className="stack" onSubmit={send}>
      <b>Отчёт за сегодня</b>
      <div className="kv">
        <div className="field"><label>{inv ? "Приглашено" : "Обработано"}</label><input className="inp mono" inputMode="numeric" value={a} onChange={(e) => setA(e.target.value.replace(/\D/g, ""))} /></div>
        <div className="field"><label>{inv ? "Чатов-источников" : "Оплат"}</label><input className="inp mono" inputMode="numeric" value={b} onChange={(e) => setB(e.target.value.replace(/\D/g, ""))} /></div>
      </div>
      <textarea className="inp" placeholder="Что сработало, что нет" value={c} onChange={(e) => setC(e.target.value)} />
      <button className="btn pri w">Отправить отчёт</button>
    </form>
  );
}
