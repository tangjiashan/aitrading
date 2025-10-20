import json
import logging

import httpx
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from dotenv import load_dotenv
from openai import AsyncOpenAI

from core.config import MONITOR_SYMBOLS
from services.market import fetch_klines_by_market
from services.indicators import calculate_rsi, get_hammer_signal, get_inverted_hammer_signal,  \
    get_bearish_engulfing_signal, get_bullish_engulfing_signal
import os
load_dotenv()  # 自动读取 .env 文件
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
SILICONFLOW_API_KEY = os.getenv("SILICONFLOW_API_KEY")
USE_SILICONFLOW = os.getenv("USE_SILICONFLOW", "false").lower() == "true"
scheduler = AsyncIOScheduler()
logger = logging.getLogger(__name__)

# -------------------------
# LLM 分析模块（抽象化）
# -------------------------
async def llm_call_async(prompt: str) -> str:
    """
    自动根据环境变量选择使用 OpenAI 或 SiliconFlow。
    prompt: 完整文本提示
    return: 模型返回的文本结果
    """

    # 优先使用 SiliconFlow
    if USE_SILICONFLOW and SILICONFLOW_API_KEY:
        try:
            async with httpx.AsyncClient(timeout=60) as client:
                headers = {
                    "Content-Type": "application/json",
                    "Authorization": f"Bearer {SILICONFLOW_API_KEY}"
                }
                payload = {
                    "model": "Qwen/Qwen2.5-72B-Instruct",  # 推荐模型（中文能力强）
                    "messages": [
                        {"role": "system", "content": "你是一位专业的量化交易分析师，只依据技术面判断市场。"},
                        {"role": "user", "content": prompt}
                    ],
                    "temperature": 0.1,
                    "max_tokens": 1024,
                }
                resp = await client.post(
                    "https://api.siliconflow.cn/v1/chat/completions",
                    json=payload,
                    headers=headers
                )
                resp.raise_for_status()
                data = resp.json()
                return data["choices"][0]["message"]["content"]
        except Exception as e:
            logger.warning(f"[SiliconFlow] 请求失败，回退到 OpenAI: {e}")

    # 默认使用 OpenAI
    if not OPENAI_API_KEY:
        raise RuntimeError("缺少 OPENAI_API_KEY 或 SILICONFLOW_API_KEY")

    client = AsyncOpenAI(api_key=OPENAI_API_KEY)
    try:
        resp = await client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "你是一位专业的量化交易分析师，只依据技术面判断市场。"},
                {"role": "user", "content": prompt}
            ],
            temperature=0.1
        )
        return resp.choices[0].message.content
    except Exception as e:
        logger.error(f"[OpenAI] 调用失败: {e}")
        raise

async def analyze_with_llm(signal_data: dict, kline_data: list) -> dict:
    """
    把 signal 和最近 K 线打包成 prompt 给 LLM，让 LLM 判断：
     - 是否在支撑位
     - 是否处于上升趋势
     - 是否推荐交易（简短理由）
    返回字典：
      {
        "llm_raw": "...",
        "llm_decision": "recommend"|"reject"|"uncertain",
        "llm_reason": "..."
      }
    """

    prompt = f"""
你是一个严格基于技术面的专业交易分析师（只使用下面给出的 K 线数据和信号），不要引入外部基本面或新闻因素。
同时你的交易系统为追随趋势交易，当锤子线或者看涨吞没信号在支撑位或者上涨趋势结构中出现时做多，当倒锤子线或看跌吞没信号出现在阻力位或者下降趋势结构时做空。
信号JSON:
{signal_data}

最近120根K线（列：timestamp,open,high,low,close,volume），时间按 UTC：
{kline_data}



请回答以下问题：
1) 信号是否满足交易系统: 是/否（如果是，请说明信号处于什么位置）；
2) 信号是否与趋势方向一致: Up/Down/Sideways（请简要说明）；
3) 信号是否值得入场操作: Recommend/Reject（请说明推荐或拒绝的理由）。
"""

    llm_text = await llm_call_async(prompt)
    # 这里做最小解析：尽量抽取关键关键词；更复杂的解析可按需增强
    # 将 llm_text 返回给上层，让调用方决定如何解读
    return {
        "llm_raw": llm_text,
        "llm_decision": "recommend" if "推荐" in llm_text or "Recommend" in llm_text.splitlines()[2] else "uncertain",
    }



