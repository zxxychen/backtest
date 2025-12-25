from data_provider import DataProvider
from datetime import datetime, timedelta

# 创建数据提供者实例
dp = DataProvider()

# 测试股票代码
symbol = '600628'

print(f"测试股票代码: {symbol}")
print("=" * 50)

# 获取当前日期作为结束日期
today = datetime.now().strftime('%Y-%m-%d')
# 开始日期设为一年前
start_date = (datetime.now() - timedelta(days=365)).strftime('%Y-%m-%d')

print(f"日期范围: {start_date} 到 {today}")

# 测试get_stock_data方法
try:
    print("\n调用get_stock_data...")
    result = dp.get_stock_data(symbol, start_date, today)
    
    print("\n成功获取数据!")
    print(f"股票代码: {result['meta']['symbol']}")
    print(f"股票名称: {result['meta']['name']}")
    print(f"数据条数: {len(result['data'])}")
    print(f"数据时间范围: {result['data'][0]['date']} 到 {result['data'][-1]['date']}")
    
    # 打印前几条数据
    print("\n前5条数据:")
    for i, row in enumerate(result['data'][:5]):
        print(f"{i+1}. {row['date']} - 开:{row['open']}, 高:{row['high']}, 低:{row['low']}, 收:{row['close']}, 量:{row['volume']}")
        
except Exception as e:
    print(f"\n获取数据失败: {e}")

# 测试get_latest_price方法
try:
    print("\n调用get_latest_price...")
    price = dp.get_latest_price(symbol)
    print(f"最新价格: {price}")
    
except Exception as e:
    print(f"\n获取最新价格失败: {e}")
