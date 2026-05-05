# 📗 **README.md — MariaDB Analyzer Role**

# MariaDB Analyzer

After the installation we analyze the running MariaDB instance and generate a detailed performance report.  
It is optimized for workloads such as Nextcloud but works with any MariaDB installation.

The role:

- collects live MariaDB settings directly from the database
- analyzes memory usage of MariaDB server processes
- detects whether the host is shared (DB + application) or dedicated
- calculates recommended tuning parameters based on system RAM and CPU
- outputs a clear comparison between current and recommended values

---

## What the Role Does

### 1. Reads Active MariaDB Settings (No File Parsing)
The role uses:

```yaml
- community.mysql.mysql_variables:
    variable: "{{ item }}"
```

This retrieves **the effective runtime configuration** directly from the running instance, including:

- values from `/etc/mysql/mariadb.conf.d/90-nextcloud.cnf` (or equivalent)
- values set via `SET GLOBAL`
- built-in defaults

This is far more accurate than parsing configuration files.

---

### 2. Analyzes MariaDB Process Memory Usage
The role inspects all running MariaDB server processes (`mariadbd` or `mysqld` for older
installations) and calculates:

- number of active processes
- minimum RSS
- maximum RSS
- average RSS

This helps identify memory pressure, leaks, or oversized buffer pool settings.

---

### 3. Detects Host Type (Shared vs. Dedicated)
If the database host (`nextcloud_db.host`) resolves to `localhost`, `127.0.0.1`, or `::1`,
the role marks it as a **shared host** (DB + Nextcloud on the same machine).

Shared hosts receive more conservative tuning recommendations to leave headroom for PHP-FPM,
the web server, and other services.

---

### 4. Calculates Recommended Settings Dynamically

Recommendations are based on:

- total system RAM (`ansible_facts.memtotal_mb`)
- CPU cores (`ansible_facts.processor_vcpus`)
- whether the host is shared or dedicated
- virtualization type (LXC containers receive lower `innodb_io_capacity`)
- MariaDB/InnoDB best practices for OLTP workloads
- Nextcloud-specific tuning guidelines

#### RAM Budget
| Deployment | RAM budget |
|---|---|
| Collocated (shared) | 20 % of total RAM |
| Dedicated DB server | 50 % of total RAM |

#### Computed values

- **max_connections**
  - shared host: 50
  - dedicated DB: 150

- **innodb_buffer_pool_size**
  = 70 % of the RAM budget
  (the single most impactful InnoDB setting)

- **innodb_log_buffer_size**
  = max(64 MB, 5 % of RAM budget)

- **innodb_flush_log_at_trx_commit = 2**
  (safe performance trade-off; full durability requires `1`)

- **innodb_io_capacity**
  = 1000 (or 400 inside LXC where direct I/O is limited)

- **innodb_read_io_threads / innodb_write_io_threads**
  = max(4, CPU cores)

- **thread_cache_size**
  = max(8, 1 % of RAM budget)

- **tmp_table_size / max_heap_table_size**
  = min(64 MB, 5 % of RAM budget)
  (both must match to avoid disk spills)

- **table_open_cache**
  = max(400, CPU cores × 100)

- **join_buffer_size / sort_buffer_size** = 4 MB  
- **read_buffer_size / read_rnd_buffer_size** = 2 MB  
- **key_buffer_size** = 32 MB (MyISAM system tables only)

---

## Deployment Scenarios

The role handles three scenarios transparently:

| Scenario | Connection method | Process stats |
|---|---|---|
| Collocated (DB + Nextcloud on same host) | Unix socket (peer auth) | ✅ available |
| Dedicated DB server (managed by this playbook) | Unix socket on DB host via `delegate_to` | ✅ available |
| Managed DB service (`nextcloud_db.managed: true`) | TCP with admin credentials | ❌ not available |

---

## Example Output

```json
TASK [mariadb_analyzer : Display MariaDB analysis summary] ******************************************
ok: [nextcloud.example.com] => {
    "msg": [
        "MariaDB 10.11.8-MariaDB Analysis Report",
        "",
        "Host type:",
        "  Deployment: collocated",
        "  DB server total RAM: 7757 MB",
        "  Reserved for MariaDB: 1551 MB",
        "  DB server CPU cores: 4",
        "",
        "Process stats (1 processes):",
        "  RSS min/avg/max: 352152/352152/352152 kB",
        "",
        "Current configuration:",
        "  max_connections         = 200",
        "  innodb_buffer_pool_size = 256 MB",
        "  innodb_log_buffer_size  = 32 MB",
        "  innodb_flush_log_at_trx_commit = 2",
        "  innodb_io_capacity      = 400",
        "  innodb_read_io_threads  = 4",
        "  innodb_write_io_threads = 4",
        "  thread_cache_size       = 0",
        "  tmp_table_size          = 64 MB",
        "  max_heap_table_size     = 64 MB",
        "  table_open_cache        = 400",
        "  join_buffer_size        = 0 MB",
        "  sort_buffer_size        = 0 MB",
        "  key_buffer_size         = 128 MB",
        "",
        "Recommended settings:",
        "  max_connections         = 50",
        "  innodb_buffer_pool_size = 1085M",
        "  innodb_log_buffer_size  = 77M",
        "  innodb_flush_log_at_trx_commit = 2",
        "  innodb_io_capacity      = 1000",
        "  innodb_read_io_threads  = 4",
        "  innodb_write_io_threads = 4",
        "  thread_cache_size       = 15",
        "  tmp_table_size          = 64M",
        "  max_heap_table_size     = 64M",
        "  table_open_cache        = 400",
        "  join_buffer_size        = 4M",
        "  sort_buffer_size        = 4M",
        "  key_buffer_size         = 32M",
        "",
        "To apply recommendations, set mariadb_tuning_parameters in group_vars/all/database.yml",
        "and rerun the playbook."
    ]
}
```

---

## Applying Recommendations

Copy the recommended values into `group_vars/all/database.yml` under the
`mariadb_tuning_parameters` key and rerun the playbook:

```yaml
mariadb_tuning_parameters:
  max_connections: 50
  innodb_buffer_pool_size: "1085M"
  innodb_log_buffer_size: "77M"
  innodb_flush_log_at_trx_commit: 2
  innodb_io_capacity: 1000
  innodb_read_io_threads: 4
  innodb_write_io_threads: 4
  thread_cache_size: 15
  tmp_table_size: "64M"
  max_heap_table_size: "64M"
  table_open_cache: 400
  join_buffer_size: "4M"
  sort_buffer_size: "4M"
  key_buffer_size: "32M"
```

You may also override the RAM budget manually (in MB) if you want to reserve more or less
memory for MariaDB, regardless of auto-detection:

```yaml
mariadb_reserved_ram_mb: 2048
```

---

## Why This Role Is Useful

MariaDB tuning is often done with copy-pasted defaults that were written for completely
different hardware. The most common mistake is an undersized `innodb_buffer_pool_size` —
leaving most of the available RAM unused.

This role provides:

- accurate live settings (not config file parsing)
- hardware-aware recommendations
- safe defaults for mixed (shared) and dedicated workloads
- clear output that shows exactly what to change and why

It is ideal for:

- Nextcloud installations using MariaDB
- small to medium MariaDB servers
- shared hosts where DB and application run together
- administrators who want predictable performance without manual tuning
