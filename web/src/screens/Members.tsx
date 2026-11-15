import { useEffect, useState } from "react";
import { api, type User } from "../api";
import { ErrorBox, Loading, useToast } from "../ui";

type M = { id: number; user: User; order: { id: number; title: string } };

export default function Members() {
  const [list, setList] = useState<M[] | null>(null);
  const [err, setErr] = useState("");
  const toast = useToast();
  const load = () => api<M[]>("/api/admin/order-members").then(setList).catch((e) => setErr(e.message));
  useEffect(() => { load(); }, []);
  if (err) return <ErrorBox text={err} retry={load} />;
  if (!list) return <Loading />;
  if (!list.length) return <div className="card empty">Новых откликов нет</div>;
  const confirm = async (m: M) => {
    try { await api(`/api/admin/order-members/${m.id}/confirm`, { method: "POST" }); toast(`${m.user.first_name} в заказе, бот сообщил`); load(); }
    catch (e) { toast((e as Error).message); }
  };
  return (
    <section className="card" style={{ paddingBlock: 4 }}>
      <div className="list">{list.map((m) => (
        <div className="item" key={m.id}>
          <div className="ava">{m.user.first_name[0]}</div>
          <div className="grow"><b>{m.user.first_name} {m.user.last_name ?? ""}</b><span className="xs mute">{m.order.title}</span></div>
          <button className="btn s pri" onClick={() => confirm(m)}>Подтвердить</button>
        </div>
      ))}</div>
    </section>
  );
}
