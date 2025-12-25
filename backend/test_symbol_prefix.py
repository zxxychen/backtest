from data_provider import DataProvider
from datetime import datetime, timedelta

# 创建数据提供者实例
dp = DataProvider()

# 获取当前日期作为结束日期
today = datetime.now().strftime('%Y-%m-%d')
# 开始日期设为一年前
start_date = (datetime.now() - timedelta(days=365)).strftime('%Y-%m-%d')

# 测试用例：股票代码前缀 -> 预期后缀
# 沪市主板
sh_main_board = [
    ('600519', '.SS'),  # 贵州茅台
    ('601398', '.SS'),  # 工商银行
    ('603288', '.SS'),  # 海天味业
    ('605001', '.SS'),  # 威奥股份
]

# 科创板
star_market = [
    ('688001', '.SS'),  # 华兴源创
]

# 深圳主板
sz_main_board = [
    ('000001', '.SZ'),  # 平安银行
    ('001234', '.SZ'),  # 泰慕士
    ('002415', '.SZ'),  # 海康威视
    ('003000', '.SZ'),  # 小熊电器
]

# 创业板
gem_board = [
    ('300059', '.SZ'),  # 东方财富
    ('301000', '.SZ'),  # 肇民科技
]

# 测试函数
def test_symbol_prefix(stock_list, board_name):
    print(f"\n{'='*60}")
    print(f"测试 {board_name} 股票代码前缀")
    print(f"{'='*60}")
    
    success_count = 0
    total_count = len(stock_list)
    
    for symbol, expected_suffix in stock_list:
        try:
            print(f"\n测试股票代码: {symbol}")
            print(f"预期后缀: {expected_suffix}")
            
            # 测试_try_symbol_with_suffixes方法
            result_symbol = dp._try_symbol_with_suffixes(symbol)
            print(f"实际后缀: {result_symbol[len(symbol):]}")
            
            # 验证后缀是否正确
            if result_symbol.endswith(expected_suffix):
                print("✓ 后缀判断正确")
            else:
                print(f"✗ 后缀判断错误: 预期 {expected_suffix}, 实际 {result_symbol[len(symbol):]}")
            
            # 测试实际获取数据
            print("获取股票数据...")
            result = dp.get_stock_data(symbol, start_date, today)
            print(f"✓ 成功获取数据: {result['meta']['symbol']} - {result['meta']['name']}")
            print(f"数据条数: {len(result['data'])}")
            
            success_count += 1
            
        except Exception as e:
            print(f"✗ 测试失败: {e}")
    
    print(f"\n{'='*60}")
    print(f"{board_name} 测试结果: {success_count}/{total_count} 成功")
    print(f"{'='*60}")
    return success_count, total_count

# 运行所有测试
print("股票代码前缀自动判断测试")
print(f"测试日期范围: {start_date} 到 {today}")

# 沪市主板测试
test_symbol_prefix(sh_main_board, "沪市主板")

# 科创板测试
test_symbol_prefix(star_market, "科创板")

# 深圳主板测试
test_symbol_prefix(sz_main_board, "深圳主板")

# 创业板测试
test_symbol_prefix(gem_board, "创业板")
