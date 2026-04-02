"""Abstract compute provider interface."""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple

import pulumi


@dataclass
class ServerResult:
    """Standardised return value for a created server."""

    public_ip: Optional[pulumi.Output[str]] = None
    private_ip: Optional[pulumi.Output[str]] = None


def normalize_fqdn(name: str, zone_name: Optional[str]) -> str:
    """Append zone_name if the name is not already a full FQDN."""
    if not zone_name:
        return name
    zone_suffix = f".{zone_name}"
    if name.endswith(zone_suffix) or name.count(".") >= 2:
        return name
    return f"{name}{zone_suffix}"


def parse_server_spec(
    spec: Dict[str, Any],
    zone_name: Optional[str] = None,
) -> Tuple[str, List[str], Dict[str, str], List[str]]:
    """Extract common fields from a server spec.

    Returns:
        (server_fqdn, dns_aliases, additional_fqdn_map, all_aliases)

    ``additional_fqdn_map`` maps label keys (``additional_fqdn_<name>``)
    to their normalised FQDN values.

    ``all_aliases`` is a deduplicated list of dns_aliases + additional FQDNs.
    """
    name = spec["name"]
    server_fqdn = normalize_fqdn(name, zone_name)

    dns_aliases = spec.get("dns_aliases", [])
    if isinstance(dns_aliases, str):
        dns_aliases = [dns_aliases]

    additional_fqdn_map: Dict[str, str] = {}
    for k, v in spec.items():
        if k.startswith("additional_fqdn_") and isinstance(v, str) and v:
            additional_fqdn_map[k] = normalize_fqdn(v, zone_name)
    raw_additional_fqdns = spec.get("additional_fqdns", {})
    if isinstance(raw_additional_fqdns, dict):
        for k, v in raw_additional_fqdns.items():
            if isinstance(v, str) and v:
                additional_fqdn_map[f"additional_fqdn_{k}"] = normalize_fqdn(v, zone_name)

    all_aliases: List[str] = []
    seen: set = set()
    for alias in [*dns_aliases, *additional_fqdn_map.values()]:
        if alias and alias not in seen:
            seen.add(alias)
            all_aliases.append(alias)

    return server_fqdn, dns_aliases, additional_fqdn_map, all_aliases


class ComputeProvider(ABC):
    """Interface that all compute providers must implement.

    Each provider translates the common server spec format into
    provider-specific resources (instances, firewalls, security groups,
    SSH keys, networks, …).
    """

    @abstractmethod
    def create_servers(
        self,
        server_specs: List[Dict[str, Any]],
        *,
        ssh_pub_key: str,
        user_data: str,
        environment: str,
        zone_name: Optional[str] = None,
        network_config: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, ServerResult]:
        """Provision servers according to *server_specs*.

        Returns a mapping of server name → ServerResult.
        """
