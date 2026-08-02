# miner-widget-stats

macOS menu bar widget that shows the live Bitcoin hashrate from pool.braiins.com next to the ambient temperature from a Tuya sensor.

![python](https://img.shields.io/badge/python-3.10+-3776AB?style=flat-square&logo=python&logoColor=white)
![license](https://img.shields.io/badge/license-MIT-A31F34?style=flat-square)
![status](https://img.shields.io/badge/status-active-22863A?style=flat-square)
![platform](https://img.shields.io/badge/platform-macOS-000?style=flat-square&logo=apple&logoColor=white)

One glance at the menu bar tells you whether the miner runs and whether the room gets too hot.

```
  WiFi   Vol    12.5TH/s 45.2°C    Battery   Mon 16:02
                |
                miner-widget-stats
```

The widget updates every 5 minutes. It runs as a persistent tray process with [rumps](https://github.com/jaredks/rumps). It reads the temperature from the Tuya Cloud API and the hashrate from the account API of pool.braiins.com.

## Install

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Configure

Create a `.env` file in the repository root:

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

Get the Braiins token from pool.braiins.com under Access Profile, then API Tokens. Get the Tuya credentials from [iot.tuya.com](https://iot.tuya.com/) after you link the sensor in the Tuya Smart or Smart Life app.

## Use

```bash
python miner_widget.py
```

For autostart, link `com.miner.widget.plist` into `~/Library/LaunchAgents/` and load it with `launchctl`.

## How it works

```
miner_widget.py         rumps tray app, update loop, number formatting
get_api.py              Tuya Cloud API with HMAC signing, access token and device status
com.miner.widget.plist  LaunchAgent template for autostart
```

A mining shed does not need Grafana. It needs one number on screen at all times. A menu bar widget stays visible, costs nothing when nothing changes, and takes no browser tab.

## Limits

- macOS only. rumps wraps the AppKit status bar.
- Both the pool token and the Tuya credentials are required. The widget shows nothing without them.
- No tests.

## License

[MIT](LICENSE)
