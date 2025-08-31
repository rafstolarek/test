"""Inteless PV integration."""

from __future__ import annotations

import logging
from typing import Any

import aiohttp
import async_timeout

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .const import (
    API_BASE,
    CLIENT_ID,
    CONF_PASSWORD,
    CONF_PLANT_ID,
    CONF_USERNAME,
    DOMAIN,
    PLATFORMS,
)

_LOGGER = logging.getLogger(__name__)


class IntelessPVClient:
    """Client for communicating with Inteless PV API."""

    def __init__(
        self,
        session: aiohttp.ClientSession,
        username: str,
        password: str,
        plant_id: str,
    ) -> None:
        self._session = session
        self._username = username
        self._password = password
        self._plant_id = plant_id
        self._token: str | None = None

    async def async_login(self) -> None:
        """Log in and store the access token."""
        url = f"{API_BASE}/oauth/token"
        payload = {
            "username": self._username,
            "password": self._password,
            "grant_type": "password",
            "client_id": CLIENT_ID,
        }
        async with async_timeout.timeout(15):
            resp = await self._session.post(url, data=payload)
            data: dict[str, Any] = await resp.json()
        self._token = data.get("access_token")
        if not self._token:
            raise RuntimeError("Login failed")

    async def async_get_realtime(self) -> dict[str, Any]:
        """Return realtime data for plant."""
        if not self._token:
            await self.async_login()
        headers = {"Authorization": f"Bearer {self._token}"}
        url = f"{API_BASE}/plant/{self._plant_id}/realtime"
        async with async_timeout.timeout(15):
            resp = await self._session.get(url, headers=headers)
            data: dict[str, Any] = await resp.json()
        return data.get("data", {})


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Inteless PV integration from a config entry."""
    session = async_get_clientsession(hass)
    client = IntelessPVClient(
        session,
        entry.data[CONF_USERNAME],
        entry.data[CONF_PASSWORD],
        entry.data[CONF_PLANT_ID],
    )
    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = client

    for platform in PLATFORMS:
        hass.async_create_task(
            hass.config_entries.async_forward_entry_setup(entry, platform)
        )
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id)
    return unload_ok
