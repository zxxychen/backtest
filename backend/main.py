import argparse
import numpy as np
import pandas as pd
from datetime import datetime
import os
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from data_provider import DataProvider
from backtest import BacktestEngine

def plot_results(stock_data, backtest_results):
    """
    绘制回测结果
    
    参数:
        stock_data: 股票数据
        backtest_results: 回测结果
    """
    # 转换数据格式
    df = pd.DataFrame(stock_data['data'])
    df['date'] = pd.to_datetime(df['date'])
    
    equity_df = pd.DataFrame(backtest_results['equity_curve'])
    equity_df['date'] = pd.to_datetime(equity_df['date'])
    
    # 计算10日、20日、60日移动平均线
    df['MA10'] = df['close'].rolling(window=10).mean()
    df['MA20'] = df['close'].rolling(window=20).mean()
    df['MA60'] = df['close'].rolling(window=60).mean()
    
    # 创建子图
    fig = make_subplots(
        rows=4, cols=1,
        shared_xaxes=True,
        vertical_spacing=0.1,
        subplot_titles=(f'{stock_data["meta"]["name"]} ({stock_data["meta"]["symbol"]}) - K线图',
                       '成交量',
                       '回测权益曲线',
                       '交易记录'),
        specs=[
            [{'type': 'candlestick'}],
            [{'type': 'bar'}],
            [{'type': 'scatter'}],
            [{'type': 'table'}]
        ]
    )
    
    # 1. K线图
    # 区分涨跌
    up = df[df.close >= df.open]
    down = df[df.close < df.open]
    
    # 绘制蜡烛图
    fig.add_trace(
        go.Candlestick(
            x=df['date'],
            open=df['open'],
            high=df['high'],
            low=df['low'],
            close=df['close'],
            name='K线',
            increasing=dict(line=dict(color='red')),
            decreasing=dict(line=dict(color='green'))
        ),
        row=1, col=1
    )
    
    # 添加移动平均线
    fig.add_trace(
        go.Scatter(
            x=df['date'],
            y=df['MA10'],
            mode='lines',
            name='MA10',
            line=dict(color='blue', width=1)
        ),
        row=1, col=1
    )
    
    fig.add_trace(
        go.Scatter(
            x=df['date'],
            y=df['MA20'],
            mode='lines',
            name='MA20',
            line=dict(color='orange', width=1)
        ),
        row=1, col=1
    )
    
    fig.add_trace(
        go.Scatter(
            x=df['date'],
            y=df['MA60'],
            mode='lines',
            name='MA60',
            line=dict(color='green', width=1)
        ),
        row=1, col=1
    )
    
    # 添加买卖点标注
    trades = backtest_results['trades']
    if trades:
        # 提取买入点
        buy_dates = [pd.to_datetime(trade['date']) for trade in trades if trade['type'] == 'buy']
        buy_prices = [trade['price'] for trade in trades if trade['type'] == 'buy']
        
        # 提取卖出点
        sell_dates = [pd.to_datetime(trade['date']) for trade in trades if trade['type'] == 'sell']
        sell_prices = [trade['price'] for trade in trades if trade['type'] == 'sell']
        
        # 添加买入点标记
        fig.add_trace(
            go.Scatter(
                x=buy_dates,
                y=buy_prices,
                mode='markers',
                name='买入点',
                marker=dict(
                    symbol='triangle-up',
                    size=10,
                    color='red',
                    line=dict(width=1, color='black')
                ),
                hovertemplate='买入日期: %{x}<br>买入价格: %{y:.2f}<extra></extra>'
            ),
            row=1, col=1
        )
        
        # 添加卖出点标记
        fig.add_trace(
            go.Scatter(
                x=sell_dates,
                y=sell_prices,
                mode='markers',
                name='卖出点',
                marker=dict(
                    symbol='triangle-down',
                    size=10,
                    color='green',
                    line=dict(width=1, color='black')
                ),
                hovertemplate='卖出日期: %{x}<br>卖出价格: %{y:.2f}<extra></extra>'
            ),
            row=1, col=1
        )
    
    # 设置K线图布局
    fig.update_yaxes(title_text="价格", row=1, col=1)
    
    # 2. 成交量图
    fig.add_trace(
        go.Bar(
            x=up['date'],
            y=up['volume'],
            name='上涨成交量',
            marker_color='red'
        ),
        row=2, col=1
    )
    
    fig.add_trace(
        go.Bar(
            x=down['date'],
            y=down['volume'],
            name='下跌成交量',
            marker_color='green'
        ),
        row=2, col=1
    )
    
    fig.update_yaxes(title_text="成交量", row=2, col=1)
    
    # 3. 权益曲线图
    fig.add_trace(
        go.Scatter(
            x=equity_df['date'],
            y=equity_df['equity'],
            mode='lines',
            name='权益曲线',
            line=dict(color='blue', width=2)
        ),
        row=3, col=1
    )
    
    fig.update_yaxes(title_text="权益金额", row=3, col=1)
    fig.update_xaxes(title_text="日期", row=3, col=1)
    
    # 4. 交易记录表
    trades = backtest_results['trades']
    if trades:
        # 准备表格数据
        table_headers = ['买入日期', '买入价格', '卖出日期', '卖出价格', '数量', '买入金额', '卖出金额', '收益']
        table_data = []
        trade_colors = []
        
        # 将交易记录配对（买入和卖出）
        i = 0
        while i < len(trades):
            # 找到买入记录
            if trades[i]['type'] == 'buy':
                buy_trade = trades[i]
                # 寻找下一个卖出记录
                sell_trade = None
                for j in range(i+1, len(trades)):
                    if trades[j]['type'] == 'sell':
                        sell_trade = trades[j]
                        i = j + 1  # 跳过已配对的卖出记录
                        break
                
                if sell_trade:
                    # 计算收益
                    buy_total = buy_trade['amount'] + buy_trade['fee']
                    sell_total = sell_trade['amount'] - sell_trade['fee']
                    profit = sell_total - buy_total
                    profit_percent = (profit / buy_total) * 100
                    
                    # 格式化数据
                    table_data.append([
                        buy_trade['date'],
                        f"{buy_trade['price']:.2f}",
                        sell_trade['date'],
                        f"{sell_trade['price']:.2f}",
                        buy_trade['quantity'],
                        f"{buy_total:.2f}",
                        f"{sell_total:.2f}",
                        f"{profit:.2f} ({profit_percent:.2f}%)"
                    ])
                    
                    # 设置收益颜色（正收益红色，负收益绿色）
                    trade_colors.append(['#ffffff', '#ffffff', '#ffffff', '#ffffff', '#ffffff', '#ffffff', '#ffffff', '#ff0000' if profit > 0 else '#00ff00'])
                else:
                    i += 1  # 没有找到对应的卖出记录，继续下一个
            else:
                i += 1  # 跳过单独的卖出记录
        
        # 如果有未配对的交易记录，单独显示
        if i < len(trades):
            # 显示未完成的交易
            unpaired_header = ['日期', '类型', '价格', '数量', '金额', '佣金', '状态']
            unpaired_data = []
            for trade in trades[i:]:
                unpaired_data.append([
                    trade['date'],
                    trade['type'],
                    f"{trade['price']:.2f}",
                    trade['quantity'],
                    f"{trade['amount']:.2f}",
                    f"{trade['fee']:.2f}",
                    '未完成'
                ])
            
            # 创建组合表格数据
            combined_headers = table_headers + [''] * (7 - len(table_headers))
            combined_data = []
            for data in table_data:
                combined_data.append(data + [''] * (7 - len(data)))
            combined_data.append([''] * 7)  # 空行分隔
            combined_data.append(['未完成的交易记录'] + [''] * 6)  # 标题行
            for data in unpaired_data:
                combined_data.append(data)
            
            # 添加表格
            fig.add_trace(
                go.Table(
                    header=dict(
                        values=combined_headers,
                        fill_color='lightgrey',
                        align='left',
                        font=dict(size=12, color='black')
                    ),
                    cells=dict(
                        values=list(zip(*combined_data)),
                        fill_color=['#f5f5f5', '#ffffff'] * len(combined_data),
                        align='left',
                        font=dict(size=11, color='black')
                    )
                ),
                row=4, col=1
            )
        else:
            # 添加配对后的表格
            fig.add_trace(
                go.Table(
                    header=dict(
                        values=table_headers,
                        fill_color='lightgrey',
                        align='left',
                        font=dict(size=12, color='black')
                    ),
                    cells=dict(
                        values=list(zip(*table_data)),
                        fill_color=trade_colors,
                        align='left',
                        font=dict(size=11, color='black')
                    )
                ),
                row=4, col=1
            )
    else:
        # 如果没有交易记录，使用表格组件显示提示信息
        fig.add_trace(
            go.Table(
                header=dict(
                    values=['交易记录'],
                    fill_color='lightgrey',
                    align='center',
                    font=dict(size=12, color='black')
                ),
                cells=dict(
                    values=[['没有交易记录']],
                    fill_color='white',
                    align='center',
                    font=dict(size=14, color='black')
                )
            ),
            row=4, col=1
        )
    
    # 设置整体布局
    fig.update_layout(
        height=1200,  # 增加高度以容纳表格
        width=1200,
        title_text=f"回测结果 - 策略: {backtest_results['strategy']}, 参数: {backtest_results['params']}",
        showlegend=True,
        hovermode='x unified',
        dragmode='zoom',  # 默认为缩放模式
        xaxis_rangeslider_visible=False  # 隐藏底部的范围滑块
    )
    
    # 设置所有子图的X轴和Y轴在缩放时自适应
    for i in range(1, 4):
        fig.update_xaxes(autorange=True, row=i, col=1)
        
        # 对于Y轴，使用更灵活的自动缩放设置
        if i == 1:  # K线图
            fig.update_yaxes(
                autorange=True, 
                row=i, col=1,
                fixedrange=False,  # 允许手动调整范围
                tickformat='.2f'   # 价格保留两位小数
            )
        elif i == 2:  # 成交量图
            fig.update_yaxes(
                autorange=True, 
                row=i, col=1,
                fixedrange=False,
                tickformat='.0f'   # 成交量保留整数
            )
        else:  # 权益曲线图
            fig.update_yaxes(
                autorange=True, 
                row=i, col=1,
                fixedrange=False,
                tickformat='.2f'   # 金额保留两位小数
            )
    
    # 保存图表为HTML文件
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    filename = f"backtest_result_{backtest_results['symbol']}_{backtest_results['strategy']}_{timestamp}.html"
    filepath = os.path.join(os.path.dirname(__file__), filename)
    fig.write_html(filepath)
    
    return filepath

