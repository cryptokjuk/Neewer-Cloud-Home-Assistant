"""Neewer Cloud integration."""

from __future__ import annotations

import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryNotReady
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .api import NeewerCloudAPI, NeewerError
from .const import CONF_ACCOUNT, CONF_CLIENT_ID, CONF_PASSWORD, DOMAIN

_LOGGER = logging.getLogger(__name__)

PLATFORMS: list[Platform] = [Platform.LIGHT]

type NeewerCloudConfigEntry = ConfigEntry[NeewerCloudAPI]


async def async_setup_entry(hass: HomeAssistant, entry: NeewerCloudConfigEntry) -> bool:
    """Set up Neewer Cloud from a config entry."""
    api = NeewerCloudAPI(
        async_get_clientsession(hass),
        account=entry.data[CONF_ACCOUNT],
        password=entry.data[CONF_PASSWORD],
        client_id=entry.data[CONF_CLIENT_ID],
    )
    try:
        await api.login()
    except NeewerError as err:
        _LOGGER.error("Neewer Cloud login failed: %s", err)
        raise ConfigEntryNotReady(str(err)) from err

    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = api
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: NeewerCloudConfigEntry) -> bool:
    """Unload a config entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id)
    return unload_ok
