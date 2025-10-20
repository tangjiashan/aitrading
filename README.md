# 说明
> 这是一个基于纯裸k的AI交易助手，面向加密／数字资产自动信号检测K线，并将K线发给LLM分析，由LLM自动识别潜在交易机会并触发通知。

# 项目架构
```
┌───────────────────────┐
│ 配置（MONITOR_SYMBOLS）│
└───────────┬───────────┘
            │
            ▼
┌───────────────────────┐
│ 定时调度模块（Scheduler）│
│ 每15min/1h/4h触发 → scan_all_symbols │
└───────────┬───────────┘
            │
            ▼
┌─────────────────────────────────────────────┐
│ 市场数据获取模块（services.market）           │
│ fetch_klines_by_market(symbol, interval, limit)│
└───────────┬────────────────────────────────────┘
            │
            ▼
┌───────────────────────────────────────────────────────────────────────┐
│ 指标 /形态检测模块（services.indicators）                            │
│ calculate_rsi, get_hammer_signal, get_inverted_hammer_signal,        │
│ get_bearish_engulfing_signal, find_support_resistance, is_near_level │
└───────────┬─────────────────────────────────────────────────────────────┘
            │
            ▼
┌───────────────────────────────┐
│ 信号触发判断（如果检测到形态）     │
│ → 调用 analyze_with_llm(...) 或 notify 通知模块 │
└───────────┬───────────────────────┘
            │
            ▼
┌───────────────────────────────────────────────┐
│ LLM 分析模块（llm_call_async + analyze_with_llm） │
│ 使用 prompt + K线 + 信号数据 → 得出结构化分析结果           │
└───────────┬───────────────────────────────────────────────┘
            │
            ▼
┌───────────────────────────────┐
│ 通知模块（Webhook／Discord／Dify）         │
│ notify_dify(symbol, interval, data)       │
└───────────────────────────────┘


```


## 核心功能包括：
- 定时扫描选定交易对（symbols）及时间周期（intervals）  
- 获取历史 K 线数据、计算指标（如 RSI）  
- 检测经典技术形态（锤子线、倒锤子线、吞没形态等）  
- 判断是否触发交易信号  
- 使用大语言模型（LLM）进一步分析信号是否处于支撑／趋势结构中  
- 将符合条件的信号通过 Webhook（如 Discord／Dify）推送给用户  

> ⚠️ 本项目仅作为技术演示用途，不构成投资建议。请谨慎使用。

## 架构概览  
1. **配置模块**：在 `core/config.py` 中定义需监控的 symbols、intervals、扫描频率等。  
2. **调度模块**：使用 APScheduler 定时触发 scan 函数，按计划执行数据拉取与信号检测。  
3. **市场数据模块**：`services.market` 提供 fetch_klines_by_market 接口，用于拉取历史 OHLCV 数据。  
4. **指标／形态模块**：`services.indicators` 中实现 RSI 计算、支撑／阻力识别、形态检测（如锤子线、吞没）。  
5. **信号触发模块**：组合检测结果判断是否触发信号，并将信号数据推入下一步。  
6. **LLM 分析模块**：`llm_call_async` 及 `analyze_with_llm` 用于将信号与 K 线数据构造 prompt 提交大语言模型分析，输出结构化建议。  
7. **通知模块**：`notify_dify()` 或 其他 Webhook 方式将最终信号推送给用户／机器人。  

# 快速开始  
## 前提  
- Python 3.9 及以上  
- 安装依赖：  
  ```bash
  pip install -r requirements.txt

- 配置环境变量（可通过 .env 文件）：
```
OPENAI_API_KEY=sk-xxxxxx        # （可选）OpenAI API Key  
SILICONFLOW_API_KEY=sk-xxxxxx   # （可选）国产 LLM Key  
USE_SILICONFLOW=true            # 是否优先使用 SiliconFlow  
DISCORD_WEBHOOK_URL=https://…   # 通知 Webhook URL  

```
- 在 core/config.py 中编辑你要监控的交易对，例如：
```
MONITOR_SYMBOLS = [
    {"market": "binance", "symbol": "BTCUSDT", "interval": "4h"},
    {"market": "binance", "symbol": "ETHUSDT", "interval": "1h"},
]
```
- 启动扫描任务
python main.py   

# 自定义与扩展

- 添加新形态检测：在 services.indicators 中实现新函数（如 double top、breakout 等），并在主流程中接入。
- 调整 LLM Prompt 逻辑：可以修改 analyze_with_llm() 中的 prompt 模板，加入更多上下文或策略规则。
- 下单执行：目前系统主要触发通知。如需自动下单，可在通知模块后接入交易所 API（如 Binance 、 Interactive Brokers 等）。
- 回测支持：可将拉取的历史 K 线数据导入 Back-testing 模块，实现信号回测。

# 注意事项 & 风险提示

> 本系统为辅助工具，不保证盈利。市场存在高度风险。
> 使用 LLM 分析时，请谨慎控制请求频率、避免 429 错误。
> 一定要对你的 API Key、Webhook URL、交易所 API Secret 等敏感信息保密。
> 如果使用真实交易，请务必做好资金管理、风控逻辑、模拟测试。
