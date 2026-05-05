# EuroOffice Role

> **Preview:** This role is currently in preview. Configuration details and behaviour may change in future releases.

Documentation for deploying the Euro-Office Document Server with this playbook via the `eurooffice` role and configuring Nextcloud integration in the `nextcloud_app` role.

## Overview

Euro-Office is an OnlyOffice-compatible document server. The integration in this playbook follows the same architecture as the `onlyoffice` role — the Nextcloud `onlyoffice` app is used for the integration on both sides.

This setup uses two layers:

1. `roles/eurooffice` deploys the Euro-Office Document Server container — either collocated (appended to the shared Compose file) or on a dedicated server (standalone Compose + nginx reverse proxy).
2. `roles/nextcloud_app/tasks/configure/eurooffice.yml` installs and configures the Nextcloud `onlyoffice` app via the `reinernippes.nextcloud` collection modules.

> **Note:** Euro-Office and OnlyOffice are mutually exclusive. Enable only one at a time via `nextcloud_install.eurooffice` or `nextcloud_install.onlyoffice`.

## Role: `eurooffice`

### What the role does

- Creates persistent directories for Euro-Office data, logs, lib, and db under `/opt/eurooffice/`
- Detects deployment mode automatically based on inventory group membership:
  - **Collocated** (eurooffice host == nextcloud host): appends service block to shared `/opt/nextcloud/docker_compose/compose.yml`; the Nextcloud webserver proxies `/onlyoffice/` to `http://127.0.0.1:8443/`
  - **Dedicated server**: deploys a standalone Compose file with nginx reverse proxy (`eurooffice-dedicated-nginx.conf.j2`) on port 443
- Enables JWT-based auth for Nextcloud integration:
  - `JWT_SECRET={{ passwords.eurooffice_secret }}`

### Role structure

```
roles/eurooffice/tasks/
  ├── main.yml           Determines collocated vs. dedicated
  ├── collocated.yml     Appends to shared compose.yml
  └── dedicated.yml      Standalone compose + nginx reverse proxy

roles/eurooffice/templates/
  └── eurooffice-dedicated-nginx.conf.j2   nginx TLS reverse proxy for dedicated server
```

### Inventory requirement

The role runs on hosts in the inventory group `eurooffice`.

Two deployment patterns are supported:

1. Collocated (same host as Nextcloud):

```yaml
eurooffice:
  hosts:
    nextcloud.example.com:
```

2. Dedicated host:

```yaml
eurooffice:
  hosts:
    eurooffice.example.com:
```

## Nextcloud app integration

When `nextcloud_install.eurooffice` is enabled, the `nextcloud_app` role includes:

- `roles/nextcloud_app/tasks/configure/eurooffice.yml`

This task file configures the Nextcloud integration using `reinernippes.nextcloud` collection modules:

- Installs and enables the `onlyoffice` app via `reinernippes.nextcloud.occ_app`
- Determines the backend URL based on deployment mode:
  - **Collocated**: `https://<nextcloud_fqdn>/onlyoffice/`
  - **Dedicated**: `https://<eurooffice_fqdn>`
- Sets `DocumentServerUrl` via `reinernippes.nextcloud.occ_config_app`
- Sets `jwt_secret` via `reinernippes.nextcloud.occ_config_app`
- For self-signed/test certificates, disables TLS peer verification via `reinernippes.nextcloud.occ_config_system`:
  - `onlyoffice verify_peer_off` → `true`

## Required and relevant variables

From `group_vars/all/nextcloud.yml`:

| Variable | Default | Description |
|----------|---------|-------------|
| `nextcloud_install.eurooffice` | `false` | Feature toggle — set to `true` to deploy Euro-Office |

From `group_vars/all/common.yml`:

| Variable | Default | Description |
|----------|---------|-------------|
| `eurooffice_fqdn` | First host in `eurooffice` group | Domain name of the Euro-Office server. For collocated setups this equals `nextcloud_fqdn` |
| `passwords.eurooffice_secret` | *(auto-generated)* | JWT secret shared between Euro-Office and Nextcloud |

From TLS configuration:

- `tls_certificate.type`
- `tls_certificate_test`
- `tls_certificate_key`
- `tls_certificate_fullchain`

## Port guidance

The Euro-Office container is mapped to `127.0.0.1:8443:80` on the host in both collocated and dedicated modes:

- **Collocated**: the Nextcloud webserver (nginx/Apache) proxies `/onlyoffice/` → `http://127.0.0.1:8443/`
- **Dedicated**: nginx terminates TLS on port 443 and proxies to `http://127.0.0.1:8443`

Since Euro-Office and OnlyOffice are mutually exclusive, they share the same port without conflict.

## Task flow

```text
nextcloud.yml
  -> role: eurooffice (hosts: eurooffice)
      -> roles/eurooffice/tasks/main.yml
          -> collocated.yml (if same host as nextcloud)
          -> dedicated.yml  (if separate host)
  -> role: docker (task_from: compose_up.yml)
      -> starts eurooffice container
  -> role: nextcloud_app (hosts: nextcloud)
      -> roles/nextcloud_app/tasks/configure/eurooffice.yml
```
