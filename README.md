# Shopee Telegram SaaS

SaaS multiusuário com **FastAPI + Worker + PostgreSQL + React (Vite)** para automatizar publicação de ofertas da Shopee no Telegram, preservando a lógica central original:

- Autenticação Shopee com `SHA256 Credential={APP_ID}, Timestamp={timestamp}, Signature={signature}`.
- Query GraphQL `productOfferV2(limit: 5, sortType: 2)`.
- Formatação de legenda em HTML para Telegram.
- Envio via endpoint `sendPhoto`.
- Prevenção de repostagem via tabela `sent_products`.
- Intervalos padrão: `1200 / 60 / 30` segundos.

## Estrutura

- `backend/app/main.py`: API REST (auth, bots, status, produtos enviados)
- `backend/app/services/shopee_service.py`: integração Shopee
- `backend/app/services/telegram_service.py`: legenda e envio Telegram
- `backend/app/workers/bot_runner.py`: loop contínuo de automação
- `frontend/src/App.jsx`: dashboard web responsivo

## Executar com Docker

```bash
docker compose up --build
```

Acesse:
- Frontend: `http://localhost:5173`
- Backend: `http://localhost:8000/docs`

## Segurança

Credenciais sensíveis dos bots (`shopee_secret`, `telegram_token`, `telegram_channel_id`) são criptografadas no banco e nunca retornadas no frontend.
