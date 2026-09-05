<div align="center">

# 🛡️ CampusNet Guard

**English** | [简体中文](README.zh.md)

**Campus network auto-login and reconnect tool for Ruijie ePortal environments**

[![Python](https://img.shields.io/badge/Python-3.10%2B-blue)](https://python.org)
[![License](https://img.shields.io/badge/License-MIT-green)](LICENSE)
[![Platform](https://img.shields.io/badge/Platform-Windows%20%7C%20Linux%20%7C%20macOS-lightgrey)]()
[![Official Site](https://img.shields.io/badge/Official-Site-blue)](https://campusnet.journeymind.blog)

</div>

---

## In one sentence

CampusNet Guard is a campus-network auto-authentication and reconnect-on-dropout tool for Ruijie ePortal, covering dorms, classrooms, labs, offices, libraries, server rooms, NAS boxes, software routers, and mini PCs — anywhere you need to stay online on the campus network.

## Product name and command names

| Name | Notes |
|------|------|
| **CampusNet Guard** | Public product name and release download file names |
| **campusnet** | Recommended CLI command |
| **campusnet-guard** | Compatible CLI alias |
| **cyber-lobster** | Legacy-compatible command / internal Python package name |

Maintainers and future development should first read the [project context](docs/PROJECT_CONTEXT.md), which records the current release status, build entry points, proxy/TUN compatibility boundaries, and next priorities.

---

## Use cases

| Scenario | Notes |
|------|------|
| Dorm computers | Personal laptops and desktops, auto-reconnect on dropout |
| Classrooms / labs | Workstation and teaching machines, stay online |
| Offices | Office computers, avoid repeated authentication |
| Libraries | Shared-area devices (saving credentials not recommended) |
| Server rooms | Many devices, long-term online |
| NAS | Synology / QNAP etc., 24/7 online |
| Software routers | OpenWrt / iKuai etc., gateway-level guarding |
| Mini PCs | Raspberry Pi, industrial PCs, mini hosts |
| Personal computers | Any device that needs to stay online on the campus network |

---

## ⬇️ Downloads

**Regular Windows users**: download `campusnet-guard-windows.zip`, unzip, and double-click `1-点我启动-校园网守护.exe`. No Python installation required.

### Fast downloads in mainland China (preferred for regular users)

- [Lanzou cloud, no login required](https://wwbha.lanzoue.com/b01d716nwf) (password: `39vp`)
- [China Mobile Cloud Drive](https://yun.139.com/shareweb/#/w/i/2w2KCnNR2MPzl) (code: `igtu`)
- [China Telecom Cloud Drive](https://cloud.189.cn/web/share?code=zeUzei2eIZz2) (code: `7bn1`)

### GitHub Releases (trusted source and version source)

👉 [GitHub Releases download page](https://github.com/mi179/campusnet-guard/releases/latest)

More download notes: [docs/MIRROR_DOWNLOADS.md](docs/MIRROR_DOWNLOADS.md) or the [official site](https://campusnet.journeymind.blog).

> ⚠️ **Security note**: download only from the official site, GitHub Releases, or the cloud links listed here. Never run exe files of unknown origin.

---

## 🚀 Quick start (Windows)

### Step 1: Download and unzip

Download `campusnet-guard-windows.zip` from the [Releases page](https://github.com/mi179/campusnet-guard/releases/latest) and unzip it anywhere.

### Step 2: Double-click to run

Double-click `1-点我启动-校园网守护.exe`.

> **First-run notice**: the current build is not code-signed, so Windows SmartScreen may warn about an unknown publisher. Download only from official GitHub Releases and decide for yourself whether to trust it. Click **"More info"** → **"Run anyway"**. See [Windows security notices](#windows-security-notices).

### Step 3: Add an account

Open the GUI's **Advanced** page and click **Add account**:

1. Choose the carrier (China Telecom / Mobile / Unicom / campus network)
2. Enter your student ID
3. Enter your password (masked while typing)
4. Confirm the authentication server address (it differs between schools)
5. Click **Save and verify**

Once verification succeeds the account is saved automatically. The password is never stored in plaintext — it is protected by Windows DPAPI encryption.

### Step 4: Start guarding

Back on the **Home** page, click **Start guarding**. The program checks the network every 10 seconds and re-authenticates automatically when the connection drops.

### Step 5 (optional): Start on boot

Open the **Settings** page and check **Run automatically after boot and guard the campus network**. From then on it starts and enters guard mode at login.

---

## 🖥️ GUI pages

| Page | Function |
|------|------|
| **Home** | Start guarding, stop guarding, log out / go offline, test network, live log |
| **Advanced** | Add accounts, switch between accounts, test login, delete accounts |
| **Settings** | Check interval, guard on boot, config save location |
| **Help** | Built-in usage instructions |

---

## Windows security notices

### "Unknown publisher" / SmartScreen blocking

The current build is not code-signed, so Windows SmartScreen may warn about an unknown publisher. Download only from official GitHub Releases and decide for yourself whether to trust it.

How to proceed:
1. Blue dialog → click **"More info"** → **"Run anyway"**
2. Yellow dialog → click **"More info"** → **"Run anyway"**

### Why UPX compression is not used

UPX is an executable compression tool that can trigger false positives in security software. This project does not use UPX, so files are larger (~15 MB) but compatibility is better.

---

## 🔒 Account and password security

- **Passwords are never written to disk in plaintext**
  - Windows: encrypted with DPAPI, bound to the current system user — re-entry required after switching user or machine
  - Linux: passwords protected by a local key, config file permission 600
  - macOS: passwords protected by the current user's local key, config file permission 600
- **Config file permissions**: `chmod 600`, readable and writable by the current user only
- **Config paths**:
  - Windows: `%APPDATA%\cyber-lobster\config.json`
  - Linux: `~/.config/cyber-lobster/config.json`
  - macOS: `~/.config/cyber-lobster/config.json`
- **Config is separate from the program**: wherever the EXE lives does not affect the config location
- **No telemetry**: no logs, passwords, cookies, or tokens are collected

---

## 🐧 Linux usage

Linux ships a DEB package with a desktop GUI, and the full CLI is retained. Suitable for desktop machines, NAS, software routers, mini PCs, and lab/office workstations.

### Install

```bash
# Debian / Ubuntu: one-line install of the latest release
curl -fsSL https://raw.githubusercontent.com/mi179/campusnet-guard/main/scripts/linux/install_deb.sh | bash
```

Build a local DEB from source:

```bash
bash scripts/linux/build_deb.sh
sudo apt install ./dist/campusnet-guard_*_all.deb
```

Or install manually:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e .
```

### Usage

```bash
# Open the GUI; you can also search "校园网守护" in the app menu
campusnet-gui

# Add an account (password entered masked, saved encrypted)
campusnet setup

# Start auto-reconnect on dropout
campusnet start

# Diagnose config and network status
campusnet doctor

# List saved accounts
campusnet list
```

> `cyber-lobster` is the legacy-compatible command and still works. `campusnet` is the recommended lightweight CLI entry for CampusNet Guard.

### Running in the background

```bash
# Run in tmux
tmux new -s campusnet
campusnet start
# Ctrl+B D detaches; the program keeps running
# tmux attach -t campusnet to reconnect

# Run in screen
screen -S campusnet
campusnet start
# Ctrl+A D detaches
# screen -r campusnet to reconnect
```

### systemd user service (advanced)

The repository provides a systemd user service template but does not enable it automatically. Advanced users can configure it by hand:

```ini
# ~/.config/systemd/user/campusnet-guard.service
[Unit]
Description=CampusNet Guard campus network auto-authentication daemon
After=network-online.target

[Service]
Type=simple
ExecStart=%h/.venv/bin/campusnet start
Restart=on-failure
RestartSec=30

[Install]
WantedBy=default.target
```

### More detail

See [docs/LINUX_USAGE.md](docs/LINUX_USAGE.md).

---

## 🍎 macOS usage

GitHub Releases provide native GUI installers for both Apple Silicon and Intel:

- M1/M2/M3/M4/M5: download `campusnet-guard-macos-apple-silicon.dmg`
- Intel Macs: download `campusnet-guard-macos-intel.dmg`

Open the DMG and drag CampusNet Guard into Applications. If Gatekeeper blocks the first launch, Control-click the app in Finder and choose "Open". Details: [macOS usage guide](docs/QUICK_START_MACOS.md).

The macOS GUI includes account management, login verification, dropout guarding, and run-at-login — no separate Python installation needed.

---

## 🔧 CLI commands (Linux / troubleshooting)

Desktop users on Windows, Linux, and macOS all have the GUI; the CLI below suits servers and troubleshooting.

| Command | Purpose |
|------|------|
| `campusnet setup` | Add an account (`add` is an alias) |
| `campusnet start` | Start guarding |
| `campusnet list` | List accounts |
| `campusnet verify` | Verify login (`test` is an alias) |
| `campusnet doctor` | Diagnostics |
| `campusnet logout` | Log out / go offline |
| `campusnet autostart enable` | Enable run-at-login |

> `cyber-lobster` is the legacy-compatible command and still works. `campusnet` is the recommended entry.

Full command list: `campusnet --help`

---

## ❓ FAQ

### Q: Login fails — what now?

1. **Wrong carrier** — China Telecom is DX, Mobile is YD, Unicom is LT; on-campus direct connection is "campus network"
2. **Wrong account or password** — confirm your student ID and password
3. **Wrong authentication server address** — it differs between schools; example `172.16.54.18`. Ask your school's network center to confirm
4. **Expired queryString** — re-add the account, or copy it from the browser login page

### Q: No authentication page pops up in classrooms / the library?

Different areas may use different authentication servers. Try changing the authentication server address when adding the account. Some classrooms/network environments never show an authentication page — that may be a school network policy restriction.

### Q: Concurrent device limits?

The school's network system may limit how many devices can be online at once. Over the limit, other devices get kicked offline. That depends on school policy and this tool cannot change it.

### Q: GitHub downloads are slow?

Regular Windows users should prefer the fast mainland-China mirrors:

- [Lanzou cloud, no login required](https://wwbha.lanzoue.com/b01d716nwf) (password: `39vp`)
- [China Mobile Cloud Drive](https://yun.139.com/shareweb/#/w/i/2w2KCnNR2MPzl) (code: `igtu`)
- [China Telecom Cloud Drive](https://cloud.189.cn/web/share?code=zeUzei2eIZz2) (code: `7bn1`)

GitHub Releases remains the trusted source and version source. Never download exe files from random download sites in search results.

### Q: Password stops working after switching machines?

Passwords encrypted with Windows DPAPI are bound to the current system user. After changing machine or user, run `campusnet setup` again to enter the password.

### Q: I have a system proxy, VPN, or TUN mode on — do I need to turn it off first?

Usually not. CampusNet Guard tries to send campus authentication requests directly to the authentication server instead of through the environment proxy.

If login fails, first run:

```bash
campusnet doctor
```

and look at the "proxy/VPN compatibility" section of the output. Regular users can temporarily pause the proxy/VPN/TUN and retry; advanced users can add the authentication server address to a direct-connect rule.

### Q: I can't find the run-at-login program?

The autostart program does not show a desktop icon. It runs in the background with an icon only in the system tray (bottom-right of the taskbar). If you cannot find it, press `Ctrl+Shift+Esc` to open Task Manager and check the "Startup" tab.

### Q: How do I uninstall?

1. Delete the downloaded program folder
2. Delete the config file:
   - Windows: `%APPDATA%\cyber-lobster\`
   - Linux: `~/.config/cyber-lobster/`
   - macOS: `~/.config/cyber-lobster/`

---

## ⚠️ Disclaimer

- This tool is only for **automatic authentication and reconnect-on-dropout with the user's own campus network account**
- It **does not bypass authentication, crack anything, share accounts, or defeat concurrent-device limits**
- It **only submits the user's own credentials automatically**, mimicking the normal login flow
- **Authentication policies, concurrent device limits, and whether classrooms show an authentication page** are decided by the network system and cannot be controlled by this tool
- Some classrooms/network environments **show no authentication page, cannot authenticate, or are at the device limit** — that may not be a software problem
- **Compatibility with every Ruijie ePortal version is not guaranteed**
- **Saving credentials on shared computers is not recommended**
- Users should **comply with their school's network management rules**
- Download from **GitHub Releases or the official page**; never run exe files of unknown origin
- **Users are responsible** for their own account security and network compliance

Details: [docs/DISCLAIMER.md](docs/DISCLAIMER.md).

---

## 📦 Release artifacts

| File | Purpose |
|------|------|
| `campusnet-guard-windows.zip` | Windows user download package |
| `campusnet-guard_all.deb` | Debian / Ubuntu GUI installer |
| `campusnet-guard-macos-apple-silicon.dmg` | Apple Silicon Mac GUI installer |
| `campusnet-guard-macos-intel.dmg` | Intel Mac GUI installer |
| `1-点我启动-校园网守护.exe` | GUI build (recommended) |
| `9-排障工具-不懂不用点.exe` | Troubleshooting tool — regular users don't need to open it |

- **Windows and macOS need no Python installation** — the release packages bundle the Python runtime
- **No PyInstaller installation needed** — that is a development tool, not required by users
- **Linux users**: the DEB is recommended; source installation is also supported

---

## 📄 License

[MIT](LICENSE)

---

## Official site and fast downloads in China

- Official site: <https://campusnet.journeymind.blog>
- GitHub Releases: <https://github.com/mi179/campusnet-guard/releases/latest>
- Fast mainland-China downloads: see [docs/MIRROR_DOWNLOADS.md](docs/MIRROR_DOWNLOADS.md)

> ⚠️ **Security note**: whichever channel you download from, cross-check against GitHub Releases or the official site first, and avoid exe files of unknown origin.

---

<div align="center">
  Made with ❤️ · CampusNet Guard keeps your campus network online<br>
  <sub>Found a problem? Open an issue → https://github.com/mi179/campusnet-guard/issues</sub>
</div>
