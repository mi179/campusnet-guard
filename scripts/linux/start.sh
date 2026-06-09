#!/bin/bash
# CampusNet Guard — Linux 启动守护脚本
# 用法: bash scripts/linux/start.sh
# 可选参数: bash scripts/linux/start.sh --interval 30

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_DIR="$(cd "$SCRIPT_DIR/../.." && pwd)"

cd "$PROJECT_DIR"

if [ -f ".venv/bin/activate" ]; then
    source .venv/bin/activate
fi

exec cyber-lobster start "$@"
