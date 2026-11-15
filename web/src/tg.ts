type TgWebApp = {
  initData: string;
  colorScheme?: "light" | "dark";
  ready: () => void;
  expand: () => void;
  HapticFeedback?: { notificationOccurred: (t: "success" | "error" | "warning") => void; selectionChanged: () => void };
  openTelegramLink?: (url: string) => void;
  onEvent?: (e: string, cb: () => void) => void;
};

export const tg: TgWebApp | undefined = (window as unknown as { Telegram?: { WebApp?: TgWebApp } }).Telegram?.WebApp;

export function initTelegram() {
  if (!tg) return;
  tg.ready();
  tg.expand();
  const apply = () => document.documentElement.setAttribute("data-theme", tg.colorScheme === "dark" ? "dark" : "light");
  if (tg.initData) {
    apply();
    tg.onEvent?.("themeChanged", apply);
  }
}

export const haptic = (t: "success" | "error" | "warning" = "success") => tg?.HapticFeedback?.notificationOccurred(t);
