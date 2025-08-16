# MySQL Monitor Integration - Example Configurations

## Lovelace Dashboard Examples

### 1. Overview Dashboard

```yaml
title: MySQL Monitor
views:
  - title: Overview
    path: mysql-overview
    cards:
      - type: vertical-stack
        cards:
          - type: markdown
            content: |
              # MySQL Server Status
              **Host:** {{ state_attr('sensor.mysql_server_info', 'hostname') }}
              **Version:** {{ state_attr('sensor.mysql_server_info', 'version') }}
              **Uptime:** {{ state_attr('sensor.mysql_server_info', 'uptime_formatted') }}
          
          - type: horizontal-stack
            cards:
              - type: gauge
                entity: sensor.mysql_cpu_usage
                name: CPU Usage
                min: 0
                max: 100
                severity:
                  green: 0
                  yellow: 80
                  red: 95
              
              - type: gauge
                entity: sensor.mysql_memory_usage
                name: Memory Usage
                min: 0
                max: 100
                severity:
                  green: 0
                  yellow: 85
                  red: 95
          
          - type: entities
            title: Connection Statistics
            entities:
              - entity: sensor.mysql_threads_connected
                name: Active Connections
              - entity: sensor.mysql_max_used_connections
                name: Max Used Connections
              - entity: sensor.mysql_connections_usage
                name: Connection Pool Usage
          
          - type: entities
            title: Query Performance
            entities:
              - entity: sensor.mysql_queries
                name: Total Queries
              - entity: sensor.mysql_slow_queries
                name: Slow Queries
              - entity: sensor.mysql_query_cache_hit_rate
                name: Query Cache Hit Rate
```

### 2. Database Sizes Dashboard

```yaml
- title: Databases
  path: mysql-databases
  cards:
    - type: custom:auto-entities
      card:
        type: entities
        title: Database Sizes
      filter:
        include:
          - entity_id: sensor.mysql_db_*_size
      sort:
        method: state
        reverse: true
        numeric: true
    
    - type: history-graph
      title: Database Growth
      entities:
        - entity: sensor.mysql_db_myapp_size
        - entity: sensor.mysql_db_logs_size
      hours_to_show: 168
```

### 3. Performance Metrics Dashboard

```yaml
- title: Performance
  path: mysql-performance
  cards:
    - type: vertical-stack
      cards:
        - type: statistics-graph
          title: Query Rate
          entities:
            - sensor.mysql_queries
          stat_types:
            - change
          period:
            rolling_window:
              duration:
                hours: 24
        
        - type: entities
          title: InnoDB Buffer Pool
          entities:
            - entity: sensor.mysql_buffer_pool_hit_rate
              name: Hit Rate
            - entity: sensor.mysql_innodb_buffer_pool_pages_free
              name: Free Pages
            - entity: sensor.mysql_innodb_buffer_pool_pages_dirty
              name: Dirty Pages
```

## Automation Examples

### 1. High Resource Usage Alert

```yaml
automation:
  - alias: "MySQL High Resource Alert"
    description: "Alert when MySQL uses too many resources"
    trigger:
      - platform: numeric_state
        entity_id: sensor.mysql_cpu_usage
        above: 90
        for:
          minutes: 5
      - platform: numeric_state
        entity_id: sensor.mysql_memory_usage
        above: 90
        for:
          minutes: 5
    condition:
      - condition: time
        after: "08:00:00"
        before: "22:00:00"
    action:
      - service: notify.mobile_app
        data:
          title: "⚠️ MySQL Alert"
          message: >
            MySQL resource usage is critical!
            CPU: {{ states('sensor.mysql_cpu_usage') }}%
            Memory: {{ states('sensor.mysql_memory_usage') }}%
          data:
            importance: high
            channel: alerts
```

### 2. Database Size Monitoring

```yaml
automation:
  - alias: "Database Size Warning"
    description: "Warn when database grows too large"
    trigger:
      - platform: template
        value_template: >
          {{ states('sensor.mysql_db_production_size')|float(0) > 10737418240 }}
    action:
      - service: notify.email_admin
        data:
          title: "Database Size Warning"
          message: >
            Production database has exceeded 10GB.
            Current size: {{ (states('sensor.mysql_db_production_size')|float / 1073741824)|round(2) }}GB
```

### 3. Slow Query Alert

```yaml
automation:
  - alias: "MySQL Slow Query Alert"
    description: "Alert on slow query increase"
    trigger:
      - platform: state
        entity_id: sensor.mysql_slow_queries
    condition:
      - condition: template
        value_template: >
          {{ (trigger.to_state.state|int - trigger.from_state.state|int) > 10 }}
    action:
      - service: notify.slack
        data:
          message: >
            ⚠️ MySQL slow queries increased by 
            {{ trigger.to_state.state|int - trigger.from_state.state|int }}
            in the last {{ states('input_number.mysql_scan_interval') }} seconds
```

### 4. Replication Lag Monitor

```yaml
automation:
  - alias: "MySQL Replication Lag"
    description: "Monitor replication lag"
    trigger:
      - platform: numeric_state
        entity_id: sensor.mysql_replication_status
        attribute: seconds_behind_master
        above: 60
    action:
      - service: notify.ops_team
        data:
          title: "MySQL Replication Lag"
          message: >
            Replication lag detected: 
            {{ state_attr('sensor.mysql_replication_status', 'seconds_behind_master') }} seconds
```

