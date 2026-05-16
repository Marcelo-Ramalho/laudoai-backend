from pydantic_settings import BaseSettings
from supabase import create_client, Client
from functools import lru_cache


class Settings(BaseSettings):
    supabase_url: str
    supabase_key: str
    openai_api_key: str
    anthropic_api_key: str
    r2_account_id: str = ""
    r2_access_key: str = ""
    r2_secret_key: str = ""
    r2_bucket: str = "laudoai-arquivos"
    r2_public_url: str = ""
    stripe_secret_key: str = ""
    stripe_webhook_secret: str = ""
    app_env: str = "development"
    secret_key: str = "laudoai_secret_key"

    class Config:
        env_file = ".env"


@lru_cache()
def get_settings() -> Settings:
    return Settings()


def get_supabase() -> Client:
    settings = get_settings()
    return create_client(settings.supabase_url, settings.supabase_key)
