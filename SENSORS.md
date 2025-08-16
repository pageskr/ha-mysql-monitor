# MySQL Monitor Sensor List

This document provides a complete list of all sensors created by the MySQL Monitor integration.

## System Resource Sensors

| Sensor ID | Name | Description | Unit |
|-----------|------|-------------|------|
| `sensor.mysql_cpu_usage` | CPU Usage | Overall system CPU usage | % |
| `sensor.mysql_memory_usage` | Memory Usage | Overall system memory usage | % |
| `sensor.mysql_data_directory_usage` | Data Directory Usage | MySQL data directory disk usage | % |
| `sensor.mysql_mysql_cpu_usage` | MySQL CPU Usage | MySQL process CPU usage | % |
| `sensor.mysql_mysql_memory_usage` | MySQL Memory Usage | MySQL process memory usage | % |

## Connection Sensors

| Sensor ID | Name | Description | Unit |
|-----------|------|-------------|------|
| `sensor.mysql_threads_connected` | Threads Connected | Currently connected threads | count |
| `sensor.mysql_threads_running` | Threads Running | Currently running threads | count |
| `sensor.mysql_max_used_connections` | Max Used Connections | Peak connection count | count |
| `sensor.mysql_aborted_clients` | Aborted Clients | Failed client connections | count |
| `sensor.mysql_aborted_connects` | Aborted Connects | Failed connection attempts | count |
| `sensor.mysql_connection_errors_*` | Connection Errors | Various connection error types | count |
| `sensor.mysql_connections_usage` | Connections Usage | Connection pool usage percentage | % |

## Query Sensors

| Sensor ID | Name | Description | Unit |
|-----------|------|-------------|------|
| `sensor.mysql_queries` | Queries | Total queries executed | count |
| `sensor.mysql_questions` | Questions | Client queries | count |
| `sensor.mysql_slow_queries` | Slow Queries | Queries exceeding long_query_time | count |
| `sensor.mysql_com_select` | Com Select | SELECT statements | count |
| `sensor.mysql_com_insert` | Com Insert | INSERT statements | count |
| `sensor.mysql_com_update` | Com Update | UPDATE statements | count |
| `sensor.mysql_com_delete` | Com Delete | DELETE statements | count |
| `sensor.mysql_com_replace` | Com Replace | REPLACE statements | count |
| `sensor.mysql_com_commit` | Com Commit | COMMIT statements | count |
| `sensor.mysql_com_rollback` | Com Rollback | ROLLBACK statements | count |

## InnoDB Sensors

| Sensor ID | Name | Description | Unit |
|-----------|------|-------------|------|
| `sensor.mysql_innodb_buffer_pool_pages_total` | Buffer Pool Pages Total | Total buffer pool pages | count |
| `sensor.mysql_innodb_buffer_pool_pages_free` | Buffer Pool Pages Free | Free buffer pool pages | count |
| `sensor.mysql_innodb_buffer_pool_pages_dirty` | Buffer Pool Pages Dirty | Dirty buffer pool pages | count |
| `sensor.mysql_innodb_buffer_pool_pages_flushed` | Buffer Pool Pages Flushed | Flushed pages | count |
| `sensor.mysql_innodb_buffer_pool_read_requests` | Buffer Pool Read Requests | Read requests | count |
| `sensor.mysql_innodb_buffer_pool_reads` | Buffer Pool Reads | Physical reads | count |
| `sensor.mysql_innodb_buffer_pool_write_requests` | Buffer Pool Write Requests | Write requests | count |
| `sensor.mysql_innodb_buffer_pool_wait_free` | Buffer Pool Wait Free | Wait for free page | count |
| `sensor.mysql_innodb_data_read` | InnoDB Data Read | Bytes read | bytes |
| `sensor.mysql_innodb_data_written` | InnoDB Data Written | Bytes written | bytes |
| `sensor.mysql_innodb_os_log_written` | InnoDB Log Written | Log bytes written | bytes |
| `sensor.mysql_innodb_row_lock_waits` | Row Lock Waits | Row lock wait count | count |
| `sensor.mysql_innodb_row_lock_time` | Row Lock Time | Total lock wait time | ms |
| `sensor.mysql_innodb_rows_read` | Rows Read | Rows read | count |
| `sensor.mysql_innodb_rows_inserted` | Rows Inserted | Rows inserted | count |
| `sensor.mysql_innodb_rows_updated` | Rows Updated | Rows updated | count |
| `sensor.mysql_innodb_rows_deleted` | Rows Deleted | Rows deleted | count |

## Cache Sensors

