
# ☁️ Nextcloud AIO BIB (All in One, But in Big))

Pulumi Code and Ansible Playbook to deploy:

* Nextcloud (Latest) - <https://nextcloud.com/>
* nginx - <https://nginx.org/> or Apache <https://httpd.apache.org/>
* PHP - <http://www.php.net/>
* MariaDB - <https://mariadb.org/> or PostgreSQL <https://www.postgresql.org/>
* redis - <https://redis.io/> (valkey on RedHat based Systems)
* restic backup - <https://restic.readthedocs.io>
* Nextcloud Talk with HPB
* Nextcloud AppAPI Basis (HaPR Daemon)
* Fulltextsearch / Elasticsearch
* OnlyOffice <https://www.onlyoffice.com/>
* Collabora Online <https://www.collaboraoffice.com/>

Ready to login in less than 20 minutes.

Most of the settings are recommendations from the following web page: <https://docs.nextcloud.com/server/latest/admin_manual/>, <https://www.c-rieger.de/>, <https://decatec.de/home-server/> or <https://www.hanssonit.se/>

## Requirements

You can set up your own server manually or provision cloud infrastructure
automatically using Pulumi. See [cloud-stuff/README.md](cloud-stuff/README.md)
for tested providers (Hetzner, Scaleway, …) and configuration details.

Testet Linux Flavours:

- Ubuntu 24.04
- Debian 12/13 
- CentOS 10
- AlmaLinux 10
- RockyLinux 10 

> ⚠️ **WARNING**: Your existing setup will be overwritten. It's strongly recommendet to only run this playbook on fresh installed instances.

> ⚠️ **WARNING**: This playbook is not compatible with previous versions of this repo. Do not run this version on older installations.

> ⚠️ **WARNING**: This is work in progress. Not all combinations are tested. Some don't work yet.

### Server Topology (Current Scope)

- Minimum setup for this playbook: at least one server for the Nextcloud application stack (`nextcloud`, `webserver`, typically also `database`/`redis` in collocated mode).
- For productive Talk deployments, you should additionally provide dedicated servers for:
  - `coturn`
  - `signal` (signaling/recording)
- `onlyoffice` can be provided on an additional dedicated server (status: see table below).
- Current limitation: no full HA setup (high-availability cluster) is supported/provisioned at this time.

### Tested Combinations

✅ = works  &nbsp;&nbsp; 🟡 = not tested (yet) &nbsp;&nbsp; 🔒 = works only with LE certs &nbsp;&nbsp; ❌ = not working / not yet implemented

