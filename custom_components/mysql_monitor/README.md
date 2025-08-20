# MySQL Monitor for Home Assistant

A comprehensive MySQL monitoring integration for Home Assistant that provides detailed insights into your MySQL server performance, resource usage, and database statistics.

## Features

### 🖥️ System Resource Monitoring
- **CPU Usage**: Overall system CPU usage
- **Memory Usage**: System memory consumption
- **Server Info**: Version, uptime, configuration details

### 📊 MySQL Performance Metrics
- **Connection Statistics**: Active, idle, and maximum connections
- **Query Performance**: Query rates, slow queries, query cache hit rates
- **InnoDB Metrics**: Buffer pool usage, row operations, data I/O
- **Replication Status**: Master/slave status and lag monitoring (optional)

### 💾 Database & Table Analytics
- **Database Sizes**: Track size, table count, and row counts per database
- **Table Statistics**: Largest tables, fragmented tables, tables without primary keys
- **Storage Engine Stats**: Usage by storage engine type

### 🔍 Advanced Monitoring
- **Transaction Monitoring**: Active transactions, long-running queries
- **Binary Log Status**: Binlog file sizes and positions
- **Performance Schema**: Top queries, table I/O, user statistics
- **Connection Errors**: Comprehensive error tracking

## Installation

1. Copy the `mysql_monitor` folder to your Home Assistant `custom_components` directory
2. Restart Home Assistant
3. Go to Configuration > Integrations > Add Integration > MySQL Monitor
4. Enter your MySQL connection details

## Configuration

### Connection Settings
- **Host**: MySQL server hostname or IP address
- **Port**: MySQL server port (default: 3306)
- **Username**: MySQL username
- **Password**: MySQL password
- **SSL Options**: Enable SSL and configure certificates

### Options
- **Include Databases**: Comma-separated list of databases to monitor (empty = all)
- **Exclude Databases**: Comma-separated list of databases to exclude
- **Update Interval**: How often to fetch data (10-3600 seconds)
- **Enable Query Cache Monitoring**: Monitor query cache metrics (optional)
- **Enable Replication Monitoring**: Monitor replication status (optional)

## Security Recommendations

### Create a Read-Only User
```sql
CREATE USER 'ha_monitor'@'%' IDENTIFIED BY 'strong_password';
GRANT SELECT, SHOW VIEW, REPLICATION CLIENT, PROCESS ON *.* TO 'ha_monitor'@'%';
GRANT SELECT ON performance_schema.* TO 'ha_monitor'@'%';
FLUSH PRIVILEGES;
```

### Network Security
- Restrict MySQL access to Home Assistant IP only
- Use SSL/TLS for connections
- Configure firewall rules appropriately

## Sensors Created

### Global Status Sensors
- Connections (threads_connected, threads_running, connection_errors)
- Queries (queries, questions, slow_queries, etc.)
- InnoDB metrics (buffer pool, data I/O, row operations)
- Cache statistics (query cache hits/misses) - optional
- Network I/O (bytes sent/received)
- Temporary tables and files
- Replication metrics - optional

### System Resource Sensors
- `sensor.mysql_cpu_usage`: Overall CPU usage
- `sensor.mysql_memory_usage`: Overall memory usage

### Database Sensors (per database)
- `sensor.mysql_db_[name]_size`: Database size in bytes
- `sensor.mysql_db_[name]_tables`: Number of tables
- `sensor.mysql_db_[name]_rows`: Estimated total rows

### Performance Sensors
- `sensor.mysql_query_cache_hit_rate`: Query cache effectiveness (optional)
- `sensor.mysql_buffer_pool_hit_rate`: InnoDB buffer pool effectiveness
- `sensor.mysql_connections_usage`: Connection pool usage percentage
- `sensor.mysql_slow_queries`: Number of slow queries
- `sensor.mysql_active_transactions`: Number of active transactions

## Automation Examples

### Alert on High CPU Usage
```yaml
automation:
  - alias: "MySQL High CPU Alert"
    trigger:
      - platform: numeric_state
        entity_id: sensor.mysql_cpu_usage
        above: 90
        for: "00:05:00"
    action:
      - service: notify.mobile_app
        data:
          title: "MySQL Alert"
          message: "MySQL CPU usage is above 90%!"
```

### Monitor Database Growth
```yaml
automation:
  - alias: "Database Size Alert"
    trigger:
      - platform: numeric_state
        entity_id: sensor.mysql_db_myapp_size
        above: 10737418240  # 10GB in bytes
    action:
      - service: notify.email
        data:
          title: "Database Size Warning"
          message: "MyApp database has exceeded 10GB"
```

## Dashboard Examples

### Basic Monitoring Card
```yaml
type: entities
title: MySQL Status
entities:
  - entity: sensor.mysql_server_info
  - entity: sensor.mysql_connections_usage
  - entity: sensor.mysql_cpu_usage
  - entity: sensor.mysql_memory_usage
  - entity: sensor.mysql_slow_queries
```

### Database Size Graph
```yaml
type: history-graph
title: Database Sizes
entities:
  - entity: sensor.mysql_db_app_size
  - entity: sensor.mysql_db_logs_size
hours_to_show: 168
```

## Troubleshooting

### Connection Issues
- Verify MySQL user permissions
- Check firewall/network settings
- Ensure MySQL is listening on the correct interface
- Test SSL certificate paths if using SSL

### Missing Metrics
- Some metrics require specific MySQL configurations
- Performance Schema must be enabled for advanced metrics
- Replication metrics only appear on configured master/slave servers

### Performance Impact
- Increase update interval for large deployments
- Consider excluding large databases from detailed monitoring
- Monitor the integration's impact on MySQL performance

## Requirements

- Home Assistant 2023.1 or newer
- MySQL 5.7 or newer (MySQL 8.0+ recommended)
- Python packages: pymysql, psutil

## Author

**Pages in Korea (pages.kr)** (@pageskr)

## License

This integration is provided as-is for the Home Assistant community.

## Support

For issues and feature requests, please visit:
https://github.com/pageskr/ha-mysql-monitor/issues
