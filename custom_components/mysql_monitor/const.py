"""Constants for MySQL Monitor integration."""

DOMAIN = "mysql_monitor"

# Default values
DEFAULT_PORT = 3306
DEFAULT_SCAN_INTERVAL = 60

# Configuration keys
CONF_USE_SSL = "use_ssl"
CONF_SSL_CA = "ssl_ca"
CONF_SSL_VERIFY = "ssl_verify"
CONF_INCLUDE_DBS = "include_dbs"
CONF_EXCLUDE_DBS = "exclude_dbs"
CONF_SCAN_INTERVAL = "scan_interval"
CONF_ENABLE_QUERY_CACHE = "enable_query_cache"
CONF_ENABLE_REPLICATION = "enable_replication"

# System databases to exclude
SYSTEM_DATABASES = [
    "information_schema",
    "mysql",
    "performance_schema",
    "sys",
]

# Connection error metrics to aggregate
CONNECTION_ERROR_METRICS = [
    "Connection_errors_accept",
    "Connection_errors_internal",
    "Connection_errors_max_connections",
    "Connection_errors_peer_address",
    "Connection_errors_select",
    "Connection_errors_tcpwrap",
]

# Metric categories
METRIC_CATEGORIES = {
    "connections": [
        "Threads_connected",
        "Threads_running",
        "Max_used_connections",
        "Aborted_clients",
        "Aborted_connects",
    ],
    "queries": [
        "Queries",
        "Questions",
        "Slow_queries",
        "Com_select",
        "Com_insert",
        "Com_update",
        "Com_delete",
        "Com_replace",
        "Com_commit",
        "Com_rollback",
    ],
    "innodb": [
        "Innodb_buffer_pool_pages_total",
        "Innodb_buffer_pool_pages_free",
        "Innodb_buffer_pool_pages_dirty",
        "Innodb_buffer_pool_pages_flushed",
        "Innodb_buffer_pool_read_requests",
        "Innodb_buffer_pool_reads",
        "Innodb_buffer_pool_write_requests",
        "Innodb_buffer_pool_wait_free",
        "Innodb_data_read",
        "Innodb_data_written",
        "Innodb_os_log_written",
        "Innodb_rows_read",
        "Innodb_rows_inserted",
        "Innodb_rows_updated",
        "Innodb_rows_deleted",
    ],
    "network": [
        "Bytes_received",
        "Bytes_sent",
    ],
    "temp_tables": [
        "Created_tmp_disk_tables",
        "Created_tmp_files",
        "Created_tmp_tables",
    ],
}

# Query cache metrics (conditional)
QUERY_CACHE_METRICS = [
    "Qcache_hits",
    "Qcache_inserts",
    "Qcache_lowmem_prunes",
    "Qcache_not_cached",
    "Qcache_queries_in_cache",
    "Qcache_total_blocks",
    "Qcache_free_blocks",
    "Qcache_free_memory",
]

# Replication metrics (conditional)
REPLICATION_METRICS = [
    "Rpl_semi_sync_master_clients",
    "Rpl_semi_sync_master_net_waits",
    "Rpl_semi_sync_master_no_tx",
    "Rpl_semi_sync_master_status",
    "Rpl_semi_sync_master_tx_avg_wait_time",
    "Rpl_semi_sync_master_tx_wait_time",
    "Rpl_semi_sync_master_tx_waits",
    "Rpl_semi_sync_master_wait_pos_backtraverse",
    "Rpl_semi_sync_master_wait_sessions",
    "Rpl_semi_sync_master_yes_tx",
]

# Units for metrics
METRIC_UNITS = {
    "bytes": [
        "Bytes_received",
        "Bytes_sent",
        "Innodb_data_read",
        "Innodb_data_written",
        "Innodb_os_log_written",
        "Qcache_free_memory",
    ],
    "milliseconds": [],
    "percentage": [],
}

# Sensor icons
SENSOR_ICONS = {
    "default": "mdi:database",
    "connections": "mdi:connection",
    "queries": "mdi:database-search",
    "innodb": "mdi:database-cog",
    "cache": "mdi:cached",
    "network": "mdi:network",
    "temp_tables": "mdi:table",
    "locks": "mdi:lock",
    "replication": "mdi:database-sync",
    "cpu": "mdi:cpu-64-bit",
    "memory": "mdi:memory",
    "disk": "mdi:harddisk",
    "size": "mdi:database",
    "tables": "mdi:table-multiple",
    "rows": "mdi:table-row",
    "errors": "mdi:alert-circle",
}

# Resource monitor thresholds
RESOURCE_THRESHOLDS = {
    "cpu_warning": 80,
    "cpu_critical": 95,
    "memory_warning": 85,
    "memory_critical": 95,
    "disk_warning": 80,
    "disk_critical": 90,
    "connections_warning": 80,
    "connections_critical": 95,
}
