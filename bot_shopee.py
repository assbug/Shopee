import os
import time
import json
import hashlib
import logging
import random
import html
import tempfile
from typing import Any, Dict, Iterable, List, Sequence, Set, Tuple

import requests
from requests.adapters import HTTPAdapter
from urllib3.util import Retry
from dotenv import load_dotenv

load_dotenv()

# =============================
# CONFIG
# =============================

SHOPEE_APP_ID = os.getenv("SHOPEE_APP_ID")
SHOPEE_SECRET = os.getenv("SHOPEE_SECRET")

API_URL = "https://open-api.affiliate.shopee.com.br/graphql"

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
TELEGRAM_CANAL_ID = os.getenv("TELEGRAM_CANAL_ID")

POST_INTERVAL_BASE = int(os.getenv("POST_INTERVAL", "60"))
FETCH_INTERVAL_BASE = int(os.getenv("FETCH_INTERVAL", "120"))
JITTER_SECONDS = int(os.getenv("JITTER_SECONDS", "20"))
MAX_PAGES = int(os.getenv("MAX_PAGES", "6"))
REQUEST_TIMEOUT = int(os.getenv("REQUEST_TIMEOUT", "12"))

ENVIADOS_FILE = os.getenv("ENVIADOS_FILE", "enviados.json")

logging.basicConfig(
    level=os.getenv("LOG_LEVEL", "INFO"),
    format="%(asctime)s - %(levelname)s - %(message)s",
)


# =============================
# HTTP SESSION
# =============================

def criar_sessao() -> requests.Session:
    retry = Retry(
        total=3,
        backoff_factor=0.6,
        status_forcelist=(429, 500, 502, 503, 504),
        allowed_methods=("POST",),
    )
    adapter = HTTPAdapter(max_retries=retry)
    session = requests.Session()
    session.mount("https://", adapter)
    session.mount("http://", adapter)
    return session


SESSION = criar_sessao()


# =============================
# JSON
# =============================

def carregar_json(file_path: str) -> List[str]:
    if not os.path.exists(file_path):
        return []

    try:
        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)
            if isinstance(data, list):
                return [str(item) for item in data]
    except json.JSONDecodeError:
        logging.warning("Arquivo %s inválido. Recriando com lista vazia.", file_path)
    except OSError as exc:
        logging.error("Falha ao ler %s: %s", file_path, exc)

    return []


def salvar_json(file_path: str, data: Iterable[str]) -> None:
    pasta = os.path.dirname(file_path) or "."
    os.makedirs(pasta, exist_ok=True)

    fd, tmp_path = tempfile.mkstemp(prefix="enviados_", suffix=".tmp", dir=pasta)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            json.dump(sorted(set(data)), f, indent=2, ensure_ascii=False)
        os.replace(tmp_path, file_path)
    except OSError as exc:
        logging.error("Falha ao salvar %s: %s", file_path, exc)
        try:
            os.remove(tmp_path)
        except OSError:
            pass


produtos_enviados: Set[str] = set(carregar_json(ENVIADOS_FILE))


# =============================
# AUTH HEADER / API
# =============================

def gerar_headers(query: str) -> Dict[str, str]:
    timestamp = str(int(time.time()))
    factor = f"{SHOPEE_APP_ID}{timestamp}{query}{SHOPEE_SECRET}"
    signature = hashlib.sha256(factor.encode("utf-8")).hexdigest()

    return {
        "Content-Type": "application/json",
        "Authorization": (
            "SHA256 "
            f"Credential={SHOPEE_APP_ID}, Timestamp={timestamp}, Signature={signature}"
        ),
    }


def graphql_request(query: str, variables: Dict[str, Any] | None = None) -> Dict[str, Any]:
    payload = {"query": query, "variables": variables or {}}
    payload_text = json.dumps(payload, ensure_ascii=False)

    response = SESSION.post(
        API_URL,
        headers=gerar_headers(payload_text),
        data=payload_text.encode("utf-8"),
        timeout=REQUEST_TIMEOUT,
    )
    response.raise_for_status()

    data = response.json()
    if data.get("errors"):
        raise ValueError(f"GraphQL retornou erros: {data['errors']}")

    return data


# =============================
# UTIL
# =============================

def to_float(value: Any, default: float = 0.0) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def normalizar_nome(nome: str) -> str:
    return " ".join((nome or "").lower().split())


