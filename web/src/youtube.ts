type YTPlayer = { getCurrentTime: () => number; seekTo: (s: number, allow: boolean) => void; playVideo: () => void; destroy: () => void };
type YTNs = { Player: new (el: HTMLElement, opts: unknown) => YTPlayer };
declare global {
  interface Window { YT?: YTNs; onYouTubeIframeAPIReady?: () => void }
}

let loading: Promise<YTNs> | null = null;

export function loadYT(): Promise<YTNs> {
  if (window.YT?.Player) return Promise.resolve(window.YT);
  if (!loading) {
    loading = new Promise((resolve) => {
      window.onYouTubeIframeAPIReady = () => resolve(window.YT!);
      const s = document.createElement("script");
      s.src = "https://www.youtube.com/iframe_api";
      document.head.appendChild(s);
    });
  }
  return loading;
}

/** Плеер урока: субтитры YouTube включены по умолчанию, видео с доступом «по ссылке». */
export async function createPlayer(el: HTMLElement, videoId: string): Promise<YTPlayer> {
  const YT = await loadYT();
  return new YT.Player(el, {
    videoId,
    host: "https://www.youtube-nocookie.com",
    playerVars: { cc_load_policy: 1, cc_lang_pref: "ru", hl: "ru", rel: 0, playsinline: 1, modestbranding: 1 },
  });
}
export type { YTPlayer };
