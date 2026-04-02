# Database Roles (PostgreSQL & MariaDB)

Ansible roles to install and configure the database management system for Nextcloud. The two roles — `postgres` and `mariadb` — are mutually exclusive and selected via the `nextcloud_db.type` variable.

> **Note:** These roles only install and configure the DBMS itself. The actual Nextcloud database and user are created by the [Nextcloud role](NEXTCLOUD_README.md) during installation.

## Supported Platforms

- Debian / Ubuntu
- RHEL / AlmaLinux / Rocky Linux

## Role Selection

In the main playbook, the database role is applied conditionally:

```yaml
roles:
  - role: mariadb
    when: (nextcloud_db.type == 'mysql')
  - role: postgres
    when: (nextcloud_db.type == 'pgsql')
```

## PostgreSQL Role

### What This Role Does

1. **Installs PostgreSQL** packages from the official PGDG repository (added by the [OS role](OS_README.md))
2. **Generates locales** required for the database (Debian/Ubuntu)
3. **Initializes the data directory** (RedHat only — Debian handles this automatically)
4. **Starts and enables** the PostgreSQL service
5. **Applies tuning parameters** via `ALTER SYSTEM` (from `postgres_tuning_parameters`)
6. **Configures `pg_hba.conf`** — allows the Nextcloud user to connect via unix socket with MD5 authentication
7. **Creates the Nextcloud database, user, and grants privileges** (schema `public`, default privileges on tables)
8. **Sets environment variables** (`PGDATA`, `PATH`) via `/etc/profile.d/postgres.sh` (on older distributions)

### Task Flow

```
tasks/main.yml
  ├── Debian.yml          Install packages, generate locales
  │   or RedHat.yml       Install packages (from PGDG repo)
  ├── initialize.yml      Set env vars, init data dir, start service
  ├── configure.yml       ALTER SYSTEM tuning, pg_hba.conf, socket dirs
  └── database.yml        Create database, user, and grant privileges
```

### Variables

#### User-defined variables (`group_vars/all/database.yml`)

| Variable | Default | Description |
|----------|---------|-------------|
| `nextcloud_db.type` | `pgsql` | Database type (`pgsql` or `mysql`) |
| `nextcloud_db.host` | `localhost` | Database host |
| `nextcloud_db.name` | `nextcloud` | Database name |
| `nextcloud_db.user` | `nextcloud` | Database user |
| `nextcloud_db.password` | *(empty → auto-generated)* | Database password |
| `postgresql_version` | `18` | PostgreSQL major version to install |
| `postgres_tuning_parameters` | *(see below)* | List of PostgreSQL `ALTER SYSTEM` parameters |

#### Tuning Parameters

