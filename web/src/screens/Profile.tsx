import { DIRS, type Me } from "../api";
import { useToast } from "../ui";

const ROLE: Record<string, string> = { guest: "Гость", student: "Ученик", member: "Участник команды", mentor: "Наставник", manager: "Менеджер", admin: "Админ" };

export default function Profile({ me }: { me: Me }) {
  const u = me.user;
  const toast = useToast();
  const copy = async () => {
    if (!me.ref_link) return;
    try { await navigator.clipboard.writeText(me.ref_link); toast("Ссылка скопирована"); } catch { toast(me.ref_link); }
  };
  return (
    <div className="stack">
      <section className="card">
        <div className="row"><div className="ava l me">{(u.first_name[0] ?? "?") + (u.last_name?.[0] ?? "")}</div>
          <div className="grow"><h2 className="disp" style={{ fontSize: 21 }}>{u.first_name} {u.last_name ?? ""}</h2>
            <div className="sm mute">{u.ref_code} · {ROLE[u.role]}{u.direction ? ` · ${DIRS[u.direction]}` : ""}</div></div></div>
      </section>
      {me.ref_link && (
        <section className="card">
          <h3 className="h3">Реферальная ссылка</h3>
          <p className="sm mute">Приведи ученика или заказчика и получай процент.</p>
          <div className="ref"><code>{me.ref_link}</code><button className="btn s pri" onClick={copy}>Копировать</button></div>
        </section>
      )}
      <section className="card"><h3 className="h3">Связь</h3><p className="sm mute">Голосовые можно присылать боту: он переведёт их в текст. Писать админу в личку можно напрямую.</p></section>
    </div>
  );
}
