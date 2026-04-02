"""Provider-neutral firewall policy profiles.

This module defines provider-neutral ingress profiles and shared rule-selection
logic. Each compute provider converts the concrete profiles into
provider-specific resources.
"""

from typing import Any, Dict, List, Set, TypedDict


class IngressRule(TypedDict):
    protocol: str
    port: str


RULE_PROFILES: Dict[str, List[IngressRule]] = {
    "ssh": [
        {"protocol": "tcp", "port": "22"},
    ],
    "letsencrypt": [
        {"protocol": "tcp", "port": "80"},
    ],
    "nextcloud": [
        {"protocol": "tcp", "port": "443"},
    ],
    "coturn": [
        {"protocol": "tcp", "port": "3478"},
        {"protocol": "udp", "port": "3478"},
        {"protocol": "tcp", "port": "443"},
        {"protocol": "udp", "port": "443"},
        {"protocol": "udp", "port": "32769-65535"},
    ],
    "coturn-collocated": [
        {"protocol": "tcp", "port": "3478"},
        {"protocol": "udp", "port": "3478"},
        {"protocol": "tcp", "port": "5349"},
        {"protocol": "udp", "port": "5349"},
        {"protocol": "udp", "port": "32769-65535"},
    ],
    "signal": [
        {"protocol": "tcp", "port": "443"},
        {"protocol": "udp", "port": "20000-65535"},
    ],
    # Collocated OnlyOffice runs on 8443 (443 is typically owned by webserver).
    "onlyoffice-collocated": [
        {"protocol": "tcp", "port": "8443"},
    ],
}


def _resolve_onlyoffice_rule_name(groups: List[str]) -> str:
    """Return the concrete OnlyOffice profile for this host.

    Dedicated OnlyOffice hosts use HTTPS on 443 and therefore reuse the
    ``nextcloud`` profile. Collocated OnlyOffice hosts need the additional 8443
    profile because 443 is already owned by the webserver.
    """
    if "nextcloud" in groups and "onlyoffice" in groups:
        return "onlyoffice-collocated"
    return "nextcloud"


def _resolve_coturn_rule_name(groups: List[str]) -> str:
    """Return the concrete Coturn profile for this host.

    Dedicated Coturn hosts expose TURN/TLS on 443. When Coturn is collocated
    with Nextcloud, 443 is already occupied by the webserver, so the default
    TURN/TLS port 5349 is used instead while STUN stays on 3478.
    """
    if "nextcloud" in groups and "coturn" in groups:
        return "coturn-collocated"
    return "coturn"


def resolve_rule_names(
    spec: Dict[str, Any],
    *,
    rules_key: str,
    default_rules: List[str],
) -> List[str]:
    """Resolve effective rule names for one server spec.

    Applies shared inference for collocated roles and de-duplicates while
    preserving order.
    """
    raw_names = list(spec.get(rules_key, default_rules))
    groups = spec.get("server_groups", [])
    names: List[str] = []

    for name in raw_names:
        if name == "onlyoffice":
            names.append(_resolve_onlyoffice_rule_name(groups))
        elif name == "coturn":
            names.append(_resolve_coturn_rule_name(groups))
        else:
            names.append(name)

    # Collocation inference: Nextcloud + OnlyOffice on one host needs 8443.
    if (
        "nextcloud" in groups
        and "onlyoffice" in groups
        and "onlyoffice-collocated" not in names
    ):
        names.append("onlyoffice-collocated")

    # Coturn inference: add the correct dedicated or collocated profile based
    # on where the coturn role runs.
    coturn_rule_name = _resolve_coturn_rule_name(groups)
    if "coturn" in groups and coturn_rule_name not in names:
        names.append(coturn_rule_name)

    result: List[str] = []
    seen = set()
    for name in names:
        if name in seen:
            continue
        seen.add(name)
        result.append(name)
    return result


def collect_required_rule_names(
    server_specs: List[Dict[str, Any]],
    *,
    rules_key: str,
    default_rules: List[str],
) -> Set[str]:
    """Collect all concrete rule profiles needed across a list of servers."""
    required: Set[str] = set()
    for spec in server_specs:
        required.update(
            resolve_rule_names(
                spec,
                rules_key=rules_key,
                default_rules=default_rules,
            )
        )
    return required
