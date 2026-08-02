#!/usr/bin/env python3
"""Reads the Tuya Cloud device the widget shows a temperature from.

Run directly to print the raw status and the current reading, which is how a
credential or device problem is diagnosed without the widget in the way.
"""

import os
import sys

import requests
from dotenv import load_dotenv

from tuya import TuyaError, base_url, make_headers, read_temperature, unwrap

load_dotenv()

ACCESS_ID = os.getenv("TUYA_ACCESS_ID")
ACCESS_SECRET = os.getenv("TUYA_ACCESS_SECRET")
REGION = os.getenv("TUYA_REGION", "eu")
DEVICE_ID = os.getenv("TUYA_DEVICE_ID")

BASE_URL = base_url(REGION)

# Seconds to wait on a Tuya call. The widget updates every few minutes, so a
# stalled request must not hold its update thread.
TIMEOUT = 15


def require_credentials() -> None:
    """Stop with a readable message when the account is not configured.

    Called from the entry points rather than at import, so the widget can start
    without Tuya set up and simply show no temperature.
    """
    missing = [
        name
        for name, value in (
            ("TUYA_ACCESS_ID", ACCESS_ID),
            ("TUYA_ACCESS_SECRET", ACCESS_SECRET),
            ("TUYA_DEVICE_ID", DEVICE_ID),
        )
        if not value
    ]
    if missing:
        raise TuyaError(f"Missing in .env: {', '.join(missing)}")


def _headers(path: str, token: str = "") -> dict:
    return make_headers(ACCESS_ID, ACCESS_SECRET, path, token)


def get_access_token() -> str:
    """Access token for the configured account. Raises TuyaError when refused."""
    require_credentials()
    path = "/v1.0/token?grant_type=1"
    r = requests.get(BASE_URL + path, headers=_headers(path), timeout=TIMEOUT)
    r.raise_for_status()
    return unwrap(r.json(), "Token")["access_token"]


def get_device_status(token: str):
    """Status list for the configured device. Raises TuyaError when refused."""
    path = f"/v1.0/devices/{DEVICE_ID}/status"
    r = requests.get(BASE_URL + path, headers=_headers(path, token), timeout=TIMEOUT)
    r.raise_for_status()
    return unwrap(r.json(), "Status")


def main():
    try:
        token = get_access_token()
        status = get_device_status(token)
    except (TuyaError, requests.RequestException) as e:
        print(f"Chyba: {e}", file=sys.stderr)
        return 1

    print("Full status JSON:")
    print(status)

    temperature = read_temperature(status)
    if temperature is None:
        print("\nPolozka va_temperature nenalezena.")
    else:
        print(f"\nAktualni teplota: {temperature:.1f} C")
    return 0


if __name__ == "__main__":
    sys.exit(main())
