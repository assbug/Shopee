import logging
from typing import Any

import requests


logger = logging.getLogger(__name__)


def format_caption(product: dict[str, Any]) -> str:
    nome_produto = product['productName']
    link_produto = product['productLink']

    preco_atual = float(product['price'])
    preco_atual_str = f'{preco_atual:.2f}'.replace('.', ',')
    taxa_desconto_str = product.get('priceDiscountRate')

    linha_preco = f'💸 <b>R$ {preco_atual_str}</b>'
    if taxa_desconto_str:
        try:
            taxa_desconto = float(taxa_desconto_str) / 100
            if taxa_desconto > 0:
                preco_original = preco_atual / (1 - taxa_desconto)
                preco_original_str = f'{preco_original:.2f}'.replace('.', ',')
                linha_preco = f'💰 De <del>R$ {preco_original_str}</del>\n🔥 Por <b>R$ {preco_atual_str}</b>'
        except (ValueError, ZeroDivisionError):
            pass

    detalhes_adicionais: list[str] = []
    vendas = product.get('sales')
    if vendas and int(vendas) > 10:
        detalhes_adicionais.append(f'📈 <b>+{vendas} vendidos!</b>')

    nome_loja = product.get('shopName')
    if nome_loja:
        detalhes_adicionais.append(f'🏪 Loja: {nome_loja}')

    linha_detalhes = '\n'.join(detalhes_adicionais)

    return f"""
🔥 OFERTA IMPERDÍVEL 🛍️

{nome_produto}

{linha_preco}

{linha_detalhes if linha_detalhes else ''}

🚀 <a href=\"{link_produto}\">COMPRAR AGORA</a>
Preço sujeito a alteração. Verifique no link!
"""


def send_telegram_product(product: dict[str, Any], telegram_token: str, telegram_channel_id: str) -> bool:
    send_url = f'https://api.telegram.org/bot{telegram_token}/sendPhoto'
    caption = format_caption(product)
    payload = {
        'chat_id': telegram_channel_id,
        'photo': product['imageUrl'],
        'caption': caption,
        'parse_mode': 'HTML',
    }

    try:
        response = requests.post(send_url, data=payload, timeout=15)
        response.raise_for_status()
        response_json = response.json()
        if not response_json.get('ok'):
            logger.error('Erro na API do Telegram: %s', response_json.get('description'))
            return False
        return True
    except requests.exceptions.RequestException as exc:
        logger.error('Falha ao enviar mensagem para o Telegram: %s', exc)
        return False
