from fastapi import Depends, FastAPI, HTTPException
from sqlalchemy.orm import Session

from auth import create_access_token, get_current_user, hash_password, verify_password
from database import Base, engine, get_db
from models import Bot, SentProduct, User
from schemas import (
    BotCreateRequest,
    BotResponse,
    BotUpdateRequest,
    LoginRequest,
    RegisterRequest,
    SentProductResponse,
    TokenResponse,
)
from security import encrypt_value

app = FastAPI(title='Shopee Telegram SaaS')
Base.metadata.create_all(bind=engine)


@app.get('/health')
def health():
    return {'status': 'ok'}


@app.post('/auth/register', response_model=TokenResponse)
def register(payload: RegisterRequest, db: Session = Depends(get_db)):
    existing = db.query(User).filter(User.email == payload.email).first()
    if existing:
        raise HTTPException(status_code=400, detail='Email já cadastrado')

    user = User(email=payload.email, password_hash=hash_password(payload.password))
    db.add(user)
    db.commit()
    db.refresh(user)
    return TokenResponse(access_token=create_access_token(user.id))


@app.post('/auth/login', response_model=TokenResponse)
def login(payload: LoginRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == payload.email).first()
    if not user or not verify_password(payload.password, user.password_hash):
        raise HTTPException(status_code=401, detail='Credenciais inválidas')
    return TokenResponse(access_token=create_access_token(user.id))


@app.get('/bots', response_model=list[BotResponse])
def list_bots(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return db.query(Bot).filter(Bot.user_id == current_user.id).order_by(Bot.id.desc()).all()


@app.post('/bots', response_model=BotResponse)
def create_bot(payload: BotCreateRequest, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    bot = Bot(
        user_id=current_user.id,
        shopee_app_id=payload.shopee_app_id,
        shopee_secret_enc=encrypt_value(payload.shopee_secret),
        telegram_token_enc=encrypt_value(payload.telegram_token),
        telegram_channel_id=payload.telegram_channel_id,
        status=payload.status,
        post_interval_seconds=payload.post_interval_seconds,
        fetch_interval_seconds=payload.fetch_interval_seconds,
        error_retry_seconds=payload.error_retry_seconds,
    )
    db.add(bot)
    db.commit()
    db.refresh(bot)
    return bot


@app.put('/bots/{bot_id}', response_model=BotResponse)
def update_bot(
    bot_id: int,
    payload: BotUpdateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    bot = db.query(Bot).filter(Bot.id == bot_id, Bot.user_id == current_user.id).first()
    if not bot:
        raise HTTPException(status_code=404, detail='Bot não encontrado')

    if payload.shopee_app_id is not None:
        bot.shopee_app_id = payload.shopee_app_id
    if payload.shopee_secret is not None:
        bot.shopee_secret_enc = encrypt_value(payload.shopee_secret)
    if payload.telegram_token is not None:
        bot.telegram_token_enc = encrypt_value(payload.telegram_token)
    if payload.telegram_channel_id is not None:
        bot.telegram_channel_id = payload.telegram_channel_id
    if payload.status is not None:
        bot.status = payload.status
    if payload.post_interval_seconds is not None:
        bot.post_interval_seconds = payload.post_interval_seconds
    if payload.fetch_interval_seconds is not None:
        bot.fetch_interval_seconds = payload.fetch_interval_seconds
    if payload.error_retry_seconds is not None:
        bot.error_retry_seconds = payload.error_retry_seconds

    db.commit()
    db.refresh(bot)
    return bot


@app.get('/bots/{bot_id}/sent-products', response_model=list[SentProductResponse])
def list_sent_products(bot_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    bot = db.query(Bot).filter(Bot.id == bot_id, Bot.user_id == current_user.id).first()
    if not bot:
        raise HTTPException(status_code=404, detail='Bot não encontrado')

    return (
        db.query(SentProduct)
        .filter(SentProduct.bot_id == bot_id)
        .order_by(SentProduct.created_at.desc())
        .limit(50)
        .all()
    )
