"""Config flow for MySQL Monitor."""
import logging
from typing import Any, Dict, Optional

import voluptuous as vol
from homeassistant import config_entries
from homeassistant.const import (
    CONF_HOST,
    CONF_PASSWORD,
    CONF_PORT,
    CONF_USERNAME,
)
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResult
from homeassistant.helpers import config_validation as cv

from .const import (
    CONF_EXCLUDE_DBS,
    CONF_INCLUDE_DBS,
    CONF_SCAN_INTERVAL,
    CONF_SSL_CA,
    CONF_SSL_VERIFY,
    CONF_USE_SSL,
    DEFAULT_PORT,
    DEFAULT_SCAN_INTERVAL,
    DOMAIN,
)
from .mysql_client import MySQLClient

_LOGGER = logging.getLogger(__name__)


class MySQLMonitorConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for MySQL Monitor."""
    
    VERSION = 1
    
    async def async_step_user(
        self, user_input: Optional[Dict[str, Any]] = None
    ) -> FlowResult:
        """Handle the initial step."""
        errors = {}
        
        if user_input is not None:
            # Test connection
            client = MySQLClient(
                host=user_input[CONF_HOST],
                port=user_input[CONF_PORT],
                username=user_input[CONF_USERNAME],
                password=user_input[CONF_PASSWORD],
                use_ssl=user_input.get(CONF_USE_SSL, False),
                ssl_ca=user_input.get(CONF_SSL_CA),
                ssl_verify=user_input.get(CONF_SSL_VERIFY, True),
            )
            
            try:
                await self.hass.async_add_executor_job(client.test_connection)
                
                # Create unique ID
                await self.async_set_unique_id(
                    f"{user_input[CONF_HOST]}:{user_input[CONF_PORT]}"
                )
                self._abort_if_unique_id_configured()
                
                # Store config
                return self.async_create_entry(
                    title=f"MySQL {user_input[CONF_HOST]}:{user_input[CONF_PORT]}",
                    data=user_input,
                    options={
                        CONF_INCLUDE_DBS: "",
                        CONF_EXCLUDE_DBS: "",
                        CONF_SCAN_INTERVAL: DEFAULT_SCAN_INTERVAL,
                    },
                )
            except Exception as err:
                _LOGGER.error("Failed to connect to MySQL: %s", err)
                errors["base"] = "cannot_connect"
            finally:
                await self.hass.async_add_executor_job(client.close)
        
        # Show form
        data_schema = vol.Schema({
            vol.Required(CONF_HOST): str,
            vol.Required(CONF_PORT, default=DEFAULT_PORT): cv.port,
            vol.Required(CONF_USERNAME): str,
            vol.Required(CONF_PASSWORD): str,
            vol.Optional(CONF_USE_SSL, default=False): bool,
            vol.Optional(CONF_SSL_CA): str,
            vol.Optional(CONF_SSL_VERIFY, default=True): bool,
        })
        
        return self.async_show_form(
            step_id="user",
            data_schema=data_schema,
            errors=errors,
        )
    
    @staticmethod
    def async_get_options_flow(config_entry):
        """Get options flow."""
        return MySQLMonitorOptionsFlow(config_entry)


class MySQLMonitorOptionsFlow(config_entries.OptionsFlow):
    """Handle options flow for MySQL Monitor."""
    
    def __init__(self, config_entry):
        """Initialize options flow."""
        self.config_entry = config_entry
    
    async def async_step_init(
        self, user_input: Optional[Dict[str, Any]] = None
    ) -> FlowResult:
        """Handle options flow."""
        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)
        
        data_schema = vol.Schema({
            vol.Optional(
                CONF_INCLUDE_DBS,
                default=self.config_entry.options.get(CONF_INCLUDE_DBS, ""),
            ): str,
            vol.Optional(
                CONF_EXCLUDE_DBS,
                default=self.config_entry.options.get(CONF_EXCLUDE_DBS, ""),
            ): str,
            vol.Optional(
                CONF_SCAN_INTERVAL,
                default=self.config_entry.options.get(
                    CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL
                ),
            ): vol.All(vol.Coerce(int), vol.Range(min=10, max=3600)),
        })
        
        return self.async_show_form(
            step_id="init",
            data_schema=data_schema,
        )
