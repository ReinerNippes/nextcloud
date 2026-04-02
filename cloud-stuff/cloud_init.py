"""Cloud-init user-data generation for the Ansible user."""

import yaml


def make_user_data(ssh_pub_key: str) -> str:
    """Return a cloud-init user-data string that creates an 'ansible' user."""

    cloud_init_config = {
        "manage_etc_hosts": False,
        "users": [
            "default",
            {
                "name": "ansible",
                "gecos": "Ansible User",
                "shell": "/bin/bash",
                "sudo": "ALL=(ALL) NOPASSWD:ALL",
                "lock_passwd": True,
                "ssh_authorized_keys": [ssh_pub_key],
            },
        ],
    }
    return "#cloud-config\n" + yaml.dump(
        cloud_init_config, default_flow_style=False
    )
