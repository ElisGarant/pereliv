import { useEffect, useState } from "react";
import { api } from "../api";
import { ErrorBox, Loading } from "../ui";

type L = { id: number; title: string; duration_sec: number; status: "done" | "current" | "locked" };
type M = { id: number; title: string; lessons: L[] };

export default function Academy({ open }: { open: (id: number) => void }) {
  const [mods, setMods] = useState<M[] | null>(null);
  const [err, setErr] = useState("");
  const load = () => api<M[]>("/api/academy/modules").then(setMods).catch((e) => setErr(e.message));
  useEffect(() => { load(); }, []);
  if (err) return <ErrorBox text={err} retry={load} />;
  if (!mods) return <Loading />;
  const all = mods.flatMap((m) => m.lessons), done = all.filter((l) => l.status === "done").length;
  const cur = all.find((l) => l.status === "current");
  return (
    <div className="stack">
      <section className="card hero">
        <span className="lbl">Академия</span>
        <h2 className="disp hero-t">Пройдено {done} из {all.length}</h2>
        <div className="bar a" style={{ margin: "10px 0 14px" }}><i style={{ width: `${all.length ? (done / all.length) * 100 : 0}%` }} /></div>
        {cur && <button className="btn pri" onClick={() => open(cur.id)}>Продолжить: {cur.title}</button>}
      </section>
      {mods.map((m) => (
        <section className="card" key={m.id}>
          <div className="btw"><h3 className="h3">{m.title}</h3><span className="mono xs mute">{m.lessons.filter((l) => l.status === "done").length}/{m.lessons.length}</span></div>
          <div className="list" style={{ marginTop: 6 }}>
            {m.lessons.map((l, k) => (
              <button key={l.id} className={`lesson ${l.status === "done" ? "d" : l.status === "current" ? "c" : "l"}`} disabled={l.status === "locked"} onClick={() => open(l.id)}>
                <span className="n">{l.status === "done" ? "✓" : k + 1}</span>
                <span className="grow"><b className="sm">{l.title}</b><span className="xs mute">{Math.max(1, Math.round(l.duration_sec / 60))} мин{l.status === "locked" ? " · откроется после предыдущего" : l.status === "current" ? " · текущий" : ""}</span></span>
              </button>
            ))}
          </div>
        </section>
      ))}
    </div>
  );
}
