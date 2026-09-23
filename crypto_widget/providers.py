"""三个公开现货行情接口的交易对映射与响应校验。"""

import json
from decimal import Decimal, InvalidOperation
from urllib.parse import urlencode

from .config import normalize_symbol

SOURCE_ORDER = ("binance", "okx", "bybit")
SOURCE_NAMES = {"binance": "Binance", "okx": "OKX", "bybit": "Bybit"}


def split_symbol(symbol):
    for quote in ("FDUSD", "USDT", "USDC", "TUSD", "BUSD", "DAI", "BTC", "ETH", "BNB", "EUR", "TRY", "USD", "BRL", "AUD", "GBP"):
        if symbol.endswith(quote) and len(symbol) > len(quote):
            return symbol[:-len(quote)], quote
    return symbol, ""


def instrument_id(source, symbol):
    symbol = normalize_symbol(symbol)
    if source == "okx":
        base, quote = split_symbol(symbol)
        if not quote:
            raise ValueError("无法识别计价币种，请使用 BTCUSDT 等完整现货交易对")
        return f"{base}-{quote}"
    return symbol


def price_url(source, symbol):
    instrument = instrument_id(source, symbol)
    if source == "binance":
        return "https://api.binance.com/api/v3/ticker/price?" + urlencode({"symbol": instrument})
    if source == "okx":
        return "https://www.okx.com/api/v5/market/ticker?" + urlencode({"instId": instrument})
    if source == "bybit":
        return "https://api.bybit.com/v5/market/tickers?" + urlencode({"category": "spot", "symbol": instrument})
    raise ValueError("不支持的行情数据源")


def _positive_price(raw):
    value = Decimal(str(raw))
    if not value.is_finite() or value <= 0 or value.adjusted() > 20:
        raise ValueError("价格无效")
    return value


def parse_price(data):
    """兼容原有 Binance 价格解析接口。"""
    try:
        return _positive_price(json.loads(data)["price"])
    except (ValueError, TypeError, KeyError, InvalidOperation, UnicodeError) as exc:
        raise ValueError("行情响应无效") from exc


def parse_provider_price(source, symbol, data):
    try:
        payload = json.loads(data)
        instrument = instrument_id(source, symbol)
        if source == "binance":
            if payload.get("symbol") != instrument:
                raise ValueError("交易对不匹配")
            raw = payload["price"]
        elif source == "okx":
            if payload.get("code") != "0":
                raise ValueError("交易所返回错误")
            item = next(row for row in payload["data"] if row["instId"] == instrument)
            if item.get("instType") != "SPOT":
                raise ValueError("不是现货行情")
            raw = item["last"]
        elif source == "bybit":
            if payload.get("retCode") != 0 or payload["result"]["category"] != "spot":
                raise ValueError("不是有效的现货行情")
            item = next(row for row in payload["result"]["list"] if row["symbol"] == instrument)
            raw = item["lastPrice"]
        else:
            raise ValueError("不支持的数据源")
        return _positive_price(raw)
    except (ValueError, TypeError, KeyError, AttributeError, StopIteration, InvalidOperation, UnicodeError) as exc:
        raise ValueError("交易对不受支持或现货行情响应无效") from exc
