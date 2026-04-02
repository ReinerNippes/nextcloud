# Dynamic Cloud Inventories

When provisioning servers with [Pulumi](../cloud-stuff/README.md), you don't need to maintain static inventory files. Instead, Ansible can discover servers automatically using cloud provider inventory plugins. Servers are assigned to inventory groups based on **labels** (Hetzner) or **tags** (Scaleway) that Pulumi sets during provisioning.

## How It Works

1. **Pulumi creates servers** with metadata labels/tags like `group_nextcloud: true`, `group_redis: true`, etc.
2. **An `env` label** separates multiple deployments in the same cloud account (e.g. `env=debian13`, `env=production`).
3. **Ansible's inventory plugin** queries the cloud API, discovers servers, and maps labels/tags to inventory groups.
4. **No manual inventory editing** is required — adding or removing servers in Pulumi automatically updates the Ansible inventory.

## Hetzner Cloud

Uses the `hetzner.hcloud.hcloud` inventory plugin.

### Prerequisites

```bash
ansible-galaxy collection install hetzner.hcloud
export HCLOUD_TOKEN="your-hetzner-cloud-api-token"

# Or retrieve the token from a Pulumi stack:
export HCLOUD_TOKEN=$(cd cloud-stuff && pulumi config get hetzner:token --stack <your-stack>)
```

### Example Inventory File

```yaml
---
plugin: hetzner.hcloud.hcloud

# Only include servers belonging to this environment
label_selector: "env=<your-stack>"

# Use the server name as inventory hostname
hostname: "{{ hcloud_name }}"

# Map labels to Ansible groups
groups:
  nextcloud:       "hcloud_labels.group_nextcloud       | default('') == 'true'"
  redis:           "hcloud_labels.group_redis           | default('') == 'true'"
  database:        "hcloud_labels.group_database        | default('') == 'true'"
  webserver:       "hcloud_labels.group_webserver       | default('') == 'true'"
  docker:          "hcloud_labels.group_docker          | default('') == 'true'"
  elasticsearch:   "hcloud_labels.group_elasticsearch   | default('') == 'true'"
  coturn:          "hcloud_labels.group_coturn          | default('') == 'true'"
  signal:          "hcloud_labels.group_signal          | default('') == 'true'"
  hapr:            "hcloud_labels.group_hapr            | default('') == 'true'"
  nextcloudoffice: "hcloud_labels.group_nextcloudoffice | default('') == 'true'"
  onlyoffice:      "hcloud_labels.group_onlyoffice      | default('') == 'true'"

# Compose host variables from labels
compose:
  ansible_user: "'ansible'"
  ansible_ssh_private_key_file: "'~/.ssh/id_ed25519'"
  additional_fqdns: "hcloud_labels | dict2items | selectattr('key', 'match', '^additional_fqdn_') | items2dict"
  additional_certificate_fqdns: "additional_fqdns.values() | list"

connect_with: public_ipv4
```

The file must end in `.hcloud.yml` for Ansible to recognize it as a Hetzner Cloud inventory (e.g. `hetzner-inventory.production.hcloud.yml`).

### Usage

```bash
ansible-playbook -i hetzner-inventory.production.hcloud.yml nextcloud.yml
```

## Scaleway

Uses the `scaleway.scaleway.scaleway` inventory plugin.

### Prerequisites

```bash
ansible-galaxy collection install scaleway.scaleway
export SCW_ACCESS_KEY="your-access-key"
export SCW_SECRET_KEY="your-secret-key"

# Or retrieve from a Pulumi stack:
export SCW_ACCESS_KEY=$(cd cloud-stuff && pulumi config get scaleway:accessKey --stack <your-stack>)
export SCW_SECRET_KEY=$(cd cloud-stuff && pulumi config get scaleway:secretKey --stack <your-stack>)
```

### Example Inventory File

```yaml
---
plugin: scaleway.scaleway.scaleway

# Filter by tags
tags:
  - "env=<your-stack>"

regions:
  - fr-par-1

# Map tags to Ansible groups
groups:
  nextcloud:       "'group_nextcloud'       in tags"
  redis:           "'group_redis'           in tags"
  database:        "'group_database'        in tags"
  webserver:       "'group_webserver'       in tags"
  docker:          "'group_docker'          in tags"
  elasticsearch:   "'group_elasticsearch'   in tags"
  coturn:          "'group_coturn'          in tags"
  signal:          "'group_signal'          in tags"
  hapr:            "'group_hapr'            in tags"
  nextcloudoffice: "'group_nextcloudoffice' in tags"
  onlyoffice:      "'group_onlyoffice'      in tags"

compose:
  ansible_user: "'ansible'"
  ansible_ssh_private_key_file: "'~/.ssh/id_ed25519'"
```

> **Note:** The Scaleway dynamic inventory is not yet tested. The example above is based on the [scaleway.scaleway collection documentation](https://galaxy.ansible.com/ui/repo/published/scaleway/scaleway/) and may need adjustments.

### Usage

```bash
ansible-playbook -i scaleway-inventory.production.scaleway.yml nextcloud.yml
```

## Label / Tag Mapping

Pulumi sets the following metadata on each server automatically:

| Label / Tag | Purpose |
|------------|---------|
| `env=<stack>` | Environment selector — isolates multiple deployments |
| `group_nextcloud=true` | Assigns server to `nextcloud` group |
| `group_redis=true` | Assigns server to `redis` group |
| `group_database=true` | Assigns server to `database` group |
| `group_webserver=true` | Assigns server to `webserver` group |
| `group_docker=true` | Assigns server to `docker` group |
| `group_elasticsearch=true` | Assigns server to `elasticsearch` group |
| `group_coturn=true` | Assigns server to `coturn` group |
| `group_signal=true` | Assigns server to `signal` group |
| `group_hapr=true` | Assigns server to `hapr` group |
| `group_nextcloudoffice=true` | Assigns server to `nextcloudoffice` group |
| `group_onlyoffice=true` | Assigns server to `onlyoffice` group |
| `additional_fqdn_<name>=<fqdn>` | Additional FQDNs for webserver vhosts and TLS certificates |

A single server can have multiple group labels (e.g. a single-server setup has all groups on one host).
