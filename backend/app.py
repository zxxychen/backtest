from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import os
from data_provider import DataProvider
from backtest import BacktestEngine

# 创建Flask应用
app = Flask(__name__, static_folder='../frontend')
CORS(app)  # 启用CORS，允许跨域请求

# 初始化数据提供者和回测引擎
data_provider = DataProvider()
backtest_engine = BacktestEngine(data_provider)

# API路由：获取股票数据
@app.route('/api/stock_data', methods=['GET'])
def get_stock_data():
    try:
        # 获取请求参数
        symbol = request.args.get('symbol', '').upper()
        start_date = request.args.get('start_date', '')
        end_date = request.args.get('end_date', '')
        auto_adjust = request.args.get('auto_adjust', 'true').lower() == 'true'  # 默认获取前复权数据
        
        # 验证参数
        if not symbol:
            return jsonify({'error': '股票代码不能为空'}), 400
        
        # 如果没有提供日期范围，使用默认值
        if not start_date or not end_date:
            start_date, end_date = data_provider.get_default_date_range()
        
        # 获取股票数据
        data = data_provider.get_stock_data(symbol, start_date, end_date, auto_adjust)
        
        return jsonify(data)
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# API路由：执行回测
@app.route('/api/backtest', methods=['POST'])
def run_backtest():
    try:
        # 获取请求数据
        data = request.get_json()
        
        # 验证必要参数
        if not data:
            return jsonify({'error': '请求数据不能为空'}), 400
        
        symbol = data.get('symbol', '').upper()
        if not symbol:
            return jsonify({'error': '股票代码不能为空'}), 400
        
        strategy = data.get('strategy', '')
        if not strategy:
            return jsonify({'error': '策略名称不能为空'}), 400
        
        # 获取可选参数
        params = data.get('params', {})
        initial_cash = float(data.get('initial_cash', 100000))
        commission = float(data.get('commission', 0.001))
        
        # 执行回测
        results = backtest_engine.run_backtest(
            symbol=symbol,
            strategy_name=strategy,
            params=params,
            initial_cash=initial_cash,
            commission=commission
        )
        
        return jsonify(results)
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# 静态文件路由
@app.route('/')
def serve_index():
    return send_from_directory(app.static_folder, 'index.html')

@app.route('/<path:path>')
def serve_static(path):
    return send_from_directory(app.static_folder, path)

# 主函数
if __name__ == '__main__':
    # 获取端口号，默认为5000
    port = int(os.environ.get('PORT', 5000))
    
    # 启动应用
    app.run(host='0.0.0.0', port=port, debug=True)