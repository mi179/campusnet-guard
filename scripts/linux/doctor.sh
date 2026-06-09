#!/bin/bash
# CampusNet Guard — Linux 诊断脚本
# 用法: bash scripts/linux/doctor.sh

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_DIR="$(cd "$SCRIPT_DIR/../.." && pwd)"

cd "$PROJECT_DIR"

if [ -f ".venv/bin/activate" ]; then
    source .venv/bin/activate
fi

cyber-lobster doctor
