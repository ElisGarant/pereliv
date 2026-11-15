import { useEffect, useState } from "react";
import { api, DIRS, type Me } from "../api";
import { haptic } from "../tg";
import { ErrorBox, Loading, useToast } from "../ui";

type Free = { id: number; title: string; youtube_id: string | null; duration_sec: number; seen: boolean };
type Q = { text: string; options: string[]; kind: "fit" | "task" };
type Res = { scores: Record<string, number>; top: string; smart: number; fit_total: number };
const STEPS = ["Знакомство", "Уроки", "Тест", "Заявка"];
const DESC: Record<string, string> = {
  inv: "Находишь людей в тематических чатах и приводишь их в каналы заказчиков",
  msg: "Переписываешься с клиентами в Telegram и доводишь до оплаты",
  call: "Звонишь тёплым клиентам и записываешь их на услуги",
  lead: "Ищешь и проверяешь контакты компаний для заказчиков",
};

export default function Onboarding({ me, reload }: { me: Me; reload: () => void }) {
  const app = me.application;
  const [step, setStep] = useState(0);
  const [res, setRes] = useState<Res | null>(null);
  if (app && app.status !== "rejected") return <Status me={me} reload={reload} />;
  return (
    <div className="ob">
      <div className="obsteps">{STEPS.map((n, k) => <div key={n} className={k < step ? "d" : k === step ? "c" : ""}><i /><span>{n}</span></div>)}</div>
      {step === 0 && <Welcome name={me.user.first_name} next={() => setStep(1)} rejected={app?.status === "rejected"} />}
      {step === 1 && <FreeLessons next={() => setStep(2)} />}
      {step === 2 && <RoleTest onDone={(r) => { setRes(r); setStep(3); }} />}
      {step === 3 && res && <ApplicationForm res={res} done={reload} />}
    </div>
  );
}

function Welcome({ name, next, rejected }: { name: string; next: () => void; rejected: boolean }) {
  return (
    <section className="card hero">
      <span className="lbl">ELI_S team</span>
      <h2 className="disp hero-t">{name ? `${name}, учись продавать и сразу зарабатывай` : "Учись продавать и сразу зарабатывай"}</h2>
      {rejected && <p className="sm" style={{ color: "var(--warn)" }}>Прошлая заявка не прошла. Можно попробовать снова.</p>}
      <div className="list" style={{ marginTop: 12 }}>
        {[["Учишься бесплатно", "короткие уроки по 2–5 минут, тесты и разборы"], ["Берёшь заказы", "инвайтинг, переписка, звонки, лидген"], ["Получаешь за результат", "выплаты раз в неделю, всё прозрачно"]].map(([a, b], k) => (
          <div className="item" key={a}><span className="mono xs" style={{ width: 18, color: "var(--acc)" }}>0{k + 1}</span><div className="grow"><b>{a}</b><span className="xs mute">{b}</span></div></div>
        ))}
      </div>
      <button className="btn pri w" style={{ marginTop: 12 }} onClick={next}>Начать · 10 минут</button>
    </section>
  );
}

