from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file='.env', env_file_encoding='utf-8')

    app_name: str = 'Shopee SaaS'
    database_url: str = 'postgresql://postgres:postgres@db:5432/shopee_saas'
    jwt_secret: str = 'change-me'
    jwt_algorithm: str = 'HS256'
    access_token_expire_minutes: int = 60 * 24
    encryption_key: str = 'change-with-fernet-key'

    shopee_api_url: str = 'https://open-api.affiliate.shopee.com.br/graphql'
    post_interval_seconds: int = 1200
    fetch_interval_seconds: int = 60
    error_retry_seconds: int = 30


settings = Settings()
