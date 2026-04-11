# OS Role

Ansible role to prepare the operating system for a Nextcloud deployment. Runs on **all** hosts as the first role in the playbook.

## Supported Platforms

- Debian / Ubuntu
- RHEL / AlmaLinux / Rocky Linux
- openSUSE Leap 16

## What This Role Does

1. **Adds package repositories** (nginx, PHP/Sury/Ondrej, PostgreSQL, Redis, Docker, Elasticsearch) depending on host group membership and selected components
2. **Updates the OS** (`apt dist-upgrade` or `dnf update`)
3. **Installs base packages** required by subsequent roles and general administration
4. **Configures hostname and `/etc/hosts`** — sets the hostname from `inventory_hostname`, deploys a clean `/etc/hosts` via template (removes the Debian default `127.0.1.1` entry, detects DHCP vs. static IP)
5. **Manages credentials** — generates random passwords for all components and stores them in a central password file

## Task Flow

```
tasks/main.yml
  ├── Debian.yml                 Debian/Ubuntu specific tasks
  │   └── Debian_repositories.yml   Add APT repositories (nginx, PHP, PostgreSQL, Redis, Docker, Elasticsearch)
  ├── RedHat.yml                 RHEL/Alma/Rocky/Fedora specific tasks
  │   └── RedHat_repositories.yml   Add YUM/DNF repositories (EPEL, nginx, PostgreSQL)
  ├── Suse.yml                   openSUSE Leap specific tasks
  │   └── Suse_repositories.yml     Add zypper repositories (nginx, PostgreSQL, Docker, Elasticsearch)
  ├── (set hostname + deploy /etc/hosts via etc_hosts.j2 template)
  └── passwords.yml              Generate and persist passwords for all components
```

## Repository Setup

### Debian / Ubuntu

Repositories are added conditionally based on host group membership and configuration:

| Repository | Condition | Source |
|------------|-----------|--------|
| nginx (mainline) | Host in `webserver` group, `nextcloud_webserver_type == 'nginx'` | `nginx.org` |
| PHP (Ondrej/Sury) | Host in `webserver` group | Launchpad PPA (Ubuntu) or `packages.sury.org` (Debian) |
| PostgreSQL | Host in `database` group, `nextcloud_db.type == 'pgsql'` | `apt.postgresql.org` |
| Redis | Host in `redis` group | `packages.redis.io` |
| Docker | Host in `docker` group | `download.docker.com` |
| Elasticsearch | Host in `elasticsearch` group | `artifacts.elastic.co` |

### RedHat / Alma / Rocky / Fedora

| Repository | Condition | Source |
|------------|-----------|--------|
| EPEL | Always | `epel-release` package |
| nginx (mainline) | Host in `webserver` group | `nginx.org` |
| PostgreSQL | Host in `database` group | `download.postgresql.org` |

### openSUSE Leap

| Repository | Condition | Source |
|------------|-----------|--------|
| nginx (mainline) | Host in `webserver` group | `nginx.org` |
| PostgreSQL | Host in `database` group | `download.postgresql.org` |
| Docker CE | Host in `docker` group | `download.docker.com` |
| Elasticsearch 9.x | Host in `elasticsearch` group | `artifacts.elastic.co` |

## Installed Packages

### Debian / Ubuntu

```
apt-transport-https  bash-completion  bzip2  ca-certificates  cron  curl
dialog  dirmngr  facter  git  gnupg  gnupg2  htop  jq  libfontconfig1
libfuse2  locate  lsb-release  net-tools  nodejs  npm  rsyslog  screen
smbclient  socat  sqlite3  ssl-cert  sudo  tree  unzip  vim  wget  zip
```

Additionally on Ubuntu and Debian ≤ 12: `software-properties-common`

### RedHat / Alma / Rocky / Fedora

```
zip  unzip  bzip2  curl  wget  cronie  firewalld  tar
python3-policycoreutils  python3-cryptography
```

## Hostname and `/etc/hosts`

The role sets the system hostname and deploys a clean `/etc/hosts` via template (`etc_hosts.j2`).

**Hostname:** Set to the short name derived from `inventory_hostname` (e.g. `nextcloud.example.com` → `nextcloud`).

**`/etc/hosts` behavior:**

| Network type | `/etc/hosts` content |
|---|---|
| **Static IP** | `<real-ip>  <fqdn>  <shortname>` — FQDN resolves to the actual server IP |
| **DHCP** | Only `localhost` entries — hostname resolution is left to DNS |

**Why this matters:**

Many cloud providers (e.g. Hetzner) ship Debian images with a default `/etc/hosts` containing `127.0.1.1 debian`. This causes problems for services like coturn/TURN that resolve the server's FQDN to a loopback address instead of the real IP. The template removes the `127.0.1.1` entry entirely and ensures the FQDN always points to the correct address.

DHCP detection uses `ansible_facts['default_ipv4']['type']`. On DHCP-managed interfaces, no IP-to-hostname mapping is written because the address may change — DNS is expected to handle resolution.

## Password Management

The role generates and persists passwords for all components in a single YAML file.

| Variable | Default | Description |
|----------|---------|-------------|
| `password_file` | `/opt/nextcloud/password_file.yml` | Path to the credential store |
| `password_vars` | Defined in `group_vars/all/common.yml` | List of password entries to manage |

**Behavior:**

- If the password file already exists, existing passwords are preserved
- New passwords are only generated for entries not yet present in the file
- If a password is pre-defined in the inventory (e.g. `nextcloud_passwd`, `nextcloud_db.password`), that value is used instead of a random one
- Random passwords are 32 characters (letters + digits)
- The file is owned by `root:root` with mode `0600`
- Passwords are distributed to all hosts via `set_fact` so every role can access them

### Managed Password Entries

| Entry | Pre-defined variable | Used by |
|-------|---------------------|---------|
| `nextcloud_admin` | `nextcloud_passwd` | Nextcloud admin account |
| `database` | `nextcloud_db.password` | Database server |
| `restic_backup_secret` | `restic_backup_secret` | Restic backup |
| `redis` | — | Redis server |
| `coturn` | — | Coturn (Talk) |
| `signal_nextcloud_secret` | — | HPB signaling |
| `signal_internal_secret` | — | HPB signaling |
| `signal_recording_secret` | — | HPB signaling |
| `collabora_admin` | — | Collabora Online |
| `hp_shared_key` | — | High Performance Backend |

## Unused Artifacts

The following files exist in the role but serve no function:

| File | Description |
|------|-------------|
| `handlers/main.yml` | Empty handlers file (contains only YAML header) |
| `vars/main.yml` | Empty vars file (contains only YAML header) |
