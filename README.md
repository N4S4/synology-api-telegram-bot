# Synology API Telegram Bot

A Telegram bot to control your Synology NAS via the [synology-api](https://github.com/N4S4/synology-api) library.

## Features

- **24 Synology modules** — 740+ API functions (FileStation, Docker, DownloadStation, Surveillance...)
- **File Browser** — explore folders, search files, download files directly in Telegram
- **Argument collection** — the bot asks for required parameters step by step
- **Access control** — only whitelisted Telegram users can interact with the bot
- **Secure** — password via `SYNOLOGY_PASSWORD` env var, config outside repo
- **aiogram 3.x** — modern async Telegram Bot API with FSM per-chat state

## Premises

- **Python 3.9+** is required.
- You should know how Telegram bots work — create one via [@BotFather](https://t.me/BotFather) first.
- This bot is **not a finished product**. It works, but I can't guarantee it will handle every edge case. Use it at your own discretion.
- You're expected to know some Python. Please do your research before opening issues — but feel free to reach out with real concerns.
- The code still has room for polish. Contributions are welcome.

## Quick Start

```bash
git clone https://github.com/N4S4/synology-api-telegram-bot.git
cd synology-api-telegram-bot
pip install -r requirements.txt

# REQUIRED environment variables (see .env.example)
export TELEGRAM_TOKEN="your_bot_token_here"
export ALLOWED_USERS="123456789"      # Your Telegram user ID (from @userinfobot)

# Optional: set NAS password via env var instead of config file
export SYNOLOGY_PASSWORD="your_nas_password"

# Run the bot
python -m synology_api_telegram_bot.main_bot
```

## Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `TELEGRAM_TOKEN` | Yes | Bot token from [@BotFather](https://t.me/BotFather) |
| `ALLOWED_USERS` | Yes | Comma-separated Telegram user IDs. **Without this the bot refuses all connections.** |
| `SYNOLOGY_PASSWORD` | No | NAS password override (falls back to config file) |

> Get your Telegram user ID from [@userinfobot](https://t.me/userinfobot) — just send `/start`.

## Usage

### General workflow
1. Send `/start` to your bot on Telegram
2. Configure your NAS: IP, port, username, password, etc.
3. Click **Finish Configuration**
4. Choose a module (e.g., `core_sys_info`, `docker_api`)
5. Click **login** to authenticate
6. Select a function — the bot will ask for arguments if needed
7. Results are returned as formatted JSON

### Commands

| Command | Description |
|---------|-------------|
| `/start` | Show configuration menu |
| `/help` | Show help and workflow |
| `/status` | Show connection status and config validation |
| `/cancel` | Cancel current operation (arg collection, search, config) |

### File Browser (`filestation` module)

Select `filestation` from the module list to access a visual file browser:

| Action | Description |
|--------|-------------|
| `📂 Browse Files` | Browse folders starting from `/home`. Tap `📁 folder` to enter, `⬆ Back` to go up, `🏠 Home` to reset. |
| `🔍 Search Files` | Search files by pattern (e.g., `*.py`, `backup*`). Choose `/home` or type a custom path. Results are clickable. |
| `📥 Download` | Download a selected file. The bot sends it as a Telegram document (max 50 MB). |
| `ℹ️ File Info` | Show file metadata: path, size, owner, modification date. |
| `📋 All Functions` | Access the raw 48 FileStation API functions with the standard keyboard. |

## Access Control

The bot uses `ALLOWED_USERS` to whitelist Telegram user IDs. Anyone not in the list gets:

> ⛔ **User not recognized.**  
> OUT OF MY STUFF!  
> Device auto-destruction **ACTIVATED!**  
> Your device CPU will burn in **1 minute**. 🔥

Set it to your ID to lock everyone else out:

```bash
export ALLOWED_USERS="123456788"
# or multiple users:
export ALLOWED_USERS="123456788,123456789"
```

## Docker

```bash
docker build -t synology-telegram-bot .
docker run \
  -e TELEGRAM_TOKEN="your_token" \
  -e ALLOWED_USERS="your_telegram_id" \
  -e SYNOLOGY_PASSWORD="your_pass" \
  synology-telegram-bot
```

## Modules Available

| Category | Modules |
|----------|---------|
| **File** | FileStation, Drive Admin, USB Copy |
| **System** | System Info, LogCenter, Security Advisor, Universal Search |
| **Users** | User management, Group management, Shared Folders |
| **Network** | DHCP Server, Directory Server, OAuth, VPN |
| **Backup** | Active Backup for Business, Backup & Restore, Snapshot |
| **Media** | AudioStation, DownloadStation, NoteStation, Photos |
| **Containers** | Docker / Container Manager, Virtual Machine Manager |
| **Security** | Surveillance Station (329 functions) |
| **Cloud** | Cloud Sync |

## Configuration

Configuration is stored in `~/.config/synology-bot/config.json` (outside the repo for security).

## Consider My Work

This project takes time and effort to maintain. If you find it useful or fun, please consider supporting it:

- **PayPal:** [paypal.me/ren4s4](https://paypal.me/ren4s4)

## License

MIT
