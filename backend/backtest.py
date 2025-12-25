import numpy as np
import pandas as pd
from datetime import datetime
from strategy.strategies import STRATEGY_MAP

class BacktestEngine:
    """
    回测引擎类，负责执行交易策略回测
    """
    
    def __init__(self, data_provider):
        """
        初始化回测引擎
        
        参数:
            data_provider: 数据提供者实例
        """
        self.data_provider = data_provider
    
    def run_backtest(self, symbol, strategy_name, params, initial_cash=100000, commission=0.001):
        """
        执行回测
        
        参数:
            symbol (str): 股票代码
            strategy_name (str): 策略名称
            params (dict): 策略参数
            initial_cash (float): 初始资金
            commission (float): 交易佣金比例
            
        返回:
            dict: 回测结果
        """
        try:
            # 获取股票数据
            start_date, end_date = self.data_provider.get_default_date_range()
            stock_data = self.data_provider.get_stock_data(symbol, start_date, end_date)
            
            # 转换为DataFrame以便计算
            df = pd.DataFrame(stock_data['data'])
            df['date'] = pd.to_datetime(df['date'])
            df.set_index('date', inplace=True)
            
            # 根据策略名称选择策略
            if strategy_name not in STRATEGY_MAP:
                raise ValueError(f"不支持的策略: {strategy_name}")
            
            # 执行策略
            signals = STRATEGY_MAP[strategy_name](df, params)
            
            # 执行回测
            results = self._execute_backtest(df, signals, initial_cash, commission)
            
            # 计算性能指标
            metrics = self._calculate_metrics(results['equity_curve'], results['total_trades'])
            
            # 构建回测结果
            backtest_results = {
                'symbol': symbol,
                'strategy': strategy_name,
                'params': params,
                'initial_cash': initial_cash,
                'commission': commission,
                'start_date': start_date,
                'end_date': end_date,
                'metrics': metrics,
                'trades': results['trades'],
                'equity_curve': results['equity_curve']
            }
            
            return backtest_results
            
        except Exception as e:
            raise Exception(f"回测执行失败: {str(e)}")
    
    def _execute_backtest(self, df, signals, initial_cash, commission):
        """
        执行回测交易
        
        参数:
            df (DataFrame): 股票数据
            signals (DataFrame): 信号数据
            initial_cash (float): 初始资金
            commission (float): 交易佣金比例
            
        返回:
            dict: 包含交易记录和权益曲线的字典
        """
        # 初始化回测变量
        cash = initial_cash
        shares = 0
        equity = initial_cash
        trades = []
        equity_curve = []
        
        # 遍历每个交易日
        for date, row in signals.iterrows():
            # 记录当前权益
            equity = cash + shares * row['close']
            equity_curve.append({
                'date': date.strftime('%Y-%m-%d'),
                'equity': equity
            })
            
            # 检查是否有交易信号
            if row['position'] == 1:  # 买入信号
                # 计算可购买的股票数量
                buy_price = row['close']
                max_shares = int(cash / (buy_price * (1 + commission)))
                
                if max_shares > 0:
                    # 执行买入
                    amount = max_shares * buy_price
                    fee = amount * commission
                    cash -= amount + fee
                    shares += max_shares
                    
                    # 记录交易
                    trades.append({
                        'date': date.strftime('%Y-%m-%d'),
                        'type': 'buy',
                        'price': buy_price,
                        'quantity': max_shares,
                        'amount': amount,
                        'fee': fee
                    })
            
            elif row['position'] == -1:  # 卖出信号
                if shares > 0:
                    # 执行卖出
                    sell_price = row['close']
                    amount = shares * sell_price
                    fee = amount * commission
                    cash += amount - fee
                    
                    # 记录交易
                    trades.append({
                        'date': date.strftime('%Y-%m-%d'),
                        'type': 'sell',
                        'price': sell_price,
                        'quantity': shares,
                        'amount': amount,
                        'fee': fee
                    })
                    
                    shares = 0
        
        # 最后一天如果还有持仓，强制平仓
        if shares > 0 and len(df) > 0:
            last_date = df.index[-1]
            last_price = df.loc[last_date, 'close']
            amount = shares * last_price
            fee = amount * commission
            cash += amount - fee
            
            # 记录平仓交易
            trades.append({
                'date': last_date.strftime('%Y-%m-%d'),
                'type': 'sell',
                'price': last_price,
                'quantity': shares,
                'amount': amount,
                'fee': fee
            })
            
            # 更新权益曲线
            equity = cash
            equity_curve.append({
                'date': last_date.strftime('%Y-%m-%d'),
                'equity': equity
            })
        
        return {
            'trades': trades,
            'equity_curve': equity_curve,
            'total_trades': len(trades)
        }
    
    def _calculate_metrics(self, equity_curve, total_trades):
        """
        计算回测性能指标
        
        参数:
            equity_curve (list): 权益曲线数据
            total_trades (int): 实际交易次数
            
        返回:
            dict: 性能指标
        """
        # 转换为DataFrame以便计算
        df = pd.DataFrame(equity_curve)
        df['date'] = pd.to_datetime(df['date'])
        df.set_index('date', inplace=True)
        
        # 计算每日收益率
        df['daily_return'] = df['equity'].pct_change()
        
        # 计算总收益率
        total_return = (df['equity'].iloc[-1] / df['equity'].iloc[0]) - 1
        
        # 计算年化收益率
        days = (df.index[-1] - df.index[0]).days
        annual_return = (1 + total_return) ** (365 / days) - 1
        
        # 计算最大回撤
        df['cumulative_return'] = (1 + df['daily_return']).cumprod()
        df['cumulative_max'] = df['cumulative_return'].cummax()
        df['drawdown'] = (df['cumulative_return'] / df['cumulative_max']) - 1
        max_drawdown = df['drawdown'].min()
        
        # 计算夏普比率（假设无风险利率为0）
        sharpe_ratio = np.sqrt(252) * (df['daily_return'].mean() / df['daily_return'].std())
        
        # 使用实际的交易次数（传入的参数）
        # total_trades = len(df[df['daily_return'] != 0])  # 不再使用这个错误的计算方法
        
        # 计算胜率
        win_trades = len(df[df['daily_return'] > 0])
        win_rate = win_trades / total_trades if total_trades > 0 else 0
        
        # 计算平均盈利和平均亏损
        avg_profit = df[df['daily_return'] > 0]['daily_return'].mean()
        avg_loss = df[df['daily_return'] < 0]['daily_return'].mean()
        
        # 计算盈亏比
        profit_loss_ratio = abs(avg_profit / avg_loss) if avg_loss != 0 else 0
        
        # 计算最大连续盈利次数
        consecutive_wins = 0
        max_consecutive_wins = 0
        
        for _, row in df.iterrows():
            if row['daily_return'] > 0:
                consecutive_wins += 1
                max_consecutive_wins = max(max_consecutive_wins, consecutive_wins)
            else:
                consecutive_wins = 0
        
        return {
            'total_return': total_return,
            'annual_return': annual_return,
            'max_drawdown': max_drawdown,
            'sharpe_ratio': sharpe_ratio,
            'total_trades': total_trades,
            'win_rate': win_rate,
            'avg_profit': avg_profit,
            'avg_loss': avg_loss,
            'profit_loss_ratio': profit_loss_ratio,
            'max_consecutive_wins': max_consecutive_wins
        }
