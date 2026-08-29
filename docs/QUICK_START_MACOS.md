# CampusNet Guard macOS 使用说明

## 安装

1. Apple Silicon（M1/M2/M3/M4/M5）下载 `campusnet-guard-macos-apple-silicon.dmg`。
2. Intel Mac 下载 `campusnet-guard-macos-intel.dmg`。
3. 打开 DMG，将 **CampusNet Guard** 拖入 **Applications**。
4. 从“应用程序”中打开 CampusNet Guard。

## 首次打开的安全提示

当前自动构建版本没有 Apple Developer ID 公证。若 macOS 阻止打开：

1. 在 Finder 的“应用程序”中找到 CampusNet Guard。
2. 按住 Control 点击应用，选择“打开”。
3. 在确认窗口中再次选择“打开”。

请只使用 GitHub Releases 或项目官网提供的安装包，并核对对应的 SHA-256 文件。

## 使用

首次运行进入“高级”页添加账号，验证成功后回到“主页”点击“开始守护”。在“设置”页可以开启登录后自动运行。

配置默认保存在 `~/.config/cyber-lobster/config.json`，密码使用当前用户的本地密钥保护。
