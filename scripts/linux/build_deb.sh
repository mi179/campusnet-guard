#!/bin/bash
# Build a native, architecture-independent Debian package.

set -euo pipefail

ROOT_DIR=$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)
OUTPUT_DIR=${1:-"$ROOT_DIR/dist"}
PACKAGE_NAME=campusnet-guard
VERSION=$(awk '$1 == "version" && $2 == "=" { gsub(/"/, "", $3); print $3; exit }' "$ROOT_DIR/pyproject.toml")

if [ -z "$VERSION" ]; then
    echo "[ERROR] 无法从 pyproject.toml 读取版本号" >&2
    exit 1
fi

if ! command -v dpkg-deb >/dev/null 2>&1; then
    echo "[ERROR] 未找到 dpkg-deb，请先安装 dpkg-dev" >&2
    exit 1
fi

BUILD_DIR=$(mktemp -d)
PACKAGE_ROOT="$BUILD_DIR/$PACKAGE_NAME"
trap 'rm -rf "$BUILD_DIR"' EXIT

install -d \
    "$PACKAGE_ROOT/DEBIAN" \
    "$PACKAGE_ROOT/usr/bin" \
    "$PACKAGE_ROOT/usr/lib/python3/dist-packages/cyber_lobster" \
    "$PACKAGE_ROOT/usr/lib/systemd/user" \
    "$PACKAGE_ROOT/usr/share/applications" \
    "$PACKAGE_ROOT/usr/share/icons/hicolor/scalable/apps" \
    "$PACKAGE_ROOT/usr/share/doc/$PACKAGE_NAME"

install -m 0644 \
    "$ROOT_DIR"/src/cyber_lobster/*.py \
    "$PACKAGE_ROOT/usr/lib/python3/dist-packages/cyber_lobster/"

install -m 0755 /dev/stdin "$PACKAGE_ROOT/usr/bin/campusnet" <<'EOF'
#!/usr/bin/python3
from cyber_lobster.cli import main

raise SystemExit(main())
EOF

ln -s campusnet "$PACKAGE_ROOT/usr/bin/campusnet-guard"
ln -s campusnet "$PACKAGE_ROOT/usr/bin/cyber-lobster"

install -m 0755 /dev/stdin "$PACKAGE_ROOT/usr/bin/campusnet-gui" <<'EOF'
#!/usr/bin/python3
from cyber_lobster.gui import main

raise SystemExit(main())
EOF

ln -s campusnet-gui "$PACKAGE_ROOT/usr/bin/campusnet-guard-gui"
ln -s campusnet-gui "$PACKAGE_ROOT/usr/bin/cyber-lobster-gui"

install -m 0644 /dev/stdin "$PACKAGE_ROOT/usr/share/applications/campusnet-guard.desktop" <<'EOF'
[Desktop Entry]
Type=Application
Name=CampusNet Guard
Name[zh_CN]=校园网守护
Comment=Campus network auto-login and reconnect tool
Comment[zh_CN]=校园网自动认证与断网重连工具
Exec=campusnet-gui
Icon=campusnet-guard
Terminal=false
Categories=Network;
Keywords=campus;network;ePortal;校园网;认证;
StartupNotify=true
EOF

install -m 0644 \
    "$ROOT_DIR/assets/campusnet-guard.svg" \
    "$PACKAGE_ROOT/usr/share/icons/hicolor/scalable/apps/campusnet-guard.svg"

install -m 0644 /dev/stdin "$PACKAGE_ROOT/usr/lib/systemd/user/campusnet-guard.service" <<'EOF'
[Unit]
Description=CampusNet Guard 校园网自动认证守护
After=network-online.target

[Service]
Type=simple
ExecStart=/usr/bin/campusnet start --interval 10
Restart=on-failure
RestartSec=30

[Install]
WantedBy=default.target
EOF

install -m 0644 "$ROOT_DIR/LICENSE" "$PACKAGE_ROOT/usr/share/doc/$PACKAGE_NAME/copyright"
install -m 0644 "$ROOT_DIR/README.md" "$PACKAGE_ROOT/usr/share/doc/$PACKAGE_NAME/README.md"
install -m 0644 "$ROOT_DIR/docs/LINUX_USAGE.md" "$PACKAGE_ROOT/usr/share/doc/$PACKAGE_NAME/LINUX_USAGE.md"

BUILD_EPOCH=${SOURCE_DATE_EPOCH:-$(git -C "$ROOT_DIR" log -1 --format=%ct 2>/dev/null || date +%s)}
CHANGELOG_DATE=$(date --utc --date="@$BUILD_EPOCH" --rfc-email)
install -m 0644 /dev/stdin "$PACKAGE_ROOT/usr/share/doc/$PACKAGE_NAME/changelog.Debian" <<EOF
$PACKAGE_NAME ($VERSION) unstable; urgency=medium

  * Build CampusNet Guard $VERSION Debian package.

 -- mi179 <noreply@github.com>  $CHANGELOG_DATE
EOF
gzip -9n "$PACKAGE_ROOT/usr/share/doc/$PACKAGE_NAME/changelog.Debian"

INSTALLED_SIZE=$(du -sk "$PACKAGE_ROOT/usr" | cut -f1)
install -m 0644 /dev/stdin "$PACKAGE_ROOT/DEBIAN/control" <<EOF
Package: $PACKAGE_NAME
Version: $VERSION
Section: net
Priority: optional
Architecture: all
Maintainer: mi179 <noreply@github.com>
Installed-Size: $INSTALLED_SIZE
Depends: python3 (>= 3.10), python3-requests, python3-tk
Homepage: https://github.com/mi179/campusnet-guard
Description: Ruijie ePortal campus network auto-login and reconnect tool
 CampusNet Guard provides a desktop GUI, an interactive CLI, and a background
 watcher for automatic campus network authentication and reconnection.
EOF

find "$PACKAGE_ROOT" -type d -exec chmod 0755 {} +
mkdir -p "$OUTPUT_DIR"
OUTPUT_FILE="$OUTPUT_DIR/${PACKAGE_NAME}_${VERSION}_all.deb"

dpkg-deb --root-owner-group --build "$PACKAGE_ROOT" "$OUTPUT_FILE"

STABLE_OUTPUT="$OUTPUT_DIR/${PACKAGE_NAME}_all.deb"
install -m 0644 "$OUTPUT_FILE" "$STABLE_OUTPUT"
(
    cd "$OUTPUT_DIR"
    sha256sum "$(basename "$OUTPUT_FILE")" >"$(basename "$OUTPUT_FILE").sha256"
    sha256sum "$(basename "$STABLE_OUTPUT")" >"$(basename "$STABLE_OUTPUT").sha256"
)

echo "[OK] $OUTPUT_FILE"
echo "[OK] $STABLE_OUTPUT"