def intervalo_com_jitter(base: int, jitter: int) -> float:
    return max(1, base + random.uniform(-jitter, jitter))


def parse_nichos(entrada: str) -> List[str]:
    # Permite: "fone, teclado gamer; cadeira"
    raw = entrada.replace(";", ",")
    nichos = [item.strip() for item in raw.split(",") if item.strip()]
    return nichos if nichos else [entrada.strip()]


# =============================
# SHORT LINK
# =============================

def gerar_short_link(url_original: str) -> str:
    query = """
    mutation($originUrl: String!) {
      generateShortLink(input: { originUrl: $originUrl }) {
        shortLink
      }
    }
    """

    try:
        data = graphql_request(query, {"originUrl": url_original})
        short_link = data.get("data", {}).get("generateShortLink", {}).get("shortLink")
        return short_link or url_original
    except Exception as exc:
        logging.warning("Falha ao gerar short link (%s): %s", url_original, exc)
        return url_original


# =============================
# BUSCAR PRODUTOS
# =============================

def buscar_produtos(keyword: str, page: int = 1, limit: int = 10, sort_type: int | None = None) -> List[Dict[str, Any]]:
    # sortType comuns: 2/3/5. Mantemos randomização para variar vitrine.
    sort = sort_type if sort_type is not None else random.choice([2, 3, 5])

    query = """
    query($keyword: String!, $limit: Int!, $page: Int!, $sortType: Int!) {
      productOfferV2(keyword: $keyword, limit: $limit, page: $page, sortType: $sortType) {
        nodes {
          productName
          price
          imageUrl
          productLink
          shopName
          ratingStar
          sales
        }
      }
    }
    """

    try:
        data = graphql_request(
            query,
            {
                "keyword": keyword,
                "limit": limit,
                "page": page,
                "sortType": sort,
            },
        )
        nodes = data.get("data", {}).get("productOfferV2", {}).get("nodes", [])
        return nodes if isinstance(nodes, list) else []
    except Exception as exc:
        logging.warning("Falha ao buscar produtos de '%s' (página %s): %s", keyword, page, exc)
        return []


def buscar_multinichos(nichos: Sequence[str], pages: int = MAX_PAGES) -> List[Dict[str, Any]]:
    produtos: List[Dict[str, Any]] = []

    for nicho in nichos:
        for page in range(1, pages + 1):
            produtos.extend(buscar_produtos(nicho, page=page))
            time.sleep(random.uniform(0.3, 0.8))  # reduz rajadas na API

    return produtos


# =============================
# FILTROS E RANQUEAMENTO
# =============================

def remover_parecidos(produtos: Sequence[Dict[str, Any]]) -> List[Dict[str, Any]]:
    vistos: Set[str] = set()
    filtrados: List[Dict[str, Any]] = []

    for p in produtos:
        nome = normalizar_nome(p.get("productName", ""))
        shop = normalizar_nome(p.get("shopName", ""))
        chave = f"{nome[:45]}::{shop[:20]}"

        if chave in vistos:
            continue

        vistos.add(chave)
        filtrados.append(p)

    return filtrados


def filtrar_preco(produtos: Sequence[Dict[str, Any]], preco_min: float, preco_max: float) -> List[Dict[str, Any]]:
    return [
        p
        for p in produtos
        if preco_min <= to_float(p.get("price"), -1) <= preco_max
    ]


def filtrar_avaliacao(produtos: Sequence[Dict[str, Any]], avaliacao_min: float) -> List[Dict[str, Any]]:
    return [
        p
        for p in produtos
        if to_float(p.get("ratingStar"), 0) >= avaliacao_min
    ]


def score_produto(produto: Dict[str, Any]) -> float:
    rating = to_float(produto.get("ratingStar"), 0)
    vendas = to_float(produto.get("sales"), 0)
    preco = to_float(produto.get("price"), 0)

    # score heurístico: prioriza qualidade + prova social, sem ignorar ticket
    return (rating * 30) + min(vendas, 10000) * 0.02 + max(0, 200 - preco) * 0.05


def ordenar_por_potencial(produtos: Sequence[Dict[str, Any]]) -> List[Dict[str, Any]]:
    return sorted(produtos, key=score_produto, reverse=True)


