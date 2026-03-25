import hashlib
import logging
import time
from typing import Any

import requests

SHOPEE_API_URL = 'https://open-api.affiliate.shopee.com.br/graphql'

QUERY = (
    '{"query":"{\n'
    'productOfferV2(limit: 5, sortType: 2){\n'
    ' nodes{\n'
    ' productName\n'
    ' price\n'
    ' priceDiscountRate\n'
    ' productLink\n'
    ' imageUrl\n'
    ' sales\n'
    ' shopName\n'
    ' }\n'
    '}\n'
    '}"}'
)


def pegar_produtos(shopee_app_id: str, shopee_secret: str) -> list[dict[str, Any]] | None:
    timestamp = str(int(time.time()))
    factor = shopee_app_id + timestamp + QUERY + shopee_secret
    signature = hashlib.sha256(factor.encode('utf-8')).hexdigest()

    headers = {
        'Content-Type': 'application/json',
        'Authorization': f'SHA256 Credential={shopee_app_id}, Timestamp={timestamp}, Signature={signature}',
    }

    try:
        response = requests.post(SHOPEE_API_URL, headers=headers, data=QUERY, timeout=10)
        response.raise_for_status()
        dados = response.json()

        if 'errors' in dados or 'data' not in dados:
            logging.error(f'Erro na resposta da API da Shopee: {dados}')
            return None

        return dados['data']['productOfferV2']['nodes']
    except requests.exceptions.RequestException as e:
        logging.error(f'Falha ao conectar com a API da Shopee: {e}')
        return None
