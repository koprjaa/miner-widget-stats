# Miner Stats

macOS menu bar widget pro monitoring mining pool a teploty. Zobrazuje aktuální hash rate z pool.braiins.com a teplotu z Tuya API s automatickými aktualizacemi každých 5 minut.

## Instalace

```bash
pip install -r requirements.txt
```

## Konfigurace

Vytvořte `.env` soubor s vašimi credentials:

## Použití

Spuštění widgetu:
```bash
python miner_widget.py
```

Widget se zobrazí v menu bar s formátem: `12.5TH/s 45.2°C`

Konfigurace přes `.env` soubor:
```
# Pool.braiins.com konfigurace
TOKEN=your_pool_token
COIN=btc
BASE_URL=https://pool.braiins.com
UPDATE_INTERVAL=300
MAX_RETRIES=3
RETRY_DELAY=5

# Tuya API konfigurace
TUYA_ACCESS_ID=your_tuya_access_id
TUYA_ACCESS_SECRET=your_tuya_access_secret
TUYA_REGION=eu
TUYA_DEVICE_ID=your_tuya_device_id
```

## Licence

MIT - viz [LICENSE](LICENSE) soubor.
