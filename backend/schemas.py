from datetime import datetime

from pydantic import BaseModel, EmailStr


class RegisterRequest(BaseModel):
    email: EmailStr
    password: str


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = 'bearer'


class BotCreateRequest(BaseModel):
    shopee_app_id: str
    shopee_secret: str
    telegram_token: str
    telegram_channel_id: str
    status: bool = True
    post_interval_seconds: int = 1200
    fetch_interval_seconds: int = 60
    error_retry_seconds: int = 30


class BotUpdateRequest(BaseModel):
    shopee_app_id: str | None = None
    shopee_secret: str | None = None
    telegram_token: str | None = None
    telegram_channel_id: str | None = None
    status: bool | None = None
    post_interval_seconds: int | None = None
    fetch_interval_seconds: int | None = None
    error_retry_seconds: int | None = None


class BotResponse(BaseModel):
    id: int
    user_id: int
    shopee_app_id: str
    telegram_channel_id: str
    status: bool
    post_interval_seconds: int
    fetch_interval_seconds: int
    error_retry_seconds: int
    last_run_at: datetime | None
    created_at: datetime

    class Config:
        from_attributes = True


class SentProductResponse(BaseModel):
    id: int
    bot_id: int
    product_link: str
    created_at: datetime

    class Config:
        from_attributes = True
