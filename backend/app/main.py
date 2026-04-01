from fastapi import Depends, FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session

from .auth import create_access_token, get_current_user, hash_password, verify_password
from .database import Base, engine, get_db
from .models import Bot, SentProduct, User
from .schemas import BotCreate, BotOut, BotUpdate, SentProductOut, Token, UserCreate, UserLogin
from .services.crypto_service import encrypt

Base.metadata.create_all(bind=engine)

app = FastAPI(title='Shopee SaaS API')

app.add_middleware(
    CORSMiddleware,
    allow_origins=['*'],
    allow_credentials=True,
    allow_methods=['*'],
    allow_headers=['*'],
)


@app.get('/health')
def health():
    return {'status': 'ok'}


@app.post('/auth/register', response_model=Token)
def register(payload: UserCreate, db: Session = Depends(get_db)):
    exists = db.query(User).filter(User.email == payload.email).first()
    if exists:
        raise HTTPException(status_code=400, detail='Email já cadastrado')

    user = User(email=payload.email, password_hash=hash_password(payload.password))
    db.add(user)
    db.commit()
    token = create_access_token(user.email)
    return Token(access_token=token)


@app.post('/auth/login', response_model=Token)
def login(payload: UserLogin, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == payload.email).first()
    if not user or not verify_password(payload.password, user.password_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='Credenciais inválidas')

    return Token(access_token=create_access_token(user.email))


@app.get('/bots', response_model=list[BotOut])
def list_bots(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return db.query(Bot).filter(Bot.user_id == user.id).order_by(Bot.created_at.desc()).all()


@app.post('/bots', response_model=BotOut)
def create_bot(payload: BotCreate, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    bot = Bot(
        user_id=user.id,
        name=payload.name,
        shopee_app_id=payload.shopee_app_id,
        shopee_secret_encrypted=encrypt(payload.shopee_secret),
        telegram_token_encrypted=encrypt(payload.telegram_token),
        telegram_channel_id_encrypted=encrypt(payload.telegram_channel_id),
        status=payload.status,
        post_interval_seconds=payload.post_interval_seconds,
        fetch_interval_seconds=payload.fetch_interval_seconds,
        error_retry_seconds=payload.error_retry_seconds,
    )
    db.add(bot)
    db.commit()
    db.refresh(bot)
    return bot


@app.put('/bots/{bot_id}', response_model=BotOut)
def update_bot(bot_id: int, payload: BotUpdate, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    bot = db.query(Bot).filter(Bot.id == bot_id, Bot.user_id == user.id).first()
    if not bot:
        raise HTTPException(status_code=404, detail='Bot não encontrado')

    for field, value in payload.model_dump(exclude_unset=True).items():
        if value is None:
            continue
        if field == 'shopee_secret':
            bot.shopee_secret_encrypted = encrypt(value)
        elif field == 'telegram_token':
            bot.telegram_token_encrypted = encrypt(value)
        elif field == 'telegram_channel_id':
            bot.telegram_channel_id_encrypted = encrypt(value)
        else:
            setattr(bot, field, value)

    db.commit()
    db.refresh(bot)
    return bot


@app.patch('/bots/{bot_id}/toggle', response_model=BotOut)
def toggle_bot(bot_id: int, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    bot = db.query(Bot).filter(Bot.id == bot_id, Bot.user_id == user.id).first()
    if not bot:
        raise HTTPException(status_code=404, detail='Bot não encontrado')
    bot.status = not bot.status
    db.commit()
    db.refresh(bot)
    return bot


@app.get('/bots/{bot_id}/sent-products', response_model=list[SentProductOut])
def list_sent_products(bot_id: int, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    bot = db.query(Bot).filter(Bot.id == bot_id, Bot.user_id == user.id).first()
    if not bot:
        raise HTTPException(status_code=404, detail='Bot não encontrado')

    return (
        db.query(SentProduct)
        .filter(SentProduct.bot_id == bot_id)
        .order_by(SentProduct.created_at.desc())
        .limit(20)
        .all()
    )
