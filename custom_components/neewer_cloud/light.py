"""Light platform for Neewer Cloud."""

from __future__ import annotations

import logging
from typing import Any

from homeassistant.components.light import (
    ATTR_BRIGHTNESS,
    ATTR_COLOR_TEMP_KELVIN,
    ATTR_EFFECT,
    ATTR_HS_COLOR,
    ColorMode,
    LightEntity,
    LightEntityFeature,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .api import NeewerCloudAPI, NeewerError
from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

MIN_KELVIN = 2700
MAX_KELVIN = 6500


def _to_level(brightness: int) -> int:
    """Convert HA 0-255 brightness to the cloud 0-1000 scale."""
    return max(0, min(1000, round(brightness * 1000 / 255)))


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up one light entity per cloud device."""
    api: NeewerCloudAPI = hass.data[DOMAIN][entry.entry_id]

    try:
        devices = await api.get_devices()
    except NeewerError as err:
        _LOGGER.error("Could not list Neewer devices: %s", err)
        return

    entities: list[NeewerCloudLight] = []
    for device in devices:
        device_id = device.get("deviceId")
        if not device_id:
            continue
        try:
            scenes = await api.get_scenes(device_id)
        except NeewerError as err:
            _LOGGER.warning("Could not load scenes for %s: %s", device_id, err)
            scenes = {}
        entities.append(NeewerCloudLight(api, device, scenes))

    if entities:
        async_add_entities(entities)


class NeewerCloudLight(LightEntity):
    """A Neewer light controlled through Neewer's cloud."""

    _attr_has_entity_name = True
    _attr_name = None
    _attr_supported_color_modes = {ColorMode.COLOR_TEMP, ColorMode.HS}
    _attr_min_color_temp_kelvin = MIN_KELVIN
    _attr_max_color_temp_kelvin = MAX_KELVIN
    _attr_supported_features = LightEntityFeature.EFFECT

    def __init__(
        self,
        api: NeewerCloudAPI,
        device: dict[str, Any],
        scenes: dict[str, dict[str, Any]],
    ) -> None:
        self._api = api
        self._device_id = device["deviceId"]
        self._scenes = scenes
        self._attr_effect_list = list(scenes) or None
        self._attr_unique_id = f"{self._device_id}_light"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, self._device_id)},
            name=device.get("deviceName") or "Neewer light",
            manufacturer="Neewer",
            model=device.get("deviceModel") or device.get("deviceType"),
        )
        self._attr_is_on = False
        self._attr_brightness = 255
        self._attr_color_temp_kelvin = 4000
        self._attr_hs_color = (0.0, 0.0)
        self._attr_color_mode = ColorMode.COLOR_TEMP
        self._attr_effect: str | None = None

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Expose the last API error for troubleshooting."""
        return {"cloud_last_error": self._api.last_error}

    async def async_turn_on(self, **kwargs: Any) -> None:
        """Turn the light on and apply the requested settings."""
        brightness = kwargs.get(ATTR_BRIGHTNESS)
        level = _to_level(
            brightness if brightness is not None else self._attr_brightness
        )
        effect = kwargs.get(ATTR_EFFECT)
        hs_color = kwargs.get(ATTR_HS_COLOR)
        color_temp = kwargs.get(ATTR_COLOR_TEMP_KELVIN)

        try:
            if not self._attr_is_on:
                await self._api.turn_on(self._device_id, True)

            if effect is not None:
                scene = self._scenes.get(effect)
                if scene is None:
                    match = next(
                        (
                            name
                            for name in self._scenes
                            if name.lower() == effect.lower()
                        ),
                        None,
                    )
                    if match is None:
                        raise NeewerError(f"unknown effect: {effect}")
                    scene = self._scenes[match]
                    effect = match
                await self._api.execute_scene(
                    self._device_id,
                    scene["effect_id"],
                    level,
                    scene["effect_order"],
                )
                self._attr_effect = effect
            elif hs_color is not None:
                await self._api.set_color(
                    self._device_id,
                    level,
                    int(hs_color[0]) % 360,
                    round(hs_color[1]),
                )
                self._attr_hs_color = hs_color
                self._attr_color_mode = ColorMode.HS
                self._attr_effect = None
            elif color_temp is not None:
                await self._api.set_lighting(
                    self._device_id, brightness=level, temperature=color_temp
                )
                self._attr_color_temp_kelvin = color_temp
                self._attr_color_mode = ColorMode.COLOR_TEMP
                self._attr_effect = None
            elif brightness is not None:
                await self._api.set_lighting(self._device_id, brightness=level)
        except NeewerError as err:
            raise HomeAssistantError(str(err)) from err

        self._attr_is_on = True
        if brightness is not None:
            self._attr_brightness = brightness
        self.async_write_ha_state()

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Turn the light off."""
        try:
            await self._api.turn_on(self._device_id, False)
        except NeewerError as err:
            raise HomeAssistantError(str(err)) from err

        self._attr_is_on = False
        self.async_write_ha_state()