function FreeLessons({ next }: { next: () => void }) {
  const [list, setList] = useState<Free[] | null>(null);
  const [err, setErr] = useState("");
  const [open, setOpen] = useState<Free | null>(null);
  const load = () => api<Free[]>("/api/onboarding/free-lessons").then(setList).catch((e) => setErr(e.message));
  useEffect(() => { load(); }, []);
  if (err) return <ErrorBox text={err} retry={load} />;
  if (!list) return <Loading />;
  const seen = list.filter((l) => l.seen).length, need = Math.min(2, list.length);
  const markSeen = async (l: Free) => { await api(`/api/onboarding/free-lessons/${l.id}/seen`, { method: "POST" }); setOpen(null); load(); };
  return (
    <>
      <div><h2 className="disp" style={{ fontSize: 24 }}>Короткие уроки</h2><p className="sm mute" style={{ margin: "6px 0 0" }}>Посмотри хотя бы {need}, чтобы понять, чем здесь занимаются.</p></div>
      {open && (
        <section className="card stack">
          <b>{open.title}</b>
          {open.youtube_id ? <div className="player"><iframe src={`https://www.youtube-nocookie.com/embed/${open.youtube_id}?cc_load_policy=1&cc_lang_pref=ru&hl=ru&rel=0`} title={open.title} allow="autoplay; encrypted-media; fullscreen" allowFullScreen /></div>
            : <div className="empty">Видео скоро добавим</div>}
          <button className="btn pri w" onClick={() => markSeen(open)}>Посмотрел</button>
        </section>
      )}
      <section className="card" style={{ paddingBlock: 4 }}>
        <div className="list">{list.map((l, k) => (
          <button key={l.id} className={`lesson ${l.seen ? "d" : ""}`} onClick={() => setOpen(l)}>
            <span className="n">{l.seen ? "✓" : k + 1}</span>
            <span className="grow"><b className="sm">{l.title}</b><span className="xs mute">{Math.max(1, Math.round(l.duration_sec / 60))} мин{l.seen ? " · просмотрено" : ""}</span></span>
          </button>
        ))}</div>
      </section>
      <button className="btn pri w" disabled={seen < need} onClick={next}>{seen < need ? `Посмотри ещё ${need - seen}` : "Дальше: тест на роль"}</button>
    </>
  );
}

function RoleTest({ onDone }: { onDone: (r: Res) => void }) {
  const [qs, setQs] = useState<Q[] | null>(null);
  const [i, setI] = useState(0);
  const [ans, setAns] = useState<number[]>([]);
  const [res, setRes] = useState<Res | null>(null);
  const toast = useToast();
  useEffect(() => { api<{ questions: Q[] }>("/api/onboarding/role-test").then((d) => setQs(d.questions)); }, []);
  if (!qs) return <Loading />;
  if (res) return (
    <>
      <section className="card hero">
        <span className="lbl">Результат теста</span>
        <h2 className="disp hero-t">Тебе подходит: {DIRS[res.top]}</h2>
        <p className="sm mute">{DESC[res.top]}.</p>
        <div style={{ display: "grid", gap: 10, marginTop: 14 }}>
          {Object.keys(DIRS).sort((a, b) => res.scores[b] - res.scores[a]).map((d) => (
            <div key={d}><div className="btw sm"><span>{DIRS[d]}</span><span className="mono xs">{Math.round(res.scores[d] / res.fit_total * 100)}%</span></div>
              <div className={`bar ${d === res.top ? "a" : ""}`} style={{ marginTop: 6 }}><i style={{ width: `${res.scores[d] / res.fit_total * 100}%` }} /></div></div>
          ))}
        </div>
        <span className={`tag ${res.smart === 2 ? "ok" : "warn"}`} style={{ marginTop: 14 }}>Задачи на сообразительность: {res.smart}/2</span>
      </section>
      <button className="btn pri w" onClick={() => onDone(res)}>Дальше: анкета</button>
    </>
  );
  const q = qs[i];
  const pick = async (k: number) => {
    const next = [...ans.slice(0, i), k];
    setAns(next);
    haptic("success");
    if (i < qs.length - 1) { setTimeout(() => setI(i + 1), 180); return; }
    try { setRes(await api<Res>("/api/onboarding/role-test", { method: "POST", body: { answers: next } })); }
    catch (e) { toast((e as Error).message); }
  };
  return (
    <>
      <div className="btw"><span className="lbl">Вопрос {i + 1} из {qs.length}</span>{i > 0 && <button className="link" onClick={() => setI(i - 1)}>← Назад</button>}</div>
      <div className="pips">{qs.map((_, k) => <i key={k} className={k < i ? "ok" : k === i ? "cur" : ""} />)}</div>
      <h2 className="disp" style={{ fontSize: "clamp(19px,4.6vw,24px)", lineHeight: 1.25 }}>{q.text}</h2>
      <div style={{ display: "grid", gap: 8 }}>
        {q.options.map((o, k) => <button key={k} className={`opt ${ans[i] === k ? "ok" : ""}`} onClick={() => pick(k)}><span className="k">{"АБВГ"[k]}</span><span className="grow">{o}</span></button>)}
      </div>
      <div className="xs mute">{q.kind === "task" ? "Это мини-задача: тут есть верный ответ." : "Верных ответов нет, выбирай как есть."}</div>
    </>
  );
}

