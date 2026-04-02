"""Scaleway compute provider."""

from typing import Any, Dict, List, Optional

import pulumiverse_scaleway as scaleway
from pulumi import ResourceOptions

from compute import ComputeProvider, ServerResult, parse_server_spec
from compute.firewall_policy import RULE_PROFILES, resolve_rule_names
from ssh_waiter import SshWaiter

def _build_security_group(
    name: str,
    rule_names: list,
    *,
    provider: scaleway.Provider,
    project_id: str,
    zone: str,
) -> scaleway.InstanceSecurityGroup:
    """Create a single security group with merged rule sets."""
    seen: set = set()
    inbound_rules = []
    for rule_name in rule_names:
        for rule in RULE_PROFILES.get(rule_name, []):
            protocol = rule["protocol"].upper()
            port = rule["port"]
            if "-" in port:
                key = (protocol, None, port)
            else:
                key = (protocol, int(port), None)
            if key in seen:
                continue
            seen.add(key)
            kwargs = {"action": "accept", "protocol": protocol}
            if "-" in port:
                kwargs["port_range"] = port
            else:
                kwargs["port"] = int(port)
            inbound_rules.append(scaleway.InstanceSecurityGroupInboundRuleArgs(**kwargs))

    return scaleway.InstanceSecurityGroup(
        f"{name}-sg",
        name=name,
        inbound_default_policy="drop",
        outbound_default_policy="accept",
        stateful=True,
        inbound_rules=inbound_rules,
        project_id=project_id,
        zone=zone,
        opts=ResourceOptions(provider=provider),
    )


class ScalewayCompute(ComputeProvider):
    """Scaleway — instances, security groups, optional private network."""

    def __init__(
        self,
        access_key: str,
        secret_key: str,
        project_id: str,
        region: str = "fr-par",
        zone: str = "fr-par-1",
    ):
        self._provider = scaleway.Provider(
            "scaleway",
            access_key=access_key,
            secret_key=secret_key,
            project_id=project_id,
            region=region,
            zone=zone,
        )
        self._project_id = project_id
        self._region = region
        self._zone = zone

    @property
    def provider(self) -> scaleway.Provider:
        """Expose provider for managed services and DNS that need it."""
        return self._provider

    @property
    def project_id(self) -> str:
        return self._project_id

    @property
    def region(self) -> str:
        return self._region

    @property
    def zone(self) -> str:
        return self._zone

    def _create_network(self, config: Dict[str, Any]) -> scaleway.VpcPrivateNetwork:
        net_name = config.get("name", "nextcloud-net")
        return scaleway.VpcPrivateNetwork(
            net_name,
            name=net_name,
            project_id=self._project_id,
            region=self._region,
            opts=ResourceOptions(provider=self._provider),
        )

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
        # SSH key
        scaleway.IamSshKey(
            "ansible-ssh-key",
            name="ansible",
            public_key=ssh_pub_key,
            project_id=self._project_id,
            opts=ResourceOptions(provider=self._provider),
        )

        network = self._create_network(network_config) if network_config else None

        servers: Dict[str, ServerResult] = {}

        for spec in server_specs:
            name = spec["name"]
            server_fqdn, dns_aliases, additional_fqdn_map, all_aliases = parse_server_spec(spec, zone_name)
            image = spec["image"]
            commercial_type = spec.get("commercial_type", "DEV1-L")
            nets = spec.get("networks", ["public"])
            groups = spec.get("server_groups", [])

            tags = [f"group_{g}" for g in groups]
            tags.append(f"env_{environment}")
            for k, v in additional_fqdn_map.items():
                tags.append(f"{k}={v}")

            has_public = "public" in nets
            has_private = "private" in nets

            rule_names = resolve_rule_names(
                spec,
                rules_key="public_firewall_rules",
                default_rules=["ssh", "letsencrypt", "nextcloud"],
            )
            sg = _build_security_group(
                name, rule_names,
                provider=self._provider,
                project_id=self._project_id,
                zone=self._zone,
            )

            public_ip_resource = None
            if has_public:
                public_ip_resource = scaleway.InstanceIp(
                    f"{name}-ip",
                    project_id=self._project_id,
                    zone=self._zone,
                    tags=tags,
                    opts=ResourceOptions(provider=self._provider),
                )

            server_kwargs: Dict[str, Any] = {
                "name": name,
                "type": commercial_type,
                "image": image,
                "tags": tags,
                "security_group_id": sg.id,
                "cloud_init": user_data,
                "project_id": self._project_id,
                "zone": self._zone,
            }
            if public_ip_resource:
                server_kwargs["ip_id"] = public_ip_resource.id

            server = scaleway.InstanceServer(
                name,
                opts=ResourceOptions(
                    provider=self._provider, ignore_changes=["cloud_init"],
                ),
                **server_kwargs,
            )

            if has_private and network is not None:
                scaleway.InstancePrivateNic(
                    f"{name}-private-nic",
                    server_id=server.id,
                    private_network_id=network.id,
                    zone=self._zone,
                    opts=ResourceOptions(provider=self._provider),
                )

            if has_public and public_ip_resource:
                SshWaiter(
                    f"{name}-ssh-wait",
                    ip=public_ip_resource.address,
                    timeout=300,
                    opts=ResourceOptions(depends_on=[server]),
                )

            servers[name] = ServerResult(
                public_ip=public_ip_resource.address if public_ip_resource else None,
            )

        return servers
