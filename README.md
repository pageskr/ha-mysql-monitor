# MySQL Monitor for Home Assistant

[![hacs_badge](https://img.shields.io/badge/HACS-Custom-41BDF5.svg)](https://github.com/hacs/integration)
[![GitHub Release](https://img.shields.io/github/release/pageskr/ha-mysql-monitor.svg)](https://github.com/pageskr/ha-mysql-monitor/releases)
[![License](https://img.shields.io/github/license/pageskr/ha-mysql-monitor.svg)](LICENSE)

A comprehensive MySQL monitoring integration for Home Assistant that provides detailed insights into your MySQL/MariaDB server performance, resource usage, and database statistics.

## 🚀 Features

### 📊 Performance Monitoring
- **Real-time Metrics**: Track queries, connections, and throughput
- **Query Performance**: Monitor slow queries and query cache effectiveness
- **InnoDB Engine**: Buffer pool hit rates, I/O operations, row-level operations
- **Connection Pool**: Active/idle connections, connection errors tracking
- **Transaction Monitoring**: Active transactions and isolation levels

### 💾 Database Analytics
- **Database Metrics**: Size, table count, and row statistics per database
- **Table Analysis**: Largest tables, fragmented tables, tables without primary keys
- **Storage Engines**: Usage statistics by storage engine type
- **Binary Logs**: Binlog file tracking and positions

### 🖥️ System Resources
- **CPU Usage**: Overall system CPU utilization
- **Memory Usage**: System memory consumption and availability
- **Disk Space**: Data directory usage monitoring
- **Process Stats**: MySQL process-specific resource usage (when available)

### 🔧 Advanced Features
- **Replication Monitoring**: Master/slave status and replication lag (optional)
- **Query Cache Analysis**: Hit rates and memory usage (optional)
- **Lock Wait Statistics**: Current lock waits and historical data
- **Performance Schema**: Top queries and table I/O statistics
- **Custom Alerts**: Create automations based on any metric

## 📋 Requirements

- Home Assistant 2023.1 or newer
- MySQL 5.7+ or MariaDB 10.2+ (MySQL 8.0+ recommended)
- MySQL user with appropriate permissions

## 🛠️ Installation

### HACS Installation (Recommended)

1. Open HACS in your Home Assistant instance
2. Click on "Integrations"
3. Click the three dots in the top right corner and select "Custom repositories"
4. Add repository URL: `https://github.com/pageskr/ha-mysql-monitor`
5. Select category: "Integration"
6. Click "Add"
7. Search for "MySQL Monitor" in HACS
8. Click "Download" and select the latest version
9. Restart Home Assistant

### Manual Installation

1. Download the latest release from [GitHub Releases](https://github.com/pageskr/ha-mysql-monitor/releases)
2. Extract the `mysql_monitor` folder to your `custom_components` directory:
   ```
   custom_components/
   └── mysql_monitor/
       ├── __init__.py
       ├── manifest.json
       ├── sensor.py
       └── ...
   ```
3. Restart Home Assistant

## ⚙️ Configuration

### Step 1: Create MySQL User

Create a dedicated read-only user for monitoring:

```sql
CREATE USER 'homeassistant'@'%' IDENTIFIED BY 'your_secure_password';

-- Grant minimum required permissions
GRANT SELECT, SHOW VIEW, REPLICATION CLIENT, PROCESS ON *.* TO 'homeassistant'@'%';

-- For Performance Schema metrics (optional but recommended)
GRANT SELECT ON performance_schema.* TO 'homeassistant'@'%';

-- Apply permissions
FLUSH PRIVILEGES;
```

**Security Note**: Replace `%` with your Home Assistant IP address for better security:
```sql
CREATE USER 'homeassistant'@'192.168.1.100' IDENTIFIED BY 'your_secure_password';
```

### Step 2: Add Integration

1. Go to **Settings** → **Devices & Services**
2. Click **+ ADD INTEGRATION**
3. Search for "MySQL Monitor"
4. Enter connection details:
   - **Host**: MySQL server address
   - **Port**: MySQL port (default: 3306)
   - **Username**: MySQL username
   - **Password**: MySQL password
   - **SSL Options**: Configure if using SSL/TLS

### Step 3: Configure Options

After setup, click **CONFIGURE** to adjust:

- **Include Databases**: Comma-separated list (empty = all databases)
  ```
  Example: production,staging,wordpress
  ```
- **Exclude Databases**: Comma-separated list to exclude
  ```
  Example: test,temp_db
  ```
- **Update Interval**: Data refresh rate in seconds (10-3600)
- **Enable Query Cache**: Monitor query cache metrics
- **Enable Replication**: Monitor replication status

## 📊 Sensors Created

### System Sensors
| Sensor | Description | Unit |
|--------|-------------|------|
| `sensor.mysql_server_info` | Server version and status | - |
| `sensor.mysql_cpu_usage` | System CPU usage | % |
| `sensor.mysql_memory_usage` | System memory usage | % |

### Connection Sensors
| Sensor | Description | Unit |
|--------|-------------|------|
| `sensor.mysql_threads_connected` | Currently connected threads | count |
| `sensor.mysql_threads_running` | Currently running threads | count |
| `sensor.mysql_max_used_connections` | Historical maximum connections | count |
| `sensor.mysql_connections_usage` | Connection pool usage | % |
| `sensor.mysql_connection_errors` | Total connection errors | count |

### Query Performance
| Sensor | Description | Unit |
|--------|-------------|------|
| `sensor.mysql_queries` | Total queries executed | count |
| `sensor.mysql_questions` | Statements sent by clients | count |
| `sensor.mysql_slow_query_logs` | Slow queries count | count |
| `sensor.mysql_com_select` | SELECT statements | count |
| `sensor.mysql_com_insert` | INSERT statements | count |
| `sensor.mysql_com_update` | UPDATE statements | count |
| `sensor.mysql_com_delete` | DELETE statements | count |

### InnoDB Metrics
| Sensor | Description | Unit |
|--------|-------------|------|
| `sensor.mysql_buffer_pool_hit_rate` | Buffer pool effectiveness | % |
| `sensor.mysql_innodb_buffer_pool_pages_*` | Buffer pool page statistics | count |
| `sensor.mysql_innodb_data_read` | Data read | bytes |
| `sensor.mysql_innodb_data_written` | Data written | bytes |
| `sensor.mysql_innodb_rows_*` | Row operations | count |

### Database Sensors (per database)
| Sensor Pattern | Description | Unit |
|----------------|-------------|------|
| `sensor.mysql_db_[name]_size` | Database size | bytes |
| `sensor.mysql_db_[name]_tables` | Number of tables | count |
| `sensor.mysql_db_[name]_rows` | Estimated row count | count |

### Optional Sensors
- **Query Cache**: Hit rate, memory usage (when enabled)
- **Replication**: Master/Slave status, lag time (when enabled)

## 🔔 Automation Examples

### High CPU Alert
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
          title: "⚠️ MySQL Alert"
          message: "MySQL server CPU usage is above 90%!"
```

### Database Size Monitor
```yaml
automation:
  - alias: "Database Size Warning"
    trigger:
      - platform: numeric_state
        entity_id: sensor.mysql_db_production_size
        above: 10737418240  # 10GB
    action:
      - service: notify.email
        data:
          title: "Database Size Alert"
          message: >
            Production database exceeded 10GB.
            Current size: {{ (states('sensor.mysql_db_production_size')|float / 1073741824)|round(2) }}GB
```

### Connection Pool Alert
```yaml
automation:
  - alias: "MySQL Connection Pool Critical"
    trigger:
      - platform: numeric_state
        entity_id: sensor.mysql_connections_usage
        above: 85
    action:
      - service: persistent_notification.create
        data:
          title: "MySQL Connection Warning"
          message: >
            Connection pool usage: {{ states('sensor.mysql_connections_usage') }}%
            Active: {{ state_attr('sensor.mysql_connections_usage', 'active_connections') }}
            Max: {{ state_attr('sensor.mysql_connections_usage', 'max_connections') }}
```

## 📈 Dashboard Examples

### Overview Card
```yaml
type: vertical-stack
cards:
  - type: entities
    title: MySQL Status
    entities:
      - entity: sensor.mysql_server_info
      - entity: sensor.mysql_cpu_usage
      - entity: sensor.mysql_memory_usage
      - entity: sensor.mysql_connections_usage
      
  - type: horizontal-stack
    cards:
      - type: gauge
        entity: sensor.mysql_buffer_pool_hit_rate
        name: Buffer Hit Rate
        min: 0
        max: 100
        severity:
          green: 95
          yellow: 85
          red: 0
          
      - type: gauge
        entity: sensor.mysql_connections_usage
        name: Connections
        min: 0
        max: 100
        severity:
          green: 0
          yellow: 70
          red: 85
```

### Database Growth Chart
```yaml
type: history-graph
title: Database Growth
entities:
  - entity: sensor.mysql_db_production_size
  - entity: sensor.mysql_db_staging_size
hours_to_show: 168
refresh_interval: 600
```

### Performance Metrics
```yaml
type: custom:mini-graph-card
title: Query Performance
entities:
  - entity: sensor.mysql_queries
    name: Total Queries
  - entity: sensor.mysql_slow_query_logs
    name: Slow Queries
    y_axis: secondary
hours_to_show: 24
points_per_hour: 4
show:
  labels: true
  labels_secondary: true
```

## 🔍 Troubleshooting

### Connection Issues

1. **Test MySQL connection**:
   ```bash
   mysql -h your_mysql_host -u homeassistant -p
   ```

2. **Check permissions**:
   ```sql
   SHOW GRANTS FOR 'homeassistant'@'%';
   ```

3. **Verify firewall rules** allow connection on MySQL port

4. **For SSL issues**, ensure certificate paths are correct and accessible

### Missing Sensors

- **Performance Schema metrics**: Ensure `performance_schema = ON` in MySQL config
- **Replication metrics**: Only appear on configured master/slave servers
- **Query Cache**: May be disabled in MySQL 8.0+ (deprecated feature)

### High Resource Usage

1. Increase update interval (60-300 seconds recommended)
2. Exclude large or unnecessary databases
3. Monitor integration's impact via MySQL process list

## 🛡️ Security Best Practices

1. **Use dedicated read-only user** - Never use root or admin accounts
2. **Restrict access by IP** - Limit MySQL user to Home Assistant's IP
3. **Enable SSL/TLS** - Encrypt connections between HA and MySQL
4. **Regular password rotation** - Update credentials periodically
5. **Monitor access logs** - Check for unauthorized access attempts

## 📝 Sensor Attributes

Most sensors include detailed attributes for deeper insights:

### Server Info Attributes
- Version details, uptime, configuration
- Global variables (max_connections, buffer sizes)
- Lock timeout settings

### Connection Error Attributes
- Breakdown by error type
- Individual error counters

### Database Sensor Attributes
- Detailed size breakdown (data/index/free)
- Top 5 largest tables
- Fragmentation statistics

### InnoDB Sensor Attributes
- Lock wait statistics
- Row lock metrics
- Detailed buffer pool stats

## 🤝 Contributing

Contributions are welcome! Please:

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 👤 Author

**Pages in Korea (pages.kr)** (@pageskr)

- GitHub: [@pageskr](https://github.com/pageskr)
- Website: [pages.kr](https://pages.kr)

## 🙏 Acknowledgments

- Home Assistant Community
- MySQL/MariaDB developers
- Contributors and testers

## 📞 Support

- **Issues**: [GitHub Issues](https://github.com/pageskr/ha-mysql-monitor/issues)
- **Discussions**: [GitHub Discussions](https://github.com/pageskr/ha-mysql-monitor/discussions)
- **Documentation**: [Wiki](https://github.com/pageskr/ha-mysql-monitor/wiki)

---

Made with ❤️ for the Home Assistant Community
