# Synology API Telegram Bot

A Telegram bot to control your Synology NAS via the [synology-api](https://github.com/N4S4/synology-api) library.

## Features

- **24 Synology modules** — 740+ API functions (FileStation, Docker, DownloadStation, Surveillance...)
- **File Browser** — explore folders, search files, download files directly in Telegram
- **Argument collection** — the bot asks for required parameters step by step
- **Access control** — only whitelisted Telegram users can interact with the bot
- **Secure** — NAS password via `SYNOLOGY_PASSWORD` env var or config file, config stored outside repo
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

# Edit the hardcoded values in synology_api_telegram_bot/main_bot.py:
#   _HARDCODED_TOKEN = "YOUR_BOT_TOKEN_HERE"   → your real token
#   _HARDCODED_USERS = "159718277"             → your Telegram user ID
# Then run:
python -m synology_api_telegram_bot.main_bot
```

## Configuration

**Bot credentials:** Edit the hardcoded values at the top of `synology_api_telegram_bot/main_bot.py`:

- `_HARDCODED_TOKEN` — bot token from [@BotFather](https://t.me/BotFather)
- `_HARDCODED_USERS` — comma-separated Telegram user IDs (get yours from [@userinfobot](https://t.me/userinfobot))

These values are baked into the source. Environment variables (`TELEGRAM_TOKEN`, `ALLOWED_USERS`) take priority if set, but the compose file does not inject them — the hardcoded values are authoritative.

**NAS connection:** Stored in `~/.config/synology-bot/config.json` (outside the repo for security), configured interactively via `/start`.

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

Set it in `main_bot.py` to lock everyone else out:

```python
_HARDCODED_USERS = "159718277"
# or multiple users:
_HARDCODED_USERS = "159718277,123456789"
```

## Docker

Edit `_HARDCODED_TOKEN` and `_HARDCODED_USERS` in `main_bot.py` first, then:

```bash
docker compose build --no-cache
docker compose up -d
```

Or with plain `docker run` (env vars override hardcoded values if you prefer):

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
