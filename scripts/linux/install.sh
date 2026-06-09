#!/bin/bash
# CampusNet Guard — Linux 安装脚本
# 用法: bash scripts/linux/install.sh

set -e

echo "=== CampusNet Guard 安装 ==="

# 1. 检查 python3
if ! command -v python3 &>/dev/null; then
    echo "[错误] 未找到 python3，请先安装 Python 3.10+"
    echo "  Ubuntu/Debian: sudo apt install python3 python3-venv python3-pip"
    echo "  Fedora:        sudo dnf install python3 python3-venv python3-pip"
    echo "  Arch:          sudo pacman -S python python-pip"
    exit 1
fi

PYTHON_VERSION=$(python3 -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')")
echo "[信息] Python 版本: $PYTHON_VERSION"

# 2. 检查版本
MAJOR=$(python3 -c "import sys; print(sys.version_info.major)")
MINOR=$(python3 -c "import sys; print(sys.version_info.minor)")
if [ "$MAJOR" -lt 3 ] || ([ "$MAJOR" -eq 3 ] && [ "$MINOR" -lt 10 ]); then
    echo "[错误] 需要 Python 3.10+，当前版本 $PYTHON_VERSION"
    exit 1
fi

# 3. 创建虚拟环境
if [ ! -d ".venv" ]; then
    echo "[信息] 创建虚拟环境..."
    python3 -m venv .venv
else
    echo "[信息] 虚拟环境已存在"
fi

# 4. 激活并安装
echo "[信息] 安装依赖..."
.venv/bin/pip install --upgrade pip -q
.venv/bin/pip install -e . -q

echo ""
echo "=== 安装完成 ==="
echo ""
echo "下一步:"
echo "  source .venv/bin/activate"
echo "  cyber-lobster setup      # 添加账号"
echo "  cyber-lobster start      # 启动守护"
echo "  cyber-lobster doctor     # 诊断"