| Sensor ID | Name | Description | Unit |
|-----------|------|-------------|------|
| `sensor.mysql_qcache_hits` | Query Cache Hits | Cache hit count | count |
| `sensor.mysql_qcache_inserts` | Query Cache Inserts | Cache insert count | count |
| `sensor.mysql_qcache_lowmem_prunes` | Query Cache Lowmem Prunes | Queries removed due to low memory | count |
| `sensor.mysql_qcache_not_cached` | Query Cache Not Cached | Uncacheable queries | count |
| `sensor.mysql_qcache_queries_in_cache` | Queries In Cache | Current cached queries | count |
| `sensor.mysql_qcache_total_blocks` | Query Cache Total Blocks | Total cache blocks | count |
| `sensor.mysql_qcache_free_blocks` | Query Cache Free Blocks | Free cache blocks | count |
| `sensor.mysql_qcache_free_memory` | Query Cache Free Memory | Free cache memory | bytes |
| `sensor.mysql_query_cache_hit_rate` | Query Cache Hit Rate | Cache effectiveness | % |

## Network Sensors

| Sensor ID | Name | Description | Unit |
|-----------|------|-------------|------|
| `sensor.mysql_bytes_received` | Bytes Received | Network bytes received | bytes |
| `sensor.mysql_bytes_sent` | Bytes Sent | Network bytes sent | bytes |

## Temporary Table Sensors

| Sensor ID | Name | Description | Unit |
|-----------|------|-------------|------|
| `sensor.mysql_created_tmp_disk_tables` | Created Tmp Disk Tables | Disk-based temp tables | count |
| `sensor.mysql_created_tmp_files` | Created Tmp Files | Temporary files created | count |
| `sensor.mysql_created_tmp_tables` | Created Tmp Tables | Temporary tables created | count |

## Lock Sensors

| Sensor ID | Name | Description | Unit |
|-----------|------|-------------|------|
| `sensor.mysql_table_locks_immediate` | Table Locks Immediate | Immediate table locks | count |
| `sensor.mysql_table_locks_waited` | Table Locks Waited | Table lock waits | count |
| `sensor.mysql_innodb_row_lock_current_waits` | Current Row Lock Waits | Active row lock waits | count |
| `sensor.mysql_innodb_row_lock_time_avg` | Avg Row Lock Time | Average lock wait time | ms |
| `sensor.mysql_innodb_row_lock_time_max` | Max Row Lock Time | Maximum lock wait time | ms |
| `sensor.mysql_lock_waits` | Lock Waits | Current lock wait count | count |

## Performance Sensors

| Sensor ID | Name | Description | Unit |
|-----------|------|-------------|------|
| `sensor.mysql_buffer_pool_hit_rate` | Buffer Pool Hit Rate | InnoDB buffer pool effectiveness | % |
| `sensor.mysql_slow_query_count` | Slow Query Count | Number of slow queries | count |
| `sensor.mysql_transaction_count` | Active Transactions | Active transaction count | count |

## Database Sensors (per database)

For each monitored database, the following sensors are created:

| Sensor ID Pattern | Name Pattern | Description | Unit |
|-------------------|--------------|-------------|------|
| `sensor.mysql_db_[name]_size` | DB [name] Size | Database size | bytes |
| `sensor.mysql_db_[name]_tables` | DB [name] Tables | Number of tables | count |
| `sensor.mysql_db_[name]_rows` | DB [name] Rows | Estimated row count | count |

## Replication Sensors

| Sensor ID | Name | Description | Unit |
|-----------|------|-------------|------|
| `sensor.mysql_replication_status` | Replication Status | Master/Slave status | text |

### Replication Attributes

The replication sensor includes these attributes:
- `role`: master or slave
- `master_host`: Master server (slave only)
- `io_running`: IO thread status (slave only)
- `sql_running`: SQL thread status (slave only)
- `seconds_behind_master`: Replication lag (slave only)
- `binlog_file`: Current binlog file (master only)
- `binlog_position`: Current binlog position (master only)

## Server Info Sensor

| Sensor ID | Name | Description | Unit |
|-----------|------|-------------|------|
| `sensor.mysql_server_info` | Server Info | MySQL version and status | text |

### Server Info Attributes

- `version`: MySQL version
- `hostname`: Server hostname
- `datadir`: Data directory path
- `uptime_seconds`: Server uptime in seconds
- `uptime_formatted`: Human-readable uptime
- `max_connections`: Maximum allowed connections
- `innodb_buffer_pool_size`: Buffer pool size
- `query_cache_size`: Query cache size

## Sensor Attributes

Most sensors include additional attributes with related metrics and detailed information. Common attributes include:

- **Status sensors**: Related metrics from the same category
- **Resource sensors**: Detailed resource usage breakdown
- **Database sensors**: Table statistics, largest tables
- **Performance sensors**: Configuration values, detailed statistics

## Notes

1. Database sensors are created dynamically based on discovered databases
2. Some sensors require specific MySQL features to be enabled (e.g., Performance Schema)
3. Replication sensors only appear on configured master/slave servers
4. All numeric sensors support graphing in Home Assistant
5. Sensor updates occur based on the configured scan interval
