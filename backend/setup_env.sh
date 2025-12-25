#!/bin/bash

# 虚拟环境设置脚本
# 用于创建venv并安装requirements.txt中的所有依赖

echo "=== 开始设置虚拟环境 ==="

# 检查Python是否安装
if ! command -v python3 &> /dev/null; then
    echo "❌ 错误: Python 3 未安装"
    exit 1
fi

# 设置变量
VENV_DIR="venv"
REQUIREMENTS_FILE="requirements.txt"

# 检查虚拟环境是否已存在
if [ -d "$VENV_DIR" ]; then
    echo "⚠️  警告: 虚拟环境 $VENV_DIR 已存在"
    echo "是否删除并重新创建？(y/n)"
    read -r response
    if [[ "$response" =~ ^[Yy]$ ]]; then
        echo "正在删除现有虚拟环境..."
        rm -rf "$VENV_DIR"
    else
        echo "跳过创建虚拟环境"
        # 激活现有虚拟环境
        if [ -f "$VENV_DIR/bin/activate" ]; then
            echo "正在激活现有虚拟环境..."
            source "$VENV_DIR/bin/activate"
        else
            echo "❌ 错误: 虚拟环境激活脚本不存在"
            exit 1
        fi
        # 跳转到安装依赖部分
    fi
fi

# 创建虚拟环境
echo "正在创建虚拟环境 $VENV_DIR..."
python3 -m venv "$VENV_DIR"

if [ $? -ne 0 ]; then
    echo "❌ 错误: 创建虚拟环境失败"
    exit 1
fi

# 激活虚拟环境
echo "正在激活虚拟环境..."
source "$VENV_DIR/bin/activate"

# 升级pip
echo "正在升级pip..."
pip install --upgrade pip

# 安装依赖
echo "正在安装依赖（来自 $REQUIREMENTS_FILE）..."

if [ ! -f "$REQUIREMENTS_FILE" ]; then
    echo "❌ 错误: $REQUIREMENTS_FILE 不存在"
    exit 1
fi

pip install -r "$REQUIREMENTS_FILE"

if [ $? -ne 0 ]; then
    echo "❌ 错误: 安装依赖失败"
    exit 1
fi

echo "✅ 虚拟环境设置完成！"
echo ""
echo "使用说明："
echo "1. 激活虚拟环境：source $VENV_DIR/bin/activate"
echo "2. 退出虚拟环境：deactivate"
echo ""
echo "=== 设置结束 ==="