# Changelog

## v3.1 (unreleased)

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
- Removed leftover `roles/php/vars/main.yml-new`