def main():
    """
    主函数，用于运行回测并显示结果
    """
    # 设置命令行参数
    parser = argparse.ArgumentParser(description='股票回测系统')
    parser.add_argument('--symbol', type=str, default='600519', help='股票代码')
    parser.add_argument('--strategy', type=str, default='ma_cross', choices=['ma_cross', 'rsi', 'macd', 'dragon'], help='回测策略')
    parser.add_argument('--initial_cash', type=float, default=100000.0, help='初始资金')
    parser.add_argument('--commission', type=float, default=0.001, help='交易佣金比例')
    parser.add_argument('--interactive', action='store_true', help='启用交互式输入')
    
    args = parser.parse_args()
    
    print("=" * 60)
    print("股票回测系统")
    print("=" * 60)
    
    # 1. 获取股票代码
    if args.interactive:
        symbol = input("请输入股票代码: ").strip()
    else:
        symbol = args.symbol
        print(f"使用默认股票代码: {symbol}")
    
    # 2. 选择回测策略
    if args.interactive:
        print("\n可用策略:")
        print("1. 移动平均线交叉策略 (ma_cross)")
        print("2. RSI超买超卖策略 (rsi)")
        print("3. MACD交叉策略 (macd)")
        print("4. 量价时空龙战法 (dragon)")
        
        strategy_choice = input("请选择策略 (1-4): ").strip()
        
        # 映射策略选择
        strategy_map = {
            '1': 'ma_cross',
            '2': 'rsi',
            '3': 'macd',
            '4': 'dragon'
        }
        
        if strategy_choice not in strategy_map:
            print("无效的策略选择")
            return
        
        strategy_name = strategy_map[strategy_choice]
    else:
        strategy_name = args.strategy
        print(f"使用默认策略: {strategy_name}")
    
    # 3. 设置策略参数
    params = {}
    
    if strategy_name == 'ma_cross':
        if args.interactive:
            print("\n移动平均线交叉策略参数:")
            short_period = int(input("短期均线周期 (默认10): ") or "10")
            long_period = int(input("长期均线周期 (默认50): ") or "50")
        else:
            short_period = 10
            long_period = 50
            print(f"使用默认参数: 短期均线={short_period}, 长期均线={long_period}")
        params = {'short_period': short_period, 'long_period': long_period}
    elif strategy_name == 'rsi':
        if args.interactive:
            print("\nRSI策略参数:")
            period = int(input("RSI周期 (默认14): ") or "14")
            overbought = int(input("超买阈值 (默认70): ") or "70")
            oversold = int(input("超卖阈值 (默认30): ") or "30")
        else:
            period = 14
            overbought = 70
            oversold = 30
            print(f"使用默认参数: 周期={period}, 超买阈值={overbought}, 超卖阈值={oversold}")
        params = {'period': period, 'overbought': overbought, 'oversold': oversold}
    elif strategy_name == 'macd':
        if args.interactive:
            print("\nMACD策略参数:")
            fast_period = int(input("快速EMA周期 (默认12): ") or "12")
            slow_period = int(input("慢速EMA周期 (默认26): ") or "26")
            signal_period = int(input("信号EMA周期 (默认9): ") or "9")
        else:
            fast_period = 12
            slow_period = 26
            signal_period = 9
            print(f"使用默认参数: 快速EMA={fast_period}, 慢速EMA={slow_period}, 信号EMA={signal_period}")
        params = {'fast_period': fast_period, 'slow_period': slow_period, 'signal_period': signal_period}
    elif strategy_name == 'dragon':
        if args.interactive:
            print("\n量价时空龙战法参数:")
            vol_period = int(input("成交量周期 (默认20): ") or "20")
            price_period = int(input("价格周期 (默认20): ") or "20")
            ma_short = int(input("短期均线 (默认5): ") or "5")
            ma_long = int(input("长期均线 (默认20): ") or "20")
            rsi_threshold = int(input("RSI阈值 (默认50): ") or "50")
            vol_multiple = float(input("成交量放大倍数 (默认1.5): ") or "1.5")
        else:
            vol_period = 20
            price_period = 20
            ma_short = 5
            ma_long = 20
            rsi_threshold = 50
            vol_multiple = 1.5
            print(f"使用默认参数: 成交量周期={vol_period}, 价格周期={price_period}, 短期均线={ma_short}, 长期均线={ma_long}, RSI阈值={rsi_threshold}, 成交量放大倍数={vol_multiple}")
        params = {'vol_period': vol_period, 'price_period': price_period, 'ma_short': ma_short, 'ma_long': ma_long, 'rsi_threshold': rsi_threshold, 'vol_multiple': vol_multiple}
    
    # 4. 设置回测参数
    if args.interactive:
        print("\n回测参数:")
        initial_cash = float(input("初始资金 (默认100000): ") or "100000")
        commission = float(input("交易佣金比例 (默认0.001): ") or "0.001")
    else:
        initial_cash = args.initial_cash
        commission = args.commission
        print(f"使用默认回测参数: 初始资金={initial_cash}, 交易佣金={commission}")
    
    print("\n正在初始化回测...")
    
    try:
        # 5. 初始化数据提供者和回测引擎
        data_provider = DataProvider()
        backtest_engine = BacktestEngine(data_provider)
        
        # 6. 获取股票数据
        print(f"\n正在获取 {symbol} 的股票数据...")
        start_date, end_date = data_provider.get_default_date_range(years=5)
        stock_data = data_provider.get_stock_data(symbol, start_date, end_date)
        
        print(f"获取数据成功！时间范围: {start_date} 至 {end_date}")
        print(f"数据条数: {len(stock_data['data'])}")
        
        # 7. 运行回测
        print("\n正在运行回测...")
        backtest_results = backtest_engine.run_backtest(
            symbol=symbol,
            strategy_name=strategy_name,
            params=params,
            initial_cash=initial_cash,
            commission=commission
        )
        
        # 8. 打印回测结果
        print("\n" + "=" * 60)
        print("回测结果")
        print("=" * 60)
        
        metrics = backtest_results['metrics']
        
        print(f"\n基本信息:")
        print(f"股票代码: {backtest_results['symbol']}")
        print(f"策略: {backtest_results['strategy']}")
        print(f"参数: {backtest_results['params']}")
        print(f"初始资金: {backtest_results['initial_cash']:.2f}")
        print(f"交易佣金: {backtest_results['commission']:.3f}")
        print(f"回测周期: {backtest_results['start_date']} 至 {backtest_results['end_date']}")
        
        print(f"\n性能指标:")
        # 总收益率
        total_return = metrics['total_return']
        if total_return > 0:
            print(f"总收益率: \033[31m{total_return:.2%}\033[0m")
        elif total_return < 0:
            print(f"总收益率: \033[32m{total_return:.2%}\033[0m")
        else:
            print(f"总收益率: {total_return:.2%}")
        
        # 年化收益率
        annual_return = metrics['annual_return']
        if annual_return > 0:
            print(f"年化收益率: \033[31m{annual_return:.2%}\033[0m")
        elif annual_return < 0:
            print(f"年化收益率: \033[32m{annual_return:.2%}\033[0m")
        else:
            print(f"年化收益率: {annual_return:.2%}")
        
        # 最大回撤
        max_drawdown = metrics['max_drawdown']
        if max_drawdown > 0:
            print(f"最大回撤: \033[31m{max_drawdown:.2%}\033[0m")
        elif max_drawdown < 0:
            print(f"最大回撤: \033[32m{max_drawdown:.2%}\033[0m")
        else:
            print(f"最大回撤: {max_drawdown:.2%}")
        
        print(f"夏普比率: {metrics['sharpe_ratio']:.2f}")
        print(f"总交易次数: {metrics['total_trades']}")
        
        # 胜率
        win_rate = metrics['win_rate']
        if win_rate > 0.5:
            print(f"胜率: \033[31m{win_rate:.2%}\033[0m")
        elif win_rate < 0.5:
            print(f"胜率: \033[32m{win_rate:.2%}\033[0m")
        else:
            print(f"胜率: {win_rate:.2%}")
        
        # 平均盈利
        avg_profit = metrics['avg_profit']
        if not pd.isna(avg_profit) and avg_profit > 0:
            print(f"平均盈利: \033[31m{avg_profit:.2%}\033[0m")
        else:
            print(f"平均盈利: {avg_profit:.2%}")
        
        # 平均亏损
        avg_loss = metrics['avg_loss']
        if not pd.isna(avg_loss) and avg_loss < 0:
            print(f"平均亏损: \033[32m{avg_loss:.2%}\033[0m")
        else:
            print(f"平均亏损: {avg_loss:.2%}")
        
        print(f"盈亏比: {metrics['profit_loss_ratio']:.2f}")
        print(f"最大连续盈利次数: {metrics['max_consecutive_wins']}")
        
        # 计算最终权益
        equity_curve = backtest_results['equity_curve']
        final_equity = equity_curve[-1]['equity'] if equity_curve else initial_cash
        print(f"\n最终权益: {final_equity:.2f}")
        
        # 9. 绘制并保存图表
        print("\n正在生成回测图表...")
        chart_file = plot_results(stock_data, backtest_results)
        print(f"图表已保存至: {chart_file}")
        
        # 10. 打印交易记录
        print("\n" + "=" * 60)
        print("交易记录")
        print("=" * 60)
        
        trades = backtest_results['trades']
        if trades:
            print(f"{'日期':<12} {'类型':<6} {'价格':<10} {'数量':<10} {'金额':<12} {'佣金':<10}")
            print("-" * 60)
            
            for trade in trades:
                print(f"{trade['date']:<12} {trade['type']:<6} {trade['price']:<10.2f} {trade['quantity']:<10} {trade['amount']:<12.2f} {trade['fee']:<10.2f}")
        else:
            print("没有交易记录")
            
        print("\n" + "=" * 60)
        print("回测完成！")
        print("=" * 60)
        
    except Exception as e:
        print(f"\n回测失败: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    main()
