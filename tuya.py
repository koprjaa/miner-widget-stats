#!/usr/bin/env python3
"""Signing and reading a Tuya Cloud device.

The request signature and the unit conversion are pure functions, so they can be
read and tested without an account. Nothing here calls sys.exit: the widget has
to keep running when a reading fails.
"""

import hashlib
import hmac
import time
import uuid

# Tuya reports temperature in tenths of a degree.
TEMPERATURE_SCALE = 10.0

# Status code holding the ambient temperature.
TEMPERATURE_CODE = "va_temperature"


class TuyaError(RuntimeError):
    """Tuya answered, but refused the request."""


def base_url(region: str = "eu") -> str:
    return f"https://openapi.tuya{region}.com"


def signature(access_id: str, secret: str, path: str, ts: str, nonce: str, token: str = "") -> str:
    """HMAC-SHA256 signature for one request.

    Tuya signs the method, a hash of the body, an empty header line and the
    path, then prefixes the client id, the token, the timestamp and the nonce.
    The order is fixed by the API and every part is required.
    """
    empty_body = hashlib.sha256(b"").hexdigest()
    # Written as a join because that is how Tuya documents it: four parts, one
    # per line, the third of them empty. An f-string hides the empty line.
    string_to_sign = "\n".join(["GET", empty_body, "", path])
    base = access_id + (token or "") + ts + nonce + string_to_sign
    return hmac.new(secret.encode(), base.encode(), hashlib.sha256).hexdigest().upper()


def make_headers(access_id: str, secret: str, path: str, token: str = "") -> dict:
    """Signed headers for a GET. The timestamp and nonce are generated here."""
    ts = str(int(time.time() * 1000))
    nonce = uuid.uuid4().hex
    headers = {
        "client_id": access_id,
        "sign_method": "HMAC-SHA256",
        "t": ts,
        "nonce": nonce,
        "sign": signature(access_id, secret, path, ts, nonce, token),
    }
    if token:
        headers["access_token"] = token
    return headers


def read_temperature(status) -> float | None:
    """Ambient temperature in degrees, or None when the device did not report it."""
    if not status:
        return None
    item = next((d for d in status if d.get("code") == TEMPERATURE_CODE), None)
    if item is None or item.get("value") is None:
        return None
    try:
        return item["value"] / TEMPERATURE_SCALE
    except TypeError:
        return None


def unwrap(payload: dict, what: str):
    """The result of a Tuya response, or raise when the call was refused."""
    if not payload.get("success", False):
        raise TuyaError(f"{what} failed: {payload}")
    return payload["result"]
