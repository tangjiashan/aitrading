import talib
import pandas as pd
import datetime
from scipy.signal import argrelextrema
import numpy as np

from candlestick import candlestick


def calculate_rsi(df: pd.DataFrame, period: int = 14):
    return talib.RSI(df['close'], timeperiod=period)


def detect_123_continuation_patterns(
    klines,
    tp_mult=1.5,
    length=5,
    use_close_for_entry=True,
    show_plot=True,
    min_signal_distance=5,
    mode="both"  # 可选: "long", "short", "both"
):
    """
        检测123反转形态，返回所有成功的形态
    """
    result = []

    highs = [float(k[2]) for k in klines]
    lows = [float(k[3]) for k in klines]
    closes = [float(k[4]) for k in klines]
    timestamps = [int(k[0]) for k in klines]
    times = pd.to_datetime(timestamps, unit='ms')

    lastHigh = 0.0
    lastLow = float("inf")
    timeHigh = 0
    timeLow = 0
    dir_up = False
    last_signal_index_long = -1000
    last_signal_index_short = -1000

    for i in range(length, len(klines) - 1):
        h = max(highs[i - length: i + length + 1])
        l = min(lows[i - length: i + length + 1])
        isMax = highs[i] == h
        isMin = lows[i] == l

        # ---- Long 逻辑 ----
        if mode in ["long", "both"]:
            if dir_up:
                if isMin and lows[i] < lastLow:
                    lastLow = lows[i]
                    timeLow = i
                elif isMax and highs[i] > lastLow:
                    lastHigh = highs[i]
                    timeHigh = i
                    dir_up = False
            else:
                if isMax and highs[i] > lastHigh:
                    lastHigh = highs[i]
                    timeHigh = i
                elif isMin and lows[i] < lastHigh:
                    lastLow = lows[i]
                    timeLow = i
                    dir_up = True

                    for j in range(i + 1, len(klines) - 1):
                        k = j
                        price_check = closes[j] if use_close_for_entry else highs[j]
                        if price_check > lastHigh and j - last_signal_index_long >= min_signal_distance:
                            entry_price = lastHigh
                            stop_loss = lastLow
                            take_profit = entry_price + (lastHigh - lastLow) * tp_mult
                            # dt = times[j]
                            result.append({
                                "type": "long",
                                "index": k,
                                "timestamp": timestamps[k],
                                "entry_price": round(entry_price, 2),
                                "stop_loss": round(stop_loss, 2),
                                "take_profit": round(take_profit, 2)
                            })
                            last_signal_index_long = j
                            break

        # ---- Short 逻辑 ----
        if mode in ["short", "both"]:
            if not dir_up:
                if isMax and highs[i] > lastHigh:
                    lastHigh = highs[i]
                    timeHigh = i
                elif isMin and lows[i] < lastHigh:
                    lastLow = lows[i]
                    timeLow = i
                    dir_up = True
            else:
                if isMin and lows[i] < lastLow:
                    lastLow = lows[i]
                    timeLow = i
                elif isMax and highs[i] > lastLow:
                    lastHigh = highs[i]
                    timeHigh = i
                    dir_up = False

                    for j in range(i + 1, len(klines) - 1):
                        k = j
                        price_check = closes[j] if use_close_for_entry else lows[j]
                        if price_check < lastLow and j - last_signal_index_short >= min_signal_distance:
                            entry_price = lastLow
                            stop_loss = lastHigh
                            take_profit = entry_price - (stop_loss - entry_price) * tp_mult
                            dt = times[j]
                            result.append({
                                "type": "short",
                                "index": k,
                                "timestamp": timestamps[k],
                                "entry_price": round(entry_price, 2),
                                "stop_loss": round(stop_loss, 2),
                                "take_profit": round(take_profit, 2)
                            })
                            last_signal_index_short = j
                            break

    return result

def rsi(series, period=14):
    delta = series.diff()
    gain = delta.clip(lower=0).ewm(alpha=1/period, min_periods=period).mean()
    loss = -delta.clip(upper=0).ewm(alpha=1/period, min_periods=period).mean()
    rs = gain / loss
    return 100 - (100 / (1 + rs))

