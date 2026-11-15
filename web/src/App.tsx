import { useEffect, useState } from "react";
import { api, RANK, type Me } from "./api";
import { ErrorBox, Loading } from "./ui";
import Onboarding from "./screens/Onboarding";
import Academy from "./screens/Academy";
import LessonScreen from "./screens/Lesson";
import Orders from "./screens/Orders";
import Profile from "./screens/Profile";
import Admin from "./screens/Admin";

type Tab = "academy" | "orders" | "me" | "admin";
const TABS: [Tab, string, number][] = [["academy", "Академия", 1], ["orders", "Заказы", 2], ["me", "Профиль", 0], ["admin", "Админка", 4]];

export default function App() {
  const [me, setMe] = useState<Me | null>(null);
  const [err, setErr] = useState("");
  const [tab, setTab] = useState<Tab>("academy");
  const [lesson, setLesson] = useState<number | null>(null);
  const load = () => api<Me>("/api/me").then(setMe).catch((e) => setErr(e.message));
  useEffect(() => { load(); }, []);
  if (err) return <main className="main"><ErrorBox text={err} retry={() => { setErr(""); load(); }} /></main>;
  if (!me) return <main className="main"><Loading /></main>;
  const rank = RANK[me.user.role];
  if (rank === 0) return <main className="main"><header className="top"><h1>ELI_S team</h1></header><Onboarding me={me} reload={load} /></main>;
  const tabs = TABS.filter(([, , r]) => rank >= r);
  return (
    <>
      <main className="main">
        <header className="top"><h1>{lesson ? "Урок" : tabs.find((t) => t[0] === tab)?.[1]}</h1></header>
        {tab === "academy" && (lesson ? <LessonScreen id={lesson} back={() => setLesson(null)} /> : <Academy open={setLesson} />)}
        {tab === "orders" && <Orders />}
        {tab === "me" && <Profile me={me} />}
        {tab === "admin" && <Admin isAdmin={rank >= RANK.admin} />}
      </main>
      <nav className="tabbar">
        {tabs.map(([k, n]) => <button key={k} className={tab === k ? "on" : ""} onClick={() => { setTab(k); setLesson(null); }}>{n}</button>)}
      </nav>
    </>
  );
}
