import pandas as pd
import numpy as np


def ma_cross_strategy(df, params):
    """
    移动平均线交叉策略
    
    参数:
        df (DataFrame): 股票数据
        params (dict): 策略参数，包含short_period和long_period
        
    返回:
        DataFrame: 信号数据
    """
    short_period = params.get('short_period', 10)
    long_period = params.get('long_period', 50)
    
    # 计算移动平均线
    df['short_ma'] = df['close'].rolling(window=short_period).mean()
    df['long_ma'] = df['close'].rolling(window=long_period).mean()
    
    # 生成信号
    df['signal'] = 0
    df.loc[df['short_ma'] > df['long_ma'], 'signal'] = 1
    df.loc[df['short_ma'] < df['long_ma'], 'signal'] = -1
    
    # 计算信号变化（交叉点）
    df['position'] = df['signal'].diff()
    
    return df


def rsi_strategy(df, params):
    """
    RSI超买超卖策略
    
    参数:
        df (DataFrame): 股票数据
        params (dict): 策略参数，包含period、overbought和oversold
        
    返回:
        DataFrame: 信号数据
    """
    period = params.get('period', 14)
    overbought = params.get('overbought', 70)
    oversold = params.get('oversold', 30)
    
    # 计算RSI
    delta = df['close'].diff()
    gain = delta.where(delta > 0, 0)
    loss = -delta.where(delta < 0, 0)
    
    avg_gain = gain.rolling(window=period).mean()
    avg_loss = loss.rolling(window=period).mean()
    
    rs = avg_gain / avg_loss
    df['rsi'] = 100 - (100 / (1 + rs))
    
    # 生成信号
    df['signal'] = 0
    df.loc[df['rsi'] > overbought, 'signal'] = -1  # 超买卖出
    df.loc[df['rsi'] < oversold, 'signal'] = 1    # 超卖买入
    
    # 计算信号变化
    df['position'] = df['signal'].diff()
    
    return df


def macd_strategy(df, params):
    """
    MACD交叉策略
    
    参数:
        df (DataFrame): 股票数据
        params (dict): 策略参数，包含fast_period、slow_period和signal_period
        
    返回:
        DataFrame: 信号数据
    """
    fast_period = params.get('fast_period', 12)
    slow_period = params.get('slow_period', 26)
    signal_period = params.get('signal_period', 9)
    
    # 计算EMA
    ema_fast = df['close'].ewm(span=fast_period, adjust=False).mean()
    ema_slow = df['close'].ewm(span=slow_period, adjust=False).mean()
    
    # 计算MACD线和信号线
    df['macd_line'] = ema_fast - ema_slow
    df['signal_line'] = df['macd_line'].ewm(span=signal_period, adjust=False).mean()
    
    # 生成信号
    df['signal'] = 0
    df.loc[df['macd_line'] > df['signal_line'], 'signal'] = 1
    df.loc[df['macd_line'] < df['signal_line'], 'signal'] = -1
    
    # 计算信号变化
    df['position'] = df['signal'].diff()
    
    return df