def detect_rsi_filter(rsi_series, i, direction):
    if i < 1: return False
    if direction == "long":
        return 30 < rsi_series[i] < 50 and rsi_series[i] > rsi_series[i - 1]
    elif direction == "short":
        return 50 < rsi_series[i] < 70 and rsi_series[i] < rsi_series[i - 1]
    return False

def detect_volume_filter(volumes, i, avg_period=20):
    if i < avg_period: return False
    return volumes[i] > volumes[i - avg_period:i].mean()

def detect_three_bar_pattern(df, i):
    o, h, l, c = df.open, df.high, df.low, df.close
    if i < 2: return None
    if (c[i - 2] > o[i - 2] and c[i - 1] < o[i - 1] and c[i] > o[i] and c[i] > c[i - 1] and l[i] > l[i - 1]):
        return "long"
    if (c[i - 2] < o[i - 2] and c[i - 1] > o[i - 1] and c[i] < o[i] and c[i] < c[i - 1] and h[i] < h[i - 1]):
        return "short"
    return None

def check_trade_signal(df, pattern_lookback=5, volume_avg_n=20):
    """
        检测多种信号，如满足则入场开单
        """
    rsi_series = rsi(df['close'], period=14)
    volumes = df['volume'].values

    # 1. 获取 123 突破信号（含入场点/止损/止盈）
    patterns = detect_123_continuation_patterns(df)
    signals = []

    for p in patterns:
        i = p['signal_index']
        direction = p['direction']
        entry = p['entry']
        reasons = []

        # ❶ 检查 pattern_lookback 区间内是否存在同方向 Three Bar Reversal Pattern
        three_bar_match = False
        for j in range(i - pattern_lookback, i):
            if j >= 2 and detect_three_bar_pattern(df, j) == direction:
                three_bar_match = True
                break
        if not three_bar_match:
            continue
        reasons.append("3bar-match")

        # ❷ RSI 过滤器（在突破 K 线处生效）
        if not detect_rsi_filter(rsi_series, i, direction):
            continue
        reasons.append("RSI-ok")

        # ❸ 成交量过滤器（在突破 K 线处判断）
        if not detect_volume_filter(volumes, i, avg_period=volume_avg_n):
            continue
        reasons.append("volume-high")

        # ✅ 所有过滤器通过，保留信号
        signals.append({
            "signal": True,
            "direction": direction,
            "entry_price": entry,
            "stop_loss": p['stop_loss'],
            "take_profit": p['take_profit'],
            "signal_index": i,
            "reason": ["123-breakout"] + reasons
        })

    return signals


def three_bar_reversal_pattern(df, direction="both"):
    """
    检测 Three Bar Reversal Pattern（反转形态）
    形态特征：
        多头反转：bar1收跌，bar2最低价低于bar1和bar3，bar3收盘价高于bar1和bar2的最高价
        空头反转：bar1收涨，bar2最高价高于bar1和bar3，bar3收盘价低于bar1和bar2的最低价
    """
    signals = []
    df = df.reset_index(drop=True)
    for i in range(2, len(df)):
        bar1 = df.iloc[i - 2]
        bar2 = df.iloc[i - 1]
        bar3 = df.iloc[i]

        open1, close1, high1, low1 = bar1["open"], bar1["close"], bar1["high"], bar1["low"]
        open2, close2, high2, low2 = bar2["open"], bar2["close"], bar2["high"], bar2["low"]
        open3, close3, high3, low3 = bar3["open"], bar3["close"], bar3["high"], bar3["low"]

        # 多头反转条件
        is_bullish = (
            close1 < open1 and
            low2 < low1 and low2 < low3 and
            close3 > high1 and close3 > high2
        )

        # 空头反转条件
        is_bearish = (
            close1 > open1 and
            high2 > high1 and high2 > high3 and
            close3 < low1 and close3 < low2
        )

        timestamp = int(bar3["open_time"])  # 转换为毫秒时间戳

        if direction in ("long", "both") and is_bullish:
            signals.append({"type": "long", "timestamp": timestamp})

        if direction in ("short", "both") and is_bearish:
            signals.append({"type": "short", "timestamp": timestamp})

    return signals



