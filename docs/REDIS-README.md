# Redis Role

Ansible role to install and configure Redis (Debian/Ubuntu) or Valkey (RedHat) as the in-memory cache backend for Nextcloud. Runs on hosts in the `redis` inventory group.

## Supported Platforms

- Debian / Ubuntu → **Redis** (from the official redis.io repository, added by the [OS role](OS_README.md))
- RHEL / AlmaLinux / Rocky Linux → **Valkey** (from EPEL)
- openSUSE Leap 16 → **Valkey** (from default repositories)

## What This Role Does

1. **Installs Redis/Valkey** packages
2. **Configures the server** via in-place edits of the stock configuration file:
   - Disables TCP listening (`port 0`)
   - Enables a unix socket for local communication
   - Sets `maxclients 10240`
   - Sets a random password (from the central password store)
3. **Adds the webserver user** to the Redis group (when Redis and Nextcloud run on the same host) so PHP-FPM can access the unix socket
4. **Applies system tuning** for Redis:
   - `vm.overcommit_memory = 1` (required for reliable BGSAVE via fork + copy-on-write)
   - Disables Transparent Hugepages (THP) via a oneshot systemd service to avoid latency issues
5. **Starts and enables** the Redis/Valkey service

## Task Flow

```
tasks/main.yml
  ├── Debian.yml                      Install packages (apt)
  │   or RedHat.yml                   Install packages (dnf, from EPEL)
  ├── Configure redis/valkey.conf     In-place lineinfile edits
  ├── Add webserver user to redis group (if co-located)
  ├── sysctl vm.overcommit_memory=1
  ├── Disable transparent hugepages   Check + deploy systemd service
  └── Start and enable service
```

## Configuration

The role modifies the stock configuration file using `lineinfile` (no template is deployed):

| Setting | Value | Purpose |
|---------|-------|---------|
| `port` | `0` | Disable TCP — communication via unix socket only |
| `unixsocket` | `/run/<service>/<service>.sock` | Unix socket path |
| `unixsocketperm` | `770` | Socket accessible by owner + group |
| `maxclients` | `10240` | Maximum concurrent client connections |
| `requirepass` | `{{ passwords.redis }}` | Authentication password (auto-generated) |

### Configuration file path

| Platform | Path |
|----------|------|
| Debian / Ubuntu | `/etc/redis/redis.conf` |
| RedHat / Alma / Rocky | `/etc/valkey/valkey.conf` |

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

### Connection variables

| Variable | Default | Description |
|----------|---------|-------------|
| `redis_socket.path` | `/run/{{ redis_service_name[ansible_facts['os_family']] }}/{{ redis_service_name[ansible_facts['os_family']] }}.sock` | Unix socket path (used by Nextcloud PHP config; resolves to `redis.sock` on Debian and `valkey.sock` on RedHat/Suse) |
| `redis_socket.perm` | `770` | Socket file permissions |
| `redis_tcp.address` | *(auto-detected from inventory)* | TCP address (for remote Redis setups) |
| `redis_tcp.port` | `6379` | TCP port (not used when `port 0` is set) |

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
