# Docker Role

Ansible role to install Docker and manage a shared Docker Compose file for all containerized Nextcloud services. Runs on hosts in the `docker` inventory group.

## Supported Platforms

- Debian / Ubuntu (Docker CE from `download.docker.com`, added by the [OS role](OS_README.md))
- RHEL / AlmaLinux / Rocky Linux (Docker CE from docker.com repo)
- openSUSE Leap 16 (Docker CE from `download.docker.com`, added by the [OS role](OS_README.md))

## What This Role Does

1. **Removes conflicting packages** (old `docker.io`, `podman`, etc.)
2. **Installs Docker CE** and the Compose plugin
3. **Enables and starts** the Docker daemon
4. **Adds the deploy user** to the `docker` group (when running via sudo)
5. **Creates the shared Compose directory** (`/opt/nextcloud/docker_compose/`)
6. **Seeds the Compose file** with the `watchtower` service and a `nextcloud` Docker network
7. **Creates the Docker network** `nextcloud`

The role is invoked **twice** in the main playbook:

- **First pass** (`main.yml`): Installs Docker, creates the Compose file with the base services
- **Second pass** (`compose_up.yml`): Starts all containers after other roles have added their services

## Shared Compose File Mechanism

The central design pattern of this role is a **shared Docker Compose file** that multiple roles contribute to. Instead of each role managing its own container lifecycle, all containerized services are collected into a single Compose file and started together.

### How It Works

```
1. docker role        → creates /opt/nextcloud/docker_compose/compose.yml
                         with watchtower service + nextcloud network
                                    ↓
2. exapp_hapr role    → appends appapi-harp service block
3. nextcloudoffice    → appends collabora/code service block
4. signal role        → appends nats-server + recording service blocks
                                    ↓
5. docker role        → runs compose_up.yml → docker compose up
                                    ↓
6. nextcloud role     → installs Nextcloud (containers already running)
```

Each role uses `ansible.builtin.blockinfile` with a unique marker to insert its service definition into the existing Compose file. This allows services to be added or removed independently without conflicting with each other.

### Contributing Roles

| Role | Service(s) added | Marker | Condition |
|------|-----------------|--------|-----------|
| **docker** | `watchtower` | `docker compose file for nextcloud services` | Always |
| **exapp_hapr** | `appapi-harp` | `appapi-harp service` | `nextcloud_install.hapr` |
| **nextcloudoffice** | `nextcloudoffice` (Collabora) | `nextcloudoffice service` | `nextcloud_install.nextcloudoffice` |
| **signal** | `nats-server` | `nats-server service` | `nextcloud_install.hpb` |
| **signal** | `nextcloud-recording` | `nextcloud-recording service` | `nextcloud_install.hpb` |

### Resulting Compose File Structure

```yaml
# /opt/nextcloud/docker_compose/compose.yml
---
networks:
  nextcloud:
    external: true
services:
  watchtower:       # always present (docker role)
    ...
  appapi-harp:      # if hapr enabled (exapp_hapr role)
    ...
  nextcloudoffice:  # if nextcloudoffice enabled (nextcloudoffice role)
    ...
  nats-server:      # if hpb enabled (signal role)
    ...
  nextcloud-recording:  # if hpb enabled (signal role)
    ...
```

## Task Flow

### First Pass — Installation (`main.yml`)

```
tasks/main.yml
  ├── Debian.yml              Remove old Docker, install docker-ce
  │   or RedHat.yml           Remove conflicting packages, add repo, install docker-ce
  ├── Enable and start Docker
  ├── Add deploy user to docker group
  ├── Create /opt/nextcloud/docker_compose/
  ├── Seed compose.yml with watchtower service
  └── Create Docker network "nextcloud"
```

### Second Pass — Start Containers (`compose_up.yml`)

```
tasks/compose_up.yml
  └── docker_compose_v2 up    Start all services defined in compose.yml
```

This task delegates to each Docker host and uses `pull: missing` to only download images that aren't already present.

## Playbook Execution Order

The Docker role's two-pass design is orchestrated in the main playbook:

```
nextcloud.yml
  ├── os              (all hosts)
  ├── redis           (redis hosts)
  ├── webserver       (webserver hosts)
  ├── tls-certificate (webserver, coturn, signal hosts)
  ├── database        (database hosts)
  ├── docker          ← First pass: install Docker, seed compose.yml
  ├── exapp_hapr      ← Adds appapi-harp to compose.yml
  ├── fulltextsearch  (elasticsearch hosts)
  ├── nextcloudoffice ← Adds collabora to compose.yml
  ├── coturn          (coturn hosts)
  ├── signal          ← Adds nats + recording to compose.yml
  ├── docker          ← Second pass: compose_up.yml (start all containers)
  ├── nextcloud       (Nextcloud install — containers already running)
  └── ...
```

## Docker Network

All services share a user-defined bridge network called `nextcloud`, created as an external network by this role. Services that need to reach each other (e.g. Collabora → Nextcloud) communicate through this network. The `appapi-harp` service uses `network_mode: host` instead, as it needs direct host access.

## Watchtower

The base Compose file always includes [Watchtower](https://containrrr.dev/watchtower/), which automatically updates running containers:

| Setting | Default | Description |
|---------|---------|-------------|
| `WATCHTOWER_POLL_INTERVAL` | `86400` (24h) | How often to check for image updates |
| `WATCHTOWER_CLEANUP` | `true` | Remove old images after update |
| `WATCHTOWER_INCLUDE_RESTARTING` | `true` | Also update restarting containers |
| `TZ` | `Europe/Berlin` | Timezone for log timestamps |

All services opt in via the label `com.centurylinklabs.watchtower.enable: "true"`.

## Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `watchtower_poll_interval` | `86400` | Watchtower polling interval in seconds |
| `nextcloud_timezone` | `Europe/Berlin` | Timezone for container environments |
| `nextcloud_fqdn` | *(from inventory)* | Used by Collabora and recording services |

## Installed Packages

| Debian / Ubuntu | RedHat / Alma / Rocky |
|-----------------|----------------------|
| `docker-ce` | `docker-ce` |
| `docker-compose-plugin` | `docker-compose-plugin` |
| `python3-docker` | `docker-ce-cli` |
| | `containerd.io` |
| | `docker-buildx-plugin` |

## Platform Differences

| Aspect | Debian / Ubuntu | RedHat / Alma / Rocky |
|--------|-----------------|----------------------|
| Repository | Added by [OS role](OS_README.md) via `deb822_repository` | Added directly via `get_url` to `/etc/yum.repos.d/` |
| Conflicting packages | `docker`, `docker-engine`, `docker.io` | `docker`, `docker-client*`, `docker-common`, `docker-latest*`, `podman`, `runc` |
| Python bindings | `python3-docker` (apt) | Not installed via dnf (may need manual install) |

## Files Managed on Disk

```
/opt/nextcloud/docker_compose/              Compose project directory
/opt/nextcloud/docker_compose/compose.yml   Shared Compose file (assembled by multiple roles)
```
