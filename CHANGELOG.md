# Changelog

## v3.2 (May 2026)

### New: Euro-Office Document Server

- New `eurooffice` role for Euro-Office Document Server (OnlyOffice-compatible)
- Supports collocated and dedicated server deployment (mirrors `onlyoffice` architecture)
- Reverse-proxied through nginx/Apache; reuses Nextcloud `onlyoffice` app on the integration side
- New `nextcloud_install.eurooffice` toggle, `eurooffice_fqdn` variable, and `eurooffice_secret` JWT password
- Webserver config combines OnlyOffice and Euro-Office vhost block (`/onlyoffice/` proxy to `127.0.0.1:8443`)
- Added `eurooffice` group to all example inventories and dynamic inventories (Hetzner labels + Scaleway tags)
- Tested on Debian 13, Rocky 10, CentOS 10, openSUSE Leap 16
- New documentation: `docs/EUROOFFICE-README.md`

### New: MariaDB Analyzer Role

- New `mariadb_analyzer` role for live tuning analysis (mirrors `postgres_analyzer`)
- Reads runtime variables via `community.mysql.mysql_variables` (no config file parsing)
- Hardware-aware recommendations: `innodb_buffer_pool_size`, `innodb_log_buffer_size`,
  `max_connections`, `thread_cache_size`, `tmp_table_size`, IO threads, and more
- Handles three deployment scenarios: collocated, dedicated server (delegated), managed service
- Added to `nextcloud.yml` and `nextcloud-performance-tuning.yml` (runs when `nextcloud_db.type == 'mysql'`)
- New `mariadb_tuning_parameters` user variable (rendered into `90-nextcloud.cnf`)
- New documentation: `docs/MariaDB_Analyzer.md`

### New: Dedicated Database / Redis Servers (Functional)

- Database (PostgreSQL / MariaDB) and Redis on separate hosts now fully supported
- PostgreSQL on dedicated host:
  - `listen_addresses = *`, `scram-sha-256` auth (replaces md5)
  - Source IP for `pg_hba.conf` is detected dynamically via `ip route get` (delegated to Nextcloud host) — no static `postgres_allowed_ipv4` needed
  - Stale `pg_hba.conf` TCP entries for previous source IPs are removed automatically
  - Handlers flushed before dependent plays run
- MariaDB on dedicated host:
  - `bind-address = 0.0.0.0` + `port = 3306`; collocated mode uses `skip-networking`
- Redis on dedicated host:
  - TCP mode bound to `127.0.0.1` + `ansible_host` (private IP) — collocated mode keeps Unix socket
  - `redis_tcp.address` resolves from `ansible_host` (with `default_ipv4` fallback)
- Database creation tasks (`create_pgsql.yml`, `create_mysql.yml`) refactored to delegate to the DB host and use peer auth — no admin TCP credentials required for the playbook-managed scenarios

### New: Managed Database / Redis Support

- New `nextcloud_db.managed` flag for external managed database services (e.g. AWS RDS, Scaleway Managed PostgreSQL/MySQL)
- New `nextcloud_db.admin_user` / `nextcloud_db.admin_password` variables for managed/dedicated admin access
- New `database_admin` entry in `password_vars`
- `postgres_analyzer` and `mariadb_analyzer` understand managed services (no process stats, TCP admin login)
- New `redis_password` user variable (`group_vars/all/redis.yml`) for fixed Redis passwords (e.g. for restore from backup)

### New: Pulumi Stack Examples (Split)

- `Pulumi.nextcloud.yaml.example` replaced by three focused examples:
  - `Pulumi.hetzner-single.yaml.example` — Hetzner all-in-one
  - `Pulumi.hetzner-multitier.yaml.example` — Hetzner with intern-only DB and Redis behind a private network
  - `Pulumi.scaleway-managed.yaml.example` — Scaleway compute + Cloudflare DNS + managed PostgreSQL + managed Redis
- `cloud-stuff/README.md` Quick Start rewritten with explicit 7-step procedure that preserves the generated `encryptionsalt`

