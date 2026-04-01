import hashlib
import logging
import time
from typing import Any

import requests

from ..config import settings


logger = logging.getLogger(__name__)

SHOPEE_QUERY = (
    '{"query":"{\\n'
    'productOfferV2(limit: 5, sortType: 2){\\n'
    ' nodes{\\n'
    ' productName\\n'
    ' price\\n'
    ' priceDiscountRate\\n'
    ' productLink\\n'
    ' imageUrl\\n'
    ' sales\\n'
    ' shopName\\n'
    ' }\\n'
    '}\\n'
    '}"}'
)


def fetch_products(shopee_app_id: str, shopee_secret: str) -> list[dict[str, Any]] | None:
    timestamp = str(int(time.time()))
    factor = shopee_app_id + timestamp + SHOPEE_QUERY + shopee_secret
    signature = hashlib.sha256(factor.encode('utf-8')).hexdigest()

    headers = {
        'Content-Type': 'application/json',
        'Authorization': f'SHA256 Credential={shopee_app_id}, Timestamp={timestamp}, Signature={signature}',
    }

    try:
        response = requests.post(settings.shopee_api_url, headers=headers, data=SHOPEE_QUERY, timeout=10)
        response.raise_for_status()
        data = response.json()

        if 'errors' in data or 'data' not in data:
            logger.error('Erro na resposta da API da Shopee: %s', data)
            return None

        return data['data']['productOfferV2']['nodes']
    except requests.exceptions.RequestException as exc:
        logger.error('Falha ao conectar com a API da Shopee: %s', exc)
        return None
