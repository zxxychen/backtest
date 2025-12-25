import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta
import requests
import os
import json

class DataProvider:
    """
    数据提供者类，负责从Yahoo Finance获取股票历史数据
    """
    
    def __init__(self):
        """初始化数据提供者"""
        self.cache = {}  # 内存缓存，避免重复请求
        self.data_dir = os.path.join(os.path.dirname(__file__), 'data')  # 数据存储目录
        
        # 确保数据目录存在
        if not os.path.exists(self.data_dir):
            os.makedirs(self.data_dir)
    
    def _try_symbol_with_suffixes(self, symbol):
        """
        根据股票代码前缀自动判断所属板块并添加相应的后缀
        
        参数:
            symbol (str): 股票代码（可能不带后缀）
            
        返回:
            str: 带正确后缀的股票代码
            
        异常:
            ValueError: 如果无法判断股票代码所属板块或获取数据失败
        """
        # 如果已经带了后缀，直接返回
        if symbol.endswith('.SS') or symbol.endswith('.SZ'):
            return symbol
        
        # 只移除空格，保留股票代码的前导零
        symbol = symbol.strip()
        
        # 根据股票代码前缀判断所属板块
        prefix = symbol[:3]  # 取前三位
        
        # 沪市主板：600/601/603/605开头
        # 科创板：688开头
        # 这些都使用.SS后缀
        if (prefix.startswith('600') or prefix.startswith('601') or 
            prefix.startswith('603') or prefix.startswith('605') or 
            prefix.startswith('688')):
            suffix = '.SS'
        
        # 深圳主板：000/001/002/003开头
        # 创业板：300/301开头
        # 这些都使用.SZ后缀
        elif (prefix.startswith('000') or prefix.startswith('001') or 
              prefix.startswith('002') or prefix.startswith('003') or 
              prefix.startswith('300') or prefix.startswith('301')):
            suffix = '.SZ'
        
        # 无法判断的情况，使用原有的尝试机制
        else:
            print(f"无法根据前缀 {prefix} 判断股票 {symbol} 的所属板块，将尝试所有后缀")
            suffixes = ['.SS', '.SZ']
            
            for suffix in suffixes:
                try:
                    full_symbol = symbol + suffix
                    stock = yf.Ticker(full_symbol)
                    
                    # 使用更灵活的时间范围来判断股票代码是否有效
                    df = stock.history(period='1y')
                    
                    if not df.empty:
                        return full_symbol
                    
                    df = stock.history(period='5y')
                    
                    if not df.empty:
                        return full_symbol
                except Exception as e:
                    print(f"尝试 {full_symbol} 时出错: {str(e)}")
                    continue
            
            # 如果所有后缀都尝试失败，抛出异常
            raise ValueError(f"无法获取股票 {symbol} 的数据，请检查股票代码是否正确")
        
        # 尝试带后缀的股票代码
        full_symbol = symbol + suffix
        
        try:
            stock = yf.Ticker(full_symbol)
            
            # 验证股票代码是否有效
            df = stock.history(period='1y')
            
            if not df.empty:
                return full_symbol
            
            df = stock.history(period='5y')
            
            if not df.empty:
                return full_symbol
            
            # 如果没有历史数据，抛出异常
            raise ValueError(f"无法获取股票 {full_symbol} 的历史数据")
        
        except Exception as e:
            print(f"验证 {full_symbol} 时出错: {str(e)}")
            # 如果验证失败，尝试另一个后缀作为备选
            alt_suffix = '.SZ' if suffix == '.SS' else '.SS'
            alt_full_symbol = symbol + alt_suffix
            
            try:
                stock = yf.Ticker(alt_full_symbol)
                df = stock.history(period='1y')
                
                if not df.empty:
                    print(f"备选后缀 {alt_suffix} 验证成功")
                    return alt_full_symbol
            except Exception as alt_e:
                print(f"尝试备选后缀 {alt_suffix} 时出错: {str(alt_e)}")
            
            # 如果所有尝试都失败，抛出异常
            raise ValueError(f"无法获取股票 {symbol} 的数据，请检查股票代码是否正确")
    
    def _get_cache_file_path(self, symbol, start_date, end_date, auto_adjust):
        """
        获取缓存文件的路径
        
        参数:
            symbol (str): 股票代码
            start_date (str): 开始日期
            end_date (str): 结束日期
            auto_adjust (bool): 是否获取前复权数据
            
        返回:
            str: 缓存文件的路径
        """
        filename = f"{symbol}_{start_date}_{end_date}_{auto_adjust}.json"
        return os.path.join(self.data_dir, filename)
    
    def _is_data_up_to_date(self, cached_data, start_date, end_date):
        """
        检查缓存数据是否最新
        
        参数:
            cached_data (dict): 缓存的数据
            start_date (str): 请求的开始日期
            end_date (str): 请求的结束日期
            
        返回:
            bool: 如果数据最新返回True，否则返回False
        """
        # 检查数据的日期范围
        if not cached_data or 'data' not in cached_data or not cached_data['data']:
            return False
        
        # 获取缓存数据的最早和最晚日期
        cache_dates = [item['date'] for item in cached_data['data']]
        if not cache_dates:
            return False
        
        earliest_cache_date = min(cache_dates)
        latest_cache_date = max(cache_dates)
        
        # 检查请求的日期范围是否完全包含在缓存数据中
        if earliest_cache_date <= start_date and latest_cache_date >= end_date:
            return True
        
        return False
    
    def get_stock_data(self, symbol, start_date, end_date, auto_adjust=True):
        """
        获取股票历史数据
        
        参数:
            symbol (str): 股票代码
            start_date (str): 开始日期，格式为'YYYY-MM-DD'
            end_date (str): 结束日期，格式为'YYYY-MM-DD'
            auto_adjust (bool): 是否获取前复权数据，默认True
            
        返回:
            dict: 包含股票数据和元数据的字典
        """
        # 尝试自动添加后缀
        try:
            symbol = self._try_symbol_with_suffixes(symbol)
        except ValueError as e:
            raise e
        
        # 检查内存缓存，包含复权参数
        cache_key = f"{symbol}_{start_date}_{end_date}_{auto_adjust}"
        if cache_key in self.cache:
            return self.cache[cache_key]
        
        # 检查本地文件缓存
        cache_file = self._get_cache_file_path(symbol, start_date, end_date, auto_adjust)
        if os.path.exists(cache_file):
            try:
                with open(cache_file, 'r', encoding='utf-8') as f:
                    cached_data = json.load(f)
                
                # 检查数据是否最新
                if self._is_data_up_to_date(cached_data, start_date, end_date):
                    # 更新内存缓存
                    self.cache[cache_key] = cached_data
                    return cached_data
            except Exception as e:
                print(f"读取缓存文件失败: {str(e)}")
        
        try:
            # 使用yfinance获取数据，auto_adjust=True表示获取前复权数据
            stock = yf.Ticker(symbol)
            df = stock.history(start=start_date, end=end_date, auto_adjust=auto_adjust)
            
            # 检查数据是否为空
            if df.empty:
                raise ValueError(f"无法获取股票 {symbol} 的数据，请检查股票代码是否正确或日期范围是否合适")
            
            # 转换为所需格式
            data = []
            for index, row in df.iterrows():
                # 处理时区信息，确保日期格式正确
                date_str = index.strftime('%Y-%m-%d')
                data.append({
                    'date': date_str,
                    'open': float(row.get('Open', 0)),
                    'high': float(row.get('High', 0)),
                    'low': float(row.get('Low', 0)),
                    'close': float(row.get('Close', 0)),
                    'volume': int(row.get('Volume', 0))
                })
            
            # 获取股票元数据，添加容错处理
            meta = {
                'symbol': symbol,
                'name': symbol,  # 默认值
                'currency': 'USD',  # 默认值
                'exchange': ''  # 默认值
            }
            
            # 尝试获取股票信息，添加异常处理以避免整个请求失败
            try:
                info = stock.info
                if info is not None:
                    meta['name'] = info.get('longName', info.get('shortName', symbol))
                    meta['currency'] = info.get('currency', 'USD')
                    meta['exchange'] = info.get('exchange', '')
            except Exception as info_error:
                # 如果获取信息失败，只记录错误但不影响主流程
                print(f"获取股票 {symbol} 信息时出错: {str(info_error)}")
            
            # 构建返回结果
            result = {
                'meta': meta,
                'data': data
            }
            
            # 保存到本地文件缓存
            cache_file = self._get_cache_file_path(symbol, start_date, end_date, auto_adjust)
            try:
                with open(cache_file, 'w', encoding='utf-8') as f:
                    json.dump(result, f, indent=2, ensure_ascii=False)
            except Exception as e:
                print(f"保存缓存文件失败: {str(e)}")
            
            # 保存到内存缓存
            self.cache[cache_key] = result
            
            return result
            
        except requests.exceptions.HTTPError as http_err:
            if http_err.response.status_code == 429:
                raise Exception("请求频率过高，请稍后再试")
            raise Exception(f"网络请求错误: {str(http_err)}")
        except ValueError as val_err:
            raise val_err  # 直接传递值错误
        except Exception as e:
            raise Exception(f"获取股票数据时出错: {str(e)}")
    
    def get_latest_price(self, symbol):
        """
        获取股票最新价格
        
        参数:
            symbol (str): 股票代码
            
        返回:
            float: 最新价格
        """
        try:
            # 尝试自动添加后缀
            symbol = self._try_symbol_with_suffixes(symbol)
            stock = yf.Ticker(symbol)
            
            # 尝试获取最新价格
            latest_price = None
            
            # 方法1: 从info中获取
            try:
                info = stock.info
                latest_price = info.get('regularMarketPrice', info.get('currentPrice', None))
            except Exception as info_err:
                print(f"从info获取股票 {symbol} 最新价格失败: {str(info_err)}")
            
            # 方法2: 如果方法1失败，尝试获取最近的收盘价
            if latest_price is None:
                try:
                    df = stock.history(period='1d')
                    if not df.empty:
                        latest_price = float(df['Close'].iloc[-1])
                except Exception as history_err:
                    print(f"从历史数据获取股票 {symbol} 最新价格失败: {str(history_err)}")
            
            # 方法3: 如果还是失败，尝试获取最近5天的数据
            if latest_price is None:
                try:
                    df = stock.history(period='5d')
                    if not df.empty:
                        latest_price = float(df['Close'].iloc[-1])
                except Exception as recent_err:
                    print(f"从最近5天数据获取股票 {symbol} 最新价格失败: {str(recent_err)}")
            
            if latest_price is None:
                raise ValueError(f"无法获取股票 {symbol} 的最新价格，请检查股票代码是否正确")
            
            return float(latest_price)
            
        except requests.exceptions.HTTPError as http_err:
            if http_err.response.status_code == 429:
                raise Exception("请求频率过高，请稍后再试")
            raise Exception(f"网络请求错误: {str(http_err)}")
        except ValueError as val_err:
            raise val_err
        except Exception as e:
            raise Exception(f"获取最新价格时出错: {str(e)}")
    
    def get_default_date_range(self, years=5):
        """
        获取默认日期范围（从当前日期向前推指定年数）
        
        参数:
            years (int): 年数
            
        返回:
            tuple: (start_date, end_date)，格式为('YYYY-MM-DD', 'YYYY-MM-DD')
        """
        end_date = datetime.now()
        start_date = end_date - timedelta(days=365 * years)
        
        return (start_date.strftime('%Y-%m-%d'), end_date.strftime('%Y-%m-%d'))