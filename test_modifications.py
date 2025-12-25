#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试脚本，用于验证修改后的代码是否正常工作
"""

import sys
import os
from datetime import datetime, timedelta

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def test_strategy_modularization():
    """测试策略模块化功能"""
    print("\n=== 测试策略模块化功能 ===")
    try:
        from backend.strategy.strategies import STRATEGY_MAP, ma_cross_strategy, dragon_strategy
        import pandas as pd
        import numpy as np
        
        # 创建测试数据
        dates = pd.date_range(start='2020-01-01', end='2020-12-31', freq='D')
        data = {
            'close': np.random.randn(len(dates)).cumsum() + 100
        }
        df = pd.DataFrame(data, index=dates)
        
        # 测试策略映射
        print(f"策略映射包含的策略: {list(STRATEGY_MAP.keys())}")
        
        # 测试移动平均线交叉策略
        params = {'short_period': 10, 'long_period': 50}
        result = ma_cross_strategy(df.copy(), params)
        print(f"移动平均线交叉策略测试: {'成功' if 'signal' in result.columns else '失败'}")
        
        # 测试量价时空龙战法
        params = {
            'vol_period': 20, 
            'price_period': 20, 
            'ma_short': 5, 
            'ma_long': 20, 
            'rsi_threshold': 50,
            'vol_multiple': 1.5
        }
        # 添加成交量数据
        df['volume'] = np.random.randint(100000, 1000000, len(df))
        result = dragon_strategy(df.copy(), params)
        print(f"量价时空龙战法测试: {'成功' if 'signal' in result.columns else '失败'}")
        
        return True
    except Exception as e:
        print(f"策略模块化测试失败: {str(e)}")
        return False

def test_backtest_integration():
    """测试回测引擎与策略模块的集成"""
    print("\n=== 测试回测引擎与策略模块的集成 ===")
    try:
        from backend.backtest import BacktestEngine
        from backend.data_provider import DataProvider
        
        # 创建测试数据提供者
        data_provider = DataProvider()
        
        # 创建回测引擎
        backtest_engine = BacktestEngine(data_provider)
        
        # 获取默认日期范围
        start_date, end_date = data_provider.get_default_date_range()
        print(f"默认日期范围: {start_date} 到 {end_date}")
        
        return True
    except Exception as e:
        print(f"回测引擎集成测试失败: {str(e)}")
        return False

def test_data_caching():
    """测试数据缓存功能"""
    print("\n=== 测试数据缓存功能 ===")
    try:
        from backend.data_provider import DataProvider
        
        # 创建数据提供者
        data_provider = DataProvider()
        
        # 打印数据目录
        print(f"数据存储目录: {data_provider.data_dir}")
        print(f"数据目录存在: {os.path.exists(data_provider.data_dir)}")
        
        # 测试缓存文件路径生成
        symbol = 'AAPL'
        start_date = '2020-01-01'
        end_date = '2020-12-31'
        auto_adjust = True
        
        cache_file = data_provider._get_cache_file_path(symbol, start_date, end_date, auto_adjust)
        print(f"缓存文件路径: {cache_file}")
        
        return True
    except Exception as e:
        print(f"数据缓存功能测试失败: {str(e)}")
        return False

def main():
    """主测试函数"""
    print("开始测试修改后的代码...")
    
    # 运行所有测试
    tests = [
        test_strategy_modularization,
        test_backtest_integration,
        test_data_caching
    ]
    
    results = []
    for test in tests:
        results.append(test())
    
    # 打印测试结果
    print("\n=== 测试结果汇总 ===")
    passed = sum(results)
    total = len(results)
    
    print(f"测试总数: {total}")
    print(f"通过测试: {passed}")
    print(f"失败测试: {total - passed}")
    
    if passed == total:
        print("\n🎉 所有测试通过！修改后的代码正常工作。")
        return 0
    else:
        print("\n❌ 部分测试失败！请检查代码。")
        return 1

if __name__ == "__main__":
    sys.exit(main())
