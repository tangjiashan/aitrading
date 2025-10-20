SERVER_CONFIG = {
    "host": "0.0.0.0",
    "port": 8900,
    "reload": True  # 可选，开发模式下自动重载
}
PROXY_ADDRESS = "http://127.0.0.1:7890"
BINANCE_BASE_URL = "https://api.binance.com/api/v3/"

MONITOR_SYMBOLS = [
    {"symbol": "BTCUSDT", "market": "binance","interval": "15m"},
    {"symbol": "ETHUSDT", "market": "binance","interval": "15m"},
    {"symbol": "SOLUSDT", "market": "binance", "interval": "15m"},
    {"symbol": "DOGEUSDT", "market": "binance","interval": "15m"},
    {"symbol": "XRPUSDT", "market": "binance","interval": "15m"}
]