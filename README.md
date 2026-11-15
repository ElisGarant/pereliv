# ELI_S team

Telegram-бот и Mini App агентства: вход новичка, Академия с видеоуроками и тестами, заказы, админка.

| Папка | Что там |
|---|---|
| `design/index.html` | кликабельный прототип всех экранов, включая вторую очередь |
| `docs/MVP_SCOPE.md` | что входит в первую версию, а что нет |
| `docs/TESTING.md` | как проверить прототип на команде |
| `server/app` | API на FastAPI |
| `server/bot` | бот на aiogram 3 (общая база с API) |
| `supabase/migrations` | схема базы для Supabase |
| `web` | Mini App на React + Vite |

## Запуск локально

```bash
# 1. Сервер
cd server
python3 -m venv .venv && .venv/bin/pip install -r requirements-dev.txt
cp .env.example .env            # для локальной проверки поставь DEV_MODE=true, ADMIN_IDS=1
.venv/bin/python -m app.seed    # стартовые уроки и заказы
.venv/bin/uvicorn app.main:app --reload --port 8000

# 2. Mini App (в другом терминале)
cd web
npm install
VITE_DEV_USER=500 npm run dev   # откроется как новичок с id 500; VITE_DEV_USER=1 — как админ

# 3. Бот (нужен BOT_TOKEN в server/.env)
cd server && .venv/bin/python -m bot.main
```

Тесты сервера: `cd server && .venv/bin/python -m pytest`.

## Supabase

1. Создай проект, открой SQL Editor и выполни `supabase/migrations/0001_init.sql`.
   На всех таблицах включён RLS без политик: напрямую к ним не попасть, работает только сервер.
2. Строку подключения из Project Settings → Database вставь в `DATABASE_URL`, заменив `postgresql://` на `postgresql+asyncpg://`.
3. После изменения моделей пересобери схему: `cd server && .venv/bin/python -m app.schema > ../supabase/migrations/0002_....sql` (для новых таблиц пиши ALTER вручную).

## Голосовые

Бот сам переводит голосовые в текст на сервере (Whisper), без внешних ключей. Голосовые идут по одному, не больше 2 ядер, модель выгружается после простоя.
Для локальной проверки: `.venv/bin/pip install -r requirements-voice.txt`. Подробности и настройки в `docs/DEPLOY.md`.

## Запуск на сервере

`docs/DEPLOY.md`: Docker, автоматический https, настройка бота в @BotFather.

## Видео уроков

Видео загружается в YouTube с доступом **«По ссылке»** («Ограниченный доступ» в приложении не откроется). Субтитры берутся из YouTube автоматически.

## Безопасность

- Вход только через Telegram `initData`, подпись проверяется на каждом запросе (`server/app/telegram_auth.py`).
- Права проверяются на сервере (`require("student")`, `require("admin")` и т.д.).
- Ответы на тесты не уходят в приложение, проверка на сервере.
- Решения по заявкам и смена ролей пишутся в `audit_log`.
