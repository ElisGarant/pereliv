import { useEffect, useRef, useState } from "react";
import { api } from "../api";
import { haptic } from "../tg";
import { ErrorBox, fmtT, Loading, md, useToast } from "../ui";
import { createPlayer, type YTPlayer } from "../youtube";

type Q = { id: number; text: string; options: string[] };
type Lesson = {
  id: number; title: string; status: string; youtube_id: string | null; duration_sec: number; chapters: [number, string][];
  summary_md: string; task_text: string; materials: { title: string; url?: string }[]; xp: number;
  quiz: { pass_score: number; retake_minutes: number; questions: Q[]; best_score: number; attempts: number };
};
type Note = { id: number; t_sec: number | null; text: string };
type QRes = { score: number; total: number; passed: boolean; results: { correct: number; ok: boolean; explanation: string }[]; xp: number };

export default function LessonScreen({ id, back }: { id: number; back: () => void }) {
  const [l, setL] = useState<Lesson | null>(null);
  const [err, setErr] = useState("");
  const [tab, setTab] = useState<"sum" | "notes">("sum");
  const player = useRef<YTPlayer | null>(null);
  const box = useRef<HTMLDivElement>(null);
  useEffect(() => { api<Lesson>(`/api/academy/lessons/${id}`).then(setL).catch((e) => setErr(e.message)); }, [id]);
  useEffect(() => {
    if (!l?.youtube_id || !box.current) return;
    const el = document.createElement("div");
    box.current.replaceChildren(el);
    let p: YTPlayer | null = null;
    createPlayer(el, l.youtube_id).then((x) => { p = x; player.current = x; });
    return () => { p?.destroy(); player.current = null; };
  }, [l?.youtube_id]);
  if (err) return <ErrorBox text={err} retry={back} />;
  if (!l) return <Loading />;
  const seek = (s: number) => { player.current?.seekTo(s, true); player.current?.playVideo(); box.current?.scrollIntoView({ behavior: "smooth", block: "start" }); };
  const now = () => Math.floor(player.current?.getCurrentTime() ?? 0);
  return (
    <div className="stack">
      <button className="link" onClick={back}>← Курс</button>
      <div className="player" ref={box}>{!l.youtube_id && <div className="empty" style={{ color: "#fff" }}>Видео скоро добавим</div>}</div>
      <div><h2 className="disp" style={{ fontSize: "clamp(20px,4.5vw,26px)", lineHeight: 1.2 }}>{l.title}</h2>
        <div className="xs mute" style={{ marginTop: 6 }}>{fmtT(l.duration_sec)} · {l.chapters.length} глав · тест из {l.quiz.questions.length} · +{l.xp} XP</div></div>
      {l.chapters.length > 0 && (
        <section className="card" style={{ paddingBlock: 4 }}>
          <div className="list">{l.chapters.map(([s, n]) => <button key={s} className="chap" onClick={() => seek(s)}><span className="mono">{fmtT(s)}</span><b className="grow">{n}</b></button>)}</div>
        </section>
      )}
      <div className="seg">{([["sum", "Конспект"], ["notes", "Мои заметки"]] as const).map(([k, n]) => <button key={k} className={tab === k ? "on" : ""} onClick={() => setTab(k)}>{n}</button>)}</div>
      {tab === "sum" ? (
        <section className="card">
          <div className="prose" dangerouslySetInnerHTML={{ __html: md(l.summary_md) || "<p class='mute'>Конспект скоро появится</p>" }} />
          {l.materials.length > 0 && <div className="list" style={{ marginTop: 10 }}>{l.materials.map((m) => <a key={m.title} className="item" href={m.url} target="_blank" rel="noopener"><b>{m.title}</b></a>)}</div>}
          {l.task_text && <div className="task" style={{ marginTop: 14 }}><b>Задание к уроку</b><div>{l.task_text}</div></div>}
        </section>
      ) : <Notes lessonId={l.id} now={now} seek={seek} />}
      <Quiz l={l} />
    </div>
  );
}