def dragon_strategy(df, params):
    """
    量价时空龙战法策略 - 优化版
    改进：增加窄幅震荡持续时间要求，改进成交量萎缩判断，优化突破确认
    
    参数:
        df (DataFrame): 股票数据
        params (dict): 策略参数，包含vol_period、price_period、ma_short、ma_long、rsi_threshold、
                     consolidation_period、consolidation_threshold、vol_multiple、consolidation_min_days
        
    返回:
        DataFrame: 信号数据
    """
    # 获取参数
    vol_period = params.get('vol_period', 20)  # 成交量周期
    price_period = params.get('price_period', 20)  # 价格周期
    ma_short = params.get('ma_short', 5)  # 短期均线
    ma_long = params.get('ma_long', 20)  # 长期均线
    rsi_threshold = params.get('rsi_threshold', 50)  # RSI阈值
    vol_multiple = params.get('vol_multiple', 1.5)  # 成交量放大倍数
    consolidation_period = params.get('consolidation_period', 30)  # 窄幅震荡周期
    consolidation_threshold = params.get('consolidation_threshold', 3.0)  # 震荡幅度阈值(%)
    consolidation_min_days = params.get('consolidation_min_days', 10)  # 窄幅震荡最小持续天数
    
    # 1. 计算成交量相关指标
    df['vol_avg'] = df['volume'].rolling(window=vol_period).mean()
    df['vol_ratio'] = df['volume'] / df['vol_avg']
    
    # 2. 计算价格相关指标
    df['price_high'] = df['high'].rolling(window=price_period).max()
    df['price_low'] = df['low'].rolling(window=price_period).min()
    
    # 3. 计算均线
    df['ma_short'] = df['close'].rolling(window=ma_short).mean()
    df['ma_long'] = df['close'].rolling(window=ma_long).mean()
    
    # 4. 计算RSI
    delta = df['close'].diff()
    gain = delta.where(delta > 0, 0)
    loss = -delta.where(delta < 0, 0)
    avg_gain = gain.rolling(window=14).mean()
    avg_loss = loss.rolling(window=14).mean()
    rs = avg_gain / avg_loss
    df['rsi'] = 100 - (100 / (1 + rs))
    
    # 5. 计算窄幅震荡指标
    # 价格振幅百分比
    df['price_range'] = df['high'].rolling(window=consolidation_period).max() - df['low'].rolling(window=consolidation_period).min()
    df['price_mid'] = df['close'].rolling(window=consolidation_period).mean()
    df['price_range_pct'] = (df['price_range'] / df['price_mid']) * 100
    
    # 成交量萎缩指标 - 改进：使用更长时间的历史平均值比较
    df['vol_consolidation'] = df['volume'].rolling(window=consolidation_period).mean() / df['volume'].rolling(window=vol_period*3).mean()
    
    # 窄幅震荡条件：价格振幅小 + 成交量明显萎缩
    df['is_consolidating'] = (
        (df['price_range_pct'] < consolidation_threshold) &  # 价格振幅小于阈值
        (df['vol_consolidation'] < 0.7) &  # 成交量更明显萎缩（0.7倍以下）
        (df['volume'] < df['vol_avg'])  # 当前成交量也小于平均
    )
    
    # 6. 计算窄幅震荡持续时间 - 使用pandas向量化操作替代for循环
    df['consolidation_days'] = df['is_consolidating'].groupby((~df['is_consolidating']).cumsum()).cumcount()
    
    # 7. 生成买入信号
    # 条件：长时间窄幅震荡后 + 成交量显著放大 + 收盘价突破 + 均线多头 + RSI强势
    buy_condition = (
        (df['consolidation_days'] >= consolidation_min_days) &  # 窄幅震荡持续足够天数
        (df['vol_ratio'] > vol_multiple) &  # 成交量放大
        (df['close'] > df['price_high'].shift(1)) &  # 收盘价突破近期高点（而非盘中突破）
        (df['close'] > df['open']) &  # 突破日收阳线
        (df['ma_short'] > df['ma_long']) &  # 均线多头
        (df['rsi'] > rsi_threshold)  # RSI强势
    )
    
    # 8. 生成卖出信号
    # 条件：价格跌破短期均线且在短期均线下运行一段时间
    below_ma = df['close'] < df['ma_short']
    df['below_ma_days'] = below_ma.groupby((~below_ma).cumsum()).cumcount()
    
    sell_condition = (
        (df['below_ma_days'] >= 2) |  # 连续2天收盘价低于短期均线
        (df['rsi'] < 30)  # 或RSI超卖
    )
    
    # 9. 生成信号
    df['signal'] = 0
    
    # 只在没有持仓时买入
    in_position = False
    for i in range(len(df)):
        if buy_condition.iloc[i] and not in_position:
            df.loc[df.index[i], 'signal'] = 1
            in_position = True
        elif sell_condition.iloc[i] and in_position:
            df.loc[df.index[i], 'signal'] = -1
            in_position = False
    
    # 计算信号变化
    df['position'] = df['signal'].diff()
    
    return df


# 策略映射，用于根据策略名称获取策略函数
STRATEGY_MAP = {
    'ma_cross': ma_cross_strategy,
    'rsi': rsi_strategy,
    'macd': macd_strategy,
    'dragon': dragon_strategy
}