### 5. Connection Pool Exhaustion

```yaml
automation:
  - alias: "MySQL Connection Pool Alert"
    description: "Alert when connection pool is nearly exhausted"
    trigger:
      - platform: numeric_state
        entity_id: sensor.mysql_connections_usage
        above: 85
    action:
      - service: persistent_notification.create
        data:
          title: "MySQL Connection Warning"
          message: >
            Connection pool usage is at {{ states('sensor.mysql_connections_usage') }}%.
            Active: {{ state_attr('sensor.mysql_connections_usage', 'active_connections') }}
            Max: {{ state_attr('sensor.mysql_connections_usage', 'max_connections') }}
```

## Template Sensors

### 1. Human-Readable Database Sizes

```yaml
template:
  - sensor:
      - name: "MySQL Production DB Size GB"
        unit_of_measurement: "GB"
        state: >
          {{ (states('sensor.mysql_db_production_size')|float(0) / 1073741824)|round(2) }}
        
      - name: "MySQL Total Database Size"
        unit_of_measurement: "GB"
        state: >
          {% set ns = namespace(total=0) %}
          {% for state in states.sensor if state.entity_id.endswith('_size') and 'mysql_db_' in state.entity_id %}
            {% set ns.total = ns.total + state.state|float(0) %}
          {% endfor %}
          {{ (ns.total / 1073741824)|round(2) }}
```

### 2. Query Rate Calculations

```yaml
template:
  - sensor:
      - name: "MySQL Queries Per Second"
        unit_of_measurement: "q/s"
        state: >
          {% set current = states('sensor.mysql_queries')|int(0) %}
          {% set previous = state_attr('sensor.mysql_queries', 'last_value')|int(current) %}
          {% set interval = states('input_number.mysql_scan_interval')|int(60) %}
          {{ ((current - previous) / interval)|round(2) }}
```

### 3. InnoDB Efficiency Metrics

```yaml
template:
  - sensor:
      - name: "MySQL InnoDB Read Efficiency"
        unit_of_measurement: "%"
        state: >
          {% set requests = states('sensor.mysql_innodb_buffer_pool_read_requests')|float(1) %}
          {% set reads = states('sensor.mysql_innodb_buffer_pool_reads')|float(0) %}
          {% if requests > 0 %}
            {{ (100 * (1 - (reads / requests)))|round(2) }}
          {% else %}
            0
          {% endif %}
```

## Scripts

### 1. MySQL Performance Report

```yaml
script:
  mysql_performance_report:
    alias: "Generate MySQL Performance Report"
    sequence:
      - service: notify.email_admin
        data:
          title: "MySQL Performance Report"
          message: |
            MySQL Performance Report - {{ now().strftime('%Y-%m-%d %H:%M') }}
            
            Server Information:
            - Version: {{ state_attr('sensor.mysql_server_info', 'version') }}
            - Uptime: {{ state_attr('sensor.mysql_server_info', 'uptime_formatted') }}
            
            Resource Usage:
            - CPU: {{ states('sensor.mysql_cpu_usage') }}%
            - Memory: {{ states('sensor.mysql_memory_usage') }}%
            - Connections: {{ states('sensor.mysql_connections_usage') }}%
            
            Performance Metrics:
            - Queries: {{ states('sensor.mysql_queries') }}
            - Slow Queries: {{ states('sensor.mysql_slow_queries') }}
            - Query Cache Hit Rate: {{ states('sensor.mysql_query_cache_hit_rate') }}%
            - Buffer Pool Hit Rate: {{ states('sensor.mysql_buffer_pool_hit_rate') }}%
            
            Top Databases by Size:
            {% for state in states.sensor | selectattr('entity_id', 'match', 'sensor.mysql_db_.*_size') | sort(attribute='state', reverse=true) %}
            - {{ state.name }}: {{ (state.state|float / 1073741824)|round(2) }} GB
            {% endfor %}
```

### 2. MySQL Health Check

```yaml
script:
  mysql_health_check:
    alias: "MySQL Health Check"
    sequence:
      - choose:
          - conditions:
              - condition: numeric_state
                entity_id: sensor.mysql_cpu_usage
                above: 90
            sequence:
              - service: notify.mobile_app
                data:
                  message: "MySQL CPU usage critical: {{ states('sensor.mysql_cpu_usage') }}%"
          - conditions:
              - condition: numeric_state
                entity_id: sensor.mysql_connections_usage
                above: 80
            sequence:
              - service: notify.mobile_app
                data:
                  message: "MySQL connection pool high: {{ states('sensor.mysql_connections_usage') }}%"
        default:
          - service: notify.mobile_app
            data:
              message: "MySQL health check passed ✅"
```

## Input Helpers for Configuration

```yaml
input_number:
  mysql_scan_interval:
    name: MySQL Scan Interval
    min: 10
    max: 300
    step: 10
    unit_of_measurement: seconds
    icon: mdi:timer

input_boolean:
  mysql_alerts_enabled:
    name: MySQL Alerts Enabled
    icon: mdi:bell

input_select:
  mysql_alert_severity:
    name: MySQL Alert Severity
    options:
      - Low
      - Medium
      - High
      - Critical
    icon: mdi:alert
```

## Notification Groups

```yaml
notify:
  - name: mysql_admins
    platform: group
    services:
      - service: mobile_app_admin_phone
      - service: email_admin
      - service: slack_ops_channel
```
