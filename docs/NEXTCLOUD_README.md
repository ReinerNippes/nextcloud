# Nextcloud Roles

Ansible roles to download, install, and configure Nextcloud including webserver, database, and optional components.

The former monolithic `nextcloud` role has been split into three focused roles:

| Role | Purpose |
|------|---------|
| `nextcloud_prepare` | OS preparation, database creation, webserver configuration, SELinux |
| `nextcloud_install` | Nextcloud download, installation, core configuration (mail, logging, preview) |
| `nextcloud_app` | App installation and add-on configuration (Talk, Office, Fulltextsearch, etc.) |

All `occ` interactions now use the [`reinernippes.nextcloud` Ansible collection](OCC-MODULES-README.md) instead of raw `command: php occ` calls.

## Supported Platforms

- Debian / Ubuntu
- RHEL / AlmaLinux / Rocky Linux
- openSUSE Leap 16

## What These Roles Do

### `nextcloud_prepare`

1. **OS preparation** — Installs packages (ffmpeg, imagemagick, ghostscript, etc.) and configures ImageMagick policies
2. **Database creation** — Creates the Nextcloud database and user (MySQL/MariaDB or PostgreSQL)
3. **Webserver configuration** — Deploys nginx or Apache vhost with TLS, HTTP/2, and security headers
4. **SELinux** — Configures contexts, booleans, and custom policy modules (RedHat only)

### `nextcloud_install`

5. **Nextcloud installation** — Downloads and extracts the Nextcloud archive, runs `occ maintenance:install`
6. **Core configuration** — Sets `config.php` values via collection modules, configures mail, logging, preview providers
7. **Cron** — Sets up the Nextcloud cron job

### `nextcloud_app`

8. **App management** — Installs and enables apps via `reinernippes.nextcloud.occ_app`
9. **Optional components** — Talk, HPB, Collabora Office, OnlyOffice, Whiteboard, Fulltextsearch, ExApps/HaPR, Notify Push

## Task Flow

### `nextcloud_prepare`

```
roles/nextcloud_prepare/tasks/main.yml
  ├── os/main.yml                     OS packages, ImageMagick, data directories
  │   ├── os/Debian.yml               apt packages
  │   ├── os/RedHat.yml               dnf packages
  │   └── os/Suse.yml                 zypper packages
  ├── database/create_mysql.yml       Create MySQL/MariaDB database + user
  │   or database/create_pgsql.yml    Create PostgreSQL database + user
  ├── webserver/nginx.yml             nginx config (nginx.conf, http.conf, nextcloud.conf)
  │   or webserver/apache.yml         Apache config (vhosts, mods, security)
  │       ├── apache_Debian.yml
  │       ├── apache_RedHat.yml
  │       └── apache_Suse.yml
  └── selinux.yml                     SELinux contexts + booleans (RedHat only)
```

### `nextcloud_install`

```
roles/nextcloud_install/tasks/main.yml
  ├── [download + extract Nextcloud]
  ├── configure/nextcloud.yml         First setup, config.php, trusted domains
  ├── configure/mail.yml              Mail/SMTP configuration
  ├── configure/logging.yml           Log file + audit log setup
  ├── configure/preview.yml           Preview provider configuration
  └── [cron job setup]
```

### `nextcloud_app`

```
roles/nextcloud_app/tasks/main.yml
  ├── [Install apps via occ_app]      Bulk app install/enable
  ├── configure/fulltextsearch.yml    Elasticsearch integration (optional)
  ├── configure/nextcloudoffice.yml   Collabora Online / richdocuments (optional)
  ├── configure/onlyoffice.yml        OnlyOffice integration (optional)
  ├── configure/whiteboard.yml        Whiteboard WebSocket config (optional)
  ├── configure/talk.yml              Talk + HPB signaling (optional)
  ├── configure/exapp_hapr.yml        ExApps with HaPR daemon (optional)
  └── configure/notify_push.yml       Push notifications daemon (optional)
```

## Variables

### Main Variables (`group_vars/all/nextcloud.yml`)

| Variable | Default | Description |
|----------|---------|-------------|
| `nextcloud_fqdn` | `inventory_hostname` of first nextcloud host | Server domain name |
| `tls_certificate.type` | `selfsigned` | Certificate type: `selfsigned` or `acme.sh` |
| `tls_certificate.email` | — | Email for ACME registration (required for `acme.sh`) |
| `tls_certificate.acme_ca` | — | ACME CA: `zerossl`, `letsencrypt`, `letsencrypt_test` |
| `nextcloud_www_dir` | `/var/www/nextcloud` | Nextcloud web root directory |
| `nextcloud_data_dir` | `/var/nc-data` | Nextcloud data directory |
| `nextcloud_admin` | `admin` | Nextcloud admin username |
| `nextcloud_passwd` | `''` (auto-generated) | Admin password (leave empty for random) |
| `nextcloud_archive` | `https://download.nextcloud.com/.../latest.tar.bz2` | Nextcloud download URL |
| `nextcloud_default_phone_region` | `DE` | Default region for phone numbers (ISO 3166-1) |
| `onlyoffice_fqdn` | First host in `onlyoffice` group | OnlyOffice server domain name |
| `nextcloudoffice_fqdn` | First host in `nextcloudoffice` group | Collabora Online server domain name |

