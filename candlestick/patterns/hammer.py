from candlestick.patterns.candlestick_finder import CandlestickFinder


class Hammer(CandlestickFinder):
    def __init__(self, target=None):
        super().__init__(self.get_class_name(), 1, target=target)

    def logic(self, idx):
        candle = self.data.iloc[idx]

        # close = candle[self.close_column]
        # open = candle[self.open_column]
        # high = candle[self.high_column]
        # low = candle[self.low_column]
        # return (((high - low) > 3 * (open - close)) and
        #         ((close - low) / (.001 + high - low) > 0.6) and
        #         ((open - low) / (.001 + high - low) > 0.6))

        # 方法1
        # close = candle[self.close_column]
        # open_ = candle[self.open_column]
        # high = candle[self.high_column]
        # low = candle[self.low_column]
        #
        # body = abs(close - open_)
        # candle_range = high - low
        # upper_shadow = high - max(close, open_)
        # lower_shadow = min(close, open_) - low
        #
        # if candle_range == 0:
        #     return False  # 避免除以0错误
        #
        # return (
        #         body <= candle_range * 0.3 and  # 实体在30%以内
        #         lower_shadow > candle_range * 0.6 and  # 下影线占比 > 60%
        #         upper_shadow < candle_range * 0.1  # 上影线占比 < 10%
        # )

        #  方法2
        open_price = candle[self.open_column]
        close_price = candle[self.close_column]
        high = candle[self.high_column]
        low = candle[self.low_column]
        body = abs(close_price - open_price)
        upper_shadow = high - max(open_price, close_price)
        lower_shadow = min(open_price, close_price) - low
        total_range = high - low

        # 判断逻辑更严格，排除 Doji 和上影线太长的情况
        is_hammer = (
                body > 0.001 and  # 实体必须有大小，避免Doji
                lower_shadow >= 1.8 * body and  # 下影线至少是实体1.7倍
                upper_shadow <= body and # 上影线不应比实体长
                upper_shadow < total_range * 0.2  # 上影线占实体比 < 20%
        )

        return is_hammer