async def scan_all_symbols():
    for item in MONITOR_SYMBOLS:
        if item["market"] == "binance":
            try:
                df = fetch_klines_by_market(
                    market=item["market"],
                    symbol=item["symbol"],
                    interval=item["interval"],
                    limit=120
                )
                rsi = calculate_rsi(df)
                hammer_signal = get_hammer_signal(df, rsi.iloc[-2])
                inverted_hammer_signal = get_inverted_hammer_signal(df, rsi.iloc[-2])
                bearish_engulfing_signal = get_bearish_engulfing_signal(df, rsi.iloc[-2])
                bullish_engulfing_signal = get_bullish_engulfing_signal(df, rsi.iloc[-2])

                if hammer_signal is not None and hammer_signal["signal"]:
                    logger.info(f"[SIGNAL] {item['symbol']} 检测到hammer结构: {hammer_signal}")
                    llm_result = await analyze_with_llm(hammer_signal, df)
                    logger.info("=== LLM 原始分析 ===")
                    logger.info(json.dumps(llm_result, indent=2, ensure_ascii=False))

                elif inverted_hammer_signal is not None and inverted_hammer_signal["signal"]:
                    logger.info(f"[SIGNAL] {item['symbol']} 检测到inverted_hammer结构: {inverted_hammer_signal}")
                    llm_result = await analyze_with_llm(inverted_hammer_signal, df)
                    logger.info("=== LLM 原始分析 ===")
                    logger.info(json.dumps(llm_result, indent=2, ensure_ascii=False))
                elif bearish_engulfing_signal is not None and bearish_engulfing_signal["signal"]:
                    logger.info(f"[SIGNAL] {item['symbol']} 检测到bearish_engulfing结构: {bearish_engulfing_signal}")
                    llm_result = await analyze_with_llm(bearish_engulfing_signal, df)
                    logger.info("=== LLM 原始分析 ===")
                    logger.info(json.dumps(llm_result, indent=2, ensure_ascii=False))
                elif bullish_engulfing_signal is not None and bullish_engulfing_signal["signal"]:
                    logger.info(f"[SIGNAL] {item['symbol']} 检测到bullish_engulfing结构: {bullish_engulfing_signal}")
                    llm_result = await analyze_with_llm(bullish_engulfing_signal, df)
                    logger.info("=== LLM 原始分析 ===")
                    logger.info(json.dumps(llm_result, indent=2, ensure_ascii=False))
                else:
                    logger.info(f"[NO SIGNAL] for {item['symbol']}")
            except Exception as e:
                logger.info(f"[ERROR] 获取 {item['symbol']} 数据失败: {e}")

async def scan_test_symbols():

    signal_data = {
        "symbol": "BTCUSDT",
        "interval": "4h",
        "signal_type": "hammer",
        "type": "long",
        "timestamp": "2025-10-20T12:01:00",
        "entry_price": 108436.2,
        "stop_loss": 107350.1,
        "take_profit": 110608.4,
        "tp_mult": 2,
        "rsi": 34.21
    }
    df = fetch_klines_by_market('binance','BTCUSDT','4h', limit=120)
    llm_result = await analyze_with_llm(signal_data, df)
    print("=== LLM 原始分析 ===")
    print(json.dumps(llm_result, indent=2, ensure_ascii=False))



def start_scheduler():
    if not scheduler.running:
        scheduler.add_job(scan_test_symbols,
                          "cron",
                          minute="*/15",
                          timezone="UTC")
        scheduler.start()
        # scheduler.add_job(scan_all_symbols,
        #                   "cron",
        #                   minute=55,
        #                   hour="*/1",
        #                   timezone="UTC")
        # scheduler.start()