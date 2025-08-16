# Home Assistant MySQL Monitor Integration

A comprehensive MySQL monitoring integration for Home Assistant that provides detailed insights into your MySQL server performance, resource usage, and database statistics.

## Features

- 🖥️ **System Resource Monitoring**: CPU, Memory, Disk I/O
- 📊 **MySQL Performance Metrics**: Connections, Queries, InnoDB, Cache
- 💾 **Database Analytics**: Size tracking, table statistics
- 🔍 **Advanced Monitoring**: Transactions, locks, replication, binlog
- 📈 **Real-time Graphs**: Historical data with Home Assistant graphs
- 🚨 **Automation Ready**: Trigger alerts based on any metric

## Quick Start

1. Copy to your `custom_components` directory
2. Restart Home Assistant
3. Add integration via UI
4. Enter MySQL connection details

## Requirements

- Home Assistant 2023.1+
- MySQL 5.7+ (8.0+ recommended)
- Python packages: pymysql, psutil

## Documentation

- [Installation Guide](INSTALLATION.md)
- [Configuration Examples](EXAMPLES.md)
- [README (English)](custom_components/mysql_monitor/README.md)

## Support

- GitHub: https://github.com/pageskr/ha-mysql-monitor
- Issues: https://github.com/pageskr/ha-mysql-monitor/issues

## Author

**Pages in Korea** (@pageskr)

## License

This project is provided for the Home Assistant community.