### Feature Toggles (`nextcloud_install`)

| Key | Default | Description |
|-----|---------|-------------|
| `nextcloud_install.preview` | `true` | Preview icon generation |
| `nextcloud_install.notify_push` | `true` | Client push notification daemon |
| `nextcloud_install.talk` | `false` | Nextcloud Talk (video/audio calls) |
| `nextcloud_install.hpb` | `false` | High Performance Backend for Talk |
| `nextcloud_install.hapr` | `false` | HaPR reverse proxy for ExApps |
| `nextcloud_install.nextcloudoffice` | `false` | Collabora Online (richdocuments) |
| `nextcloud_install.onlyoffice` | `false` | OnlyOffice document server |
| `nextcloud_install.whiteboard` | `false` | Excalidraw-based collaborative whiteboard |
| `nextcloud_install.fulltextsearch` | `false` | Elasticsearch-based full text search |

### S3 Backend (`group_vars/all/s3_backend.yml`)

S3 can be used as primary storage. Leave `objectstore_s3_key` empty to disable.

| Variable | Default | Description |
|----------|---------|-------------|
| `objectstore_s3_key` | `''` | S3 access key (empty = disabled) |
| `objectstore_s3_secret` | `''` | S3 secret key |
| `objectstore_s3_bucket_name` | `nextcloud-<fqdn>` | Bucket name |
| `objectstore_s3_hostname` | `s3.amazonaws.com` | S3 endpoint |
| `objectstore_s3_port` | `443` | S3 port |
| `objectstore_s3_use_ssl` | `true` | Use SSL for S3 |
| `objectstore_s3_region` | `us-east-1` | S3 region |
| `objectstore_s3_use_path_style` | `true` | Path-style access (required for MinIO etc.) |

### Logging

| Variable | Default | Description |
|----------|---------|-------------|
| `nextcloud_logging_level` | `2` | Log level (0=debug, 1=info, 2=warning, 3=error, 4=fatal) |
| `nextcloud_logging_rotate_size` | `104857600` (100 MB) | Log rotation threshold in bytes |
| `nextcloud_logging_rotate_keep` | `10` | Number of rotated log files to keep |

Log files are written to `/var/log/nextcloud/`:
- `nextcloud.log` — Application log
- `audit.log` — Admin audit log

### Nextcloud Configuration Defaults (`defaults/main.yml`)

The role applies a set of `config.php` values via `occ config:system:set`. Key settings include:

| Setting | Value | Notes |
|---------|-------|-------|
| Redis cache | Socket (local) or TCP (remote) | Based on inventory grouping |
| `memcache.local` | APCu | |
| `memcache.locking` | Redis | |
| File previews | Enabled | PNG, JPEG, GIF, PDF, Office formats, etc. |
| `auth.bruteforce.protection.enabled` | `true` | |
| `trashbin_retention_obligation` | `auto,7` | Automatic cleanup, max 7 days |
| `skeletondirectory` | `''` (empty) | No default files for new users |
| `activity_expire_days` | `14` | |
| `updater.release.channel` | `stable` | |

### Mail Configuration

Mail is configured when `nextcloud_mail.configure` is `true`. Set values in your inventory or `group_vars`:

| Variable | Description |
|----------|-------------|
| `nextcloud_mail.from` | Sender address |
| `nextcloud_mail.domain` | Mail domain |
| `nextcloud_mail.smtpmode` | SMTP mode |
| `nextcloud_mail.smtphost` | SMTP server |
| `nextcloud_mail.smtpport` | SMTP port |
| `nextcloud_mail.smtpsecure` | Encryption (`ssl`, `tls`) |
| `nextcloud_mail.smtpauth` | Auth enabled (`1` or `0`) |
| `nextcloud_mail.smtpauthtype` | Auth type (e.g. `LOGIN`) |
| `nextcloud_mail.smtpname` | SMTP username |
| `nextcloud_mail.smtppwd` | SMTP password |

## Webserver Configuration

### nginx

Three config files are deployed:

| Template | Target | Purpose |
|----------|--------|---------|
| `nginx.conf.j2` | `/etc/nginx/nginx.conf` | Main config (workers, logging, SSL early data) |
| `http.conf.j2` | `/etc/nginx/conf.d/http.conf` | HTTP→HTTPS redirect, ACME challenge, PHP upstream |
| `nextcloud.conf.j2` | `/etc/nginx/conf.d/nextcloud.conf` | HTTPS vhost with TLS, security headers, fastcgi |

### Apache

- Enables required modules (proxy_fcgi, rewrite, headers, ssl, etc.)
- Deploys vhost with SSL, HSTS, and PHP-FPM proxy
- On Debian: uses `sites-available/sites-enabled` pattern, removes default vhost
- On RedHat: deploys `php.conf` and vhost in `conf.d/`
- On openSUSE: uses `a2enmod` for module management, `apache2-event` MPM

### Port Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `nextcloud_web_port` | `80` | HTTP port (redirect to HTTPS) |
| `nextcloud_ssl_port` | `443` | HTTPS port |

## Database

The role creates the database and user on the first run. Supported types:

### MySQL / MariaDB

Creates database with `utf8mb4` encoding and grants all privileges to the Nextcloud user.

### PostgreSQL

Creates database with `UTF-8` encoding, user, and grants `ALL` on schema `public` including default privileges on tables.

Database settings are configured separately — see `group_vars/all/database.yml`.

## Optional Components

### Nextcloud Talk

Installs the `spreed` app and configures STUN/TURN servers using the coturn host from inventory. When `nextcloud_install.hpb` is enabled, also configures the High Performance Backend signaling server.

TURN/TLS uses `coturn_tls_port`, which is selected automatically:
- `5349` when coturn is collocated on the Nextcloud host
- `443` when coturn runs on a dedicated server

Why this matters:
- In many corporate, school, or guest networks, outbound traffic is heavily restricted and often only ports like 443 are allowed.
- TURN over 443 (TCP/UDP) therefore improves call reliability for participants behind restrictive firewalls or proxies.
- In collocated setups, port 443 is usually already occupied by the webserver (nginx/apache), so coturn stays on 5349 by default.

### Collabora Online (Nextcloud Office)

Installs the `richdocuments` app and configures the WOPI URL pointing to the local Collabora container.

### Fulltextsearch

Installs and configures three apps:
- `fulltextsearch`
- `fulltextsearch_elasticsearch`
- `files_fulltextsearch`

Connects to a local Elasticsearch instance at `http://localhost:9200`.

### ExApps with HaPR

Installs the `app_api` app and registers the HaPR (HaProxy Reverse Proxy) deploy daemon for Docker-based external applications.

### Whiteboard

Installs and configures the Excalidraw-based collaborative whiteboard app. The whiteboard WebSocket server runs as a Docker container and can be deployed collocated with Nextcloud or on a dedicated server. See [WHITEBOARD-README.md](WHITEBOARD-README.md) for details (if available).

### Notify Push

Deploys a systemd service (`notify_push.service`) that runs the push daemon for real-time client notifications. Listens on port 7867 and connects to the local Nextcloud instance.

## SELinux (RedHat only)

When SELinux is enabled, the role:

- Sets `httpd_sys_rw_content_t` context on data, config, and app directories
- Enables necessary SELinux booleans (network connect, sendmail, etc.)
- Loads custom policy modules for PHP-FPM socket access, Redis socket access, and upload temp directory

## Files Managed on Disk

```
/var/www/nextcloud/                         Nextcloud web root
/var/nc-data/                               Nextcloud data directory
/var/log/nextcloud/nextcloud.log            Application log
/var/log/nextcloud/audit.log                Audit log

# nginx
/etc/nginx/nginx.conf
/etc/nginx/conf.d/http.conf
/etc/nginx/conf.d/default.conf
/etc/nginx/conf.d/nextcloud.conf            (only when nginx selected)

# Apache (Debian)
/etc/apache2/ports.conf
/etc/apache2/sites-available/nextcloud.conf
/etc/apache2/sites-enabled/nextcloud.conf   (symlink)

# Apache (RedHat)
/etc/httpd/conf.d/php.conf
/etc/httpd/conf.d/nextcloud.conf

# Systemd services
notify_push.service                         (when notify_push enabled)

# Cron
*/5 * * * * php -f /var/www/nextcloud/cron.php
```

## `force_nextcloud_config`

Set `force_nextcloud_config: true` to re-apply all Nextcloud configuration values (config.php, mail, apps, database tuning) on subsequent runs. By default, configuration is only applied during the initial setup.

```bash
ansible-playbook nextcloud.yml -e "force_nextcloud_config=true"
```
