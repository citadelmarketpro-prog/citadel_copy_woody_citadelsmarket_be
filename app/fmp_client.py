import requests
from decouple import config

FMP_BASE = "https://financialmodelingprep.com/api/v3"
_API_KEY = None


def _key():
    global _API_KEY
    if _API_KEY is None:
        _API_KEY = config("FMP_API_KEY", default="")
    return _API_KEY


def fmp_get(endpoint, params=None):
    url = f"{FMP_BASE}{endpoint}"
    p = {"apikey": _key()}
    if params:
        p.update(params)
    resp = requests.get(url, params=p, timeout=15)
    resp.raise_for_status()
    return resp.json()


def get_quotes(symbols):
    """Batch quote fetch for any list of FMP symbols."""
    if not symbols:
        return []
    return fmp_get(f"/quote/{','.join(symbols)}")


def get_news(feed_type="stock", limit=50):
    """
    Fetch news from FMP.
    feed_type: 'stock' | 'forex' | 'crypto' | 'general'
    """
    endpoints = {
        "stock":   "/stock_news",
        "forex":   "/forex_news",
        "crypto":  "/crypto_news",
        "general": "/general_news",
    }
    return fmp_get(endpoints.get(feed_type, "/stock_news"), {"limit": limit})