def get_123_signal(klines, rsi):
    """
    检测123反转形态，返回最后一个成功的形态
    """
    try:
        # 获取倒数第二根已收盘K线的时间戳
        confirmed_ts = klines.iloc[-2]["open_time"]
        patterns = detect_123_continuation_patterns(
            klines.values.tolist(),
            tp_mult=1.5,
            length=5,
            use_close_for_entry=True,
            show_plot=False,
            min_signal_distance=10,
            mode="both"
        )
        if not patterns:
            return {"signal": False, "message": "No 123 pattern found"}
        # 只保留出现在“已收盘倒数第二根K线”的信号
        # valid = [
        #     p for p in patterns
        #     if int(p["timestamp"]) == confirmed_ts
        # ]
        # valid = []
        # for p in patterns:
        #     print(p["timestamp"])
        #     if int(p["timestamp"]) == confirmed_ts:
        #         valid.append(p)

        # if not valid:
        #     return {"signal": False, "message": "No signal in last confirmed candle"}

        latest = patterns[-1]
        if latest["timestamp"] == confirmed_ts:
            return {
                "signal": True,
                "signal_type": "123_breakout",
                "type": latest["type"],
                "timestamp": datetime.datetime.now().isoformat(),
                "entry_price": latest["entry_price"],
                "stop_loss": latest["stop_loss"],
                "tp_mult": 1.5,
                "take_profit": latest["take_profit"],
                "rsi": round(rsi, 2)
            }

    except Exception as e:
        return {"error": str(e)}




def get_hammer_signal(klines, rsi):
    """
    检测hammer反转形态，返回最后一个成功的形态
    """
    try:
        # 获取倒数第二根已收盘K线的时间戳
        confirmed_ts = klines.iloc[-2]["open_time"]
        target = 'hammer'
        patterns = candlestick.hammer(klines, target=target)
        if patterns.empty:
            return {"signal": False, "message": "No hammer pattern found"}
        valid = patterns[patterns[target] == True]
        if valid.empty:
            return {"signal": False, "message": "No signal in last confirmed candle"}

        if valid.iloc[-1]["open_time"] == confirmed_ts:
            entry_price = float(klines.iloc[-2]["close"])
            stop_loss = float(klines.iloc[-2]["low"])
            take_profit = entry_price+(entry_price-stop_loss)*2
            return {
                "signal": True,
                "signal_type": target,
                "type": "long",
                "timestamp": datetime.datetime.now().isoformat(),
                "entry_price": entry_price,
                "stop_loss": stop_loss,
                "tp_mult": 2,
                "take_profit": take_profit,
                "rsi": round(rsi, 2)
            }

    except Exception as e:
        return {"error": str(e)}




def get_inverted_hammer_signal(klines,rsi):
    """
    检测inverted_hammer反转形态，返回最后一个成功的形态
    """
    try:
        # 获取倒数第二根已收盘K线的时间戳
        confirmed_ts = klines.iloc[-2]["open_time"]
        target = 'inverted_hammer'
        patterns = candlestick.inverted_hammer(klines, target=target)
        if patterns.empty:
            return {"signal": False, "message": "No inverted_hammer pattern found"}
        valid = patterns[patterns[target] == True]
        if valid.empty:
            return {"signal": False, "message": "No signal in last confirmed candle"}

        if valid.iloc[-1]["open_time"] == confirmed_ts:
            entry_price = float(klines.iloc[-2]["close"])
            stop_loss = float(klines.iloc[-2]["high"])
            take_profit = entry_price-(stop_loss-entry_price)*2
            return {
                "signal": True,
                "signal_type": target,
                "type": "short",
                "timestamp": datetime.datetime.now().isoformat(),
                "entry_price": entry_price,
                "stop_loss": stop_loss,
                "tp_mult": 2,
                "take_profit": take_profit,
                "rsi": round(rsi, 2)
            }

    except Exception as e:
        return {"error": str(e)}


