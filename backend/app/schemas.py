from datetime import datetime

from pydantic import BaseModel, EmailStr, Field


class UserCreate(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8)


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class Token(BaseModel):
    access_token: str
    token_type: str = 'bearer'


class BotCreate(BaseModel):
    name: str
    shopee_app_id: str
    shopee_secret: str
    telegram_token: str
    telegram_channel_id: str
    status: bool = False
    post_interval_seconds: int = 1200
    fetch_interval_seconds: int = 60
    error_retry_seconds: int = 30


class BotUpdate(BaseModel):
    name: str | None = None
    shopee_app_id: str | None = None
    shopee_secret: str | None = None
    telegram_token: str | None = None
    telegram_channel_id: str | None = None
    status: bool | None = None
    post_interval_seconds: int | None = None
    fetch_interval_seconds: int | None = None
    error_retry_seconds: int | None = None


class BotOut(BaseModel):
    id: int
    name: str
    shopee_app_id: str
    status: bool
    post_interval_seconds: int
    fetch_interval_seconds: int
    error_retry_seconds: int
    last_run_at: datetime | None
    created_at: datetime

    class Config:
        from_attributes = True


class SentProductOut(BaseModel):
    id: int
    bot_id: int
    product_link: str
    created_at: datetime

    class Config:
        from_attributes = True
