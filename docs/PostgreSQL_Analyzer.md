# 📗 **README.md — PostgreSQL Analyzer Role**

# PostgreSQL Analyzer

After the installation we analyze the running PostgreSQL instance and generates a detailed performance report.  
It is optimized for workloads such as Nextcloud but works with any PostgreSQL installation.

The role:

- collects live PostgreSQL settings directly from the database  
- analyzes memory usage of backend processes  
- detects whether the host is shared (DB + application) or dedicated  
- calculates recommended tuning parameters based on system RAM and CPU  
- outputs a clear comparison between current and recommended values

---

## What the Role Does

### 1. Reads Active PostgreSQL Settings (No File Parsing)
The role uses: 

- community.postgresql.postgresql_info: 
  filter: setting


This retrieves **the effective runtime configuration**, including:

- values from `postgresql.conf`
- values from `postgresql.auto.conf`
- values set via `ALTER SYSTEM`
- built‑in defaults
- dynamic values calculated by PostgreSQL

This is far more accurate than parsing configuration files.

---

### 2. Analyzes PostgreSQL Backend Memory Usage
The role inspects all running PostgreSQL backend processes and calculates:

- number of active backends  
- minimum RSS  
- maximum RSS  
- average RSS  

This helps identify memory growth, leaks, or oversized work_mem settings.

---

### 3. Detects Host Type (Shared vs. Dedicated)
If the host belongs to both inventory groups:

- `nextcloud`
- `database`

then the role marks it as a **shared host**.

Shared hosts receive more conservative tuning recommendations.

---

### 4. Calculates Recommended Settings Dynamically

Recommendations are based on:

- total system RAM (`ansible_facts.memtotal_mb`)
- CPU cores (`ansible_facts.processor_vcpus`)
- whether the host is shared or dedicated
- PostgreSQL best practices for OLTP workloads
- Nextcloud‑specific tuning guidelines

The role computes:

- **max_connections**  
  - shared host: 50  
  - dedicated DB: 100  

- **shared_buffers**  
  = 25% of PostgreSQL RAM budget

- **effective_cache_size**  
  = 60% of PostgreSQL RAM budget

- **work_mem**  
  = 25% of PostgreSQL RAM budget / max_connections  
  (safe even under parallel queries)

- **maintenance_work_mem**  
  = 10% of PostgreSQL RAM budget

- **random_page_cost = 1.1**  
  (optimized for SSD/NVMe)

- **effective_io_concurrency**  
  = 200 (or 0 inside LXC)

- **max_worker_processes / max_parallel_workers**  
  = number of CPU cores

These values are safe, modern, and tuned for real‑world workloads.

---

## Example Output

```json
TASK [postgres_analyzer : Display PostgreSQL analysis summary] ********************************************************************************************************************************************************************************************************************
ok: [nextcloud.example.com] => {
    "msg": [
        "📊 PostgreSQL 17.9 Analysis Report",
        "",
        "Host type:",
        "  Shared host (DB + Nextcloud): True",
        "  Total RAM: 7757 MB",
        "  Reserved for PostgreSQL: 1551 MB",
        "  CPU cores: 4",
        "",
        "Current configuration:",
        "  max_connections = 50",
        "  shared_buffers = 1GB",
        "  effective_cache_size = 2GB",
        "  work_mem = 4MB",
        "  maintenance_work_mem = 64MB",
        "  random_page_cost = 1.1",
        "  effective_io_concurrency = 200",
        "  huge_pages = off",
        "  min_wal_size = 1GB",
        "  max_wal_size = 4GB",
        "  max_worker_processes = 4",
        "  max_parallel_workers = 4",
        "",
        "Recommended settings:",
        "  max_connections = 50",
        "  shared_buffers = 387MB",
        "  effective_cache_size = 930MB",
        "  work_mem = 7MB",
        "  maintenance_work_mem = 155MB",
        "  random_page_cost = 1.1",
        "  effective_io_concurrency = 200",
        "  huge_pages = off",
        "  min_wal_size = 1GB",
        "  max_wal_size = 4GB",
        "  max_worker_processes = 4",
        "  max_parallel_workers = 4",
        "",
        "To apply recommendations, set the variable postgres_tuning_parameters in group_vars/all/database.yml",
        "and rerun the playbook."
    ]
}
```

No configuration is required, but you may override the RAM budget:

```yaml
postgres_reserved_ram_mb: 2048
```

## Why This Role Is Useful

PostgreSQL tuning is often misunderstood and frequently done using outdated rules of thumb.

This role provides:
- accurate live settings (not config files)
- hardware‑aware recommendations
- safe defaults for mixed workloads
- clear explanations of what each value means

It is ideal for:
- Nextcloud installations
- small to medium PostgreSQL servers
- shared hosts
- administrators who want predictable performance