def get_bullish_engulfing_signal(klines,rsi):
    """
        检测bullish_engulfing反转形态，返回最后一个成功的形态
        """
    try:
        # 获取倒数第二根已收盘K线的时间戳
        confirmed_ts = klines.iloc[-2]["open_time"]
        target = 'bullish_engulfing'
        patterns = candlestick.bullish_engulfing(klines, target=target)
        if patterns.empty:
            return {"signal": False, "message": "No bullish_engulfing pattern found"}
        valid = patterns[patterns[target] == True]
        if valid.empty:
            return {"signal": False, "message": "No bullish_engulfing signal in last confirmed candle"}

        if valid.iloc[-1]["open_time"] == confirmed_ts:
            entry_price = float(klines.iloc[-2]["close"])
            stop_loss = float(klines.iloc[-2]["low"])
            take_profit = entry_price+(entry_price-stop_loss)*2
            return {
                "signal": True,
                "signal_type": target,
                "type": "long",
                "timestamp": datetime.datetime.now().isoformat(),
                "entry_price": entry_price,
                "stop_loss": stop_loss,
                "tp_mult": 2,
                "take_profit": take_profit,
                "rsi": round(rsi, 2)
            }

    except Exception as e:
        return {"error": str(e)}


def get_bearish_engulfing_signal(klines,rsi):
    """
    检测bearish_engulfing反转形态，返回最后一个成功的形态
    """
    try:
        # 获取倒数第二根已收盘K线的时间戳
        confirmed_ts = klines.iloc[-2]["open_time"]
        target = 'bearish_engulfing'
        patterns = candlestick.bearish_engulfing(klines, target=target)
        if patterns.empty:
            return {"signal": False, "message": "No bearish_engulfing pattern found"}
        valid = patterns[patterns[target] == True]
        if valid.empty:
            return {"signal": False, "message": "No bearish_engulfing signal in last confirmed candle"}

        if valid.iloc[-1]["open_time"] == confirmed_ts:
            entry_price = float(klines.iloc[-2]["close"])
            stop_loss = float(klines.iloc[-2]["high"])
            take_profit = entry_price-(stop_loss-entry_price)*2
            return {
                "signal": True,
                "signal_type": target,
                "type": "short",
                "timestamp": datetime.datetime.now().isoformat(),
                "entry_price": entry_price,
                "stop_loss": stop_loss,
                "tp_mult": 2,
                "take_profit": take_profit,
                "rsi": round(rsi, 2)
            }

    except Exception as e:
        return {"error": str(e)}





def find_support_resistance(df, order=10, threshold=0.02):
    """
    参数说明：
    - df: 包含 open, high, low, close 的K线数据
    - order: 用于寻找局部极值的窗口大小
    - threshold: 支撑/阻力价格聚合的容忍度（比例）

    返回：support_levels, resistance_levels（两个浮点数列表）
    """
    close = df['close'].astype(float).values

    # 识别局部极小值（支撑）和局部极大值（阻力）
    local_min = argrelextrema(close, np.less_equal, order=order)[0]
    local_max = argrelextrema(close, np.greater_equal, order=order)[0]

    support_candidates = close[local_min].astype(float)
    resistance_candidates = close[local_max].astype(float)

    def cluster_levels(levels):
        clustered = []
        for level in levels:
            if not any(abs(level - c) / c < threshold for c in clustered):
                clustered.append(level)
        return clustered

    support = cluster_levels(support_candidates)
    resistance = cluster_levels(resistance_candidates)

    return support, resistance

def is_volume_spike(df, idx, window=20, spike_ratio=1.5):
    """
    判断当前K线是否放量
    - window: 计算平均成交量的周期
    - spike_ratio: 当前成交量是平均的多少倍算放量
    """
    if idx < window:
        return False
    avg_volume = df['volume'].iloc[idx - window:idx].mean()
    current_volume = df['volume'].iloc[idx]
    return current_volume > spike_ratio * avg_volume


def is_near_level(price, levels, tolerance=0.005):
    """
    判断某价格是否接近某组支撑/阻力位
    - tolerance: 允许价格相对偏差，比如0.005代表0.5%
    """
    return any(abs(price - level) / level < tolerance for level in levels)
