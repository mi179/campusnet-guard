#!/bin/bash
# Download and install the latest CampusNet Guard Debian package.

set -euo pipefail

PACKAGE_URL=${CAMPUSNET_GUARD_DEB_URL:-https://github.com/mi179/campusnet-guard/releases/latest/download/campusnet-guard_all.deb}
WORK_DIR=$(mktemp -d -t campusnet-guard-install.XXXXXX)
DEB_FILE="$WORK_DIR/$(basename "${PACKAGE_URL%%\?*}")"
trap 'rm -rf "$WORK_DIR"' EXIT

if ! command -v apt-get >/dev/null 2>&1 || ! command -v dpkg-deb >/dev/null 2>&1; then
    echo "[错误] 此安装脚本仅支持 Debian、Ubuntu 及其衍生系统。" >&2
    exit 1
fi

if [ "$(id -u)" -eq 0 ]; then
    SUDO=()
elif command -v sudo >/dev/null 2>&1; then
    SUDO=(sudo)
else
    echo "[错误] 安装软件包需要 root 权限，但系统中没有 sudo。" >&2
    exit 1
fi

chmod 0755 "$WORK_DIR"
echo "[信息] 正在下载 $PACKAGE_URL"
if command -v curl >/dev/null 2>&1; then
    curl --fail --location --show-error --silent "$PACKAGE_URL" --output "$DEB_FILE"
elif command -v wget >/dev/null 2>&1; then
    wget --quiet --output-document="$DEB_FILE" "$PACKAGE_URL"
else
    echo "[错误] 需要 curl 或 wget 才能下载安装包。" >&2
    exit 1
fi
chmod 0644 "$DEB_FILE"

if [ "$(dpkg-deb --field "$DEB_FILE" Package)" != "campusnet-guard" ]; then
    echo "[错误] 下载的文件不是有效的 CampusNet Guard 软件包。" >&2
    exit 1
fi

VERSION=$(dpkg-deb --field "$DEB_FILE" Version)
echo "[信息] 已下载 CampusNet Guard $VERSION"

CHECKSUM_URL="${PACKAGE_URL}.sha256"
CHECKSUM_FILE="$WORK_DIR/$(basename "$DEB_FILE").sha256"
if command -v curl >/dev/null 2>&1 && curl --fail --location --show-error --silent "$CHECKSUM_URL" --output "$CHECKSUM_FILE"; then
    (cd "$WORK_DIR" && sha256sum --check "$(basename "$CHECKSUM_FILE")")
elif command -v wget >/dev/null 2>&1 && wget --quiet --output-document="$CHECKSUM_FILE" "$CHECKSUM_URL"; then
    (cd "$WORK_DIR" && sha256sum --check "$(basename "$CHECKSUM_FILE")")
else
    echo "[提示] 发布页未提供校验文件，跳过 SHA-256 校验。"
fi

if [ "${CAMPUSNET_GUARD_DRY_RUN:-0}" = "1" ]; then
    echo "[完成] 下载、包元数据和校验和验证通过（未执行安装）。"
    exit 0
fi

echo "[信息] 正在通过 APT 安装（会自动安装图形界面依赖）..."
"${SUDO[@]}" apt-get install -y "$DEB_FILE"

echo
echo "[完成] CampusNet Guard $VERSION 已安装。"
echo "       从应用菜单搜索: 校园网守护，或运行: campusnet-gui"
