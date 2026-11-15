# Запуск на сервере

## Что нужно
| Что | Зачем |
|---|---|
| VPS: **2 ядра, 4 ГБ памяти**, Ubuntu, Docker | API, бот, Mini App. Под расшифровку голосовых бот берёт не больше 2 ядер и 2 ГБ |
| Домен (или поддомен) | Mini App работает только по https |
| Бот от @BotFather | токен и имя |
| Проект Supabase | база |

Если сервер на 2 ГБ памяти, поставь в `server/.env` `WHISPER_MODEL=base`: быстрее и легче, но хуже понимает речь.

## Шаги
1. **Домен:** A-запись `app.твой-домен` → IP сервера.
2. **База:** Supabase → SQL Editor → выполнить `supabase/migrations/0001_init.sql`.
3. **Код на сервер:** `git clone` репозитория.
4. **Настройки:**
   ```bash
   cp .env.example .env                  # DOMAIN=app.твой-домен
   cp server/.env.example server/.env    # BOT_TOKEN, BOT_USERNAME, DATABASE_URL, ADMIN_IDS
   ```
   В `DATABASE_URL` строка из Supabase, начало заменить на `postgresql+asyncpg://`.
   `ADMIN_IDS` — твой Telegram id (узнать у @userinfobot).
5. **Стартовые данные:** `docker compose run --rm api python -m app.seed`
6. **Запуск:** `docker compose up -d --build`. Caddy сам получит https-сертификат.
7. **Бот в @BotFather:**
   - `/setmenubutton` → выбрать бота → ссылка `https://app.твой-домен` → текст «Открыть»;
   - `/setdomain` → тот же домен (для входа через Telegram).
8. **Проверка:** открыть `https://app.твой-домен/health` → `{"ok":true}`, написать боту `/start`.

## Голосовые
- По умолчанию расшифровка своя: Whisper на сервере, без ключей.
- Модель скачивается при первом голосовом (около 500 МБ для `small`) и хранится в томе `models`.
- Голосовые обрабатываются строго по одному. Остальные ждут в очереди, бот пишет «передо мной ещё N».
- Длиннее 3 минут не расшифровываются (`VOICE_MAX_SEC`).
- Если 15 минут не было голосовых, модель выгружается из памяти.
- Замер на 2 ядрах, модель `small`: ~13 секунд на минуту речи.
- Выключить совсем: `TRANSCRIBE_ENGINE=off`.

## Обновление
```bash
git pull && docker compose up -d --build
```

## Логи
```bash
docker compose logs -f bot   # или api, web
```
