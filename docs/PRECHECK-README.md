# Pre-Check Role

Validates Nextcloud deployment configuration before any installation begins. This role runs as a pre-flight check to catch configuration errors early and provide clear error messages.

## Purpose

- Validates office solution configuration (ensure only one is enabled)
- Validates inventory structure (required groups exist)
- Can be extended with additional checks as needed

## When it runs

At the very beginning of the playbook (after OS package update), before any component installation.

## Task Structure

```
tasks/main.yml                   Orchestrates all check tasks
├── office_config.yml            Office solution conflict validation
└── inventory_validation.yml      Inventory structure validation
```

## Office Configuration Check

Ensures that `nextcloud_install.nextcloudoffice` and `nextcloud_install.onlyoffice` are not both enabled.

**Checked variables:**
- `nextcloud_install.nextcloudoffice`
- `nextcloud_install.onlyoffice`

**Failure message:** Clear explanation with instructions to fix via group_vars or command-line override.

## Inventory Validation Check

Ensures required inventory groups exist and are not empty.

**Checked groups:**
- `nextcloud` (required, must have ≥ 1 host)
- `database` (required, must have ≥ 1 host)
- `webserver` (required, must have ≥ 1 host)

**Failure message:** Explains which group is missing and shows correct inventory structure.

## Extending the Role

To add new validation checks:

1. Create a new file in `tasks/` (e.g., `tasks/my_check.yml`)
2. Add `include_tasks` to `tasks/main.yml`:

```yaml
- name: Include my custom checks
  ansible.builtin.include_tasks: my_check.yml
```

3. Use `ansible.builtin.assert` with clear `fail_msg` and `success_msg`:

```yaml
- name: My custom validation
  ansible.builtin.assert:
    that:
      - "my_condition | bool"
    fail_msg: |
      ─────────────────────────────────────────────────────────────────────────────
      🚫 ERROR: Description of what went wrong
      ─────────────────────────────────────────────────────────────────────────────
      
      Details and instructions...
      
      ─────────────────────────────────────────────────────────────────────────────
    success_msg: "✓ My check passed"
  run_once: true
  delegate_to: localhost
```

## Example: Adding a TLS check

Create `tasks/tls_validation.yml`:

```yaml
---
- name: Ensure TLS certificate type is valid
  ansible.builtin.assert:
    that:
      - "tls_certificate.type in ['acme.sh', 'selfsigned']"
    fail_msg: |
      ─────────────────────────────────────────────────────────────────────────────
      🚫 ERROR: Invalid TLS certificate type
      ─────────────────────────────────────────────────────────────────────────────
      
      tls_certificate.type: {{ tls_certificate.type }}
      
      Valid options:
        • acme.sh      (Let's Encrypt / ACME)
        • selfsigned   (Self-signed for testing)
      
      ─────────────────────────────────────────────────────────────────────────────
    success_msg: "✓ TLS configuration valid: {{ tls_certificate.type }}"
  run_once: true
  delegate_to: localhost
```

Then add to `tasks/main.yml`:

```yaml
- name: Include TLS validation checks
  ansible.builtin.include_tasks: tls_validation.yml
```

## Execution Details

- Runs with `run_once: true` to execute only once per play
- Delegates to `localhost` to validate configuration before connecting to inventory hosts
- Uses `gather_facts: false` in the calling play (see playbook integration)