# =============================
# TELEGRAM
# =============================

def legenda(produto: Dict[str, Any]) -> str:
    nome = html.escape(produto.get("productName", "Produto sem nome"))
    preco = to_float(produto.get("price"), 0)
    preco_str = f"{preco:.2f}".replace(".", ",")
    vendas = int(to_float(produto.get("sales"), 0))
    rating = to_float(produto.get("ratingStar"), 0)
    link = produto.get("productLink", "")

    return (
        "🔥 <b>OFERTA SHOPEE</b>\n\n"
        f"🛍️ {nome}\n\n"
        f"💸 <b>R$ {preco_str}</b>\n"
        f"⭐ {rating:.1f}/5\n"
        f"📦 {vendas} vendidos\n\n"
        f"🚀 <a href=\"{link}\">COMPRAR AGORA</a>"
    )


def enviar(produto: Dict[str, Any]) -> bool:
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendPhoto"
    payload = {
        "chat_id": TELEGRAM_CANAL_ID,
        "photo": produto.get("imageUrl", ""),
        "caption": legenda(produto),
        "parse_mode": "HTML",
    }

    try:
        response = SESSION.post(url, data=payload, timeout=REQUEST_TIMEOUT)
        response.raise_for_status()
        ok = response.json().get("ok", False)
        if not ok:
            logging.warning("Telegram respondeu sem OK: %s", response.text)
        return bool(ok)
    except Exception as exc:
        logging.error("Erro ao enviar para Telegram: %s", exc)
        return False


# =============================
# LOOP
# =============================

def loop(nichos: Sequence[str], preco_min: float, preco_max: float, avaliacao_min: float) -> None:
    falhas_seguidas = 0

    while True:
        logging.info("Buscando produtos para nichos: %s", ", ".join(nichos))

        produtos = buscar_multinichos(nichos)
        produtos = remover_parecidos(produtos)
        produtos = filtrar_preco(produtos, preco_min, preco_max)
        produtos = filtrar_avaliacao(produtos, avaliacao_min)
        produtos = ordenar_por_potencial(produtos)

        enviados_no_ciclo = 0

        for p in produtos:
            link_original = p.get("productLink", "")
            if not link_original or link_original in produtos_enviados:
                continue

            p["productLink"] = gerar_short_link(link_original)

            if enviar(p):
                produtos_enviados.add(link_original)
                salvar_json(ENVIADOS_FILE, produtos_enviados)
                enviados_no_ciclo += 1
                logging.info("Enviado: %s", p.get("productName", "(sem nome)"))
                time.sleep(intervalo_com_jitter(POST_INTERVAL_BASE, JITTER_SECONDS // 2))

        if enviados_no_ciclo == 0:
            falhas_seguidas += 1
        else:
            falhas_seguidas = 0

        # backoff progressivo quando nada novo é enviado
        espera = FETCH_INTERVAL_BASE + min(falhas_seguidas * 20, 300)
        espera = intervalo_com_jitter(int(espera), JITTER_SECONDS)

        logging.info(
            "Ciclo finalizado: %s enviados, aguardando %.1fs para nova busca...",
            enviados_no_ciclo,
            espera,
        )
        time.sleep(espera)


# =============================
# START
# =============================

def main() -> None:
    if not all([SHOPEE_APP_ID, SHOPEE_SECRET, TELEGRAM_TOKEN, TELEGRAM_CANAL_ID]):
        print("Configure corretamente o arquivo .env")
        raise SystemExit(1)

    print("=== BOT SHOPEE AFILIADO V4 ===")

    entrada_nichos = input("Digite um ou mais nichos/produtos (separe por vírgula): ").strip()
    nichos = parse_nichos(entrada_nichos)

    preco_min = float(input("Preço mínimo (R$): ").strip())
    preco_max = float(input("Preço máximo (R$): ").strip())
    avaliacao_min = float(input("Avaliação mínima (0-5): ").strip())

    if preco_min < 0 or preco_max < 0 or preco_min > preco_max:
        print("Faixa de preço inválida.")
        raise SystemExit(1)

    if not (0 <= avaliacao_min <= 5):
        print("Avaliação mínima deve estar entre 0 e 5.")
        raise SystemExit(1)

    loop(nichos, preco_min, preco_max, avaliacao_min)


if __name__ == "__main__":
    main()
