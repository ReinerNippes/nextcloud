# Nextcloud Office (Collabora) Role

Documentation for deploying Collabora Online with this playbook via the `nextcloudoffice` role and configuring integration in the `nextcloud` role.

## Overview

This setup uses two layers:

1. `roles/nextcloudoffice` deploys a Collabora container (`collabora/code`) — either collocated (appended to the shared Compose file) or on a dedicated server (standalone Compose + nginx reverse proxy).
2. `roles/nextcloud_app/tasks/configure/nextcloudoffice.yml` installs and configures the Nextcloud app (`richdocuments`) via the `reinernippes.nextcloud` collection modules.

## Role: `nextcloudoffice`

### What the role does

- Includes OS-specific package tasks:
  - Debian/Ubuntu: ensures apt components and installs fonts (`ttf-mscorefonts-installer`, `fonts-noto-core`)
  - RedHat-family: installs Noto fonts and helper packages
  - openSUSE: installs required fonts
- Detects deployment mode automatically based on inventory group membership:
  - **Collocated** (nextcloudoffice host == nextcloud host): appends service block to shared `/opt/nextcloud/docker_compose/compose.yml`
  - **Dedicated server**: deploys a standalone Compose file with nginx reverse proxy (`nextcloudoffice-dedicated-nginx.conf.j2`)
- Configures container environment, including:
  - `aliasgroup1` based on `nextcloud_fqdn`
  - admin password from `passwords.collabora_admin`

### Role structure

```
roles/nextcloudoffice/tasks/
  ├── main.yml           Determines collocated vs. dedicated
  ├── Debian.yml         OS-specific packages (Debian/Ubuntu)
  ├── RedHat.yml         OS-specific packages (RHEL/Alma/Rocky)
  ├── Suse.yml           OS-specific packages (openSUSE)
  ├── collocated.yml     Appends to shared compose.yml
  └── dedicated.yml      Standalone compose + nginx reverse proxy
```

### Inventory requirement

The role runs on hosts in inventory group `nextcloudoffice`.

Typical collocated setup:

```yaml
nextcloudoffice:
  hosts:
    nextcloud.example.com:
```

Dedicated server setup:

```yaml
nextcloudoffice:
  hosts:
    office.example.com:
```

## Nextcloud app integration

When `nextcloud_install.nextcloudoffice` is enabled, the `nextcloud_app` role includes:

- `roles/nextcloud_app/tasks/configure/nextcloudoffice.yml`

This task file configures Nextcloud app integration using `reinernippes.nextcloud` collection modules:

- Installs and enables the `richdocuments` app via `reinernippes.nextcloud.occ_app`
- Sets WOPI URL via `reinernippes.nextcloud.occ_config_app`:
  - `wopi_url` → `https://<nextcloudoffice_fqdn>:<nextcloud_ssl_port>`
- Sets WOPI allowlist
- Disables certificate verification for self-signed/test certs
- Runs `richdocuments:activate-config`

## Required and relevant variables

From `group_vars/all/nextcloud.yml`:

- `nextcloud_install.nextcloudoffice` (feature toggle)
- `nextcloud_fqdn`
- `nextcloudoffice_fqdn` (defaults to first host in `nextcloudoffice` group)

From web/TLS config:

- `nextcloud_ssl_port`

From password generation (`group_vars/all/common.yml`):

- `passwords.collabora_admin`

## Webserver behavior

If `nextcloud_install.nextcloudoffice` is true, Nextcloud webserver templates add proxy locations for Collabora endpoints (for example `/browser` and `/hosting/discovery`) and forward traffic to `https://127.0.0.1:9980`.

## Task flow

```text
nextcloud.yml
  -> role: nextcloudoffice (hosts: nextcloudoffice)
      -> roles/nextcloudoffice/tasks/main.yml
          -> collocated.yml (if same host as nextcloud)
          -> dedicated.yml  (if separate host)
  -> role: docker (task_from: compose_up.yml)
      -> starts collabora container
  -> role: nextcloud_app (hosts: nextcloud)
      -> roles/nextcloud_app/tasks/configure/nextcloudoffice.yml
```

## Notes

- This role is intended for Collabora Online integration (Nextcloud Office app `richdocuments`).
- The role currently uses the `collabora/code:latest` image tag.
- For stable operations, pinning image versions can be considered in production environments.
