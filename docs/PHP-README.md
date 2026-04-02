# PHP Role

Ansible role to install and configure PHP-FPM for Nextcloud.

## Supported Platforms

- Debian / Ubuntu (via Sury PPA)
- RHEL / AlmaLinux / Rocky Linux (via Remi repository)

## What This Role Does

1. **Installs PHP** with all required and (optionally) additional extensions
2. **Deploys drop-in INI files** (`99-nextcloud.ini`) — no stock config files are modified
3. **Deploys a dedicated `[nextcloud]` FPM pool** (`nextcloud.conf`) and disables the default `[www]` pool
4. **Tunes `php-fpm.conf`** (emergency restart, process control timeout)
5. **Configures SELinux** contexts and ACLs (RedHat only, when SELinux is enabled)
6. **Enables and starts** the `php-fpm` service

## Configuration Strategy

The role never edits stock PHP configuration files (`php.ini`, `www.conf`, etc.).
Instead it uses PHP's built-in drop-in and override mechanisms:

### Drop-in INI files (`conf.d/99-nextcloud.ini`)

PHP scans a `conf.d/` directory for additional `.ini` files that override the main `php.ini`.

| OS family | CLI scan directory | FPM scan directory |
|-----------|--------------------|--------------------|
| Debian    | `/etc/php/X.Y/cli/conf.d/` | `/etc/php/X.Y/fpm/conf.d/` |
| RedHat    | `/etc/php.d/` (shared) | `/etc/php.d/` (shared) |

On **Debian/Ubuntu**, CLI and FPM have separate `conf.d/` directories, so each gets its
own `99-nextcloud.ini` with different values (e.g. `memory_limit = -1` for CLI vs `1G` for FPM).

On **RedHat/Alma/Rocky**, CLI and FPM share `/etc/php.d/`. Only the CLI drop-in is deployed
there (with `memory_limit = -1`). FPM-specific overrides are applied via `php_admin_value`
directives in the pool configuration (see below).

### FPM pool configuration (`nextcloud.conf`)

The default `[www]` pool is disabled (renamed to `www.conf.disabled`).
A dedicated `[nextcloud]` pool is deployed via the `nextcloud-pool.conf.j2` template.

On RedHat, the pool config includes `php_admin_value` directives to override settings
that differ between CLI and FPM:

```ini
php_admin_value[memory_limit] = 1G
php_admin_value[cgi.fix_pathinfo] = 0
php_admin_value[session.cookie_secure] = 1
php_admin_value[session.gc_maxlifetime] = 36000
```

> **Note:** `PHP_INI_SYSTEM` directives like `disable_functions` and `expose_php` cannot be
> overridden per pool — they apply globally to both CLI and FPM on RedHat.

## Templates

| Template | Purpose | Deployed to |
|----------|---------|-------------|
| `nextcloud-cli.ini.j2` | CLI PHP settings + opcache + apcu | `conf.d/99-nextcloud.ini` (CLI) |
| `nextcloud-fpm.ini.j2` | FPM PHP settings + opcache + session | `conf.d/99-nextcloud.ini` (FPM, Debian only) |
| `nextcloud-pool.conf.j2` | FPM pool `[nextcloud]` | `nextcloud.conf` in pool directory |

## Files Managed on Disk

### Debian / Ubuntu

```
/etc/php/X.Y/cli/conf.d/99-nextcloud.ini    ← CLI drop-in
/etc/php/X.Y/fpm/conf.d/99-nextcloud.ini    ← FPM drop-in
/etc/php/X.Y/fpm/pool.d/nextcloud.conf      ← FPM pool
/etc/php/X.Y/fpm/pool.d/www.conf.disabled   ← default pool (disabled)
/etc/php/X.Y/fpm/php-fpm.conf               ← tuned via lineinfile
```

### RedHat / AlmaLinux / Rocky

```
/etc/php.d/99-nextcloud.ini                  ← shared drop-in (CLI values)
/etc/php-fpm.d/nextcloud.conf               ← FPM pool (with php_admin_value overrides)
/etc/php-fpm.d/www.conf.disabled            ← default pool (disabled)
/etc/php-fpm.conf                           ← tuned via lineinfile
```

## Required Variables

| Variable | Description |
|----------|-------------|
| `php_version` | PHP version string, e.g. `"8.3"` |
| `nextcloud_db.type` | Database type: `mysql` or `pgsql` |
| `nextcloud_webserver_type` | Webserver: `nginx` or `apache` |
| `php_tuning` | FPM process manager tuning — see [PHP_tuning.md](PHP_tuning.md) |
| `web_user` | Dict mapping webserver type and OS family to the service user |
| `web_group` | Dict mapping webserver type and OS family to the service group |
| `php_socket` | Dict mapping OS family to the FPM socket path |

## Optional Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `php_install_optional_packages` | `false` | Install smbclient, ldap, imap extensions |

## Task Flow

```
tasks/main.yml
  ├── Debian.yml or RedHat.yml    (repo setup + package install)
  ├── configure.yml               (drop-in INIs + pool + php-fpm.conf)
  ├── selinux.yml                 (RedHat + SELinux enabled only)
  └── enable php-fpm service
```
