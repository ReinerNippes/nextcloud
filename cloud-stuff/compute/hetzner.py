"""Hetzner Cloud compute provider."""

from typing import Any, Dict, List, Optional

import pulumi_hcloud as hcloud
from pulumi import InvokeOptions, ResourceOptions

from compute import ComputeProvider, ServerResult, parse_server_spec
from compute.firewall_policy import (
    RULE_PROFILES,
    collect_required_rule_names,
    resolve_rule_names,
)
from ssh_waiter import SshWaiter


def _build_firewall_defs() -> Dict[str, list]:
    defs: Dict[str, list] = {}
    for profile_name, rules in RULE_PROFILES.items():
        defs[profile_name] = [
            {
                "direction": "in",
                "protocol": rule["protocol"],
                "port": rule["port"],
                "source_ips": ["0.0.0.0/0", "::/0"],
                "description": f"{profile_name}:{rule['protocol']}/{rule['port']}",
            }
            for rule in rules
        ]
    return defs


_FIREWALL_DEFS = _build_firewall_defs()


class HetznerCompute(ComputeProvider):
    """Hetzner Cloud — servers, firewalls, optional private network."""

    def __init__(self, token: str, ssh_key_name: str, location: str = "fsn1"):
        self._provider = hcloud.Provider("hcloud", token=token)
        self._location = location

        self._ssh_key = hcloud.get_ssh_key(
            name=ssh_key_name,
            opts=InvokeOptions(provider=self._provider),
        )
        self._opts = ResourceOptions(provider=self._provider)

    def _create_firewalls(
        self,
        environment: str,
        required_firewall_names: List[str],
    ) -> Dict[str, hcloud.Firewall]:
        env_prefix = environment.replace("_", "-")
        firewalls = {}
        for name in required_firewall_names:
            rules_data = _FIREWALL_DEFS[name]
            rules = [hcloud.FirewallRuleArgs(**r) for r in rules_data]
            firewalls[name] = hcloud.Firewall(
                f"{name}-firewall", name=f"{env_prefix}-{name}", rules=rules, opts=self._opts,
            )
        return firewalls

    def _create_network(
        self, config: Dict[str, Any]
    ) -> hcloud.Network:
        net_name = config.get("name", "nextcloud-net")
        network = hcloud.Network(
            net_name,
            name=net_name,
            ip_range=config.get("ip_range", "10.0.0.0/16"),
            opts=self._opts,
        )
        hcloud.NetworkSubnet(
            f"{net_name}-subnet",
            network_id=network.id,
            type="cloud",
            network_zone="eu-central",
            ip_range=config.get("subnet", "10.0.1.0/24"),
            opts=self._opts,
        )
        return network

    def create_servers(
        self,
        server_specs,
        *,
        ssh_pub_key,
        user_data,
        environment,
        zone_name=None,
        network_config=None,
    ):
        required_firewall_names = sorted(
            collect_required_rule_names(
                server_specs,
                rules_key="public_firewall_rules",
                default_rules=["ssh", "letsencrypt", "nextcloud"],
            )
        )
        firewalls = self._create_firewalls(environment, required_firewall_names)
        network = self._create_network(network_config) if network_config else None

        servers: Dict[str, ServerResult] = {}

        for spec in server_specs:
            name = spec["name"]
            server_name, dns_aliases, additional_fqdn_map, all_aliases = parse_server_spec(spec, zone_name)
            image = spec["image"]
            server_type = spec.get("server_type", "cx32")
            nets = spec.get("networks", ["public"])
            groups = spec.get("server_groups", [])

            labels = {f"group_{g}": "true" for g in groups}
            labels["env"] = environment
            if zone_name:
                labels["zone"] = zone_name
            for k, v in additional_fqdn_map.items():
                labels[k] = v

            fw_names = resolve_rule_names(
                spec,
                rules_key="public_firewall_rules",
                default_rules=["ssh", "letsencrypt", "nextcloud"],
            )
            fw_ids = [firewalls[fw].id for fw in fw_names if fw in firewalls]

            has_public = "public" in nets
            has_private = "private" in nets

            server = hcloud.Server(
                name,
                name=server_name,
                server_type=server_type,
                image=image,
                location=self._location,
                ssh_keys=[self._ssh_key.id],
                firewall_ids=fw_ids,
                labels=labels,
                public_nets=[hcloud.ServerPublicNetArgs(
                    ipv4_enabled=has_public, ipv6_enabled=has_public,
                )],
                user_data=user_data,
                opts=ResourceOptions(
                    provider=self._provider, ignore_changes=["user_data"],
                ),
            )

            if has_private and network is not None:
                hcloud.ServerNetwork(
                    f"{name}-net",
                    server_id=server.id,
                    network_id=network.id,
                    opts=self._opts,
                )

            if has_public:
                SshWaiter(
                    f"{name}-ssh-wait",
                    ip=server.ipv4_address,
                    timeout=300,
                    opts=ResourceOptions(depends_on=[server]),
                )

            servers[name] = ServerResult(
                public_ip=server.ipv4_address if has_public else None,
            )

        return servers
