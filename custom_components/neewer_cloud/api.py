"""Neewer cloud API client.

Endpoints and payloads were reconstructed from the NEEWER Home Android app
(com.neewer.neewerapp 2.2.4). The API is private and may change without notice.
"""

from __future__ import annotations

import hashlib
import logging
from typing import Any

import aiohttp

from .const import (
    AUTH_HEADER,
    BASE_URL,
    CLIENT_NAME,
    CLIENT_VERSION,
    CODE_OK,
    CODE_TOKEN_EXPIRED,
    CODE_TOKEN_INVALID,
    DEFAULT_LANGUAGE,
    DEFAULT_ZONE,
    EP_COLOR,
    EP_DEVICES_BY_GROUP,
    EP_GROUPS,
    EP_LIGHTING,
    EP_LOGIN,
    EP_SCENE_EXECUTE,
    EP_SCENES,
    EP_TURN_ON,
)

_LOGGER = logging.getLogger(__name__)

REQUEST_TIMEOUT = 20


class NeewerError(Exception):
    """Generic API failure."""


class NeewerAuthError(NeewerError):
    """Login failed."""


class NeewerCloudAPI:
    """Thin async client for the Neewer cloud."""

    def __init__(
        self,
        session: aiohttp.ClientSession,
        account: str,
        password: str,
        client_id: str,
        zone: str = DEFAULT_ZONE,
    ) -> None:
        self._session = session
        self._account = account
        self._password = password
        self._client_id = client_id
        self._zone = zone
        self.access_token: str | None = None
        self.refresh_token: str | None = None
        self.last_error: str | None = None
        self.raw_scenes: dict[str, Any] = {}

    # ---- transport -----------------------------------------------------

    def _headers(self) -> dict[str, str]:
        headers = {
            "Authorization": AUTH_HEADER,
            "Content-Type": "application/json; charset=utf-8",
            "accept": "application/json",
            "zone": self._zone,
            "dictLanguage": DEFAULT_LANGUAGE,
        }
        if self.access_token:
            headers["accessToken"] = self.access_token
        if self.refresh_token:
            headers["refreshToken"] = self.refresh_token
        return headers

    async def _request(
        self,
        method: str,
        path: str,
        payload: dict[str, Any] | None = None,
        retry: bool = True,
    ) -> Any:
        url = f"{BASE_URL}{path}"
        try:
            async with self._session.request(
                method,
                url,
                json=payload,
                headers=self._headers(),
                timeout=aiohttp.ClientTimeout(total=REQUEST_TIMEOUT),
            ) as response:
                if response.status != 200:
                    text = await response.text()
                    raise NeewerError(f"HTTP {response.status}: {text[:200]}")
                body = await response.json(content_type=None)
        except aiohttp.ClientError as err:
            raise NeewerError(f"network error: {err}") from err

        code = body.get("code")
        try:
            code = int(code)
        except (TypeError, ValueError):
            code = -1
        message = body.get("message") or ""

        if code in (CODE_TOKEN_EXPIRED, CODE_TOKEN_INVALID) and retry:
            _LOGGER.debug("Neewer token rejected (%s), logging in again", code)
            await self.login()
            return await self._request(method, path, payload, retry=False)

        if code != CODE_OK:
            self.last_error = f"{code}: {message}"
            raise NeewerError(f"{code}: {message}")

        self.last_error = None
        return body.get("data")

    # ---- auth ----------------------------------------------------------

    async def login(self) -> None:
        """Authenticate and keep the access/refresh tokens."""
        payload = {
            "account": self._account,
            "passwordSecure": hashlib.md5(
                self._password.encode("utf-8")
            ).hexdigest(),
            "clientId": self._client_id,
            "clientName": CLIENT_NAME,
            "clientVersion": CLIENT_VERSION,
        }
        try:
            data = await self._request("POST", EP_LOGIN, payload, retry=False)
        except NeewerError as err:
            if str(err).startswith(("network error", "HTTP")):
                raise
            raise NeewerAuthError(str(err)) from err
        if not isinstance(data, dict) or not data.get("accessToken"):
            raise NeewerAuthError("no access token in login response")
        self.access_token = data["accessToken"]
        self.refresh_token = data.get("refreshToken")
        _LOGGER.debug("Neewer cloud login succeeded")

    # ---- discovery -----------------------------------------------------

    async def get_devices(self) -> list[dict[str, Any]]:
        """Return the user's devices."""
        devices: list[dict[str, Any]] = []
        groups = await self._request("GET", EP_GROUPS)
        for group in (groups or {}).get("list", []) or []:
            for device in group.get("deviceInfos", []) or []:
                if device.get("deviceId"):
                    devices.append(device)

        if devices:
            return devices

        data = await self._request(
            "POST", EP_DEVICES_BY_GROUP, {"groupId": 0}
        )
        return list((data or {}).get("list", []) or [])

    async def get_scenes(self, device_id: str) -> dict[str, dict[str, Any]]:
        """Return {scene name: {effect_id, effect_order}} for one device."""
        data = await self._request("POST", EP_SCENES, {"deviceId": device_id})
        self.raw_scenes[device_id] = data
        scenes: dict[str, dict[str, Any]] = {}
        for category in (data or {}).get("list", []) or []:
            for scene in category.get("sceneEffectSpeedData", []) or []:
                name = scene.get("effectName")
                effect_id = scene.get("effectId")
                if not name or effect_id is None:
                    continue
                orders = [
                    entry.get("effectOrder")
                    for entry in scene.get("effectControlSpeed", []) or []
                    if entry.get("effectOrder") is not None
                ]
                scenes[name] = {
                    "effect_id": int(effect_id),
                    "effect_order": int(orders[0]) if orders else 0,
                }
        return scenes

    # ---- control -------------------------------------------------------

    async def turn_on(self, device_id: str, on: bool) -> None:
        await self._request(
            "POST", EP_TURN_ON, {"deviceId": device_id, "on": on}
        )

    async def set_lighting(
        self,
        device_id: str,
        brightness: int | None = None,
        temperature: int | None = None,
    ) -> None:
        payload: dict[str, Any] = {"deviceId": device_id, "panelIndex": 0}
        if brightness is not None:
            payload["brightness"] = brightness
        if temperature is not None:
            payload["temperature"] = temperature
        await self._request("POST", EP_LIGHTING, payload)

    async def set_color(
        self, device_id: str, brightness: int, hue: int, saturation: int
    ) -> None:
        await self._request(
            "POST",
            EP_COLOR,
            {
                "deviceId": device_id,
                "lightColorType": 1,
                "brightness": brightness,
                "hue": hue,
                "saturation": saturation,
                "panelIndex": 0,
                "hsiList": [
                    {"hue": hue, "saturation": saturation, "lightness": 100}
                ],
            },
        )

    async def execute_scene(
        self,
        device_id: str,
        effect_id: int,
        brightness: int,
        effect_order: int = 0,
    ) -> None:
        await self._request(
            "POST",
            EP_SCENE_EXECUTE,
            {
                "deviceId": device_id,
                "effectId": effect_id,
                "brightness": brightness,
                "effectOrder": effect_order,
            },
        )
