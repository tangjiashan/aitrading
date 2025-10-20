import pandas as pd
import requests
from core.config import BINANCE_BASE_URL,PROXY_ADDRESS
from fastapi import HTTPException


def fetch_binance_klines(symbol: str, interval: str, limit: int):
    url = f"{BINANCE_BASE_URL}klines"
    params = {"symbol": symbol.upper(), "interval": interval, "limit": limit}
    # 发送 GET 请求
    response = requests.get(url, params=params, proxies={"https": PROXY_ADDRESS})
    if response.status_code != 200:
        raise HTTPException(status_code=500, detail="Binance API Error")
    raw = response.json()
    df = pd.DataFrame(raw, columns=[
        "open_time", "open", "high", "low", "close", "volume",
        "close_time", "quote_asset_volume", "num_trades",
        "taker_buy_base_vol", "taker_buy_quote_vol", "ignore"
    ])
    df = df[["open_time", "open", "high", "low", "close", "volume"]]
    df = df.astype({"open": float, "high": float, "low": float, "close": float, "volume": float})
    return df