function Notes({ lessonId, now, seek }: { lessonId: number; now: () => number; seek: (s: number) => void }) {
  const [list, setList] = useState<Note[]>([]);
  const [text, setText] = useState("");
  const [tc, setTc] = useState<number | null>(null);
  const toast = useToast();
  const load = () => api<Note[]>(`/api/academy/lessons/${lessonId}/notes`).then(setList);
  useEffect(() => { load(); }, [lessonId]);
  const save = async () => {
    if (!text.trim()) { toast("Сначала напиши заметку"); return; }
    await api(`/api/academy/lessons/${lessonId}/notes`, { method: "POST", body: { text, t_sec: tc } });
    setText(""); setTc(null); load(); toast("Заметка сохранена");
  };
  return (
    <section className="card">
      <div className="xs mute" style={{ marginBottom: 10 }}>Видно только тебе</div>
      <div className="notes-box">
        <textarea className="inp" value={text} onChange={(e) => setText(e.target.value)} placeholder="Мысль, вопрос, фраза, которую хочешь забрать" />
        <div className="row" style={{ marginTop: 8, gap: 8, flexWrap: "wrap" }}>
          <button className={`btn s ${tc !== null ? "pri" : ""}`} onClick={() => setTc(tc !== null ? null : now())}>{tc !== null ? `Тайм-код ${fmtT(tc)} ✓` : "Поставить тайм-код"}</button>
          <span className="grow" />
          <button className="btn s pri" onClick={save}>Сохранить</button>
        </div>
      </div>
      <div className="list" style={{ marginTop: 6 }}>
        {list.length ? list.map((n) => (
          <div className="nitem" key={n.id}>
            {n.t_sec !== null ? <button className="tc" onClick={() => seek(n.t_sec!)}>{fmtT(n.t_sec)}</button> : <span className="tc" style={{ opacity: 0.45 }}>––:––</span>}
            <div className="grow sm">{n.text}</div>
            <button className="ndel" aria-label="Удалить заметку" onClick={async () => { await api(`/api/academy/notes/${n.id}`, { method: "DELETE" }); load(); }}>✕</button>
          </div>
        )) : <div className="empty">Пока пусто. Поставь тайм-код и запиши мысль.</div>}
      </div>
    </section>
  );
}

function Quiz({ l }: { l: Lesson }) {
  const qs = l.quiz.questions;
  const [stage, setStage] = useState<"intro" | "q" | "res">("intro");
  const [i, setI] = useState(0);
  const [ans, setAns] = useState<number[]>([]);
  const [res, setRes] = useState<QRes | null>(null);
  const toast = useToast();
  if (!qs.length) return null;
  const finish = async (all: number[]) => {
    try { const r = await api<QRes>(`/api/academy/lessons/${l.id}/quiz`, { method: "POST", body: { answers: all } }); setRes(r); setStage("res"); haptic(r.passed ? "success" : "warning"); }
    catch (e) { toast((e as Error).message); setStage("intro"); }
  };
  if (stage === "intro") return (
    <section className="card">
      <span className="lbl">Тест по уроку</span>
      <h3 className="h3" style={{ marginTop: 4 }}>{l.status === "done" ? `Сдан · лучший результат ${l.quiz.best_score}/${qs.length}` : `${qs.length} вопросов · проходной ${l.quiz.pass_score}`}</h3>
      <p className="sm mute">Ответы проверяются после последнего вопроса. Если не сдашь, пересдача через {l.quiz.retake_minutes} мин.</p>
      <button className="btn pri" onClick={() => { setAns([]); setI(0); setStage("q"); }}>{l.status === "done" ? "Пройти ещё раз" : "Начать тест"}</button>
    </section>
  );
  if (stage === "res" && res) return (
    <section className="card stack">
      <div className="row" style={{ gap: 14 }}><div className="score" style={{ color: res.passed ? "var(--ok)" : "var(--bad)" }}>{res.score}/{res.total}</div>
        <div><h3 className="h3">{res.passed ? "Урок пройден" : "Пока не сдан"}</h3><div className="sm mute">{res.passed ? `+${res.xp} XP, следующий урок открыт` : `Нужно ${l.quiz.pass_score}. Пересдача через ${l.quiz.retake_minutes} мин.`}</div></div></div>
      {res.results.map((r, k) => !r.ok && (
        <div className="note" key={k}><span><b>{qs[k].text}</b><br />Верно: {qs[k].options[r.correct]}. {r.explanation}</span></div>
      ))}
    </section>
  );
  const q = qs[i];
  return (
    <section className="card stack">
      <div className="pips">{qs.map((_, k) => <i key={k} className={k < i ? "cur" : ""} />)}</div>
      <span className="lbl">Вопрос {i + 1} из {qs.length}</span>
      <h3 className="h3" style={{ fontSize: 17 }}>{q.text}</h3>
      <div style={{ display: "grid", gap: 8 }}>{q.options.map((o, k) => (
        <button key={k} className="opt" onClick={() => { const a = [...ans, k]; setAns(a); if (i < qs.length - 1) setI(i + 1); else finish(a); }}>
          <span className="k">{"АБВГДЕ"[k]}</span><span className="grow">{o}</span></button>
      ))}</div>
    </section>
  );
}