Default tuning parameters are defined in `group_vars/all/database.yml`. Use [PGTune](https://pgtune.leopard.in.ua/) to generate optimal values for your system:

```yaml
postgres_tuning_parameters:
  - max_connections: 50
  - shared_buffers: 387MB
  - effective_cache_size: 930MB
  - work_mem: 7MB
  - maintenance_work_mem: 155MB
  - random_page_cost: 1.1
  - effective_io_concurrency: 200
  - checkpoint_completion_target: 0.9
  - default_statistics_target: 100
  - huge_pages: 'off'
  - min_wal_size: 1GB
  - max_wal_size: 4GB
  - max_worker_processes: 4
  - max_parallel_workers_per_gather: 2
  - max_parallel_workers: 4
  - max_parallel_maintenance_workers: 2
```

For detailed analysis and tuning under real load, see the [PostgreSQL Analyzer](PostgreSQL_Analyzer.md).

#### Internal variables (`group_vars/all/database/main.yml`)

| Variable | Debian | RedHat |
|----------|--------|--------|
| `postgresql_packages` | `postgresql-17`, `python3-psycopg2` | `postgresql17-server`, `python3-psycopg2` |
| `postgresql_data_dir` | `/var/lib/postgresql/17/main` | `/var/lib/pgsql/17/data` |
| `postgresql_bin_path` | `/usr/lib/postgresql/17/bin` | `/usr/pgsql-17/bin` |
| `postgresql_config_path` | `/etc/postgresql/17/main` | `/var/lib/pgsql/17/data` |
| `postgresql_daemon_service_name` | `postgresql@17-main` | `postgresql-17` |

### Platform Differences

| Aspect | Debian / Ubuntu | RedHat / Alma / Rocky |
|--------|-----------------|----------------------|
| Locale generation | `locale_gen` module | Not needed |
| Data directory init | Automatic at install | Manual via `postgresql-setup initdb` |
| Config path | `/etc/postgresql/17/main` | `/var/lib/pgsql/17/data` |
| Environment profile | Not deployed (modern systems) | Not deployed (modern systems) |

### Unused Artifacts

| File | Description |
|------|-------------|
| `vars/main.yml` | Entirely commented out — all variables moved to `group_vars/all/database/main.yml` |
| `defaults/main.yml` | Contains `postgresql_version: 17` which is overridden by `group_vars/all/database.yml` |

---

## MariaDB Role

### What This Role Does

1. **Installs MariaDB** packages (distribution packages on Debian, MariaDB repo on RedHat)
2. **Deploys a custom configuration file** (`90-nextcloud.cfg`) via drop-in — stock config is not modified
3. **Starts and enables** the MariaDB service
4. **Removes the anonymous user** and **test database** for security hardening

### Task Flow

```
tasks/main.yml
  ├── apt.yml             Install packages (Debian/Ubuntu)
  │   or dnf.yml          Add MariaDB repo, install packages, open firewall port (RedHat)
  ├── Deploy 90-nextcloud.cfg (my.cnf.j2 template)
  ├── Start and enable MariaDB
  └── Remove anonymous user and test database
```

### Configuration (`my.cnf.j2`)

The template deploys a drop-in configuration file with Nextcloud-optimized settings:

| Section | Key Settings |
|---------|-------------|
| `[client]` | `default-character-set = utf8mb4` |
| `[mysqld]` | `max_connections = 200`, `tmp_table_size = 64M`, `max_heap_table_size = 64M` |
| InnoDB | `innodb_buffer_pool_size = 256M`, `innodb_flush_log_at_trx_commit = 2`, `innodb_flush_method = O_DIRECT` |
| Character set | `character-set-server = utf8mb4`, `collation-server = utf8mb4_general_ci` |
| Nextcloud-specific | `transaction_isolation = READ-COMMITTED`, `binlog_format = ROW` |

### Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `nextcloud_db.type` | `pgsql` | Set to `mysql` to use MariaDB |
| `nextcloud_db.host` | `localhost` | Database host |
| `nextcloud_db.name` | `nextcloud` | Database name |
| `nextcloud_db.user` | `nextcloud` | Database user |
| `nextcloud_db.password` | *(empty → auto-generated)* | Database password |

#### Internal variables (`roles/mariadb/vars/main.yml`)

| Variable | Debian | RedHat |
|----------|--------|--------|
| `mariadb_conf_dir` | `/etc/mysql/mariadb.conf.d/` | `/etc/my.cnf.d` |
| `mariadb_socket` | `/var/run/mysqld/mysqld.sock` | `/var/lib/mysql/mysql.sock` |

### Installed Packages

| Debian / Ubuntu | RedHat / Alma / Rocky |
|-----------------|----------------------|
| `mariadb-server` (distro) | `MariaDB-server` (MariaDB repo) |
| `mariadb-client` | `MariaDB-client` |
| `python3-pymysql` | `python3-PyMySQL` |

### Platform Differences

| Aspect | Debian / Ubuntu | RedHat / Alma / Rocky |
|--------|-----------------|----------------------|
| Package source | Distribution packages | MariaDB YUM repository |
| Firewall | Not managed | Opens port 3306 via firewalld (remote DB only) |
| Config drop-in path | `/etc/mysql/mariadb.conf.d/90-nextcloud.cfg` | `/etc/my.cnf.d/90-nextcloud.cfg` |

### Unused Artifacts

| File | Description |
|------|-------------|
| `defaults/main.yml` | Contains commented-out `mariadb_version` / `mariadb_mirror_server` — MariaDB version is now determined by the distribution on Debian |
