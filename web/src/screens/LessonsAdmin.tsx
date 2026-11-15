import { useEffect, useState } from "react";
import { api, DIRS } from "../api";
import { ErrorBox, fmtT, Loading, md, useToast } from "../ui";

type ML = { id: number; title: string; published: boolean; position: number };
type Mod = { id: number; title: string; direction: string | null; is_free: boolean; lessons: ML[] };
type Q = { text: string; options: string[]; correct: number; explanation: string };
type Draft = { id?: number; module_id: number; title: string; position: number; youtube: string; duration_sec: number; chapters: [number, string][];
  summary_md: string; task_text: string; materials: { title: string; url: string }[]; pass_score: number; retake_minutes: number; xp: number; published: boolean; questions: Q[] };

const ytId = (s: string) => (s.trim().match(/^[\w-]{11}$/) ? s.trim() : s.match(/(?:youtu\.be\/|[?&]v=|\/embed\/|\/shorts\/|\/live\/)([\w-]{11})/)?.[1] ?? null);
const toSec = (t: string) => t.split(":").reduce((a, x) => a * 60 + Number(x), 0);
const chText = (c: [number, string][]) => c.map(([s, n]) => `${fmtT(s)} ${n}`).join("\n");
const parseCh = (t: string): [number, string][] => t.split("\n").map((l) => l.trim().match(/^(\d{1,2}:\d{2}(?::\d{2})?)\s*[-–—]?\s*(.+)$/)).filter(Boolean).map((m) => [toSec(m![1]), m![2]] as [number, string]);

export default function LessonsAdmin() {
  const [mods, setMods] = useState<Mod[] | null>(null);
  const [err, setErr] = useState("");
  const [edit, setEdit] = useState<Draft | null>(null);
  const [newMod, setNewMod] = useState("");
  const toast = useToast();
  const load = () => api<Mod[]>("/api/admin/modules").then(setMods).catch((e) => setErr(e.message));
  useEffect(() => { load(); }, []);
  if (err) return <ErrorBox text={err} retry={load} />;
  if (!mods) return <Loading />;
  if (edit) return <Editor draft={edit} mods={mods} close={() => { setEdit(null); load(); }} />;
  const open = async (id: number) => setEdit({ ...(await api<Draft>(`/api/admin/lessons/${id}`)), id });
  const add = (m: Mod) => setEdit({ module_id: m.id, title: "", position: m.lessons.length, youtube: "", duration_sec: 0, chapters: [], summary_md: "", task_text: "",
    materials: [], pass_score: 1, retake_minutes: 60, xp: 100, published: false, questions: [] });
  const addModule = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!newMod.trim()) return;
    await api("/api/admin/modules", { method: "POST", body: { title: newMod.trim(), position: mods.length } }); setNewMod(""); toast("Модуль добавлен"); load();
  };
  return (
    <div className="stack">
      {mods.map((m) => (
        <section className="card" key={m.id}>
          <div className="btw"><h3 className="h3">{m.title}</h3><span className="xs mute">{m.is_free ? "бесплатные" : m.direction ? DIRS[m.direction] : "для всех"}</span></div>
          <div className="list" style={{ marginTop: 6 }}>
            {m.lessons.map((l) => (
              <button className="item" key={l.id} onClick={() => open(l.id)}>
                <span className={`tag ${l.published ? "ok" : "warn"}`}>{l.published ? "опубликован" : "черновик"}</span><b className="grow sm">{l.title}</b>
              </button>
            ))}
            <button className="link" style={{ padding: "10px 0" }} onClick={() => add(m)}>+ Урок</button>
          </div>
        </section>
      ))}
      <form className="row" onSubmit={addModule}><input className="inp" value={newMod} onChange={(e) => setNewMod(e.target.value)} placeholder="Новый модуль, например «Звонки»" /><button className="btn" disabled={!newMod.trim()}>Добавить</button></form>
    </div>
  );
}

