# Changelog

## Version 1.0.0 (2024-01-XX)

### Initial Release

#### Features
- **System Resource Monitoring**
  - CPU usage (system and MySQL process)
  - Memory usage (system and MySQL process)
  - Disk I/O statistics
  - Data directory disk usage

- **MySQL Performance Metrics**
  - Connection statistics (active, idle, max used)
  - Query performance (rates, slow queries)
  - InnoDB metrics (buffer pool, row operations, lock waits)
  - Query cache statistics
  - Network I/O (bytes sent/received)
  - Temporary tables and files
  - Lock statistics
  - Replication metrics

- **Database & Table Analytics**
  - Per-database size tracking
  - Table count per database
  - Row count estimates
  - Largest tables by size
  - Most fragmented tables
  - Tables without primary keys

- **Advanced Monitoring**
  - Transaction monitoring
  - Lock wait analysis
  - Binary log status
  - Performance Schema integration
  - Process list monitoring
  - Storage engine statistics

- **Integration Features**
  - Easy UI-based configuration
  - SSL/TLS support
  - Database include/exclude filters
  - Configurable update intervals
  - Multi-language support (English, Korean)

#### Security
- Support for read-only MySQL users
- SSL/TLS encryption
- IP-based access restrictions

#### Documentation
- Comprehensive installation guide
- Security best practices
- Example dashboards and automations
- Troubleshooting guide

---

For future updates and releases, check:
https://github.com/pageskr/ha-mysql-monitor/releases
