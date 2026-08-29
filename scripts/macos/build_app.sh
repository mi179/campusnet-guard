#!/bin/bash
# Build native CampusNet Guard macOS GUI packages on the current architecture.

set -euo pipefail

if [ "$(uname -s)" != "Darwin" ]; then
    echo "[ERROR] macOS 应用只能在 macOS 或 GitHub macOS Runner 上构建。" >&2
    exit 1
fi

ROOT_DIR=$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)
PYTHON_BIN=${PYTHON_BIN:-python3}
VERSION=$(awk '$1 == "version" && $2 == "=" { gsub(/"/, "", $3); print $3; exit }' "$ROOT_DIR/pyproject.toml")
MACHINE=$(uname -m)

case "$MACHINE" in
    arm64) ARCH_LABEL=apple-silicon ;;
    x86_64) ARCH_LABEL=intel ;;
    *)
        echo "[ERROR] 不支持的 macOS 架构: $MACHINE" >&2
        exit 1
        ;;
esac

if [ -z "$VERSION" ]; then
    echo "[ERROR] 无法从 pyproject.toml 读取版本号" >&2
    exit 1
fi

for tool in iconutil hdiutil codesign ditto; do
    if ! command -v "$tool" >/dev/null 2>&1; then
        echo "[ERROR] 未找到 macOS 构建工具: $tool" >&2
        exit 1
    fi
done

BUILD_DIR="$ROOT_DIR/build/macos-$ARCH_LABEL"
PACKAGE_DIR="$BUILD_DIR/package"
PYINSTALLER_DIST="$BUILD_DIR/pyinstaller-dist"
ICON_FILE="$BUILD_DIR/CampusNet Guard.icns"
APP_PATH="$ROOT_DIR/dist/CampusNet Guard.app"
DMG_PATH="$ROOT_DIR/dist/campusnet-guard-macos-$ARCH_LABEL.dmg"
ZIP_PATH="$ROOT_DIR/dist/campusnet-guard-macos-$ARCH_LABEL.zip"

rm -rf "$BUILD_DIR" "$APP_PATH"
rm -f "$DMG_PATH" "$ZIP_PATH" "$DMG_PATH.sha256" "$ZIP_PATH.sha256"
mkdir -p "$BUILD_DIR" "$ROOT_DIR/dist"

"$PYTHON_BIN" "$ROOT_DIR/scripts/macos/create_icns.py" \
    "$ROOT_DIR/assets/campusnet-guard.svg" \
    "$ICON_FILE"

"$PYTHON_BIN" -m PyInstaller \
    --noconfirm \
    --clean \
    --windowed \
    --name "CampusNet Guard" \
    --icon "$ICON_FILE" \
    --osx-bundle-identifier "blog.journeymind.campusnet-guard" \
    --paths "$ROOT_DIR/src" \
    --collect-submodules cyber_lobster \
    --hidden-import tkinter \
    --hidden-import tkinter.ttk \
    --hidden-import requests \
    --distpath "$PYINSTALLER_DIST" \
    --workpath "$BUILD_DIR/pyinstaller-work" \
    --specpath "$BUILD_DIR" \
    "$ROOT_DIR/gui_main.py"

ditto "$PYINSTALLER_DIST/CampusNet Guard.app" "$APP_PATH"

PLIST="$APP_PATH/Contents/Info.plist"
set_plist_string() {
    local key=$1
    local value=$2
    /usr/libexec/PlistBuddy -c "Set :$key $value" "$PLIST" 2>/dev/null || \
        /usr/libexec/PlistBuddy -c "Add :$key string $value" "$PLIST"
}
set_plist_string CFBundleShortVersionString "$VERSION"
set_plist_string CFBundleVersion "$VERSION"
set_plist_string CFBundleDisplayName "CampusNet Guard"
set_plist_string LSMinimumSystemVersion "12.0"

codesign --force --deep --sign - "$APP_PATH"
codesign --verify --deep --strict "$APP_PATH"
plutil -lint "$PLIST"
test -x "$APP_PATH/Contents/MacOS/CampusNet Guard"

mkdir -p "$PACKAGE_DIR"
ditto "$APP_PATH" "$PACKAGE_DIR/CampusNet Guard.app"
ln -s /Applications "$PACKAGE_DIR/Applications"
install -m 0644 "$ROOT_DIR/docs/QUICK_START_MACOS.md" "$PACKAGE_DIR/使用说明.md"

hdiutil create \
    -volname "CampusNet Guard" \
    -srcfolder "$PACKAGE_DIR" \
    -format UDZO \
    -ov \
    "$DMG_PATH"
ditto -c -k --sequesterRsrc --keepParent "$APP_PATH" "$ZIP_PATH"

(
    cd "$ROOT_DIR/dist"
    shasum -a 256 "$(basename "$DMG_PATH")" >"$(basename "$DMG_PATH").sha256"
    shasum -a 256 "$(basename "$ZIP_PATH")" >"$(basename "$ZIP_PATH").sha256"
)

echo "[OK] CampusNet Guard $VERSION ($ARCH_LABEL)"
echo "[OK] $DMG_PATH"
echo "[OK] $ZIP_PATH"
