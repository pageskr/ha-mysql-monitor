"""MySQL client for the integration."""
import logging
import re
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

import pymysql
import psutil

from .const import SYSTEM_DATABASES

_LOGGER = logging.getLogger(__name__)


class MySQLClient:
    """MySQL client wrapper."""
    
    def __init__(
        self,
        host: str,
        port: int,
        username: str,
        password: str,
        use_ssl: bool = False,
        ssl_ca: Optional[str] = None,
        ssl_verify: bool = True,
    ) -> None:
        """Initialize MySQL client."""
        self.host = host
        self.port = port
        self.username = username
        self.password = password
        self.use_ssl = use_ssl
        self.ssl_ca = ssl_ca
        self.ssl_verify = ssl_verify
        self._connection = None
    
    def _get_connection(self):
        """Get MySQL connection."""
        if self._connection is None or not self._connection.open:
            ssl_config = None
            if self.use_ssl:
                ssl_config = {
                    "ca": self.ssl_ca,
                    "check_hostname": self.ssl_verify,
                    "verify_mode": self.ssl_verify,
                }
            
            self._connection = pymysql.connect(
                host=self.host,
                port=self.port,
                user=self.username,
                password=self.password,
                charset="utf8mb4",
                cursorclass=pymysql.cursors.DictCursor,
                ssl=ssl_config,
                autocommit=True,
            )
        
        return self._connection
    
    def test_connection(self) -> bool:
        """Test MySQL connection."""
        try:
            conn = self._get_connection()
            with conn.cursor() as cursor:
                cursor.execute("SELECT 1")
                return True
        except Exception as err:
            _LOGGER.error("Failed to connect to MySQL: %s", err)
            raise
    
    def close(self):
        """Close MySQL connection."""
        if self._connection:
            self._connection.close()
            self._connection = None
    
    def get_server_info(self) -> Dict[str, Any]:
        """Get MySQL server information."""
        conn = self._get_connection()
        with conn.cursor() as cursor:
            cursor.execute("SELECT VERSION() as version")
            version = cursor.fetchone()["version"]
            
            cursor.execute("SELECT @@hostname as hostname")
            hostname = cursor.fetchone()["hostname"]
            
            cursor.execute("SHOW VARIABLES LIKE 'datadir'")
            datadir_result = cursor.fetchone()
            datadir = datadir_result["Value"] if datadir_result else None
            
            cursor.execute("SELECT NOW() as server_time")
            server_time = cursor.fetchone()["server_time"]
            
            cursor.execute("SHOW STATUS LIKE 'Uptime'")
            uptime_result = cursor.fetchone()
            uptime = int(uptime_result["Value"]) if uptime_result else 0
            
            return {
                "version": version,
                "hostname": hostname,
                "datadir": datadir,
                "current_time": server_time,
                "uptime": uptime,
            }
    
    def get_global_status(self) -> Dict[str, Any]:
        """Get MySQL global status."""
        conn = self._get_connection()
        with conn.cursor() as cursor:
            cursor.execute("SHOW GLOBAL STATUS")
            return {row["Variable_name"]: row["Value"] for row in cursor.fetchall()}
    
    def get_global_variables(self) -> Dict[str, Any]:
        """Get MySQL global variables."""
        conn = self._get_connection()
        with conn.cursor() as cursor:
            cursor.execute("SHOW GLOBAL VARIABLES")
            return {row["Variable_name"]: row["Value"] for row in cursor.fetchall()}
    
    def get_innodb_status(self) -> Dict[str, Any]:
        """Get and parse InnoDB engine status."""
        conn = self._get_connection()
        try:
            with conn.cursor() as cursor:
                cursor.execute("SHOW ENGINE INNODB STATUS")
                result = cursor.fetchone()
                if not result or "Status" not in result:
                    return {}
                
                status_text = result["Status"]
                
                # Parse InnoDB status
                parsed = {}
                
                # History list length
                match = re.search(r"History list length (\d+)", status_text)
                if match:
                    parsed["history_list_length"] = int(match.group(1))
                
                # Pending reads/writes
                match = re.search(r"Pending flushes \(fsync\) log: (\d+)", status_text)
                if match:
                    parsed["pending_log_flushes"] = int(match.group(1))
                
                # Checkpoint info
                match = re.search(r"Log sequence number\s+(\d+)", status_text)
                if match:
                    parsed["log_sequence_number"] = int(match.group(1))
                
                match = re.search(r"Log flushed up to\s+(\d+)", status_text)
                if match:
                    parsed["log_flushed_up_to"] = int(match.group(1))
                
                match = re.search(r"Last checkpoint at\s+(\d+)", status_text)
                if match:
                    parsed["last_checkpoint_at"] = int(match.group(1))
                
                # Pending I/O
                match = re.search(r"Pending normal aio reads: (\d+)", status_text)
                if match:
                    parsed["pending_aio_reads"] = int(match.group(1))
                
                match = re.search(r"Pending normal aio writes: (\d+)", status_text)
                if match:
                    parsed["pending_aio_writes"] = int(match.group(1))
                
                # Mutex info
                match = re.search(r"Mutex spin waits (\d+)", status_text)
                if match:
                    parsed["mutex_spin_waits"] = int(match.group(1))
                
                match = re.search(r"Mutex spin rounds (\d+)", status_text)
                if match:
                    parsed["mutex_spin_rounds"] = int(match.group(1))
                
                # Transaction info
                match = re.search(r"Trx id counter (\d+)", status_text)
                if match:
                    parsed["transaction_id_counter"] = int(match.group(1))
                
                # Deadlocks
                match = re.search(r"LATEST DETECTED DEADLOCK", status_text)
                parsed["has_recent_deadlock"] = bool(match)
                
                return parsed
        except Exception as err:
            _LOGGER.warning("Failed to get InnoDB status: %s", err)
            return {}
    
    def get_performance_data(self) -> Dict[str, Any]:
        """Get performance schema data if available."""
        conn = self._get_connection()
        data = {}
        
        try:
            with conn.cursor() as cursor:
                # Check if performance_schema is enabled
                cursor.execute("SHOW VARIABLES LIKE 'performance_schema'")
                result = cursor.fetchone()
                if not result or result["Value"] != "ON":
                    return {"enabled": False}
                
                data["enabled"] = True
                
                # Statement summary
                try:
                    cursor.execute("""
                        SELECT 
                            DIGEST_TEXT,
                            COUNT_STAR,
                            SUM_TIMER_WAIT,
                            SUM_LOCK_TIME,
                            SUM_ROWS_AFFECTED,
                            SUM_ROWS_SENT,
                            SUM_ROWS_EXAMINED
                        FROM performance_schema.events_statements_summary_by_digest
                        WHERE DIGEST_TEXT IS NOT NULL
                        ORDER BY SUM_TIMER_WAIT DESC
                        LIMIT 10
                    """)
                    data["top_statements"] = cursor.fetchall()
                except Exception:
                    data["top_statements"] = []
                
                # Table I/O summary
                try:
                    cursor.execute("""
                        SELECT 
                            OBJECT_SCHEMA,
                            OBJECT_NAME,
                            COUNT_STAR,
                            SUM_TIMER_WAIT,
                            COUNT_READ,
                            COUNT_WRITE,
                            COUNT_FETCH,
                            COUNT_INSERT,
                            COUNT_UPDATE,
                            COUNT_DELETE
                        FROM performance_schema.table_io_waits_summary_by_table
                        WHERE OBJECT_SCHEMA NOT IN %s
                            AND OBJECT_SCHEMA IS NOT NULL
                        ORDER BY SUM_TIMER_WAIT DESC
                        LIMIT 10
                    """, (SYSTEM_DATABASES,))
                    data["table_io_summary"] = cursor.fetchall()
                except Exception:
                    data["table_io_summary"] = []
                
                # File I/O summary
                try:
                    cursor.execute("""
                        SELECT 
                            FILE_NAME,
                            COUNT_STAR,
                            SUM_TIMER_WAIT,
                            COUNT_READ,
                            COUNT_WRITE,
                            SUM_NUMBER_OF_BYTES_READ,
                            SUM_NUMBER_OF_BYTES_WRITE
                        FROM performance_schema.file_summary_by_instance
                        WHERE FILE_NAME IS NOT NULL
                        ORDER BY SUM_TIMER_WAIT DESC
                        LIMIT 10
                    """)
                    data["file_io_summary"] = cursor.fetchall()
                except Exception:
                    data["file_io_summary"] = []
                
                # User summary
                try:
                    cursor.execute("""
                        SELECT 
                            USER,
                            CURRENT_CONNECTIONS,
                            TOTAL_CONNECTIONS
                        FROM performance_schema.users
                        WHERE USER IS NOT NULL
                    """)
                    data["user_summary"] = cursor.fetchall()
                except Exception:
                    data["user_summary"] = []
                
        except Exception as err:
            _LOGGER.warning("Failed to get performance schema data: %s", err)
            data["enabled"] = False
            data["error"] = str(err)
        
        return data
    
    def get_process_list(self) -> List[Dict[str, Any]]:
        """Get current process list."""
        conn = self._get_connection()
        try:
            with conn.cursor() as cursor:
                cursor.execute("""
                    SELECT 
                        ID,
                        USER,
                        HOST,
                        DB,
                        COMMAND,
                        TIME,
                        STATE,
                        INFO
                    FROM INFORMATION_SCHEMA.PROCESSLIST
                    WHERE COMMAND != 'Sleep'
                    ORDER BY TIME DESC
                    LIMIT 20
                """)
                return cursor.fetchall()
        except Exception as err:
            _LOGGER.warning("Failed to get process list: %s", err)
            return []
    
    def get_replication_status(self) -> Dict[str, Any]:
        """Get replication status."""
        conn = self._get_connection()
        data = {}
        
        try:
            with conn.cursor() as cursor:
                # Master status
                try:
                    cursor.execute("SHOW MASTER STATUS")
                    master = cursor.fetchone()
                    if master:
                        data["master"] = master
                except Exception:
                    pass
                
                # Slave status
                try:
                    cursor.execute("SHOW SLAVE STATUS")
                    slave = cursor.fetchone()
                    if slave:
                        data["slave"] = {
                            "Slave_IO_State": slave.get("Slave_IO_State"),
                            "Master_Host": slave.get("Master_Host"),
                            "Master_Port": slave.get("Master_Port"),
                            "Slave_IO_Running": slave.get("Slave_IO_Running"),
                            "Slave_SQL_Running": slave.get("Slave_SQL_Running"),
                            "Seconds_Behind_Master": slave.get("Seconds_Behind_Master"),
                            "Last_IO_Error": slave.get("Last_IO_Error"),
                            "Last_SQL_Error": slave.get("Last_SQL_Error"),
                            "Exec_Master_Log_Pos": slave.get("Exec_Master_Log_Pos"),
                            "Relay_Log_Pos": slave.get("Relay_Log_Pos"),
                        }
                except Exception:
                    pass
        except Exception as err:
            _LOGGER.debug("No replication configured: %s", err)
        
        return data
    
    def get_system_resources(self) -> Dict[str, Any]:
        """Get system resource usage of MySQL server."""
        data = {}
        
        try:
            # Get overall system stats
            data["cpu_percent"] = psutil.cpu_percent(interval=1)
            data["cpu_count"] = psutil.cpu_count()
            
            memory = psutil.virtual_memory()
            data["memory_total"] = memory.total
            data["memory_used"] = memory.used
            data["memory_available"] = memory.available
            data["memory_percent"] = memory.percent
            
            # Try to get MySQL process specific stats
            try:
                # Find MySQL process by connection
                for proc in psutil.process_iter(['pid', 'name', 'connections']):
                    try:
                        if 'mysql' in proc.info['name'].lower():
                            connections = proc.connections()
                            for conn in connections:
                                if conn.status == 'LISTEN' and conn.laddr.port == self.port:
                                    mysql_proc = proc
                                    
                                    # MySQL process specific stats
                                    data["mysql_cpu_percent"] = mysql_proc.cpu_percent(interval=0.1)
                                    data["mysql_memory_info"] = mysql_proc.memory_info()._asdict()
                                    data["mysql_memory_percent"] = mysql_proc.memory_percent()
                                    data["mysql_num_threads"] = mysql_proc.num_threads()
                                    data["mysql_connections"] = len(mysql_proc.connections())
                                    
                                    # I/O counters
                                    try:
                                        io_counters = mysql_proc.io_counters()
                                        data["mysql_io_read_count"] = io_counters.read_count
                                        data["mysql_io_write_count"] = io_counters.write_count
                                        data["mysql_io_read_bytes"] = io_counters.read_bytes
                                        data["mysql_io_write_bytes"] = io_counters.write_bytes
                                    except Exception:
                                        pass
                                    
                                    break
                    except (psutil.NoSuchProcess, psutil.AccessDenied):
                        continue
            except Exception as err:
                _LOGGER.debug("Could not get MySQL process stats: %s", err)
            
            # Disk usage for data directory
            try:
                conn = self._get_connection()
                with conn.cursor() as cursor:
                    cursor.execute("SHOW VARIABLES LIKE 'datadir'")
                    result = cursor.fetchone()
                    if result:
                        datadir = result["Value"]
                        disk_usage = psutil.disk_usage(datadir)
                        data["datadir_total"] = disk_usage.total
                        data["datadir_used"] = disk_usage.used
                        data["datadir_free"] = disk_usage.free
                        data["datadir_percent"] = disk_usage.percent
            except Exception as err:
                _LOGGER.debug("Could not get disk usage: %s", err)
        
        except Exception as err:
            _LOGGER.error("Failed to get system resources: %s", err)
        
        return data
    
    def get_database_sizes(
        self, 
        include_dbs: List[str], 
        exclude_dbs: List[str]
    ) -> Dict[str, Dict[str, Any]]:
        """Get database sizes and statistics."""
        conn = self._get_connection()
        with conn.cursor() as cursor:
            # Build WHERE clause for database filtering
            where_clauses = ["table_schema NOT IN %s"]
            params = [SYSTEM_DATABASES]
            
            if include_dbs:
                where_clauses = ["table_schema IN %s"]
                params = [include_dbs]
            elif exclude_dbs:
                # Combine system DBs and excluded DBs
                excluded = list(SYSTEM_DATABASES) + exclude_dbs
                params = [excluded]
            
            where_clause = " AND ".join(where_clauses)
            
            cursor.execute(f"""
                SELECT 
                    table_schema as db_name,
                    COUNT(DISTINCT table_name) as table_count,
                    SUM(table_rows) as total_rows,
                    SUM(data_length) as data_size,
                    SUM(index_length) as index_size,
                    SUM(data_length + index_length) as total_size,
                    SUM(data_free) as free_size
                FROM information_schema.tables
                WHERE {where_clause}
                GROUP BY table_schema
            """, params)
            
            databases = {}
            for row in cursor.fetchall():
                databases[row["db_name"]] = {
                    "table_count": row["table_count"] or 0,
                    "total_rows": row["total_rows"] or 0,
                    "data_size": row["data_size"] or 0,
                    "index_size": row["index_size"] or 0,
                    "total_size": row["total_size"] or 0,
                    "free_size": row["free_size"] or 0,
                }
            
            return databases
    
    def get_table_statistics(
        self,
        include_dbs: List[str],
        exclude_dbs: List[str],
        limit: int = 20
    ) -> Dict[str, List[Dict[str, Any]]]:
        """Get table statistics."""
        conn = self._get_connection()
        data = {}
        
        with conn.cursor() as cursor:
            # Build WHERE clause
            where_clauses = ["table_schema NOT IN %s"]
            params = [SYSTEM_DATABASES]
            
            if include_dbs:
                where_clauses = ["table_schema IN %s"]
                params = [include_dbs]
            elif exclude_dbs:
                excluded = list(SYSTEM_DATABASES) + exclude_dbs
                params = [excluded]
            
            where_clause = " AND ".join(where_clauses)
            
            try:
                # Largest tables by size
                cursor.execute(f"""
                    SELECT 
                        table_schema,
                        table_name,
                        table_rows,
                        data_length,
                        index_length,
                        data_length + index_length as total_size,
                        data_free
                    FROM information_schema.tables
                    WHERE {where_clause}
                        AND table_type = 'BASE TABLE'
                    ORDER BY (data_length + index_length) DESC
                    LIMIT %s
                """, params + [limit])
                data["largest_tables"] = cursor.fetchall()
            except Exception:
                data["largest_tables"] = []
            
            try:
                # Most fragmented tables
                cursor.execute(f"""
                    SELECT 
                        table_schema,
                        table_name,
                        data_free,
                        data_length + index_length as total_size,
                        ROUND((data_free / (data_length + index_length + 1)) * 100, 2) as fragmentation_pct
                    FROM information_schema.tables
                    WHERE {where_clause} 
                        AND data_free > 0 
                        AND data_length + index_length > 0
                        AND table_type = 'BASE TABLE'
                    ORDER BY data_free DESC
                    LIMIT %s
                """, params + [limit])
                data["fragmented_tables"] = cursor.fetchall()
            except Exception:
                data["fragmented_tables"] = []
            
            try:
                # Tables without primary key
                cursor.execute(f"""
                    SELECT 
                        t.table_schema,
                        t.table_name,
                        t.table_rows,
                        t.data_length + t.index_length as total_size
                    FROM information_schema.tables t
                    WHERE {where_clause}
                        AND NOT EXISTS (
                            SELECT 1 
                            FROM information_schema.statistics s
                            WHERE s.table_schema = t.table_schema 
                                AND s.table_name = t.table_name
                                AND s.index_name = 'PRIMARY'
                        )
                        AND t.table_type = 'BASE TABLE'
                    ORDER BY (t.data_length + t.index_length) DESC
                    LIMIT %s
                """, params + [limit])
                data["tables_without_pk"] = cursor.fetchall()
            except Exception:
                data["tables_without_pk"] = []
            
        return data
    
    def get_query_cache_info(self) -> Dict[str, Any]:
        """Get query cache information."""
        conn = self._get_connection()
        with conn.cursor() as cursor:
            cursor.execute("""
                SHOW VARIABLES LIKE 'query_cache_%'
            """)
            
            cache_vars = {row["Variable_name"]: row["Value"] for row in cursor.fetchall()}
            
            # Check if query cache is enabled
            if cache_vars.get("query_cache_type", "OFF") == "OFF":
                return {"enabled": False}
            
            cursor.execute("""
                SHOW STATUS LIKE 'Qcache_%'
            """)
            
            cache_status = {row["Variable_name"]: row["Value"] for row in cursor.fetchall()}
            
            # Calculate hit rate
            hits = int(cache_status.get("Qcache_hits", 0))
            inserts = int(cache_status.get("Qcache_inserts", 0))
            
            hit_rate = 0
            if hits + inserts > 0:
                hit_rate = (hits / (hits + inserts)) * 100
            
            return {
                "enabled": True,
                "size": cache_vars.get("query_cache_size", 0),
                "limit": cache_vars.get("query_cache_limit", 0),
                "hits": hits,
                "inserts": inserts,
                "hit_rate": hit_rate,
                "queries_in_cache": int(cache_status.get("Qcache_queries_in_cache", 0)),
                "free_memory": int(cache_status.get("Qcache_free_memory", 0)),
                "free_blocks": int(cache_status.get("Qcache_free_blocks", 0)),
                "total_blocks": int(cache_status.get("Qcache_total_blocks", 0)),
            }
    
    def get_binlog_info(self) -> Dict[str, Any]:
        """Get binary log information."""
        conn = self._get_connection()
        data = {}
        
        try:
            with conn.cursor() as cursor:
                # Check if binary logging is enabled
                cursor.execute("SHOW VARIABLES LIKE 'log_bin'")
                log_bin = cursor.fetchone()
                
                if not log_bin or log_bin["Value"] != "ON":
                    return {"enabled": False}
                
                data["enabled"] = True
                
                # Get binary log files
                cursor.execute("SHOW BINARY LOGS")
                logs = cursor.fetchall()
                
                data["log_files"] = logs
                data["log_count"] = len(logs)
                data["total_size"] = sum(log.get("File_size", 0) for log in logs)
                
                # Get current log file
                cursor.execute("SHOW MASTER STATUS")
                master_status = cursor.fetchone()
                if master_status:
                    data["current_log"] = master_status.get("File")
                    data["current_position"] = master_status.get("Position")
                
                # Get binlog format
                cursor.execute("SHOW VARIABLES LIKE 'binlog_format'")
                binlog_format = cursor.fetchone()
                data["format"] = binlog_format["Value"] if binlog_format else "UNKNOWN"
                
        except Exception as err:
            _LOGGER.debug("Could not get binary log info: %s", err)
            data["enabled"] = False
            data["error"] = str(err)
        
        return data
    
    def get_connection_pool_stats(self) -> Dict[str, Any]:
        """Get connection pool statistics."""
        conn = self._get_connection()
        with conn.cursor() as cursor:
            cursor.execute("""
                SELECT 
                    COUNT(*) as total_connections,
                    SUM(CASE WHEN COMMAND = 'Sleep' THEN 1 ELSE 0 END) as idle_connections,
                    SUM(CASE WHEN COMMAND != 'Sleep' THEN 1 ELSE 0 END) as active_connections,
                    MAX(TIME) as max_connection_time,
                    AVG(TIME) as avg_connection_time
                FROM INFORMATION_SCHEMA.PROCESSLIST
            """)
            pool_stats = cursor.fetchone()
            
            cursor.execute("SHOW VARIABLES LIKE 'max_connections'")
            max_conn = cursor.fetchone()
            
            cursor.execute("SHOW STATUS LIKE 'Max_used_connections'")
            max_used = cursor.fetchone()
            
            return {
                "total_connections": pool_stats["total_connections"] or 0,
                "idle_connections": pool_stats["idle_connections"] or 0,
                "active_connections": pool_stats["active_connections"] or 0,
                "max_connection_time": pool_stats["max_connection_time"] or 0,
                "avg_connection_time": float(pool_stats["avg_connection_time"] or 0),
                "max_connections": int(max_conn["Value"]) if max_conn else 0,
                "max_used_connections": int(max_used["Value"]) if max_used else 0,
                "connection_usage_pct": (
                    (int(max_used["Value"]) / int(max_conn["Value"])) * 100
                    if max_conn and max_used and int(max_conn["Value"]) > 0
                    else 0
                ),
            }
    
    def get_slow_query_stats(self) -> Dict[str, Any]:
        """Get slow query statistics."""
        conn = self._get_connection()
        data = {}
        
        with conn.cursor() as cursor:
            # Check if slow query log is enabled
            cursor.execute("SHOW VARIABLES LIKE 'slow_query_log'")
            slow_log = cursor.fetchone()
            
            if not slow_log or slow_log["Value"] != "ON":
                return {"enabled": False}
            
            data["enabled"] = True
            
            # Get slow query settings
            cursor.execute("""
                SHOW VARIABLES WHERE Variable_name IN (
                    'slow_query_log_file',
                    'long_query_time',
                    'log_queries_not_using_indexes'
                )
            """)
            
            for row in cursor.fetchall():
                data[row["Variable_name"]] = row["Value"]
            
            # Get slow query count
            cursor.execute("SHOW STATUS LIKE 'Slow_queries'")
            slow_count = cursor.fetchone()
            data["slow_query_count"] = int(slow_count["Value"]) if slow_count else 0
            
            # Try to get slow queries from performance schema if available
            try:
                cursor.execute("""
                    SELECT 
                        DIGEST_TEXT,
                        COUNT_STAR,
                        SUM_TIMER_WAIT,
                        MAX_TIMER_WAIT,
                        AVG_TIMER_WAIT,
                        SUM_ROWS_EXAMINED,
                        SUM_ROWS_SENT
                    FROM performance_schema.events_statements_summary_by_digest
                    WHERE AVG_TIMER_WAIT > %s * 1000000000
                        AND DIGEST_TEXT IS NOT NULL
                    ORDER BY SUM_TIMER_WAIT DESC
                    LIMIT 10
                """, (float(data.get("long_query_time", 10)),))
                
                data["top_slow_queries"] = cursor.fetchall()
            except Exception:
                data["top_slow_queries"] = []
        
        return data
    
    def get_lock_wait_stats(self) -> Dict[str, Any]:
        """Get lock wait statistics."""
        conn = self._get_connection()
        data = {}
        
        try:
            with conn.cursor() as cursor:
                # InnoDB lock waits - check if sys schema exists
                try:
                    cursor.execute("""
                        SELECT 
                            waiting_trx_id,
                            waiting_pid,
                            waiting_query,
                            blocking_trx_id,
                            blocking_pid,
                            blocking_query,
                            wait_started,
                            wait_age_secs,
                            locked_table,
                            locked_index
                        FROM sys.innodb_lock_waits
                        LIMIT 10
                    """)
                    data["current_lock_waits"] = cursor.fetchall()
                except Exception:
                    # Try alternative method
                    cursor.execute("""
                        SELECT 
                            r.trx_id AS waiting_trx_id,
                            r.trx_mysql_thread_id AS waiting_pid,
                            r.trx_query AS waiting_query,
                            b.trx_id AS blocking_trx_id,
                            b.trx_mysql_thread_id AS blocking_pid,
                            b.trx_query AS blocking_query,
                            r.trx_wait_started AS wait_started
                        FROM information_schema.innodb_lock_waits w
                        JOIN information_schema.innodb_trx r ON w.requesting_trx_id = r.trx_id
                        JOIN information_schema.innodb_trx b ON w.blocking_trx_id = b.trx_id
                        LIMIT 10
                    """)
                    data["current_lock_waits"] = cursor.fetchall()
                
                # Lock wait timeout setting
                cursor.execute("SHOW VARIABLES LIKE 'innodb_lock_wait_timeout'")
                timeout = cursor.fetchone()
                data["lock_wait_timeout"] = int(timeout["Value"]) if timeout else 50
                
                # Historical lock wait stats
                cursor.execute("""
                    SHOW STATUS WHERE Variable_name IN (
                        'Innodb_row_lock_waits',
                        'Innodb_row_lock_time',
                        'Innodb_row_lock_time_avg',
                        'Innodb_row_lock_time_max',
                        'Table_locks_waited'
                    )
                """)
                
                for row in cursor.fetchall():
                    data[row["Variable_name"]] = int(row["Value"])
        except Exception as err:
            _LOGGER.debug("Could not get lock wait stats: %s", err)
            data["current_lock_waits"] = []
        
        return data
    
    def get_buffer_pool_stats(self) -> Dict[str, Any]:
        """Get InnoDB buffer pool statistics."""
        conn = self._get_connection()
        try:
            with conn.cursor() as cursor:
                cursor.execute("""
                    SELECT 
                        POOL_ID,
                        POOL_SIZE,
                        FREE_BUFFERS,
                        DATABASE_PAGES,
                        OLD_DATABASE_PAGES,
                        MODIFIED_DATABASE_PAGES,
                        PENDING_DECOMPRESS,
                        PENDING_READS,
                        PENDING_FLUSH_LRU,
                        PENDING_FLUSH_LIST,
                        PAGES_MADE_YOUNG,
                        PAGES_NOT_MADE_YOUNG,
                        PAGES_MADE_YOUNG_RATE,
                        PAGES_MADE_NOT_YOUNG_RATE,
                        NUMBER_PAGES_READ,
                        NUMBER_PAGES_CREATED,
                        NUMBER_PAGES_WRITTEN,
                        PAGES_READ_RATE,
                        PAGES_CREATE_RATE,
                        PAGES_WRITTEN_RATE,
                        NUMBER_PAGES_GET,
                        HIT_RATE,
                        YOUNG_MAKE_PER_THOUSAND_GETS,
                        NOT_YOUNG_MAKE_PER_THOUSAND_GETS,
                        NUMBER_PAGES_READ_AHEAD,
                        NUMBER_READ_AHEAD_EVICTED,
                        READ_AHEAD_RATE,
                        READ_AHEAD_EVICTED_RATE,
                        LRU_IO_TOTAL,
                        LRU_IO_CURRENT,
                        UNCOMPRESS_TOTAL,
                        UNCOMPRESS_CURRENT
                    FROM information_schema.INNODB_BUFFER_POOL_STATS
                """)
                
                pools = cursor.fetchall()
                
                if not pools:
                    return {
                        "pool_count": 0,
                        "total_size": 0,
                        "total_free": 0,
                        "total_database_pages": 0,
                        "total_dirty_pages": 0,
                        "avg_hit_rate": 0,
                        "pools": []
                    }
                
                # Aggregate stats
                total_stats = {
                    "pool_count": len(pools),
                    "total_size": sum(p["POOL_SIZE"] or 0 for p in pools),
                    "total_free": sum(p["FREE_BUFFERS"] or 0 for p in pools),
                    "total_database_pages": sum(p["DATABASE_PAGES"] or 0 for p in pools),
                    "total_dirty_pages": sum(p["MODIFIED_DATABASE_PAGES"] or 0 for p in pools),
                    "avg_hit_rate": sum(p["HIT_RATE"] or 0 for p in pools) / len(pools) if pools else 0,
                    "pools": pools
                }
                
                # Calculate usage percentage
                if total_stats["total_size"] > 0:
                    total_stats["usage_pct"] = (
                        (total_stats["total_size"] - total_stats["total_free"]) / 
                        total_stats["total_size"]
                    ) * 100
                    total_stats["dirty_pct"] = (
                        total_stats["total_dirty_pages"] / total_stats["total_size"]
                    ) * 100
                else:
                    total_stats["usage_pct"] = 0
                    total_stats["dirty_pct"] = 0
                
                return total_stats
        except Exception as err:
            _LOGGER.warning("Failed to get buffer pool stats: %s", err)
            return {
                "pool_count": 0,
                "total_size": 0,
                "total_free": 0,
                "total_database_pages": 0,
                "total_dirty_pages": 0,
                "avg_hit_rate": 0,
                "pools": []
            }
    
    def get_transaction_info(self) -> Dict[str, Any]:
        """Get transaction information."""
        conn = self._get_connection()
        data = {}
        
        try:
            with conn.cursor() as cursor:
                # Active transactions
                cursor.execute("""
                    SELECT 
                        trx_id,
                        trx_state,
                        trx_started,
                        trx_requested_lock_id,
                        trx_wait_started,
                        trx_weight,
                        trx_mysql_thread_id,
                        trx_query,
                        trx_operation_state,
                        trx_tables_in_use,
                        trx_tables_locked,
                        trx_rows_locked,
                        trx_rows_modified
                    FROM information_schema.INNODB_TRX
                    ORDER BY trx_started
                """)
                
                transactions = cursor.fetchall()
                data["active_transactions"] = transactions
                data["transaction_count"] = len(transactions)
                
                # Long running transactions
                data["long_running_transactions"] = [
                    trx for trx in transactions
                    if trx["trx_started"] and 
                    (datetime.now() - trx["trx_started"]).total_seconds() > 60
                ]
                
                # Transaction isolation level
                cursor.execute("SELECT @@tx_isolation as isolation_level")
                result = cursor.fetchone()
                if result:
                    data["default_isolation_level"] = result["isolation_level"]
                else:
                    cursor.execute("SELECT @@transaction_isolation as isolation_level")
                    result = cursor.fetchone()
                    data["default_isolation_level"] = result["isolation_level"] if result else "UNKNOWN"
                
                # Rollback segment info
                cursor.execute("""
                    SHOW STATUS WHERE Variable_name IN (
                        'Com_commit',
                        'Com_rollback',
                        'Com_rollback_to_savepoint',
                        'Com_savepoint'
                    )
                """)
                
                for row in cursor.fetchall():
                    data[row["Variable_name"]] = int(row["Value"])
        except Exception as err:
            _LOGGER.warning("Failed to get transaction info: %s", err)
            data["active_transactions"] = []
            data["transaction_count"] = 0
            data["long_running_transactions"] = []
        
        return data
    
    def get_storage_engine_stats(self) -> Dict[str, Any]:
        """Get storage engine statistics."""
        conn = self._get_connection()
        with conn.cursor() as cursor:
            # Storage engines in use
            cursor.execute("""
                SELECT 
                    ENGINE,
                    COUNT(*) as table_count,
                    SUM(DATA_LENGTH) as total_data_size,
                    SUM(INDEX_LENGTH) as total_index_size,
                    SUM(DATA_LENGTH + INDEX_LENGTH) as total_size
                FROM information_schema.TABLES
                WHERE TABLE_SCHEMA NOT IN %s
                    AND ENGINE IS NOT NULL
                GROUP BY ENGINE
            """, (SYSTEM_DATABASES,))
            
            engines = {}
            for row in cursor.fetchall():
                engines[row["ENGINE"]] = {
                    "table_count": row["table_count"],
                    "data_size": row["total_data_size"] or 0,
                    "index_size": row["total_index_size"] or 0,
                    "total_size": row["total_size"] or 0,
                }
            
            # Available storage engines
            cursor.execute("SHOW ENGINES")
            available_engines = {}
            for row in cursor.fetchall():
                available_engines[row["Engine"]] = {
                    "support": row["Support"],
                    "comment": row["Comment"],
                    "transactions": row.get("Transactions", "NO"),
                    "xa": row.get("XA", "NO"),
                    "savepoints": row.get("Savepoints", "NO"),
                }
            
            return {
                "engines_in_use": engines,
                "available_engines": available_engines,
            }
