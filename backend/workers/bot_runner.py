import logging
import time
from datetime import datetime

from sqlalchemy.exc import IntegrityError

from database import SessionLocal
from models import Bot, SentProduct
from security import decrypt_value
from services.shopee_service import pegar_produtos
from services.telegram_service import enviar_telegram

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S',
)


def process_bot(bot_id: int):
    db = SessionLocal()
    try:
        bot = db.query(Bot).filter(Bot.id == bot_id, Bot.status.is_(True)).first()
        if not bot:
            return

        logging.info(f'Buscando novos produtos na Shopee para bot #{bot.id}...')
        shopee_secret = decrypt_value(bot.shopee_secret_enc)
        telegram_token = decrypt_value(bot.telegram_token_enc)

        produtos = pegar_produtos(bot.shopee_app_id, shopee_secret)
        if produtos is None:
            logging.warning(
                f'Não foi possível obter produtos para bot #{bot.id}. Tentando novamente em {bot.error_retry_seconds} segundos.'
            )
            time.sleep(bot.error_retry_seconds)
            return

        novos_produtos_encontrados = 0
        for p in produtos:
            already_sent = (
                db.query(SentProduct)
                .filter(SentProduct.bot_id == bot.id, SentProduct.product_link == p['productLink'])
                .first()
            )
            if already_sent:
                continue

            logging.info(f"Novo produto encontrado: {p['productName']} (Vendas: {p.get('sales')})")
            if enviar_telegram(p, telegram_token, bot.telegram_channel_id):
                sp = SentProduct(bot_id=bot.id, product_link=p['productLink'])
                db.add(sp)
                try:
                    db.commit()
                except IntegrityError:
                    db.rollback()
                logging.info(f"Postado com sucesso: {p['productName']}")
                novos_produtos_encontrados += 1
                time.sleep(bot.post_interval_seconds)
            else:
                logging.error(f"Falha ao postar o produto: {p['productName']}")

        if novos_produtos_encontrados == 0:
            logging.info(f'Nenhum produto novo encontrado para bot #{bot.id}.')

        bot.last_run_at = datetime.utcnow()
        db.commit()
    finally:
        db.close()


def main_loop():
    logging.info('>>> Worker iniciado com sucesso! <<<')
    while True:
        db = SessionLocal()
        try:
            active_bot_ids = [row[0] for row in db.query(Bot.id).filter(Bot.status.is_(True)).all()]
        finally:
            db.close()

        for bot_id in active_bot_ids:
            process_bot(bot_id)

        sleep_for = 60
        if active_bot_ids:
            db = SessionLocal()
            try:
                first_bot = db.query(Bot).filter(Bot.id == active_bot_ids[0]).first()
                if first_bot:
                    sleep_for = first_bot.fetch_interval_seconds
            finally:
                db.close()

        logging.info(f'Aguardando {sleep_for} segundos para o próximo ciclo.\n')
        time.sleep(sleep_for)


if __name__ == '__main__':
    try:
        main_loop()
    except KeyboardInterrupt:
        logging.info('>>> Worker encerrado pelo usuário. <<<')
