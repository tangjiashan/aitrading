def fetch_klines_by_market(market: str, symbol: str, interval: str, limit: int):
    if market == "binance":
        from .binance import fetch_binance_klines
        return fetch_binance_klines(symbol, interval, limit)
    elif market == "us":
        from .us_stock import fetch_us_stock_klines
        return fetch_us_stock_klines(symbol, interval, limit)
    else:
        raise ValueError(f"Unsupported market: {market}")