function Chips({ list, value, set }: { list: [string, string][]; value: string; set: (v: string) => void }) {
  return <div className="chips">{list.map(([v, n]) => <button type="button" key={v} className={value === v ? "on" : ""} onClick={() => set(v)}>{n}</button>)}</div>;
}

function ApplicationForm({ res, done }: { res: Res; done: () => void }) {
  const [f, setF] = useState({ direction: res.top, age_group: "25–34", hours: "4–6 часов", experience: "Немного", goal: "Заработок", about: "", adult_and_rules: false });
  const [busy, setBusy] = useState(false);
  const toast = useToast();
  const set = (k: keyof typeof f) => (v: string | boolean) => setF({ ...f, [k]: v });
  const opts = (xs: string[]) => xs.map((x) => [x, x] as [string, string]);
  const submit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!f.adult_and_rules) { toast("Подтверди, что тебе есть 18"); return; }
    setBusy(true);
    try { await api("/api/onboarding/application", { method: "POST", body: f }); haptic("success"); done(); }
    catch (err) { toast((err as Error).message); haptic("error"); }
    finally { setBusy(false); }
  };
  return (
    <>
      <div><h2 className="disp" style={{ fontSize: 24 }}>Анкета</h2><p className="sm mute" style={{ margin: "6px 0 0" }}>2 минуты. Имя и Telegram мы уже знаем.</p></div>
      <form className="card stack" onSubmit={submit}>
        <div className="field"><label>Направление</label><Chips list={Object.entries(DIRS).map(([k, n]) => [k, k === res.top ? `${n} · по тесту` : n])} value={f.direction} set={set("direction")} /></div>
        <div className="field"><label>Возраст</label><Chips list={opts(["18–24", "25–34", "35+"])} value={f.age_group} set={set("age_group")} /></div>
        <div className="field"><label>Сколько часов в день готов работать</label><Chips list={opts(["2–3 часа", "4–6 часов", "6+ часов"])} value={f.hours} set={set("hours")} /></div>
        <div className="field"><label>Опыт с клиентами</label><Chips list={opts(["Нет", "Немного", "Есть"])} value={f.experience} set={set("experience")} /></div>
        <div className="field"><label>Зачем тебе это</label><Chips list={opts(["Заработок", "Навык", "И то и другое"])} value={f.goal} set={set("goal")} /></div>
        <div className="field"><label htmlFor="about">Пара слов о себе · необязательно</label><textarea id="about" className="inp" value={f.about} onChange={(e) => set("about")(e.target.value)} placeholder="Например: свободен с 18:00" /></div>
        <label className="row sm" style={{ gap: 10 }}><input type="checkbox" checked={f.adult_and_rules} onChange={(e) => set("adult_and_rules")(e.target.checked)} /> Мне есть 18 лет, согласен с правилами команды</label>
        <button className="btn pri w" disabled={busy}>{busy ? "Отправляю…" : "Отправить заявку"}</button>
      </form>
    </>
  );
}

function Status({ me, reload }: { me: Me; reload: () => void }) {
  const a = me.application!;
  const T = {
    pending: ["Заявка на рассмотрении", "Обычно отвечаем за 1–2 дня. Ответ придёт в бот.", "warn"],
    waitlist: ["Лист ожидания", "Сейчас мест нет. Напишем, как только освободится.", "acc"],
    approved: ["Ты в команде", "Академия открыта.", "ok"],
    rejected: ["Пока не подходит", "Через 30 дней можно подать снова.", "bad"],
  }[a.status];
  return (
    <div className="ob">
      <section className="card hero">
        <span className={`tag ${T[2]}`}>{T[0]}</span>
        <h2 className="disp hero-t">{a.status === "pending" ? "Заявка отправлена" : T[0]}</h2>
        <p className="sm mute">{T[1]}</p>
        <p className="sm">Направление: <b>{DIRS[a.direction]}</b></p>
        <button className="btn s" onClick={reload}>Обновить статус</button>
      </section>
    </div>
  );
}
