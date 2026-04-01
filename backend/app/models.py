from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .database import Base


class User(Base):
    __tablename__ = 'users'

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    plan: Mapped[str] = mapped_column(String(50), default='free', nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)

    bots: Mapped[list['Bot']] = relationship(back_populates='user', cascade='all, delete-orphan')


class Bot(Base):
    __tablename__ = 'bots'

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    name: Mapped[str] = mapped_column(String(120), nullable=False)

    shopee_app_id: Mapped[str] = mapped_column(String(120), nullable=False)
    shopee_secret_encrypted: Mapped[str] = mapped_column(Text, nullable=False)
    telegram_token_encrypted: Mapped[str] = mapped_column(Text, nullable=False)
    telegram_channel_id_encrypted: Mapped[str] = mapped_column(Text, nullable=False)

    status: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    post_interval_seconds: Mapped[int] = mapped_column(Integer, default=1200, nullable=False)
    fetch_interval_seconds: Mapped[int] = mapped_column(Integer, default=60, nullable=False)
    error_retry_seconds: Mapped[int] = mapped_column(Integer, default=30, nullable=False)
    last_run_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)

    user: Mapped[User] = relationship(back_populates='bots')
    sent_products: Mapped[list['SentProduct']] = relationship(back_populates='bot', cascade='all, delete-orphan')


class SentProduct(Base):
    __tablename__ = 'sent_products'
    __table_args__ = (UniqueConstraint('bot_id', 'product_link', name='uq_bot_product_link'),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    bot_id: Mapped[int] = mapped_column(ForeignKey('bots.id', ondelete='CASCADE'), nullable=False)
    product_link: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)

    bot: Mapped[Bot] = relationship(back_populates='sent_products')
