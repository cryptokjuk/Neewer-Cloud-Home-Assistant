"""Config flow for the Neewer Cloud integration."""

from __future__ import annotations

import logging
import uuid
from typing import Any

import voluptuous as vol

from homeassistant.config_entries import ConfigFlow, ConfigFlowResult
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.selector import (
    TextSelector,
    TextSelectorConfig,
    TextSelectorType,
)

from .api import NeewerAuthError, NeewerCloudAPI, NeewerError
from .const import (
    CONF_ACCOUNT,
    CONF_CLIENT_ID,
    CONF_PASSWORD,
    DEFAULT_ZONE,
    DOMAIN,
)

_LOGGER = logging.getLogger(__name__)

USER_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_ACCOUNT): TextSelector(
            TextSelectorConfig(autocomplete="username")
        ),
        vol.Required(CONF_PASSWORD): TextSelector(
            TextSelectorConfig(
                type=TextSelectorType.PASSWORD,
                autocomplete="current-password",
            )
        ),
    }
)


class NeewerCloudConfigFlow(ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Neewer Cloud."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        errors: dict[str, str] = {}

        if user_input is not None:
            account = user_input[CONF_ACCOUNT].strip()
            client_id = str(uuid.uuid4())
            api = NeewerCloudAPI(
                async_get_clientsession(self.hass),
                account=account,
                password=user_input[CONF_PASSWORD],
                client_id=client_id,
                zone=DEFAULT_ZONE,
            )
            try:
                await api.login()
            except NeewerAuthError as err:
                _LOGGER.warning("Neewer login rejected: %s", err)
                errors["base"] = "invalid_auth"
            except NeewerError as err:
                _LOGGER.warning("Neewer login failed: %s", err)
                errors["base"] = "cannot_connect"
            else:
                await self.async_set_unique_id(account.lower())
                self._abort_if_unique_id_configured()
                return self.async_create_entry(
                    title=f"Neewer ({account})",
                    data={
                        CONF_ACCOUNT: account,
                        CONF_PASSWORD: user_input[CONF_PASSWORD],
                        CONF_CLIENT_ID: client_id,
                    },
                )

        return self.async_show_form(
            step_id="user", data_schema=USER_SCHEMA, errors=errors
        )
