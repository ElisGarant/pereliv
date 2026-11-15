from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    bot_token: str = ""
    bot_username: str = ""  # без @, нужен для реф-ссылки
    database_url: str = "sqlite+aiosqlite:///./dev.db"
    webapp_url: str = "http://localhost:5173"
    admin_ids: str = ""  # Telegram id через запятую
    dev_mode: bool = False  # разрешает заголовок X-Dev-User для локальной разработки
    initdata_ttl: int = 86400
    cors_origins: str = "http://localhost:5173"

    # Расшифровка голосовых: любой OpenAI-совместимый endpoint /audio/transcriptions
    transcribe_api_url: str = ""
    transcribe_api_key: str = ""
    transcribe_model: str = "whisper-1"

    @property
    def admin_id_set(self) -> set[int]:
        return {int(x) for x in self.admin_ids.replace(" ", "").split(",") if x}


@lru_cache
def get_settings() -> Settings:
    return Settings()
