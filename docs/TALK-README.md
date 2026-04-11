
# Talk and HPB Roles

Documentation for deploying Nextcloud Talk with this playbook, including the `coturn` role and the optional `signal` (HPB) role.

## Supported Platforms

- Debian / Ubuntu
- RHEL / AlmaLinux / Rocky Linux
- openSUSE Leap 16

## Architecture Overview

For Talk calls, this setup uses two backend components:

- `coturn` role: TURN/STUN relay for connectivity through NAT/firewalls
- `signal` role: Spreed signaling + Janus media backend (HPB)

### Sizing Recommendation

- Small environments (about 2-3 participants per call): often work fine with Talk + `coturn` only.
- Larger conferences or higher load: enable HPB (`signal`) for better scalability and media handling.

## What The Roles Do

### coturn role

- Installs and configures coturn on hosts in group `coturn`
- Generates TURN credentials used by Nextcloud Talk
- Exposes TURN/TLS endpoint used by clients for relay traffic

#### TURN/TLS port behavior

The playbook now sets the TURN/TLS port automatically via `coturn_tls_port`:

- Collocated setup (first `coturn` host equals first `nextcloud` host): `5349` (coturn default)
- Dedicated coturn server: `443`

If needed, you can override this in inventory or `group_vars`:

```yaml
all:
	vars:
		coturn_tls_port: 443
```

### signal role (optional)

- Installs Spreed signaling and Janus on hosts in group `signal`
- Configures webserver integration for signaling endpoints
- Integrates with Nextcloud Talk HPB configuration
- Requires a separate second server (do not run `signal` on the main Nextcloud host)

## Required Feature Toggles

Configure [group_vars/all/nextcloud.yml](group_vars/all/nextcloud.yml):

```yaml
nextcloud_install:
	talk: true
	hpb: true
```

If you want Talk without HPB (small setup), keep `talk: true` and set `hpb: false`.

## Inventory Layout

Minimum setup with TURN only:

```yaml
coturn:
	hosts:
		turn.example.com:
```

Collocated TURN setup (same host as Nextcloud):

```yaml
nextcloud:
	hosts:
		nextcloud.example.com:

coturn:
	hosts:
		nextcloud.example.com:
```

Setup with optional HPB signal server:

```yaml
coturn:
	hosts:
		turn.example.com:

signal:
	hosts:
		signal.example.com:

webserver:
	hosts:
		signal.example.com:

docker:
	hosts:
		signal.example.com:
```

The `signal` host should also be in `webserver` and `docker`, because HPB services and their reverse proxy are deployed there.
If HPB is enabled, this `signal` host must be a dedicated second server.

## Recording DNS/Certificate Special Case

When Talk recording is enabled, the recording endpoint needs its own DNS name and certificate SAN.

Use one of these inventory variables on the `signal` group:

- Preferred: `additional_fqdns.additional_fqdn_recording`
- Legacy-compatible: `additional_certificate_fqdns` (list)

Example:

```yaml
signal:
	vars:
		additional_fqdns:
			additional_fqdn_recording: rec.example.com
	hosts:
		signal.example.com:
```

Legacy example:

```yaml
signal:
	vars:
		additional_certificate_fqdns:
			- rec.example.com
	hosts:
		signal.example.com:
```

Ensure DNS `A/AAAA` records for `rec.example.com` point to the signal/recording endpoint so certificate issuance and HTTPS access work correctly.

## Task Flow (Talk/HPB Related)

```
roles/coturn/tasks/main.yml            TURN server installation and config
roles/signal/tasks/main.yml            HPB signaling and Janus deployment
roles/signal/tasks/config_nginx.yml    Signaling and recording vhost config
roles/nextcloud_app/tasks/configure/talk.yml  Nextcloud Talk app + TURN/HPB registration
```

## Summary

1. Enable Talk in [group_vars/all/nextcloud.yml](group_vars/all/nextcloud.yml).
2. Add at least one host to `coturn`.
3. Add `signal` only if you need HPB (recommended for larger conferences).
4. If `signal` is used, deploy it on a dedicated second server and also place that host in `webserver` and `docker`.
5. For recording, define an additional recording FQDN and corresponding DNS record.
