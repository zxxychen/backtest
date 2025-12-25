import yfinance as yf

# 测试股票代码
symbol = '600628'

print(f"测试股票代码: {symbol}")

# 测试不同后缀
suffixes = ['.SS', '.SZ']

for suffix in suffixes:
    full_symbol = symbol + suffix
    print(f"\n尝试 {full_symbol}:")
    
    try:
        stock = yf.Ticker(full_symbol)
        
        # 测试获取历史数据，使用当前年份的范围
        print("获取历史数据...")
        df = stock.history(period='1y')
        print(f"历史数据形状: {df.shape}")
        print(f"数据是否为空: {df.empty}")
        
        if not df.empty:
            print(f"最近5条数据:")
            print(df.tail())
        
        # 测试获取info
        print("\n获取股票信息...")
        try:
            info = stock.info
            print(f"股票名称: {info.get('longName', '未知')}")
            print(f"交易所: {info.get('exchange', '未知')}")
        except Exception as e:
            print(f"获取info失败: {e}")
            
    except Exception as e:
        print(f"发生错误: {e}")
