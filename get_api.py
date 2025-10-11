#!/usr/bin/env python3
import time
import uuid
import hmac
import hashlib
import requests
import sys
import os
from dotenv import load_dotenv

# Načtení .env proměnných
load_dotenv()

# ───── KONFIGURACE ─────
ACCESS_ID     = os.getenv("TUYA_ACCESS_ID")
ACCESS_SECRET = os.getenv("TUYA_ACCESS_SECRET")
REGION        = os.getenv("TUYA_REGION", "eu")
DEVICE_ID     = os.getenv("TUYA_DEVICE_ID")
# ────────────────────────

# Validace povinných proměnných
if not ACCESS_ID or not ACCESS_SECRET or not DEVICE_ID:
    print("❌ Chyba: Chybí povinné Tuya API proměnné v .env souboru", file=sys.stderr)
    print("Požadované proměnné: TUYA_ACCESS_ID, TUYA_ACCESS_SECRET, TUYA_DEVICE_ID", file=sys.stderr)
    sys.exit(1)

BASE_URL = f"https://openapi.tuya{REGION}.com"

def make_headers(path: str, token: str = "") -> dict:
    method = "GET"
    ts     = str(int(time.time() * 1000))
    nonce  = uuid.uuid4().hex
    content_sha = hashlib.sha256(b"").hexdigest()
    string_to_sign = "\n".join([method, content_sha, "", path])
    base = ACCESS_ID + (token or "") + ts + nonce + string_to_sign
    sign = hmac.new(ACCESS_SECRET.encode(), base.encode(), hashlib.sha256).hexdigest().upper()

    hdr = {
        "client_id":   ACCESS_ID,
        "sign_method": "HMAC-SHA256",
        "t":           ts,
        "nonce":       nonce,
        "sign":        sign
    }
    if token:
        hdr["access_token"] = token
    return hdr

def get_access_token() -> str:
    path = "/v1.0/token?grant_type=1"
    r = requests.get(BASE_URL + path, headers=make_headers(path))
    r.raise_for_status()
    data = r.json()
    if not data.get("success", False):
        print("❌ Token error:", data, file=sys.stderr); sys.exit(1)
    return data["result"]["access_token"]

def get_device_status(token: str):
    path = f"/v1.0/devices/{DEVICE_ID}/status"
    r = requests.get(BASE_URL + path, headers=make_headers(path, token))
    r.raise_for_status()
    data = r.json()
    if not data.get("success", False):
        print("❌ Status error:", data, file=sys.stderr); sys.exit(1)
    return data["result"]

def main():
    token  = get_access_token()
    status = get_device_status(token)

    print("▶️ Full status JSON:")
    print(status)

    # najdeme přesně va_temperature a přepočítáme na °C
    temp_item = next((d for d in status if d.get("code") == "va_temperature"), None)
    if temp_item is not None:
        temp_c = temp_item["value"] / 10.0
        print(f"\n🌡️ Aktuální teplota: {temp_c:.1f} °C")
    else:
        print("\n⚠️ Položka va_temperature nenalezena.")

if __name__ == "__main__":
    main()
