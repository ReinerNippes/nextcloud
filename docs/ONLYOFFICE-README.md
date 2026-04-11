# OnlyOffice Role

Documentation for deploying OnlyOffice Document Server with this playbook via the `onlyoffice` role and configuring integration in the `nextcloud` role.

## Overview

This setup uses two layers:

1. `roles/onlyoffice` deploys the OnlyOffice Document Server container — either collocated (appended to the shared Compose file) or on a dedicated server (standalone Compose + nginx reverse proxy).
2. `roles/nextcloud_app/tasks/configure/onlyoffice.yml` installs and configures the Nextcloud `onlyoffice` app via the `reinernippes.nextcloud` collection modules.

## Role: `onlyoffice`

### What the role does

- Creates persistent directories for OnlyOffice data, logs, lib, and db
- Detects deployment mode automatically based on inventory group membership:
  - **Collocated** (onlyoffice host == nextcloud host): appends service block to shared `/opt/nextcloud/docker_compose/compose.yml`
  - **Dedicated server**: deploys a standalone Compose file with nginx reverse proxy (`onlyoffice-dedicated-nginx.conf.j2`)
- Mounts TLS certificate files into the container
- Enables JWT-based auth for Nextcloud integration:
  - `JWT_ENABLED=true`
  - `JWT_SECRET={{ passwords.onlyoffice_secret }}`

### Role structure

```
roles/onlyoffice/tasks/
  ├── main.yml           Determines collocated vs. dedicated
  ├── collocated.yml     Appends to shared compose.yml
  └── dedicated.yml      Standalone compose + nginx reverse proxy
```

### Inventory requirement

The role runs on hosts in inventory group `onlyoffice`.

Two deployment patterns are supported:

1. Collocated (same host as Nextcloud):

```yaml
onlyoffice:
  hosts:
    nextcloud.example.com:
```

2. Dedicated host:

```yaml
onlyoffice:
  hosts:
    onlyoffice.example.com:
```

## Nextcloud app integration

When `nextcloud_install.onlyoffice` is enabled, the `nextcloud_app` role includes:

- `roles/nextcloud_app/tasks/configure/onlyoffice.yml`

This task file configures Nextcloud app integration using `reinernippes.nextcloud` collection modules:

- Installs and enables the `onlyoffice` app via `reinernippes.nextcloud.occ_app`
- Sets server URL via `reinernippes.nextcloud.occ_config_app`:
  - `DocumentServerUrl` → `https://<onlyoffice_fqdn>:<onlyoffice_ssl_port>`
- Sets JWT secret via `reinernippes.nextcloud.occ_config_app`
- For self-signed/test certificates, disables TLS peer verification via `reinernippes.nextcloud.occ_config_system`:
  - `onlyoffice verify_peer_off` → `true`

## Required and relevant variables

From `group_vars/all/nextcloud.yml`:

- `nextcloud_install.onlyoffice` (feature toggle)
- `onlyoffice_fqdn` (defaults to first host in `onlyoffice` group)

From `group_vars/all/common.yml`:

- `onlyoffice_ssl_port` (default: `8443`)
- `passwords.onlyoffice_secret`

From TLS configuration:

- `tls_certificate.type`
- `tls_certificate_test`
- `tls_certificate_key`
- `tls_certificate_file`
- `tls_certificate_fullchain`
- `tls_certificate_directory`

## Port guidance

Current default in this repository is:

- `onlyoffice_ssl_port: 8443`

This avoids conflict when OnlyOffice is collocated with Nextcloud (where 443 is already used by the webserver).

For dedicated OnlyOffice hosts, you can override to 443 in inventory or group vars:

```yaml
all:
  vars:
    onlyoffice_ssl_port: 443
```

## Task flow

```text
nextcloud.yml
  -> role: onlyoffice (hosts: onlyoffice)
      -> roles/onlyoffice/tasks/main.yml
          -> collocated.yml (if same host as nextcloud)
          -> dedicated.yml  (if separate host)
  -> role: docker (task_from: compose_up.yml)
      -> starts onlyoffice container
  -> role: nextcloud_app (hosts: nextcloud)
      -> roles/nextcloud_app/tasks/configure/onlyoffice.yml
```

## Notes

- This setup configures HTTPS inside the OnlyOffice container using mounted certificate files.
- For self-signed/test certificates, both container and Nextcloud-side settings are adapted to allow integration.
- The role currently uses the `onlyoffice/documentserver:latest` image tag.
