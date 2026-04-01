import logging
import time
from datetime import datetime

from sqlalchemy.orm import Session

from ..database import SessionLocal
from ..models import Bot, SentProduct
from ..services.crypto_service import decrypt
from ..services.shopee_service import fetch_products
from ..services.telegram_service import send_telegram_product


logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S',
)
logger = logging.getLogger(__name__)


def run_single_bot(db: Session, bot: Bot) -> None:
    logger.info('Buscando novos produtos na Shopee para bot %s...', bot.id)

    products = fetch_products(shopee_app_id=bot.shopee_app_id, shopee_secret=decrypt(bot.shopee_secret_encrypted))
    if products is None:
        logger.warning('Bot %s: falha ao buscar produtos. retry em %s segundos', bot.id, bot.error_retry_seconds)
        return

    telegram_token = decrypt(bot.telegram_token_encrypted)
    telegram_channel_id = decrypt(bot.telegram_channel_id_encrypted)

    sent_count = 0
    for product in products:
        already_sent = (
            db.query(SentProduct)
            .filter(SentProduct.bot_id == bot.id, SentProduct.product_link == product['productLink'])
            .first()
        )
        if already_sent:
            continue

        logger.info('Bot %s novo produto encontrado: %s', bot.id, product['productName'])
        if send_telegram_product(product, telegram_token, telegram_channel_id):
            db.add(SentProduct(bot_id=bot.id, product_link=product['productLink']))
            db.commit()
            sent_count += 1
            logger.info('Bot %s postado com sucesso: %s', bot.id, product['productName'])
            time.sleep(bot.post_interval_seconds)
        else:
            logger.error('Bot %s falha ao postar produto: %s', bot.id, product['productName'])

    bot.last_run_at = datetime.utcnow()
    db.commit()

    if sent_count == 0:
        logger.info('Bot %s nenhum produto novo nesta busca.', bot.id)


def run_worker() -> None:
    logger.info('>>> Worker iniciado com sucesso! <<<')
    while True:
        db = SessionLocal()
        try:
            active_bots = db.query(Bot).filter(Bot.status.is_(True)).all()
            if not active_bots:
                time.sleep(10)
                continue

            for bot in active_bots:
                run_single_bot(db, bot)
                time.sleep(bot.fetch_interval_seconds)
        except KeyboardInterrupt:
            logger.info('>>> Worker encerrado pelo usuário. <<<')
            break
        except Exception as exc:
            logger.exception('Erro não tratado no worker: %s', exc)
            time.sleep(30)
        finally:
            db.close()


if __name__ == '__main__':
    run_worker()
