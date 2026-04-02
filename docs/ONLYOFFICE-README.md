# OnlyOffice Role

Documentation for deploying OnlyOffice Document Server with this playbook via the `onlyoffice` role and configuring integration in the `nextcloud` role.

## Overview

This setup uses two layers:

1. `roles/onlyoffice` adds the OnlyOffice Document Server container to the shared Docker Compose file.
2. `roles/nextcloud/tasks/configure/onlyoffice.yml` installs and configures the Nextcloud `onlyoffice` app via `occ`.

## Role: `onlyoffice`

### What the role does

- Creates persistent directories:
  - `/opt/onlyoffice/DocumentServer/data`
  - `/opt/onlyoffice/DocumentServer/logs`
  - `/opt/onlyoffice/DocumentServer/lib`
  - `/opt/onlyoffice/DocumentServer/db`
- Appends an `onlyoffice` service block to `/opt/nextcloud/docker_compose/compose.yml`
- Exposes container HTTPS as:
  - `<onlyoffice_ssl_port>:443`
- Mounts TLS certificate files into the container
- Enables JWT-based auth for Nextcloud integration:
  - `JWT_ENABLED=true`
  - `JWT_SECRET={{ passwords.onlyoffice_secret }}`

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

## Nextcloud role integration

When `nextcloud_install.onlyoffice` is enabled, the `nextcloud` role includes:

- `roles/nextcloud/tasks/configure/onlyoffice.yml`

This task file configures Nextcloud app integration using `occ`:

- Installs app `onlyoffice` when missing
- Enables app `onlyoffice` when disabled
- Sets server URL:
  - `config:app:set onlyoffice DocumentServerUrl --value https://<onlyoffice_fqdn>:<onlyoffice_ssl_port>`
- Sets JWT secret:
  - `config:app:set onlyoffice jwt_secret --value <passwords.onlyoffice_secret>`
- For self-signed/test certificates, disables TLS peer verification in Nextcloud:
  - `config:system:set onlyoffice verify_peer_off --value=true --type=boolean`

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
  -> role: docker (task_from: compose_up.yml)
      -> starts onlyoffice container
  -> role: nextcloud (hosts: nextcloud)
      -> roles/nextcloud/tasks/configure/onlyoffice.yml
```

## Notes

- This setup configures HTTPS inside the OnlyOffice container using mounted certificate files.
- For self-signed/test certificates, both container and Nextcloud-side settings are adapted to allow integration.
- The role currently uses the `onlyoffice/documentserver:latest` image tag.
