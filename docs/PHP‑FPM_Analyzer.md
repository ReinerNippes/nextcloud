# PHP-FPM Analyzer

After the installation we analyze the running PHP-FPM instance and provides a detailed report of:

- current memory usage of PHP-FPM worker processes  
- the effective PHP-FPM configuration (pm, max_children, spare servers, etc.)  
- recommended settings based on real memory usage and available system RAM  
- a summary that helps administrators tune PHP-FPM for performance and stability

The role is designed for environments such as Nextcloud, but works with any PHP-FPM pool.

---

## What the Role Does

### 1. Collects PHP-FPM Process Statistics
The role inspects all running PHP-FPM worker processes and calculates:

- **Number of processes**
- **Minimum memory usage**
- **Maximum memory usage**
- **Average memory usage**

These values are derived from the RSS (resident set size) of each worker process.

This allows the role to understand how much memory each PHP worker actually consumes in real-world load.

---

### 2. Reads the Current PHP-FPM Configuration
The role extracts the active settings from:

- `/etc/php/*/fpm/pool.d/www.conf`
- or a custom pool file if configured

It reads:

- `pm`
- `pm.max_children`
- `pm.start_servers`
- `pm.min_spare_servers`
- `pm.max_spare_servers`

These values are shown in the report so you can compare them with the recommended settings.

---

### 3. Calculates Recommended Settings
The recommendations are based on:

- **actual average memory usage per worker**
- **reserved RAM for PHP-FPM** (configurable)
- **best practices for dynamic process management**

The role computes:

- `pm = dynamic`  
  (recommended for most workloads)

- `pm.max_children`  
  = reserved RAM / average worker size

- `pm.start_servers`  
  = 25% of max_children

- `pm.min_spare_servers`  
  = 25% of max_children

- `pm.max_spare_servers`  
  = 50% of max_children

These values ensure that PHP-FPM uses memory efficiently without overloading the system.

---

## Example Output

The report looks like:

```
TASK [php_fpm_analyser : Display summary] *****************************************************************************************************************************************************************************************************************************************
ok: [nextcloud.example.com] => {
    "msg": [
        "📊 PHP-FPM analysis completed",
        "",
        "Number of processes: 15",
        "Minimum size:        61.4 MB",
        "Maximum size:        129.1 MB",
        "Average size:        105.3 MB",
        "",
        "Current configuration (from /etc/php/8.4/fpm/pool.d/www.conf ):",
        "  pm = ['dynamic']",
        "  pm.max_children = ['50']",
        "  pm.start_servers = ['10']",
        "  pm.min_spare_servers = ['10']",
        "  pm.max_spare_servers = ['25']",
        "",
        "Recommended settings:",
        "  pm = dynamic",
        "  pm.max_children = 10.0",
        "  pm.start_servers = 2",
        "  pm.min_spare_servers = 2",
        "  pm.max_spare_servers = 5",
        "",
        "Basis:",
        "  Reserved RAM for PHP-FPM: 1024 MB",
        "  Average process size: 105.3 MB",
        "",
        "To apply recommendations, set the variable php_tuning in group_vars/all/php.yml",
        "and rerun the playbook."
    ]
}
```

##  Why This Role Is Useful

PHP-FPM tuning is often guesswork.

This role removes the guesswork by basing recommendations on real memory usage and system capacity, ensuring:
• 	stable performance
• 	fewer OOM kills
• 	predictable memory consumption
• 	optimal worker counts for your hardware