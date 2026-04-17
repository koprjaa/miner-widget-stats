# miner-widget-stats

**macOS menu-bar widget that shows live Bitcoin hashrate from pool.braiins.com and ambient temperature from a Tuya sensor, side-by-side.**

![python](https://img.shields.io/badge/python-3.10+-3776AB?style=flat-square&logo=python&logoColor=white)
![license](https://img.shields.io/badge/license-MIT-A31F34?style=flat-square)
![status](https://img.shields.io/badge/status-active-22863A?style=flat-square)
![platform](https://img.shields.io/badge/platform-macOS-000?style=flat-square&logo=apple&logoColor=white)
![rumps](https://img.shields.io/badge/rumps-menu%20bar-555?style=flat-square)

One glance at the top-right of the screen tells you whether the miner is happy and whether the mining shed is getting too hot.

```
  ▲ WiFi   🔊    12.5TH/s 45.2°C    🔋   Mon 16:02
                └──── miner-widget-stats
```

Updates every 5 minutes. Backed by a persistent tray process via [rumps](https://github.com/jaredks/rumps), with Tuya Cloud API for the thermometer and pool.braiins.com's account API for the hashrate.

## Install + run

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python miner_widget.py
```

For autostart on login, symlink the included `com.miner.widget.plist` into `~/Library/LaunchAgents/` and `launchctl load` it.

## Config

Create `.env` in the repo root:

```ini
# Braiins Pool
TOKEN=your_pool_access_token
COIN=btc
BASE_URL=https://pool.braiins.com
UPDATE_INTERVAL=300
MAX_RETRIES=3
RETRY_DELAY=5

# Tuya Cloud
TUYA_ACCESS_ID=your_access_id
TUYA_ACCESS_SECRET=your_access_secret
TUYA_REGION=eu
TUYA_DEVICE_ID=your_device_id
```

- Braiins token from [pool.braiins.com → Access Profile → API Tokens](https://pool.braiins.com/)
- Tuya credentials from [iot.tuya.com](https://iot.tuya.com/) after linking your sensor via the Tuya Smart / Smart Life app

## What's where

- `miner_widget.py` — rumps tray app, update loop, formatting
- `get_api.py` — Tuya Cloud HMAC-signed API (access token + device status)
- `com.miner.widget.plist` — LaunchAgent template for autostart

## Why rumps instead of a web dashboard

A mining shed upstairs doesn't need Grafana. It needs one number on-screen at all times with zero friction. A menu-bar widget is always visible, costs nothing when nothing changes, and doesn't occupy a browser tab.

## License

[MIT](LICENSE)