function Editor({ draft, mods, close }: { draft: Draft; mods: Mod[]; close: () => void }) {
  const [d, setD] = useState<Draft>(draft);
  const [chs, setChs] = useState(chText(draft.chapters));
  const [prev, setPrev] = useState(false);
  const [busy, setBusy] = useState(false);
  const toast = useToast();
  const set = <K extends keyof Draft>(k: K, v: Draft[K]) => setD({ ...d, [k]: v });
  const setQ = (i: number, q: Partial<Q>) => set("questions", d.questions.map((x, k) => (k === i ? { ...x, ...q } : x)));
  const yt = ytId(d.youtube);
  const chapters = parseCh(chs);
  const checks: [string, boolean][] = [["Видео по ссылке", !!yt], ["Хотя бы 2 главы", chapters.length >= 2], ["Конспект", d.summary_md.trim().length >= 40],
    ["Тест от 3 вопросов", d.questions.length >= 3 && d.questions.every((q) => q.text.trim() && q.options.filter((o) => o.trim()).length >= 2)]];
  const save = async (publish: boolean) => {
    setBusy(true);
    const body = { ...d, chapters, published: publish, pass_score: Math.min(d.pass_score, Math.max(d.questions.length, 1)) };
    try {
      if (d.id) await api(`/api/admin/lessons/${d.id}`, { method: "PUT", body });
      else await api("/api/admin/lessons", { method: "POST", body });
      toast(publish ? "Урок опубликован" : "Черновик сохранён"); close();
    } catch (e) { toast((e as Error).message); } finally { setBusy(false); }
  };
  return (
    <div className="stack">
      <button className="link" onClick={close}>← Все уроки</button>
      <section className="card stack">
        <input className="inp title-inp" value={d.title} onChange={(e) => set("title", e.target.value)} placeholder="Название урока" />
        <div className="field"><label>Модуль</label><select className="inp" value={d.module_id} onChange={(e) => set("module_id", Number(e.target.value))}>{mods.map((m) => <option key={m.id} value={m.id}>{m.title}</option>)}</select></div>
      </section>
      <section className="card stack">
        <h3 className="h3">Видео</h3>
        <input className="inp" value={d.youtube} onChange={(e) => set("youtube", e.target.value)} placeholder="https://youtu.be/… или https://www.youtube.com/watch?v=…" />
        <div className="xs" style={{ color: !d.youtube ? "var(--mute)" : yt ? "var(--ok)" : "var(--bad)" }}>{!d.youtube ? "Доступ в YouTube: «По ссылке»" : yt ? `Видео найдено · ID ${yt}` : "Не похоже на ссылку YouTube"}</div>
        <div className="field"><label>Длительность, сек</label><input className="inp mono" inputMode="numeric" value={d.duration_sec || ""} onChange={(e) => set("duration_sec", Number(e.target.value.replace(/\D/g, "")) || 0)} /></div>
        <div className="field"><label>Главы · по строке «00:48 Название» (можно вставить из описания YouTube)</label><textarea className="inp mono" value={chs} onChange={(e) => setChs(e.target.value)} placeholder={"00:00 Вступление\n00:48 Главная ошибка"} /></div>
        <div className="xs mute">Распознано глав: {chapters.length}</div>
      </section>
      <section className="card stack">
        <div className="btw"><h3 className="h3">Конспект</h3><div className="seg"><button className={prev ? "" : "on"} onClick={() => setPrev(false)}>Текст</button><button className={prev ? "on" : ""} onClick={() => setPrev(true)}>Как увидит ученик</button></div></div>
        {prev ? <div className="prose" dangerouslySetInnerHTML={{ __html: md(d.summary_md) }} /> : <>
          <textarea className="inp mono" style={{ minHeight: 200 }} value={d.summary_md} onChange={(e) => set("summary_md", e.target.value)} />
          <div className="xs mute">## заголовок · **жирный** · - пункт · &gt; фраза-скрипт · [03:25] тайм-код</div></>}
        <div className="field"><label>Задание к уроку</label><textarea className="inp" value={d.task_text} onChange={(e) => set("task_text", e.target.value)} /></div>
      </section>
      <section className="card stack">
        <div className="btw"><h3 className="h3">Тест · {d.questions.length}</h3></div>
        <div className="kv">
          <div className="field"><label>Проходной балл</label><input className="inp mono" inputMode="numeric" value={d.pass_score} onChange={(e) => set("pass_score", Number(e.target.value.replace(/\D/g, "")) || 1)} /></div>
          <div className="field"><label>Пересдача, мин</label><input className="inp mono" inputMode="numeric" value={d.retake_minutes} onChange={(e) => set("retake_minutes", Number(e.target.value.replace(/\D/g, "")) || 0)} /></div>
          <div className="field"><label>XP</label><input className="inp mono" inputMode="numeric" value={d.xp} onChange={(e) => set("xp", Number(e.target.value.replace(/\D/g, "")) || 0)} /></div>
        </div>
        {d.questions.map((q, i) => (
          <div className="qcard" key={i}>
            <div className="btw"><span className="lbl">Вопрос {i + 1}</span><button className="ndel" aria-label="Удалить вопрос" onClick={() => set("questions", d.questions.filter((_, k) => k !== i))}>✕</button></div>
            <textarea className="inp" style={{ minHeight: 56 }} value={q.text} onChange={(e) => setQ(i, { text: e.target.value })} placeholder="Текст вопроса" />
            {q.options.map((o, j) => (
              <div className="optrow" key={j}>
                <input type="radio" name={`q${i}`} checked={q.correct === j} onChange={() => setQ(i, { correct: j })} aria-label="Верный ответ" />
                <input className={`inp ${q.correct === j ? "right" : ""}`} value={o} onChange={(e) => setQ(i, { options: q.options.map((x, k) => (k === j ? e.target.value : x)) })} placeholder={`Вариант ${j + 1}`} />
                <button className="ndel" disabled={q.options.length <= 2} aria-label="Удалить вариант" onClick={() => setQ(i, { options: q.options.filter((_, k) => k !== j), correct: q.correct === j ? 0 : q.correct > j ? q.correct - 1 : q.correct })}>✕</button>
              </div>
            ))}
            {q.options.length < 6 && <button className="link" onClick={() => setQ(i, { options: [...q.options, ""] })}>+ Вариант</button>}
            <input className="inp" value={q.explanation} onChange={(e) => setQ(i, { explanation: e.target.value })} placeholder="Объяснение после ответа" />
          </div>
        ))}
        <button className="btn" onClick={() => set("questions", [...d.questions, { text: "", options: ["", ""], correct: 0, explanation: "" }])}>+ Вопрос</button>
      </section>
      <section className="card stack">
        <h3 className="h3">Готовность</h3>
        {checks.map(([n, ok]) => <div className="row sm" key={n}><span className={`tag ${ok ? "ok" : ""}`}>{ok ? "готово" : "нет"}</span>{n}</div>)}
        <div className="row" style={{ gap: 8, flexWrap: "wrap" }}>
          <button className="btn" disabled={busy || !d.title.trim()} onClick={() => save(false)}>Сохранить черновик</button>
          <button className="btn pri" disabled={busy || !d.title.trim() || checks.some(([, ok]) => !ok)} onClick={() => save(true)}>{d.published ? "Сохранить и оставить опубликованным" : "Опубликовать"}</button>
        </div>
      </section>
    </div>
  );
}