### New: Internal-Only Servers (Hetzner)

- Servers with `public_firewall_rules: []` are labelled `intern_only=true` (Hetzner)
- Dynamic Hetzner inventory exposes a new `intern_only` group and supports a jump-host `ProxyCommand` configuration (template lines included)
- Pulumi exports `<name>_private_ipv4` for servers attached to the private network
- `ServerResult` carries the `private_ip` from `hcloud.ServerNetwork`

### New: Per-Server Hetzner Firewalls

- Hetzner compute now creates **one merged firewall per server** instead of one per rule profile
- Removes the 5-firewalls-per-server limit, regardless of how many profiles a host needs
- `collect_required_rule_names()` is no longer used by the Hetzner provider
- SSH waiter is only invoked when the `ssh` rule is part of the firewall (skipped for intern-only hosts)

### Changed

- **Default database type:** `group_vars/all/database.yml` now defaults to `pgsql` (was `mysql`)
- **PostgreSQL version:** default bumped to 18 across all OS families (Debian/Ubuntu, RedHat/Alma/Rocky, openSUSE)
- **Postgres packages:** Python client packages split into `postgresql_python_packages` (per OS family)
- **APCu PHP tuning:** `apc.shm_size = 128M` and `apc.serializer = igbinary` added to both `nextcloud-cli.ini` and `nextcloud-fpm.ini` drop-ins
- **Common vars consolidation:** `onlyoffice_fqdn`, `nextcloudoffice_fqdn`, `eurooffice_fqdn` moved from `group_vars/all/nextcloud.yml` into `group_vars/all/common.yml`
- **Documentation:** `docs/DATABASE-README.md` and `docs/REDIS-README.md` updated for PostgreSQL 18, dedicated/managed scenarios, openSUSE, and the new connection logic
- **README:** EuroOffice added to the tested combinations matrix; database/Redis dedicated rows updated to "Functional"; MariaDB Analyzer linked from the tuning section; inventory links fixed to point to `.example` files
- **EuroOffice preview note** added to the README and the `Dynamic Cloud Inventories` example

### Fixed

- **MariaDB drop-in extension:** `90-nextcloud.cfg` renamed to `90-nextcloud.cnf` so MariaDB actually picks it up
- **Default app bug:** `nextcloud_general.defaultapp` corrected from `file` to `files`
- **Restic backup/restore scripts:** use `passwords.database` instead of the (often empty) `nextcloud_db.password`
- **Coturn (Debian):** group membership change now notifies a coturn restart (TLS group access takes effect immediately)
- **Nextcloud nginx vhost:** OnlyOffice/EuroOffice block guarded against missing groups; combined into a single `/onlyoffice/` location

### Removed

- `Pulumi.nextcloud.yaml.example` (replaced by the three split stack examples)
- Static `postgres_allowed_ipv4` and `postgresql_hba_entries` defaults (auto-detected now)
- `nextcloud_db.migration` field from defaults (was unused)
- Legacy single-firewall set creation in Hetzner compute (replaced by per-server merged firewall)

### Known Outstanding (Tracked TODOs)

- Private-network policies (`network_policies`) are defined in stack examples but not yet enforced; planned as OS-level nftables rules via Ansible (Hetzner has no private-network firewalls)
- Wiring the Pulumi private network into Scaleway managed services (`__main__.py` lines 181, 194)
- Firewall role: actual rule management for Debian (`ufw`/`nftables`) and RedHat (`firewalld`) — only placeholders today

## v3.1 (April 2026)

### New: Whiteboard Role

- New `whiteboard` role for Excalidraw-based collaborative whiteboard with WebSocket server
- Supports collocated deployment (on Nextcloud host) and dedicated server
- Docker container with nginx/Apache reverse proxy integration
- Controlled via `nextcloud_install.whiteboard` variable

### New: Office Co-Hosting (Collocated & Dedicated Server)

