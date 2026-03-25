from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from database import Base


class User(Base):
    __tablename__ = 'users'

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    plan: Mapped[str] = mapped_column(String(50), default='free', nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)

    bots: Mapped[list['Bot']] = relationship('Bot', back_populates='user')


class Bot(Base):
    __tablename__ = 'bots'

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey('users.id'), nullable=False, index=True)

    shopee_app_id: Mapped[str] = mapped_column(String(255), nullable=False)
    shopee_secret_enc: Mapped[str] = mapped_column(String(1024), nullable=False)
    telegram_token_enc: Mapped[str] = mapped_column(String(1024), nullable=False)
    telegram_channel_id: Mapped[str] = mapped_column(String(255), nullable=False)

    status: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    post_interval_seconds: Mapped[int] = mapped_column(Integer, default=1200, nullable=False)
    fetch_interval_seconds: Mapped[int] = mapped_column(Integer, default=60, nullable=False)
    error_retry_seconds: Mapped[int] = mapped_column(Integer, default=30, nullable=False)
    last_run_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)

    user: Mapped[User] = relationship('User', back_populates='bots')
    sent_products: Mapped[list['SentProduct']] = relationship('SentProduct', back_populates='bot')


class SentProduct(Base):
    __tablename__ = 'sent_products'
    __table_args__ = (UniqueConstraint('bot_id', 'product_link', name='uq_bot_product_link'),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    bot_id: Mapped[int] = mapped_column(ForeignKey('bots.id'), nullable=False, index=True)
    product_link: Mapped[str] = mapped_column(String(2048), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)

    bot: Mapped[Bot] = relationship('Bot', back_populates='sent_products')
