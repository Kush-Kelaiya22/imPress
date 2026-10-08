"""Device authentication (#66): the shared provisioning key and per-device keys.

Every device starts with the site's shared key (IMPRESS_DEVICE_API_KEY), which
it uses to register. Registration issues the device its own key; the backend
keeps only its SHA-256. The key becomes **active** the first time the device
uses it. Until then a lost response is harmless: registering again with the
shared key issues a new key.

Once a device's key is active:
- only that key can act for the device's MAC: the shared key can't, so
  whoever holds the shared key can no longer impersonate it;
- the key works only for that MAC, so one device can't act for another;
- an admin can reset it (the device then re-registers with the shared key)
  or disable the device, which refuses every call for its MAC.

With IMPRESS_DEVICE_KEYS_REQUIRED=true the shared key is accepted for
registration only; firmware that predates per-device keys then stops working.
"""

import hashlib
import secrets
from dataclasses import dataclass

from fastapi import Depends, Header, HTTPException
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from .config import api_key_ok, settings
from .database import get_db
from .models import EspDevice
from .timeutil import istnow


def key_hash(key: str) -> str:
    return hashlib.sha256(key.encode()).hexdigest()


def new_device_key() -> tuple[str, str]:
    """(raw key for the device, hash to store)."""
    raw = secrets.token_urlsafe(32)
    return raw, key_hash(raw)


@dataclass
class DeviceCaller:
    """Who is calling: the shared key (device None) or one device's own key."""
    device: EspDevice | None

    @property
    def shared(self) -> bool:
        return self.device is None


async def _by_mac(db: AsyncSession, mac: str) -> EspDevice | None:
    return await db.scalar(select(EspDevice).where(func.lower(EspDevice.mac_address) == (mac or "").strip().lower()))


async def caller_for_key(db: AsyncSession, key: str | None) -> DeviceCaller | None:
    """The caller this key identifies, or None for an unknown key."""
    if api_key_ok(key):
        return DeviceCaller(None)
    if not key:
        return None
    device = await db.scalar(select(EspDevice).where(EspDevice.api_key_hash == key_hash(key)))
    if device is None:
        return None
    if device.key_confirmed_at is None:          # first use activates it
        device.key_confirmed_at = istnow()
    return DeviceCaller(device)


async def device_caller(x_api_key: str = Header(...), db: AsyncSession = Depends(get_db)) -> DeviceCaller:
    caller = await caller_for_key(db, x_api_key)
    if caller is None:
        # 401, not 403: the firmware drops a device key on 401 (it was reset)
        # and registers again; a 403 (disabled, wrong device) keeps it.
        raise HTTPException(401, "Invalid device API key")
    return caller


async def denial(db: AsyncSession, caller: DeviceCaller, mac: str | None, *, registering=False) -> str | None:
    """Why this caller may not act for this MAC, or None if it may."""
    if caller.device is not None:
        if (mac or "").strip().lower() != caller.device.mac_address.lower():
            return "this device key belongs to another device"
        if caller.device.is_active is False:
            return "this device is disabled"
        return None
    target = await _by_mac(db, mac) if mac else None
    if target is not None and target.is_active is False:
        return "this device is disabled"
    if target is not None and target.key_confirmed_at is not None:
        return "this device has its own key: use it, or reset it on the Modules page"
    if settings.DEVICE_KEYS_REQUIRED and not registering:
        return "the shared key is accepted for registration only (IMPRESS_DEVICE_KEYS_REQUIRED)"
    return None


async def authorize(db: AsyncSession, caller: DeviceCaller, mac: str | None, *, registering=False) -> None:
    reason = await denial(db, caller, mac, registering=registering)
    if reason:
        raise HTTPException(403, reason)