- Refactored `nextcloudoffice` and `onlyoffice` roles to support both collocated and dedicated server deployments
- Both roles now auto-detect collocation via inventory group membership
- Split tasks into `collocated.yml` and `dedicated.yml` with shared Docker Compose templates
- Added `nextcloudoffice_fqdn` variable (mirrors `onlyoffice_fqdn` pattern)
- TLS certificates now provisioned for `nextcloudoffice` and `whiteboard` hosts

### New: Nextcloud Role Split

- Monolithic `nextcloud` role split into three focused roles:
  - `nextcloud_prepare` — OS prep, database creation, webserver config
  - `nextcloud_install` — Nextcloud download, installation, upgrade
  - `nextcloud_app` — App configuration (Talk, HPB, Office, Fulltextsearch, ExApps, etc.)

### New: `reinernippes.nextcloud` Ansible Collection

- All `occ` interactions replaced with custom Ansible modules from the `reinernippes.nextcloud` collection
- Modules: `occ_app`, `occ_command`, `occ_config_app`, `occ_config_system`, `occ_group`, `occ_info`, `occ_maintenance`, `occ_user`
- Replaces raw `command: php occ …` calls with idempotent, typed modules (proper changed/failed handling)
- Collection lives in a separate repository (`ansible-collection-nextcloud-occ`)
- Added `nextcloud_occ_env` environment for occ commands

### New: openSUSE Leap 16 Support

- Added `Suse.yml` tasks for all roles:
  coturn, docker, fulltextsearch, mariadb, nextcloud, os, php, postgres, redis, restic_backup, signal, webserver (nginx + apache)
- Added `Suse_repositories.yml` for OS-level repo management (nginx, PostgreSQL, Docker, Elasticsearch)
- Valkey (Redis-fork) support on openSUSE — service name, socket path, and user mappings
- PHP packages: added `posix`, `ctype`, `pcntl`, `exif`, `sysvsem` (separate packages on openSUSE)
- Variable mappings for Suse in `group_vars/all/` (common, database, redis, webserver)

### New: Apache Support on openSUSE

- Split `apache.yml` into OS-specific files: `apache_Debian.yml`, `apache_RedHat.yml`, `apache_Suse.yml`
- openSUSE uses `a2enmod` (via `community.general.apache2_module`) for module management
- Installed `apache2-event` MPM package, removed `apache2-prefork`
- Consolidated `php.conf.j2` template for all OS families
- Removed `00-mpm.conf` static file (no longer needed)
- Removed obsolete `Satisfy Any` directive from `nextcloud.conf.j2` (Apache 2.2 leftover)
- Fixed `web_user`/`web_group` for Suse Apache: `wwwrun`/`www` (was incorrectly `apache`/`apache`)

### New: Firewall Role

- New `firewall` role added to `nextcloud.yml` (runs after `os`, before `precheck`)
- Gathers `service_facts` and disables `firewalld` on openSUSE
- Placeholder tasks for Debian and RedHat
- Planned: per-server port management based on assigned roles

### Improvements

- **Redis/Valkey config:** `lineinfile` regexes now match both commented and active config lines (`^#?\s*...`)
- **Elasticsearch repos:** upgraded from 7.x to 9.x; moved from `fulltextsearch` role into `os/*_repositories.yml` (Suse, RedHat); Debian already had it
- **Fulltextsearch tasks:** cleaned up — removed redundant OS update and repo tasks from `Suse.yml` and `RedHat.yml`
- **PHP (RedHat):** task cleanup and restructuring
- **Coturn:** systemd override and task improvements
- **OS packages:** added `openssh-clients` on Suse for sftp transfer support
- **Firewall policy:** extended `RULE_PROFILES` for whiteboard and office dedicated servers
- **TLS certificates:** acme.sh now provisions certs for `office` and `whiteboard` hosts; additional certificate FQDNs support
- **Preview icons:** new `nextcloud_install.preview` toggle
- **Inventory:** added `whiteboard` and `nextcloudoffice` groups to all example inventories