| Feature | Ubuntu 24.04 | Debian 12 | Debian 13 | AlmaLinux 10 | Rocky 10 | CentOS10 |
|---------|:---:|:---:|:---:|:---:|:---:|:---:|
| PostgreSQL | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| MariaDB | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| nginx | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| Apache | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| acme.sh (Let's Encrypt) | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| Self-signed Certificate | ✅ | ✅ | ✅ | ✅ | ✅ | 🟡 |
| Talk (nginx) | ✅ | ✅ | ✅ | ✅ | ✅ | 🟡 |
| Talk (Apache) | 🟡 | 🟡 | ✅ | ✅ | ✅ | ✅ |
| Talk HPB (nginx) | 🔒 | 🔒 | 🔒 | 🔒 | 🔒 | 🟡 |
| Talk HPB (Apache) | 🟡 | 🟡 | 🔒 | 🟡 | 🟡 | 🔒 |
| Nextcloud Office (nginx) | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| Nextcloud Office (Apache) | 🟡 | 🟡 | ✅ | 🟡 | ✅ | ✅ |
| OnlyOffice | 🟡 | 🟡 | ✅ | 🟡 | ✅ | ✅ |
| Fulltextsearch | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| ExApps (HaPR) | 🔒 | 🔒 | 🔒 | 🟡 | 🔒 | 🔒 |
| Notify Push | ✅ | ✅ | ✅ | 🟡 | ✅ | ✅ |
| S3 Primary Storage | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ |
| Whiteboard | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ |
| CrowdSec | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ |
| SMTP Relayserver | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ |

### Dedicated Server Offloading Status

| Component | Collocation | Dedicated Server | Notes |
|-----------|:---:|:---:|-------|
| Coturn | ✅ | ✅ | Recommended for external Talk participants behind restrictive firewalls |
| Signaling / Recording | ❌ | ✅ | Recommended for HPB setups |
| OnlyOffice | ✅ | ✅ | Technically possible, currently not fully tested in matrix |
| Database (PostgreSQL/MariaDB) | ✅ | 🟡 | Work in progress |
| Redis | ✅ | 🟡 | Work in progress |


> **Note:** My personal setup and most of my testing is done with Debian/Ubuntu, nginx, and PostgreSQL. This does not mean these are the recommended choices — it simply means other combinations may receive less testing. This is a hobby project. I provide no guarantees of any kind. Use at your own risk.

## 📘 Usage

### How to install Ansible and required collections

You can install Ansible in two ways:

1. **Control Host Setup:**
	- Install Ansible on a separate control host (your laptop, a management VM, etc.).
	- The playbook is executed from the control host and connects via SSH to the managed node (the server where Nextcloud will be installed).
	- This is the recommended and most common setup for managing multiple servers.

2. **Direct Installation on Managed Node:**
	- Alternatively, you can install Ansible directly on the server where you want to install Nextcloud.
	- In this case, the playbook runs locally on the same machine (localhost).


**Installation steps:**

*For Ubuntu/Debian ≤ 12:*

```bash
sudo apt update
sudo apt install -y python3-pip
pip3 install --user ansible-core
export PATH="$HOME/.local/bin:$PATH"
ansible --version
```

*For Debian 13 (recommended for compatibility):*

```bash
sudo apt update
sudo apt install -y python3-venv python3-pip
python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install ansible-core
ansible --version
```

You must always activate the virtual environment (`source .venv/bin/activate`) before running Ansible commands.

**Install required Ansible collections:**

If a `requirements.yml` file is present (as in this repository), run:

```bash
ansible-galaxy collection install -r requirements.yml
```

To list installed collections:

```bash
ansible-galaxy collection list
```

### Prepare the Nextcloud Servers

#### Setting up the Nextcloud Server User

Before running the playbook, you must ensure that the target server(s) are accessible and that a user with the necessary privileges exists:

**For remote installations:**

- Create a dedicated user (e.g., `ansible`) on the managed node (the server where Nextcloud will be installed).
- The user running the playbook must have passwordless `sudo` rights on the remote machine, or provide the sudo password using the appropriate Ansible variable (e.g., `ansible_become_password`).
- The user must be able to log in via SSH from the control host. Set up SSH key authentication for secure, passwordless access.

Example (run as root or with sudo on the managed node):

```bash
adduser ansible
usermod -aG sudo ansible
# Configure passwordless sudo for the user (edit /etc/sudoers or add a file in /etc/sudoers.d/)
echo 'ansible ALL=(ALL) NOPASSWD:ALL' | sudo tee /etc/sudoers.d/ansible
# Set up SSH key authentication (from control host):
ssh-copy-id ansible@your-server
```

**For local installations:**

- The user running the playbook must have passwordless `sudo` rights on the local machine, or provide the sudo password using the appropriate Ansible variable (e.g., `ansible_become_password`).
- When the variable `ansible_connection:` is set to `local`, no ssh connection needs to be setup.

**SSH Connection Configuration:**

You can customize the SSH connection settings in your inventory or via Ansible configuration. For more details, see the official documentation:
https://docs.ansible.com/projects/ansible/latest/collections/ansible/builtin/ssh_connection.html


#### Using and Adapting the Inventory

To get started, copy one of the example inventory files to a new file named `inventory` in the project root and adapt it to your environment:

- [inventory-localhost](inventory-localhost) (for local installations)
- [inventory-remote-single-server](inventory-remote-single-server) (for single remote server)
- [inventory-remote-multi-server](inventory-remote-multi-server) (for multi-tier setups)

For cloud deployments provisioned with Pulumi, use dynamic inventories instead of static files. See [Dynamic Cloud Inventories](docs/DYNAMIC-INVENTORY-README.md) for details on Hetzner and Scaleway.

> ⚠️ **Note**: Each playbook run deploys exactly **one** Nextcloud environment. If you place more than one server in a group like `nextcloud`, `database`, `redis`, `signal`, etc., this will be interpreted as a load-balanced / HA cluster in future versions. This is **not yet supported**. (This limitation does not apply to the `docker` and `webserver` groups.) 

> 💡 **Tip**: For mass deployments of multiple environments (e.g. cross-distribution testing), take a look at [cloud-stuff/test_matrix.sh](cloud-stuff/test_matrix.sh). It automates `pulumi up`, playbook runs, and `pulumi destroy` per stack. For persistent environments, remove the final `pulumi destroy` step.

Example:

```bash
cp inventory-remote-single-server inventory
# Edit the 'inventory' file to match your server hostnames and configuration
```

Alternatively, you can set the inventory file path directly in the Ansible configuration. In this repository, the default inventory file is set in [ansible.cfg](ansible.cfg) (see line 2):

```
[defaults]
inventory = inventory-remote-single-server
```

You can change this path to point to any inventory file you want to use.

### Controlling the Installation with Variables

The behavior and configuration of the playbook are controlled by variables defined in the files under [group_vars/all/](group_vars/all/). The directory uses two types of files to separate user configuration from internal defaults:

| Type | Example | Purpose |
|------|---------|---------|
| `*.yml` (top-level files) | `database.yml`, `nextcloud.yml`, `php.yml` | **User variables** — settings you are expected to review and customize |
| `<folder>/main.yml` | `database/main.yml`, `redis/main.yml`, `webserver/main.yml` | **Internal variables** — platform-specific paths, package names, service mappings |

This mirrors the separation Ansible provides between `defaults/` (low-priority, meant to be overridden) and `vars/` (high-priority, set by the role author). The top-level `*.yml` files are the equivalent of role defaults — your knobs to turn. The `<folder>/main.yml` files are the equivalent of role vars — values that normally don't need to be changed.

```
group_vars/all/
  ├── nextcloud.yml          ← user config: FQDN, admin user, enabled components
  ├── database.yml           ← user config: DB type, version, tuning parameters
  ├── database/main.yml      ← internal: package names, paths, socket locations
  ├── php.yml                ← user config: PHP version, memory limits
  ├── redis/main.yml         ← internal: package names, service names per OS
  ├── webserver/main.yml     ← internal: service names, paths per OS
  ├── backup.yml             ← user config: restic backup settings
  ├── mail.yml               ← user config: SMTP settings
  ├── s3_backend.yml         ← user config: S3 primary storage
  └── common.yml             ← shared variables (password store, TLS paths, service maps)
```

To customize your installation:

1. Open the relevant `*.yml` file in [group_vars/all/](group_vars/all/) (e.g., [group_vars/all/nextcloud.yml](group_vars/all/nextcloud.yml), [group_vars/all/database.yml](group_vars/all/database.yml), etc.).
2. Adjust the variables according to your requirements. Each file is documented with comments to help you understand the available options.
3. Save your changes before running the playbook.

> **Note:** You should normally not need to edit the `<folder>/main.yml` files unless you are adapting the playbook to an unsupported platform or have very specific requirements.

These variables allow you to control:
- Nextcloud configuration (admin user, trusted domains, etc.)
- Database settings (type, credentials, host)
- Mail server configuration
- Backup options
- PHP settings
- S3 backend and storage
- And more

You can also override variables in your inventory file or via the command line using `-e` if needed.


### Running the Playbook

Once you have installed Ansible, set up your inventory, and configured the variables, you can run the playbook to start the installation.

**Basic command:**

```bash
ansible-playbook nextcloud.yml
```

If you are using a custom inventory file, specify it with the `-i` option:

```bash
ansible-playbook -i inventory-remote-single-server nextcloud.yml
```

If you are using a Python virtual environment (recommended), make sure to activate it first:

```bash
source .venv/bin/activate
ansible-playbook nextcloud.yml
```

You can also pass extra variables on the command line using `-e`:

```bash
ansible-playbook -i inventory nextcloud.yml -e "nextcloud_admin_password=YourSecretPassword"
```

For more options, see the [Ansible documentation](https://docs.ansible.com/ansible/latest/cli/ansible-playbook.html).

If everything is going according to plan the playbook will finish with the following message:

```
TASK [We are ready] ***************************************************************************************************************************
ok: [nextcloud.example.com] => {
    "changed": false,
    "msg": [
        "Your Nextcloud 33.0.0.16 at https://nextcloud.example.com is ready.",
        "Login with user: admin and password: G9u6dfTQCR2vvExZqSY80TX3xLJsG1he",
        "Other secrets you'll find in the /opt/nextcloud/password_file.yml."
    ]
}

```

Login to your nextcloud web site <https://nextcloud.example.com>

Users and passwords have been set according to the entries in the inventory if defined there. Otherwise the admin password will be displayed at the end of playbook. Additionally you can find them in the credential_store = /opt/nextcloud

> **⚠️ Security Notice:** The playbook log output contains sensitive data such as passwords and API tokens. If you use AAP, AWX, or any external logging aggregator, make sure logs are stored securely and access is restricted.

### Nextcloud Talk and High Performance Backend (HPB)

For detailed instructions on how to install and configure Nextcloud Talk and the High Performance Backend (HPB) with this playbook using the  [inventory-remote-multi-server](inventory-remote-multi-server), see:

When HPB is enabled, the `signal` role must run on a dedicated second server (separate from the main Nextcloud host).

- [TALK.md: Installing Nextcloud Talk and HPB](docs/TALK-README.md)

---------------

## 🔧 Tuning

This project includes two dedicated analyzer roles — one for PHP‑FPM and one for PostgreSQL — to help you tune a Nextcloud installation based on real system behavior. These analyzers are used in two different contexts:

### Initial Analysis (nextcloud.yml)

At the end of the main installation playbook [nextcloud](nextclould.yml), both analyzers run once to provide an overview of the system state immediately after installation.

This gives you a baseline understanding of:
- 	how PHP‑FPM is configured and how much memory its workers consume
- 	how PostgreSQL is configured and how it allocates resources
- 	whether the system appears balanced right after deployment

However, this initial analysis does not reflect real‑world load. It simply shows the configuration and memory footprint at rest.

### Performance Tuning Under Load 

For meaningful tuning, you should run the dedicated performance tuning playbook: [nextcloud-performance-tuning](nextcloud-performance-tuning.yml)

This playbook is designed to be executed after the system has been in use, ideally under realistic or peak load.
It collects live metrics from PHP‑FPM and PostgreSQL, evaluates memory usage, and generates hardware‑aware recommendations that reflect how the system behaves when users are active.

This second pass is essential for:

- 	identifying bottlenecks
- 	adjusting worker counts
- 	optimizing memory allocation
- 	ensuring long‑term stability and performance

### 📄 Detailed Analyzer Documentation

You can find full explanations of how each analyzer works, what the output means, and how the recommendations are calculated here:

- 	[PHP‑FPM Analyzer README](docs/PHP‑FPM_Analyzer.md)
- 	[PostgreSQL Analyzer README](docs/PostgreSQL_Analyzer.md)

Together, these tools provide a comprehensive tuning workflow: baseline analysis after installation, followed by performance‑driven tuning under real load.

> **Note:** The tuning recommendations are based on publicly available best practices and internet research. They are not guaranteed to be optimal for every environment. Suggestions and contributions are welcome — feel free to open an issue or pull request. A MySQL/MariaDB tuning analyzer is planned but not yet implemented.

----------

## 🛡️ Hardening

After deployment, you can harden your servers using the [nextcloud-hardening.yml](nextcloud-hardening.yml) playbook. It applies OS and SSH hardening based on the [DevSec Hardening Framework](https://dev-sec.io/) ([GitHub](https://github.com/dev-sec/ansible-collection-hardening)).

```bash
ansible-playbook nextcloud-hardening.yml
```

We use only the default settings from the collection, which make the systems secure while keeping Nextcloud fully functional. The only override is enabling IPv4 forwarding, which is required for Docker networking.

If you need stricter hardening, review the collection's variables directly and override them in `group_vars/all/hardening.yml`. This is of course unsupported — you're on your own.

----------

## �📚 Role Documentation

For detailed information on how individual roles work and how to configure them:

- [Pre-Check Role](docs/PRECHECK-README.md) — Pre-flight validation checks (office configuration, inventory structure), extensible framework
- [OS Role](docs/OS_README.md) — OS preparation, package repositories, base packages, password management
- [Database Roles](docs/DATABASE-README.md) — PostgreSQL and MariaDB installation, configuration, and tuning
- [Redis Role](docs/REDIS-README.md) — Redis/Valkey installation, unix socket configuration, system tuning
- [Docker Role](docs/DOCKER-README.md) — Docker installation, shared Compose file mechanism, Watchtower
- [TLS Certificate Role](docs/TLS-CERT-README.md) — Certificate provisioning with acme.sh or self-signed, automatic renewal, platform differences
- [PHP Role](docs/PHP-README.md) — PHP-FPM installation and configuration, drop-in INI strategy, pool management
- [Nextcloud Role](docs/NEXTCLOUD_README.md) — Nextcloud installation, webserver, database, and optional components (Talk, Collabora, Fulltextsearch, ExApps)
- [Nextcloud Office Role (Collabora)](docs/NEXTCLOUDOFFICE-README.md) — Collabora container deployment and richdocuments integration via nextcloud role
- [OnlyOffice Role](docs/ONLYOFFICE-README.md) — OnlyOffice Document Server deployment and Nextcloud app integration (DocumentServerUrl/JWT)

----------

## 🧸 Support for Children in Need

If you find this Playbook helpful and want to donate something, please go to this web page to donate for children in need. 

https://wir-fuer-kinder-in-not.org/ and click on "Spenden" (Donate)


----------

Ansible and Pulumi files in this repository are co-authored with GitHub Copilot.

