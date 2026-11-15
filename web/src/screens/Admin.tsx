import { useState } from "react";
import Applications from "./Applications";
import LessonsAdmin from "./LessonsAdmin";
import Members from "./Members";

export default function Admin({ isAdmin }: { isAdmin: boolean }) {
  const [tab, setTab] = useState<"apps" | "lessons" | "members">("apps");
  const tabs: [typeof tab, string][] = [["apps", "Заявки"], ["members", "Отклики"], ...(isAdmin ? [["lessons", "Уроки"]] as [typeof tab, string][] : [])];
  return (
    <div className="stack">
      <div className="seg">{tabs.map(([k, n]) => <button key={k} className={tab === k ? "on" : ""} onClick={() => setTab(k)}>{n}</button>)}</div>
      {tab === "apps" && <Applications />}
      {tab === "members" && <Members />}
      {tab === "lessons" && <LessonsAdmin />}
    </div>
  );
}
