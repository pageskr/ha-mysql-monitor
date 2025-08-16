# MySQL Monitor Integration Installation Guide

## Prerequisites

- Home Assistant 2023.1 or newer
- MySQL Server 5.7 or newer (8.0+ recommended)
- MySQL user with appropriate permissions

## Installation Steps

### 1. Manual Installation

1. Download or clone this repository
2. Copy the `custom_components/mysql_monitor` folder to your Home Assistant configuration directory:
   ```
   <config_dir>/custom_components/mysql_monitor/
   ```
3. Restart Home Assistant

### 2. HACS Installation (Coming Soon)

This integration will be available through HACS in the future.

## Configuration

### 1. Add Integration

1. Go to Settings → Devices & Services
2. Click "+ ADD INTEGRATION"
3. Search for "MySQL Monitor"
4. Click on it to start configuration

### 2. Connection Setup

Enter the following information:

- **Host**: Your MySQL server address (e.g., 192.168.1.100 or mysql.local)
- **Port**: MySQL port (default: 3306)
- **Username**: MySQL username (recommend read-only user)
- **Password**: MySQL password
- **Use SSL**: Enable if your MySQL server requires SSL
- **SSL CA Certificate**: Path to CA certificate file (if using SSL)
- **Verify SSL**: Whether to verify SSL certificate

### 3. Options Configuration

After initial setup, you can configure:

- **Include Databases**: Comma-separated list of databases to monitor
  - Example: `myapp,wordpress,logs`
  - Leave empty to monitor all databases
  
- **Exclude Databases**: Comma-separated list of databases to exclude
  - Example: `test,temp_db`
  - System databases are automatically excluded
  
- **Update Interval**: How often to fetch data (in seconds)
  - Minimum: 10 seconds
  - Maximum: 3600 seconds (1 hour)
  - Recommended: 60-120 seconds for production systems

## MySQL User Setup

### Minimum Required Permissions

```sql
-- Create monitoring user
CREATE USER 'homeassistant'@'%' IDENTIFIED BY 'your_secure_password';

-- Grant minimum required permissions
GRANT SELECT, SHOW VIEW, REPLICATION CLIENT, PROCESS ON *.* TO 'homeassistant'@'%';

-- If using Performance Schema metrics
GRANT SELECT ON performance_schema.* TO 'homeassistant'@'%';

-- Apply permissions
FLUSH PRIVILEGES;
```

### Restrict Access by IP (Recommended)

```sql
-- Create user restricted to Home Assistant IP
CREATE USER 'homeassistant'@'192.168.1.50' IDENTIFIED BY 'your_secure_password';

-- Grant permissions
GRANT SELECT, SHOW VIEW, REPLICATION CLIENT, PROCESS ON *.* TO 'homeassistant'@'192.168.1.50';
GRANT SELECT ON performance_schema.* TO 'homeassistant'@'192.168.1.50';
FLUSH PRIVILEGES;
```

## SSL Configuration

### 1. MySQL Server SSL Setup

Ensure your MySQL server has SSL enabled:

```sql
SHOW VARIABLES LIKE '%ssl%';
```

### 2. Home Assistant SSL Client Setup

1. Copy your CA certificate to Home Assistant config directory:
   ```
   /config/mysql-ca.pem
   ```

2. In the integration setup:
   - Enable "Use SSL"
   - Set "SSL CA Certificate Path" to `/config/mysql-ca.pem`
   - Enable "Verify SSL Certificate"

## Verification

After setup, verify the integration is working:

1. Check for new entities under Developer Tools → States
2. Look for entities starting with `sensor.mysql_`
3. Check logs for any errors: Settings → System → Logs

## Troubleshooting

### Cannot Connect Error

1. Verify MySQL is accessible from Home Assistant:
   ```bash
   mysql -h your_mysql_host -u homeassistant -p
   ```

2. Check firewall rules allow connection on MySQL port

3. Verify user permissions:
   ```sql
   SHOW GRANTS FOR 'homeassistant'@'%';
   ```

### Missing Sensors

1. Some sensors require specific MySQL features:
   - Performance Schema must be enabled
   - Replication sensors only appear on master/slave setups
   - Query cache sensors require query cache to be enabled

2. Check integration logs for specific errors

### Performance Issues

1. Increase update interval for large databases
2. Use include/exclude filters to limit monitored databases
3. Monitor integration's impact on MySQL:
   ```sql
   SHOW PROCESSLIST;
   ```

## Support

For issues or questions:
- GitHub Issues: https://github.com/pageskr/ha-mysql-monitor/issues
- Home Assistant Community: https://community.home-assistant.io
