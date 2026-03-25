from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file='.env', extra='ignore')

    app_name: str = 'Shopee Telegram SaaS'
    database_url: str = 'postgresql://postgres:postgres@db:5432/shopee_saas'
    jwt_secret: str = 'change-me'
    jwt_algorithm: str = 'HS256'
    jwt_exp_minutes: int = 60 * 24
    fernet_key: str = ''

    post_interval_seconds: int = 1200
    fetch_interval_seconds: int = 60
    error_retry_seconds: int = 30


settings = Settings()
