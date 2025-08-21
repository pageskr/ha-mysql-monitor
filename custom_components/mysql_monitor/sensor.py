"""Sensor platform for MySQL Monitor."""
import logging
from typing import Any, Dict, List, Optional

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import (
    PERCENTAGE,
    UnitOfInformation,
    UnitOfTime,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceEntryType, DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import (
    CoordinatorEntity,
    DataUpdateCoordinator,
)

from .const import (
    DOMAIN,
    METRIC_CATEGORIES,
    METRIC_UNITS,
    QUERY_CACHE_METRICS,
    REPLICATION_METRICS,
    CONNECTION_ERROR_METRICS,
    RESOURCE_THRESHOLDS,
    SENSOR_ICONS,
)

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up MySQL Monitor sensors."""
    coordinator = hass.data[DOMAIN][entry.entry_id]["coordinator"]
    
    sensors = []
    
    # Get feature flags
    features = coordinator.data.get("features", {})
    enable_query_cache = features.get("query_cache", False)
    enable_replication = features.get("replication", False)
    
    # Server info sensor
    sensors.append(MySQLServerInfoSensor(coordinator, entry))
    
    # Global status sensors (Slow_queries는 여기서 제외)
    for category, metrics in METRIC_CATEGORIES.items():
        for metric in metrics:
            if metric != "Slow_queries":  # Slow_queries는 별도 처리
                sensors.append(
                    MySQLGlobalStatusSensor(coordinator, entry, metric, category)
                )
    
    # Connection Errors aggregate sensor
    sensors.append(MySQLConnectionErrorsSensor(coordinator, entry))
    
    # Query cache sensors (conditional)
    if enable_query_cache:
        for metric in QUERY_CACHE_METRICS:
            sensors.append(
                MySQLGlobalStatusSensor(coordinator, entry, metric, "cache")
            )
    
    # Replication sensors (conditional)
    if enable_replication:
        for metric in REPLICATION_METRICS:
            sensors.append(
                MySQLGlobalStatusSensor(coordinator, entry, metric, "replication")
            )
    
    # System resource sensors
    sensors.extend([
        MySQLSystemResourceSensor(coordinator, entry, "cpu_percent", "CPU Usage"),
        MySQLSystemResourceSensor(coordinator, entry, "memory_percent", "Memory Usage"),
    ])
    
    # Database size sensors
    if coordinator.data and "database_sizes" in coordinator.data:
        for db_name in coordinator.data["database_sizes"]:
            sensors.extend([
                MySQLDatabaseSensor(coordinator, entry, db_name, "total_size", "Size"),
                MySQLDatabaseSensor(coordinator, entry, db_name, "table_count", "Tables"),
                MySQLDatabaseSensor(coordinator, entry, db_name, "total_rows", "Rows"),
            ])
    
    # Performance sensors
    sensors.extend([
        MySQLPerformanceSensor(coordinator, entry, "buffer_pool_hit_rate"),
        MySQLPerformanceSensor(coordinator, entry, "connections_usage"),
        MySQLPerformanceSensor(coordinator, entry, "slow_query_logs"),  # 이름 변경
        MySQLPerformanceSensor(coordinator, entry, "transaction_count"),
    ])
    
    # Query cache hit rate sensor (conditional)
    if enable_query_cache:
        sensors.append(MySQLPerformanceSensor(coordinator, entry, "query_cache_hit_rate"))
    
    # Replication sensors (conditional)
    if enable_replication and coordinator.data.get("replication_status"):
        sensors.append(MySQLReplicationSensor(coordinator, entry))
    
    async_add_entities(sensors)


class MySQLBaseSensor(CoordinatorEntity, SensorEntity):
    """Base class for MySQL sensors."""
    
    def __init__(
        self,
        coordinator: DataUpdateCoordinator,
        entry: ConfigEntry,
        sensor_type: str,
        name_suffix: str,
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator)
        self._entry = entry
        self._sensor_type = sensor_type
        self._name_suffix = name_suffix
    
    @property
    def unique_id(self) -> str:
        """Return unique ID."""
        return f"{self._entry.entry_id}_{self._sensor_type}"
    
    @property
    def name(self) -> str:
        """Return the name."""
        return f"MySQL {self._name_suffix}"
    
    @property
    def device_info(self) -> DeviceInfo:
        """Return device information."""
        return DeviceInfo(
            identifiers={(DOMAIN, self._entry.entry_id)},
            name=f"MySQL {self._entry.data['host']}:{self._entry.data['port']}",
            manufacturer="Pages in Korea (pages.kr)",
            model="MySQL Server",
            entry_type=DeviceEntryType.SERVICE,
        )


class MySQLServerInfoSensor(MySQLBaseSensor):
    """MySQL server information sensor."""
    
    def __init__(self, coordinator: DataUpdateCoordinator, entry: ConfigEntry) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator, entry, "server_info", "Server Info")
        self._attr_icon = SENSOR_ICONS["default"]
    
    @property
    def native_value(self) -> str:
        """Return the state."""
        if self.coordinator.data and "server_info" in self.coordinator.data:
            info = self.coordinator.data["server_info"]
            return f"MySQL {info.get('version', 'Unknown')}"
        return "Unknown"
    
    @property
    def extra_state_attributes(self) -> Dict[str, Any]:
        """Return state attributes."""
        if not self.coordinator.data or "server_info" not in self.coordinator.data:
            return {}
        
        info = self.coordinator.data["server_info"]
        attrs = {
            "version": info.get("version"),
            "hostname": info.get("hostname"),
            "datadir": info.get("datadir"),
            "uptime_seconds": info.get("uptime"),
        }
        
        # Add uptime in human readable format
        if info.get("uptime"):
            uptime = info["uptime"]
            days = uptime // 86400
            hours = (uptime % 86400) // 3600
            minutes = (uptime % 3600) // 60
            attrs["uptime_formatted"] = f"{days}d {hours}h {minutes}m"
        
        # Add global variables
        if "global_variables" in self.coordinator.data:
            vars_data = self.coordinator.data["global_variables"]
            attrs["max_connections"] = vars_data.get("max_connections")
            attrs["innodb_buffer_pool_size"] = vars_data.get("innodb_buffer_pool_size")
            # query_cache_size를 정수로 변환
            cache_size = vars_data.get("query_cache_size", "0")
            try:
                attrs["query_cache_size"] = int(cache_size)
            except (ValueError, TypeError):
                attrs["query_cache_size"] = 0
            attrs["version_comment"] = vars_data.get("version_comment")
            # innodb_lock_wait_timeout 추가
            lock_timeout = vars_data.get("innodb_lock_wait_timeout", "50")
            try:
                attrs["innodb_lock_wait_timeout"] = int(lock_timeout)
            except (ValueError, TypeError):
                attrs["innodb_lock_wait_timeout"] = 50
        
        # Add system resource info
        if "system_resources" in self.coordinator.data:
            resources = self.coordinator.data["system_resources"]
            attrs["cpu_count"] = resources.get("cpu_count")
            attrs["memory_total_gb"] = round(resources.get("memory_total", 0) / (1024**3), 2)
            attrs["datadir_total_gb"] = round(resources.get("datadir_total", 0) / (1024**3), 2)
            attrs["datadir_percent"] = round(resources.get("datadir_percent", 0), 2)
        
        # Add table lock statistics from global_status
        if "global_status" in self.coordinator.data:
            status = self.coordinator.data["global_status"]
            try:
                attrs["table_locks_immediate"] = int(status.get("Table_locks_immediate", 0))
                attrs["table_locks_waited"] = int(status.get("Table_locks_waited", 0))
            except (ValueError, TypeError):
                pass
        
        return attrs


class MySQLGlobalStatusSensor(MySQLBaseSensor):
    """MySQL global status metric sensor."""
    
    def __init__(
        self,
        coordinator: DataUpdateCoordinator,
        entry: ConfigEntry,
        metric: str,
        category: str,
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator, entry, metric.lower(), metric.replace("_", " ").title())
        self._metric = metric
        self._category = category
        self._attr_icon = SENSOR_ICONS.get(category, SENSOR_ICONS["default"])
        self._attr_state_class = SensorStateClass.MEASUREMENT
        
        # Set unit of measurement
        if metric in METRIC_UNITS["bytes"]:
            self._attr_device_class = SensorDeviceClass.DATA_SIZE
            self._attr_native_unit_of_measurement = UnitOfInformation.BYTES
        elif metric in METRIC_UNITS["milliseconds"]:
            self._attr_device_class = SensorDeviceClass.DURATION
            self._attr_native_unit_of_measurement = UnitOfTime.MILLISECONDS
        elif metric in METRIC_UNITS["percentage"]:
            self._attr_native_unit_of_measurement = PERCENTAGE
    
    @property
    def native_value(self) -> Optional[float]:
        """Return the state."""
        if not self.coordinator.data or "global_status" not in self.coordinator.data:
            return None
        
        value = self.coordinator.data["global_status"].get(self._metric)
        if value is not None:
            try:
                return float(value)
            except (ValueError, TypeError):
                return None
        return None
    
    @property
    def extra_state_attributes(self) -> Dict[str, Any]:
        """Return state attributes."""
        attrs = {
            "category": self._category,
            "metric": self._metric,
        }
        
        # Add related metrics from the same category
        if self.coordinator.data and "global_status" in self.coordinator.data:
            status = self.coordinator.data["global_status"]
            
            # Determine which metrics to include
            if self._category == "cache":
                related_metrics = QUERY_CACHE_METRICS
            elif self._category == "replication":
                related_metrics = REPLICATION_METRICS
            else:
                related_metrics = METRIC_CATEGORIES.get(self._category, [])
            
            for metric in related_metrics:
                if metric != self._metric and metric in status:
                    try:
                        attrs[metric.lower()] = float(status[metric])
                    except (ValueError, TypeError):
                        attrs[metric.lower()] = status[metric]
            
            # Add lock statistics for InnoDB metrics from global_status
            if self._category == "innodb":
                # InnoDB lock metrics from global_status
                lock_metrics = [
                    "Innodb_row_lock_waits",
                    "Innodb_row_lock_time",
                    "Innodb_row_lock_time_avg",
                    "Innodb_row_lock_time_max",
                    "Innodb_row_lock_current_waits",
                ]
                
                for metric in lock_metrics:
                    value = status.get(metric)
                    if value is not None:
                        try:
                            attrs[metric.lower()] = int(value)
                        except (ValueError, TypeError):
                            attrs[metric.lower()] = value
        
        return attrs


class MySQLConnectionErrorsSensor(MySQLBaseSensor):
    """MySQL connection errors aggregate sensor."""
    
    def __init__(self, coordinator: DataUpdateCoordinator, entry: ConfigEntry) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator, entry, "connection_errors", "Connection Errors")
        self._attr_icon = SENSOR_ICONS["errors"]
        self._attr_state_class = SensorStateClass.MEASUREMENT
    
    @property
    def native_value(self) -> Optional[int]:
        """Return the total of all connection errors."""
        if not self.coordinator.data or "global_status" not in self.coordinator.data:
            return None
        
        status = self.coordinator.data["global_status"]
        total = 0
        
        for error_metric in CONNECTION_ERROR_METRICS:
            value = status.get(error_metric, 0)
            try:
                total += int(value)
            except (ValueError, TypeError):
                pass
        
        return total
    
    @property
    def extra_state_attributes(self) -> Dict[str, Any]:
        """Return state attributes with individual error counts."""
        attrs = {}
        
        if self.coordinator.data and "global_status" in self.coordinator.data:
            status = self.coordinator.data["global_status"]
            
            for error_metric in CONNECTION_ERROR_METRICS:
                value = status.get(error_metric, 0)
                try:
                    attrs[error_metric.lower()] = int(value)
                except (ValueError, TypeError):
                    attrs[error_metric.lower()] = 0
        
        return attrs


class MySQLSystemResourceSensor(MySQLBaseSensor):
    """MySQL system resource sensor."""
    
    def __init__(
        self,
        coordinator: DataUpdateCoordinator,
        entry: ConfigEntry,
        resource_type: str,
        name: str,
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator, entry, f"system_{resource_type}", name)
        self._resource_type = resource_type
        self._attr_state_class = SensorStateClass.MEASUREMENT
        self._attr_native_unit_of_measurement = PERCENTAGE
        
        if "cpu" in resource_type:
            self._attr_icon = SENSOR_ICONS["cpu"]
        elif "memory" in resource_type:
            self._attr_icon = SENSOR_ICONS["memory"]
    
    @property
    def native_value(self) -> Optional[float]:
        """Return the state."""
        if not self.coordinator.data or "system_resources" not in self.coordinator.data:
            return None
        
        resources = self.coordinator.data["system_resources"]
        value = resources.get(self._resource_type)
        
        if value is not None:
            return round(float(value), 2)
        return None
    
    @property
    def extra_state_attributes(self) -> Dict[str, Any]:
        """Return state attributes."""
        if not self.coordinator.data or "system_resources" not in self.coordinator.data:
            return {}
        
        resources = self.coordinator.data["system_resources"]
        attrs = {}
        
        # Add relevant system resource data
        if "cpu" in self._resource_type:
            attrs["cpu_count"] = resources.get("cpu_count")
            # Add threshold status
            if self.native_value is not None:
                if self.native_value >= RESOURCE_THRESHOLDS["cpu_critical"]:
                    attrs["status"] = "critical"
                elif self.native_value >= RESOURCE_THRESHOLDS["cpu_warning"]:
                    attrs["status"] = "warning"
                else:
                    attrs["status"] = "normal"
        elif "memory" in self._resource_type:
            attrs["memory_total_gb"] = round(resources.get("memory_total", 0) / (1024**3), 2)
            attrs["memory_used_gb"] = round(resources.get("memory_used", 0) / (1024**3), 2)
            attrs["memory_available_gb"] = round(resources.get("memory_available", 0) / (1024**3), 2)
            # Add threshold status
            if self.native_value is not None:
                if self.native_value >= RESOURCE_THRESHOLDS["memory_critical"]:
                    attrs["status"] = "critical"
                elif self.native_value >= RESOURCE_THRESHOLDS["memory_warning"]:
                    attrs["status"] = "warning"
                else:
                    attrs["status"] = "normal"
        
        return attrs


class MySQLDatabaseSensor(MySQLBaseSensor):
    """MySQL database metric sensor."""
    
    def __init__(
        self,
        coordinator: DataUpdateCoordinator,
        entry: ConfigEntry,
        db_name: str,
        metric_type: str,
        name_suffix: str,
    ) -> None:
        """Initialize the sensor."""
        super().__init__(
            coordinator,
            entry,
            f"db_{db_name}_{metric_type}",
            f"DB {db_name} {name_suffix}"
        )
        self._db_name = db_name
        self._metric_type = metric_type
        self._attr_state_class = SensorStateClass.MEASUREMENT
        
        if metric_type == "total_size":
            self._attr_device_class = SensorDeviceClass.DATA_SIZE
            self._attr_native_unit_of_measurement = UnitOfInformation.BYTES
            self._attr_icon = SENSOR_ICONS["size"]
        elif metric_type == "table_count":
            self._attr_icon = SENSOR_ICONS["tables"]
        else:  # total_rows
            self._attr_icon = SENSOR_ICONS["rows"]
    
    @property
    def native_value(self) -> Optional[float]:
        """Return the state."""
        if not self.coordinator.data or "database_sizes" not in self.coordinator.data:
            return None
        
        db_data = self.coordinator.data["database_sizes"].get(self._db_name, {})
        value = db_data.get(self._metric_type)
        
        if value is not None:
            return float(value)
        return None
    
    @property
    def extra_state_attributes(self) -> Dict[str, Any]:
        """Return state attributes."""
        if not self.coordinator.data or "database_sizes" not in self.coordinator.data:
            return {}
        
        db_data = self.coordinator.data["database_sizes"].get(self._db_name, {})
        attrs = {
            "database": self._db_name,
        }
        
        # Add all database metrics
        for key, value in db_data.items():
            attrs[key] = value
        
        # Add table statistics if available
        if "table_stats" in self.coordinator.data:
            table_stats = self.coordinator.data["table_stats"]
            
            # Find largest tables for this database
            if "largest_tables" in table_stats:
                db_tables = [
                    t for t in table_stats["largest_tables"]
                    if t.get("table_schema") == self._db_name
                ]
                if db_tables:
                    attrs["largest_tables"] = db_tables[:5]  # Top 5 tables
        
        return attrs


class MySQLPerformanceSensor(MySQLBaseSensor):
    """MySQL performance metric sensor."""
    
    def __init__(
        self,
        coordinator: DataUpdateCoordinator,
        entry: ConfigEntry,
        metric_type: str,
    ) -> None:
        """Initialize the sensor."""
        name_map = {
            "query_cache_hit_rate": "Query Cache Hit Rate",
            "buffer_pool_hit_rate": "Buffer Pool Hit Rate",
            "connections_usage": "Connections Usage",
            "slow_query_logs": "Slow Query Logs",  # 변경됨
            "transaction_count": "Active Transactions",
        }
        super().__init__(coordinator, entry, metric_type, name_map.get(metric_type, metric_type))
        self._metric_type = metric_type
        self._attr_state_class = SensorStateClass.MEASUREMENT
        
        if "rate" in metric_type or "usage" in metric_type:
            self._attr_native_unit_of_measurement = PERCENTAGE
            self._attr_icon = "mdi:gauge"
        elif "count" in metric_type or "logs" in metric_type:
            self._attr_icon = "mdi:counter"
    
    @property
    def native_value(self) -> Optional[float]:
        """Return the state."""
        if not self.coordinator.data:
            return None
        
        if self._metric_type == "query_cache_hit_rate":
            cache_info = self.coordinator.data.get("query_cache", {})
            if cache_info.get("enabled"):
                return round(cache_info.get("hit_rate", 0), 2)
            
        elif self._metric_type == "buffer_pool_hit_rate":
            buffer_pool = self.coordinator.data.get("buffer_pool", {})
            return round(buffer_pool.get("avg_hit_rate", 0), 2)
            
        elif self._metric_type == "connections_usage":
            conn_pool = self.coordinator.data.get("connection_pool", {})
            return round(conn_pool.get("connection_usage_pct", 0), 2)
            
        elif self._metric_type == "slow_query_logs":
            # global_status에서 Slow_queries 값을 가져옴
            if "global_status" in self.coordinator.data:
                status = self.coordinator.data["global_status"]
                slow_queries = status.get("Slow_queries", 0)
                try:
                    return int(slow_queries)
                except (ValueError, TypeError):
                    return 0
            return 0
            
        elif self._metric_type == "transaction_count":
            transactions = self.coordinator.data.get("transactions", {})
            return transactions.get("transaction_count", 0)
        
        return None
    
    @property
    def extra_state_attributes(self) -> Dict[str, Any]:
        """Return state attributes."""
        attrs = {}
        
        if not self.coordinator.data:
            return attrs
        
        if self._metric_type == "query_cache_hit_rate":
            cache_info = self.coordinator.data.get("query_cache", {})
            if cache_info.get("enabled"):
                attrs.update({
                    "hits": cache_info.get("hits"),
                    "inserts": cache_info.get("inserts"),
                    "queries_in_cache": cache_info.get("queries_in_cache"),
                    "free_memory": cache_info.get("free_memory"),
                })
                
        elif self._metric_type == "buffer_pool_hit_rate":
            buffer_pool = self.coordinator.data.get("buffer_pool", {})
            attrs.update({
                "total_size": buffer_pool.get("total_size"),
                "total_free": buffer_pool.get("total_free"),
                "usage_pct": buffer_pool.get("usage_pct"),
                "dirty_pct": buffer_pool.get("dirty_pct"),
            })
            
        elif self._metric_type == "connections_usage":
            conn_pool = self.coordinator.data.get("connection_pool", {})
            attrs.update({
                "total_connections": conn_pool.get("total_connections"),
                "active_connections": conn_pool.get("active_connections"),
                "idle_connections": conn_pool.get("idle_connections"),
                "max_connections": conn_pool.get("max_connections"),
                "max_used_connections": conn_pool.get("max_used_connections"),
            })
            
        elif self._metric_type == "slow_query_logs":
            # slow_queries 데이터에서 정보 가져오기
            slow_queries = self.coordinator.data.get("slow_queries", {})
            attrs.update({
                "enabled": slow_queries.get("enabled"),
                "long_query_time": slow_queries.get("long_query_time"),
                "log_file": slow_queries.get("slow_query_log_file"),
            })
            
            # Add current lock wait count from lock_waits data
            if "lock_waits" in self.coordinator.data:
                lock_data = self.coordinator.data["lock_waits"]
                current_waits = lock_data.get("current_lock_waits", [])
                attrs["current_lock_waits"] = len(current_waits)
            
            # Add slow query related global status
            if "global_status" in self.coordinator.data:
                status = self.coordinator.data["global_status"]
                attrs["questions"] = status.get("Questions")
                attrs["queries"] = status.get("Queries")
            
        elif self._metric_type == "transaction_count":
            transactions = self.coordinator.data.get("transactions", {})
            attrs.update({
                "long_running_count": len(transactions.get("long_running_transactions", [])),
                "isolation_level": transactions.get("default_isolation_level"),
                "commits": transactions.get("Com_commit"),
                "rollbacks": transactions.get("Com_rollback"),
            })
        
        return attrs


class MySQLReplicationSensor(MySQLBaseSensor):
    """MySQL replication status sensor."""
    
    def __init__(self, coordinator: DataUpdateCoordinator, entry: ConfigEntry) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator, entry, "replication", "Replication Status")
        self._attr_icon = SENSOR_ICONS["replication"]
    
    @property
    def native_value(self) -> str:
        """Return the state."""
        if not self.coordinator.data or "replication_status" not in self.coordinator.data:
            return "Not Configured"
        
        repl_data = self.coordinator.data["replication_status"]
        
        if repl_data.get("slave"):
            slave_data = repl_data["slave"]
            io_running = slave_data.get("Slave_IO_Running") == "Yes"
            sql_running = slave_data.get("Slave_SQL_Running") == "Yes"
            
            if io_running and sql_running:
                return "Slave Running"
            elif io_running or sql_running:
                return "Slave Partial"
            else:
                return "Slave Stopped"
        
        if repl_data.get("master"):
            return "Master"
        
        return "Not Configured"
    
    @property
    def extra_state_attributes(self) -> Dict[str, Any]:
        """Return state attributes."""
        if not self.coordinator.data or "replication_status" not in self.coordinator.data:
            return {}
        
        attrs = {}
        repl_data = self.coordinator.data["replication_status"]
        
        if repl_data.get("master"):
            master = repl_data["master"]
            attrs.update({
                "role": "master",
                "binlog_file": master.get("File"),
                "binlog_position": master.get("Position"),
                "binlog_do_db": master.get("Binlog_Do_DB"),
                "binlog_ignore_db": master.get("Binlog_Ignore_DB"),
            })
        
        if repl_data.get("slave"):
            slave = repl_data["slave"]
            attrs.update({
                "role": "slave",
                "master_host": slave.get("Master_Host"),
                "master_port": slave.get("Master_Port"),
                "io_running": slave.get("Slave_IO_Running"),
                "sql_running": slave.get("Slave_SQL_Running"),
                "seconds_behind_master": slave.get("Seconds_Behind_Master"),
                "last_io_error": slave.get("Last_IO_Error"),
                "last_sql_error": slave.get("Last_SQL_Error"),
            })
        
        return attrs
