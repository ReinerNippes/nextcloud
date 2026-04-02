# TLS Certificate Role

Ansible role to provision TLS certificates for all servers in the Nextcloud deployment. Supports automated certificates via [acme.sh](https://github.com/acmesh-official/acme.sh) and self-signed certificates for testing or internal use.

## Supported Platforms

- Debian / Ubuntu
- RHEL / AlmaLinux / Rocky Linux

## Certificate Types

The role supports two modes, controlled by the `tls_certificate.type` variable:

### `acme.sh` — Let's Encrypt / ACME certificates (default)

1. Installs acme.sh to `/opt/acme.sh` with config in `/etc/acme.sh`
2. Issues an ECC (P-256) certificate using the appropriate challenge method:
   - **Webserver hosts**: Uses the running webserver (nginx or apache) for validation
   - **Non-webserver hosts** (coturn, redis, database): Uses standalone mode (port 80)
3. Deploys a systemd timer (`acme-sh.timer`) for weekly automatic renewal (Sundays at 01:17)
4. Automatically reloads affected services after issuance/renewal
5. Runs a post-hook (`fixperms.sh`) to set key permissions (`0640`) and ownership/group based on `tls_certificate_group`
6. If `setfacl` is available, the post-hook also grants read ACLs to existing `coturn`/`turnserver` users

### `selfsigned` — Self-signed certificates

1. **Generates a shared Root CA** on the Nextcloud source host (first host in `nextcloud` group, or current host if no nextcloud group):
   - CA private key: `root.ca.key`
   - CA certificate: `root.ca.crt`
2. **Distributes the shared Root CA** to all other servers executing the role:
   - Reads CA from source host via `slurp`
   - Writes CA to each server's certificate directory
3. **On each server**:
   - Creates a server private key and CSR
   - Signs the server certificate with the shared Root CA
   - Assembles a fullchain file (server cert + CA cert)
   - **Installs the CA in the system trust store**:
     - Debian/Ubuntu: `/usr/local/share/ca-certificates/`
     - RedHat/AlmaLinux/Rocky: `/etc/pki/ca-trust/source/anchors/`
   - Runs `update-ca-certificates` (Debian) or `update-ca-trust` (RedHat)

This means all servers in your deployment share the same Root CA, and all servers trust each other's certificates automatically.

Useful for development, internal networks, or when ACME is not available.

## Task Flow

```
tasks/main.yml
  ├── prepare_certs.yml          Create directories + deploy DH parameters (ffdhe4096)
  ├── acme_setup.yml             Install acme.sh (if tls_certificate.type == 'acme.sh')
  ├── acme.sh.yml                Issue certificate + deploy timer + reload services
  └── selfsigned.yml             Generate shared Root CA + distribute to all servers
                                 + generate per-server certs signed by shared CA
                                 + install CA in system trust store
```

## Variables

### User-defined variables (set in your inventory or `group_vars`)

These variables must be provided by the user:

| Variable | Required | Description |
|----------|----------|-------------|
| `tls_certificate.type` | yes | `acme.sh` or `selfsigned` |
| `tls_certificate.email` | for acme.sh | Email address for ACME account registration |
| `tls_certificate.acme_ca` | for acme.sh | ACME CA server URL (e.g. `https://acme-v02.api.letsencrypt.org/directory` or `https://acme.zerossl.com/v2/DV90` or a staging URL ending in `test`) |
| `additional_certificate_fqdns` | no | List of additional domain names (SANs) to include in the certificate |

### Variables in `common.yml`

These variables are defined in `group_vars/all/common.yml` and provide sensible defaults. Override them only if you need custom behavior.

#### Certificate paths

| Variable | Default | Description |
|----------|---------|-------------|
| `tls_certificate_directory` | `/etc/ssl/private` (Debian) or `/etc/pki/tls/private` (RedHat) | Base directory for certificates |
| `tls_certificate_common_name` | `{{ inventory_hostname }}` | Common name (CN) for the certificate |
| `tls_certificate_key_length` | `ec-256` | Key type and length (ECC P-256) |
| `tls_certificate_file` | `<dir>/<cn>_ecc/<cn>.cer` | Path to the server certificate |
| `tls_certificate_key` | `<dir>/<cn>_ecc/<cn>.key` | Path to the private key |
| `tls_certificate_fullchain` | `<dir>/<cn>_ecc/fullchain.cer` | Path to the fullchain certificate |
| `tls_certificate_csr` | `<dir>/<cn>_ecc/<cn>.csr` | Path to the CSR |
| `tls_certificate_ca` | `<dir>/<cn>_ecc/ca.cer` | Path to the CA certificate |

#### Ownership and permissions

| Variable | Default | Description |
|----------|---------|-------------|
| `tls_certificate_owner` | `root` | File owner for certificate files |
| `tls_certificate_group` | `ssl-cert` | File group for certificate files |

#### Service reload mapping

| Variable | Default | Description |
|----------|---------|-------------|
| `tls_service_map.webserver` | Derived from `webserver_service_name` | Systemd service to reload for webserver hosts |
| `tls_service_map.coturn` | `coturn.service` | Systemd service to reload for coturn hosts |
| `tls_service_map.redis` | Derived from `redis_service_name` | Systemd service to reload for standalone redis hosts |
| `tls_service_map.database` | `mariadb` or PostgreSQL service | Systemd service to reload for standalone database hosts |

The role automatically determines which services to reload based on the host's group membership in the inventory. Services are only reloaded on hosts that actually run them.

Docker containers with bind-mounted certificates (e.g. OnlyOffice) are restarted via `docker restart` after renewal, since they re-read certificates only on startup.

#### Staging detection

| Variable | Default | Description |
|----------|---------|-------------|
| `tls_certificate_test` | Auto-detected | `true` if `tls_certificate.acme_ca` URL ends with `test` (staging environment) |

#### Self-signed CA distribution

| Variable | Default | Description |
|----------|---------|-------------|
| `tls_selfsigned_ca_source_host` | First host in `nextcloud` group, or `inventory_hostname` | Host on which the shared Root CA is generated and read from |

When using `selfsigned` mode, the role automatically distributes the Root CA from the source host to all other servers. This creates a unified trust domain where all servers trust each other's certificates.

## Self-Signed CA Installation Details

When using `selfsigned` mode, the shared Root CA is installed in the **system certificate store** on all servers. This allows:

- Server-to-server TLS connections (e.g., Nextcloud → OnlyOffice) to use HTTPS without certificate warnings
- Docker containers on each host to validate certificates from other servers
- Command-line tools (`curl`, `wget`, etc.) to trust all certificates in the deployment

The CA is installed automatically into:

- Debian/Ubuntu: `/usr/local/share/ca-certificates/`
- RedHat/AlmaLinux/Rocky: `/etc/pki/ca-trust/source/anchors/`

And then the system command is run to refresh the trusted CA store:

- Debian/Ubuntu: `update-ca-certificates`
- RedHat/AlmaLinux/Rocky: `update-ca-trust extract`

## Files Managed on Disk

### acme.sh mode

```
/opt/acme.sh/                              acme.sh installation
/etc/acme.sh/                              acme.sh config, account key, account.conf
/etc/acme.sh/deploy/fixperms.sh            Post-hook script (all supported platforms)
<tls_certificate_directory>/<cn>_ecc/      Certificate files (cer, key, fullchain, csr, ca)
<tls_certificate_directory>/dhparam.pem    Pre-defined DH parameters (ffdhe4096, RFC 7919)
/etc/systemd/system/acme-sh.service        Renewal service unit
/etc/systemd/system/acme-sh.timer          Weekly renewal timer
```

### Self-signed mode

On the **source host** (first Nextcloud host):

```
<tls_certificate_directory>/root.ca.key        Shared Root CA private key
<tls_certificate_directory>/root.ca.csr        Shared Root CA CSR
```

On **all servers** executing the role:

```
<tls_certificate_directory>/                   Base certificate directory
  ├── root.ca.key                              Shared Root CA private key (copied from source)
  ├── root.ca.csr                              Shared Root CA CSR (not used locally)
  ├── <cn>_ecc/                                Per-server certificate files
  │   ├── <cn>.cer                             Server certificate
  │   ├── <cn>.key                             Server private key
  │   ├── <cn>.csr                             Server CSR
  │   └── ca.cer                               Shared Root CA certificate
  └── dhparam.pem                              Pre-defined DH parameters (ffdhe4096, RFC 7919)

/usr/local/share/ca-certificates/              (Debian/Ubuntu - system CA store)
  └── <cn>-local-ca.crt                        Shared Root CA installed in trust store

/etc/pki/ca-trust/source/anchors/              (RedHat/AlmaLinux/Rocky - system CA store)
  └── <cn>-local-ca.crt                        Shared Root CA installed in trust store
```

## Automatic Renewal (acme.sh)

A systemd timer runs weekly:

- **Timer**: `acme-sh.timer` — fires every Sunday at 01:17
- **Service**: `acme-sh.service` — runs `acme.sh --upgrade --home /opt/acme.sh --config-home /etc/acme.sh` then `acme.sh --cron --home /opt/acme.sh --config-home /etc/acme.sh`

acme.sh internally tracks certificate expiry and only renews when needed (default: 60 days before expiry). After successful renewal, the configured `--reloadcmd` restarts the affected services and the `--post-hook` fixes file permissions.

The `fixperms.sh` hook is deployed on all supported platforms and receives `CERT_GROUP` from Ansible (`tls_certificate_group`).

## Platform Differences

| Aspect | Debian / Ubuntu | RedHat / Alma / Rocky |
|--------|-----------------|----------------------|
| Certificate base directory | `/etc/ssl/private` | `/etc/pki/tls/private` |
| Key file group | `ssl-cert` | `ssl-cert` |
| Post-hook (fixperms.sh) | Deployed and used | Deployed and used |
| Webserver validation | nginx or apache | nginx or apache |

## Example Configuration

### ACME (Let's Encrypt) setup

```yaml
# group_vars/all/nextcloud.yml or host_vars
tls_certificate:
  type: "acme.sh"
  email: "admin@example.com"
  acme_ca: "letsencrypt"

# Optional: additional SANs
additional_certificate_fqdns:
  - "cloud.example.com"
  - "office.example.com"
```

### Self-signed setup example

With self-signed certificates, suppose you have this inventory:

```yaml
nextcloud:
  hosts:
    nextcloud.example.com:

onlyoffice:
  hosts:
    onlyoffice.example.com:

coturn:
  hosts:
    turn.example.com:
```

When the playbook runs with `tls_certificate.type: selfsigned`:

1. Root CA is generated on `nextcloud.example.com` (first Nextcloud host)
2. Root CA is distributed to `onlyoffice.example.com` and `turn.example.com`
3. Each host generates its own server certificate signed with the shared Root CA
4. The Root CA is installed in the system trust store on all three hosts
5. All three servers can now communicate via HTTPS without certificate warnings

Configuration:

```yaml
tls_certificate:
  type: "selfsigned"

# Optional: additional SANs (e.g., for OnlyOffice recording endpoint)
additional_certificate_fqdns:
  - "rec.example.com"
```
