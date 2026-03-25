# Shopee Telegram SaaS

Plataforma SaaS multiusuário para automação de ofertas da Shopee no Telegram.

## Stack
- Backend: FastAPI + SQLAlchemy + PostgreSQL
- Worker: Python loop contínuo
- Frontend: Next.js (App Router)
- Infra: Docker Compose

## Como subir
```bash
docker compose up --build
```

Serviços:
- Backend: http://localhost:8000
- Frontend: http://localhost:3000

## Variáveis principais (backend/.env)
- `DATABASE_URL`
- `JWT_SECRET`
- `FERNET_KEY`
- `POST_INTERVAL_SECONDS` (default 1200)
- `FETCH_INTERVAL_SECONDS` (default 60)
- `ERROR_RETRY_SECONDS` (default 30)
