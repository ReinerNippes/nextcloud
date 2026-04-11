# Changelog

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

