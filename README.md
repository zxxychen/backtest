# 股票回测系统

这是一个完整的股票回测系统，允许用户输入股票代码，获取历史数据，并使用不同的交易策略进行回测。系统会生成详细的回测报告，包括收益率、最大回撤、胜率等关键指标。

## 系统架构

### 前端
- HTML5 + CSS3 + JavaScript
- Tailwind CSS v3 (用于UI设计)
- Chart.js (用于图表展示)
- Font Awesome (用于图标)

### 后端
- Python 3.8+
- Flask (Web框架)
- yfinance (获取股票数据)
- pandas, numpy (数据处理)
- matplotlib (图表生成)
- scipy (统计计算)

## 功能特性

### 数据查询
- 支持输入股票代码获取历史数据
- 支持选择日期范围
- 支持多种市场的股票代码格式:
  - 美股: AAPL, MSFT, GOOGL
  - 港股: 0700.HK, 0005.HK
  - A股: 600519.SS (沪市), 000858.SZ (深市)

### 回测策略
- 移动平均线交叉策略
- RSI超买超卖策略
- MACD交叉策略

### 回测报告
- 总收益率、年化收益率
- 最大回撤、夏普比率
- 胜率、盈亏比
- 交易记录明细
- 收益率曲线图表

## 安装与部署

### 本地开发环境

1. 克隆项目到本地
```bash
git clone <repository-url>
cd stock-backtest-system
```

2. 安装后端依赖
```bash
cd backend
pip install -r requirements.txt
```

3. 启动后端服务
```bash
python app.py
```

4. 访问系统
在浏览器中打开 http://localhost:5000

### 生产环境部署

1. 安装依赖
```bash
cd backend
pip install -r requirements.txt
```

2. 使用Gunicorn启动应用
```bash
gunicorn app:app -b 0.0.0.0:5000
```

3. 配置反向代理 (可选)
可以使用Nginx作为反向代理，配置SSL证书等

## 使用说明

1. 在左侧控制面板中输入股票代码，选择日期范围，点击"获取数据"按钮
2. 选择回测策略并调整相应参数
3. 设置初始资金和交易佣金
4. 点击"开始回测"按钮
5. 查看回测结果，包括图表和统计数据
6. 可以点击"导出报告"按钮导出回测结果

## 注意事项

- 本系统使用Yahoo Finance作为数据源，可能存在数据延迟或不准确的情况
- 回测结果仅供参考，不构成投资建议
- 系统默认使用模拟数据进行演示，实际部署时需要确保能够连接到Yahoo Finance API

## 故障排除

### 无法获取股票数据
- 检查股票代码是否正确
- 检查网络连接是否正常
- 确认Yahoo Finance API是否可访问

### 回测结果异常
- 检查策略参数设置是否合理
- 确认初始资金和交易佣金设置是否正确
- 尝试使用更长的历史数据进行回测

## 许可证

MIT License