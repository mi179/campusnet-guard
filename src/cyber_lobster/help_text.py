"""内置帮助文档。"""

USER_GUIDE = """CampusNet Guard 帮助
========================================

普通用户怎么用
----------------------------------------
最简单方式：双击“1-点我启动-校园网守护.exe”。

图形界面里：
1. 第一次使用会进入"高级"页，点击"添加账号"
2. 输入运营商、学号、密码，点击"保存并验证"
3. 回到"主页"，点击"开始守护"

想无感使用：
打开"设置"页，勾选"开机后自动运行并守护校园网"。
下次开机后程序会自动读取账号配置、检测网络；配置正常时直接进入守护，配置缺失时才弹出窗口提醒你处理。

主页只负责日常使用：
  开始守护    开启断网自动重连
  停止守护    暂停自动重连
  注销下线    主动退出校园网登录
  检测网络    只检查外网状态，不会登录账号

高级页才管理账号：
  添加账号    第一次使用或换密码时用
  设为当前    多账号用户切换账号时用
  测试登录    排查账号或密码是否正确时用
  删除账号    清理不用的账号

如果你使用命令行版本（campusnet 是推荐入口，cyber-lobster 仍兼容）：
1. 第一次使用:
   campusnet setup

2. 开始自动重连:
   campusnet start

3. 看当前账号:
   campusnet list

4. 验证账号是否能登录:
   campusnet verify

5. 出问题时先诊断:
   campusnet doctor

6. 开机自动守护:
   campusnet autostart enable
   campusnet autostart
   campusnet autostart disable

账号和密码保存在哪里
----------------------------------------
账号信息默认保存在当前 Windows 用户的数据目录，不会保存在 EXE 所在目录。

Windows 默认位置:
  %APPDATA%\\cyber-lobster\\config.json

Linux 默认位置:
  ~/.config/cyber-lobster/config.json

密码不会明文保存。Windows 下使用 DPAPI 保护，只能由当前 Windows 用户读取。

自定义保存位置
----------------------------------------
普通用户不需要改。高级用户可以运行:

  campusnet storage
  campusnet storage D:\\MyData\\cyber-lobster

恢复默认位置:

  campusnet storage --reset

常见问题
----------------------------------------
Q: 换电脑后配置文件能直接用吗？
A: 账号配置可以复制，但 Windows DPAPI 保护的密码不能跨用户/跨电脑解密。
   换电脑后运行 campusnet setup 重新输入密码即可。

Q: 程序放到桌面、下载目录、U盘，会不会影响账号信息？
A: 不会。默认账号信息和程序位置分离。

Q: 开了代理、VPN 或 TUN 模式，需要先关掉吗？
A: 不一定。程序会尽量让校园网认证请求直连认证服务器，不走环境代理。
   如果仍然登录失败，先运行 campusnet doctor，看"代理/VPN 兼容性"提示。
   普通用户可以先临时暂停代理/VPN/TUN 后重试；高级用户可以把认证服务器地址加入直连规则。

Q: 我只想双击 EXE 使用，可以吗？
A: 可以。双击“1-点我启动-校园网守护.exe”，日常只需要看"主页"。
"""


def print_user_guide() -> None:
    print(USER_GUIDE)
