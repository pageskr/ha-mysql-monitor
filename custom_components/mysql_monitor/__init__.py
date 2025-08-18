"""MySQL Monitor Integration for Home Assistant."""
import logging
from datetime import timedelta
from decimal import Decimal

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryNotReady
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import (
    DOMAIN, 
    DEFAULT_SCAN_INTERVAL,
    CONF_ENABLE_QUERY_CACHE,
    CONF_ENABLE_REPLICATION,
)
from .mysql_client import MySQLClient

_LOGGER = logging.getLogger(__name__)

PLATFORMS = [Platform.SENSOR]


def convert_decimal(obj):
    """Convert Decimal objects to float for JSON serialization."""
    if isinstance(obj, Decimal):
        return float(obj)
    elif isinstance(obj, dict):
        return {k: convert_decimal(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [convert_decimal(item) for item in obj]
    return obj


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up MySQL Monitor from a config entry."""
    hass.data.setdefault(DOMAIN, {})
    
    # Create MySQL client
    client = MySQLClient(
        host=entry.data["host"],
        port=entry.data["port"],
        username=entry.data["username"],
        password=entry.data["password"],
        use_ssl=entry.data.get("use_ssl", False),
        ssl_ca=entry.data.get("ssl_ca"),
        ssl_verify=entry.data.get("ssl_verify", True),
    )
    
    # Test connection
    try:
        await hass.async_add_executor_job(client.test_connection)
    except Exception as err:
        _LOGGER.error("Failed to connect to MySQL: %s", err)
        raise ConfigEntryNotReady(f"Unable to connect to MySQL: {err}") from err
    
    # Create coordinator
    coordinator = MySQLDataCoordinator(
        hass,
        client,
        entry,
    )
    
    # Fetch initial data
    await coordinator.async_config_entry_first_refresh()
    
    hass.data[DOMAIN][entry.entry_id] = {
        "coordinator": coordinator,
        "client": client,
    }
    
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    
    # Reload entry when options updated
    entry.async_on_unload(entry.add_update_listener(async_reload_entry))
    
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    if unload_ok := await hass.config_entries.async_unload_platforms(entry, PLATFORMS):
        # Close MySQL connection
        client = hass.data[DOMAIN][entry.entry_id]["client"]
        await hass.async_add_executor_job(client.close)
        
        hass.data[DOMAIN].pop(entry.entry_id)
    
    return unload_ok


async def async_reload_entry(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Reload config entry."""
    await async_unload_entry(hass, entry)
    await async_setup_entry(hass, entry)


class MySQLDataCoordinator(DataUpdateCoordinator):
    """Class to manage fetching MySQL data."""
    
    def __init__(
        self,
        hass: HomeAssistant,
        client: MySQLClient,
        entry: ConfigEntry,
    ) -> None:
        """Initialize."""
        self.client = client
        self.entry = entry
        
        # Get options
        scan_interval = entry.options.get(
            "scan_interval", DEFAULT_SCAN_INTERVAL
        )
        self.include_dbs = [
            db.strip() 
            for db in entry.options.get("include_dbs", "").split(",") 
            if db.strip()
        ]
        self.exclude_dbs = [
            db.strip() 
            for db in entry.options.get("exclude_dbs", "").split(",") 
            if db.strip()
        ]
        
        # Feature flags
        self.enable_query_cache = entry.options.get(CONF_ENABLE_QUERY_CACHE, False)
        self.enable_replication = entry.options.get(CONF_ENABLE_REPLICATION, False)
        
        super().__init__(
            hass,
            _LOGGER,
            name=f"MySQL Monitor ({entry.data['host']})",
            update_interval=timedelta(seconds=scan_interval),
        )
    
    async def _async_update_data(self):
        """Fetch data from MySQL."""
        try:
            data = await self.hass.async_add_executor_job(
                self._fetch_data
            )
            # Convert all Decimal objects to float
            return convert_decimal(data)
        except Exception as err:
            _LOGGER.error("Error fetching MySQL data: %s", err)
            raise UpdateFailed(f"Error communicating with MySQL: {err}") from err
    
    def _fetch_data(self):
        """Fetch all MySQL data."""
        data = {}
        
        try:
            # Get server info
            data["server_info"] = self.client.get_server_info()
            
            # Get global status
            data["global_status"] = self.client.get_global_status()
            
            # Get global variables
            data["global_variables"] = self.client.get_global_variables()
            
            # Get InnoDB status
            data["innodb_status"] = self.client.get_innodb_status()
            
            # Get performance schema data
            data["performance_data"] = self.client.get_performance_data()
            
            # Get process list
            data["process_list"] = self.client.get_process_list()
            
            # Get replication status (conditional)
            if self.enable_replication:
                data["replication_status"] = self.client.get_replication_status()
            else:
                data["replication_status"] = {}
            
            # Get system resource usage
            data["system_resources"] = self.client.get_system_resources()
            
            # Get database sizes
            data["database_sizes"] = self.client.get_database_sizes(
                self.include_dbs, self.exclude_dbs
            )
            
            # Get table statistics
            data["table_stats"] = self.client.get_table_statistics(
                self.include_dbs, self.exclude_dbs
            )
            
            # Get query cache info (conditional)
            if self.enable_query_cache:
                data["query_cache"] = self.client.get_query_cache_info()
            else:
                data["query_cache"] = {"enabled": False}
            
            # Get binary log info
            data["binlog_info"] = self.client.get_binlog_info()
            
            # Get connection pool stats
            data["connection_pool"] = self.client.get_connection_pool_stats()
            
            # Get slow query stats
            data["slow_queries"] = self.client.get_slow_query_stats()
            
            # Get table lock waits
            data["lock_waits"] = self.client.get_lock_wait_stats()
            
            # Get buffer pool stats
            data["buffer_pool"] = self.client.get_buffer_pool_stats()
            
            # Get transaction info
            data["transactions"] = self.client.get_transaction_info()
            
            # Get storage engine stats
            data["storage_engines"] = self.client.get_storage_engine_stats()
            
            # Store feature flags
            data["features"] = {
                "query_cache": self.enable_query_cache,
                "replication": self.enable_replication,
            }
            
        except Exception as err:
            _LOGGER.error("Error in _fetch_data: %s", err)
            raise
        
        return data
