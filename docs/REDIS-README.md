# Redis Role

Ansible role to install and configure Redis (Debian/Ubuntu) or Valkey (RedHat) as the in-memory cache backend for Nextcloud. Runs on hosts in the `redis` inventory group.

## Supported Platforms

- Debian / Ubuntu → **Redis** (from the official redis.io repository, added by the [OS role](OS_README.md))
- RHEL / AlmaLinux / Rocky Linux → **Valkey** (from EPEL)
- openSUSE Leap 16 → **Valkey** (from default repositories)

## What This Role Does

1. **Installs Redis/Valkey** packages
2. **Detects deployment mode** automatically — collocated (same host as Nextcloud) or dedicated (separate host)
3. **Configures the server** via in-place edits of the stock configuration file — configuration differs by deployment mode (see [Configuration](#configuration) below)
4. **Adds the webserver user** to the Redis group (collocated only) so PHP-FPM can access the unix socket
5. **Applies system tuning** for Redis:
   - `vm.overcommit_memory = 1` (required for reliable BGSAVE via fork + copy-on-write)
   - Disables Transparent Hugepages (THP) via a oneshot systemd service to avoid latency issues
6. **Starts and enables** the Redis/Valkey service

## Task Flow

```
tasks/main.yml
  ├── Debian.yml                      Install packages (apt)
  │   or RedHat.yml                   Install packages (dnf, from EPEL)
  │   or Suse.yml                     Install packages (zypper)
  ├── Detect collocated vs. dedicated (compare redis and nextcloud group hosts)
  ├── Configure redis/valkey.conf     In-place lineinfile edits (mode-specific)
  ├── Add webserver user to redis group (collocated only)
  ├── sysctl vm.overcommit_memory=1
  ├── Disable transparent hugepages   Check + deploy systemd service
  └── Start and enable service
```

## Configuration

The role modifies the stock configuration file using `lineinfile` (no template is deployed). The exact settings depend on the deployment mode:

### Collocated mode (Redis and Nextcloud on the same host)

| Setting | Value | Purpose |
|---------|-------|--------|
| `port` | `0` | Disable TCP — unix socket only |
| `unixsocket` | `/run/<service>/<service>.sock` | Unix socket path |
| `unixsocketperm` | `770` | Socket accessible by owner + group |
| `bind` | *(commented out)* | Not needed for unix socket |
| `maxclients` | `10240` | Maximum concurrent client connections |
| `requirepass` | `{{ passwords.redis }}` | Authentication password (auto-generated) |

### Dedicated mode (Redis on a separate host)

| Setting | Value | Purpose |
|---------|-------|--------|
| `port` | `6379` | Enable TCP on the standard Redis port |
| `bind` | `127.0.0.1 {{ ansible_host }}` | Listen on loopback and the private network IP |
| `unixsocket` | *(commented out)* | Not used in dedicated mode |
| `maxclients` | `10240` | Maximum concurrent client connections |
| `requirepass` | `{{ passwords.redis }}` | Authentication password (auto-generated) |

`ansible_host` is the address the dynamic inventory assigns to the Redis server — typically the private network IP for `intern_only` servers, falling back to `default_ipv4` otherwise.

### Configuration file path

| Platform | Path |
|----------|------|
| Debian / Ubuntu | `/etc/redis/redis.conf` |
| RedHat / Alma / Rocky | `/etc/valkey/valkey.conf` |
| openSUSE / SLES | `/etc/valkey/valkey.conf` |

## System Tuning

### vm.overcommit_memory

Set to `1` so the kernel allows `fork()` to succeed even when memory is tight. Redis needs this for background persistence (BGSAVE). Skipped in container environments.

### Transparent Hugepages (THP)

THP can cause latency spikes with Redis. The role deploys a oneshot systemd service (`disable-transparent-huge-pages.service`) that writes `never` to:
- `/sys/kernel/mm/transparent_hugepage/enabled`
- `/sys/kernel/mm/transparent_hugepage/defrag`

The service is installed to `systemd_service_path[os_family]` and enabled at boot. Skipped in container environments.

## Variables

### Internal variables (`group_vars/all/redis/main.yml`)

| Variable | Debian | RedHat | Suse |
|----------|--------|--------|------|
| `redis_package_name` | `redis-server`, `redis-tools`, `python3-redis` | `valkey` | `valkey` |
| `redis_conf_path` | `/etc/redis` | `/etc/valkey` | `/etc/valkey` |
| `redis_service_name` | `redis` | `valkey` | `valkey` |
| `redis_systemd_unit` | `redis.service` | `valkey.service` | `valkey.target` |
| `redis_user_name` | `redis` | `valkey` | `valkey` |

### User-defined variables (`group_vars/all/redis.yml`)

| Variable | Default | Description |
|----------|---------|-------------|
| `redis_password` | *(empty → auto-generated)* | Set a fixed Redis password, e.g. when restoring from backup. If empty, a random password is generated and stored in the password file. |

### Connection variables (`group_vars/all/redis/main.yml`)

| Variable | Default | Description |
|----------|---------|-------------|
| `redis_socket.path` | `/run/<service>/<service>.sock` | Unix socket path — resolves to `redis.sock` on Debian, `valkey.sock` on RedHat/SUSE. Used by the Nextcloud PHP config in collocated mode. |
| `redis_socket.perm` | `770` | Socket file permissions |
| `redis_tcp.address` | `hostvars[groups['redis'][0]].ansible_host` (falls back to `default_ipv4`) | TCP address used by Nextcloud to reach a dedicated Redis server. Prefers `ansible_host` to correctly pick up private network IPs for `intern_only` servers. |
| `redis_tcp.port` | `6379` | TCP port for dedicated Redis. Not active in collocated mode (`port 0`). |

### YUM/DNF repository mapping (`redis_yum_repo`)

| Distribution | Repository |
|-------------|-----------|
| RedHat | `epel` |
| AlmaLinux | `epel` |
| Rocky | `epel` |
| Fedora | `epel` |
| CentOS | `epel` |

## Installed Packages

| Debian / Ubuntu | RedHat / Alma / Rocky |
|-----------------|----------------------|
| `redis-server` | `valkey` |
| `redis-tools` | |
| `python3-redis` | |

## Platform Differences

| Aspect | Debian / Ubuntu | RedHat / Alma / Rocky | openSUSE Leap |
|--------|-----------------|----------------------|---------------|
| Software | Redis | Valkey (Redis-compatible fork) | Valkey (Redis-compatible fork) |
| Package source | redis.io APT repository | EPEL | Default repositories |
| Service name | `redis.service` | `valkey.service` | `valkey.target` |
| Config file | `/etc/redis/redis.conf` | `/etc/valkey/valkey.conf` | `/etc/valkey/valkey.conf` |
| User / Group | `redis` | `valkey` | `valkey` |

## Unused Artifacts

| File | Description |
|------|-------------|
| `vars/main.yml` | Entirely commented out — all variables moved to `group_vars/all/redis/main.yml` |
