# Nextcloud Office (Collabora) Role

Documentation for deploying Collabora Online with this playbook via the `nextcloudoffice` role and configuring integration in the `nextcloud` role.

## Overview

This setup uses two layers:

1. `roles/nextcloudoffice` adds a Collabora container (`collabora/code`) to the shared Docker Compose file.
2. `roles/nextcloud/tasks/configure/nextcloudoffice.yml` installs and configures the Nextcloud app (`richdocuments`) via `occ`.

## Role: `nextcloudoffice`

### What the role does

- Includes OS-specific package tasks:
  - Debian/Ubuntu: ensures apt components and installs fonts (`ttf-mscorefonts-installer`, `fonts-noto-core`)
  - RedHat-family: installs Noto fonts and helper packages
- Appends a `nextcloudoffice` service block to `/opt/nextcloud/docker_compose/compose.yml`
- Runs Collabora on loopback only:
  - `127.0.0.1:9980:9980`
- Configures container environment, including:
  - `aliasgroup1` based on `nextcloud_fqdn`
  - admin password from `passwords.collabora_admin`

### Inventory requirement

The role runs on hosts in inventory group `nextcloudoffice`.

Typical collocated setup:

```yaml
nextcloudoffice:
  hosts:
    nextcloud.example.com:
```

## Nextcloud role integration

When `nextcloud_install.nextcloudoffice` is enabled, the `nextcloud` role includes:

- `roles/nextcloud/tasks/configure/nextcloudoffice.yml`

This task file configures Nextcloud app integration using `occ`:

- `app:install richdocuments`
- `app:enable richdocuments`
- `config:app:set richdocuments wopi_url --value https://<nextcloud_fqdn>:<nextcloud_ssl_port>`
- `config:app:set richdocuments wopi_allowlist --value 127.0.0.1/8,::1/128,<docker-subnet>,fe80::/10`
- `config:app:set richdocuments disable_certificate_verification --value=yes`
- `richdocuments:activate-config`

## Required and relevant variables

From `group_vars/all/nextcloud.yml`:

- `nextcloud_install.nextcloudoffice` (feature toggle)
- `nextcloud_fqdn`

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
  -> role: docker (task_from: compose_up.yml)
      -> starts collabora container
  -> role: nextcloud (hosts: nextcloud)
      -> roles/nextcloud/tasks/configure/nextcloudoffice.yml
```

## Notes

- This role is intended for Collabora Online integration (Nextcloud Office app `richdocuments`).
- The role currently uses the `collabora/code:latest` image tag.
- For stable operations, pinning image versions can be considered in production environments.
