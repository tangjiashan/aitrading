import os
from datetime import datetime
import asyncio
import numpy as np
import pandas as pd
import requests
import tweepy

from core.config import MONITOR_SYMBOLS, BINANCE_BASE_URL
from scheduler.task_runner import notify_dify
from services.market import fetch_klines_by_market
from services.indicators import get_123_signal, three_bar_reversal_pattern, detect_123_continuation_patterns, rsi, \
    calculate_rsi, get_hammer_signal, get_inverted_hammer_signal, find_support_resistance
from candlestick import candlestick
from services.notifier import send_to_x, render_message_to_image


def get_signal():
    for item in MONITOR_SYMBOLS:
        if item["market"] == "binance":
            df = fetch_klines_by_market(
                market=item["market"],
                symbol=item["symbol"],
                interval="4h",
                limit=400
            )
            df["timestamp"] = df["open_time"]
            klines = df.values.tolist()
            result = detect_123_continuation_patterns(klines)
            # draw_trade_signal_chart(df,result)
            # result = get_123_signal(klines)
            for i in result:
                date = datetime.fromtimestamp(i.get("timestamp") / 1000)
                print(date)
                print(i)


def get_pattern():
    for item in MONITOR_SYMBOLS:
        if item["market"] == "binance":
            df = fetch_klines_by_market(
                market=item["market"],
                symbol=item["symbol"],
                interval="4h",
                limit=120
            )
            rsi = calculate_rsi(df)

            # result = get_123_signal(df,rsi.iloc[-2])
            hammer_result = get_hammer_signal(df,rsi.iloc[-2])
            inverted_hammer_result = get_inverted_hammer_signal(df, rsi.iloc[-2])
            # print(result)
            print(hammer_result)
            print(inverted_hammer_result)

def get_pattern_signal():
    for item in MONITOR_SYMBOLS:
        if item["market"] == "binance":
            df = fetch_klines_by_market(
                market=item["market"],
                symbol=item["symbol"],
                interval="4h",
                limit=120
            )
            print(df.head())
            print(df.columns)
            df["timestamp"] = df["open_time"]
            df["timestamp"] = pd.to_datetime(df["timestamp"], unit="ms")
            df.set_index("timestamp", inplace=True)
            result = three_bar_reversal_pattern(df)
            print(result)

def get_pattern_type():
    for item in MONITOR_SYMBOLS:
        if item["market"] == "binance":
            candles_df = fetch_klines_by_market(
                market=item["market"],
                symbol=item["symbol"],
                interval="4h",
                limit=120
            )

            candles_df['T'] = pd.to_datetime(candles_df['open_time'], unit='ms')

            target = 'InvertedHammers'
            # candles_df = candlestick.inverted_hammer(candles_df, target=target)
            # candles_df = candlestick.doji_star(candles_df)
            # candles_df = candlestick.bearish_harami(candles_df)
            # candles_df = candlestick.bullish_harami(candles_df)
            # candles_df = candlestick.dark_cloud_cover(candles_df)
            # candles_df = candlestick.doji(candles_df)
            # candles_df = candlestick.dragonfly_doji(candles_df)
            # candles_df = candlestick.hanging_man(candles_df,target=target)
            # candles_df = candlestick.gravestone_doji(candles_df)
            # candles_df = candlestick.bearish_engulfing(candles_df)
            # candles_df = candlestick.bullish_engulfing(candles_df)
            candles_df = candlestick.hammer(candles_df,target=target)
            # candles_df = candlestick.morning_star(candles_df)
            # candles_df = candlestick.morning_star_doji(candles_df)
            # candles_df = candlestick.piercing_pattern(candles_df)
            # candles_df = candlestick.rain_drop(candles_df)
            # candles_df = candlestick.rain_drop_doji(candles_df)
            # candles_df = candlestick.star(candles_df)
            # candles_df = candlestick.shooting_star(candles_df)

            print(candles_df[candles_df[target] == True][['T', target]])

def test_candlestick():
    url = f"{BINANCE_BASE_URL}klines"
    params = {"symbol":"BTCUSDT", "interval": "4h", "limit": 270}
    # 发送 GET 请求
    PROXY_ADDRESS = "http://127.0.0.1:7890"
    # 发送 GET 请求
    response = requests.get(url, params=params, proxies={"https": PROXY_ADDRESS})
    # candles = requests.get('https://api.binance.com/api/v1/klines?symbol=BTCUSDT&interval=1d')
    candles_dict = response.json()

    candles_df = pd.DataFrame(candles_dict,
                              columns=['T', 'open', 'high', 'low', 'close', 'V', 'CT', 'QV', 'N', 'TB', 'TQ', 'I'])

    candles_df['T'] = pd.to_datetime(candles_df['T'], unit='ms')
    #
    target = 'BullishEngulfing'
    # candles_df = candlestick.inverted_hammer(candles_df, target=target)
    # candles_df = candlestick.doji_star(candles_df)
    # candles_df = candlestick.bearish_harami(candles_df,target=target) # good
    # candles_df = candlestick.bullish_harami(candles_df, target=target) # good
    # candles_df = candlestick.dark_cloud_cover(candles_df)
    # candles_df = candlestick.doji(candles_df)
    # candles_df = candlestick.dragonfly_doji(candles_df)
    # candles_df = candlestick.hanging_man(candles_df)
    # candles_df = candlestick.gravestone_doji(candles_df)
    # candles_df = candlestick.bearish_engulfing(candles_df)
    candles_df = candlestick.bullish_engulfing(candles_df)
    # candles_df = candlestick.hammer(candles_df, target=target) # good
    # candles_df = candlestick.morning_star(candles_df)
    # candles_df = candlestick.morning_star_doji(candles_df)
    # candles_df = candlestick.piercing_pattern(candles_df)
    # candles_df = candlestick.rain_drop(candles_df)
    # candles_df = candlestick.rain_drop_doji(candles_df)
    # candles_df = candlestick.star(candles_df)
    # candles_df = candlestick.shooting_star(candles_df)

    print(candles_df[candles_df[target] == True][['T', target]])
    #
    # result = find_support_resistance(candles_df)
    # print(result)
    # rsi_result =  calculate_rsi(candles_df)
    # print(rsi_result)
    # print("rsi value {}", rsi_result.iloc[-2])


if __name__ == "__main__":
    # get_signal()
    # get_pattern_signal()
    # get_pattern()
    test_candlestick()
